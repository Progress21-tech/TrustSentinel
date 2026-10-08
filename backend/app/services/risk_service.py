import time
import uuid
import json
import logging
import hashlib
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Account, AuditLog, Beneficiary, Case, Device, Intervention, RiskDecision, RiskSignal, Transaction, utcnow
from app.ml.predict import registry
from app.risk_engine.rules import Signal, action_for, evaluate_signals, explain, risk_band, score_rules
from app.risk_engine.scorer import hybrid_score
from app.schemas.risk import RiskRequest
from app.services.feature_service import extract_features
from app.ml.features import FEATURE_SCHEMA_VERSION

logger = logging.getLogger("trustsentinel.risk")


def _response(decision: RiskDecision, signals: list[RiskSignal] | None = None, case: Case | None = None) -> dict:
    return {"transaction_id": decision.transaction_id, "risk_score": decision.risk_score, "risk_band": decision.risk_band,
        "recommended_action": decision.recommended_action, "reason_codes": decision.reason_codes,
        "explanation": decision.explanation, "rule_score": decision.rule_score, "ml_score": decision.ml_score,
        "ml_status": "available" if decision.ml_score is not None else "unavailable_rules_only",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "model_version": decision.model_version, "rule_version": decision.rule_version, "latency_ms": decision.latency_ms,
        "hybrid_policy_version": decision.model_version.split("+", 1)[1] if "+" in decision.model_version else (
            "hybrid-policy-v1.0.0" if decision.model_version.startswith("iforest-") else "rules-only"),
        "signals": [{"signal_type": s.signal_type, "triggered": True, "severity": s.severity, "evidence": s.evidence,
                     "source_feature": s.source_feature} for s in (signals or [])], "case_id": case.case_id if case else None}


