import numpy as np
from app.ml.features import FEATURES
from app.ml.predict import ModelRegistry, calibrate_anomaly_score
from scripts.train_model import fit_model
from scripts.generate_data import split_name
import joblib
from app.ml.features import FEATURE_SCHEMA_VERSION

def test_isolation_forest_artifact_load_and_calibrated_inference(tmp_path):
    rng = np.random.default_rng(81)
    X = rng.normal(0, 1, (300, len(FEATURES)))
    model, reference = fit_model(X, seed=81, n_estimators=25)
    artifact_path = tmp_path / "iforest.joblib"
    joblib.dump({"artifact_format_version": 1, "model": model, "model_version": "iforest-test",
        "training_dataset_version": "synthetic-test-v1", "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "features": list(FEATURES), "normal_reference_scores": reference,
        "score_calibration": "empirical_lower_tail_percentile_v1"}, artifact_path)
    registry = ModelRegistry(artifact_path)
    features = {name: float(value) for name, value in zip(FEATURES, X[0])}
    result = registry.predict(features)
    assert registry.is_available
    assert registry.model_version == "iforest-test"
    assert result == registry.predict(features)
    assert result is not None and 0 <= result <= 1

def test_missing_artifact_returns_rules_only_fallback(tmp_path):
    registry = ModelRegistry(tmp_path / "missing.joblib")
    assert not registry.is_available
    assert registry.predict({}) is None


def test_normal_tail_calibration_is_monotonic_and_bounded():
    values = [calibrate_anomaly_score(score, "normal_tail_excess_v1", 0.8) for score in (0.2, 0.8, 0.9, 1.0)]
    assert values == sorted(values)
    assert values == [0.0, 0.0, 0.5, 1.0]


def test_validation_split_preserves_original_held_out_membership():
    assert [split_name(index) for index in range(10)] == [
        "test", "validation", "train", "train", "train",
        "test", "validation", "train", "train", "train",
    ]


def test_artifact_loads_selected_policy_metadata(tmp_path):
    rng = np.random.default_rng(91)
    X = rng.normal(0, 1, (300, len(FEATURES)))
    model, reference = fit_model(X, seed=91, n_estimators=25)
    artifact_path = tmp_path / "iforest-policy.joblib"
    joblib.dump({"artifact_format_version": 1, "model": model, "model_version": "iforest-test-v2",
        "training_dataset_version": "synthetic-test-v2", "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "features": list(FEATURES), "normal_reference_scores": reference,
        "score_calibration": "empirical_lower_tail_percentile_v1",
        "calibration_method": "normal_tail_excess_v1", "calibration_tail_cutoff": 0.8,
        "hybrid_policy": {"policy_version": "hybrid-policy-test-v2", "rule_score_weight": 0.8,
            "ml_score_weight": 0.2, "high_risk_threshold": 60}}, artifact_path)
    registry = ModelRegistry(artifact_path)
    assert registry.is_available
    assert registry.calibration_method == "normal_tail_excess_v1"
    assert registry.policy_version == "hybrid-policy-test-v2"
    assert registry.rule_score_weight == 0.8
    assert registry.ml_score_weight == 0.2
    assert registry.decision_version == "iforest-test-v2+hybrid-policy-test-v2"
