"""Shared deterministic conversion of engineered feature maps to model arrays."""
import numpy as np
from app.ml.features import vector

def preprocess(features: dict) -> np.ndarray:
    return np.asarray([vector(features)], dtype=float)
