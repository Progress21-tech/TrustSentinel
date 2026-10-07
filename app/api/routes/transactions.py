from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import require_api_key
from app.db.models import Case, Intervention, RiskDecision, RiskSignal, Transaction

router = APIRouter(prefix="/v1/transactions", tags=["transactions"], dependencies=[Depends(require_api_key)])


@router.get("/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    txn = db.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id))
    if not txn: raise HTTPException(404, detail={"error": {"code": "TRANSACTION_NOT_FOUND", "message": "Transaction was not found."}})
    decision = db.scalar(select(RiskDecision).where(RiskDecision.transaction_id == transaction_id))
    case = db.scalar(select(Case).where(Case.transaction_id == transaction_id))
    intervention = db.scalar(select(Intervention).where(Intervention.transaction_id == transaction_id))
    signals = list(db.scalars(select(RiskSignal).where(RiskSignal.transaction_id == transaction_id)))
    return {"transaction": {"transaction_id": txn.transaction_id, "account_id": txn.account_id, "beneficiary_id": txn.beneficiary_id,
        "device_id": txn.device_id, "amount": float(txn.amount), "currency": txn.currency, "channel": txn.channel,
        "status": txn.status, "timestamp": txn.timestamp},
        "risk_signals": [{"signal_type": s.signal_type, "severity": s.severity, "source_feature": s.source_feature, "signal_value": s.signal_value, "evidence": s.evidence} for s in signals],
        "risk_decision": None if decision is None else {"risk_score": decision.risk_score, "risk_band": decision.risk_band,
        "recommended_action": decision.recommended_action, "reason_codes": decision.reason_codes, "explanation": decision.explanation},
        "intervention": None if intervention is None else {"action": intervention.action, "customer_response": intervention.customer_response},
        "case_id": case.case_id if case else None}
