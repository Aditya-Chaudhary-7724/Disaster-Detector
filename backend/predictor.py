from __future__ import annotations

from datetime import datetime, timezone

from db import get_validation_metrics, insert_alert, insert_prediction
from model import (
    ALERT_THRESHOLD,
    MODEL_ALGORITHM,
    MODEL_FORMULA,
    REGION_PROFILES,
    get_feature_importance,
    get_region_snapshot,
    predict_region_risk,
    risk_level_from_score,
    list_regions,
)


def _normalize_region(region: str | None) -> str | None:
    if not region:
        return None

    region_map = {name.lower(): name for name in REGION_PROFILES}
    return region_map.get(str(region).strip().lower())


def get_available_regions() -> list[dict]:
    return list_regions()


def predict_risk(payload: dict) -> dict:
    region = _normalize_region(payload.get("region") or payload.get("location"))
    if not region:
        return {
            "success": False,
            "error": "Invalid region. Use one of: Chennai, Mumbai, Delhi, Assam, Uttarakhand, Himachal",
        }

    snapshot = get_region_snapshot(region)
    prediction = predict_region_risk(region)
    timestamp = datetime.now(timezone.utc).isoformat()
    predicted_label = 1 if prediction["risk_score"] >= ALERT_THRESHOLD else 0

    stored_prediction = insert_prediction(
        {
            "region": region,
            "rainfall": snapshot["rainfall"],
            "temperature": snapshot["temperature"],
            "humidity": snapshot["humidity"],
            "seismic_activity": snapshot["seismic_activity"],
            "soil_moisture": snapshot["soil_moisture"],
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "predicted_label": predicted_label,
            "actual_label": snapshot["actual_label"],
            "created_at": timestamp,
        }
    )

    alert_record = None
    if prediction["risk_score"] >= ALERT_THRESHOLD:
        alert_record = insert_alert(
            {
                "region": region,
                "risk_score": prediction["risk_score"],
                "level": prediction["risk_level"].upper(),
                "message": f"{region} shows {prediction['risk_level']} disaster risk based on current ML features.",
                "created_at": timestamp,
            }
        )

    validation = get_validation_metrics()
    top_features = sorted(
        get_feature_importance().items(),
        key=lambda item: item[1],
        reverse=True,
    )[:3]

    explanation = [
        f"Region selected: {region}",
        "Final Risk = 0.5*ML + 0.3*Temporal + 0.2*Spatial",
        "Predicted using rainfall, temperature, humidity, water level, soil moisture, and regional history",
        f"Current actual benchmark for validation: {risk_level_from_score(snapshot['actual_risk_score'])}",
    ]

    return {
        "success": True,
        "region": region,
        "risk_score": prediction["risk_score"],
        "risk_level": prediction["risk_level"],
        "level": prediction["risk_level"].upper(),
        "confidence": prediction["risk_score"],
        "algorithm": MODEL_ALGORITHM,
        "method": MODEL_ALGORITHM,
        "formula": MODEL_FORMULA,
        "final_risk_probability": prediction["risk_score"],
        "ml_probability": prediction["ml_prediction"],
        "ml_score": prediction["ml_score"],
        "temporal_factor": prediction["temporal_factor"],
        "temporal_score": prediction["temporal_score"],
        "spatial_influence": prediction["spatial_influence"],
        "spatial_score": prediction["spatial_score"],
        "rule_score": None,
        "feature_importance": get_feature_importance(),
        "top_features": [{"feature": name, "importance": value} for name, value in top_features],
        "explanation": explanation,
        "human_explanation": prediction["explanation"],
        "analysis": prediction["analysis"],
        "result": prediction,
        "input_features": snapshot,
        "prediction_record": stored_prediction,
        "alert_created": alert_record is not None,
        "alert": alert_record,
        "validation": validation,
    }
