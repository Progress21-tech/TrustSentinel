"""Versioned model loader shared by online inference."""
from app.ml.predict import ModelRegistry, registry

__all__ = ["ModelRegistry", "registry"]
