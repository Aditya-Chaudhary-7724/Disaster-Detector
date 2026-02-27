"""Prediction-driven alert engine (cron-ready, additive).

Usage examples:
  python backend/alert_engine.py --run-once
  python backend/alert_engine.py --run-once --date 2026-02-22

Cron example (daily 01:00):
  0 1 * * * /path/to/python /path/to/backend/alert_engine.py --run-once
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from db import init_db, insert_alert
from research_predictor import predict_hybrid

DATASET_PATH = Path(__file__).parent / "datasets" / "multi_hazard_dataset.csv"
STATE_PATH = Path(__file__).parent / "alert_state.json"

ALERT_TYPE_MAP = {
    "earthquake": "Earthquake Warning",
    "flood": "Flood Watch",
    "landslide": "Landslide Advisory",
}


def _read_state() -> Dict[str, int]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_state(state: Dict[str, int]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _parse_dataset_rows() -> List[dict]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset missing: {DATASET_PATH}. Generate it first.")

    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _select_daily_inputs(rows: List[dict], run_date: datetime) -> Dict[str, dict]:
    """Pick one representative row per disaster type for the requested date.

    If date has no row for a disaster, fallback to latest available row for that disaster.
    """

    target = run_date.strftime("%Y-%m-%d")
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("disaster_type", ""))].append(row)

    selected: Dict[str, dict] = {}
    for disaster_type in ["earthquake", "flood", "landslide"]:
        rows_for_type = grouped.get(disaster_type, [])
        if not rows_for_type:
            continue

        rows_for_type.sort(key=lambda r: r.get("timestamp", ""))
        date_match = [r for r in rows_for_type if str(r.get("timestamp", "")).startswith(target)]
        selected[disaster_type] = date_match[-1] if date_match else rows_for_type[-1]

    return selected


def _to_payload(row: dict) -> dict:
    def to_float(key: str, default: float = 0.0) -> float:
        try:
            return float(row.get(key, default) or default)
        except (TypeError, ValueError):
            return default

    return {
        "disaster_type": row.get("disaster_type", ""),
        "seismic_mag": to_float("seismic_mag"),
        "depth_km": to_float("depth_km"),
        "rainfall_24h_mm": to_float("rainfall_24h_mm"),
        "soil_moisture": to_float("soil_moisture"),
        "slope_deg": to_float("slope_deg"),
        "ndvi": to_float("ndvi", 0.5),
        "plant_density": to_float("plant_density", 0.5),
        "past_event_count": to_float("past_event_count", 0),
        "lat": to_float("latitude"),
        "lon": to_float("longitude"),
    }


def _store_alert(disaster_type: str, prediction: dict, payload: dict, reason: str, run_date: datetime) -> dict:
    alert_type = ALERT_TYPE_MAP.get(disaster_type, disaster_type.title())
    level = str(prediction.get("risk_level", "Medium")).upper()
    score = prediction.get("risk_score", 0)
    message = f"{alert_type}: {level} risk detected (score={score}). {reason}"

    alert = {
        "type": alert_type,
        "level": level,
        "message": message,
        "lat": payload.get("lat"),
        "lon": payload.get("lon"),
        "created_at": int(run_date.timestamp() * 1000),
    }
    insert_alert(alert)
    return alert


def run_daily_prediction(run_date: datetime) -> Dict[str, object]:
    rows = _parse_dataset_rows()
    selected = _select_daily_inputs(rows, run_date)

    state = _read_state()
    created_alerts = []

    init_db()

    for disaster_type, row in selected.items():
        payload = _to_payload(row)
        prediction = predict_hybrid(payload)
        if not prediction.get("success"):
            continue

        risk_level = prediction["risk_level"]
        key = f"{disaster_type}_medium_streak"

        if risk_level == "High":
            state[key] = 0
            created_alerts.append(
                _store_alert(
                    disaster_type,
                    prediction,
                    payload,
                    reason="Immediate alert: High risk threshold crossed.",
                    run_date=run_date,
                )
            )
        elif risk_level == "Medium":
            state[key] = int(state.get(key, 0)) + 1
            if state[key] >= 3:
                created_alerts.append(
                    _store_alert(
                        disaster_type,
                        prediction,
                        payload,
                        reason="Escalation: Medium risk persisted for 3 consecutive runs.",
                        run_date=run_date,
                    )
                )
                state[key] = 0
        else:
            state[key] = 0

    _write_state(state)

    return {
        "success": True,
        "date": run_date.strftime("%Y-%m-%d"),
        "alerts_created": len(created_alerts),
        "alerts": created_alerts,
        "state": state,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run research alert engine.")
    parser.add_argument("--run-once", action="store_true", help="Run one daily cycle.")
    parser.add_argument("--date", type=str, default=None, help="Optional date: YYYY-MM-DD")
    args = parser.parse_args()

    if not args.run_once:
        raise SystemExit("Use --run-once for cron-compatible single execution.")

    run_date = datetime.utcnow()
    if args.date:
        run_date = datetime.strptime(args.date, "%Y-%m-%d")

    result = run_daily_prediction(run_date)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
