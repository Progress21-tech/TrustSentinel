"""Load once and serve the versioned model with training-distribution calibration."""
from __future__ import annotations

from pathlib import Path
import logging

import joblib
import numpy as np

from app.core.config import settings
from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION, vector

logger = logging.getLogger("trustsentinel.ml")


class ModelRegistry:
    def __init__(self, model_path: str | Path | None = None):
        self.model = None
        self.reference_scores = np.asarray([], dtype=float)
        self.model_version = "unavailable"
        self.training_dataset_version: str | None = None
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
            self.model = model
            self.reference_scores = np.sort(reference)
            self.model_version = str(artifact["model_version"])
            self.training_dataset_version = str(artifact.get("training_dataset_version", "unknown"))
        except Exception as exc:
            self.load_error = f"{type(exc).__name__}: {exc}"
            logger.warning("ML artifact unavailable; rules-only fallback active (%s)", type(exc).__name__)

    @property
    def is_available(self) -> bool:
        return self.model is not None and self.reference_scores.size > 0

    def predict(self, features: dict) -> float | None:
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
            return round(float(np.clip(normalized_risk, 0.0, 1.0)), 6)
        except Exception as exc:
            self.inference_error = f"{type(exc).__name__}: {exc}"
            logger.exception("ML inference failed; rules-only fallback active")
            return None


registry = ModelRegistry()
