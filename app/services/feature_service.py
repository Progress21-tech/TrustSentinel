import math
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Account, Beneficiary, Device, Transaction
from app.ml.features import build_ml_features


def _aware(value: datetime | None) -> datetime | None:
    if value is None: return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def extract_features(db: Session, account: Account, amount: float, beneficiary_id: str, device_id: str, at: datetime) -> dict:
    at = _aware(at) or datetime.now(timezone.utc)
    history = list(db.scalars(select(Transaction).where(Transaction.account_id == account.account_id, Transaction.timestamp < at).order_by(Transaction.timestamp.desc()).limit(500)))
    amounts = [float(row.amount) for row in history]
    average = sum(amounts) / len(amounts) if amounts else max(1.0, amount)
    beneficiary_history = any(row.beneficiary_id == beneficiary_id for row in history)
    device_history = any(row.device_id == device_id for row in history)
    ben = db.scalar(select(Beneficiary).where(Beneficiary.beneficiary_id == beneficiary_id))
    device = db.scalar(select(Device).where(Device.device_id == device_id, Device.account_id == account.account_id))
    recent = [row for row in history if (_aware(row.timestamp) or at) >= at - timedelta(hours=24)]
    recent_30 = [row for row in recent if (_aware(row.timestamp) or at) >= at - timedelta(minutes=30)]
    account_created = _aware(account.created_at) or at
    recovery = _aware(account.last_recovery_at)
    recovery_recent = bool(recovery and at - timedelta(days=7) <= recovery <= at)
    ben_age = max(0, (at - (_aware(ben.first_seen_at) or at)).days) if ben else 0
    dev_age = max(0, (at - (_aware(device.first_seen_at) or at)).days) if device else 0
    deviation = amount / max(average, 1.0)
    ben_risk = float(ben.risk_score if ben else 0)
    context = {
        "amount": amount, "log_amount": math.log1p(amount), "transaction_hour": at.hour, "transaction_day": at.weekday(),
        "average_transaction_amount": average, "median_transaction_amount": sorted(amounts)[len(amounts)//2] if amounts else average,
        "max_transaction_amount": max(amounts, default=0), "transaction_count_30m": len(recent_30), "transaction_count_24h": len(recent),
        "average_daily_transactions": len(history) / max(1, ((at - account_created).days + 1)), "amount_deviation_ratio": min(deviation, 1000),
        "time_of_day_deviation": 0.0, "is_new_beneficiary": not beneficiary_history, "beneficiary_age_days": ben_age,
        "beneficiary_risk_score": ben_risk, "beneficiary_transaction_count": sum(r.beneficiary_id == beneficiary_id for r in history),
        "unique_beneficiary_count": len({r.beneficiary_id for r in history}), "is_new_device": not device_history,
        "device_age_days": dev_age, "recent_device_change": bool(account.last_device_change_at and at - timedelta(days=7) <= (_aware(account.last_device_change_at) or at) <= at),
        "device_risk_flag": bool(device and device.risk_flags), "account_age_days": max(0, (at - account_created).days),
        "recent_account_recovery": recovery_recent, "recent_password_reset": False, "recent_pin_reset": False,
        "session_duration_deviation": 0.0, "interaction_velocity": 0.0, "navigation_deviation_score": 0.0,
        "session_anomaly_score": 0.0, "linked_risky_accounts": int(ben_risk >= 60), "linked_risky_devices": int(bool(device and device.risk_flags)),
        "linked_risky_beneficiaries": int(ben_risk >= 60), "beneficiary_in_degree": 0, "beneficiary_out_degree": 0,
        "network_risk_score": ben_risk,
    }
    # One canonical builder also feeds offline training and evaluation.
    context.update(build_ml_features(context))
    return context
