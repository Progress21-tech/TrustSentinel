import math
from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION, build_ml_features, vector

def test_named_feature_schema_and_vector_order_are_stable():
    context = {"amount": 120000, "average_transaction_amount": 30000, "is_new_beneficiary": True}
    first = build_ml_features(context)
    second = build_ml_features(context)
    assert tuple(first) == FEATURES
    assert vector(context) == vector(context)
    assert list(first.values()) == list(second.values())
    assert first["amount_deviation_ratio"] == 4
    assert FEATURE_SCHEMA_VERSION

def test_missing_and_nonfinite_fields_become_finite_numeric_values():
    result = build_ml_features({"amount": float("nan"), "transaction_count_30m": float("inf"), "is_new_device": "false"})
    row = vector(result)
    assert len(row) == len(FEATURES)
    assert all(math.isfinite(value) for value in row)
    assert result["is_new_device"] == 0

def test_nonfeature_labels_and_scenario_names_are_ignored():
    bare = build_ml_features({"amount": 25000, "average_transaction_amount": 25000})
    annotated = build_ml_features({"amount": 25000, "average_transaction_amount": 25000,
        "synthetic_label": 1, "evaluation_scenario": "combined_high_risk", "dataset_split": "test"})
    assert bare == annotated
