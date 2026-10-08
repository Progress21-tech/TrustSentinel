import math
from datetime import datetime, timedelta, timezone

from app.ml.features import (
    FEATURES, FEATURE_SCHEMA_VERSION, build_ml_features,
    extract_feature_context, vector,
)


def test_named_feature_schema_and_vector_order_are_stable():
    context = {"amount": 120_000, "amount_deviation_ratio": 4,
               "has_account_history": True, "is_new_beneficiary": True}
    first = build_ml_features(context)
    assert tuple(first) == FEATURES
    assert vector(context) == vector(context)
    assert len(FEATURES) == 17
    assert first["amount_deviation_ratio"] == 4
    assert FEATURE_SCHEMA_VERSION == "trustsentinel-context-v2"


def test_missing_and_nonfinite_fields_become_finite_numeric_values():
    result = build_ml_features({"amount": float("nan"), "transaction_count_30m": float("inf"),
                                "is_new_device": "false"})
    row = vector(result)
    assert len(row) == len(FEATURES)
    assert all(math.isfinite(value) for value in row)
    assert result["is_new_device"] == 0
    assert result["has_account_history"] == 0
    assert result["amount_deviation_ratio"] == 1


def test_cold_start_is_distinct_from_measured_ratio_of_one():
    cold = build_ml_features({"amount": 50_000, "has_account_history": False})
    measured = build_ml_features({"amount": 50_000, "has_account_history": True,
                                  "amount_deviation_ratio": 1})
    assert cold["amount_deviation_ratio"] == measured["amount_deviation_ratio"] == 1
    assert cold["has_account_history"] == 0
    assert measured["has_account_history"] == 1


def test_nonfeature_labels_and_scenario_names_are_ignored():
    bare = build_ml_features({"amount": 25_000, "has_account_history": False})
    annotated = build_ml_features({"amount": 25_000, "has_account_history": False,
        "synthetic_label": 1, "evaluation_scenario": "combined_high_risk",
        "dataset_split": "test"})
    assert bare == annotated


def test_shared_history_extractor_derives_live_and_training_semantics():
    now = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    history = [
        {"timestamp": now - timedelta(minutes=10), "amount": 20_000,
         "beneficiary_id": "ben-a", "device_id": "dev-a"},
        {"timestamp": now - timedelta(days=10), "amount": 40_000,
         "beneficiary_id": "ben-b", "device_id": "dev-a"},
    ]
    features = extract_feature_context(
        amount=30_000, at=now, account_created_at=now - timedelta(days=100),
        history=history, beneficiary_id="ben-new", device_id="dev-new",
        beneficiary_first_seen_at=now, device_first_seen_at=now,
        beneficiary_risk_score=0, last_device_change_at=now - timedelta(days=2),
    )
    assert features["has_account_history"] == 1
    assert features["amount_deviation_ratio"] == 1  # mean history amount is 30,000
    assert features["transaction_count_30m"] == 1
    assert features["transaction_count_24h"] == 1
    assert features["beneficiary_transaction_count"] == 0
    assert features["unique_beneficiary_count"] == 2
    assert features["is_new_beneficiary"] == 1
    assert features["is_new_device"] == 1
    assert features["recent_device_change"] == 1
