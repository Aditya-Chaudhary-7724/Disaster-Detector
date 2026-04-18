"""Simulated satellite predictor.

Uses synthetic satellite-derived environmental signals to estimate hazard risk.
The public function names are kept stable for existing routes and callers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "models" / "satellite_rf.pkl"
META_PATH = ROOT / "models" / "satellite_rf_meta.pkl"

FEATURE_COLUMNS = ["ndvi", "rainfall_intensity", "soil_moisture", "temperature"]
_MODEL_CACHE = None
_META_CACHE: Dict[str, object] | None = None


def _risk_level(score: float) -> str:
    if score > 0.7:
        return "High"
    if score >= 0.4:
        return "Medium"
    return "Low"


def _satellite_seed(disaster_type: str, bbox: Optional[Tuple[float, float, float, float]] = None) -> int:
    token = disaster_type
    if bbox:
        token += ":" + ":".join(f"{value:.3f}" for value in bbox)
    return abs(hash(token)) % (2**32)


def _build_synthetic_dataset(n: int = 3200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for disaster_type in ["flood", "landslide"]:
        for _ in range(n):
            if disaster_type == "flood":
                rainfall = float(np.clip(rng.normal(130, 55), 0, 280))
                soil = float(np.clip(rng.normal(0.66, 0.16), 0, 1))
                ndvi = float(np.clip(rng.normal(0.48, 0.16), 0.05, 0.95))
                temp = float(np.clip(rng.normal(27, 5), 10, 42))
                base_score = 0.45 * (rainfall / 250.0) + 0.35 * soil + 0.15 * (1 - ndvi) + 0.05 * (temp / 45.0)
            else:
                rainfall = float(np.clip(rng.normal(95, 45), 0, 250))
                soil = float(np.clip(rng.normal(0.62, 0.18), 0, 1))
                ndvi = float(np.clip(rng.normal(0.36, 0.18), 0.02, 0.95))
                temp = float(np.clip(rng.normal(24, 5), 5, 38))
                base_score = 0.28 * (rainfall / 220.0) + 0.32 * soil + 0.30 * (1 - ndvi) + 0.10 * (temp / 40.0)

            noise = float(rng.normal(0, 0.04))
            score = float(np.clip(base_score + noise, 0, 1))
            if score < 0.4:
                label = "Low"
            elif score <= 0.7:
                label = "Medium"
            else:
                label = "High"

            rows.append(
                {
                    "disaster_type": disaster_type,
                    "ndvi": ndvi,
                    "rainfall_intensity": rainfall,
                    "soil_moisture": soil,
                    "temperature": temp,
                    "risk_label": label,
                }
            )
    return pd.DataFrame(rows)


def _train_model(force: bool = False):
    global _MODEL_CACHE, _META_CACHE
    if MODEL_PATH.exists() and META_PATH.exists() and not force:
        _MODEL_CACHE = joblib.load(MODEL_PATH)
        _META_CACHE = joblib.load(META_PATH)
        return _MODEL_CACHE, _META_CACHE

    df = _build_synthetic_dataset()
    X = df[FEATURE_COLUMNS]
    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=260,
                    max_depth=14,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    accuracy = float((model.predict(X_test) == y_test).mean())

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    meta = {"accuracy": round(accuracy, 4), "feature_columns": FEATURE_COLUMNS, "samples": int(len(df))}
    joblib.dump(model, MODEL_PATH)
    joblib.dump(meta, META_PATH)
    _MODEL_CACHE = model
    _META_CACHE = meta
    return model, meta


def preload_satellite_model() -> Dict[str, object]:
    _, meta = _train_model(force=False)
    return {
        "loaded": True,
        "backend": "random_forest",
        "model_path": str(MODEL_PATH),
        "accuracy": meta.get("accuracy"),
    }


def _simulate_satellite_features(disaster_type: str, feature_overrides: Optional[Dict[str, float]] = None, bbox: Optional[Tuple[float, float, float, float]] = None) -> Dict[str, float]:
    feature_overrides = feature_overrides or {}
    seed = _satellite_seed(disaster_type, bbox)
    rng = np.random.default_rng(seed)

    lat_adj = 0.0
    lon_adj = 0.0
    if bbox:
        min_lat, max_lat, min_lon, max_lon = bbox
        lat_adj = ((min_lat + max_lat) / 2.0 - 22.0) / 20.0
        lon_adj = ((min_lon + max_lon) / 2.0 - 82.0) / 20.0

    defaults = {
        "ndvi": float(np.clip(rng.normal(0.46 - 0.08 * lat_adj, 0.12), 0.05, 0.9)),
        "rainfall_intensity": float(np.clip(rng.normal(110 + 18 * lon_adj, 40), 0, 260)),
        "soil_moisture": float(np.clip(rng.normal(0.58 + 0.08 * lat_adj, 0.15), 0.05, 0.98)),
        "temperature": float(np.clip(rng.normal(27 - 2.5 * lat_adj, 4), 8, 42)),
    }

    if disaster_type == "landslide":
        defaults["ndvi"] = float(np.clip(defaults["ndvi"] - 0.06, 0.03, 0.85))
        defaults["soil_moisture"] = float(np.clip(defaults["soil_moisture"] + 0.05, 0.05, 0.99))

    values = {}
    for key, default in defaults.items():
        raw_value = feature_overrides.get(key, feature_overrides.get(key.replace("rainfall_intensity", "rainfall_24h_mm"), default))
        try:
            values[key] = float(raw_value)
        except (TypeError, ValueError):
            values[key] = default
    return values


def _predict_score(disaster_type: str, feature_overrides: Optional[Dict[str, float]] = None, bbox: Optional[Tuple[float, float, float, float]] = None) -> Dict[str, object]:
    disaster_type = (disaster_type or "").lower().strip()
    if disaster_type not in {"earthquake", "flood", "landslide"}:
        return {"success": False, "error": "Invalid disaster type"}

    if disaster_type == "earthquake":
        features = _simulate_satellite_features("flood", feature_overrides, bbox)
        score = float(np.clip(0.15 + 0.10 * (1 - features["ndvi"]) + 0.10 * features["soil_moisture"], 0, 1))
        return {
            "success": True,
            "disaster": disaster_type,
            "satellite_score": round(score, 4),
            "risk_level": _risk_level(score),
            "backend": "simulated_satellite_rules",
            "features": features,
            "hazard_breakdown": {"flood_risk": round(score, 4), "landslide_risk": round(score * 0.8, 4)},
        }

    model, meta = _train_model(force=False)
    features = _simulate_satellite_features(disaster_type, feature_overrides, bbox)
    X = pd.DataFrame([features], columns=FEATURE_COLUMNS)
    probabilities = model.predict_proba(X)[0]
    classes = list(model.classes_)
    class_probs = {label: float(prob) for label, prob in zip(classes, probabilities)}
    score = class_probs.get("High", 0.0) + 0.55 * class_probs.get("Medium", 0.0)
    score = float(np.clip(score, 0, 1))

    flood_score = score if disaster_type == "flood" else float(np.clip(score * 0.78, 0, 1))
    landslide_score = score if disaster_type == "landslide" else float(np.clip(score * 0.72, 0, 1))

    return {
        "success": True,
        "disaster": disaster_type,
        "satellite_score": round(score, 4),
        "risk_level": _risk_level(score),
        "backend": "random_forest",
        "features": features,
        "class_probabilities": {k: round(v, 4) for k, v in class_probs.items()},
        "hazard_breakdown": {
            "flood_risk": round(flood_score, 4),
            "landslide_risk": round(landslide_score, 4),
        },
        "model_accuracy": meta.get("accuracy"),
    }


def predict_satellite_risk(disaster_type: str = "", image_path: Optional[str] = None, feature_overrides: Optional[Dict[str, float]] = None) -> Dict[str, object]:
    return _predict_score(disaster_type=disaster_type, feature_overrides=feature_overrides, bbox=None)


def predict_satellite_risk_for_bbox(disaster_type: str, bbox: Tuple[float, float, float, float], image_path: Optional[str] = None, feature_overrides: Optional[Dict[str, float]] = None) -> Dict[str, object]:
    return _predict_score(disaster_type=disaster_type, feature_overrides=feature_overrides, bbox=bbox)
