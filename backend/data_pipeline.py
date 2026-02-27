"""Data synchronization pipeline for multi-hazard inputs.

- Earthquake sync from USGS every 6h
- Flood proxy generation every 24h
- Landslide proxy generation every 24h
"""

from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime, timedelta

import requests

from db import (
    get_sync_state,
    insert_earthquake,
    insert_flood,
    insert_landslide,
    set_sync_state,
)

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"

SYNC_EARTHQUAKE_SECONDS = 6 * 60 * 60
SYNC_FLOOD_SECONDS = 24 * 60 * 60
SYNC_LANDSLIDE_SECONDS = 24 * 60 * 60

# India-focused regions for hydro-meteorological proxy generation
FLOOD_REGIONS = [
    {"place": "Assam - Guwahati", "lat": 26.1445, "lon": 91.7362},
    {"place": "Bihar - Patna", "lat": 25.5941, "lon": 85.1376},
    {"place": "West Bengal - Siliguri", "lat": 26.7271, "lon": 88.3953},
    {"place": "Kerala - Kottayam", "lat": 9.5916, "lon": 76.5222},
    {"place": "UP - Lucknow", "lat": 26.8467, "lon": 80.9462},
]

LANDSLIDE_REGIONS = [
    {"place": "Sikkim - Gangtok Hills", "lat": 27.3389, "lon": 88.6065, "slope": 42},
    {"place": "Himachal - Shimla", "lat": 31.1048, "lon": 77.1734, "slope": 38},
    {"place": "Uttarakhand - Nainital", "lat": 29.3803, "lon": 79.4636, "slope": 40},
    {"place": "Meghalaya - Shillong", "lat": 25.5788, "lon": 91.8933, "slope": 36},
    {"place": "Nilgiris - Ooty", "lat": 11.4102, "lon": 76.6950, "slope": 33},
]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _stable_id(prefix: str, date_key: str, place: str) -> str:
    digest = hashlib.md5(f"{prefix}:{date_key}:{place}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{date_key}-{digest}"


def _is_india_region(lat: float, lon: float) -> bool:
    # Approx India bounds (including NE and islands window)
    return 6.0 <= lat <= 38.5 and 67.0 <= lon <= 98.5


def sync_earthquakes(force: bool = False) -> dict:
    last_sync = float(get_sync_state("earthquake_last_sync", 0) or 0)
    now = time.time()

    if not force and (now - last_sync) < SYNC_EARTHQUAKE_SECONDS:
        return {"success": True, "synced": False, "reason": "fresh", "next_in_sec": int(SYNC_EARTHQUAKE_SECONDS - (now - last_sync))}

    try:
        response = requests.get(USGS_URL, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return {"success": False, "synced": False, "error": str(exc)}

    inserted = 0
    updated_at = _now_ms()
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates") or [None, None, None]

        if coords[0] is None or coords[1] is None:
            continue

        lon = float(coords[0])
        lat = float(coords[1])
        depth = float(coords[2] or 0)
        place = str(props.get("place") or "")

        if not (_is_india_region(lat, lon) or "india" in place.lower()):
            continue

        insert_earthquake(
            {
                "id": feature.get("id"),
                "place": place,
                "magnitude": float(props.get("mag") or 0),
                "depth": depth,
                "time": int(props.get("time") or updated_at),
                "latitude": lat,
                "longitude": lon,
                "last_updated": updated_at,
            }
        )
        inserted += 1

    set_sync_state("earthquake_last_sync", now)
    set_sync_state("earthquake_last_updated_ms", updated_at)
    return {"success": True, "synced": True, "count": inserted, "last_updated": updated_at}


def _imd_risk_from_rainfall(rainfall_24h_mm: float) -> str:
    # Simplified IMD-style heavy rainfall buckets.
    if rainfall_24h_mm >= 204:
        return "HIGH"
    if rainfall_24h_mm >= 115:
        return "MEDIUM"
    return "LOW"


def sync_floods(force: bool = False) -> dict:
    last_sync = float(get_sync_state("flood_last_sync", 0) or 0)
    now = time.time()
    if not force and (now - last_sync) < SYNC_FLOOD_SECONDS:
        return {"success": True, "synced": False, "reason": "fresh"}

    today = datetime.utcnow().strftime("%Y%m%d")
    rng = random.Random(int(today))
    current_ms = _now_ms()

    count = 0
    for region in FLOOD_REGIONS:
        rainfall = round(max(0.0, rng.gauss(115, 55)), 2)
        soil_m = round(min(0.99, max(0.2, rng.gauss(0.66, 0.12))), 3)
        ndvi = round(min(0.9, max(0.15, rng.gauss(0.54, 0.1))), 3)
        slope = round(min(20, max(1, rng.gauss(7, 3))), 2)
        plant_density = round(min(0.95, max(0.08, 0.2 + 0.7 * ndvi + rng.uniform(-0.1, 0.1))), 3)

        flood = {
            "id": _stable_id("flood", today, region["place"]),
            "place": region["place"],
            "risk": _imd_risk_from_rainfall(rainfall),
            "time": current_ms,
            "latitude": region["lat"],
            "longitude": region["lon"],
            "rainfall_24h_mm": rainfall,
            "soil_moisture": soil_m,
            "slope_deg": slope,
            "ndvi": ndvi,
            "plant_density": plant_density,
        }
        insert_flood(flood)
        count += 1

    set_sync_state("flood_last_sync", now)
    set_sync_state("flood_last_updated_ms", current_ms)
    return {"success": True, "synced": True, "count": count, "last_updated": current_ms}


def _landslide_risk(rainfall: float, slope: float, soil_m: float, ndvi: float) -> str:
    score = 0
    if rainfall >= 140:
        score += 2
    elif rainfall >= 80:
        score += 1

    if slope >= 38:
        score += 2
    elif slope >= 28:
        score += 1

    if soil_m >= 0.75:
        score += 2
    elif soil_m >= 0.6:
        score += 1

    if ndvi < 0.35:
        score += 1

    if score >= 6:
        return "HIGH"
    if score >= 3:
        return "MEDIUM"
    return "LOW"


def sync_landslides(force: bool = False) -> dict:
    last_sync = float(get_sync_state("landslide_last_sync", 0) or 0)
    now = time.time()
    if not force and (now - last_sync) < SYNC_LANDSLIDE_SECONDS:
        return {"success": True, "synced": False, "reason": "fresh"}

    today = datetime.utcnow().strftime("%Y%m%d")
    rng = random.Random(int(today) + 99)
    current_ms = _now_ms()

    count = 0
    for region in LANDSLIDE_REGIONS:
        rainfall = round(max(0.0, rng.gauss(95, 45)), 2)
        soil_m = round(min(0.98, max(0.22, rng.gauss(0.68, 0.14))), 3)
        slope = round(min(58, max(12, rng.gauss(region["slope"], 5.5))), 2)
        ndvi = round(min(0.9, max(0.12, rng.gauss(0.58, 0.11))), 3)
        plant_density = round(min(0.95, max(0.08, 0.18 + 0.74 * ndvi + rng.uniform(-0.1, 0.1))), 3)

        landslide = {
            "id": _stable_id("landslide", today, region["place"]),
            "place": region["place"],
            "risk": _landslide_risk(rainfall, slope, soil_m, ndvi),
            "time": current_ms,
            "latitude": region["lat"],
            "longitude": region["lon"],
            "rainfall_24h_mm": rainfall,
            "soil_moisture": soil_m,
            "slope_deg": slope,
            "ndvi": ndvi,
            "plant_density": plant_density,
        }
        insert_landslide(landslide)
        count += 1

    set_sync_state("landslide_last_sync", now)
    set_sync_state("landslide_last_updated_ms", current_ms)
    return {"success": True, "synced": True, "count": count, "last_updated": current_ms}


def sync_all_if_due() -> dict:
    out = {}
    try:
        out["earthquakes"] = sync_earthquakes(force=False)
    except Exception as exc:
        out["earthquakes"] = {"success": False, "error": str(exc)}

    try:
        out["floods"] = sync_floods(force=False)
    except Exception as exc:
        out["floods"] = {"success": False, "error": str(exc)}

    try:
        out["landslides"] = sync_landslides(force=False)
    except Exception as exc:
        out["landslides"] = {"success": False, "error": str(exc)}

    return out