def score_transaction(db: Session, request: RiskRequest) -> dict:
    started = time.perf_counter()
    existing = db.scalar(select(RiskDecision).where(RiskDecision.transaction_id == request.transaction_id))
    if existing:
        signals = list(db.scalars(select(RiskSignal).where(RiskSignal.transaction_id == request.transaction_id)))
        case = db.scalar(select(Case).where(Case.transaction_id == request.transaction_id))
        return _response(existing, signals, case)
    account = db.scalar(select(Account).where(Account.account_id == request.account_id))
    if account is None:
        # Identifiers identify an incoming event; they are not a membership gate.
        # Provision minimal synthetic entity records so the event can be persisted
        # while feature extraction treats its entities as previously unseen.
        from app.db.models import Customer
        customer_id = f"score-{hashlib.sha256(request.account_id.encode()).hexdigest()[:32]}"
        customer = db.scalar(select(Customer).where(Customer.customer_id == customer_id))
        if customer is None:
            customer = Customer(customer_id=customer_id, risk_profile="NORMAL", status="ACTIVE")
            db.add(customer)
            db.flush()
        account = Account(account_id=request.account_id, customer_id=customer_id, status="ACTIVE")
        db.add(account)
        db.flush()
    if account.status != "ACTIVE":
        raise HTTPException(status_code=409, detail={"error": {"code": "ACCOUNT_INACTIVE", "message": "The specified account is not active."}})
    if db.scalar(select(Beneficiary).where(Beneficiary.beneficiary_id == request.beneficiary_id)) is None:
        db.add(Beneficiary(beneficiary_id=request.beneficiary_id, status="ACTIVE", risk_score=0.0))
    device = db.scalar(select(Device).where(Device.device_id == request.device_id))
    if device is None:
        db.add(Device(device_id=request.device_id, account_id=request.account_id, risk_flags=[]))
    elif device.account_id != request.account_id:
        raise HTTPException(status_code=422, detail={"error": {"code": "DEVICE_ACCOUNT_MISMATCH", "message": "The specified device belongs to a different account."}})
    db.flush()
    at = request.timestamp or datetime.now(timezone.utc)
    features = extract_features(db, account, request.amount, request.beneficiary_id, request.device_id, at)
    signals = evaluate_signals(features)
    rule_score = score_rules(signals)
    ml_started = time.perf_counter()
    ml_score = registry.predict(features)
    ml_latency_ms = round((time.perf_counter() - ml_started) * 1000, 3)
    if ml_score is not None and ml_score >= settings.ml_anomaly_reason_threshold:
        signals.append(Signal("ML_ANOMALY", True, 0,
            f"Isolation Forest anomaly evidence is in the configured anomalous tail (normalized score {ml_score:.2f}).",
            "ml_score", ml_score))
    # In the rules-only sandbox, unavailable ML contributes no invented score.
    if ml_score is None and not settings.rules_only_fallback:
        raise HTTPException(status_code=503, detail={"error": {"code": "MODEL_UNAVAILABLE", "message": "The configured policy requires the ML model."}})
    rule_weight = registry.rule_score_weight if registry.is_available else settings.rule_score_weight
    ml_weight = registry.ml_score_weight if registry.is_available else settings.ml_score_weight
    final_score = hybrid_score(rule_score, ml_score, rule_weight, ml_weight)
    band = risk_band(final_score, registry.high_risk_threshold if registry.is_available else 60)
    action = action_for(band)
    codes, explanation = explain(signals, band, action)
    txn = Transaction(transaction_id=request.transaction_id, account_id=request.account_id, beneficiary_id=request.beneficiary_id,
        device_id=request.device_id, amount=request.amount, currency=request.currency.upper(), channel=request.channel,
        timestamp=at, status="EVALUATED")
    db.add(txn); db.flush()
    persisted_signals = []
    for signal in signals:
        if signal.triggered:
            row = RiskSignal(signal_id=f"sig_{uuid.uuid4().hex}", transaction_id=txn.transaction_id,
                signal_type=signal.signal_type, source_feature=signal.source_feature, signal_value=signal.value, severity=signal.severity, evidence=signal.evidence)
            db.add(row); persisted_signals.append(row)
    decision = RiskDecision(decision_id=f"dec_{uuid.uuid4().hex}", transaction_id=txn.transaction_id, rule_score=rule_score,
        ml_score=ml_score, risk_score=round(final_score, 2), risk_band=band, recommended_action=action,
        reason_codes=codes, explanation=explanation, model_version=registry.decision_version if ml_score is not None else "rules-only",
        rule_version=settings.rule_version, latency_ms=0.0)
    db.add(decision)
    case = None
    if action in {"HOLD", "REVIEW"}:
        case = Case(case_id=f"case_{uuid.uuid4().hex[:12]}", transaction_id=txn.transaction_id, status="OPEN")
        db.add(case)
        db.add(AuditLog(actor="system", event="CASE_CREATED", entity_type="case", entity_id=case.case_id, metadata_json={"transaction_id": txn.transaction_id}))
    if action != "ALLOW":
        db.add(Intervention(intervention_id=f"int_{uuid.uuid4().hex}", transaction_id=txn.transaction_id, action=action))
    db.add(AuditLog(actor="system", event="RISK_DECISION_CREATED", entity_type="risk_decision", entity_id=decision.decision_id,
                    metadata_json={"transaction_id": txn.transaction_id, "risk_score": round(final_score, 2), "risk_band": band, "action": action, "reason_codes": codes,
                        "rule_score": rule_score, "ml_score": ml_score,
                        "model_version": registry.model_version if ml_score is not None else "rules-only",
                        "hybrid_policy_version": registry.policy_version if ml_score is not None else "rules-only",
                        "ml_status": "available" if ml_score is not None else "unavailable_rules_only"}))
    db.flush()
    latency = round((time.perf_counter() - started) * 1000, 3)
    decision.latency_ms = latency
    db.flush()
    db.commit()
    logger.info(json.dumps({"event": "risk_decision", "transaction_id": txn.transaction_id,
        "model_status": "available" if ml_score is not None else "unavailable_rules_only",
        "model_version": registry.model_version if ml_score is not None else "rules-only",
        "hybrid_policy_version": registry.policy_version if ml_score is not None else "rules-only",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "rules_score": round(rule_score, 3), "ml_score": ml_score, "hybrid_score": round(final_score, 3),
        "risk_band": band, "action": action, "ml_inference_latency_ms": ml_latency_ms, "decision_latency_ms": latency}))
    return _response(decision, persisted_signals, case)
