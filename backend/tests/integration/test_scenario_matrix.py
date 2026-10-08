from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import AuditLog, Case, RiskDecision, RiskSignal, Transaction
from app.ml.predict import registry
from app.risk_engine.rules import action_for, risk_band
from app.services.demo_service import run_scenario

SCENARIOS = (
    "new_beneficiary_large_amount", "new_device_large_transfer", "rapid_transfers",
    "risky_beneficiary", "account_recovery_new_beneficiary", "combined_high_risk",
    "normal", "legitimate_high_value",
)

def test_required_scenarios_use_hybrid_engine_and_persist_decisions():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        for name in SCENARIOS:
            result = run_scenario(session, name)
            assert 0 <= result["risk_score"] <= 100
            assert result["risk_band"] == risk_band(result["risk_score"], registry.high_risk_threshold if registry.is_available else 60)
            assert result["recommended_action"] == action_for(result["risk_band"])
            assert result["transaction_id"]
            assert result["latency_ms"] >= 0
            assert result["ml_status"] in {"available", "unavailable_rules_only"}
            assert result["ml_score"] is None or 0 <= result["ml_score"] <= 1
            transaction_id = result["transaction_id"]
            decision = session.scalar(select(RiskDecision).where(RiskDecision.transaction_id == transaction_id))
            assert decision is not None and decision.rule_score >= 0
            assert session.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id)) is not None
            assert session.scalar(select(AuditLog).where(AuditLog.entity_id == decision.decision_id)) is not None
            if result["reason_codes"]:
                assert result["explanation"]
            if result["recommended_action"] in {"HOLD", "REVIEW"}:
                assert session.scalar(select(Case).where(Case.transaction_id == transaction_id)) is not None
            if name == "legitimate_high_value":
                # It may receive friction, but amount alone must not hold or review it.
                assert result["recommended_action"] not in {"HOLD", "REVIEW"}
    finally:
        session.close()
        engine.dispose()
