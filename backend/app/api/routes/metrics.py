from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.db.database import get_db
from app.core.security import TenantPrincipal, require_api_key
from app.db.models import Case, Intervention, RiskDecision, Transaction

router = APIRouter(prefix="/v1/metrics", tags=["metrics"], dependencies=[Depends(require_api_key)])


@router.get("/summary")
def summary(principal: TenantPrincipal = Depends(require_api_key), db: Session = Depends(get_db)):
    institution_id = principal.institution_id
    decisions = list(db.scalars(select(RiskDecision).where(RiskDecision.institution_id == institution_id)))
    transactions = list(db.scalars(select(Transaction).where(Transaction.institution_id == institution_id)))
    cases = list(db.scalars(select(Case).where(Case.institution_id == institution_id)))
    interventions = list(db.scalars(select(Intervention).where(Intervention.institution_id == institution_id)))
    high = [decision for decision in decisions if decision.risk_band in {"ELEVATED", "HIGH", "CRITICAL"}]
    scams = [case for case in cases if case.outcome == "CONFIRMED_SCAM"]
    amounts = {txn.transaction_id: float(txn.amount) for txn in transactions}
    return {"transactions_evaluated": len(decisions), "high_risk_transactions": len(high),
        "high_risk_rate": round(len(high) / len(decisions), 4) if decisions else 0.0,
        "warnings": sum(item.action == "WARN" for item in interventions),
        "step_ups": sum(item.action == "STEP_UP" for item in interventions),
        "holds": sum(item.action == "HOLD" for item in interventions),
        "reviews": sum(item.action == "REVIEW" for item in interventions),
        "confirmed_scam_cases": len(scams),
        "intervention_rate": round(len(interventions) / len(decisions), 4) if decisions else 0.0,
        "confirmed_scam_rate": round(len(scams) / len(cases), 4) if cases else 0.0,
        "simulated_transaction_value": round(sum(amounts.values()), 2),
        "simulated_high_risk_value": round(sum(amounts.get(item.transaction_id, 0) for item in high), 2),
        "simulated_prevented_loss": round(sum(amounts.get(item.transaction_id, 0) for item in scams), 2),
        "prevented_loss_label": "SIMULATED; not an estimate that every transaction would have been fraudulent",
        "average_latency_ms": round(sum(item.latency_ms for item in decisions) / len(decisions), 3) if decisions else 0.0,
        "cases_created": len(cases), "analyst_actions": sum(case.outcome is not None for case in cases),
        "average_case_resolution_seconds": round(sum((case.updated_at - case.created_at).total_seconds()
            for case in cases if case.status == "RESOLVED") / max(1, sum(case.status == "RESOLVED" for case in cases)), 2)}
