"""Train and persist a reproducible Isolation Forest using the shared feature builder."""
from __future__ import annotations

import argparse
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
    dataset_seeds = data["dataset_seed"].dropna().unique().tolist()
    if len(dataset_seeds) != 1:
        raise ValueError("Synthetic transactions must come from one recorded dataset seed.")
    dataset_version = f"{DATASET_VERSION}-seed-{int(dataset_seeds[0])}"
    train_rows = data[(data["dataset_split"] == "train") & (data["synthetic_label"] == 0)]
    test_count = int((data["dataset_split"] == "test").sum())
    if len(train_rows) < max(100, len(FEATURES) * 5):
        raise ValueError(f"Insufficient normal/background training rows: {len(train_rows)}")

    # Labels, split identifiers, and scenario names are not passed to the feature builder.
    X_train = np.asarray([vector(build_ml_features(row)) for row in train_rows.to_dict("records")], dtype=float)
    if X_train.shape[1] != len(FEATURES) or not np.isfinite(X_train).all():
        raise ValueError("Training feature matrix does not match the finite named feature schema.")

    model, normal_scores = fit_model(X_train, seed, n_estimators, settings.ml_contamination,
                                     settings.ml_max_samples, settings.ml_max_features)
    # Empirical reference distribution from training-normal scores provides a stable,
    # bounded rank calibration: lower decision_function scores mean more anomalous.
    artifact = {
        "artifact_format_version": 1,
        "model": model,
        "model_version": settings.model_version,
        "training_dataset_version": dataset_version,
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
            "held_out_rows": test_count,
        },
        "score_calibration": "empirical_lower_tail_percentile_v1",
    }
    destination = Path(output or settings.model_path)
    if not destination.is_absolute():
        destination = ROOT / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, destination)
    print(f"Saved {settings.model_version} to {destination}")
    print(f"Training rows={len(train_rows)}; held-out rows={test_count}; feature count={len(FEATURES)}; seed={seed}")
    print("Model inputs exclude scenario names, split markers and synthetic labels.")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--seed", type=int, default=settings.ml_random_state)
    parser.add_argument("--n-estimators", type=int, default=settings.ml_n_estimators)
    options = parser.parse_args()
    train(options.output, options.seed, options.n_estimators)
