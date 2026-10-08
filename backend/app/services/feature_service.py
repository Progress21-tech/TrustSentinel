from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, Beneficiary, Device, Transaction
from app.ml.features import extract_feature_context


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def extract_features(db: Session, account: Account, amount: float, beneficiary_id: str, device_id: str, at: datetime) -> dict[str, float]:
    at = _aware(at) or datetime.now(timezone.utc)
    history = list(db.scalars(
        select(Transaction).where(
            Transaction.account_id == account.account_id,
            Transaction.timestamp < at,
        ).order_by(Transaction.timestamp.desc()).limit(500)
    ))
    beneficiary = db.scalar(select(Beneficiary).where(Beneficiary.beneficiary_id == beneficiary_id))
    device = db.scalar(select(Device).where(
        Device.device_id == device_id,
        Device.account_id == account.account_id,
    ))
    return extract_feature_context(
        amount=amount,
        at=at,
        account_created_at=_aware(account.created_at) or at,
        history=history,
        beneficiary_id=beneficiary_id,
        device_id=device_id,
        beneficiary_first_seen_at=_aware(beneficiary.first_seen_at) if beneficiary else None,
        device_first_seen_at=_aware(device.first_seen_at) if device else None,
        beneficiary_risk_score=float(beneficiary.risk_score or 0.0) if beneficiary else 0.0,
        last_device_change_at=_aware(account.last_device_change_at),
        last_recovery_at=_aware(account.last_recovery_at),
    )
