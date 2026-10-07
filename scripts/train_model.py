"""Train the offline Isolation Forest artifact using synthetic behavioural samples."""
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from app.core.config import settings
from app.ml.features import FEATURES

def train(output: str | None = None, seed: int = 2026):
    rng = np.random.default_rng(seed)
    n = 6000
    X = np.column_stack([rng.normal(np.log1p(55000), .65, n), rng.lognormal(0, .4, n), rng.poisson(.2, n), rng.poisson(2, n),
        rng.integers(10, 1000, n), rng.binomial(1, .03, n), rng.integers(10, 1000, n), rng.binomial(1, .02, n), rng.binomial(1, .01, n),
        rng.beta(1, 12, n), rng.beta(1, 10, n)*100, rng.beta(1, 12, n)*100])
    model = make_pipeline(StandardScaler(), IsolationForest(n_estimators=200, contamination="auto", random_state=seed))
    model.fit(X)
    path = Path(output or settings.model_path); path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "model_version": settings.model_version, "features": FEATURES}, path)
    print(f"Saved synthetic Isolation Forest artifact to {path} ({path.stat().st_size:,} bytes). Synthetic prototype only.")
    return path

if __name__ == "__main__": train()
