"""Hybrid predictor: rule-based risk + ensemble ML probability fusion.

US-4: improved modular rule estimators
US-6: Risk_final = alpha * Rule_Score + (1 - alpha) * ML_Probability
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

from ml_hybrid_predictor import predict_hybrid_ml
from satellite_predictor import predict_satellite_risk
try:
    from cnn_satellite import run_auto_cnn_prediction
except Exception:
    def run_auto_cnn_prediction():
        return {"success": False, "flood_prob": 0.0, "landslide_prob": 0.0, "confidence": 0.0}


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def classify_probability(p: float) -> str:
    if p > 0.7:
        return "HIGH"
    if p >= 0.40:
        return "MEDIUM"
    return "LOW"


def _f(payload: Dict[str, object], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in payload and payload.get(key) not in (None, ""):
            try:
                return float(payload.get(key) or default)
            except (TypeError, ValueError):
                continue
    return default


def _n(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return clamp((value - lo) / (hi - lo))


def compute_rule_risk_earthquake(payload: Dict[str, object]) -> Tuple[float, List[str]]:
    mag = _f(payload, "seismic_magnitude", "seismic_mag")
    depth = _f(payload, "depth_km")

    mag_n = _n(mag, 0.0, 8.5)
    shallow_n = 1.0 - _n(depth, 0.0, 300.0)

    score = 0.72 * mag_n + 0.28 * shallow_n
    reasons = [
        f"Magnitude contribution={mag_n:.2f}",
        f"Shallow-depth contribution={shallow_n:.2f}",
    ]

    if mag >= 6.0 and depth <= 25:
        score += 0.08
        reasons.append("Strong shallow earthquake amplification applied")

    return clamp(score), reasons


def compute_rule_risk_flood(payload: Dict[str, object]) -> Tuple[float, List[str]]:
    rain24 = _f(payload, "rainfall_24h_mm")
    rain7d = _f(payload, "rainfall_7d_mm", default=rain24 * 3.2)
    soil = _f(payload, "soil_moisture")

    rain24_n = _n(rain24, 0.0, 350.0)
    rain7d_n = _n(rain7d, 0.0, 1400.0)
    soil_n = clamp(soil)

    score = 0.38 * rain24_n + 0.34 * rain7d_n + 0.28 * soil_n
    reasons = [
        f"24h rainfall contribution={rain24_n:.2f}",
        f"7d rainfall accumulation contribution={rain7d_n:.2f}",
        f"Soil saturation contribution={soil_n:.2f}",
    ]

    if rain24 > 140 and soil > 0.75:
        score += 0.08
        reasons.append("Rainfall-soil threshold boost applied")

    return clamp(score), reasons


def compute_rule_risk_landslide(payload: Dict[str, object]) -> Tuple[float, List[str]]:
    slope = _f(payload, "slope_deg")
    ndvi = _f(payload, "ndvi", default=0.5)
    rain24 = _f(payload, "rainfall_24h_mm")
    rain7d = _f(payload, "rainfall_7d_mm", default=rain24 * 3.0)
    soil = _f(payload, "soil_moisture")

    slope_n = _n(slope, 0.0, 60.0)
    ndvi_inv = 1.0 - clamp(ndvi)
    cum_rain_n = _n(rain24 + 0.45 * rain7d, 0.0, 950.0)
    soil_n = clamp(soil)

    score = 0.35 * slope_n + 0.20 * ndvi_inv + 0.30 * cum_rain_n + 0.15 * soil_n
    reasons = [
        f"Slope contribution={slope_n:.2f}",
        f"Vegetation-loss contribution={ndvi_inv:.2f}",
        f"Cumulative rainfall contribution={cum_rain_n:.2f}",
    ]

    if slope > 35 and ndvi < 0.35 and (rain24 + rain7d) > 220:
        score += 0.08
        reasons.append("Steep-sparse-wet slope boost applied")

    return clamp(score), reasons


def _weighted_equation(payload: Dict[str, object]) -> dict:
    rainfall = _f(payload, "rainfall_24h_mm")
    slope = _f(payload, "slope_deg")
    soil = _f(payload, "soil_moisture")
    seismic = _f(payload, "seismic_mag", "seismic_magnitude")
    depth = _f(payload, "depth_km")
    ndvi = _f(payload, "ndvi", default=0.5)

    rain_n = _n(rainfall, 0, 350)
    slope_n = _n(slope, 0, 60)
    soil_n = clamp(soil)
    seismic_n = _n(seismic, 0, 8)
    depth_inv = 1.0 - _n(depth, 0, 300)
    veg_inv = 1.0 - clamp(ndvi)

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
    rainfall = _f(payload, "rainfall_24h_mm")
    slope = _f(payload, "slope_deg")
    soil = _f(payload, "soil_moisture")
    seismic = _f(payload, "seismic_mag", "seismic_magnitude")
    depth = _f(payload, "depth_km")

    if disaster == "flood":
        return (
            "Elevated rainfall accumulation and soil saturation increase flood potential"
            if rainfall > 120 and soil > 0.65
            else "Current hydro-meteorological indicators suggest moderated flood potential"
        )
    if disaster == "landslide":
        return (
            "Steep slope, cumulative rain, and weak vegetation increase landslide potential"
            if slope > 30 and rainfall > 90
            else "Present slope-rainfall-vegetation pattern indicates lower landslide potential"
        )

    return (
        "High magnitude with shallow depth increases expected earthquake impact"
        if seismic >= 5.5 and depth < 25
        else "Current magnitude-depth combination indicates lower earthquake impact"
    )


def _compute_rule_score(disaster: str, payload: Dict[str, object]) -> Tuple[float, List[str]]:
    if disaster == "earthquake":
        return compute_rule_risk_earthquake(payload)
    if disaster == "flood":
        return compute_rule_risk_flood(payload)
    if disaster == "landslide":
        return compute_rule_risk_landslide(payload)
    return 0.0, ["Invalid disaster type"]


def _build_rule_only_result(disaster: str, payload: Dict[str, object], alpha: float, error: str | None = None) -> Dict[str, object]:
    rule_score, rule_reasons = _compute_rule_score(disaster, payload)
    sat = predict_satellite_risk(disaster_type=disaster, feature_overrides=payload)
    sat_score = float(sat.get("satellite_score") or 0.0)
    cnn = run_auto_cnn_prediction()
    cnn_score = float(cnn.get("flood_prob") or 0.0) if disaster == "flood" else float(cnn.get("landslide_prob") or 0.0) if disaster == "landslide" else float(cnn.get("confidence") or 0.0) * 0.5
    final_p = clamp(0.55 * rule_score + 0.25 * sat_score + 0.20 * cnn_score)
    level = classify_probability(final_p)
    eq = _weighted_equation(payload)

    explanation = [
        "Rule-only fallback used",
        f"Rule score={rule_score:.3f}",
        f"Fusion alpha={alpha:.2f}",
    ] + rule_reasons
    if error:
        explanation.append(f"ML unavailable: {error}")

    return {
        "success": True,
        "disaster": disaster,
        "risk_score": round(final_p * 100, 2),
        "risk_level": level.title(),
        "level": level,
        "method": "Rule-Based Fallback",
        "ml_probability": None,
        "rule_score": round(rule_score, 4),
        "satellite_score": round(sat_score, 4),
        "cnn_score": round(cnn_score, 4),
        "final_risk_probability": round(final_p, 4),
        "confidence": round(final_p, 4),
        "alpha": alpha,
        "feature_importance": {},
        "top_features": [],
        "reasons": explanation,
        "explanation": explanation,
        "human_explanation": _human_explanation(disaster, payload),
        **eq,
    }


def predict_risk(payload: Dict[str, object]) -> Dict[str, object]:
    disaster = (payload.get("disaster") or payload.get("disaster_type") or "").lower()
    if disaster not in {"earthquake", "flood", "landslide"}:
        return {"success": False, "error": "Invalid disaster type. Use: earthquake / flood / landslide"}

    alpha = clamp(float(os.getenv("RISK_ALPHA", "0.4")), 0.0, 1.0)
    rule_score, rule_reasons = _compute_rule_score(disaster, payload)

    try:
        ml = predict_hybrid_ml({**payload, "disaster_type": disaster})
        ml_prob = float(ml.get("ml_probability") or ml.get("confidence") or 0.0)
        sat = predict_satellite_risk(disaster_type=disaster, feature_overrides=payload)
        sat_score = float(sat.get("satellite_score") or 0.0)
        cnn = run_auto_cnn_prediction()
        cnn_score = float(cnn.get("flood_prob") or 0.0) if disaster == "flood" else float(cnn.get("landslide_prob") or 0.0) if disaster == "landslide" else float(cnn.get("confidence") or 0.0) * 0.5

        final_p = clamp(0.25 * rule_score + 0.30 * ml_prob + 0.25 * sat_score + 0.20 * cnn_score)
        level = classify_probability(final_p)
        eq = _weighted_equation(payload)

        fi = ml.get("feature_importance", {})
        top_features = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:3]

        explanation = [
            "Fusion formula: final=0.25*rule + 0.30*ml + 0.25*satellite + 0.20*cnn",
            f"Rule score={rule_score:.3f}, ML probability={ml_prob:.3f}, satellite score={sat_score:.3f}, cnn score={cnn_score:.3f}, final={final_p:.3f}",
            f"Weather source={ml.get('weather_source', 'fallback')}",
            f"Inference latency={ml.get('latency_ms', 0)} ms",
        ] + rule_reasons

        return {
            "success": True,
            "disaster": disaster,
            "risk_score": round(final_p * 100, 2),
            "risk_level": level.title(),
            "level": level,
            "method": "Hybrid (Rule + Ensemble ML)",
            "ml_probability": round(ml_prob, 4),
            "rule_score": round(rule_score, 4),
            "satellite_score": round(sat_score, 4),
            "cnn_score": round(cnn_score, 4),
            "final_risk_probability": round(final_p, 4),
            "confidence": round(max(ml_prob, final_p), 4),
            "alpha": alpha,
            "feature_importance": fi,
            "top_features": [{"feature": f, "importance": v} for f, v in top_features],
            "probabilities": ml.get("probabilities", {}),
            "model_accuracy": ml.get("model_accuracy"),
            "weather_source": ml.get("weather_source"),
            "latency_ms": ml.get("latency_ms"),
            "ensemble": ml.get("ensemble"),
            "satellite_details": sat,
            "cnn_details": cnn,
            "reasons": explanation,
            "explanation": explanation,
            "human_explanation": _human_explanation(disaster, payload),
            **eq,
        }
    except Exception as exc:
        return _build_rule_only_result(disaster, payload, alpha=alpha, error=str(exc))
