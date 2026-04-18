"""Automatic AI predictor engines.

Includes:
- Existing global auto predictor (no manual input)
- New spatial cluster-based auto predictor with per-cluster risk
"""

from __future__ import annotations

import time
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans

from db import get_conn
from ml_hybrid_predictor import predict_hybrid_ml
from predictor import (
    compute_rule_risk_earthquake,
    compute_rule_risk_flood,
    compute_rule_risk_landslide,
)
from satellite_predictor import predict_satellite_risk, predict_satellite_risk_for_bbox
try:
    from cnn_satellite import run_auto_cnn_prediction
except Exception:
    def run_auto_cnn_prediction():
        return {"success": False, "flood_prob": 0.0, "landslide_prob": 0.0, "confidence": 0.0}

DATASET_FALLBACK = Path(__file__).parent / "datasets" / "disaster_dataset.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "disasters.db")
_CACHE_TTL_SEC = 300
_SPATIAL_CACHE: Dict[str, Dict[str, object]] = {}
_CLUSTER_HISTORY: Dict[str, List[Dict[str, object]]] = {}


def _risk_level(p: float) -> str:
    if p > 0.7:
        return "High"
    if p >= 0.40:
        return "Medium"
    return "Low"


def _trend_label(values: List[float]) -> str:
    if len(values) < 3:
        return "stable"
    x = np.arange(len(values), dtype=float)
    slope = float(np.polyfit(x, np.asarray(values, dtype=float), 1)[0])
    if slope > 0.015:
        return "increasing"
    if slope < -0.015:
        return "decreasing"
    return "stable"


def _forecast_next_7_days(history: List[float]) -> List[float]:
    values = [float(v) for v in history if v is not None]
    if not values:
        return [0.0] * 7
    x = np.arange(len(values), dtype=float)
    coeffs = np.polyfit(x, np.asarray(values, dtype=float), 1) if len(values) >= 2 else [0.0, values[-1]]
    slope, intercept = float(coeffs[0]), float(coeffs[1])
    out = []
    for day in range(1, 8):
        pred = slope * (len(values) - 1 + day) + intercept
        out.append(round(float(np.clip(pred, 0.0, 1.0)), 4))
    return out


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlon / 2.0) ** 2
    return float(2 * r * np.arcsin(np.sqrt(a)))


