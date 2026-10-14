from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import TenantPrincipal, require_api_key
from app.core.tenancy import external_identifier
from app.db.models import AuditLog, Case, RiskDecision, RiskSignal, Transaction, utcnow
from app.schemas.risk import CaseOutcomeRequest

router = APIRouter(prefix="/v1/cases", tags=["cases"], dependencies=[Depends(require_api_key)])


def _case_dict(case: Case, db: Session, institution_id: str):
    txn = db.scalar(select(Transaction).where(Transaction.institution_id == institution_id, Transaction.transaction_id == case.transaction_id))
    decision = db.scalar(select(RiskDecision).where(RiskDecision.institution_id == institution_id, RiskDecision.transaction_id == case.transaction_id))
    signals = list(db.scalars(select(RiskSignal).where(RiskSignal.institution_id == institution_id, RiskSignal.transaction_id == case.transaction_id)))
    audit_ids = [case.case_id, case.transaction_id]
    if decision:
        audit_ids.append(decision.decision_id)
    timeline = list(db.scalars(select(AuditLog).where(AuditLog.institution_id == institution_id, AuditLog.entity_id.in_(audit_ids)).order_by(AuditLog.created_at)))
    timeline_items = []
    for event in timeline:
        metadata = dict(event.metadata_json or {})
        for field, kind in (("transaction_id", "transaction"), ("account_id", "account"), ("beneficiary_id", "beneficiary"), ("device_id", "device")):
            if metadata.get(field):
                metadata[field] = external_identifier(db, institution_id, kind, metadata[field])
        timeline_items.append({"actor": event.actor, "event": event.event, "created_at": event.created_at, "metadata": metadata})
    return {"case_id": case.case_id, "transaction_id": external_identifier(db, institution_id, "transaction", case.transaction_id),
        "status": case.status, "outcome": case.outcome, "analyst_id": case.analyst_id, "notes": case.notes,
        "created_at": case.created_at, "updated_at": case.updated_at,
        "transaction": None if txn is None else {"amount": float(txn.amount), "currency": txn.currency,
            "account_id": external_identifier(db, institution_id, "account", txn.account_id)},
        "decision": None if decision is None else {"risk_score": decision.risk_score, "risk_band": decision.risk_band,
            "recommended_action": decision.recommended_action, "reason_codes": decision.reason_codes, "explanation": decision.explanation},
        "signals": [{"signal_type": s.signal_type, "source_feature": s.source_feature, "signal_value": s.signal_value,
            "evidence": s.evidence, "severity": s.severity} for s in signals],
        "timeline": timeline_items}


@router.get("")
def list_cases(status: str | None = None, risk_band: str | None = None, date: date | None = None,
               outcome: str | None = None, principal: TenantPrincipal = Depends(require_api_key), db: Session = Depends(get_db)):
    institution_id = principal.institution_id
    query = select(Case).where(Case.institution_id == institution_id).order_by(Case.created_at.desc())
    if status: query = query.where(Case.status == status.upper())
    if outcome: query = query.where(Case.outcome == outcome.upper())
    if date: query = query.where(func.date(Case.created_at) == date.isoformat())
    cases = list(db.scalars(query))
    if risk_band:
        cases = [case for case in cases if (db.scalar(select(RiskDecision).where(
            RiskDecision.institution_id == institution_id, RiskDecision.transaction_id == case.transaction_id)) or RiskDecision(risk_band="")).risk_band == risk_band.upper()]
    return {"items": [_case_dict(case, db, institution_id) for case in cases], "count": len(cases)}


@router.get("/{case_id}")
def get_case(case_id: str, principal: TenantPrincipal = Depends(require_api_key), db: Session = Depends(get_db)):
    case = db.scalar(select(Case).where(Case.institution_id == principal.institution_id, Case.case_id == case_id))
    if not case:
        raise HTTPException(404, detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case was not found."}})
    return _case_dict(case, db, principal.institution_id)


@router.post("/{case_id}/outcome")
def set_outcome(case_id: str, request: CaseOutcomeRequest, principal: TenantPrincipal = Depends(require_api_key), db: Session = Depends(get_db)):
    institution_id = principal.institution_id
    case = db.scalar(select(Case).where(Case.institution_id == institution_id, Case.case_id == case_id))
    if not case:
        raise HTTPException(404, detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case was not found."}})
    old = case.status
    case.status = "RESOLVED" if request.outcome in {"CONFIRMED_SCAM", "FALSE_POSITIVE", "LEGITIMATE"} else ("ESCALATED" if request.outcome == "ESCALATED" else "IN_REVIEW")
    case.outcome, case.analyst_id, case.notes, case.updated_at = request.outcome, principal.subject, request.notes, utcnow()
    db.add(AuditLog(institution_id=institution_id, actor=principal.subject, event="CASE_OUTCOME_RECORDED",
        entity_type="case", entity_id=case.case_id,
        metadata_json={"old_status": old, "new_status": case.status, "outcome": request.outcome, "notes": request.notes,
            "transaction_id": case.transaction_id}))
    db.commit()
    return _case_dict(case, db, institution_id)
