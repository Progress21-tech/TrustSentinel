"""Generate deterministic, account-disjoint synthetic histories and features."""
from __future__ import annotations

import argparse
import hashlib
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION, extract_feature_context

DATASET_VERSION = "trustsentinel-synthetic-v2"
DEFAULT_ACCOUNT_COUNT = 1_000
TRANSACTIONS_PER_ACCOUNT = 10
SCENARIO_PROBABILITIES = {
    "normal": 0.58,
    "borderline": 0.15,
    "new_beneficiary_abnormal_amount": 0.06,
    "new_device_high_value": 0.05,
    "rapid_transfers_new_beneficiary": 0.05,
    "risky_beneficiary_network": 0.04,
    "account_recovery_new_beneficiary": 0.03,
    "combined_high_risk": 0.02,
    "legitimate_high_value": 0.01,
    "legitimate_business_high_value": 0.01,
}
POSITIVE_SCENARIOS = {
    "new_beneficiary_abnormal_amount", "new_device_high_value",
    "rapid_transfers_new_beneficiary", "risky_beneficiary_network",
    "account_recovery_new_beneficiary", "combined_high_risk",
}


def account_split(account_index: int, account_count: int = DEFAULT_ACCOUNT_COUNT) -> str:
    """Assign entire accounts to 60/20/20 train/validation/test partitions."""
    train_accounts = int(account_count * 0.60)
    validation_accounts = int(account_count * 0.20)
    if account_index < train_accounts:
        return "train"
    if account_index < train_accounts + validation_accounts:
        return "validation"
    return "test"


def split_name(index: int) -> str:
    """Compatibility helper retained for callers that used the previous row split."""
    account_index = index // TRANSACTIONS_PER_ACCOUNT
    return account_split(account_index)


