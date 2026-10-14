from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, Beneficiary, Customer, Device, Transaction
from app.core.tenancy import resolve_identifier
from app.schemas.risk import RiskRequest
from app.services.risk_service import score_transaction

DEMO_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

SCENARIOS = {
    "normal": ("DEMO-NORMAL-001", "acct-demo-normal", 45000, False, False, False, False, 0),
    "new_beneficiary_large_amount": ("DEMO-NEW-BENEFICIARY-001", "acct-demo-new-ben", 850000, True, False, False, False, 0),
    "new_device_large_transfer": ("DEMO-NEW-DEVICE-001", "acct-demo-new-device", 700000, False, True, False, False, 0),
    "account_recovery_new_beneficiary": ("DEMO-RECOVERY-001", "acct-demo-recovery", 900000, True, False, True, False, 0),
    "rapid_transfers": ("DEMO-VELOCITY-001", "acct-demo-velocity", 80000, True, True, False, False, 4),
    "risky_beneficiary": ("DEMO-RISKY-BENEFICIARY-001", "acct-demo-risky-ben", 150000, True, False, False, True, 0),
    "combined_high_risk": ("DEMO-COMBINED-001", "acct-demo-combined", 1200000, True, True, True, True, 4),
    "legitimate_high_value": ("DEMO-LEGIT-HIGH-VALUE-001", "acct-demo-legit-high", 2000000, False, False, False, False, 0),
}


def _ensure_scenario(db: Session, scenario: str, institution_id: str):
    txn_id, account_id, amount, new_ben, new_device, recovery, risky, velocity = SCENARIOS[scenario]
    account_db_id = resolve_identifier(db, institution_id, "account", account_id, Account, "account_id")
    customer_external = f"customer-{account_id}"
    customer_id = resolve_identifier(db, institution_id, "customer", customer_external, Customer, "customer_id")
    customer = db.scalar(select(Customer).where(Customer.institution_id == institution_id, Customer.customer_id == customer_id))
    now = DEMO_AT
    if customer is None:
        customer = Customer(institution_id=institution_id, customer_id=customer_id, risk_profile="HIGH_VALUE" if scenario == "legitimate_high_value" else "NORMAL")
        db.add(customer); db.flush()
    account = db.scalar(select(Account).where(Account.institution_id == institution_id, Account.account_id == account_db_id))
    if account is None:
        account = Account(institution_id=institution_id, account_id=account_db_id, customer_id=customer_id, created_at=now - timedelta(days=900),
                          last_recovery_at=now - timedelta(days=1) if recovery else None)
        db.add(account); db.flush()
    ben_external = f"beneficiary-{account_id}-new" if new_ben or risky else f"beneficiary-{account_id}-trusted"
    dev_external = f"device-{account_id}-new" if new_device else f"device-{account_id}-trusted"
    ben_id = resolve_identifier(db, institution_id, "beneficiary", ben_external, Beneficiary, "beneficiary_id")
    dev_id = resolve_identifier(db, institution_id, "device", dev_external, Device, "device_id")
    ben = db.scalar(select(Beneficiary).where(Beneficiary.institution_id == institution_id, Beneficiary.beneficiary_id == ben_id))
    if ben is None:
        db.add(Beneficiary(institution_id=institution_id, beneficiary_id=ben_id, first_seen_at=now - timedelta(days=90) if not new_ben else now,
                           risk_score=85 if risky else 0))
    dev = db.scalar(select(Device).where(Device.institution_id == institution_id, Device.device_id == dev_id, Device.account_id == account_db_id))
    if dev is None:
        db.add(Device(institution_id=institution_id, device_id=dev_id, account_id=account_db_id, first_seen_at=now - timedelta(days=180) if not new_device else now,
                      risk_flags=["synthetic_risk"] if risky and new_device else []))
    db.flush()
    txn_db_id = resolve_identifier(db, institution_id, "transaction", txn_id, Transaction, "transaction_id")
    if not db.scalar(select(Transaction).where(Transaction.institution_id == institution_id, Transaction.transaction_id == txn_db_id)):
        baseline = 2_000_000 if scenario == "legitimate_high_value" else 20_000
        hist_ben_external = f"beneficiary-{account_id}-trusted"
        hist_device_external = f"device-{account_id}-trusted"
        hist_ben = resolve_identifier(db, institution_id, "beneficiary", hist_ben_external, Beneficiary, "beneficiary_id")
        hist_device = resolve_identifier(db, institution_id, "device", hist_device_external, Device, "device_id")
        db.add(Beneficiary(institution_id=institution_id, beneficiary_id=hist_ben, first_seen_at=now - timedelta(days=365), risk_score=0)) if db.scalar(select(Beneficiary).where(Beneficiary.institution_id == institution_id, Beneficiary.beneficiary_id == hist_ben)) is None else None
        db.add(Device(institution_id=institution_id, device_id=hist_device, account_id=account_db_id, first_seen_at=now - timedelta(days=365), risk_flags=[])) if db.scalar(select(Device).where(Device.institution_id == institution_id, Device.device_id == hist_device, Device.account_id == account_db_id)) is None else None
        for index in range(max(3, velocity)):
            db.add(Transaction(transaction_id=resolve_identifier(db, institution_id, "transaction", f"hist-{account_id}-{index}", Transaction, "transaction_id"), institution_id=institution_id, account_id=account_db_id, beneficiary_id=hist_ben,
                device_id=hist_device, amount=baseline, currency="NGN", channel="mobile_app",
                timestamp=now - timedelta(minutes=5 * (index + 1)) if index < velocity else now - timedelta(days=30 + index)))
        db.commit()
    return txn_id, account_id, amount, ben_external, dev_external, recovery


def run_scenario(db: Session, scenario: str, request_id: str | None = None, institution_id: str = "default") -> dict:
    txn_id, account_id, amount, ben_id, dev_id, recovery = _ensure_scenario(db, scenario, institution_id)
    return score_transaction(db, RiskRequest(transaction_id=txn_id, account_id=account_id, amount=amount,
        currency="NGN", beneficiary_id=ben_id, device_id=dev_id, channel="mobile_app", timestamp=DEMO_AT), request_id=request_id, institution_id=institution_id)
