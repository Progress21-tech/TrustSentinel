FEATURES = ["log_amount", "amount_deviation_ratio", "transaction_count_30m", "transaction_count_24h", "beneficiary_age_days", "is_new_beneficiary", "device_age_days", "is_new_device", "recent_account_recovery", "session_anomaly_score", "beneficiary_risk_score", "network_risk_score"]


def vector(features: dict) -> list[float]:
    return [float(features.get(name, 0)) for name in FEATURES]
