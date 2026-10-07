"""Shared configurable rules + ML score composition."""

def hybrid_score(rule_score: float, ml_score: float | None, rule_weight: float = 0.7, ml_weight: float = 0.3) -> float:
    if ml_score is None:
        return min(100.0, max(0.0, float(rule_score)))
    total_weight = max(1e-12, float(rule_weight) + float(ml_weight))
    value = (float(rule_weight) * float(rule_score) + float(ml_weight) * float(ml_score) * 100.0) / total_weight
    return min(100.0, max(0.0, value))
