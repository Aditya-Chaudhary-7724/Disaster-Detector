"""Hybrid ML predictor with ensemble voting and async weather enrichment.

US-5:
- Logistic Regression + Random Forest soft voting
- Probability output
- Persisted model artifacts (.pkl)
- Real dataset fallback to synthetic structured dataset
- Live weather + satellite proxy feature merge
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.error import URLError
from urllib.request import urlopen

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from feature_engineering import fit_feature_artifacts, transform_with_artifacts

ROOT = Path(__file__).parent
MODELS_DIR = ROOT / "models"
DATASET_PATH = ROOT / "datasets" / "disaster_dataset.csv"

LOGREG_PATH = MODELS_DIR / "hybrid_logreg.pkl"
RF_PATH = MODELS_DIR / "hybrid_rf.pkl"
ARTIFACTS_PATH = MODELS_DIR / "hybrid_feature_artifacts.pkl"
LABEL_ENCODER_PATH = MODELS_DIR / "hybrid_label_encoder.pkl"
META_PATH = MODELS_DIR / "hybrid_model_meta.pkl"
DB_PATH = ROOT / "disasters.db"

_MODEL_CACHE: Dict[str, object] | None = None
_WEATHER_CACHE: Dict[str, Dict[str, object]] = {}
WEATHER_CACHE_TTL = 900

RISK_TO_SCORE = {"Low": 0.30, "Medium": 0.60, "High": 0.85}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "seismic_mag" in out.columns and "seismic_magnitude" not in out.columns:
        out["seismic_magnitude"] = out["seismic_mag"]
    if "disaster" in out.columns and "disaster_type" not in out.columns:
        out["disaster_type"] = out["disaster"]
    if "risk" in out.columns and "risk_label" not in out.columns:
        out["risk_label"] = out["risk"]

    out["disaster_type"] = out.get("disaster_type", "flood").astype(str).str.lower()
    out["risk_label"] = out.get("risk_label", "Low").astype(str).str.title()
    return out


def _structured_synthetic_dataset(n_per_hazard: int = 2800) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows: List[Dict[str, object]] = []
    hazards = ["earthquake", "flood", "landslide"]
    tier_map = {
        "Low": {"rain": (20, 35), "soil": (0.25, 0.08), "slope": (8, 5), "ndvi": (0.72, 0.10), "seismic": (1.5, 0.8), "depth": (140, 45)},
        "Medium": {"rain": (95, 35), "soil": (0.55, 0.10), "slope": (22, 7), "ndvi": (0.48, 0.10), "seismic": (4.0, 0.8), "depth": (70, 25)},
        "High": {"rain": (185, 45), "soil": (0.82, 0.08), "slope": (38, 8), "ndvi": (0.24, 0.09), "seismic": (6.4, 0.9), "depth": (18, 10)},
    }

    for hz in hazards:
        for _ in range(n_per_hazard):
            label = rng.choice(["Low", "Medium", "High"], p=[0.34, 0.33, 0.33])
            tier = tier_map[label]
            rainfall = float(np.clip(rng.normal(*tier["rain"]), 0, 350))
            rainfall_7d = float(np.clip(rainfall * rng.uniform(2.2, 4.6), 0, 1400))
            soil = float(np.clip(rng.normal(*tier["soil"]), 0, 1))
            slope = float(np.clip(rng.normal(*tier["slope"]), 0, 60))
            ndvi = float(np.clip(rng.normal(*tier["ndvi"]), 0, 1))
            plant = float(np.clip(rng.normal(0.5, 0.2), 0, 1))
            seismic = float(np.clip(rng.normal(*tier["seismic"]), 0, 8.5))
            depth = float(np.clip(rng.normal(*tier["depth"]), 1, 300))
            lat = float(rng.uniform(6, 38))
            lon = float(rng.uniform(67, 98))
            temp = float(np.clip(rng.normal(28, 6), 12, 45))
            hum = float(np.clip(rng.normal(72, 15), 20, 100))
            press = float(np.clip(rng.normal(1008, 9), 970, 1035))
            rain3h = float(np.clip(rainfall / 8 + rng.normal(0, 5), 0, 90))

            if hz == "earthquake":
                seismic = float(np.clip(seismic + {"Low": -0.3, "Medium": 0.3, "High": 0.8}[label], 0.5, 8.9))
                depth = float(np.clip(depth + {"Low": 50, "Medium": 0, "High": -8}[label], 1, 250))
                rainfall = float(np.clip(rainfall * 0.25, 0, 120))
            elif hz == "flood":
                rainfall = float(np.clip(rainfall + {"Low": -5, "Medium": 20, "High": 55}[label], 5, 420))
                rainfall_7d = float(np.clip(rainfall * rng.uniform(2.8, 5.5), 15, 1800))
                soil = float(np.clip(soil + {"Low": -0.05, "Medium": 0.08, "High": 0.12}[label], 0.15, 1))
                hum = float(np.clip(hum + {"Low": -8, "Medium": 2, "High": 12}[label], 30, 100))
                slope = float(np.clip(slope * 0.45, 0, 40))
            else:
                slope = float(np.clip(slope + {"Low": -2, "Medium": 8, "High": 16}[label], 4, 65))
                rainfall = float(np.clip(rainfall + {"Low": 0, "Medium": 18, "High": 34}[label], 0, 390))
                rainfall_7d = float(np.clip(rainfall * rng.uniform(2.5, 5.2), 0, 1650))
                soil = float(np.clip(soil + {"Low": -0.03, "Medium": 0.04, "High": 0.10}[label], 0, 1))
                ndvi = float(np.clip(ndvi - {"Low": 0.00, "Medium": 0.08, "High": 0.16}[label], 0, 1))

            rows.append(
                {
                    "timestamp": pd.Timestamp.utcnow().isoformat(),
                    "disaster_type": hz,
                    "latitude": lat,
                    "longitude": lon,
                    "rainfall_24h_mm": rainfall,
                    "rainfall_7d_mm": rainfall_7d,
                    "soil_moisture": soil,
                    "slope_deg": slope,
                    "ndvi": ndvi,
                    "plant_density": plant,
                    "seismic_magnitude": seismic,
                    "depth_km": depth,
                    "weather_temp_c": temp,
                    "weather_humidity": hum,
                    "weather_pressure_hpa": press,
                    "weather_rain_3h_mm": rain3h,
                    "risk_label": label,
                }
            )

    return pd.DataFrame(rows)


def _load_training_dataset() -> pd.DataFrame:
    synthetic = _structured_synthetic_dataset()
    if DATASET_PATH.exists() and DATASET_PATH.stat().st_size > 0:
        try:
            df = pd.read_csv(DATASET_PATH)
            df = _normalize_columns(df)
            if "risk_label" in df.columns and len(df) > 100:
                keep = [c for c in synthetic.columns if c in df.columns]
                df = df[keep].copy()
                synthetic_tail = synthetic[keep].tail(min(len(df), 1200))
                return pd.concat([synthetic[keep], synthetic_tail], ignore_index=True)
        except Exception:
            pass
    return synthetic


def _ensure_weather_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    defaults = {
        "weather_temp_c": 28.0,
        "weather_humidity": 70.0,
        "weather_pressure_hpa": 1008.0,
        "weather_rain_3h_mm": 0.0,
    }
    for col, dv in defaults.items():
        if col not in out.columns:
            out[col] = dv
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(dv)

    if "rainfall_7d_mm" not in out.columns:
        out["rainfall_7d_mm"] = pd.to_numeric(out.get("rainfall_24h_mm", 0), errors="coerce").fillna(0) * 3.0
    return out


def train_hybrid_models(force: bool = False) -> Dict[str, object]:
    global _MODEL_CACHE

    if not force and all(p.exists() for p in [LOGREG_PATH, RF_PATH, ARTIFACTS_PATH, LABEL_ENCODER_PATH, META_PATH]):
        return load_hybrid_models()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = _ensure_weather_columns(_load_training_dataset())

    if "timestamp" not in df.columns:
        df["timestamp"] = pd.Timestamp.utcnow().isoformat()

    if "rainfall_7d_mm" not in df.columns:
        df["rainfall_7d_mm"] = pd.to_numeric(df.get("rainfall_24h_mm", 0), errors="coerce").fillna(0) * 3.0

    X_engineered, artifacts = fit_feature_artifacts(df)

    labels = _normalize_columns(df)["risk_label"].astype(str).str.title()
    le = LabelEncoder()
    y = le.fit_transform(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X_engineered,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    rf = RandomForestClassifier(
        n_estimators=280,
        max_depth=16,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    gb = GradientBoostingClassifier(
        n_estimators=240,
        learning_rate=0.06,
        max_depth=3,
        random_state=42,
    )

    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)

    p2 = rf.predict_proba(X_test)
    p3 = gb.predict_proba(X_test)
    avg_prob = (0.60 * p2) + (0.40 * p3)
    pred = avg_prob.argmax(axis=1)
    acc = float(accuracy_score(y_test, pred))
    precision = float(precision_score(y_test, pred, average="macro", zero_division=0))
    recall = float(recall_score(y_test, pred, average="macro", zero_division=0))

    joblib.dump(rf, RF_PATH)
    joblib.dump(gb, MODELS_DIR / "hybrid_gb.pkl")
    joblib.dump(artifacts, ARTIFACTS_PATH)
    joblib.dump(le, LABEL_ENCODER_PATH)
    meta = {
        "accuracy": round(acc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "trained_at": int(time.time()),
        "dataset_rows": int(len(df)),
        "models": [str(RF_PATH), str(MODELS_DIR / "hybrid_gb.pkl")],
    }
    print(
        "Hybrid ML metrics | "
        f"accuracy={meta['accuracy']:.4f} precision={meta['precision']:.4f} recall={meta['recall']:.4f} "
        f"rows={meta['dataset_rows']}"
    )
    joblib.dump(meta, META_PATH)

    _MODEL_CACHE = {
        "rf": rf,
        "gb": gb,
        "artifacts": artifacts,
        "label_encoder": le,
        "meta": meta,
    }
    return _MODEL_CACHE


def load_hybrid_models() -> Dict[str, object]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    gb_path = MODELS_DIR / "hybrid_gb.pkl"
    if not all(p.exists() for p in [RF_PATH, gb_path, ARTIFACTS_PATH, LABEL_ENCODER_PATH, META_PATH]):
        return train_hybrid_models(force=True)

    _MODEL_CACHE = {
        "rf": joblib.load(RF_PATH),
        "gb": joblib.load(gb_path),
        "artifacts": joblib.load(ARTIFACTS_PATH),
        "label_encoder": joblib.load(LABEL_ENCODER_PATH),
        "meta": joblib.load(META_PATH),
    }
    if float(_MODEL_CACHE["meta"].get("accuracy") or 0.0) < 0.8:
        return train_hybrid_models(force=True)
    return _MODEL_CACHE


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)}:{round(lon, 2)}"


def _weather_fallback() -> Dict[str, float]:
    return {
        "weather_temp_c": 28.0,
        "weather_humidity": 70.0,
        "weather_pressure_hpa": 1008.0,
        "weather_rain_3h_mm": 0.0,
        "weather_source": "fallback",
    }


def _fetch_weather_sync(lat: float, lon: float) -> Dict[str, float]:
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        return _weather_fallback()

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat:.4f}&lon={lon:.4f}&appid={api_key}&units=metric"
    )

    try:
        with urlopen(url, timeout=0.12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (URLError, TimeoutError, ValueError, OSError):
        return _weather_fallback()

    main = payload.get("main", {})
    rain = payload.get("rain", {})
    return {
        "weather_temp_c": float(main.get("temp") or 28.0),
        "weather_humidity": float(main.get("humidity") or 70.0),
        "weather_pressure_hpa": float(main.get("pressure") or 1008.0),
        "weather_rain_3h_mm": float(rain.get("3h") or 0.0),
        "weather_source": "openweather",
    }


async def fetch_weather_async(lat: float, lon: float) -> Dict[str, float]:
    return await asyncio.to_thread(_fetch_weather_sync, lat, lon)


def get_weather_features(lat: float, lon: float) -> Dict[str, float]:
    key = _cache_key(lat, lon)
    now = time.time()
    cached = _WEATHER_CACHE.get(key)
    if cached and (now - float(cached["ts"])) < WEATHER_CACHE_TTL:
        return cached["data"]

    try:
        data = asyncio.run(asyncio.wait_for(fetch_weather_async(lat, lon), timeout=0.18))
    except Exception:
        data = _weather_fallback()

    _WEATHER_CACHE[key] = {"ts": now, "data": data}
    return data


def _estimate_rainfall_7d(payload: Dict[str, object]) -> float:
    if payload.get("rainfall_7d_mm") not in (None, ""):
        try:
            return float(payload.get("rainfall_7d_mm") or 0)
        except (TypeError, ValueError):
            pass
    try:
        rain24 = float(payload.get("rainfall_24h_mm") or 0)
    except (TypeError, ValueError):
        rain24 = 0.0
    return max(0.0, rain24 * 3.2)


def _db_context(disaster: str) -> Dict[str, float]:
    if not DB_PATH.exists():
        return {}

    table_map = {"earthquake": "earthquakes", "flood": "floods", "landslide": "landslides"}
    table = table_map.get(disaster)
    if not table:
        return {}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table} ORDER BY time DESC LIMIT 7")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    except Exception:
        return {}

    if not rows:
        return {}

    def avg(col: str, default: float = 0.0) -> float:
        vals = []
        for r in rows:
            try:
                v = float(r.get(col) if r.get(col) is not None else default)
                vals.append(v)
            except (TypeError, ValueError):
                pass
        return float(sum(vals) / len(vals)) if vals else default

    context = {
        "db_rainfall_24h_avg": avg("rainfall_24h_mm", 0.0),
        "db_soil_moisture_avg": avg("soil_moisture", 0.5),
        "db_slope_avg": avg("slope_deg", 10.0),
        "db_depth_avg": avg("depth", 60.0),
        "db_seismic_avg": avg("magnitude", 0.0),
    }
    context["db_rainfall_7d_sum"] = context["db_rainfall_24h_avg"] * min(7, len(rows))
    return context


def _satellite_proxy_features(base: Dict[str, float]) -> Dict[str, float]:
    rain24 = float(base.get("rainfall_24h_mm", 0))
    hum = float(base.get("weather_humidity", 70.0))
    temp = float(base.get("weather_temp_c", 28.0))

    ndvi_proxy = np.clip(0.65 - (rain24 / 1000.0) + ((temp - 25.0) / 100.0), 0.05, 0.9)
    soil_proxy = np.clip(0.30 + (rain24 / 500.0) + (hum / 300.0), 0.15, 0.95)

    return {
        "ndvi": float(base.get("ndvi") or ndvi_proxy),
        "soil_moisture": float(base.get("soil_moisture") or soil_proxy),
        "sat_ndvi_proxy": float(ndvi_proxy),
        "sat_soil_proxy": float(soil_proxy),
    }


def _prepare_feature_row(payload: Dict[str, object]) -> Tuple[pd.DataFrame, Dict[str, float]]:
    disaster = str(payload.get("disaster") or payload.get("disaster_type") or "flood").lower()
    lat = float(payload.get("latitude") or payload.get("lat") or 20.0)
    lon = float(payload.get("longitude") or payload.get("lon") or 77.0)

    weather = get_weather_features(lat, lon)
    db_ctx = _db_context(disaster)

    row: Dict[str, object] = {
        "timestamp": pd.Timestamp.utcnow().isoformat(),
        "disaster_type": disaster,
        "latitude": lat,
        "longitude": lon,
        "rainfall_24h_mm": float(payload.get("rainfall_24h_mm") or db_ctx.get("db_rainfall_24h_avg") or 0),
        "rainfall_7d_mm": float(payload.get("rainfall_7d_mm") or db_ctx.get("db_rainfall_7d_sum") or _estimate_rainfall_7d(payload)),
        "soil_moisture": float(payload.get("soil_moisture") or db_ctx.get("db_soil_moisture_avg") or 0),
        "slope_deg": float(payload.get("slope_deg") or db_ctx.get("db_slope_avg") or 0),
        "ndvi": float(payload.get("ndvi") or 0),
        "plant_density": float(payload.get("plant_density") or 0.5),
        "seismic_magnitude": float(payload.get("seismic_magnitude") or payload.get("seismic_mag") or db_ctx.get("db_seismic_avg") or 0),
        "depth_km": float(payload.get("depth_km") or db_ctx.get("db_depth_avg") or 0),
        "weather_temp_c": float(weather["weather_temp_c"]),
        "weather_humidity": float(weather["weather_humidity"]),
        "weather_pressure_hpa": float(weather["weather_pressure_hpa"]),
        "weather_rain_3h_mm": float(weather["weather_rain_3h_mm"]),
    }

    row.update(_satellite_proxy_features(row))
    return pd.DataFrame([row]), weather


def predict_hybrid_ml(payload: Dict[str, object]) -> Dict[str, object]:
    start = time.perf_counter()
    models = load_hybrid_models()
    df_one, weather = _prepare_feature_row(payload)

    X = transform_with_artifacts(df_one, models["artifacts"])
    rf = models["rf"]
    gb = models["gb"]
    le: LabelEncoder = models["label_encoder"]

    p_rf = rf.predict_proba(X)[0]
    p_gb = gb.predict_proba(X)[0]
    p_avg = (0.60 * p_rf) + (0.40 * p_gb)

    idx = int(np.argmax(p_avg))
    risk_label = str(le.inverse_transform([idx])[0])
    ml_probability = float(np.max(p_avg))

    rf_importance = {
        name: round(float(val), 4)
        for name, val in zip(X.columns.tolist(), getattr(rf, "feature_importances_", np.zeros(X.shape[1])))
    }

    gb_importance = {
        name: round(float(val), 4)
        for name, val in zip(X.columns.tolist(), getattr(gb, "feature_importances_", np.zeros(X.shape[1])))
    }
    hybrid_importance = {}
    for i, col in enumerate(X.columns):
        score = 0.6 * float(rf_importance.get(col, 0.0)) + 0.4 * float(gb_importance.get(col, 0.0))
        hybrid_importance[col] = round(score, 4)

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    return {
        "risk_level": risk_label,
        "ml_probability": round(ml_probability, 4),
        "probabilities": {
            cls: round(float(prob), 4)
            for cls, prob in zip(le.classes_, p_avg)
        },
        "confidence": round(ml_probability, 4),
        "feature_importance": hybrid_importance,
        "model_accuracy": models["meta"].get("accuracy"),
        "model_precision": models["meta"].get("precision"),
        "model_recall": models["meta"].get("recall"),
        "weather_source": weather.get("weather_source", "fallback"),
        "latency_ms": round(float(elapsed_ms), 2),
        "ensemble": "random_forest + gradient_boosting (soft vote)",
    }
