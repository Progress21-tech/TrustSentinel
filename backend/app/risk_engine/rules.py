from dataclasses import asdict, dataclass
import json
from app.core.config import settings

WEIGHTS = {
    "NEW_BENEFICIARY": 20, "UNUSUAL_AMOUNT": 20, "NEW_DEVICE": 15,
    "RECENT_ACCOUNT_RECOVERY": 15, "HIGH_VELOCITY": 10,
    "BENEFICIARY_RISK": 15, "NETWORK_RISK": 10, "BEHAVIOURAL_DEVIATION": 10,
}

def configured_weights() -> dict[str, int]:
    try:
        supplied = json.loads(settings.rule_weights_json)
        if not isinstance(supplied, dict): return WEIGHTS
        return {name: max(0, int(supplied.get(name, weight))) for name, weight in WEIGHTS.items()}
    except (ValueError, TypeError):
        return WEIGHTS


@dataclass(frozen=True)
class Signal:
    signal_type: str
    triggered: bool
    severity: int
    evidence: str
    source_feature: str
    value: float = 0.0

    def public(self) -> dict:
        return asdict(self)


def evaluate_signals(f: dict) -> list[Signal]:
    rules = [
        ("NEW_BENEFICIARY", bool(f["is_new_beneficiary"]), "Beneficiary has not previously been used by this account.", "is_new_beneficiary", float(f["is_new_beneficiary"])),
        ("UNUSUAL_AMOUNT", f["amount_deviation_ratio"] >= 4.0, f"Amount is {f['amount_deviation_ratio']:.1f}x the account's historical average.", "amount_deviation_ratio", f["amount_deviation_ratio"]),
        ("NEW_DEVICE", bool(f["is_new_device"]), "Device has not previously been seen on this account.", "is_new_device", float(f["is_new_device"])),
        ("RECENT_ACCOUNT_RECOVERY", bool(f["recent_account_recovery"]), "Account recovery was recorded within the previous 7 days.", "recent_account_recovery", float(f["recent_account_recovery"])),
        ("HIGH_VELOCITY", f["transaction_count_30m"] >= 3 or f["transaction_count_24h"] >= 8, "Transaction activity is elevated for this account.", "transaction_count_30m", float(f["transaction_count_30m"])),
        ("BENEFICIARY_RISK", f["beneficiary_risk_score"] >= 60, "Beneficiary has an elevated synthetic risk score.", "beneficiary_risk_score", f["beneficiary_risk_score"]),
        ("NETWORK_RISK", f["network_risk_score"] >= 60, "Synthetic relationship indicators link this beneficiary to elevated risk.", "network_risk_score", f["network_risk_score"]),
        ("BEHAVIOURAL_DEVIATION", f["session_anomaly_score"] >= 0.75, "Synthetic session behaviour differs from the account baseline.", "session_anomaly_score", f["session_anomaly_score"]),
    ]
    weights = configured_weights()
    return [Signal(name, hit, weights[name], evidence if hit else f"No threshold breach for {name.lower().replace('_', ' ')}.", source, float(value)) for name, hit, evidence, source, value in rules]


def score_rules(signals: list[Signal]) -> float:
    return min(100.0, float(sum(s.severity for s in signals if s.triggered)))


def risk_band(score: float) -> str:
    if score < 30: return "LOW"
    if score < 60: return "MODERATE"
    if score < 80: return "ELEVATED"
    if score < 90: return "HIGH"
    return "CRITICAL"


def action_for(band: str) -> str:
    return {"LOW": "ALLOW", "MODERATE": "WARN", "ELEVATED": "STEP_UP", "HIGH": "HOLD", "CRITICAL": "REVIEW"}[band]


def explain(signals: list[Signal], band: str, action: str) -> tuple[list[str], str]:
    active = [s for s in signals if s.triggered]
    codes = [s.signal_type for s in active]
    if not active:
        return codes, f"No configured contextual risk signals were triggered. The transaction is rated {band.lower()} and the recommended action is {action.lower()}."
    reasons = "; ".join(s.evidence for s in active)
    return codes, f"Contextual indicators associated with elevated social-engineering risk were observed: {reasons} Recommended action: {action.lower()}. This is a risk assessment, not a determination of customer intent."
