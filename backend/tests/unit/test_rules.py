import pytest

from app.risk_engine.rules import action_for, evaluate_signals, risk_band, score_rules


def features(**overrides):
    values = {"is_new_beneficiary": False, "amount_deviation_ratio": 1,
        "is_new_device": False, "recent_account_recovery": False,
        "transaction_count_30m": 0, "transaction_count_24h": 0,
        "beneficiary_risk_score": 0}
    values.update(overrides)
    return values


@pytest.mark.parametrize("score,band", [(0,"LOW"),(29,"LOW"),(30,"MODERATE"),
    (59,"MODERATE"),(60,"ELEVATED"),(79,"ELEVATED"),(80,"HIGH"),
    (89,"HIGH"),(90,"CRITICAL"),(100,"CRITICAL")])
def test_risk_band_boundaries(score, band):
    assert risk_band(score) == band


def test_selected_high_risk_threshold_updates_moderate_boundary():
    assert risk_band(54.99, 55) == "MODERATE"
    assert risk_band(55, 55) == "ELEVATED"
    assert risk_band(64.99, 65) == "MODERATE"
    assert risk_band(65, 65) == "ELEVATED"


def test_rules_are_deterministic_and_explain_triggered_evidence():
    signals = evaluate_signals(features(is_new_beneficiary=True, amount_deviation_ratio=5))
    assert [s.signal_type for s in signals if s.triggered] == ["NEW_BENEFICIARY", "UNUSUAL_AMOUNT"]
    assert score_rules(signals) == 40
    assert all(s.evidence for s in signals)


def test_large_legitimate_amount_is_not_a_signal_without_deviation():
    assert score_rules(evaluate_signals(features(amount_deviation_ratio=1.2))) == 0


def test_action_policy_is_separate_from_raw_score():
    assert action_for("LOW") == "ALLOW"
    assert action_for("CRITICAL") == "REVIEW"


@pytest.mark.parametrize("overrides,signal,score", [
    ({"is_new_beneficiary": True}, "NEW_BENEFICIARY", 20),
    ({"amount_deviation_ratio": 4.0}, "UNUSUAL_AMOUNT", 20),
    ({"is_new_device": True}, "NEW_DEVICE", 15),
    ({"recent_account_recovery": True}, "RECENT_ACCOUNT_RECOVERY", 15),
    ({"transaction_count_30m": 3}, "HIGH_VELOCITY", 10),
    ({"beneficiary_risk_score": 60}, "BENEFICIARY_RISK", 15),
])
def test_signal_thresholds(overrides, signal, score):
    selected = next(item for item in evaluate_signals(features(**overrides)) if item.signal_type == signal)
    assert selected.triggered
    assert selected.severity == score


@pytest.mark.parametrize("overrides,signal", [
    ({"is_new_beneficiary": False}, "NEW_BENEFICIARY"),
    ({"amount_deviation_ratio": 3.99}, "UNUSUAL_AMOUNT"),
    ({"is_new_device": False}, "NEW_DEVICE"),
    ({"recent_account_recovery": False}, "RECENT_ACCOUNT_RECOVERY"),
    ({"transaction_count_30m": 2, "transaction_count_24h": 7}, "HIGH_VELOCITY"),
    ({"beneficiary_risk_score": 59.99}, "BENEFICIARY_RISK"),
])
def test_signal_negative_boundaries(overrides, signal):
    selected = next(item for item in evaluate_signals(features(**overrides)) if item.signal_type == signal)
    assert not selected.triggered
