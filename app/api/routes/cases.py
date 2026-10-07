from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import require_api_key
from app.db.models import AuditLog, Case, RiskDecision, RiskSignal, Transaction, utcnow
from app.schemas.risk import CaseOutcomeRequest

router = APIRouter(prefix="/v1/cases", tags=["cases"], dependencies=[Depends(require_api_key)])


def _case_dict(case: Case, db: Session):
    txn = db.scalar(select(Transaction).where(Transaction.transaction_id == case.transaction_id))
    decision = db.scalar(select(RiskDecision).where(RiskDecision.transaction_id == case.transaction_id))
    signals = list(db.scalars(select(RiskSignal).where(RiskSignal.transaction_id == case.transaction_id)))
    audit_ids = [case.case_id, case.transaction_id]
    if decision:
        audit_ids.append(decision.decision_id)
    timeline = list(db.scalars(select(AuditLog).where(AuditLog.entity_id.in_(audit_ids)).order_by(AuditLog.created_at)))
    return {"case_id": case.case_id, "transaction_id": case.transaction_id, "status": case.status, "outcome": case.outcome,
        "analyst_id": case.analyst_id, "notes": case.notes, "created_at": case.created_at, "updated_at": case.updated_at,
        "transaction": None if txn is None else {"amount": float(txn.amount), "currency": txn.currency, "account_id": txn.account_id},
        "decision": None if decision is None else {"risk_score": decision.risk_score, "risk_band": decision.risk_band,
            "recommended_action": decision.recommended_action, "reason_codes": decision.reason_codes, "explanation": decision.explanation},
        "signals": [{"signal_type": s.signal_type, "source_feature": s.source_feature, "signal_value": s.signal_value, "evidence": s.evidence, "severity": s.severity} for s in signals],
        "timeline": [{"actor": event.actor, "event": event.event, "created_at": event.created_at, "metadata": event.metadata_json} for event in timeline]}


@router.get("")
def list_cases(status: str | None = None, risk_band: str | None = None, date: date | None = None, outcome: str | None = None, db: Session = Depends(get_db)):
    query = select(Case).order_by(Case.created_at.desc())
    if status: query = query.where(Case.status == status.upper())
    if outcome: query = query.where(Case.outcome == outcome.upper())
    if date: query = query.where(func.date(Case.created_at) == date.isoformat())
    cases = list(db.scalars(query))
    if risk_band:
        cases = [c for c in cases if (db.scalar(select(RiskDecision).where(RiskDecision.transaction_id == c.transaction_id)) or RiskDecision(risk_band="")).risk_band == risk_band.upper()]
    return {"items": [_case_dict(c, db) for c in cases], "count": len(cases)}


@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.scalar(select(Case).where(Case.case_id == case_id))
    if not case: raise HTTPException(404, detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case was not found."}})
    return _case_dict(case, db)


@router.post("/{case_id}/outcome")
def set_outcome(case_id: str, request: CaseOutcomeRequest, db: Session = Depends(get_db)):
    case = db.scalar(select(Case).where(Case.case_id == case_id))
    if not case: raise HTTPException(404, detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case was not found."}})
    old = case.status
    case.status = "RESOLVED" if request.outcome in {"CONFIRMED_SCAM", "LEGITIMATE"} else ("ESCALATED" if request.outcome == "ESCALATED" else "IN_REVIEW")
    case.outcome, case.analyst_id, case.notes, case.updated_at = request.outcome, request.analyst_id, request.notes, utcnow()
    db.add(AuditLog(actor=request.analyst_id, event="CASE_OUTCOME_RECORDED", entity_type="case", entity_id=case.case_id,
        metadata_json={"old_status": old, "new_status": case.status, "outcome": request.outcome, "notes": request.notes}))
    db.commit()
    return _case_dict(case, db)
