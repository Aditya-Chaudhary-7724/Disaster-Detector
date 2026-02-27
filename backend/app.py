from flask import Flask, jsonify, request
from flask_cors import CORS
import time

from ai_alert_engine import generate_ai_alerts
from auto_predictor import get_cluster_risk_trend, run_auto_prediction, run_auto_prediction_spatial
from data_pipeline import sync_all_if_due, sync_earthquakes, sync_floods, sync_landslides
from db import (
    get_alerts,
    get_conn,
    get_earthquakes,
    get_floods,
    get_landslides,
    init_db,
    insert_alert,
)
from predictor import predict_risk
from research_routes import research_bp
from ml_hybrid_predictor import load_hybrid_models
from satellite_predictor import predict_satellite_risk
from satellite_predictor import preload_satellite_model

app = Flask(__name__)
CORS(app)

init_db()
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


# -------------------------------
# HOME
# -------------------------------
@app.route("/")
def home():
    return jsonify({"message": "Disaster Detector Backend Running ✅"})


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
    _safe_sync_all()
    return jsonify(get_earthquakes(100))


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
    _safe_sync_all()
    return jsonify(get_floods(100))


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
    _safe_sync_all()
    return jsonify(get_landslides(100))


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
    payload = request.get_json(force=True) or {}
    result = predict_risk(payload)

    if not result.get("success"):
        return jsonify(result), 400

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
    threshold = float(payload.get("threshold") or 70)

    result = predict_risk(payload)
    if not result.get("success"):
        return jsonify(result), 400

    score = float(result.get("risk_score") or 0)
    level = result.get("level")
    disaster = result.get("disaster")

    if score >= threshold:
        msg = f"{disaster.upper()} RISK {level}: score={score}/100 | " + ", ".join(result.get("reasons", [])[:3])
        alert = {
            "type": f"{disaster.title()} Warning",
            "alert_type": f"{disaster.title()} Warning",
            "disaster": disaster,
            "region": "Custom input",
            "level": level,
            "confidence": result.get("confidence"),
            "message": msg,
            "lat": payload.get("lat") or payload.get("latitude"),
            "lon": payload.get("lon") or payload.get("longitude"),
            "created_at": int(time.time() * 1000),
        }
        insert_alert(alert)
        return jsonify({"success": True, "alert_created": True, "alert": alert})

    return jsonify({"success": True, "alert_created": False, "result": result})


@app.route("/api/alerts/generate", methods=["POST"])
def api_generate_alerts():
    result = generate_ai_alerts(force=True)
    return jsonify(result)


@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    generate_ai_alerts(force=False)
    return jsonify(get_alerts(100))


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


@app.route("/api/auto-predict/<disaster_type>", methods=["POST"])
def auto_predict(disaster_type):
    try:
        result = run_auto_prediction(disaster_type)
        if not result.get("success"):
            return jsonify(result), 400
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/satellite-predict", methods=["POST"])
def satellite_predict():
    payload = request.get_json(force=True) or {}
    disaster_type = str(payload.get("disaster_type") or payload.get("disaster") or "").lower()
    image_path = payload.get("image_path")

    result = predict_satellite_risk(disaster_type=disaster_type, image_path=image_path)
    if not result.get("success"):
        return jsonify(result), 400
    return jsonify(result)


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
