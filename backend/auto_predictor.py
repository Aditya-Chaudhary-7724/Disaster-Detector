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

DATASET_FALLBACK = Path(__file__).parent / "datasets" / "disaster_dataset.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "disasters.db")
_CACHE_TTL_SEC = 300
_SPATIAL_CACHE: Dict[str, Dict[str, object]] = {}
_CLUSTER_HISTORY: Dict[str, List[Dict[str, object]]] = {}


def _risk_level(p: float) -> str:
    if p >= 0.75:
        return "High"
    if p >= 0.40:
        return "Medium"
    return "Low"


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

    ml = predict_hybrid_ml(agg_payload)
    ml_score = float(ml.get("ml_probability") or 0.0)

    sat = predict_satellite_risk(disaster_type=disaster_type)
    sat_score = float(sat.get("satellite_score") or 0.0)

    rule = _rule_score(disaster_type, agg_payload)

    final = max(0.0, min(1.0, 0.3 * rule + 0.4 * ml_score + 0.3 * sat_score))
    latency_ms = (time.perf_counter() - start) * 1000.0

    explanation = {
        "fusion_formula": "Final=0.3*Rule + 0.4*ML + 0.3*Satellite",
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
    }

    return {
        "success": True,
        "disaster": disaster_type,
        "rule_score": round(rule, 4),
        "ml_score": round(ml_score, 4),
        "satellite_score": round(sat_score, 4),
        "final_risk": round(final, 4),
        "risk_level": _risk_level(final),
        "confidence": round(final * 100.0, 2),
        "explanation": explanation,
        "ml_details": ml,
        "satellite_details": sat,
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


def run_auto_prediction_spatial(disaster_type: str, method: str = "kmeans", k: int = 5, debug: bool = False) -> Dict[str, object]:
    disaster_type = str(disaster_type or "").lower().strip()
    if disaster_type not in {"earthquake", "flood", "landslide"}:
        return {"success": False, "error": "Invalid disaster type. Use earthquake/flood/landslide"}

    debug_info: Dict[str, object] = {}
    if debug:
        debug_info = _debug_probe_spatial_source(disaster_type)

    key = _cache_key(disaster_type, method, k)
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

    clustered = _cluster_rows(rows, method=method, k=k)

    clusters_out: List[Dict[str, object]] = []
    heatmap: List[List[float]] = []
    alerts: List[Dict[str, object]] = []

    for cid, cdf in clustered.groupby("cluster_id"):
        feats = compute_spatial_features(cdf, clustered, disaster_type)

        rule = _rule_score(disaster_type, feats)
        ml = predict_hybrid_ml(feats)
        ml_score = float(ml.get("ml_probability") or 0.0)

        bbox = _bbox_from_cluster(cdf)
        sat = predict_satellite_risk_for_bbox(disaster_type=disaster_type, bbox=bbox)
        sat_score = float(sat.get("satellite_score") or 0.0)

        final = max(0.0, min(1.0, 0.3 * rule + 0.4 * ml_score + 0.3 * sat_score))
        centroid_lat = float(cdf["latitude"].mean())
        centroid_lon = float(cdf["longitude"].mean())
        level = _risk_level(final)

        cluster_obj = {
            "cluster_id": int(cid),
            "centroid": {"lat": round(centroid_lat, 5), "lon": round(centroid_lon, 5)},
            "risk_score": round(final, 4),
            "risk_level": level,
            "confidence": round(final, 4),
            "rule_score": round(rule, 4),
            "ml_score": round(ml_score, 4),
            "satellite_score": round(sat_score, 4),
            "size": int(len(cdf)),
            "bbox": {
                "min_lat": round(bbox[0], 5),
                "max_lat": round(bbox[1], 5),
                "min_lon": round(bbox[2], 5),
                "max_lon": round(bbox[3], 5),
            },
        }
        clusters_out.append(cluster_obj)
        heatmap.append([centroid_lat, centroid_lon, final])

        if final > 0.7:
            alerts.append(
                {
                    "cluster_id": int(cid),
                    "risk_score": round(final, 4),
                    "risk_level": level,
                    "message": f"Cluster {cid} exceeds alert threshold",
                }
            )

        _record_cluster_history(disaster_type, int(cid), final)

    clusters_out.sort(key=lambda x: x["cluster_id"])

    payload = {
        "success": True,
        "disaster": disaster_type,
        "clusters": clusters_out,
        "heatmap": heatmap,
        "cluster_alerts": alerts,
        "meta": {
            "clustering": method.lower(),
            "k": int(k),
            "source": source,
            "window_days": 7,
            "latency_ms": round((time.perf_counter() - start) * 1000.0, 2),
            "cache_ttl_sec": _CACHE_TTL_SEC,
            "fusion": "Final=0.3*Rule + 0.4*ML + 0.3*Satellite",
        },
    }

    if debug:
        payload["debug"] = {
            **debug_info,
            "rows_fetched": int(len(rows)),
            "db_exists": os.path.exists(DB_PATH),
        }

    _put_cache(key, payload)
    return payload
