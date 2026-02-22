from flask import Flask, jsonify
from flask_cors import CORS
import requests
import time
import random

from db import (
    init_db,
    insert_earthquake,
    get_all_earthquakes,
    insert_flood,
    get_all_floods,
    insert_landslide,
    get_all_landslides,
)

app = Flask(__name__)
CORS(app)

init_db()

# India bounding box
MIN_LAT, MAX_LAT = 6.5, 37.5
MIN_LON, MAX_LON = 68.0, 97.5

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"


@app.route("/")
def home():
    return jsonify({"message": "✅ Disaster Detector Backend Running"})


# ------------------- EARTHQUAKES -------------------

@app.route("/api/fetch-india", methods=["GET"])
def fetch_india_earthquakes():
    """
    Fetch last 24h earthquakes from USGS, filter India region, store in DB
    """
    res = requests.get(USGS_URL)
    data = res.json()

    count = 0
    for feature in data["features"]:
        props = feature["properties"]
        geo = feature["geometry"]
        lon, lat, depth = geo["coordinates"]

        if MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON:
            quake = {
                "id": feature["id"],
                "place": props.get("place", "Unknown"),
                "magnitude": props.get("mag", 0),
                "time": props.get("time", 0),
                "latitude": lat,
                "longitude": lon,
                "depth": depth,
            }
            insert_earthquake(quake)
            count += 1

    return jsonify({"message": "India earthquakes stored", "count": count})


@app.route("/api/earthquakes", methods=["GET"])
def get_earthquakes():
    return jsonify(get_all_earthquakes())


# ------------------- FLOODS -------------------

@app.route("/api/fetch-floods", methods=["GET"])
def fetch_floods():
    """
    Floods: For now we simulate & store flood alerts for India.
    Later: integrate IMD / CWC / GDACS flood feeds.
    """
    sample_locations = [
        ("Assam - Brahmaputra Basin", 26.2, 91.7),
        ("Bihar - Ganga Plains", 25.6, 85.1),
        ("West Bengal - Sundarbans", 22.0, 88.7),
        ("Kerala - Alappuzha", 9.5, 76.3),
        ("Uttarakhand - Dehradun", 30.3, 78.0),
    ]

    now = int(time.time() * 1000)
    count = 0

    for loc, lat, lon in sample_locations:
        severity = random.choice(["low", "medium", "high", "critical"])
        flood = {
            "id": f"flood-{loc[:6]}-{now}-{count}",
            "location": loc,
            "severity": severity,
            "time": now - random.randint(0, 6) * 3600 * 1000,
            "latitude": lat,
            "longitude": lon,
            "details": "Possible flood risk due to heavy rainfall & rising river levels.",
        }
        insert_flood(flood)
        count += 1

    return jsonify({"message": "Flood alerts stored", "count": count})


@app.route("/api/floods", methods=["GET"])
def get_floods():
    return jsonify(get_all_floods())


# ------------------- LANDSLIDES -------------------

@app.route("/api/fetch-landslides", methods=["GET"])
def fetch_landslides():
    """
    Landslides: For now simulate & store events.
    Later: integrate rainfall + slope model + NDMA alerts.
    """
    sample_locations = [
        ("Himachal - Shimla Hills", 31.1, 77.2),
        ("Uttarakhand - Chamoli", 30.7, 79.6),
        ("Sikkim - Gangtok Region", 27.3, 88.6),
        ("Meghalaya - Shillong", 25.6, 91.9),
        ("Arunachal - Tawang", 27.6, 91.9),
    ]

    now = int(time.time() * 1000)
    count = 0

    for loc, lat, lon in sample_locations:
        severity = random.choice(["low", "medium", "high"])
        landslide = {
            "id": f"landslide-{loc[:6]}-{now}-{count}",
            "location": loc,
            "severity": severity,
            "time": now - random.randint(0, 8) * 3600 * 1000,
            "latitude": lat,
            "longitude": lon,
            "details": "High slope + heavy rainfall can trigger landslides in this region.",
        }
        insert_landslide(landslide)
        count += 1

    return jsonify({"message": "Landslide alerts stored", "count": count})


