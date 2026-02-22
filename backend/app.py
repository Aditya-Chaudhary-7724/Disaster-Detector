from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
import uuid
from datetime import datetime

from db import (
    init_db,
    insert_earthquake, get_earthquakes,
    insert_flood, get_floods,
    insert_landslide, get_landslides,
    insert_alert, get_alerts
)

from predictor import predict_risk

app = Flask(__name__)
CORS(app)

init_db()

# -------------------------------
# HOME
# -------------------------------
@app.route("/")
def home():
    return jsonify({"message": "Disaster Detector Backend Running ✅"})


# -------------------------------
# EARTHQUAKES (USGS)
# -------------------------------
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

@app.route("/api/fetch-india", methods=["GET"])
def fetch_india_quakes():
    """
    Fetches USGS all_day and stores India region quakes (rough filter)
    """
    try:
        r = requests.get(USGS_URL, timeout=10)
        data = r.json()

        count = 0
        for f in data.get("features", []):
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [None, None, None])

            place = props.get("place", "")
            # crude India region filter (works decently)
            if "india" not in place.lower():
                continue

            q = {
                "id": f.get("id"),
                "place": place,
                "magnitude": float(props.get("mag") or 0),
                "depth": float(coords[2] or 0),
                "time": int(props.get("time") or 0),
                "latitude": float(coords[1] or 0),
                "longitude": float(coords[0] or 0),
            }
            insert_earthquake(q)
            count += 1

        return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/earthquakes", methods=["GET"])
def api_earthquakes():
    return jsonify(get_earthquakes(50))


# -------------------------------
# FLOODS (DEMO SYNC)
# -------------------------------
@app.route("/api/fetch-floods", methods=["GET"])
def fetch_floods():
    """
    For now: generate demo flood events (later replace with IMD/WRIS/Realtime APIs)
    """
    demo_places = [
        ("Assam - Guwahati", 26.1445, 91.7362),
        ("Bihar - Patna", 25.5941, 85.1376),
        ("UP - Lucknow", 26.8467, 80.9462),
        ("West Bengal - Siliguri", 26.7271, 88.3953),
    ]

    now_ms = int(time.time() * 1000)
    for p in demo_places:
        risk = "HIGH" if uuid.uuid4().int % 2 == 0 else "MEDIUM"
        insert_flood({
            "id": str(uuid.uuid4()),
            "place": p[0],
            "risk": risk,
            "time": now_ms,
            "latitude": p[1],
            "longitude": p[2]
        })

    return jsonify({"success": True, "message": "Flood demo synced"})


@app.route("/api/floods", methods=["GET"])
def api_floods():
    return jsonify(get_floods(50))


# -------------------------------
# LANDSLIDES (DEMO SYNC)
# -------------------------------
@app.route("/api/fetch-landslides", methods=["GET"])
def fetch_landslides():
    demo_places = [
        ("Sikkim - Gangtok Hills", 27.3389, 88.6065),
        ("Himachal - Shimla", 31.1048, 77.1734),
        ("Uttarakhand - Nainital", 29.3803, 79.4636),
        ("Meghalaya - Shillong", 25.5788, 91.8933),
    ]

    now_ms = int(time.time() * 1000)
    for p in demo_places:
        risk = "HIGH" if uuid.uuid4().int % 3 == 0 else "MEDIUM"
        insert_landslide({
            "id": str(uuid.uuid4()),
            "place": p[0],
            "risk": risk,
            "time": now_ms,
            "latitude": p[1],
            "longitude": p[2]
        })

    return jsonify({"success": True, "message": "Landslide demo synced"})


@app.route("/api/landslides", methods=["GET"])
def api_landslides():
    return jsonify(get_landslides(50))


# -------------------------------
# MITIGATION (simple)
# -------------------------------
@app.route("/api/mitigation/<disaster>", methods=["GET"])
def mitigation(disaster):
    disaster = disaster.lower()

    tips = {
        "earthquake": [
            "Drop, Cover, Hold On immediately",
            "Keep emergency kit: water, torch, powerbank",
            "Move away from glass and heavy objects",
            "After shaking stops, evacuate carefully"
        ],
        "flood": [
            "Move to higher ground immediately",
            "Avoid driving through flooded roads",
            "Keep documents in waterproof bag",
            "Switch off electricity if water enters home"
        ],
        "landslide": [
            "Avoid steep slopes during heavy rain",
            "Look for cracks in ground or walls",
            "Evacuate if rocks/soil start moving",
            "Follow local authority warnings"
        ]
    }

    return jsonify({"success": True, "disaster": disaster, "tips": tips.get(disaster, [])})


# -------------------------------
# PREDICTOR API (FORMULA ENGINE)
# -------------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(force=True) or {}
    result = predict_risk(payload)

    if not result.get("success"):
        return jsonify(result), 400

    return jsonify({
        "success": True,
        "result": result,
        "input": payload
    })


@app.route("/api/model-info", methods=["GET"])
def model_info():
    return jsonify({
        "success": True,
        "message": "Disaster Predictor Ready ✅",
        "note": "Currently using formula engine (ML can be added later)"
    })


# -------------------------------
# AUTO ALERT ENGINE
# -------------------------------
@app.route("/api/run-alert-check", methods=["POST"])
def run_alert_check():
    """
    Runs prediction risk check (based on payload) and stores an alert in DB
    if risk >= threshold
    """
    payload = request.get_json(force=True) or {}
    threshold = float(payload.get("threshold") or 70)

    result = predict_risk(payload)
    if not result.get("success"):
        return jsonify(result), 400

    score = result["risk_score"]
    level = result["level"]
    disaster = result["disaster"]

    if score >= threshold:
        msg = f"{disaster.upper()} RISK {level}: score={score}/100 | " + ", ".join(result["reasons"][:3])

        alert = {
            "type": disaster,
            "level": level,
            "message": msg,
            "lat": payload.get("lat"),
            "lon": payload.get("lon"),
            "created_at": int(time.time() * 1000)
        }
        insert_alert(alert)

        return jsonify({"success": True, "alert_created": True, "alert": alert})

    return jsonify({"success": True, "alert_created": False, "result": result})


@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    return jsonify(get_alerts(50))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
