"""Hybrid predictor: ML-first with rule-based fallback.

Risk score equation (interpretable proxy for academic reporting):
Risk Score = w1*Rain + w2*Slope + w3*Soil + w4*Seismic + w5*DepthInv + w6*VegetationInv
"""

from __future__ import annotations

from typing import Dict, List

from ml_engine import predict_with_model


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def classify(score):
    if score >= 75:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _n(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def _weighted_equation(payload: Dict[str, object]) -> dict:
    rainfall = float(payload.get("rainfall_24h_mm") or 0)
    slope = float(payload.get("slope_deg") or 0)
    soil = float(payload.get("soil_moisture") or 0)
    seismic = float(payload.get("seismic_mag") or payload.get("seismic_magnitude") or 0)
    depth = float(payload.get("depth_km") or 0)
    ndvi = float(payload.get("ndvi") or 0.5)

    rain_n = _n(rainfall, 0, 350)
    slope_n = _n(slope, 0, 60)
    soil_n = max(0.0, min(1.0, soil))
    seismic_n = _n(seismic, 0, 8)
    depth_inv = 1.0 - _n(depth, 0, 300)
    veg_inv = 1.0 - max(0.0, min(1.0, ndvi))

    # Equation for explainability (not replacing ML inference)
    w1, w2, w3, w4, w5, w6 = 0.25, 0.16, 0.19, 0.18, 0.12, 0.10
    score = w1 * rain_n + w2 * slope_n + w3 * soil_n + w4 * seismic_n + w5 * depth_inv + w6 * veg_inv

    return {
        "risk_equation": "R = 0.25*Rain + 0.16*Slope + 0.19*Soil + 0.18*Seismic + 0.12*DepthInv + 0.10*VegInv",
        "equation_terms": {
            "Rain": round(rain_n, 4),
            "Slope": round(slope_n, 4),
            "Soil": round(soil_n, 4),
            "Seismic": round(seismic_n, 4),
            "DepthInv": round(depth_inv, 4),
            "VegInv": round(veg_inv, 4),
        },
        "equation_score": round(score, 4),
    }


def _human_explanation(disaster: str, payload: Dict[str, object]) -> str:
    rainfall = float(payload.get("rainfall_24h_mm") or 0)
    slope = float(payload.get("slope_deg") or 0)
    soil = float(payload.get("soil_moisture") or 0)
    seismic = float(payload.get("seismic_mag") or payload.get("seismic_magnitude") or 0)
    depth = float(payload.get("depth_km") or 0)

    if disaster == "flood":
        return (
            "High rainfall and elevated soil moisture increase flood probability"
            if rainfall > 150 and soil > 0.7
            else "Flood risk is moderated by current rainfall-soil conditions"
        )
    if disaster == "landslide":
        return (
            "High rainfall + high soil moisture + steep slope increases landslide probability"
            if rainfall > 100 and soil > 0.65 and slope > 30
            else "Landslide risk is limited by current slope-moisture-rainfall combination"
        )

    return (
        "Strong magnitude with shallow depth increases severe shaking probability"
        if seismic >= 5.5 and depth < 25
        else "Current seismic magnitude/depth suggests lower immediate earthquake impact"
    )


def _rule_based_predict(payload: Dict[str, object]) -> Dict[str, object]:
    disaster = (payload.get("disaster") or payload.get("disaster_type") or "").lower()

    rainfall_24h = float(payload.get("rainfall_24h_mm") or 0)
    rainfall_7d = float(payload.get("rainfall_7d_mm") or 0)
    soil_moisture = float(payload.get("soil_moisture") or 0)
    slope_deg = float(payload.get("slope_deg") or 0)
    ndvi = float(payload.get("ndvi") or 0.5)
    seismic_mag = float(payload.get("seismic_mag") or payload.get("seismic_magnitude") or 0)
    depth_km = float(payload.get("depth_km") or 0)

    score = 0
    reasons: List[str] = []

    if disaster == "flood":
        if rainfall_24h > 120:
            score += 35
            reasons.append("Heavy rainfall in last 24h")
        elif rainfall_24h > 60:
            score += 20
            reasons.append("Moderate rainfall in last 24h")

        if rainfall_7d > 250:
            score += 25
            reasons.append("High rainfall accumulation in last 7 days")
        elif rainfall_7d > 120:
            score += 15
            reasons.append("Rainfall accumulation building up")

        if soil_moisture > 0.8:
            score += 20
            reasons.append("Soil moisture very high (water saturation)")
        elif soil_moisture > 0.6:
            score += 10
            reasons.append("Soil moisture elevated")

        if ndvi < 0.35:
            score += 10
            reasons.append("Low vegetation cover increases runoff")

    elif disaster == "landslide":
        if slope_deg > 35:
            score += 35
            reasons.append("Steep slope area")
        elif slope_deg > 20:
            score += 20
            reasons.append("Moderate slope area")

        if rainfall_24h > 80:
            score += 25
            reasons.append("Heavy rainfall trigger")
        elif rainfall_24h > 40:
            score += 15
            reasons.append("Moderate rainfall trigger")

        if soil_moisture > 0.75:
            score += 20
            reasons.append("Soil saturation weakens slope stability")

        if ndvi < 0.35:
            score += 10
            reasons.append("Low vegetation reduces slope binding")

    elif disaster == "earthquake":
        if seismic_mag >= 6.0:
            score += 70
            reasons.append("Strong seismic activity detected")
        elif seismic_mag >= 5.0:
            score += 50
            reasons.append("Moderate seismic activity detected")
        elif seismic_mag >= 4.0:
            score += 25
            reasons.append("Minor seismic activity detected")

        if depth_km and depth_km < 20:
            score += 15
            reasons.append("Shallow depth increases surface impact")
    else:
        return {"success": False, "error": "Invalid disaster type. Use: earthquake / flood / landslide"}

    score = clamp(score)
    level = classify(score)
    eq = _weighted_equation(payload)

    return {
        "success": True,
        "disaster": disaster,
        "risk_score": score,
        "level": level,
        "risk_level": level.title(),
        "reasons": reasons,
        "method": "Rule-Based",
        "confidence": None,
        "feature_importance": {},
        "top_features": [],
        "human_explanation": _human_explanation(disaster, payload),
        **eq,
        "explanation": reasons,
    }


def predict_risk(payload: Dict[str, object]) -> Dict[str, object]:
    disaster = (payload.get("disaster") or payload.get("disaster_type") or "").lower()
    if disaster not in {"earthquake", "flood", "landslide"}:
        return {"success": False, "error": "Invalid disaster type. Use: earthquake / flood / landslide"}

    try:
        ml = predict_with_model({**payload, "disaster_type": disaster})
        risk_level = str(ml["risk_level"]).title()
        risk_level_upper = risk_level.upper()
        score_100 = {"LOW": 30, "MEDIUM": 60, "HIGH": 85}[risk_level_upper]

        fi = ml.get("feature_importance", {})
        top_features = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:3]
        reasons = [f"ML classifier predicted {risk_level} risk."]
        if ml.get("confidence") is not None:
            reasons.append(f"Confidence = {ml['confidence']:.2f}")

        eq = _weighted_equation(payload)

        return {
            "success": True,
            "disaster": disaster,
            "risk_score": score_100,
            "level": risk_level_upper,
            "risk_level": risk_level,
            "reasons": reasons,
            "method": "ML",
            "confidence": ml.get("confidence"),
            "feature_importance": fi,
            "top_features": [{"feature": f, "importance": v} for f, v in top_features],
            "model_accuracy": ml.get("model_accuracy"),
            "human_explanation": _human_explanation(disaster, payload),
            **eq,
            "explanation": reasons,
        }
    except Exception:
        return _rule_based_predict(payload)
