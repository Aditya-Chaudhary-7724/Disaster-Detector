from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import time

from db import (
    get_alerts,
    get_conn,
    get_earthquakes,
    get_floods,
    get_landslides,
    increment_sync_counter,
    init_db,
    insert_alert,
)

ALERT_ENGINE_IMPORT_ERROR = None
DATA_PIPELINE_IMPORT_ERROR = None
PREDICTOR_IMPORT_ERROR = None
RESEARCH_IMPORT_ERROR = None
HYBRID_IMPORT_ERROR = None

try:
    from ai_alert_engine import generate_ai_alerts
except Exception as exc:
    ALERT_ENGINE_IMPORT_ERROR = str(exc)
    print(f"AI alert engine unavailable: {ALERT_ENGINE_IMPORT_ERROR}")

    def generate_ai_alerts(force=False):
        return {"success": False, "alerts": [], "error": f"AI alert engine unavailable: {ALERT_ENGINE_IMPORT_ERROR}"}

try:
    from data_pipeline import sync_all_if_due, sync_earthquakes, sync_floods, sync_landslides
except Exception as exc:
    DATA_PIPELINE_IMPORT_ERROR = str(exc)
    print(f"Data pipeline unavailable: {DATA_PIPELINE_IMPORT_ERROR}")

    def sync_all_if_due():
        return {"success": False, "error": f"Data pipeline unavailable: {DATA_PIPELINE_IMPORT_ERROR}"}

    def sync_earthquakes(force=False):
        return {"success": False, "error": f"Data pipeline unavailable: {DATA_PIPELINE_IMPORT_ERROR}"}

    def sync_floods(force=False):
        return {"success": False, "error": f"Data pipeline unavailable: {DATA_PIPELINE_IMPORT_ERROR}"}

    def sync_landslides(force=False):
        return {"success": False, "error": f"Data pipeline unavailable: {DATA_PIPELINE_IMPORT_ERROR}"}

try:
    from predictor import predict_risk
except Exception as exc:
    PREDICTOR_IMPORT_ERROR = str(exc)
    print(f"Predictor unavailable: {PREDICTOR_IMPORT_ERROR}")

    def predict_risk(payload):
        return {"success": False, "error": f"Predictor unavailable: {PREDICTOR_IMPORT_ERROR}"}

try:
    from research_routes import research_bp
except Exception as exc:
    RESEARCH_IMPORT_ERROR = str(exc)
    research_bp = None
    print(f"Research routes unavailable: {RESEARCH_IMPORT_ERROR}")

try:
    from ml_hybrid_predictor import load_hybrid_models
except Exception as exc:
    HYBRID_IMPORT_ERROR = str(exc)
    print(f"Hybrid model loader unavailable: {HYBRID_IMPORT_ERROR}")

    def load_hybrid_models():
        return None

AUTO_PREDICT_IMPORT_ERROR = None
SATELLITE_IMPORT_ERROR = None
CNN_IMPORT_ERROR = None

try:
    from auto_predictor import get_cluster_risk_trend, run_auto_prediction, run_auto_prediction_spatial, run_global_auto_prediction
except Exception as exc:
    AUTO_PREDICT_IMPORT_ERROR = str(exc)
    print(f"Auto predictor unavailable: {AUTO_PREDICT_IMPORT_ERROR}")

    def run_auto_prediction(disaster_type):
        return {"success": False, "error": f"Auto predictor unavailable: {AUTO_PREDICT_IMPORT_ERROR}"}

    def run_auto_prediction_spatial(disaster_type, method="kmeans", k=5, debug=False):
        return {"success": False, "error": f"Auto spatial predictor unavailable: {AUTO_PREDICT_IMPORT_ERROR}"}

    def get_cluster_risk_trend(cluster_id):
        return []

    def run_global_auto_prediction():
        return {"success": False, "error": f"Auto predictor unavailable: {AUTO_PREDICT_IMPORT_ERROR}"}

try:
    from satellite_predictor import predict_satellite_risk
    from satellite_predictor import preload_satellite_model
except Exception as exc:
    SATELLITE_IMPORT_ERROR = str(exc)
    print(f"Satellite predictor unavailable: {SATELLITE_IMPORT_ERROR}")

    def predict_satellite_risk(disaster_type="", image_path=None, feature_overrides=None):
        return {"success": False, "error": f"Satellite predictor unavailable: {SATELLITE_IMPORT_ERROR}"}

    def preload_satellite_model():
        return None

