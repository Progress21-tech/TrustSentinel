import numpy as np
from app.ml.features import FEATURES
from app.ml.predict import ModelRegistry
from scripts.train_model import fit_model
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
