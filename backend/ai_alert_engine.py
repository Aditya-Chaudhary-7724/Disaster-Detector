"""AI alert engine.

Runs every 6 hours (or on-demand) and generates alerts using:
- ML predictions
- Recent 7-day trend
"""

from __future__ import annotations

import time
from typing import Dict, List

from db import get_conn, get_sync_state, insert_alert, set_sync_state
from predictor import predict_risk

ALERT_INTERVAL_SECONDS = 6 * 60 * 60


def _risk_to_num(level: str) -> int:
    level = (level or "").upper()
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(level, 1)


def _level_from_mag(mag: float) -> str:
    if mag >= 6.0:
        return "HIGH"
    if mag >= 4.5:
        return "MEDIUM"
    return "LOW"


def _fetch_recent_earthquakes(hours: int = 24) -> List[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cutoff = int(time.time() * 1000) - hours * 60 * 60 * 1000
    cur.execute(
        "SELECT * FROM earthquakes WHERE time >= ? ORDER BY time DESC LIMIT 200",
        (cutoff,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _fetch_recent_rows(table: str, days: int = 7) -> List[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cutoff = int(time.time() * 1000) - days * 24 * 60 * 60 * 1000
    cur.execute(f"SELECT * FROM {table} WHERE time >= ? ORDER BY time ASC", (cutoff,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _calc_rising_trend(values: List[float]) -> bool:
    if len(values) < 4:
        return False
    head = sum(values[: len(values) // 2]) / max(1, len(values[: len(values) // 2]))
    tail = sum(values[len(values) // 2 :]) / max(1, len(values[len(values) // 2 :]))
    return tail > head + 0.15


def _earthquake_payload() -> Dict[str, float] | None:
    rows = _fetch_recent_earthquakes(24)
    if not rows:
        return None
    top = rows[0]
    return {
        "disaster": "earthquake",
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
        "seismic_mag": top.get("magnitude", 0),
        "depth_km": top.get("depth", 0),
        "rainfall_24h_mm": 0,
        "soil_moisture": 0.4,
        "slope_deg": 8,
        "ndvi": 0.5,
        "plant_density": 0.5,
    }


def _hydro_payload(table: str, disaster: str) -> Dict[str, float] | None:
    rows = _fetch_recent_rows(table, 2)
    if not rows:
        return None
    top = rows[-1]
    return {
        "disaster": disaster,
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
        "rainfall_24h_mm": top.get("rainfall_24h_mm", 0) or 0,
        "soil_moisture": top.get("soil_moisture", 0.5) or 0.5,
        "slope_deg": top.get("slope_deg", 10) or 10,
        "ndvi": top.get("ndvi", 0.5) or 0.5,
        "plant_density": top.get("plant_density", 0.5) or 0.5,
        "seismic_mag": 0,
        "depth_km": 0,
    }


def _trend_for_disaster(disaster: str) -> bool:
    if disaster == "flood":
        rows = _fetch_recent_rows("floods", 7)
        vals = [float(r.get("rainfall_24h_mm") or 0) / 250.0 + float(r.get("soil_moisture") or 0) for r in rows]
        return _calc_rising_trend(vals)

    if disaster == "landslide":
        rows = _fetch_recent_rows("landslides", 7)
        vals = [
            float(r.get("rainfall_24h_mm") or 0) / 240.0
            + float(r.get("soil_moisture") or 0)
            + float(r.get("slope_deg") or 0) / 60.0
            for r in rows
        ]
        return _calc_rising_trend(vals)

    rows = _fetch_recent_earthquakes(7 * 24)
    vals = [_risk_to_num(_level_from_mag(float(r.get("magnitude") or 0))) for r in rows]
    return _calc_rising_trend(vals)


def _alert_type(disaster: str, watch: bool = False) -> str:
    if disaster == "earthquake":
        return "Earthquake Warning" if not watch else "Earthquake Watch"
    if disaster == "flood":
        return "Flood Alert" if not watch else "Flood Watch"
    return "Landslide Advisory" if not watch else "Landslide Watch"


def _alert_descriptor(score: float) -> tuple[str, str]:
    if score > 0.7:
        return "HIGH", "Warning"
    if score >= 0.4:
        return "MEDIUM", "Watch"
    return "LOW", "Advisory"


def generate_ai_alerts(force: bool = False) -> Dict[str, object]:
    last_sync = float(get_sync_state("ai_alert_last_sync", 0) or 0)
    now = time.time()
    if not force and (now - last_sync) < ALERT_INTERVAL_SECONDS:
        return {
            "success": True,
            "generated": False,
            "reason": "fresh",
            "next_in_sec": int(ALERT_INTERVAL_SECONDS - (now - last_sync)),
            "alerts": [],
        }

    payloads = {
        "earthquake": _earthquake_payload(),
        "flood": _hydro_payload("floods", "flood"),
        "landslide": _hydro_payload("landslides", "landslide"),
    }

    created = []
    created_at = int(time.time() * 1000)

    for disaster, payload in payloads.items():
        if not payload:
            continue

        pred = predict_risk(payload)
        if not pred.get("success"):
            continue

        score = float(pred.get("final_risk_probability") or 0.0)
        level, alert_message_type = _alert_descriptor(score)
        confidence = float(pred.get("confidence") or 0.0)
        rising = _trend_for_disaster(disaster)

        trigger_high = level == "HIGH"
        trigger_watch = level == "MEDIUM" and rising
        trigger_advisory = level == "LOW" and rising and confidence >= 0.35

        if not (trigger_high or trigger_watch or trigger_advisory):
            continue

        watch = trigger_watch and not trigger_high
        alert_label = "RED ALERT" if trigger_high else "ORANGE ALERT" if trigger_watch else "BLUE ALERT"
        location = payload.get("region") or "India risk zone"
        alert = {
            "alert_type": alert_label,
            "type": alert_label,
            "disaster": disaster,
            "region": location,
            "level": level,
            "priority": level,
            "confidence": round(confidence, 4),
            "risk_score": round(score, 4),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created_at / 1000.0)),
            "location": location,
            "message": (
                f"{alert_message_type}: {_alert_type(disaster, watch=watch)} | {level} risk | "
                f"score={score:.2f} | confidence={confidence:.2f} | trend={'rising' if rising else 'stable'}"
            ),
            "lat": payload.get("latitude"),
            "lon": payload.get("longitude"),
            "created_at": created_at,
        }
        created.append(insert_alert(alert))

    set_sync_state("ai_alert_last_sync", now)

    return {
        "success": True,
        "generated": True,
        "alerts": created,
        "count": len(created),
    }
