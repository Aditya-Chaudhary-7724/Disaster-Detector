from __future__ import annotations

import os
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

from flask import Flask, jsonify, request
from flask_cors import CORS

from db import get_alerts, get_predictions, get_validation_metrics, init_db, insert_alert
from model import (
    ALERT_THRESHOLD,
    MODEL_ALGORITHM,
    MODEL_FORMULA,
    FEATURE_NAMES,
    get_dashboard_payload,
    get_dataset_metadata,
    get_disaster_items,
    get_model_metrics,
    list_regions,
)
from predictor import get_available_regions, predict_risk

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
init_db()


MITIGATION_GUIDE = {
    "Flood": [
        "Move to higher ground when heavy rain continues.",
        "Avoid driving through waterlogged roads.",
        "Keep documents and medicines in waterproof storage.",
    ],
    "Landslide": [
        "Watch for cracks, tilted trees, or falling rocks.",
        "Avoid steep slopes during intense rainfall.",
        "Follow local evacuation notices immediately.",
    ],
    "Urban Heat / Seismic": [
        "Review earthquake safety and open evacuation points.",
        "Keep water, torch, and a charged phone ready.",
        "Stay updated with district disaster advisories.",
    ],
}


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def _generate_region_alerts() -> list[dict]:
    alerts = []
    for region in get_available_regions():
        if region["risk_score"] < ALERT_THRESHOLD:
            continue
        alerts.append(
            insert_alert(
                {
                    "region": region["region"],
                    "risk_score": region["risk_score"],
                    "level": region["risk_level"].upper(),
                    "message": f"{region['region']} has a {region['risk_level']} predicted disaster risk.",
                    "created_at": request.headers.get("X-Request-Time") or datetime.utcnow().isoformat(),
                }
            )
        )
    return alerts


@app.route("/")
def home():
    return jsonify({"message": "Disaster Prediction System backend is running."})


@app.route("/api/test", methods=["GET"])
def test():
    return jsonify({"status": "Backend working"})


@app.route("/api/regions", methods=["GET"])
def api_regions():
    return jsonify({"success": True, "regions": get_available_regions()})


@app.route("/api/map", methods=["GET"])
def api_map():
    disaster = str(request.args.get("disaster", "flood")).lower()
    if disaster not in {"flood", "earthquake", "landslide"}:
        return jsonify({"success": False, "error": "Invalid disaster type"}), 400
    return jsonify({"success": True, "disaster": disaster, "items": get_disaster_items(disaster)})


@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(silent=True) or {}
    result = predict_risk(payload)
    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(
        {
            "success": True,
            "region": result["region"],
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "confidence": result["confidence"],
            "algorithm": result["algorithm"],
            "method": result["method"],
            "formula": result["formula"],
            "final_risk_probability": result["final_risk_probability"],
            "ml_probability": result["ml_probability"],
            "ml_score": result["ml_score"],
            "temporal_factor": result["temporal_factor"],
            "temporal_score": result["temporal_score"],
            "spatial_influence": result["spatial_influence"],
            "spatial_score": result["spatial_score"],
            "rule_score": result["rule_score"],
            "feature_importance": result["feature_importance"],
            "top_features": result["top_features"],
            "explanation": result["explanation"],
            "human_explanation": result["human_explanation"],
            "analysis": result["analysis"],
            "input_features": result["input_features"],
            "validation": result["validation"],
            "alert_created": result["alert_created"],
            "alert": result["alert"],
            "result": result,
        }
    )


@app.route("/api/run-alert-check", methods=["POST"])
def api_run_alert_check():
    payload = request.get_json(silent=True) or {}
    result = predict_risk(payload)
    if not result.get("success"):
        return jsonify(result), 400
    return jsonify(
        {
            "success": True,
            "alert_created": result["alert_created"],
            "alert": result["alert"],
            "result": result,
        }
    )


@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    return jsonify(get_alerts())


