"""Canonical numeric feature schema shared by training, evaluation and inference."""
from __future__ import annotations

import math
from collections.abc import Mapping

FEATURE_SCHEMA_VERSION = "trustsentinel-context-v1"
FEATURES = (
    "log_amount",
    "amount_deviation_ratio",
    "transaction_hour",
    "time_of_day_deviation",
    "transaction_count_30m",
    "transaction_count_24h",
    "beneficiary_age_days",
    "beneficiary_risk_score",
    "beneficiary_transaction_count",
    "unique_beneficiary_count",
    "is_new_beneficiary",
    "device_age_days",
    "is_new_device",
    "recent_device_change",
    "recent_account_recovery",
    "recent_password_reset",
    "recent_pin_reset",
    "session_duration_deviation",
    "interaction_velocity",
    "navigation_deviation_score",
    "session_anomaly_score",
    "linked_risky_accounts",
    "linked_risky_devices",
    "linked_risky_beneficiaries",
    "beneficiary_in_degree",
    "beneficiary_out_degree",
    "network_risk_score",
    "account_age_days",
    "average_daily_transactions",
)

_BOOLEAN_FEATURES = {
    "is_new_beneficiary", "is_new_device", "recent_device_change",
    "recent_account_recovery", "recent_password_reset", "recent_pin_reset",
}
_PROBABILITY_FEATURES = {
    "time_of_day_deviation", "session_duration_deviation", "interaction_velocity",
    "navigation_deviation_score", "session_anomaly_score",
}
_COUNT_FEATURES = {
    "transaction_count_30m", "transaction_count_24h", "beneficiary_transaction_count",
    "unique_beneficiary_count", "linked_risky_accounts", "linked_risky_devices",
    "linked_risky_beneficiaries", "beneficiary_in_degree", "beneficiary_out_degree",
}
_AGE_FEATURES = {"beneficiary_age_days", "device_age_days", "account_age_days"}


def _number(value: object, default: float = 0.0) -> float:
    """Convert missing or malformed data to finite numeric input."""
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return default
        if normalized in {"true", "false"}:
            return float(normalized == "true")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return result if math.isfinite(result) else default


def _boolean(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, str):
        return float(value.strip().lower() in {"true", "1", "yes"})
    return float(_number(value, 0.0) != 0.0)


def build_ml_features(context: Mapping[str, object]) -> dict[str, float]:
    """Build named features from event/context facts; labels and scenario IDs are ignored.

    Amount is in account currency units, time is UTC hour, ages are days, velocity
    values are event counts in their named windows, and score/proxy values are 0–100
    (risk scores) or 0–1 (session deviations). The persisted sklearn pipeline scales
    continuous values. Missing, NaN, and infinite values become finite defaults.
    """
    amount = max(0.0, _number(context.get("amount", math.expm1(max(0.0, _number(context.get("log_amount")))))))
    average = max(1.0, _number(context.get("average_transaction_amount"), amount or 1.0))
    raw = {
        "log_amount": math.log1p(amount) if "amount" in context else max(0.0, _number(context.get("log_amount"))),
        "amount_deviation_ratio": min(1000.0, max(0.0, _number(context.get("amount_deviation_ratio"), amount / average))),
        "transaction_hour": min(23.0, max(0.0, _number(context.get("transaction_hour")))),
        "time_of_day_deviation": _number(context.get("time_of_day_deviation")),
        "transaction_count_30m": _number(context.get("transaction_count_30m")),
        "transaction_count_24h": _number(context.get("transaction_count_24h")),
        "beneficiary_age_days": _number(context.get("beneficiary_age_days")),
        "beneficiary_risk_score": _number(context.get("beneficiary_risk_score")),
        "beneficiary_transaction_count": _number(context.get("beneficiary_transaction_count")),
        "unique_beneficiary_count": _number(context.get("unique_beneficiary_count")),
        "is_new_beneficiary": _boolean(context.get("is_new_beneficiary", False)),
        "device_age_days": _number(context.get("device_age_days")),
        "is_new_device": _boolean(context.get("is_new_device", False)),
        "recent_device_change": _boolean(context.get("recent_device_change", False)),
        "recent_account_recovery": _boolean(context.get("recent_account_recovery", False)),
        "recent_password_reset": _boolean(context.get("recent_password_reset", False)),
        "recent_pin_reset": _boolean(context.get("recent_pin_reset", False)),
        "session_duration_deviation": _number(context.get("session_duration_deviation")),
        "interaction_velocity": _number(context.get("interaction_velocity")),
        "navigation_deviation_score": _number(context.get("navigation_deviation_score")),
        "session_anomaly_score": _number(context.get("session_anomaly_score")),
        "linked_risky_accounts": _number(context.get("linked_risky_accounts")),
        "linked_risky_devices": _number(context.get("linked_risky_devices")),
        "linked_risky_beneficiaries": _number(context.get("linked_risky_beneficiaries")),
        "beneficiary_in_degree": _number(context.get("beneficiary_in_degree")),
        "beneficiary_out_degree": _number(context.get("beneficiary_out_degree")),
        "network_risk_score": _number(context.get("network_risk_score")),
        "account_age_days": _number(context.get("account_age_days")),
        "average_daily_transactions": _number(context.get("average_daily_transactions")),
    }
    for name in _BOOLEAN_FEATURES:
        raw[name] = _boolean(raw[name])
    for name in _PROBABILITY_FEATURES:
        raw[name] = min(1.0, max(0.0, raw[name]))
    for name in {"beneficiary_risk_score", "network_risk_score"}:
        raw[name] = min(100.0, max(0.0, raw[name]))
    for name in _COUNT_FEATURES:
        raw[name] = min(100_000.0, max(0.0, raw[name]))
    for name in _AGE_FEATURES:
        raw[name] = min(100_000.0, max(0.0, raw[name]))
    raw["average_daily_transactions"] = min(100_000.0, max(0.0, raw["average_daily_transactions"]))
    return {name: float(raw[name]) if math.isfinite(float(raw[name])) else 0.0 for name in FEATURES}


def vector(features: Mapping[str, object]) -> list[float]:
    """Return a stable, finite, named-schema ordered row for scikit-learn."""
    built = build_ml_features(features)
    return [built[name] for name in FEATURES]