def _normalize(v: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return float(np.clip((v - lo) / (hi - lo), 0.0, 1.0))


def _load_db_rows(disaster_type: str, days: int = 7) -> pd.DataFrame:
    conn = get_conn()
    cur = conn.cursor()
    cutoff = int(time.time() * 1000) - days * 24 * 60 * 60 * 1000

    if disaster_type == "earthquake":
        cur.execute(
            """
            SELECT time, latitude, longitude,
                   magnitude AS seismic_magnitude,
                   depth AS depth_km,
                   magnitude,
                   0.0 AS rainfall_24h_mm,
                   0.0 AS soil_moisture,
                   8.0 AS slope_deg,
                   0.5 AS ndvi,
                   0.5 AS plant_density
            FROM earthquakes
            WHERE time >= ?
            ORDER BY time DESC
            LIMIT 600
            """,
            (cutoff,),
        )
    elif disaster_type == "flood":
        cur.execute(
            """
            SELECT time, latitude, longitude,
                   COALESCE(rainfall_24h_mm, 0) AS rainfall_24h_mm,
                   COALESCE(soil_moisture, 0.5) AS soil_moisture,
                   COALESCE(slope_deg, 10) AS slope_deg,
                   COALESCE(ndvi, 0.5) AS ndvi,
                   COALESCE(plant_density, 0.5) AS plant_density,
                   0.0 AS seismic_magnitude,
                   0.0 AS depth_km,
                   0.0 AS magnitude
            FROM floods
            WHERE time >= ?
            ORDER BY time DESC
            LIMIT 600
            """,
            (cutoff,),
        )
    else:
        cur.execute(
            """
            SELECT time, latitude, longitude,
                   COALESCE(rainfall_24h_mm, 0) AS rainfall_24h_mm,
                   COALESCE(soil_moisture, 0.5) AS soil_moisture,
                   COALESCE(slope_deg, 10) AS slope_deg,
                   COALESCE(ndvi, 0.5) AS ndvi,
                   COALESCE(plant_density, 0.5) AS plant_density,
                   0.0 AS seismic_magnitude,
                   0.0 AS depth_km,
                   0.0 AS magnitude
            FROM landslides
            WHERE time >= ?
            ORDER BY time DESC
            LIMIT 600
            """,
            (cutoff,),
        )

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    for col in [
        "latitude",
        "longitude",
        "rainfall_24h_mm",
        "soil_moisture",
        "slope_deg",
        "ndvi",
        "plant_density",
        "seismic_magnitude",
        "depth_km",
        "magnitude",
    ]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df = df.dropna(subset=["latitude", "longitude"])
    return df


def _debug_table_name(disaster_type: str) -> str:
    return {"earthquake": "earthquakes", "flood": "floods", "landslide": "landslides"}.get(disaster_type, "")


def _debug_probe_spatial_source(disaster_type: str) -> Dict[str, object]:
    table = _debug_table_name(disaster_type)
    info: Dict[str, object] = {
        "db_path": DB_PATH,
        "db_exists": os.path.exists(DB_PATH),
        "tables": [],
        "rows_fetched": 0,
        "columns": [],
        "latest_timestamp": None,
        "filter_fallback_used": False,
    }

    print("Disaster type requested:", disaster_type)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            tdf = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            info["tables"] = tdf["name"].tolist()
    except Exception as exc:
        print("DEBUG TABLE LIST ERROR:", exc)
        return info

    if not table:
        return info

    try:
        with sqlite3.connect(DB_PATH) as conn:
            # 7-day filter debug probe
            q = f"SELECT * FROM {table} WHERE time >= (strftime('%s','now','-7 days') * 1000)"
            df = pd.read_sql_query(q, conn)

        print("Rows fetched:", len(df))
        print("Columns:", list(df.columns))
        info["rows_fetched"] = int(len(df))
        info["columns"] = [str(c) for c in df.columns]

        latest_ts = None
        if "timestamp" in df.columns and len(df):
            latest_ts = str(df["timestamp"].max())
            print("Latest timestamp:", latest_ts)
        elif "time" in df.columns and len(df):
            latest_ts = str(df["time"].max())
            print("Latest timestamp:", latest_ts)
        info["latest_timestamp"] = latest_ts

        if df.empty:
            print("WARNING: 7-day filter returned no data. Falling back to full dataset.")
            with sqlite3.connect(DB_PATH) as conn:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            info["rows_fetched"] = int(len(df))
            info["columns"] = [str(c) for c in df.columns]
            info["filter_fallback_used"] = True
    except Exception as exc:
        print("DEBUG DATA PROBE ERROR:", exc)

    return info


def _load_dataset_rows(disaster_type: str, limit: int = 500) -> pd.DataFrame:
    if not DATASET_FALLBACK.exists() or DATASET_FALLBACK.stat().st_size == 0:
        return pd.DataFrame()

    try:
        df = pd.read_csv(DATASET_FALLBACK)
    except Exception:
        return pd.DataFrame()

    if "disaster_type" not in df.columns:
        return pd.DataFrame()

    if "seismic_mag" in df.columns and "seismic_magnitude" not in df.columns:
        df["seismic_magnitude"] = df["seismic_mag"]

    df = df[df["disaster_type"].astype(str).str.lower() == disaster_type].copy()
    if df.empty:
        return pd.DataFrame()

    keep = [
        "latitude",
        "longitude",
        "rainfall_24h_mm",
        "soil_moisture",
        "slope_deg",
        "ndvi",
        "plant_density",
        "seismic_magnitude",
        "depth_km",
    ]
    for col in keep:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
        df["time"] = (ts.astype("int64") // 10**6).fillna(0)
    else:
        df["time"] = 0

    df["magnitude"] = df["seismic_magnitude"]
    return df[["time", *keep, "magnitude"]].tail(limit)


def _aggregate_features(disaster_type: str) -> Dict[str, float]:
    rows = _load_db_rows(disaster_type)
    source = "db"
    if rows.empty:
        rows = _load_dataset_rows(disaster_type)
        source = "dataset"

    if rows.empty:
        raise RuntimeError(f"No usable data found for disaster type: {disaster_type}")

    rows = rows.sort_values("time").reset_index(drop=True)

    for c in ["rainfall_24h_mm", "soil_moisture", "slope_deg", "seismic_magnitude"]:
        rows[f"{c}_roll3"] = rows[c].rolling(window=3, min_periods=1).mean()

    rainfall_7d = float(rows["rainfall_24h_mm"].tail(7).sum())
    soil_trend = float(rows["soil_moisture"].tail(3).mean() - rows["soil_moisture"].head(3).mean()) if len(rows) >= 6 else 0.0
    seismic_freq = float((rows["seismic_magnitude"] >= 4.0).sum() / max(1, min(len(rows), 7)))
    slope_instability = float((rows["slope_deg"].tail(7).mean() / 60.0) * (1.0 - rows["ndvi"].tail(7).mean()))

    agg = {
        "disaster": disaster_type,
        "disaster_type": disaster_type,
        "latitude": float(rows["latitude"].tail(7).mean()),
        "longitude": float(rows["longitude"].tail(7).mean()),
        "rainfall_24h_mm": float(rows["rainfall_24h_mm"].tail(3).mean()),
        "rainfall_7d_mm": rainfall_7d,
        "soil_moisture": float(rows["soil_moisture"].tail(3).mean()),
        "slope_deg": float(rows["slope_deg"].tail(3).mean()),
        "ndvi": float(rows["ndvi"].tail(3).mean()),
        "plant_density": float(rows["plant_density"].tail(3).mean()),
        "seismic_magnitude": float(rows["seismic_magnitude"].tail(3).mean()),
        "seismic_mag": float(rows["seismic_magnitude"].tail(3).mean()),
        "depth_km": float(rows["depth_km"].tail(3).mean()),
        "seismic_activity_frequency": seismic_freq,
        "soil_moisture_trend": soil_trend,
        "slope_instability_index": slope_instability,
        "data_source": source,
    }
    return agg


def _rule_score(disaster_type: str, payload: Dict[str, float]) -> float:
    if disaster_type == "earthquake":
        return float(compute_rule_risk_earthquake(payload)[0])
    if disaster_type == "flood":
        return float(compute_rule_risk_flood(payload)[0])
    return float(compute_rule_risk_landslide(payload)[0])


def run_auto_prediction(disaster_type: str) -> Dict[str, object]:
    disaster_type = str(disaster_type or "").lower().strip()
    if disaster_type not in {"earthquake", "flood", "landslide"}:
        return {"success": False, "error": "Invalid disaster type. Use earthquake/flood/landslide"}

    start = time.perf_counter()
    agg_payload = _aggregate_features(disaster_type)
    rows = _load_db_rows(disaster_type, days=14)
    if rows.empty:
        rows = _load_dataset_rows(disaster_type, limit=100)
    history_scores = []
    if not rows.empty:
        for _, row in rows.tail(14).iterrows():
            history_scores.append(_rule_score(disaster_type, row.to_dict()))
    trend = _trend_label(history_scores)
    future_risk_7_days = _forecast_next_7_days(history_scores[-14:])

    ml = predict_hybrid_ml(agg_payload)
    ml_score = float(ml.get("ml_probability") or 0.0)

    sat = predict_satellite_risk(disaster_type=disaster_type, feature_overrides=agg_payload)
    sat_score = float(sat.get("satellite_score") or 0.0)
    cnn = run_auto_cnn_prediction()
    cnn_score = float(cnn.get("flood_prob") or 0.0) if disaster_type == "flood" else float(cnn.get("landslide_prob") or 0.0) if disaster_type == "landslide" else float(cnn.get("confidence") or 0.0) * 0.5

    rule = _rule_score(disaster_type, agg_payload)

    final = max(0.0, min(1.0, 0.25 * rule + 0.30 * ml_score + 0.25 * sat_score + 0.20 * cnn_score))
    latency_ms = (time.perf_counter() - start) * 1000.0

    explanation = {
        "fusion_formula": "Final=0.25*Rule + 0.30*ML + 0.25*Satellite + 0.20*CNN",
        "rolling_window": "3-sample rolling means over last 7 days",
        "derived_features": {
            "seismic_activity_frequency": agg_payload.get("seismic_activity_frequency"),
            "rainfall_accumulation_7d": agg_payload.get("rainfall_7d_mm"),
            "soil_moisture_trend": agg_payload.get("soil_moisture_trend"),
            "slope_instability_index": agg_payload.get("slope_instability_index"),
        },
        "weather_source": ml.get("weather_source"),
        "dataset_source": agg_payload.get("data_source"),
        "latency_ms": round(latency_ms, 2),
        "trend": trend,
    }

    return {
        "success": True,
        "disaster": disaster_type,
        "rule_score": round(rule, 4),
        "ml_score": round(ml_score, 4),
        "satellite_score": round(sat_score, 4),
        "cnn_score": round(cnn_score, 4),
        "final_risk": round(final, 4),
        "risk_level": _risk_level(final),
        "confidence": round(final * 100.0, 2),
        "trend": trend,
        "future_risk_7_days": future_risk_7_days,
        "explanation": explanation,
        "ml_details": ml,
        "satellite_details": sat,
        "cnn_details": cnn,
    }


def run_global_auto_prediction() -> Dict[str, object]:
    candidates: List[Dict[str, object]] = []
    errors: Dict[str, str] = {}

    for disaster_type in ["earthquake", "flood", "landslide"]:
        try:
            result = run_auto_prediction(disaster_type)
            if result.get("success"):
                candidates.append(result)
            else:
                errors[disaster_type] = str(result.get("error") or "prediction failed")
        except Exception as exc:
            errors[disaster_type] = str(exc)

    if not candidates:
        return {
            "success": False,
            "error": "No auto prediction could be generated from available DB data",
            "details": errors,
        }

    best = max(candidates, key=lambda item: float(item.get("final_risk") or 0.0))
    return {
        "success": True,
        "disaster": best.get("disaster"),
        "disaster_type": best.get("disaster"),
        "risk_score": round(float(best.get("final_risk") or 0.0), 4),
        "risk_level": best.get("risk_level"),
        "confidence": round(float(best.get("confidence") or 0.0) / 100.0, 4),
        "trend": best.get("trend"),
        "explanation": best.get("explanation"),
        "future_risk_7_days": best.get("future_risk_7_days", []),
        "details": best,
        "evaluated_disasters": [
            {
                "disaster_type": item.get("disaster"),
                "risk_score": item.get("final_risk"),
                "risk_level": item.get("risk_level"),
                "confidence": item.get("confidence"),
                "trend": item.get("trend"),
                "future_risk_7_days": item.get("future_risk_7_days", []),
            }
            for item in candidates
        ],
        "errors": errors,
    }


def compute_spatial_features(cluster_df: pd.DataFrame, global_df: pd.DataFrame, disaster_type: str) -> Dict[str, float]:
    cdf = cluster_df.sort_values("time").copy()

    roll7_rain = float(cdf["rainfall_24h_mm"].rolling(window=7, min_periods=1).mean().iloc[-1])
    roll7_soil = float(cdf["soil_moisture"].rolling(window=7, min_periods=1).mean().iloc[-1])
    roll7_slope = float(cdf["slope_deg"].rolling(window=7, min_periods=1).mean().iloc[-1])
    roll7_mag = float(cdf["seismic_magnitude"].rolling(window=7, min_periods=1).mean().iloc[-1])

    vol3_rain = float(cdf["rainfall_24h_mm"].rolling(window=3, min_periods=1).std().fillna(0).iloc[-1])
    vol3_soil = float(cdf["soil_moisture"].rolling(window=3, min_periods=1).std().fillna(0).iloc[-1])

    lat_span = max(0.05, float(cdf["latitude"].max() - cdf["latitude"].min()))
    lon_span = max(0.05, float(cdf["longitude"].max() - cdf["longitude"].min()))
    area = lat_span * lon_span
    density = float(len(cdf) / area)

    seismic_freq = float((cdf["seismic_magnitude"] >= 4.0).sum() / max(1, len(cdf)))
    global_rain_mean = float(global_df["rainfall_24h_mm"].mean()) if not global_df.empty else 0.0
    rainfall_anomaly = float((roll7_rain - global_rain_mean) / max(global_rain_mean, 1.0))

    rainfall_7d_sum = float(cdf["rainfall_24h_mm"].tail(7).sum())

    out = {
        "disaster": disaster_type,
        "disaster_type": disaster_type,
        "latitude": float(cdf["latitude"].mean()),
        "longitude": float(cdf["longitude"].mean()),
        "rainfall_24h_mm": roll7_rain,
        "rainfall_7d_mm": rainfall_7d_sum,
        "soil_moisture": roll7_soil,
        "slope_deg": roll7_slope,
        "ndvi": float(cdf["ndvi"].tail(7).mean()),
        "plant_density": float(cdf["plant_density"].tail(7).mean()),
        "seismic_magnitude": roll7_mag,
        "seismic_mag": roll7_mag,
        "depth_km": float(cdf["depth_km"].tail(7).mean()),
        "rolling_volatility_3d": float((vol3_rain + vol3_soil) / 2.0),
        "cluster_density": density,
        "seismic_frequency_index": seismic_freq,
        "rainfall_anomaly_index": rainfall_anomaly,
        "slope_instability_index": float((roll7_slope / 60.0) * (1.0 - float(cdf["ndvi"].mean()))),
    }
    return out


def _cluster_rows(df: pd.DataFrame, method: str = "kmeans", k: int = 5) -> pd.DataFrame:
    if df.empty:
        return df

    coords = df[["latitude", "longitude"]].to_numpy(dtype=float)

    if method.lower() == "dbscan":
        db = DBSCAN(eps=1.25, min_samples=3)
        labels = db.fit_predict(coords)
        labels = np.where(labels < 0, 999, labels)
    else:
        n_clusters = max(1, min(int(k), len(df)))
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(coords)

    out = df.copy()
    out["cluster_id"] = labels.astype(int)
    return out


def _bbox_from_cluster(cdf: pd.DataFrame) -> Tuple[float, float, float, float]:
    return (
        float(cdf["latitude"].min()),
        float(cdf["latitude"].max()),
        float(cdf["longitude"].min()),
        float(cdf["longitude"].max()),
    )


def _cache_key(disaster_type: str, method: str, k: int) -> str:
    return f"{disaster_type}:{method.lower()}:{int(k)}"


def _cache_key_local(disaster_type: str, radius_km: int, lat: float | None, lon: float | None) -> str:
    lat_key = "auto" if lat is None else f"{lat:.2f}"
    lon_key = "auto" if lon is None else f"{lon:.2f}"
    return f"local:{disaster_type}:{radius_km}:{lat_key}:{lon_key}"


def _get_cached(key: str):
    item = _SPATIAL_CACHE.get(key)
    if not item:
        return None
    if (time.time() - float(item["ts"])) > _CACHE_TTL_SEC:
        _SPATIAL_CACHE.pop(key, None)
        return None
    return item["data"]


def _put_cache(key: str, data: Dict[str, object]) -> None:
    _SPATIAL_CACHE[key] = {"ts": time.time(), "data": data}


def _record_cluster_history(disaster: str, cluster_id: int, risk_score: float) -> None:
    key = f"{disaster}:{cluster_id}"
    history = _CLUSTER_HISTORY.setdefault(key, [])
    history.append({"timestamp": int(time.time() * 1000), "risk_score": round(risk_score, 4), "disaster": disaster})
    if len(history) > 200:
        del history[:-200]


def get_cluster_risk_trend(cluster_id: int) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    target = f":{cluster_id}"
    for key, rows in _CLUSTER_HISTORY.items():
        if key.endswith(target):
            out.extend(rows[-40:])
    out.sort(key=lambda r: r["timestamp"])
    return out[-80:]


def _row_risk_hint(disaster_type: str, row: Dict[str, object]) -> float:
    if disaster_type == "earthquake":
        return _rule_score(disaster_type, row)
    risk_map = {"LOW": 0.30, "MEDIUM": 0.60, "HIGH": 0.85}
    risk_label = str(row.get("risk") or "").upper()
    if risk_label in risk_map:
        return float(risk_map[risk_label])
    return _rule_score(disaster_type, row)


def _pick_local_center(rows: pd.DataFrame, disaster_type: str, lat: float | None = None, lon: float | None = None) -> Dict[str, float]:
    if lat is not None and lon is not None:
        return {"latitude": float(lat), "longitude": float(lon)}

    ranked = rows.copy()
    ranked["risk_hint"] = ranked.apply(lambda r: _row_risk_hint(disaster_type, r.to_dict()), axis=1)
    ranked = ranked.sort_values(["risk_hint", "time"], ascending=[False, False])
    top = ranked.iloc[0]
    return {"latitude": float(top["latitude"]), "longitude": float(top["longitude"])}


def _filter_local_rows(rows: pd.DataFrame, center_lat: float, center_lon: float, radius_km: float) -> pd.DataFrame:
    if rows.empty:
        return rows
    local = rows.copy()
    local["distance_km"] = local.apply(
        lambda r: _haversine_km(center_lat, center_lon, float(r["latitude"]), float(r["longitude"])),
        axis=1,
    )
    local = local[local["distance_km"] <= radius_km].copy()
    return local.sort_values("distance_km")


def _cell_feature_vector(local_rows: pd.DataFrame, disaster_type: str, cell_lat: float, cell_lon: float, radius_km: float) -> Dict[str, float]:
    if local_rows.empty:
        return {
            "latitude": cell_lat,
            "longitude": cell_lon,
            "rainfall_24h_mm": 0.0,
            "soil_moisture": 0.0,
            "slope_deg": 0.0,
            "ndvi": 0.5,
            "seismic_magnitude": 0.0,
            "depth_km": 0.0,
            "neighbor_influence": 0.0,
            "risk_score": 0.0,
            "reasons": ["Insufficient nearby observations"],
        }

    working = local_rows.copy()
    working["cell_distance_km"] = working.apply(
        lambda r: _haversine_km(cell_lat, cell_lon, float(r["latitude"]), float(r["longitude"])),
        axis=1,
    )
    working = working[working["cell_distance_km"] <= max(25.0, radius_km * 0.6)].copy()
    if working.empty:
        return {
            "latitude": cell_lat,
            "longitude": cell_lon,
            "rainfall_24h_mm": 0.0,
            "soil_moisture": 0.0,
            "slope_deg": 0.0,
            "ndvi": 0.5,
            "seismic_magnitude": 0.0,
            "depth_km": 0.0,
            "neighbor_influence": 0.0,
            "risk_score": 0.0,
            "reasons": ["No nearby events inside local analysis radius"],
        }

    weights = 1.0 / (working["cell_distance_km"].to_numpy(dtype=float) + 5.0)
    weights = weights / np.sum(weights)

    def wavg(column: str, default: float = 0.0) -> float:
        values = pd.to_numeric(working.get(column, default), errors="coerce").fillna(default).to_numpy(dtype=float)
        return float(np.sum(values * weights))

    rainfall = wavg("rainfall_24h_mm", 0.0)
    soil = wavg("soil_moisture", 0.0)
    slope = wavg("slope_deg", 0.0)
    ndvi = wavg("ndvi", 0.5)
    seismic = wavg("seismic_magnitude", 0.0)
    depth = wavg("depth_km", 60.0)
    neighbor_vals = np.array([_row_risk_hint(disaster_type, row) for row in working.to_dict("records")], dtype=float)
    neighbor_influence = float(np.sum(neighbor_vals * weights))

    rain_n = _normalize(rainfall, 0.0, 220.0)
    soil_n = _normalize(soil, 0.0, 1.0)
    slope_n = _normalize(slope, 0.0, 55.0)
    ndvi_inv = 1.0 - _normalize(ndvi, 0.0, 1.0)
    seismic_n = _normalize(seismic, 0.0, 7.0)
    depth_inv = 1.0 - _normalize(depth, 0.0, 300.0)

    if disaster_type == "flood":
        components = {
            "High rainfall + soil saturation detected": 0.36 * rain_n + 0.28 * soil_n,
            "Low vegetation cover increased runoff": 0.16 * ndvi_inv,
            "Nearby flood activity increased risk": 0.20 * neighbor_influence,
        }
        base = 0.36 * rain_n + 0.28 * soil_n + 0.16 * ndvi_inv
    elif disaster_type == "landslide":
        components = {
            "High rainfall + soil saturation detected": 0.24 * rain_n + 0.22 * soil_n,
            "Steep terrain instability detected": 0.24 * slope_n,
            "Nearby landslide activity increased risk": 0.20 * neighbor_influence,
        }
        base = 0.24 * rain_n + 0.22 * soil_n + 0.24 * slope_n + 0.10 * ndvi_inv
    else:
        components = {
            "Elevated seismic activity detected": 0.42 * seismic_n,
            "Shallow quake profile increased impact": 0.16 * depth_inv,
            "Nearby earthquake activity increased risk": 0.24 * neighbor_influence,
        }
        base = 0.42 * seismic_n + 0.16 * depth_inv

    risk = float(np.clip(base + 0.24 * neighbor_influence, 0.0, 1.0))
    reasons = [text for text, _ in sorted(components.items(), key=lambda item: item[1], reverse=True)[:2]]
    return {
        "latitude": cell_lat,
        "longitude": cell_lon,
        "rainfall_24h_mm": rainfall,
        "soil_moisture": soil,
        "slope_deg": slope,
        "ndvi": ndvi,
        "seismic_magnitude": seismic,
        "depth_km": depth,
        "neighbor_influence": round(neighbor_influence, 4),
        "risk_score": round(risk, 4),
        "reasons": reasons,
    }


def _generate_local_grid(center_lat: float, center_lon: float, radius_km: float) -> List[Tuple[float, float]]:
    lat_step = 0.18
    lon_step = 0.18 / max(np.cos(np.radians(center_lat)), 0.3)
    lat_radius_deg = radius_km / 111.0
    lon_radius_deg = radius_km / (111.0 * max(np.cos(np.radians(center_lat)), 0.3))

    coords: List[Tuple[float, float]] = []
    lat = center_lat - lat_radius_deg
    while lat <= center_lat + lat_radius_deg + 1e-9:
        lon = center_lon - lon_radius_deg
        while lon <= center_lon + lon_radius_deg + 1e-9:
            if _haversine_km(center_lat, center_lon, lat, lon) <= radius_km:
                coords.append((round(float(lat), 5), round(float(lon), 5)))
            lon += lon_step
        lat += lat_step
    return coords


def _cluster_danger_zones(grid_df: pd.DataFrame) -> List[Dict[str, object]]:
    risky = grid_df[grid_df["risk_score"] >= 0.4].copy()
    if risky.empty:
        return []
    coords = risky[["lat", "lng"]].to_numpy(dtype=float)
    labels = DBSCAN(eps=0.22, min_samples=2).fit_predict(coords)
    risky["zone_id"] = labels
    zones: List[Dict[str, object]] = []
    for zone_id, zone_df in risky.groupby("zone_id"):
        centroid_lat = float(zone_df["lat"].mean())
        centroid_lon = float(zone_df["lng"].mean())
        avg_risk = float(zone_df["risk_score"].mean())
        zones.append(
            {
                "zone_id": int(zone_id),
                "centroid": {"lat": round(centroid_lat, 5), "lng": round(centroid_lon, 5)},
                "risk_score": round(avg_risk, 4),
                "risk_level": _risk_level(avg_risk),
                "cell_count": int(len(zone_df)),
            }
        )
    zones.sort(key=lambda item: item["risk_score"], reverse=True)
    return zones


def run_auto_prediction_spatial(disaster_type: str, method: str = "kmeans", k: int = 5, debug: bool = False) -> Dict[str, object]:
    disaster_type = str(disaster_type or "").lower().strip()
    if disaster_type not in {"earthquake", "flood", "landslide"}:
        return {"success": False, "error": "Invalid disaster type. Use earthquake/flood/landslide"}

    debug_info: Dict[str, object] = {}
    if debug:
        debug_info = _debug_probe_spatial_source(disaster_type)

    try:
        radius_km = int(max(50, min(100, int(k) * 15)))
    except Exception:
        radius_km = 75
    key = _cache_key_local(disaster_type, radius_km, None, None)
    cached = _get_cached(key)
    if cached:
        out = {**cached, "cached": True}
        if debug:
            out["debug"] = {
                **debug_info,
                "model_file_exists": os.path.exists(os.path.join(BASE_DIR, "models", "ml_model.pkl")),
                "satellite_model_exists": os.path.exists(os.path.join(BASE_DIR, "models", "satellite_model.h5")),
            }
        return out

    start = time.perf_counter()
    if debug:
        print("Loading ML model...")
        print("Model file exists:", os.path.exists(os.path.join(BASE_DIR, "models", "ml_model.pkl")))
        print("Loading satellite model...")
        print("Satellite model exists:", os.path.exists(os.path.join(BASE_DIR, "models", "satellite_model.h5")))

    rows = _load_db_rows(disaster_type)
    source = "db"
    if rows.empty:
        rows = _load_dataset_rows(disaster_type)
        source = "dataset"

    if rows.empty:
        return {"success": False, "error": "No records available for spatial clustering"}

    center = _pick_local_center(rows, disaster_type)
    center_lat = float(center["latitude"])
    center_lon = float(center["longitude"])
    local_rows = _filter_local_rows(rows, center_lat, center_lon, radius_km)
    if local_rows.empty:
        return {"success": False, "error": "No records available inside local radius"}

    grid_points = _generate_local_grid(center_lat, center_lon, radius_km)
    grid_cells: List[Dict[str, object]] = []
    explanation_pool: List[str] = []
    for lat, lon in grid_points:
        cell = _cell_feature_vector(local_rows, disaster_type, lat, lon, radius_km)
        cell_obj = {
            "lat": lat,
            "lng": lon,
            "risk_score": cell["risk_score"],
            "risk_level": _risk_level(float(cell["risk_score"])),
            "neighbor_influence": cell["neighbor_influence"],
            "reasons": cell["reasons"],
        }
        grid_cells.append(cell_obj)
        explanation_pool.extend(cell["reasons"])

    grid_df = pd.DataFrame(grid_cells)
    danger_zones = _cluster_danger_zones(grid_df)
    alerts = [
        {
            "zone_id": zone["zone_id"],
            "risk_score": zone["risk_score"],
            "risk_level": zone["risk_level"],
            "message": f"Danger zone {zone['zone_id']} exceeds local threshold",
        }
        for zone in danger_zones
        if zone["risk_score"] >= 0.7
    ]
    for zone in danger_zones:
        _record_cluster_history(disaster_type, int(zone["zone_id"]), float(zone["risk_score"]))

    top_explanations = []
    for item in explanation_pool:
        if item not in top_explanations:
            top_explanations.append(item)
        if len(top_explanations) >= 3:
            break

    payload = {
        "success": True,
        "disaster": disaster_type,
        "analysis_center": {"lat": round(center_lat, 5), "lng": round(center_lon, 5)},
        "radius_km": radius_km,
        "local_event_count": int(len(local_rows)),
        "grid_cells": grid_cells,
        "danger_zones": danger_zones,
        "cluster_alerts": alerts,
        "explanations": top_explanations,
        "meta": {
            "model": "localized_risk_grid",
            "source": source,
            "window_days": 14,
            "latency_ms": round((time.perf_counter() - start) * 1000.0, 2),
            "cache_ttl_sec": _CACHE_TTL_SEC,
            "risk_equation": "Risk(x,y)=Σ(Wi*Fi)+NeighborInfluence",
            "neighbor_influence": "Inverse-distance weighted nearby disaster risks",
        },
    }

    if debug:
        payload["debug"] = {
            **debug_info,
            "rows_fetched": int(len(rows)),
            "local_rows": int(len(local_rows)),
            "grid_cell_count": int(len(grid_cells)),
            "db_exists": os.path.exists(DB_PATH),
        }

    _put_cache(key, payload)
    return payload
