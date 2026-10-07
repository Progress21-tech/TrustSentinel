from app.risk_engine.scorer import hybrid_score
from app.risk_engine.rules import action_for, risk_band

def test_hybrid_uses_configured_weights_and_stays_bounded():
    assert hybrid_score(40, 0.5, 0.7, 0.3) == 43.0
    assert hybrid_score(100, 1.0) == 100.0
    assert hybrid_score(-20, 0.0) == 0.0

def test_missing_ml_uses_rules_only_score():
    assert hybrid_score(75, None) == 75

def test_intervention_remains_downstream_of_score_and_band():
    score = hybrid_score(90, 0.9)
    assert risk_band(score) == "CRITICAL"
    assert action_for(risk_band(score)) == "REVIEW"
