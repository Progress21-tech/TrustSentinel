"""Generate reproducible, linked synthetic MVP entities and 10,000 transactions."""
import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.ml.features import build_ml_features

def generate(seed: int = 2026, output: Path | None = None, transactions: int = 10_000) -> Path:
    rng = random.Random(seed)
    out = output or ROOT / "data" / "synthetic"
    out.mkdir(parents=True, exist_ok=True)
    # Fixed anchor date and seed keep generated values and splits reproducible.
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    customers = [{"customer_id": f"CUS-{i:05}", "risk_profile": rng.choices(["NORMAL", "BUSINESS", "HIGH_VALUE", "SUSPICIOUS"], [65, 20, 10, 5])[0], "status": "ACTIVE"} for i in range(1000)]
    accounts = [{"account_id": f"ACC-{i:05}", "customer_id": f"CUS-{i:05}", "status": "ACTIVE", "created_at": (now-timedelta(days=rng.randint(90, 2200))).isoformat()} for i in range(1000)]
    devices = [{"device_id": f"DEV-{i:04}", "account_id": f"ACC-{i%1000:05}", "risk_flags": "[]"} for i in range(700)]
    beneficiaries = [{"beneficiary_id": f"BEN-{i:05}", "risk_score": round(rng.random()*15, 2) if i % 30 else round(rng.uniform(65, 95), 2)} for i in range(1500)]
    txns = []
    base = now - timedelta(days=365)
    categories = ["normal", "borderline", "new_beneficiary_abnormal_amount", "new_device_high_value",
        "rapid_transfers_new_beneficiary", "risky_beneficiary_network", "account_recovery_new_beneficiary",
        "combined_high_risk", "legitimate_high_value", "legitimate_business_high_value"]
    probabilities = [0.58, 0.15, 0.06, 0.05, 0.05, 0.04, 0.03, 0.02, 0.01, 0.01]
    for i in range(transactions):
        acct = i % 1000
        profile = customers[acct]["risk_profile"]
        typical = {"NORMAL": 45000, "BUSINESS": 350000, "HIGH_VALUE": 1_500_000, "SUSPICIOUS": 90000}[profile]
        scenario = rng.choices(categories, probabilities, k=1)[0]
        amount = max(1000.0, round(rng.lognormvariate(__import__("math").log(typical), 0.45), 2))
        ratio = rng.uniform(0.45, 2.5)
        new_ben, new_device, recent_recovery, beneficiary_risk = False, False, False, rng.uniform(0, 18)
        count_30m, count_24h = rng.choices([0, 1, 2], [0.7, 0.25, 0.05])[0], rng.randint(0, 5)
        session_anomaly = rng.betavariate(1.2, 10)
        if scenario == "borderline":
            new_ben = rng.random() < 0.35
            new_device = rng.random() < 0.20
            ratio = rng.uniform(2.0, 5.0)
            session_anomaly = rng.uniform(0.25, 0.78)
        elif scenario == "new_beneficiary_abnormal_amount":
            new_ben, ratio, session_anomaly = True, rng.uniform(4.0, 10.0), rng.uniform(0.45, 0.95)
        elif scenario == "new_device_high_value":
            new_device, ratio, session_anomaly = True, rng.uniform(4.0, 11.0), rng.uniform(0.4, 0.9)
        elif scenario == "rapid_transfers_new_beneficiary":
            new_ben, count_30m, count_24h = True, rng.randint(3, 7), rng.randint(5, 12)
        elif scenario == "risky_beneficiary_network":
            beneficiary_risk, session_anomaly = rng.uniform(65, 98), rng.uniform(0.2, 0.8)
        elif scenario == "account_recovery_new_beneficiary":
            new_ben, recent_recovery, ratio = True, True, rng.uniform(3.0, 7.0)
        elif scenario == "combined_high_risk":
            new_ben, new_device, recent_recovery = True, True, True
            beneficiary_risk, ratio = rng.uniform(65, 98), rng.uniform(4.0, 10.0)
            count_30m, count_24h, session_anomaly = rng.randint(3, 7), rng.randint(7, 14), rng.uniform(0.7, 1.0)
        elif scenario in {"legitimate_high_value", "legitimate_business_high_value"}:
            amount, ratio, new_ben, new_device = max(2_000_000.0, amount), rng.uniform(0.8, 1.35), False, False
            beneficiary_risk, session_anomaly = rng.uniform(0, 8), rng.uniform(0, 0.18)
            if scenario == "legitimate_business_high_value":
                amount, ratio = max(5_000_000.0, amount), rng.uniform(0.85, 1.5)
        amount = round(amount, 2)
        context = {
            "amount": amount, "average_transaction_amount": amount / max(ratio, 0.01),
            "amount_deviation_ratio": ratio, "transaction_hour": rng.randrange(24),
            "time_of_day_deviation": rng.random(), "transaction_count_30m": count_30m,
            "transaction_count_24h": count_24h, "beneficiary_age_days": 0 if new_ben else rng.randint(20, 1500),
            "beneficiary_risk_score": beneficiary_risk, "beneficiary_transaction_count": 0 if new_ben else rng.randint(1, 60),
            "unique_beneficiary_count": rng.randint(1, 25), "is_new_beneficiary": new_ben,
            "device_age_days": 0 if new_device else rng.randint(30, 1300), "is_new_device": new_device,
            "recent_device_change": new_device, "recent_account_recovery": recent_recovery,
            "recent_password_reset": False, "recent_pin_reset": False,
            "session_duration_deviation": rng.random() * 0.8, "interaction_velocity": rng.random(),
            "navigation_deviation_score": rng.random() * 0.7, "session_anomaly_score": session_anomaly,
            "linked_risky_accounts": int(beneficiary_risk >= 60), "linked_risky_devices": int(new_device and scenario != "borderline"),
            "linked_risky_beneficiaries": int(beneficiary_risk >= 60), "beneficiary_in_degree": rng.randint(0, 20),
            "beneficiary_out_degree": rng.randint(0, 15), "network_risk_score": beneficiary_risk,
            "account_age_days": rng.randint(60, 2400), "average_daily_transactions": rng.uniform(0.2, 8.0),
        }
        ml_features = build_ml_features(context)
        txns.append({"transaction_id": f"SYN-{i:07}", "account_id": f"ACC-{acct:05}", "beneficiary_id": f"BEN-{rng.randrange(1500):05}",
            "device_id": f"DEV-{acct%700:04}", "amount": amount, "currency": "NGN", "channel": rng.choice(["mobile_app", "web", "ussd", "api"]),
            "timestamp": (base + timedelta(seconds=rng.randrange(365*24*3600))).isoformat(),
            **context, **ml_features, "evaluation_scenario": scenario,
            "synthetic_label": int(scenario in {"new_beneficiary_abnormal_amount", "new_device_high_value", "rapid_transfers_new_beneficiary", "risky_beneficiary_network", "account_recovery_new_beneficiary", "combined_high_risk"})})
    rng.shuffle(txns)
    for index, row in enumerate(txns):
        # Preserve the existing every-fifth held-out test membership exactly;
        # use one fifth of the former training rows as validation.
        row["dataset_split"] = split_name(index)
        row["dataset_seed"] = seed
    for name, rows in [("customers.csv", customers), ("accounts.csv", accounts), ("devices.csv", devices), ("beneficiaries.csv", beneficiaries), ("transactions.csv", txns)]:
        pd.DataFrame(rows).to_csv(out / name, index=False)
    return out


def split_name(index: int) -> str:
    if index % 5 == 0:
        return "test"
    return "validation" if index % 5 == 1 else "train"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--transactions", type=int, default=10_000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(f"Generated related synthetic CSV data in {generate(args.seed, args.output, args.transactions)}")
