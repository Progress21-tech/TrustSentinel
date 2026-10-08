"""Controlled feature and cold-start experiments using validation rows only."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION, build_ml_features, vector
from app.ml.predict import registry
from app.risk_engine.rules import action_for, evaluate_signals, risk_band, score_rules
from app.risk_engine.scorer import hybrid_score


def _score(name: str, context: dict) -> dict:
    features = build_ml_features(context)
    row = vector(features)
    pipeline = registry.model
    started = time.perf_counter()
    raw = float(pipeline.decision_function([row])[0])
    elapsed = (time.perf_counter() - started) * 1000
    rank = int(np.searchsorted(registry.reference_scores, raw, side="right"))
    base_risk = 1.0 - rank / len(registry.reference_scores)
    ml = registry.predict(features)
    if ml is None:
        raise RuntimeError("The selected validation artifact is unavailable.")
    rules = score_rules(evaluate_signals(features))
    combined = hybrid_score(rules, ml, registry.rule_score_weight, registry.ml_score_weight)
    band = risk_band(combined, registry.high_risk_threshold)
    standardized = pipeline.named_steps["scale"].transform([row])[0].astype(float).tolist()
    return {
        "case": name,
        "features": features,
        "feature_vector": row,
        "standardized_vector": standardized,
        "raw_decision_function": raw,
        "calibration_rank": rank,
        "reference_count": int(len(registry.reference_scores)),
        "base_anomaly_risk": base_risk,
        "calibration_method": registry.calibration_method,
        "calibration_tail_cutoff": registry.calibration_tail_cutoff,
        "calibrated_ml_score": ml,
        "rules_score": rules,
        "hybrid_score": round(combined, 2),
        "risk_level": band,
        "recommended_action": action_for(band),
        "model_inference_latency_ms": round(elapsed, 4),
    }


def _context(row: dict) -> dict:
    return {name: row[name] for name in FEATURES} | {"amount": float(row["amount"])}


def run() -> dict:
    dataset_path = ROOT / "data" / "synthetic" / "transactions.csv"
    if not registry.is_available:
        raise RuntimeError("Load the newly trained artifact before validation experiments.")
    data = pd.read_csv(dataset_path)
    validation = data[data.dataset_split == "validation"].copy()
    if len(validation) != 2_000:
        raise ValueError("Validation experiments require exactly 2,000 validation records.")
    candidates = validation[(validation.synthetic_label == 0) &
                            (validation.has_account_history == 1) &
                            (validation.is_new_beneficiary == 0) &
                            (validation.is_new_device == 0)]
    if candidates.empty:
        raise ValueError("No normal validation record with account history is available as a baseline.")
    base_row = candidates.iloc[0].to_dict()
    baseline = _context(base_row)

    cases: list[tuple[str, dict]] = [("existing_history_baseline", baseline.copy())]

    # Amount sweeps preserve the same baseline or the same no-history state.
    for has_history, label in ((True, "with_history"), (False, "cold_start")):
        amount_base = baseline.copy()
        amount_base["has_account_history"] = has_history
        if not has_history:
            amount_base.update({
                "amount_deviation_ratio": 1, "transaction_count_30m": 0,
                "transaction_count_24h": 0, "beneficiary_transaction_count": 0,
                "unique_beneficiary_count": 0, "average_daily_transactions": 0,
            })
        for amount in (10_000, 50_000, 100_000, 500_000, 1_000_000):
            variant = amount_base.copy()
            variant["amount"] = amount
            if has_history:
                average = float(base_row.get("amount_history_mean", 0) or 0)
                if average > 0:
                    variant["amount_deviation_ratio"] = amount / average
                else:
                    # Use the baseline row's observed ratio as its implied reference.
                    original_amount = max(float(base_row["amount"]), 1.0)
                    implied_mean = original_amount / max(float(base_row["amount_deviation_ratio"]), 1e-6)
                    variant["amount_deviation_ratio"] = amount / max(implied_mean, 1.0)
            else:
                variant["amount_deviation_ratio"] = 1
            cases.append((f"amount_{amount}_{label}", variant))

    new_beneficiary = baseline.copy()
    new_beneficiary.update({"is_new_beneficiary": 1, "beneficiary_transaction_count": 0})
    cases.append(("new_beneficiary", new_beneficiary))
    existing_beneficiary = baseline.copy()
    existing_beneficiary.update({"is_new_beneficiary": 0,
                                  "beneficiary_transaction_count": max(1, int(baseline["beneficiary_transaction_count"]))})
    cases.append(("existing_beneficiary", existing_beneficiary))
    new_device = baseline.copy()
    new_device.update({"is_new_device": 1, "device_age_days": 0, "recent_device_change": 1})
    cases.append(("new_device", new_device))
    existing_device = baseline.copy()
    existing_device.update({"is_new_device": 0, "device_age_days": max(30, int(baseline["device_age_days"])), "recent_device_change": 0})
    cases.append(("existing_device", existing_device))
    velocity = baseline.copy()
    velocity.update({"transaction_count_30m": 3, "transaction_count_24h": max(8, int(baseline["transaction_count_24h"]))})
    cases.append(("high_velocity", velocity))
    recovery = baseline.copy()
    recovery["recent_account_recovery"] = 1
    cases.append(("recent_recovery", recovery))
    risky_beneficiary = baseline.copy()
    risky_beneficiary["beneficiary_risk_score"] = 85
    cases.append(("risky_beneficiary", risky_beneficiary))

    cold_start = baseline.copy()
    cold_start.update({
        "has_account_history": 0, "amount_deviation_ratio": 1,
        "transaction_count_30m": 0, "transaction_count_24h": 0,
        "beneficiary_transaction_count": 0, "unique_beneficiary_count": 0,
        "average_daily_transactions": 0, "account_age_days": 0,
        "beneficiary_age_days": 0, "device_age_days": 0,
        "is_new_beneficiary": 1, "is_new_device": 1,
        "recent_device_change": 0, "recent_account_recovery": 0,
    })
    cases.append(("new_account_cold_start", cold_start))
    combined = cold_start.copy()
    combined.update({"amount": max(250_000, float(baseline["amount"]) * 4),
                     "amount_deviation_ratio": 1, "recent_account_recovery": 1,
                     "beneficiary_risk_score": 85, "transaction_count_30m": 3,
                     "transaction_count_24h": 8})
    cases.append(("combined_cold_start", combined))

    results = [_score(name, context) for name, context in cases]
    baseline_vector = results[0]["features"]
    comparisons = []
    for result in results:
        changed = [name for name in FEATURES if result["features"][name] != baseline_vector[name]]
        comparisons.append({
            "case": result["case"], "changed_features": changed,
            "raw_decision_function": result["raw_decision_function"],
            "calibrated_ml_score": result["calibrated_ml_score"],
            "rules_score": result["rules_score"], "hybrid_score": result["hybrid_score"],
            "risk_level": result["risk_level"], "recommended_action": result["recommended_action"],
        })
    report = {
        "evaluation_type": "synthetic validation-only controlled input experiments",
        "dataset_version": registry.training_dataset_version,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "model_version": registry.model_version,
        "policy_version": registry.policy_version,
        "calibration_method": registry.calibration_method,
        "reference_count": int(len(registry.reference_scores)),
        "validation_rows_used_as_baseline_pool": int(len(candidates)),
        "comparisons": comparisons,
        "cases": results,
        "test_split_used": False,
    }
    destination = ROOT / "data" / "generated" / "validation_experiments.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("model_version", "policy_version", "calibration_method", "reference_count", "comparisons")}, indent=2))
    print(f"Saved validation experiments to {destination}")
    return report


if __name__ == "__main__":
    run()
