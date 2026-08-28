from .risk_engine import calculate_risk
def predict_risk(payload): return calculate_risk(**payload)
