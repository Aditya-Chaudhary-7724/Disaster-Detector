"""Additional research APIs.

These routes are additive and do not change existing endpoints.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request

from research_predictor import predict_hybrid

research_bp = Blueprint("research_bp", __name__, url_prefix="/api/research")
DATASET_PATH = Path(__file__).parent / "datasets" / "multi_hazard_dataset.csv"


def _parse_float(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


@research_bp.route("/predict", methods=["POST"])
def research_predict():
    payload = request.get_json(force=True) or {}
    result = predict_hybrid(payload)
    code = 200 if result.get("success") else 400
    return jsonify(result), code


@research_bp.route("/dataset-summary", methods=["GET"])
def dataset_summary():
    if not DATASET_PATH.exists():
        return jsonify({"success": False, "error": "Dataset not found. Run backend/generate_dataset.py"}), 404

    frequency = Counter()
    timeseries_bins = defaultdict(list)
    risk_numeric = {"Low": 0.25, "Medium": 0.55, "High": 0.85}

    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            disaster = str(row.get("disaster_type", "unknown"))
            label = str(row.get("risk_label", "Low"))
            frequency[disaster] += 1

            timestamp = str(row.get("timestamp", ""))
            if timestamp:
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    day_key = dt.strftime("%Y-%m-%d")
                except ValueError:
                    day_key = timestamp[:10]

                score_guess = risk_numeric.get(label, 0.25)
                # Add mild feature-based variation for graph smoothness
                score_guess += min(_parse_float(row, "rainfall_24h_mm") / 1200.0, 0.08)
                score_guess += min(_parse_float(row, "seismic_mag") / 100.0, 0.08)
                score_guess = max(0.0, min(score_guess, 1.0))
                timeseries_bins[day_key].append(score_guess)

    timeseries = [
        {"date": day, "risk_score": round(sum(values) / len(values), 4)}
        for day, values in sorted(timeseries_bins.items())
    ]

    return jsonify(
        {
            "success": True,
            "frequency_distribution": [
                {"disaster_type": key, "count": value}
                for key, value in sorted(frequency.items())
            ],
            "risk_score_timeseries": timeseries,
            "dataset_path": str(DATASET_PATH),
        }
    )
