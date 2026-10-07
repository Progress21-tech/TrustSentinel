import math
from pathlib import Path
import joblib
import numpy as np

from app.core.config import settings
from app.ml.features import vector


class ModelRegistry:
    def __init__(self):
        self.model = None
        self.model_version = settings.model_version
        self.load_error: str | None = None
        try:
            path = Path(settings.model_path)
            if path.exists():
                artifact = joblib.load(path)
                self.model = artifact.get("model") if isinstance(artifact, dict) else artifact
                if isinstance(artifact, dict): self.model_version = artifact.get("model_version", self.model_version)
            else:
                self.load_error = "model artifact not found"
        except Exception as exc:  # safe rules-only degradation for the sandbox
            self.load_error = type(exc).__name__

    def predict(self, features: dict) -> float | None:
        if self.model is None:
            return None
        row = np.asarray([vector(features)], dtype=float)
        raw = float(self.model.decision_function(row)[0])
        # Calibrate in a bounded, monotonic range around the model's decision boundary.
        return round(1.0 / (1.0 + math.exp(max(-30.0, min(30.0, raw * 3.0)))), 4)


registry = ModelRegistry()
