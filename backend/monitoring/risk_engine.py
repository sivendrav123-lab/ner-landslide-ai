def clamp(x):
    return max(0.0, min(100.0, float(x or 0)))


def calculate_risk(**p):
    """Transparent, explainable landslide risk model.

    Inputs are real weather observations and, when available, real sensor readings.
    Missing soil/movement inputs are not fabricated; the caller may supply a
    rainfall-derived soil-stress proxy, which is explicitly identified in the UI.
    """
    rain = clamp(max(
        float(p.get("rainfall_intensity", 0)) / 25 * 100,
        float(p.get("rainfall_24h", 0)) / 150 * 100,
        float(p.get("rainfall_7d", 0)) / 500 * 100,
    ))
    soil = clamp(p.get("soil_moisture", 0))
    slope = clamp(float(p.get("slope_angle", 0)) / 45 * 100)
    movement = clamp(
        float(p.get("ground_movement", 0)) / 20 * 70
        + float(p.get("tilt", 0)) / 10 * 20
        + float(p.get("vibration", 0)) / 10 * 10
    )
    geo = clamp(float(p.get("geological_risk", 0)) * 100)

    score = round(rain * .35 + soil * .25 + slope * .15 + movement * .15 + geo * .10, 2)
    level = "LOW" if score < 25 else "MODERATE" if score < 50 else "HIGH" if score < 75 else "CRITICAL"

    available = sum([
        float(p.get("rainfall_24h", 0)) > 0,
        float(p.get("slope_angle", 0)) > 0,
        float(p.get("geological_risk", 0)) > 0,
        float(p.get("soil_moisture", 0)) > 0,
        float(p.get("ground_movement", 0)) > 0 or float(p.get("tilt", 0)) > 0,
    ])
    confidence = round(55 + available / 5 * 40, 1)

    drivers = []
    if rain >= 60: drivers.append("elevated rainfall")
    if soil >= 60: drivers.append("high soil moisture/stress")
    if slope >= 60: drivers.append("steep terrain")
    if movement >= 40: drivers.append("ground movement/tilt activity")
    if geo >= 70: drivers.append("high geological susceptibility")
    explanation = (
        "Risk is driven by " + ", ".join(drivers) + "."
        if drivers else "Current measured environmental and terrain indicators are relatively low."
    )

    return dict(
        risk_score=score, risk_level=level,
        rainfall_factor=round(rain, 2), soil_moisture_factor=round(soil, 2),
        slope_factor=round(slope, 2), ground_movement_factor=round(movement, 2),
        geological_factor=round(geo, 2), ai_confidence=confidence,
        prediction_horizon="Next 6–12 hours",
        explanation=explanation,
    )
