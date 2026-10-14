from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import TenantPrincipal, require_api_key
from app.core.tenancy import external_identifier, resolve_identifier
from app.db.models import Case, Intervention, RiskDecision, RiskSignal, Transaction

router = APIRouter(prefix="/v1/transactions", tags=["transactions"], dependencies=[Depends(require_api_key)])


def _transaction_key(db: Session, transaction_id: str, principal: TenantPrincipal) -> str:
    return resolve_identifier(db, principal.institution_id, "transaction", transaction_id, Transaction, "transaction_id")


@router.get("")
def list_transactions(principal: TenantPrincipal = Depends(require_api_key), limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    institution_id = principal.institution_id
    transactions = list(db.scalars(select(Transaction).where(Transaction.institution_id == institution_id).order_by(Transaction.timestamp.desc()).limit(limit)))
    items = []
    for txn in transactions:
        decision = db.scalar(select(RiskDecision).where(RiskDecision.institution_id == institution_id, RiskDecision.transaction_id == txn.transaction_id))
        signals = list(db.scalars(select(RiskSignal).where(RiskSignal.institution_id == institution_id, RiskSignal.transaction_id == txn.transaction_id)))
        case = db.scalar(select(Case).where(Case.institution_id == institution_id, Case.transaction_id == txn.transaction_id))
        items.append({
            "transaction_id": external_identifier(db, institution_id, "transaction", txn.transaction_id),
            "account_id": external_identifier(db, institution_id, "account", txn.account_id),
            "amount": float(txn.amount), "currency": txn.currency, "timestamp": txn.timestamp,
            "risk_decision": None if decision is None else {
                "assessment_id": decision.decision_id, "risk_score": decision.risk_score,
                "risk_band": decision.risk_band, "recommended_action": decision.recommended_action,
            },
            "signals": [signal.signal_type for signal in signals], "case_id": case.case_id if case else None,
        })
    return {"items": items, "count": len(items)}


@router.get("/{transaction_id}")
def get_transaction(transaction_id: str, principal: TenantPrincipal = Depends(require_api_key), db: Session = Depends(get_db)):
    institution_id = principal.institution_id
    internal_id = _transaction_key(db, transaction_id, principal)
    txn = db.scalar(select(Transaction).where(Transaction.institution_id == institution_id, Transaction.transaction_id == internal_id))
    if not txn:
        raise HTTPException(404, detail={"error": {"code": "TRANSACTION_NOT_FOUND", "message": "Transaction was not found."}})
    decision = db.scalar(select(RiskDecision).where(RiskDecision.institution_id == institution_id, RiskDecision.transaction_id == internal_id))
    case = db.scalar(select(Case).where(Case.institution_id == institution_id, Case.transaction_id == internal_id))
    intervention = db.scalar(select(Intervention).where(Intervention.institution_id == institution_id, Intervention.transaction_id == internal_id))
    signals = list(db.scalars(select(RiskSignal).where(RiskSignal.institution_id == institution_id, RiskSignal.transaction_id == internal_id)))
    return {"transaction": {"transaction_id": transaction_id,
        "account_id": external_identifier(db, institution_id, "account", txn.account_id),
        "beneficiary_id": external_identifier(db, institution_id, "beneficiary", txn.beneficiary_id),
        "device_id": external_identifier(db, institution_id, "device", txn.device_id),
        "amount": float(txn.amount), "currency": txn.currency, "channel": txn.channel,
        "status": txn.status, "timestamp": txn.timestamp},
        "risk_signals": [{"signal_type": s.signal_type, "severity": s.severity, "source_feature": s.source_feature, "signal_value": s.signal_value, "evidence": s.evidence} for s in signals],
        "risk_decision": None if decision is None else {"assessment_id": decision.decision_id,
            "risk_score": decision.risk_score, "risk_band": decision.risk_band,
            "recommended_action": decision.recommended_action, "reason_codes": decision.reason_codes,
            "explanation": decision.explanation},
        "intervention": None if intervention is None else {"action": intervention.action, "customer_response": intervention.customer_response},
        "case_id": case.case_id if case else None}