try:
    from cnn_satellite import get_cnn_model_info, predict_from_coordinates, predict_from_image, run_auto_cnn_prediction
except Exception as exc:
    CNN_IMPORT_ERROR = str(exc)
    print(f"CNN predictor unavailable: {CNN_IMPORT_ERROR}")

    def run_auto_cnn_prediction():
        return {"success": False, "error": f"CNN predictor unavailable: {CNN_IMPORT_ERROR}"}

    def predict_from_coordinates(lat, lng, disaster=""):
        return {"success": False, "error": f"CNN predictor unavailable: {CNN_IMPORT_ERROR}"}

    def predict_from_image(image_path):
        return {"success": False, "error": f"CNN predictor unavailable: {CNN_IMPORT_ERROR}"}

    def get_cnn_model_info():
        return {"backend": "unavailable", "accuracy": None}

ENV_IMPORT_ERROR = None
try:
    from environmental_data import fetch_weather_data, get_environmental_bundle
except Exception as exc:
    ENV_IMPORT_ERROR = str(exc)
    print(f"Environmental data module unavailable: {ENV_IMPORT_ERROR}")

    def fetch_weather_data(lat, lng):
        return {"success": True, "lat": lat, "lng": lng, "source": f"fallback:{ENV_IMPORT_ERROR}"}

    def get_environmental_bundle(lat, lng):
        return {"success": True, "lat": lat, "lng": lng, "weather": fetch_weather_data(lat, lng), "satellite": {}, "rain": {}}

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
logger = logging.getLogger("disaster-detector")

init_db()
if research_bp is not None:
    app.register_blueprint(research_bp)

try:
    load_hybrid_models()
except Exception:
    pass

try:
    preload_satellite_model()
except Exception:
    pass


def _safe_sync_all():
    try:
        return sync_all_if_due()
    except Exception:
        return {}


def _safe_list_response(fetch_fn, limit, route_name):
    try:
        rows = fetch_fn(limit)
        return jsonify(rows or [])
    except Exception as exc:
        logger.exception("%s API error", route_name)
        increment_sync_counter("failure_count")
        return jsonify([])


def _increment_prediction_metrics(failed: bool = False):
    increment_sync_counter("prediction_count")
    if failed:
        increment_sync_counter("failure_count")


def _latest_hazard_rows():
    return {
        "earthquake": get_earthquakes(50),
        "flood": get_floods(50),
        "landslide": get_landslides(50),
    }


def _distance_km(lat1, lon1, lat2, lon2):
    import math

    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _nearest_risks(lat: float, lon: float, limit: int = 5):
    items = []
    hazard_rows = _latest_hazard_rows()
    for disaster, rows in hazard_rows.items():
        for row in rows:
            row_lat = row.get("latitude")
            row_lon = row.get("longitude")
            if row_lat is None or row_lon is None:
                continue
            try:
                distance = _distance_km(float(lat), float(lon), float(row_lat), float(row_lon))
            except Exception:
                continue
            risk_hint = row.get("risk")
            if disaster == "earthquake":
                magnitude = float(row.get("magnitude") or 0)
                risk_score = min(1.0, magnitude / 8.0)
            else:
                risk_map = {"LOW": 0.3, "MEDIUM": 0.6, "HIGH": 0.85}
                risk_score = risk_map.get(str(risk_hint or "LOW").upper(), 0.3)
            items.append(
                {
                    "disaster": disaster,
                    "title": row.get("place") or row.get("location") or "Unknown",
                    "distance_km": round(distance, 2),
                    "risk_score": round(risk_score, 4),
                    "latitude": row_lat,
                    "longitude": row_lon,
                }
            )
    items.sort(key=lambda item: (item["distance_km"], -item["risk_score"]))
    return items[:limit]


