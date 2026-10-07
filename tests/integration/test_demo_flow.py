from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base
from app.db.models import AuditLog, Case, RiskDecision, RiskSignal, Transaction
from app.services.demo_service import run_scenario

def test_scenario_persists_decision_signals_case_and_outcome_audit():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    result = run_scenario(session, "combined_high_risk")
    assert result["transaction_id"] == "DEMO-COMBINED-001"
    assert result["reason_codes"]
    assert result["case_id"]
    assert session.scalar(select(Transaction).where(Transaction.transaction_id == result["transaction_id"]))
    assert session.scalar(select(RiskDecision).where(RiskDecision.transaction_id == result["transaction_id"]))
    assert session.scalar(select(RiskSignal).where(RiskSignal.transaction_id == result["transaction_id"]))
    assert session.scalar(select(AuditLog).where(AuditLog.entity_id == result["case_id"]))
    session.close(); engine.dispose()
