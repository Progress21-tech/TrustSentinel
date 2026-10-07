from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.db.database import get_db
from app.core.security import require_api_key
from app.db.models import Case, Intervention, RiskDecision, Transaction

router = APIRouter(prefix="/v1/metrics", tags=["metrics"], dependencies=[Depends(require_api_key)])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    decisions = list(db.scalars(select(RiskDecision)))
    transactions = list(db.scalars(select(Transaction)))
    cases = list(db.scalars(select(Case)))
    interventions = list(db.scalars(select(Intervention)))
    high = [d for d in decisions if d.risk_band in {"ELEVATED", "HIGH", "CRITICAL"}]
    scams = [c for c in cases if c.outcome == "CONFIRMED_SCAM"]
    amounts = {t.transaction_id: float(t.amount) for t in transactions}
    return {"transactions_evaluated": len(decisions), "high_risk_transactions": len(high),
        "high_risk_rate": round(len(high) / len(decisions), 4) if decisions else 0.0,
        "warnings": sum(i.action == "WARN" for i in interventions), "step_ups": sum(i.action == "STEP_UP" for i in interventions),
        "holds": sum(i.action == "HOLD" for i in interventions), "reviews": sum(i.action == "REVIEW" for i in interventions),
        "confirmed_scam_cases": len(scams), "intervention_rate": round(len(interventions) / len(decisions), 4) if decisions else 0.0,
        "confirmed_scam_rate": round(len(scams) / len(cases), 4) if cases else 0.0,
        "simulated_transaction_value": round(sum(amounts.values()), 2),
        "simulated_high_risk_value": round(sum(amounts.get(d.transaction_id, 0) for d in high), 2),
        "simulated_prevented_loss": round(sum(amounts.get(c.transaction_id, 0) for c in scams), 2),
        "prevented_loss_label": "SIMULATED; not an estimate that every transaction would have been fraudulent",
        "average_latency_ms": round(sum(d.latency_ms for d in decisions) / len(decisions), 3) if decisions else 0.0,
        "cases_created": len(cases), "analyst_actions": sum(c.outcome is not None for c in cases),
        "average_case_resolution_seconds": round(sum((c.updated_at - c.created_at).total_seconds() for c in cases if c.status == "RESOLVED") / max(1, sum(c.status == "RESOLVED" for c in cases)), 2)}
