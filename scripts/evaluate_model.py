"""Report synthetic anomaly metrics and deterministic scenario outcomes."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from app.db.database import Base, SessionLocal, engine
from app.services.demo_service import SCENARIOS, run_scenario
from app.core.config import settings
from app.ml.features import FEATURES
from scripts.generate_data import generate

EXPECTED = {"normal": "LOW", "new_beneficiary_large_amount": "ELEVATED", "new_device_large_transfer": "HIGH",
    "account_recovery_new_beneficiary": "CRITICAL", "rapid_transfers": "HIGH", "risky_beneficiary": "HIGH", "combined_high_risk": "CRITICAL", "legitimate_high_value": "LOW"}

def evaluate():
    data_dir = Path(__file__).resolve().parents[1] / "data" / "synthetic"
    if not (data_dir / "transactions.csv").exists(): generate(output=data_dir)
    data = pd.read_csv(data_dir / "transactions.csv")
    customers = pd.read_csv(data_dir / "customers.csv")
    profiles = customers["risk_profile"].tolist()
    typical = {"NORMAL": 45000, "BUSINESS": 350000, "HIGH_VALUE": 1_500_000, "SUSPICIOUS": 90000}
    matrix = []
    for row in data.itertuples(index=False):
        account_index = int(row.account_id.split("-")[1])
        baseline = typical[profiles[account_index]]
        matrix.append([np.log1p(row.amount), min(row.amount / baseline, 1000), 0, 2, 100, 0, 100, 0, 0, 0, 5, 0])
    artifact = Path(settings.model_path)
    if not artifact.exists():
        print("ML metrics unavailable: train the model with python scripts/train_model.py first.")
    else:
        loaded = joblib.load(artifact)
        model = loaded.get("model") if isinstance(loaded, dict) else loaded
        prediction = (model.predict(np.asarray(matrix)) == -1).astype(int)
        labels = data["synthetic_label"].astype(int).to_numpy()
        tn, fp, fn, tp = confusion_matrix(labels, prediction, labels=[0, 1]).ravel()
        print("Synthetic-only anomaly evaluation (prototype labels, not real-world performance):")
        print(f"accuracy={accuracy_score(labels, prediction):.4f} precision={precision_score(labels, prediction, zero_division=0):.4f} recall={recall_score(labels, prediction, zero_division=0):.4f} f1={f1_score(labels, prediction, zero_division=0):.4f}")
        print(f"false_positive_rate={fp / max(1, fp + tn):.4f} confusion_matrix=[[{tn}, {fp}], [{fn}, {tp}]]")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("Scenario report (synthetic; PRD expected bands are shown for review against configured weights):")
        for name, expected in EXPECTED.items():
            result = run_scenario(db, name)
            print(f"{name:38} expected={expected:10} actual={result['risk_band']:10} score={result['risk_score']:5.1f} {'PASS' if result['risk_band'] == expected else 'REVIEW'}")
    finally: db.close()

if __name__ == "__main__": evaluate()
