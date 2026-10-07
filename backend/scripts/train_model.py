"""Train and persist a reproducible Isolation Forest using the shared feature builder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.core.config import settings
from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION, build_ml_features, vector
from scripts.generate_data import generate

DATASET_VERSION = "trustsentinel-synthetic-v1"
DEFAULT_CALIBRATION = "empirical_lower_tail_percentile_v1"


def _contamination(value: str) -> str | float:
    if value == "auto":
        return value
    numeric = float(value)
    if not 0 < numeric <= 0.5:
        raise ValueError("ML_CONTAMINATION must be 'auto' or between 0 and 0.5")
    return numeric


def _max_samples(value: str) -> str | int | float:
    if value == "auto":
        return value
    numeric = float(value)
    if not 0 < numeric <= 1 and not numeric.is_integer():
        raise ValueError("ML_MAX_SAMPLES must be 'auto', a positive integer, or a fraction in (0, 1]")
    if numeric <= 0:
        raise ValueError("ML_MAX_SAMPLES must be greater than zero")
    return int(numeric) if numeric.is_integer() else numeric


def fit_model(X_train: np.ndarray, seed: int, n_estimators: int, contamination: str = "auto",
              max_samples: str = "auto", max_features: float = 1.0) -> tuple[Pipeline, np.ndarray]:
    """Fit the configured detector and return its empirical normal-score reference."""
    model = Pipeline([
        ("scale", StandardScaler()),
        ("isolation_forest", IsolationForest(
            n_estimators=n_estimators,
            max_samples=_max_samples(max_samples),
            contamination=_contamination(contamination),
            max_features=max_features,
            random_state=seed,
            n_jobs=1,
        )),
    ])
    model.fit(X_train)
    reference = np.sort(model.decision_function(X_train).astype(float))
    return model, reference


def train(output: str | None = None, seed: int | None = None, n_estimators: int | None = None) -> Path:
    seed = settings.ml_random_state if seed is None else seed
    n_estimators = settings.ml_n_estimators if n_estimators is None else n_estimators
    data_path = ROOT / "data" / "synthetic" / "transactions.csv"
    if not data_path.exists():
        generate(seed=seed)
    data = pd.read_csv(data_path)
    if "dataset_split" not in data or "synthetic_label" not in data or "dataset_seed" not in data:
        raise ValueError("Synthetic dataset is missing deterministic split/label columns; regenerate it.")
    if not {"train", "validation", "test"}.issubset(set(data["dataset_split"].astype(str))):
        raise ValueError("Synthetic data must include train, validation, and held-out test splits.")
    dataset_seeds = data["dataset_seed"].dropna().unique().tolist()
    if len(dataset_seeds) != 1:
        raise ValueError("Synthetic transactions must come from one recorded dataset seed.")
    dataset_version = f"{DATASET_VERSION}-seed-{int(dataset_seeds[0])}"
    train_rows = data[(data["dataset_split"] == "train") & (data["synthetic_label"] == 0)]
    validation_count = int((data["dataset_split"] == "validation").sum())
    test_count = int((data["dataset_split"] == "test").sum())
    if validation_count == 0 or test_count != 2_000:
        raise ValueError("Expected a validation split and the unchanged 2,000-row held-out test set.")
    if len(train_rows) < max(100, len(FEATURES) * 5):
        raise ValueError(f"Insufficient normal/background training rows: {len(train_rows)}")

    # Labels, split identifiers, and scenario names are not passed to the feature builder.
    X_train = np.asarray([vector(build_ml_features(row)) for row in train_rows.to_dict("records")], dtype=float)
    if X_train.shape[1] != len(FEATURES) or not np.isfinite(X_train).all():
        raise ValueError("Training feature matrix does not match the finite named feature schema.")

    model, normal_scores = fit_model(X_train, seed, n_estimators, settings.ml_contamination,
                                     settings.ml_max_samples, settings.ml_max_features)
    selection_path = ROOT / "data" / "generated" / "calibration_selection.json"
    if not selection_path.is_file():
        raise ValueError("Run python scripts/calibrate_policy.py before training the calibrated artifact.")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection and selection.get("dataset_version") != dataset_version:
        raise ValueError("Validation calibration selection does not match the training dataset version.")
    if selection and selection.get("split_version") != "train_validation_test_v1":
        raise ValueError("Validation calibration selection is missing the current train/validation/test split version.")
    if selection and selection.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
        raise ValueError("Validation calibration selection does not match the current feature schema.")
    calibration_method = selection.get("calibration_method", DEFAULT_CALIBRATION)
    if calibration_method not in {DEFAULT_CALIBRATION, "normal_tail_excess_v1"}:
        raise ValueError(f"Unsupported selected calibration method: {calibration_method}")
    calibration_tail_cutoff = selection.get("calibration_tail_cutoff")
    if calibration_method == "normal_tail_excess_v1" and calibration_tail_cutoff is None:
        raise ValueError("Selected tail calibration is missing its training-derived cutoff.")
    if calibration_method == "normal_tail_excess_v1" and not 0 <= float(calibration_tail_cutoff) < 1:
        raise ValueError("Selected tail calibration cutoff must be in [0, 1).")
    selected_rule_weight = float(selection.get("rule_weight", settings.rule_score_weight))
    selected_ml_weight = float(selection.get("ml_weight", settings.ml_score_weight))
    if selected_rule_weight < 0 or selected_ml_weight < 0 or selected_rule_weight + selected_ml_weight <= 0:
        raise ValueError("Selected validation policy has invalid hybrid weights.")
    if int(selection.get("high_risk_threshold", 60)) != 60:
        raise ValueError("Selected policy cannot override the established risk-band boundary.")
    # Empirical reference distribution from training-normal scores provides a stable,
    # bounded rank calibration: lower decision_function scores mean more anomalous.
    artifact = {
        "artifact_format_version": 1,
        "model": model,
        "model_version": settings.model_version,
        "training_dataset_version": dataset_version,
        "training_split_version": "train_validation_test_v1" if "validation" in set(data["dataset_split"]) else "legacy_train_test_v1",
        "training_seed": seed,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "features": list(FEATURES),
        "normal_reference_scores": normal_scores,
        "model_configuration": {
            "algorithm": "IsolationForest",
            "n_estimators": n_estimators,
            "max_samples": settings.ml_max_samples,
            "contamination": settings.ml_contamination,
            "max_features": settings.ml_max_features,
            "random_state": seed,
            "training_population": "train split rows with synthetic_label=0 only",
            "training_rows": len(train_rows),
            "validation_rows": validation_count,
            "held_out_rows": test_count,
        },
        "score_calibration": "empirical_lower_tail_percentile_v1",
        "calibration_method": calibration_method,
        "calibration_tail_cutoff": calibration_tail_cutoff,
        "hybrid_policy": {
            "policy_version": selection.get("policy_version", "hybrid-policy-v1.0.0"),
            "rule_score_weight": selected_rule_weight,
            "ml_score_weight": selected_ml_weight,
            "high_risk_threshold": int(selection.get("high_risk_threshold", 60)),
            "selection_dataset_version": selection.get("dataset_version"),
        },
    }
    destination = Path(output or settings.model_path)
    if not destination.is_absolute():
        destination = ROOT / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, destination)
    print(f"Saved {settings.model_version} to {destination}")
    print(f"Training rows={len(train_rows)}; validation rows={validation_count}; held-out rows={test_count}; feature count={len(FEATURES)}; seed={seed}")
    print(f"Calibration={calibration_method}; hybrid policy={artifact['hybrid_policy']['policy_version']} ({artifact['hybrid_policy']['rule_score_weight']:.2f}/{artifact['hybrid_policy']['ml_score_weight']:.2f})")
    print("Model inputs exclude scenario names, split markers and synthetic labels.")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--seed", type=int, default=settings.ml_random_state)
    parser.add_argument("--n-estimators", type=int, default=settings.ml_n_estimators)
    options = parser.parse_args()
    train(options.output, options.seed, options.n_estimators)
