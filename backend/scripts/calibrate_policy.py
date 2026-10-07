"""Select hybrid policy settings on validation data without reading held-out rows."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION, build_ml_features, vector
from app.risk_engine.rules import evaluate_signals, score_rules
from app.risk_engine.scorer import hybrid_score
from scripts.train_model import fit_model

WEIGHTS = ((0.80, 0.20), (0.75, 0.25), (0.70, 0.30), (0.65, 0.35), (0.60, 0.40))
THRESHOLDS = tuple(value / 100 for value in range(55, 66))
LEGITIMATE_SCENARIOS = {"normal", "legitimate_high_value", "legitimate_business_high_value"}


def _metrics(labels: list[int], predictions: list[int]) -> dict[str, float | int]:
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predictions))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predictions))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predictions))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predictions))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision, "recall": recall,
        "f1": 2 * precision * recall / max(1e-12, precision + recall),
        "false_positive_rate": fp / max(1, fp + tn),
    }


def _scenario_metrics(data: pd.DataFrame, scores: list[float], predictions: list[int]) -> dict:
    output = {}
    for scenario, group in data.groupby("evaluation_scenario", sort=True):
        indexes = [data.index.get_loc(index) for index in group.index]
        group_scores = [scores[index] for index in indexes]
        group_predictions = [predictions[index] for index in indexes]
        output[str(scenario)] = {
            "records": len(indexes),
            "positive_labels": int(group["synthetic_label"].sum()),
            "median_score": float(np.median(group_scores)),
            "high_risk_rate": float(np.mean(group_predictions)),
        }
    return output


def _summarize(labels: list[int], data: pd.DataFrame, scores: list[float], threshold: float) -> dict:
    predictions = [int(score >= threshold) for score in scores]
    return {
        "threshold": threshold,
        "metrics": _metrics(labels, predictions),
        "scenario_metrics": _scenario_metrics(data, scores, predictions),
    }


def calibrate() -> dict:
    dataset_path = ROOT / "data" / "synthetic" / "transactions.csv"
    if not dataset_path.is_file():
        raise FileNotFoundError("Generate synthetic data before calibration.")
    data = pd.read_csv(dataset_path)
    required = {"dataset_split", "synthetic_label", "evaluation_scenario", "dataset_seed"}
    if not required.issubset(data.columns):
        raise ValueError("Dataset lacks split/label/scenario metadata; regenerate it.")
    train = data[data.dataset_split == "train"].copy()
    validation = data[data.dataset_split == "validation"].copy()
    # Intentionally never select, score, or summarize rows tagged test in this script.
    if train.empty or validation.empty or (data.dataset_split == "test").sum() != 2_000:
        raise ValueError("Expected non-empty train/validation splits and the unchanged 2,000-row held-out test split.")
    train_normal = train[train.synthetic_label == 0]
    if len(train_normal) < max(100, len(FEATURES) * 5):
        raise ValueError("Insufficient normal training rows for Isolation Forest.")

    x_train = np.asarray([vector(build_ml_features(row)) for row in train_normal.to_dict("records")], dtype=float)
    x_valid = np.asarray([vector(build_ml_features(row)) for row in validation.to_dict("records")], dtype=float)
    if not np.isfinite(x_train).all() or not np.isfinite(x_valid).all():
        raise ValueError("Non-finite feature values found during calibration.")

    model, normal_reference = fit_model(
        x_train, settings.ml_random_state, settings.ml_n_estimators,
        settings.ml_contamination, settings.ml_max_samples, settings.ml_max_features,
    )
    raw_train = model.decision_function(x_train).astype(float)
    raw_valid = model.decision_function(x_valid).astype(float)
    normal_reference = np.sort(normal_reference)
    train_base_risk = 1.0 - np.searchsorted(normal_reference, raw_train, side="right") / len(normal_reference)
    valid_base_risk = 1.0 - np.searchsorted(normal_reference, raw_valid, side="right") / len(normal_reference)

    thresholds_from_train = {
        f"normal_tail_q{int(q * 100)}": float(np.quantile(train_base_risk, q))
        for q in (0.80, 0.90, 0.95)
    }
    # Keep named candidate cutoffs distinct in the report and selection metadata.
    calibration_candidates = [("empirical_lower_tail_percentile_v1", None)] + [
        ("normal_tail_excess_v1", cutoff) for cutoff in thresholds_from_train.values()
    ]

    labels = [int(value) for value in validation.synthetic_label.tolist()]
    validation = validation.reset_index(drop=True)
    rules = [score_rules(evaluate_signals(build_ml_features(row))) for row in validation.to_dict("records")]
    search = []
    current_baseline = None
    current_weights_at_threshold = []
    calibration_summary = []
    for calibration_method, cutoff in calibration_candidates:
        if calibration_method == "empirical_lower_tail_percentile_v1":
            ml = np.clip(valid_base_risk, 0.0, 1.0)
        else:
            ml = np.clip((valid_base_risk - float(cutoff)) / max(1e-12, 1.0 - float(cutoff)), 0.0, 1.0)
        for rule_weight, ml_weight in WEIGHTS:
            scores = [hybrid_score(rule, float(anomaly), rule_weight, ml_weight) for rule, anomaly in zip(rules, ml)]
            for threshold in THRESHOLDS:
                result = _summarize(labels, validation, scores, threshold * 100)
                result.update({"rule_weight": rule_weight, "ml_weight": ml_weight,
                    "calibration_method": calibration_method, "calibration_tail_cutoff": cutoff})
                search.append(result)
                if threshold == 0.60:
                    if calibration_method == "empirical_lower_tail_percentile_v1" and (rule_weight, ml_weight) == (0.70, 0.30):
                        current_baseline = result
                    if calibration_method == "empirical_lower_tail_percentile_v1":
                        current_weights_at_threshold.append(result)
                    if (rule_weight, ml_weight) == (0.70, 0.30):
                        calibration_summary.append(result)

    validation_baselines = {
        "rules_only": _summarize(labels, validation, rules, 60),
        "ml_only": _summarize(labels, validation, (valid_base_risk * 100).tolist(), settings.ml_high_risk_threshold * 100),
        "hybrid_70_30_60": current_baseline,
    }

    def safe(candidate: dict) -> bool:
        scenarios_result = candidate["scenario_metrics"]
        return all(scenarios_result.get(name, {}).get("high_risk_rate", 0.0) == 0.0 for name in LEGITIMATE_SCENARIOS)

    selectable = [entry for entry in search if entry["threshold"] == 60 and
                  entry["metrics"]["precision"] > 0.90 and
                  entry["metrics"]["false_positive_rate"] < 0.10 and safe(entry)]
    eligible_pool = selectable or [entry for entry in search if entry["threshold"] == 60 and
                                   entry["metrics"]["false_positive_rate"] < 0.10 and safe(entry)]
    if not eligible_pool:
        raise RuntimeError("No validation candidate preserves normal/legitimate scenario safety with false-positive rate below 10%.")
    no_regression = [entry for entry in selectable if
                     entry["metrics"]["recall"] >= current_baseline["metrics"]["recall"] and
                     entry["metrics"]["f1"] >= current_baseline["metrics"]["f1"]]
    if no_regression:
        selected = min(no_regression, key=lambda entry: (
            abs(entry["rule_weight"] - 0.70) + abs(entry["ml_weight"] - 0.30) +
            (0.0 if entry["calibration_method"] == "empirical_lower_tail_percentile_v1" else 1.0),
            -entry["metrics"]["f1"], -entry["metrics"]["recall"],
        ))
        selection_reason = "smallest_change_meeting_precision_false_positive_safety_and_validation_recall_f1_non_regression"
    elif selectable:
        selected = max(selectable, key=lambda entry: (
            entry["metrics"]["f1"], entry["metrics"]["recall"], entry["metrics"]["precision"],
        ))
        selection_reason = "highest_validation_f1_among_candidates_meeting_precision_false_positive_and_legitimate_safety_constraints"
    else:
        selected = max(eligible_pool, key=lambda entry: (
            entry["metrics"]["f1"], entry["metrics"]["recall"], entry["metrics"]["precision"],
        ))
        selection_reason = "best_validation_f1_under_false_positive_and_legitimate_safety_constraints; precision_target_not_met"
    selected_policy_version = (
        "hybrid-policy-v1.0.0"
        if selected["rule_weight"] == 0.70 and selected["ml_weight"] == 0.30 and
        selected["calibration_method"] == "empirical_lower_tail_percentile_v1"
        else "hybrid-policy-v1.1.0"
    )
    selected_policy = {
        "dataset_version": f"trustsentinel-synthetic-v1-seed-{int(data.dataset_seed.iloc[0])}",
        "split_version": "train_validation_test_v1",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "rule_weight": selected["rule_weight"],
        "ml_weight": selected["ml_weight"],
        "high_risk_threshold": 60,
        "calibration_method": selected["calibration_method"],
        "calibration_tail_cutoff": selected["calibration_tail_cutoff"],
        "policy_version": selected_policy_version,
        "selection_reason": selection_reason,
    }
    report = {
        "evaluation_type": "synthetic validation only; not real-world fraud performance",
        "dataset_version": f"trustsentinel-synthetic-v1-seed-{int(data.dataset_seed.iloc[0])}",
        "split_version": "train_validation_test_v1",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "split_counts": {str(name): int(count) for name, count in data.dataset_split.value_counts().items()},
        "split_definition": "Existing every-fifth test rows preserved; one fifth of remaining rows assigned validation; all other rows train.",
        "test_split_used": False,
        "training_rows": int(len(train)), "training_normal_rows": int(len(train_normal)),
        "validation_rows": int(len(validation)),
        "model_hyperparameters": {
            "algorithm": "IsolationForest", "n_estimators": settings.ml_n_estimators,
            "max_samples": settings.ml_max_samples, "contamination": settings.ml_contamination,
            "max_features": settings.ml_max_features, "random_state": settings.ml_random_state,
        },
        "training_normal_tail_cutoffs": thresholds_from_train,
        "threshold_policy_note": "55-65 candidates are reported for analysis; only 60 is selectable so the configured risk-band boundary remains unchanged.",
        "validation_baseline_old_hybrid": current_baseline,
        "validation_baselines": validation_baselines,
        "threshold_experiments_current_calibration_70_30": [entry for entry in search
            if entry["calibration_method"] == "empirical_lower_tail_percentile_v1" and
            entry["rule_weight"] == 0.70 and entry["threshold"] in [value * 100 for value in THRESHOLDS]],
        "weight_experiments_current_calibration_threshold_60": current_weights_at_threshold,
        "calibration_experiments_70_30_threshold_60": calibration_summary,
        "all_validation_candidates": search,
        "precision_target_met_on_validation": selected["metrics"]["precision"] > 0.90,
        "selected_validation_candidate": selected,
        "selected_policy": selected_policy,
    }
    output_dir = ROOT / "data" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "calibration_validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output_dir / "calibration_selection.json").write_text(json.dumps(selected_policy, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "validation_baselines", "threshold_experiments_current_calibration_70_30",
        "weight_experiments_current_calibration_threshold_60", "calibration_experiments_70_30_threshold_60",
        "precision_target_met_on_validation", "selected_validation_candidate", "selected_policy",
    )}, indent=2))
    print(f"Saved validation report to {output_dir / 'calibration_validation_report.json'}")
    print(f"Saved selected policy to {output_dir / 'calibration_selection.json'}")
    return report


if __name__ == "__main__":
    calibrate()
