"""Research predictor module (additive).

Hybrid predictor design:
1) Physics-informed weighted formula.
2) Rule boosts for compound hazard situations.
3) ML-ready output structure (normalized features + contributions).
"""

from __future__ import annotations

from typing import Dict, Tuple


WEIGHTS = {
    "S": 0.24,   # seismic_mag
    "D": 0.16,   # inverse depth
    "Rf": 0.20,  # rainfall_24h_mm
    "M": 0.14,   # soil_moisture
    "Sl": 0.16,  # slope_deg
    "V": 0.10,   # vegetation inverse (1 - ndvi)
}


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def normalize(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return clamp((value - lo) / (hi - lo))


def _coerce_float(payload: Dict[str, object], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def compute_formula_terms(payload: Dict[str, object]) -> Dict[str, float]:
    """Compute normalized formula terms.

    Formula terms:
    S  = seismic_mag (normalized to [0,1] over [0,8])
    D  = inverse depth_km (1 - normalized depth over [0,300])
    Rf = rainfall_24h_mm (normalized over [0,320])
    M  = soil_moisture (clamped [0,1])
    Sl = slope_deg (normalized over [0,60])
    V  = vegetation inverse (1 - ndvi)
    """

    seismic_mag = _coerce_float(payload, "seismic_mag")
    depth_km = _coerce_float(payload, "depth_km")
    rainfall_24h_mm = _coerce_float(payload, "rainfall_24h_mm")
    soil_moisture = _coerce_float(payload, "soil_moisture")
    slope_deg = _coerce_float(payload, "slope_deg")
    ndvi = _coerce_float(payload, "ndvi", 0.5)

    terms = {
        "S": normalize(seismic_mag, 0.0, 8.0),
        "D": 1.0 - normalize(depth_km, 0.0, 300.0),
        "Rf": normalize(rainfall_24h_mm, 0.0, 320.0),
        "M": clamp(soil_moisture),
        "Sl": normalize(slope_deg, 0.0, 60.0),
        "V": 1.0 - clamp(ndvi),
    }
    return terms


def map_risk(score: float) -> str:
    if score < 0.4:
        return "Low"
    if score <= 0.7:
        return "Medium"
    return "High"


def _rule_adjustment(payload: Dict[str, object]) -> Tuple[float, list[str]]:
    """Rule layer for hybrid behavior (small bounded adjustments)."""

    disaster_type = str(payload.get("disaster_type", "")).lower()
    seismic_mag = _coerce_float(payload, "seismic_mag")
    rainfall = _coerce_float(payload, "rainfall_24h_mm")
    soil_moisture = _coerce_float(payload, "soil_moisture")
    slope_deg = _coerce_float(payload, "slope_deg")

    delta = 0.0
    reasons: list[str] = []

    if disaster_type == "earthquake" and seismic_mag >= 6.0:
        delta += 0.08
        reasons.append("Strong seismic magnitude observed (>= 6.0).")

    if disaster_type == "flood" and rainfall >= 180:
        delta += 0.07
        reasons.append("Extreme 24h rainfall elevates flood probability.")

    if disaster_type == "landslide" and slope_deg >= 40 and soil_moisture >= 0.75:
        delta += 0.09
        reasons.append("Steep wet slope combination indicates instability.")

    if rainfall >= 120 and soil_moisture >= 0.8:
        delta += 0.04
        reasons.append("Rainfall and soil saturation are jointly high.")

    return delta, reasons


def predict_hybrid(payload: Dict[str, object]) -> Dict[str, object]:
    disaster_type = str(payload.get("disaster_type") or payload.get("disaster") or "").lower()
    if disaster_type not in {"earthquake", "flood", "landslide"}:
        return {
            "success": False,
            "error": "Invalid disaster_type. Use earthquake, flood, or landslide.",
        }

    normalized_terms = compute_formula_terms(payload)

    # Research formula (requested):
    # R = w1*S + w2*D + w3*Rf + w4*M + w5*Sl + w6*V
    base_score = sum(WEIGHTS[k] * normalized_terms[k] for k in WEIGHTS)
    delta, rule_reasons = _rule_adjustment({**payload, "disaster_type": disaster_type})
    risk_score = clamp(base_score + delta)
    risk_level = map_risk(risk_score)

    contributions = {
        "seismic_mag": round(WEIGHTS["S"] * normalized_terms["S"], 4),
        "depth_inverse": round(WEIGHTS["D"] * normalized_terms["D"], 4),
        "rainfall_24h_mm": round(WEIGHTS["Rf"] * normalized_terms["Rf"], 4),
        "soil_moisture": round(WEIGHTS["M"] * normalized_terms["M"], 4),
        "slope_deg": round(WEIGHTS["Sl"] * normalized_terms["Sl"], 4),
        "vegetation_inverse": round(WEIGHTS["V"] * normalized_terms["V"], 4),
        "rule_adjustment": round(delta, 4),
    }

    explanation = [
        f"Base formula score: {base_score:.3f}",
        f"Rule adjustment: {delta:+.3f}",
        f"Mapped risk level: {risk_level}",
    ] + rule_reasons

    return {
        "success": True,
        "disaster_type": disaster_type,
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "normalized_terms": {k: round(v, 4) for k, v in normalized_terms.items()},
        "contributions": contributions,
        "explanation": explanation,
        "model_ready_features": {
            "seismic_mag": _coerce_float(payload, "seismic_mag"),
            "depth_km": _coerce_float(payload, "depth_km"),
            "rainfall_24h_mm": _coerce_float(payload, "rainfall_24h_mm"),
            "soil_moisture": _coerce_float(payload, "soil_moisture"),
            "slope_deg": _coerce_float(payload, "slope_deg"),
            "ndvi": _coerce_float(payload, "ndvi", 0.5),
            "plant_density": _coerce_float(payload, "plant_density", 0.5),
            "past_event_count": _coerce_float(payload, "past_event_count", 0),
        },
    }
