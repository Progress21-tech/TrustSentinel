"""Compare rules-only, ML-only and hybrid scores on one deterministic held-out set."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.core.config import settings
from app.db.database import Base
from app.db.models import AuditLog, Case, RiskDecision, RiskSignal, Transaction
from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION, build_ml_features, vector
from app.ml.predict import ModelRegistry, registry
from app.risk_engine.rules import action_for, evaluate_signals, risk_band, score_rules
from app.risk_engine.scorer import hybrid_score
from app.services.demo_service import run_scenario
from scripts.generate_data import generate

SCENARIOS = (
    "new_beneficiary_large_amount",
    "new_device_large_transfer",
    "rapid_transfers",
    "risky_beneficiary",
    "account_recovery_new_beneficiary",
    "combined_high_risk",
    "normal",
    "legitimate_high_value",
)


def _confusion(labels: list[int], predictions: list[int]) -> dict:
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predictions))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predictions))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predictions))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predictions))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "accuracy": (tp + tn) / max(1, tp + tn + fp + fn),
        "high_risk_precision_proxy": precision,
        "high_risk_recall_proxy": recall,
        "f1_proxy": 2 * precision * recall / max(1e-12, precision + recall),
        "false_positive_proxy": fp / max(1, fp + tn),
    }


def _evaluation_set(path: Path) -> pd.DataFrame:
    try:
        expected_seed = int(registry.training_dataset_version.rsplit("-seed-", 1)[1])
    except (AttributeError, IndexError, ValueError):
        raise ValueError("Model artifact is missing its synthetic dataset seed/version.")
    if not path.exists():
        generate(seed=expected_seed)
    data = pd.read_csv(path)
    required = {"dataset_split", "synthetic_label", "evaluation_scenario", "dataset_seed", "amount"}
    if not required.issubset(data.columns):
        raise ValueError("Evaluation dataset schema is stale; run python scripts/generate_data.py first.")
    held_out = data[data["dataset_split"] == "test"].copy()
    if held_out.empty:
        raise ValueError("The deterministic held-out test split is empty.")
    seeds = data["dataset_seed"].dropna().unique().tolist()
    if seeds != [expected_seed]:
        raise ValueError(f"Evaluation data seed {seeds} does not match model dataset {registry.training_dataset_version}; regenerate and retrain together.")
    return held_out


def evaluate() -> dict:
    artifact_path = Path(settings.model_path)
    if not artifact_path.is_absolute():
        artifact_path = ROOT / artifact_path
    if not artifact_path.is_file() or not registry.is_available:
        raise RuntimeError("A calibrated model artifact is required; run python scripts/train_model.py first.")
    data = _evaluation_set(ROOT / "data" / "synthetic" / "transactions.csv")
    labels = [int(value) for value in data["synthetic_label"].tolist()]

    rule_scores, ml_scores, hybrid_scores, ml_times = [], [], [], []
    for record in data.to_dict("records"):
        features = build_ml_features(record)
        # vector() applies the same named schema and order used by online inference.
        if len(vector(features)) != len(FEATURES):
            raise ValueError("Feature vector length drift detected.")
        rule_score = score_rules(evaluate_signals(features))
        started = time.perf_counter()
        ml_score = registry.predict(features)
        ml_times.append((time.perf_counter() - started) * 1000)
        if ml_score is None:
            raise RuntimeError("ML inference failed while evaluating the held-out dataset.")
        rule_scores.append(rule_score)
        ml_scores.append(ml_score * 100.0)
        hybrid_scores.append(hybrid_score(rule_score, ml_score, settings.rule_score_weight, settings.ml_score_weight))

    predictions = {
        "rules_only": [int(score >= 60) for score in rule_scores],
        "ml_only": [int(score >= settings.ml_high_risk_threshold * 100) for score in ml_scores],
        "hybrid": [int(score >= 60) for score in hybrid_scores],
    }
    methods = {
        "rules_only": {"threshold": 60, "metrics": _confusion(labels, predictions["rules_only"])},
        "ml_only": {"threshold": settings.ml_high_risk_threshold * 100, "metrics": _confusion(labels, predictions["ml_only"])},
        "hybrid": {"threshold": 60, "metrics": _confusion(labels, predictions["hybrid"])},
    }
    scenario_metrics = {}
    for name, group in data.groupby("evaluation_scenario", sort=True):
        indices = group.index.tolist()
        scenario_metrics[str(name)] = {
            "records": len(group),
            "synthetic_high_risk_records": int(group["synthetic_label"].sum()),
            "rules_median_score": statistics.median(rule_scores[data.index.get_loc(index)] for index in indices),
            "ml_median_score": statistics.median(ml_scores[data.index.get_loc(index)] for index in indices),
            "hybrid_median_score": statistics.median(hybrid_scores[data.index.get_loc(index)] for index in indices),
            "hybrid_high_risk_rate": sum(predictions["hybrid"][data.index.get_loc(index)] for index in indices) / len(indices),
        }

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    scenario_runs = []
    try:
        for name in SCENARIOS:
            result = run_scenario(session, name)
            transaction = session.scalar(select(Transaction).where(Transaction.transaction_id == result["transaction_id"]))
            decision = session.scalar(select(RiskDecision).where(RiskDecision.transaction_id == result["transaction_id"]))
            signal_count = len(list(session.scalars(select(RiskSignal).where(RiskSignal.transaction_id == result["transaction_id"]))))
            audit = session.scalar(select(AuditLog).where(AuditLog.entity_id == (decision.decision_id if decision else "")))
            case = session.scalar(select(Case).where(Case.transaction_id == result["transaction_id"]))
            scenario_runs.append({
                "scenario": name, "transaction_id": result["transaction_id"], "risk_score": result["risk_score"],
                "risk_band": result["risk_band"], "recommended_action": result["recommended_action"],
                "reason_codes": result["reason_codes"], "explanation": result["explanation"],
                "rules_score": result["rule_score"], "ml_score": result["ml_score"], "ml_status": result["ml_status"],
                "latency_ms": result["latency_ms"], "decision_persisted": decision is not None,
                "transaction_persisted": transaction is not None, "triggered_signals_persisted": signal_count,
                "audit_persisted": audit is not None, "case_id": case.case_id if case else None,
            })
    finally:
        session.close()
        engine.dispose()

    normal_count = len(labels) - sum(labels)
    positive_scenarios = sorted(data.loc[data["synthetic_label"] == 1, "evaluation_scenario"].astype(str).unique().tolist())
    report = {
        "evaluation_type": "synthetic prototype only; not real-world fraud performance",
        "dataset_version": registry.training_dataset_version,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "model_version": registry.model_version,
        "records": len(labels), "normal_records": normal_count, "synthetic_high_risk_records": sum(labels),
        "scenario_coverage": positive_scenarios, "scenario_coverage_count": len(positive_scenarios),
        "classification_threshold_definition": "risk score >= 60 is high risk; ML-only uses configured ML score threshold",
        "methods": methods,
        "ml_inference_latency_ms": {"mean": statistics.mean(ml_times), "median": statistics.median(ml_times)},
        "by_scenario": scenario_metrics,
        "api_scenario_runs": scenario_runs,
    }
    output = ROOT / "data" / "generated" / "evaluation_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved evaluation report to {output}")
    return report


if __name__ == "__main__":
    evaluate()