@app.route("/api/alerts/generate", methods=["POST"])
def api_generate_alerts():
    alerts = _generate_region_alerts()
    return jsonify({"success": True, "count": len(alerts), "alerts": alerts})


@app.route("/api/validation", methods=["GET"])
def api_validation():
    return jsonify({"success": True, **get_validation_metrics()})


@app.route("/api/model-info", methods=["GET"])
def api_model_info():
    return jsonify(
        {
            "success": True,
            "model": MODEL_ALGORITHM,
            "algorithm": MODEL_ALGORITHM,
            "formula": MODEL_FORMULA,
            "features": FEATURE_NAMES,
            "regions": [item["region"] for item in get_available_regions()],
            "training_metrics": get_model_metrics(),
            "datasets": get_dataset_metadata(),
        }
    )


@app.route("/api/mitigation", methods=["GET"])
def api_mitigation_all():
    items = []
    for region in list_regions():
        hazard = region["primary_hazard"]
        items.append(
            {
                "region": region["region"],
                "primary_hazard": hazard,
                "tips": MITIGATION_GUIDE.get(hazard, []),
                "emergency_contacts": [
                    {"label": "Police", "number": "100"},
                    {"label": "Ambulance", "number": "102"},
                    {"label": "Fire", "number": "101"},
                ],
            }
        )
    return jsonify({"success": True, "items": items})


@app.route("/api/mitigation/<disaster>", methods=["GET"])
def api_mitigation(disaster: str):
    key = str(disaster).replace("-", " ").title()
    return jsonify(
        {
            "success": True,
            "disaster": key,
            "tips": MITIGATION_GUIDE.get(key, []),
            "emergency_contacts": ["National Emergency: 112", "Ambulance: 108", "Police: 100"],
        }
    )


@app.route("/api/earthquakes", methods=["GET"])
def api_earthquakes():
    return jsonify(get_disaster_items("earthquake"))


@app.route("/api/floods", methods=["GET"])
def api_floods():
    return jsonify(get_disaster_items("flood"))


@app.route("/api/landslides", methods=["GET"])
def api_landslides():
    return jsonify(get_disaster_items("landslide"))


@app.route("/api/performance", methods=["GET"])
def api_performance():
    return jsonify(
        {
            "success": True,
            "training_metrics": get_model_metrics(),
            "validation_metrics": get_validation_metrics(),
            "prediction_count": len(get_predictions(500)),
            "alert_count": len(get_alerts(500)),
        }
    )


@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    disaster = str(request.args.get("disaster", "flood")).lower()
    if disaster not in {"flood", "earthquake", "landslide"}:
        return jsonify({"success": False, "error": "Invalid disaster type"}), 400

    payload = get_dashboard_payload(disaster)
    return jsonify(
        {
            "success": True,
            **payload,
            "validation": get_validation_metrics(),
        }
    )


@app.route("/api/high-risk-location", methods=["GET"])
def api_high_risk_location():
    items = sorted(get_available_regions(), key=lambda item: item["risk_score"], reverse=True)
    top = items[0]
    return jsonify(
        {
            "success": True,
            "region": top["region"],
            "location_name": top["region"],
            "lat": top["lat"],
            "lng": top["lon"],
            "risk_score": top["risk_score"],
            "risk_level": top["risk_level"],
        }
    )


@app.route("/api/nearest-risks", methods=["GET"])
def api_nearest_risks():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "lat and lon query params are required"}), 400

    items = []
    for region in get_available_regions():
        items.append(
            {
                "region": region["region"],
                "disaster": region["primary_hazard"],
                "title": region["region"],
                "distance_km": round(_distance_km(lat, lon, region["lat"], region["lon"]), 2),
                "risk_score": region["risk_score"],
                "latitude": region["lat"],
                "longitude": region["lon"],
            }
        )

    items.sort(key=lambda item: item["distance_km"])
    return jsonify({"success": True, "items": items[:5]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    app.run(debug=True, host="0.0.0.0", port=port)