@app.route("/api/landslides", methods=["GET"])
def get_landslides():
    return jsonify(get_all_landslides())


# ------------------- ALERTS (Unified) -------------------

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """
    Combine top alerts from all disasters
    """
    quakes = get_all_earthquakes()[:5]
    floods = get_all_floods()[:5]
    landslides = get_all_landslides()[:5]

    alerts = []

    for q in quakes:
        alerts.append({
            "type": "earthquake",
            "title": q["place"],
            "severity": "high" if q["magnitude"] >= 5 else "medium",
            "time": q["time"],
            "lat": q["latitude"],
            "lon": q["longitude"],
            "details": f"Magnitude {q['magnitude']} | Depth {q['depth']} km",
        })

    for f in floods:
        alerts.append({
            "type": "flood",
            "title": f["location"],
            "severity": f["severity"],
            "time": f["time"],
            "lat": f["latitude"],
            "lon": f["longitude"],
            "details": f["details"],
        })

    for l in landslides:
        alerts.append({
            "type": "landslide",
            "title": l["location"],
            "severity": l["severity"],
            "time": l["time"],
            "lat": l["latitude"],
            "lon": l["longitude"],
            "details": l["details"],
        })

    alerts = sorted(alerts, key=lambda x: x["time"], reverse=True)
    return jsonify(alerts)


# ------------------- MITIGATION -------------------

@app.route("/api/mitigation/<disaster>", methods=["GET"])
def mitigation(disaster):
    tips = {
        "earthquake": [
            "Drop, Cover, and Hold On",
            "Stay away from windows & heavy furniture",
            "Keep emergency kit ready (water, torch, medicine)",
            "After shaking stops, evacuate calmly",
        ],
        "flood": [
            "Move to higher ground immediately",
            "Avoid walking/driving through flood waters",
            "Turn off electricity if safe",
            "Keep drinking water & essentials stored",
        ],
        "landslide": [
            "Avoid steep slopes during heavy rainfall",
            "Watch for cracks on ground / falling rocks",
            "Evacuate if warning signs appear",
            "Follow local authority alerts",
        ],
    }

    return jsonify({"disaster": disaster, "tips": tips.get(disaster, [])})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

# ==============================
# ✅ Disaster Risk Predictor API
# ==============================
from flask import request
from predictor import predict_risk


# ================================
# ✅ Disaster Predictor API
# ================================
from flask import request

@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(force=True)

    disaster = payload.get("disaster", "earthquake")
    seismic_mag = float(payload.get("seismic_mag", 0))
    depth_km = float(payload.get("depth_km", 0))
    rainfall_24h_mm = float(payload.get("rainfall_24h_mm", 0))
    slope_deg = float(payload.get("slope_deg", 0))
    soil_moisture = float(payload.get("soil_moisture", 0))
    ndvi = float(payload.get("ndvi", 0))
    plant_density = float(payload.get("plant_density", 0))

    # ✅ Simple formula risk scores (0-1)
    if disaster == "earthquake":
        score = min(1.0, (seismic_mag / 8.0) + (0.15 if depth_km < 30 else 0.05))
    elif disaster == "flood":
        score = min(1.0, (rainfall_24h_mm / 200.0) + soil_moisture * 0.3)
    elif disaster == "landslide":
        score = min(1.0, (rainfall_24h_mm / 200.0) * 0.4 + (slope_deg / 60.0) * 0.4 + soil_moisture * 0.2)
    else:
        score = 0.2

    if score >= 0.7:
        level = "High"
    elif score >= 0.4:
        level = "Medium"
    else:
        level = "Low"

    return jsonify({
        "success": True,
        "disaster": disaster,
        "risk_score": round(score, 3),
        "risk_level": level,
        "input": payload
    })

@app.route("/api/model-info", methods=["GET"])
def model_info():
    return jsonify({
        "success": True,
        "message": "Disaster Predictor Ready ✅",
        "note": "Currently using formula-based prediction (dataset/ML can be added next)"
    })
