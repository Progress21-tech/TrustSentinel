"""Generate reproducible, linked synthetic MVP entities and 10,000 transactions."""
import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def generate(seed: int = 2026, output: Path | None = None, transactions: int = 10_000) -> Path:
    rng = random.Random(seed)
    out = output or ROOT / "data" / "synthetic"
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    customers = [{"customer_id": f"CUS-{i:05}", "risk_profile": rng.choices(["NORMAL", "BUSINESS", "HIGH_VALUE", "SUSPICIOUS"], [65, 20, 10, 5])[0], "status": "ACTIVE"} for i in range(1000)]
    accounts = [{"account_id": f"ACC-{i:05}", "customer_id": f"CUS-{i:05}", "status": "ACTIVE", "created_at": (now-timedelta(days=rng.randint(90, 2200))).isoformat()} for i in range(1000)]
    devices = [{"device_id": f"DEV-{i:04}", "account_id": f"ACC-{i%1000:05}", "risk_flags": "[]"} for i in range(700)]
    beneficiaries = [{"beneficiary_id": f"BEN-{i:05}", "risk_score": round(rng.random()*15, 2) if i % 30 else round(rng.uniform(65, 95), 2)} for i in range(1500)]
    txns = []
    base = now - timedelta(days=365)
    for i in range(transactions):
        acct = i % 1000
        profile = customers[acct]["risk_profile"]
        typical = {"NORMAL": 45000, "BUSINESS": 350000, "HIGH_VALUE": 1_500_000, "SUSPICIOUS": 90000}[profile]
        amount = max(1000, round(rng.lognormvariate(__import__("math").log(typical), 0.55), 2))
        txns.append({"transaction_id": f"SYN-{i:07}", "account_id": f"ACC-{acct:05}", "beneficiary_id": f"BEN-{rng.randrange(1500):05}",
            "device_id": f"DEV-{acct%700:04}", "amount": amount, "currency": "NGN", "channel": rng.choice(["mobile_app", "web", "ussd", "api"]),
            "timestamp": (base + timedelta(seconds=rng.randrange(365*24*3600))).isoformat(), "synthetic_label": int(profile == "SUSPICIOUS" or amount > typical*5)})
    for name, rows in [("customers.csv", customers), ("accounts.csv", accounts), ("devices.csv", devices), ("beneficiaries.csv", beneficiaries), ("transactions.csv", txns)]:
        pd.DataFrame(rows).to_csv(out / name, index=False)
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--transactions", type=int, default=10_000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(f"Generated related synthetic CSV data in {generate(args.seed, args.output, args.transactions)}")
