from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class RiskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"transaction_id": "txn_001", "account_id": "acct_001", "amount": 850000, "currency": "NGN", "beneficiary_id": "ben_001", "device_id": "dev_001", "channel": "mobile_app"}]})
    transaction_id: str = Field(min_length=1, max_length=100)
    account_id: str = Field(min_length=1, max_length=80)
    amount: float = Field(gt=0, le=1_000_000_000)
    currency: str = Field(default="NGN", min_length=3, max_length=8)
    beneficiary_id: str = Field(min_length=1, max_length=80)
    device_id: str = Field(min_length=1, max_length=80)
    channel: Literal["mobile_app", "web", "ussd", "api"]
    timestamp: datetime | None = None

class ScenarioRequest(BaseModel):
    scenario: Literal["normal", "new_beneficiary_large_amount", "new_device_large_transfer", "account_recovery_new_beneficiary", "rapid_transfers", "risky_beneficiary", "combined_high_risk", "legitimate_high_value"]


class CaseOutcomeRequest(BaseModel):
    outcome: Literal["CONFIRMED_SCAM", "LEGITIMATE", "NEEDS_REVIEW", "ESCALATED"]
    notes: str | None = Field(default=None, max_length=2000)
    analyst_id: str = Field(default="sandbox-analyst", max_length=80)


class SignalResponse(BaseModel):
    signal_type: str
    triggered: bool
    severity: int
    evidence: str
    source_feature: str


class RiskResponse(BaseModel):
    transaction_id: str
    risk_score: float
    risk_band: str
    recommended_action: str
    reason_codes: list[str]
    explanation: str
    rule_score: float
    ml_score: float | None
    ml_status: str = "available"
    model_version: str
    rule_version: str
    latency_ms: float
    signals: list[SignalResponse] = Field(default_factory=list)
    case_id: str | None = None