def _current_high_risk_location():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COALESCE(location, place) AS location_name, latitude, longitude, risk, time
        FROM floods
        WHERE UPPER(COALESCE(risk, '')) = 'HIGH'
        ORDER BY time DESC
        LIMIT 1
        """
    )
    flood = cur.fetchone()

    cur.execute(
        """
        SELECT COALESCE(location, place) AS location_name, latitude, longitude, risk, time
        FROM landslides
        WHERE UPPER(COALESCE(risk, '')) = 'HIGH'
        ORDER BY time DESC
        LIMIT 1
        """
    )
    landslide = cur.fetchone()

    cur.execute(
        """
        SELECT place AS location_name, latitude, longitude, magnitude, time
        FROM earthquakes
        WHERE magnitude >= 5.5
        ORDER BY time DESC
        LIMIT 1
        """
    )
    earthquake = cur.fetchone()
    conn.close()

    candidates = []
    if flood:
        candidates.append(
            {
                "lat": float(flood["latitude"]),
                "lng": float(flood["longitude"]),
                "disaster": "flood",
                "risk_score": 0.85,
                "location_name": flood["location_name"] or "Flood zone",
                "time": int(flood["time"] or 0),
            }
        )
    if landslide:
        candidates.append(
            {
                "lat": float(landslide["latitude"]),
                "lng": float(landslide["longitude"]),
                "disaster": "landslide",
                "risk_score": 0.85,
                "location_name": landslide["location_name"] or "Landslide zone",
                "time": int(landslide["time"] or 0),
            }
        )
    if earthquake:
        magnitude = float(earthquake["magnitude"] or 0)
        candidates.append(
            {
                "lat": float(earthquake["latitude"]),
                "lng": float(earthquake["longitude"]),
                "disaster": "earthquake",
                "risk_score": round(min(0.95, magnitude / 7.0), 4),
                "location_name": earthquake["location_name"] or "Earthquake zone",
                "time": int(earthquake["time"] or 0),
            }
        )

    if candidates:
        candidates.sort(key=lambda item: (item["risk_score"], item["time"]), reverse=True)
        return candidates[0]

    fallback = _nearest_risks(22.9734, 78.6569, limit=1)
    if fallback:
        top = fallback[0]
        return {
            "lat": float(top["latitude"]),
            "lng": float(top["longitude"]),
            "disaster": top["disaster"],
            "risk_score": float(top["risk_score"]),
            "location_name": top["title"],
        }
    return None


# -------------------------------
# HOME
# -------------------------------
@app.route("/")
def home():
    return jsonify({"message": "Disaster Detector Backend Running ✅"})


@app.route("/api/test", methods=["GET"])
def test():
    return {"status": "Backend working"}


# -------------------------------
# EARTHQUAKES (USGS real-time)
# -------------------------------
@app.route("/api/fetch-india", methods=["GET"])
def fetch_india_quakes():
    try:
        info = sync_earthquakes(force=True)
        return jsonify({"success": True, **info})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/earthquakes", methods=["GET"])
def api_earthquakes():
    logger.info("Earthquake API hit")
    _safe_sync_all()
    return _safe_list_response(get_earthquakes, 100, "Earthquake")


# -------------------------------
# FLOODS (daily rainfall-proxy)
# -------------------------------
@app.route("/api/fetch-floods", methods=["GET"])
def fetch_floods():
    try:
        info = sync_floods(force=True)
        return jsonify({"success": True, **info})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/floods", methods=["GET"])
def api_floods():
    logger.info("Flood API hit")
    _safe_sync_all()
    return _safe_list_response(get_floods, 100, "Flood")


# -------------------------------
# LANDSLIDES (daily proxy)
# -------------------------------
@app.route("/api/fetch-landslides", methods=["GET"])
def fetch_landslides():
    try:
        info = sync_landslides(force=True)
        return jsonify({"success": True, **info})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/landslides", methods=["GET"])
def api_landslides():
    logger.info("Landslide API hit")
    _safe_sync_all()
    return _safe_list_response(get_landslides, 100, "Landslide")


# -------------------------------
# MITIGATION
# -------------------------------
@app.route("/api/mitigation/<disaster>", methods=["GET"])
def mitigation(disaster):
    disaster = disaster.lower()

    tips = {
        "earthquake": [
            "Drop, Cover, Hold On immediately",
            "Keep emergency kit: water, torch, powerbank",
            "Move away from glass and heavy objects",
            "After shaking stops, evacuate carefully",
        ],
        "flood": [
            "Move to higher ground immediately",
            "Avoid driving through flooded roads",
            "Keep documents in waterproof bag",
            "Switch off electricity if water enters home",
        ],
        "landslide": [
            "Avoid steep slopes during heavy rain",
            "Look for cracks in ground or walls",
            "Evacuate if rocks/soil start moving",
            "Follow local authority warnings",
        ],
    }

    emergency_contacts = {
        "earthquake": ["Police: 100", "Ambulance: 108"],
        "flood": ["Fire Department: 101", "Rescue Team: 112"],
        "landslide": ["Police: 100", "Medical Emergency: 108"],
    }

    return jsonify(
        {
            "success": True,
            "disaster": disaster,
            "tips": tips.get(disaster, []),
            "emergency_contacts": emergency_contacts.get(disaster, []),
        }
    )


# -------------------------------
# PREDICTOR API (ML-first + fallback)
# -------------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        payload = request.get_json(silent=True) or {}
        logger.info("Prediction request received for disaster=%s", payload.get("disaster") or payload.get("disaster_type"))
        result = predict_risk(payload)
    except Exception as exc:
        logger.exception("Prediction API failed")
        _increment_prediction_metrics(failed=True)
        return jsonify({"success": False, "error": str(exc)}), 500

    if not result.get("success"):
        _increment_prediction_metrics(failed=True)
        return jsonify(result), 400
    _increment_prediction_metrics(failed=False)

    # Backward-compatible shape + new ML-first shape
    return jsonify(
        {
            "success": True,
            "risk_level": result.get("risk_level") or (result.get("level", "LOW").title()),
            "risk_score": result.get("risk_score"),
            "confidence": result.get("confidence"),
            "method": result.get("method", "Rule-Based"),
            "ml_probability": result.get("ml_probability"),
            "rule_score": result.get("rule_score"),
            "final_risk_probability": result.get("final_risk_probability"),
            "alpha": result.get("alpha"),
            "latency_ms": result.get("latency_ms"),
            "explanation": result.get("explanation") or result.get("reasons", []),
            "feature_importance": result.get("feature_importance", {}),
            "top_features": result.get("top_features", []),
            "risk_equation": result.get("risk_equation"),
            "equation_score": result.get("equation_score"),
            "human_explanation": result.get("human_explanation"),
            "result": result,
            "input": payload,
        }
    )


@app.route("/api/model-info", methods=["GET"])
def model_info():
    return jsonify(
        {
            "success": True,
            "message": "Disaster Predictor Ready ✅",
            "note": "ML-first predictor with rule-based fallback enabled",
        }
    )


# -------------------------------
# ALERT ENGINE APIs
# -------------------------------
@app.route("/api/run-alert-check", methods=["POST"])
def run_alert_check():
    payload = request.get_json(force=True) or {}
    threshold = float(payload.get("threshold") or 0.7)
    if threshold > 1:
        threshold = threshold / 100.0

    result = predict_risk(payload)
    if not result.get("success"):
        return jsonify(result), 400

    score = float(result.get("final_risk_probability") or result.get("risk_score") or 0)
    level = str(result.get("level") or "LOW").upper()
    disaster = result.get("disaster")

    if score >= threshold:
        advisory = "Warning" if score > 0.7 else "Watch" if score >= 0.4 else "Advisory"
        msg = f"{disaster.upper()} {advisory}: score={score:.2f} | " + ", ".join(result.get("reasons", [])[:3])
        alert = {
            "type": f"{disaster.title()} {advisory}",
            "alert_type": f"{disaster.title()} {advisory}",
            "disaster": disaster,
            "region": payload.get("location") or "Custom input",
            "level": level,
            "priority": level,
            "confidence": result.get("confidence"),
            "risk_score": round(score, 4),
            "message": msg,
            "lat": payload.get("lat") or payload.get("latitude"),
            "lon": payload.get("lon") or payload.get("longitude"),
            "created_at": int(time.time() * 1000),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "location": payload.get("location") or f"{payload.get('lat') or payload.get('latitude')}, {payload.get('lon') or payload.get('longitude')}",
        }
        stored = insert_alert(alert)
        logger.info("Alert triggered for disaster=%s level=%s score=%.3f", disaster, level, score)
        increment_sync_counter("alert_count")
        return jsonify({"success": True, "alert_created": True, "alert": stored})

    return jsonify({"success": True, "alert_created": False, "result": result})


@app.route("/api/alerts/generate", methods=["POST"])
def api_generate_alerts():
    result = generate_ai_alerts(force=True)
    if result.get("success"):
        increment_sync_counter("alert_count", int(result.get("count") or len(result.get("alerts", []))))
    return jsonify(result)


@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    try:
        generate_ai_alerts(force=False)
    except Exception as exc:
        logger.exception("Alerts generation error")
    try:
        rows = get_alerts(100)
        return jsonify(rows or [])
    except Exception as exc:
        logger.exception("Alerts API error")
        return jsonify([])


# -------------------------------
# ANALYTICS APIs
# -------------------------------
@app.route("/api/analytics/disaster-frequency", methods=["GET"])
def analytics_disaster_frequency():
    _safe_sync_all()
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS c FROM earthquakes")
    eq = int(cur.fetchone()["c"])
    cur.execute("SELECT COUNT(*) AS c FROM floods")
    fl = int(cur.fetchone()["c"])
    cur.execute("SELECT COUNT(*) AS c FROM landslides")
    ls = int(cur.fetchone()["c"])

    conn.close()
    return jsonify(
        [
            {"name": "Earthquake", "count": eq},
            {"name": "Flood", "count": fl},
            {"name": "Landslide", "count": ls},
        ]
    )


@app.route("/api/analytics/risk-trend", methods=["GET"])
def analytics_risk_trend():
    _safe_sync_all()
    conn = get_conn()
    cur = conn.cursor()

    cutoff = int(time.time() * 1000) - 7 * 24 * 60 * 60 * 1000

    cur.execute("SELECT time, magnitude FROM earthquakes WHERE time >= ? ORDER BY time ASC", (cutoff,))
    eq_rows = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT time, risk FROM floods WHERE time >= ? ORDER BY time ASC", (cutoff,))
    flood_rows = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT time, risk FROM landslides WHERE time >= ? ORDER BY time ASC", (cutoff,))
    land_rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    points = []
    for r in eq_rows[-40:]:
        points.append(
            {
                "timestamp": r["time"],
                "disaster": "Earthquake",
                "risk_score": min(100, int((float(r["magnitude"] or 0) / 7.5) * 100)),
            }
        )

    risk_map = {"LOW": 35, "MEDIUM": 60, "HIGH": 85}
    for r in flood_rows[-20:]:
        points.append(
            {
                "timestamp": r["time"],
                "disaster": "Flood",
                "risk_score": risk_map.get(str(r["risk"]).upper(), 35),
            }
        )

    for r in land_rows[-20:]:
        points.append(
            {
                "timestamp": r["time"],
                "disaster": "Landslide",
                "risk_score": risk_map.get(str(r["risk"]).upper(), 35),
            }
        )

    points.sort(key=lambda x: x["timestamp"])
    return jsonify(points[-100:])


@app.route("/api/analytics/prediction-confidence", methods=["GET"])
def analytics_prediction_confidence():
    conn = get_conn()
    cur = conn.cursor()
    cutoff = int(time.time() * 1000) - 7 * 24 * 60 * 60 * 1000
    cur.execute(
        "SELECT created_at, confidence, disaster FROM alerts WHERE created_at >= ? ORDER BY created_at ASC",
        (cutoff,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    out = [
        {
            "timestamp": r["created_at"],
            "confidence": float(r["confidence"] or 0),
            "disaster": r.get("disaster") or "unknown",
        }
        for r in rows
    ]
    return jsonify(out)


@app.route("/api/auto-predict", methods=["POST"])
def auto_predict_global():
    try:
        logger.info("Auto predictor invoked without manual input")
        result = run_global_auto_prediction()
        if not result.get("success"):
            _increment_prediction_metrics(failed=True)
            return jsonify(result), 400
        _increment_prediction_metrics(failed=False)
        return jsonify(result)
    except Exception as exc:
        logger.exception("Auto predictor API failed")
        _increment_prediction_metrics(failed=True)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/auto-predict/<disaster_type>", methods=["POST"])
def auto_predict(disaster_type):
    try:
        logger.info("Auto predictor invoked for disaster=%s", disaster_type)
        result = run_auto_prediction(disaster_type)
        if not result.get("success"):
            _increment_prediction_metrics(failed=True)
            return jsonify(result), 400
        _increment_prediction_metrics(failed=False)
        return jsonify(result)
    except Exception as exc:
        logger.exception("Typed auto predictor API failed")
        _increment_prediction_metrics(failed=True)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/satellite-predict", methods=["POST"])
def satellite_predict():
    payload = request.get_json(force=True) or {}
    disaster_type = str(payload.get("disaster_type") or payload.get("disaster") or "").lower()
    image_path = payload.get("image_path")

    result = predict_satellite_risk(disaster_type=disaster_type, image_path=image_path, feature_overrides=payload)
    if not result.get("success"):
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/cnn-predict", methods=["POST"])
def cnn_predict():
    payload = request.get_json(silent=True) or {}
    try:
        lat = payload.get("lat") or payload.get("latitude")
        lng = payload.get("lng") or payload.get("longitude")
        disaster = str(payload.get("disaster") or payload.get("disaster_type") or "").lower()
        if lat is None or lng is None:
            high_risk = _current_high_risk_location()
            if not high_risk:
                increment_sync_counter("failure_count")
                return jsonify({"success": False, "error": "No high-risk location available"}), 400
            lat = high_risk["lat"]
            lng = high_risk["lng"]
            disaster = disaster or high_risk.get("disaster", "")
            location_name = high_risk.get("location_name")
        else:
            location_name = payload.get("location_name")
        env_bundle = get_environmental_bundle(float(lat), float(lng))
        result = predict_from_coordinates(float(lat), float(lng), disaster=disaster, weather=env_bundle.get("weather", {}))
        if not result.get("success"):
            increment_sync_counter("failure_count")
            return jsonify(result), 400
        result["weather"] = env_bundle.get("weather", {})
        result["satellite"] = env_bundle.get("satellite", {})
        result["rain"] = env_bundle.get("rain", {})
        result["location_name"] = location_name
        return jsonify(result)
    except Exception as exc:
        logger.exception("CNN predictor API failed")
        increment_sync_counter("failure_count")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/high-risk-location", methods=["GET"])
def high_risk_location():
    _safe_sync_all()
    item = _current_high_risk_location()
    if not item:
        return jsonify({"success": False, "error": "No high-risk location found"}), 404
    return jsonify({"success": True, **item})


@app.route("/api/weather-data", methods=["GET"])
def weather_data():
    try:
        lat = float(request.args.get("lat"))
        lng = float(request.args.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "lat and lng query params are required"}), 400
    return jsonify(fetch_weather_data(lat, lng))


@app.route("/api/environmental-data", methods=["GET"])
def environmental_data():
    try:
        lat = float(request.args.get("lat"))
        lng = float(request.args.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "lat and lng query params are required"}), 400
    return jsonify(get_environmental_bundle(lat, lng))


@app.route("/api/auto-predict-spatial/<disaster_type>", methods=["GET"])
def auto_predict_spatial(disaster_type):
    method = request.args.get("method", "kmeans")
    debug = str(request.args.get("debug", "0")).lower() in {"1", "true", "yes", "on"}
    try:
        k = int(request.args.get("k", 5))
    except (TypeError, ValueError):
        k = 5

    try:
        result = run_auto_prediction_spatial(disaster_type=disaster_type, method=method, k=k, debug=debug)
        if not result.get("success"):
            return jsonify(result), 400
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/risk-trend/<int:cluster_id>", methods=["GET"])
def risk_trend_cluster(cluster_id):
    rows = get_cluster_risk_trend(cluster_id)
    return jsonify({"success": True, "cluster_id": cluster_id, "points": rows})


@app.route("/api/performance", methods=["GET"])
def performance_dashboard():
    hybrid = load_hybrid_models() or {}
    hybrid_meta = hybrid.get("meta", {}) if isinstance(hybrid, dict) else {}
    sat_meta = preload_satellite_model() or {}
    cnn_meta = get_cnn_model_info() or {}
    conn = get_conn()
    cur = conn.cursor()
    def get_counter(key):
        cur.execute("SELECT value FROM sync_state WHERE key=?", (key,))
        row = cur.fetchone()
        try:
            return int(row["value"]) if row else 0
        except (TypeError, ValueError):
            return 0
    prediction_count = get_counter("prediction_count")
    alert_count = get_counter("alert_count")
    failure_count = get_counter("failure_count")
    conn.close()
    return jsonify(
        {
            "success": True,
            "models": {
                "hybrid_ml": hybrid_meta,
                "satellite_model": sat_meta,
                "cnn_model": cnn_meta,
            },
            "system_metrics": {
                "prediction_count": prediction_count,
                "alert_count": alert_count,
                "failure_count": failure_count,
                "latest_latency_ms": hybrid_meta.get("latest_latency_ms", hybrid_meta.get("latency_ms")),
            },
        }
    )


@app.route("/api/nearest-risks", methods=["GET"])
def nearest_risks():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "lat and lon query params are required"}), 400
    return jsonify({"success": True, "items": _nearest_risks(lat, lon)})


if __name__ == "__main__":
    print("🚀 Disaster Detector Backend Running on http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5050)
