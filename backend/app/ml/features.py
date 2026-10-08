"""Canonical, serving-available feature contract shared by training and inference."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone

FEATURE_SCHEMA_VERSION = "trustsentinel-context-v2"
FEATURES = (
    "log_amount",
    "amount_deviation_ratio",
    "has_account_history",
    "transaction_hour",
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
    "account_age_days",
    "average_daily_transactions",
)

_BOOLEAN_FEATURES = {
    "has_account_history", "is_new_beneficiary", "is_new_device",
    "recent_device_change", "recent_account_recovery",
}
_COUNT_FEATURES = {
    "transaction_count_30m", "transaction_count_24h",
    "beneficiary_transaction_count", "unique_beneficiary_count",
}
_AGE_FEATURES = {"beneficiary_age_days", "device_age_days", "account_age_days"}


def _number(value: object, default: float = 0.0) -> float:
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
    if isinstance(value, str):
        return float(value.strip().lower() in {"true", "1", "yes"})
    return float(_number(value) != 0.0)


def build_ml_features(context: Mapping[str, object]) -> dict[str, float]:
    """Bound and order source-derived context; labels and unknown keys are ignored."""
    amount = max(0.0, _number(context.get("amount")))
    has_history = _boolean(context.get("has_account_history", False))
    fallback_ratio = 1.0 if not has_history else 0.0
    raw = {
        "log_amount": math.log1p(amount),
        # 1 is a neutral fallback only when has_account_history=0; the flag
        # keeps this distinct from a measured ratio of exactly one.
        "amount_deviation_ratio": _number(context.get("amount_deviation_ratio"), fallback_ratio),
        "has_account_history": has_history,
        "transaction_hour": _number(context.get("transaction_hour")),
        "transaction_count_30m": _number(context.get("transaction_count_30m")),
        "transaction_count_24h": _number(context.get("transaction_count_24h")),
        "beneficiary_age_days": _number(context.get("beneficiary_age_days")),
        "beneficiary_risk_score": _number(context.get("beneficiary_risk_score")),
        "beneficiary_transaction_count": _number(context.get("beneficiary_transaction_count")),
        "unique_beneficiary_count": _number(context.get("unique_beneficiary_count")),
        "is_new_beneficiary": _boolean(context.get("is_new_beneficiary")),
        "device_age_days": _number(context.get("device_age_days")),
        "is_new_device": _boolean(context.get("is_new_device")),
        "recent_device_change": _boolean(context.get("recent_device_change")),
        "recent_account_recovery": _boolean(context.get("recent_account_recovery")),
        "account_age_days": _number(context.get("account_age_days")),
        "average_daily_transactions": _number(context.get("average_daily_transactions")),
    }
    for name in _BOOLEAN_FEATURES:
        raw[name] = _boolean(raw[name])
    raw["transaction_hour"] = min(23.0, max(0.0, raw["transaction_hour"]))
    raw["beneficiary_risk_score"] = min(100.0, max(0.0, raw["beneficiary_risk_score"]))
    for name in _COUNT_FEATURES | _AGE_FEATURES:
        raw[name] = min(100_000.0, max(0.0, raw[name]))
    raw["amount_deviation_ratio"] = min(1000.0, max(0.0, raw["amount_deviation_ratio"]))
    raw["average_daily_transactions"] = min(100_000.0, max(0.0, raw["average_daily_transactions"]))
    return {name: float(raw[name]) if math.isfinite(float(raw[name])) else 0.0 for name in FEATURES}


def _get(row: object, name: str, default: object = None) -> object:
    if isinstance(row, Mapping):
        return row.get(name, default)
    return getattr(row, name, default)


def _aware(value: object, default: datetime) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return default
    if not isinstance(value, datetime):
        return default
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def extract_feature_context(
    *, amount: float, at: datetime, account_created_at: datetime,
    history: Sequence[object], beneficiary_id: str, device_id: str,
    beneficiary_first_seen_at: datetime | None, device_first_seen_at: datetime | None,
    beneficiary_risk_score: float, last_device_change_at: datetime | None = None,
    last_recovery_at: datetime | None = None,
) -> dict[str, float]:
    """Derive the same live-observable facts from transaction/entity history.

    `history` must contain only events strictly before `at`; both the online
    extractor and synthetic generator call this function.
    """
    at = _aware(at, datetime.now(timezone.utc))
    account_created_at = _aware(account_created_at, at)
    prior = sorted(
        (row for row in history if _aware(_get(row, "timestamp"), at) < at),
        key=lambda row: _aware(_get(row, "timestamp"), at),
    )[-500:]
    amounts = [_number(_get(row, "amount")) for row in prior]
    avg_amount = sum(amounts) / len(amounts) if amounts else 0.0
    recent_24h = [row for row in prior if _aware(_get(row, "timestamp"), at) >= at - timedelta(hours=24)]
    recent_30m = [row for row in recent_24h if _aware(_get(row, "timestamp"), at) >= at - timedelta(minutes=30)]
    account_age = max(0, (at - account_created_at).days)
    ben_count = sum(_get(row, "beneficiary_id") == beneficiary_id for row in prior)
    device_seen = any(_get(row, "device_id") == device_id for row in prior)
    unique_beneficiaries = len({str(_get(row, "beneficiary_id")) for row in prior if _get(row, "beneficiary_id") is not None})
    ratio = amount / max(avg_amount, 1.0) if prior else 1.0

    def in_last_week(event_at: datetime | None) -> bool:
        if event_at is None:
            return False
        event = _aware(event_at, at)
        return at - timedelta(days=7) <= event <= at

    ben_first = _aware(beneficiary_first_seen_at, at) if beneficiary_first_seen_at else at
    dev_first = _aware(device_first_seen_at, at) if device_first_seen_at else at
    derived = {
        "amount": amount,
        "amount_deviation_ratio": min(ratio, 1000.0),
        "has_account_history": bool(prior),
        "transaction_hour": at.hour,
        "transaction_count_30m": len(recent_30m),
        "transaction_count_24h": len(recent_24h),
        "beneficiary_age_days": max(0, (at - ben_first).days),
        "beneficiary_risk_score": beneficiary_risk_score,
        "beneficiary_transaction_count": ben_count,
        "unique_beneficiary_count": unique_beneficiaries,
        "is_new_beneficiary": ben_count == 0,
        "device_age_days": max(0, (at - dev_first).days),
        "is_new_device": not device_seen,
        "recent_device_change": in_last_week(last_device_change_at),
        "recent_account_recovery": in_last_week(last_recovery_at),
        "account_age_days": account_age,
        "average_daily_transactions": len(prior) / max(1, account_age + 1),
    }
    return build_ml_features(derived)


def vector(features: Mapping[str, object]) -> list[float]:
    built = build_ml_features(features)
    return [built[name] for name in FEATURES]
