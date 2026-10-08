"""Load once and serve the versioned model with training-distribution calibration."""
from __future__ import annotations

from pathlib import Path
import logging

import joblib
import numpy as np

from app.core.config import settings
from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION, vector

logger = logging.getLogger("trustsentinel.ml")


def calibrate_anomaly_score(base_risk: float, method: str, tail_cutoff: float | None = None) -> float:
    """Apply a deterministic monotonic normalization to a base empirical tail rank."""
    if method == "empirical_lower_tail_percentile_v1":
        value = base_risk
    elif method == "normal_tail_excess_v1":
        if tail_cutoff is None or not 0 <= tail_cutoff < 1:
            raise ValueError("normal-tail calibration requires a cutoff in [0, 1)")
        value = (base_risk - tail_cutoff) / (1.0 - tail_cutoff)
    else:
        raise ValueError(f"Unsupported anomaly calibration method: {method}")
    return round(float(np.clip(value, 0.0, 1.0)), 6)


class ModelRegistry:
    def __init__(self, model_path: str | Path | None = None):
        self.model = None
        self.reference_scores = np.asarray([], dtype=float)
        self.model_version = "unavailable"
        self.training_dataset_version: str | None = None
        self.dataset_sha256: str | None = None
        self.training_split_version = "legacy_train_test_v1"
        self.calibration_method = "empirical_lower_tail_percentile_v1"
        self.calibration_tail_cutoff: float | None = None
        self.policy_version = "hybrid-policy-v1.0.0"
        self.rule_score_weight = settings.rule_score_weight
        self.ml_score_weight = settings.ml_score_weight
        self.high_risk_threshold = 60
        self.load_error: str | None = None
        self.inference_error: str | None = None
        path = Path(model_path or settings.model_path)
        try:
            if not path.is_absolute():
                path = Path(__file__).resolve().parents[2] / path
            if not path.is_file():
                raise FileNotFoundError("model artifact not found")
            artifact = joblib.load(path)
            if not isinstance(artifact, dict) or artifact.get("artifact_format_version") != 1:
                raise ValueError("unsupported model artifact format")
            if artifact.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
                raise ValueError("model feature schema version does not match the application")
            if artifact.get("score_calibration") != "empirical_lower_tail_percentile_v1":
                raise ValueError("model artifact is missing the supported score calibration metadata")
            if tuple(artifact.get("features", ())) != FEATURES:
                raise ValueError("model feature ordering does not match the application")
            reference = np.asarray(artifact.get("normal_reference_scores"), dtype=float).reshape(-1)
            reference = reference[np.isfinite(reference)]
            if reference.size < 100:
                raise ValueError("model artifact has too few calibration reference scores")
            model = artifact.get("model")
            if model is None or not hasattr(model, "decision_function"):
                raise ValueError("model artifact does not provide decision_function")
            self.reference_scores = np.sort(reference)
            self.model_version = str(artifact["model_version"])
            self.training_dataset_version = str(artifact.get("training_dataset_version", "unknown"))
            self.dataset_sha256 = str(artifact.get("dataset_sha256")) if artifact.get("dataset_sha256") else None
            self.training_split_version = str(artifact.get("training_split_version", "legacy_train_test_v1"))
            self.calibration_method = str(artifact.get("calibration_method", "empirical_lower_tail_percentile_v1"))
            self.calibration_tail_cutoff = artifact.get("calibration_tail_cutoff")
            # Validate artifact normalization metadata during load rather than at request time.
            calibrate_anomaly_score(0.5, self.calibration_method, self.calibration_tail_cutoff)
            policy = artifact.get("hybrid_policy", {})
            self.policy_version = str(policy.get("policy_version", "hybrid-policy-v1.0.0"))
            self.rule_score_weight = float(policy.get("rule_score_weight", settings.rule_score_weight))
            self.ml_score_weight = float(policy.get("ml_score_weight", settings.ml_score_weight))
            self.high_risk_threshold = int(policy.get("high_risk_threshold", 60))
            if self.rule_score_weight < 0 or self.ml_score_weight < 0 or self.rule_score_weight + self.ml_score_weight <= 0:
                raise ValueError("model artifact contains invalid hybrid policy weights")
            if not 55 <= self.high_risk_threshold <= 65:
                raise ValueError("artifact high-risk threshold must be between 55 and 65")
            self.model = model
        except Exception as exc:
            self.load_error = f"{type(exc).__name__}: {exc}"
            logger.warning("ML artifact unavailable; rules-only fallback active (%s)", type(exc).__name__)

    @property
    def is_available(self) -> bool:
        return self.model is not None and self.reference_scores.size > 0

    @property
    def decision_version(self) -> str:
        if self.model is None:
            return "rules-only"
        return f"{self.model_version}+{self.policy_version}"

    def predict(self, features: dict, apply_selected_calibration: bool = True) -> float | None:
        """Return empirical lower-tail anomaly percentile in [0,1], or None on fallback."""
        if not self.is_available:
            return None
        try:
            row = np.asarray([vector(features)], dtype=float)
            if row.shape[1] != len(FEATURES) or not np.isfinite(row).all():
                raise ValueError("invalid model input vector")
            raw_score = float(self.model.decision_function(row)[0])
            rank = int(np.searchsorted(self.reference_scores, raw_score, side="right"))
            normalized_risk = 1.0 - rank / self.reference_scores.size
            self.inference_error = None
            method = self.calibration_method if apply_selected_calibration else "empirical_lower_tail_percentile_v1"
            cutoff = self.calibration_tail_cutoff if apply_selected_calibration else None
            return calibrate_anomaly_score(normalized_risk, method, cutoff)
        except Exception as exc:
            self.inference_error = f"{type(exc).__name__}: {exc}"
            logger.exception("ML inference failed; rules-only fallback active")
            return None


registry = ModelRegistry()
