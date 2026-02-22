"""
Simple Rule-Based Predictor (Formula Engine)
Output:
- risk_score: 0-100
- level: LOW / MEDIUM / HIGH
- reasons: explanation list
"""

def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))

def classify(score):
    if score >= 75:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"

def predict_risk(payload):
    disaster = (payload.get("disaster") or "").lower()

    # Inputs (with defaults)
    rainfall_24h = float(payload.get("rainfall_24h_mm") or 0)
    rainfall_7d = float(payload.get("rainfall_7d_mm") or 0)
    soil_moisture = float(payload.get("soil_moisture") or 0)  # 0..1
    slope_deg = float(payload.get("slope_deg") or 0)
    ndvi = float(payload.get("ndvi") or 0.5)  # 0..1
    plant_density = float(payload.get("plant_density") or 0.5)  # 0..1
    seismic_mag = float(payload.get("seismic_mag") or 0)
    depth_km = float(payload.get("depth_km") or 0)

    score = 0
    reasons = []

    # -------------------------
    # FLOOD
    # -------------------------
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

        # vegetation can reduce runoff slightly
        if ndvi < 0.35:
            score += 10
            reasons.append("Low vegetation cover increases runoff")

        score = clamp(score)

    # -------------------------
    # LANDSLIDE
    # -------------------------
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

        score = clamp(score)

    # -------------------------
    # EARTHQUAKE (Risk estimation only)
    # -------------------------
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

        # shallow depth = stronger shaking at surface
        if depth_km and depth_km < 20:
            score += 15
            reasons.append("Shallow depth increases surface impact")

        score = clamp(score)

    else:
        return {
            "success": False,
            "error": "Invalid disaster type. Use: earthquake / flood / landslide"
        }

    level = classify(score)

    return {
        "success": True,
        "disaster": disaster,
        "risk_score": score,
        "level": level,
        "reasons": reasons
    }