def generate(seed: int = 2026, output: Path | None = None, transactions: int = 10_000) -> Path:
    if transactions <= 0 or transactions % TRANSACTIONS_PER_ACCOUNT:
        raise ValueError(f"transactions must be a positive multiple of {TRANSACTIONS_PER_ACCOUNT}")
    account_count = transactions // TRANSACTIONS_PER_ACCOUNT
    if account_count % 5:
        raise ValueError("account count must be divisible by five for account-disjoint 60/20/20 splits")

    rng = random.Random(seed)
    out = output or ROOT / "data" / "synthetic"
    out.mkdir(parents=True, exist_ok=True)
    anchor = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first_event = anchor - timedelta(days=365)
    channels = ("mobile_app", "web", "ussd", "api")
    profiles = ["NORMAL", "BUSINESS", "HIGH_VALUE", "SUSPICIOUS"]
    profile_weights = [65, 20, 10, 5]
    typical_amount = {"NORMAL": 45_000.0, "BUSINESS": 5_500_000.0,
                      "HIGH_VALUE": 2_500_000.0, "SUSPICIOUS": 90_000.0}

    customers = []
    accounts = []
    account_meta: dict[str, dict] = {}
    for i in range(account_count):
        account_id = f"ACC-{i:05}"
        created = first_event - timedelta(days=rng.randint(0, 2_200))
        profile = rng.choices(profiles, profile_weights, k=1)[0]
        customers.append({"customer_id": f"CUS-{i:05}", "risk_profile": profile, "status": "ACTIVE"})
        accounts.append({"account_id": account_id, "customer_id": f"CUS-{i:05}", "status": "ACTIVE",
                         "created_at": created.isoformat()})
        account_meta[account_id] = {"index": i, "created_at": created, "profile": profile,
                                    "last_recovery_at": None, "last_device_change_at": None}

    account_scenarios: dict[str, list[str]] = {}
    for i in range(account_count):
        account_id = f"ACC-{i:05}"
        scenarios = rng.choices(list(SCENARIO_PROBABILITIES), list(SCENARIO_PROBABILITIES.values()),
                                k=TRANSACTIONS_PER_ACCOUNT)
        for position, scenario in enumerate(scenarios):
            if scenario == "rapid_transfers_new_beneficiary" and position < 3:
                scenarios[position] = "normal"
        rapid_positions = [position for position, scenario in enumerate(scenarios)
                           if scenario == "rapid_transfers_new_beneficiary"]
        for position in rapid_positions[1:]:
            scenarios[position] = "normal"
        account_scenarios[account_id] = scenarios
        profile = account_meta[account_id]["profile"]
        if "legitimate_business_high_value" in scenarios:
            profile = "BUSINESS"
        elif "legitimate_high_value" in scenarios:
            profile = "HIGH_VALUE"
        account_meta[account_id]["profile"] = profile
        customers[i]["risk_profile"] = profile

    beneficiaries: dict[str, dict] = {}
    devices: dict[str, dict] = {}
    account_histories: dict[str, list[dict]] = {}
    for i in range(1_500):
        beneficiary_id = f"BEN-{i:05}"
        beneficiaries[beneficiary_id] = {
            "beneficiary_id": beneficiary_id,
            "first_seen_at": (first_event - timedelta(days=rng.randint(1, 1_500))).isoformat(),
            "risk_score": round(rng.uniform(65, 95), 2) if i % 30 == 0 else round(rng.uniform(0, 15), 2),
            "status": "ACTIVE",
        }

    rows: list[dict] = []
    for i in range(transactions):
        account_index = i // TRANSACTIONS_PER_ACCOUNT
        local_index = i % TRANSACTIONS_PER_ACCOUNT
        account_id = f"ACC-{account_index:05}"
        account = account_meta[account_id]
        base_typical = typical_amount[account["profile"]]
        category = account_scenarios[account_id][local_index]
        at = first_event + timedelta(days=local_index * 36 + rng.randint(0, 4),
                                     minutes=rng.randint(0, 1_439))

        # Create a real preceding-history burst for the velocity scenario. Those
        # preceding transactions remain ordinary labeled events.
        burst_index = account.get("_burst_index")
        if category == "rapid_transfers_new_beneficiary" and local_index >= 3 and burst_index is None:
            burst_base = first_event + timedelta(days=local_index * 36 + 2)
            for back, slot in enumerate(range(local_index - 3, local_index)):
                preceding_index = account_index * TRANSACTIONS_PER_ACCOUNT + slot
                rows[preceding_index]["timestamp"] = (burst_base + timedelta(minutes=back * 5)).isoformat()
            at = burst_base + timedelta(minutes=15)
            account["_burst_index"] = local_index

        account_history = account_histories.setdefault(account_id, [])
        historical_amounts = [row["amount"] for row in account_history]
        account_average = sum(historical_amounts) / len(historical_amounts) if historical_amounts else base_typical
        expected = rng.lognormvariate(__import__("math").log(base_typical), 0.42)

        if category == "borderline":
            amount = account_average * rng.uniform(1.7, 3.6) if account_history else expected * rng.uniform(1.0, 1.8)
        elif category in {"new_beneficiary_abnormal_amount", "new_device_high_value"}:
            amount = account_average * rng.uniform(3.0, 6.0) if account_history else expected * rng.uniform(2.0, 4.0)
        elif category == "rapid_transfers_new_beneficiary":
            amount = account_average * rng.uniform(0.8, 1.8) if account_history else expected
        elif category == "risky_beneficiary_network":
            amount = account_average * rng.uniform(1.0, 2.5) if account_history else expected * rng.uniform(0.8, 1.8)
        elif category == "account_recovery_new_beneficiary":
            amount = account_average * rng.uniform(1.3, 3.2) if account_history else expected * rng.uniform(1.0, 2.0)
        elif category == "combined_high_risk":
            amount = account_average * rng.uniform(3.0, 5.5) if account_history else expected * rng.uniform(2.0, 4.5)
        elif category == "legitimate_high_value":
            amount = max(2_000_000.0, expected)
            if account_history:
                amount = account_average * rng.uniform(0.85, 1.5)
        elif category == "legitimate_business_high_value":
            amount = max(5_000_000.0, expected)
            if account_history:
                amount = account_average * rng.uniform(0.9, 1.5)
        else:
            amount = expected
        amount = round(max(1_000.0, amount), 2)

        # Account-history familiarity is derived from history, not copied from
        # the scenario label. Scenario examples select new/existing underlying
        # entities; the canonical feature extractor derives novelty itself.
        account_beneficiaries = {row["beneficiary_id"] for row in account_history}
        if category in {"new_beneficiary_abnormal_amount", "rapid_transfers_new_beneficiary",
                       "account_recovery_new_beneficiary", "combined_high_risk"}:
            beneficiary_id = f"BEN-NEW-{account_index:05}-{local_index:02}"
            risk = rng.uniform(65, 95) if category == "combined_high_risk" else rng.uniform(0, 18)
            beneficiaries[beneficiary_id] = {"beneficiary_id": beneficiary_id,
                "first_seen_at": at.isoformat(), "risk_score": round(risk, 2), "status": "ACTIVE"}
        elif category == "risky_beneficiary_network":
            beneficiary_id = f"BEN-RISK-{account_index:05}-{local_index:02}"
            beneficiaries[beneficiary_id] = {"beneficiary_id": beneficiary_id,
                "first_seen_at": at.isoformat(), "risk_score": round(rng.uniform(65, 95), 2), "status": "ACTIVE"}
        elif account_beneficiaries and rng.random() < 0.75:
            beneficiary_id = rng.choice(sorted(account_beneficiaries))
        else:
            beneficiary_id = f"BEN-{rng.randrange(1_500):05}"
        beneficiary = beneficiaries[beneficiary_id]

        device_id = f"DEV-{account_index:05}-BASE"
        if device_id not in devices:
            devices[device_id] = {"device_id": device_id, "account_id": account_id,
                                  "first_seen_at": (first_event - timedelta(days=rng.randint(1, 365))).isoformat(),
                                  "risk_flags": "[]"}
        if category in {"new_device_high_value", "combined_high_risk"}:
            device_id = f"DEV-NEW-{account_index:05}-{local_index:02}"
            devices[device_id] = {"device_id": device_id, "account_id": account_id,
                                  "first_seen_at": at.isoformat(), "risk_flags": "[]"}
            account["last_device_change_at"] = at - timedelta(days=2)
        device = devices[device_id]

        if category in {"account_recovery_new_beneficiary", "combined_high_risk"}:
            account["last_recovery_at"] = at - timedelta(days=1)

        features = extract_feature_context(
            amount=amount, at=at, account_created_at=account["created_at"],
            history=account_history, beneficiary_id=beneficiary_id, device_id=device_id,
            beneficiary_first_seen_at=datetime.fromisoformat(beneficiary["first_seen_at"]),
            device_first_seen_at=datetime.fromisoformat(device["first_seen_at"]),
            beneficiary_risk_score=beneficiary["risk_score"],
            last_device_change_at=account["last_device_change_at"],
            last_recovery_at=account["last_recovery_at"],
        )
        transaction_id = f"SYN-{i:07}"
        rows.append({
            "transaction_id": transaction_id, "account_id": account_id,
            "beneficiary_id": beneficiary_id, "device_id": device_id,
            "amount": amount, "currency": "NGN", "channel": rng.choice(channels),
            "timestamp": at.isoformat(), **features,
            "_last_device_change_at": account["last_device_change_at"].isoformat() if account["last_device_change_at"] else None,
            "_last_recovery_at": account["last_recovery_at"].isoformat() if account["last_recovery_at"] else None,
            "evaluation_scenario": category,
            "synthetic_label": int(category in POSITIVE_SCENARIOS),
            "dataset_split": account_split(account_index, account_count),
            "dataset_seed": seed,
            "dataset_version": DATASET_VERSION,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
        })
        account_history.append(rows[-1])

    # Ensure per-account rows are chronological and recompute feature values
    # after any burst timestamps were adjusted. Each account belongs to one split.
    by_account: dict[str, list[dict]] = {}
    for row in rows:
        by_account.setdefault(row["account_id"], []).append(row)
    for account_id, account_rows in by_account.items():
        account_rows.sort(key=lambda row: (row["timestamp"], row["transaction_id"]))
        account = account_meta[account_id]
        history: list[dict] = []
        for row in account_rows:
            ben = beneficiaries[row["beneficiary_id"]]
            device = devices[row["device_id"]]
            row.update(extract_feature_context(
                amount=row["amount"], at=datetime.fromisoformat(row["timestamp"]),
                account_created_at=account["created_at"], history=history,
                beneficiary_id=row["beneficiary_id"], device_id=row["device_id"],
                beneficiary_first_seen_at=datetime.fromisoformat(ben["first_seen_at"]),
                device_first_seen_at=datetime.fromisoformat(device["first_seen_at"]),
                beneficiary_risk_score=ben["risk_score"],
                last_device_change_at=datetime.fromisoformat(row["_last_device_change_at"]) if row["_last_device_change_at"] else None,
                last_recovery_at=datetime.fromisoformat(row["_last_recovery_at"]) if row["_last_recovery_at"] else None,
            ))
            history.append(row)
            row.pop("_last_device_change_at", None)
            row.pop("_last_recovery_at", None)

    for account_row in accounts:
        account_state = account_meta[account_row["account_id"]]
        account_row["last_recovery_at"] = account_state["last_recovery_at"].isoformat() if account_state["last_recovery_at"] else None
        account_row["last_device_change_at"] = account_state["last_device_change_at"].isoformat() if account_state["last_device_change_at"] else None

    pd.DataFrame(customers).to_csv(out / "customers.csv", index=False)
    pd.DataFrame(accounts).to_csv(out / "accounts.csv", index=False)
    pd.DataFrame(list(devices.values())).to_csv(out / "devices.csv", index=False)
    pd.DataFrame(list(beneficiaries.values())).to_csv(out / "beneficiaries.csv", index=False)
    pd.DataFrame(rows).to_csv(out / "transactions.csv", index=False)
    manifest = {
        "dataset_version": DATASET_VERSION,
        "dataset_seed": seed,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_count": len(FEATURES),
        "features": list(FEATURES),
        "records": len(rows),
        "account_count": account_count,
        "transactions_per_account": TRANSACTIONS_PER_ACCOUNT,
        "split_definition": "account-disjoint 60/20/20 train/validation/test",
        "split_counts": pd.Series([row["dataset_split"] for row in rows]).value_counts().to_dict(),
        "label_fields_excluded_from_features": ["synthetic_label", "evaluation_scenario", "dataset_split"],
    }
    import json
    (out / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    digest = hashlib.sha256((out / "transactions.csv").read_bytes()).hexdigest()
    (out / "dataset_sha256.txt").write_text(digest + "\n", encoding="ascii")
    print(f"Generated {len(rows)} records; split counts={manifest['split_counts']}; schema={FEATURE_SCHEMA_VERSION}; sha256={digest}")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--transactions", type=int, default=10_000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(f"Generated synthetic CSV data in {generate(args.seed, args.output, args.transactions)}")
