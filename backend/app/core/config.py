from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "trustsentinel-backend"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./trustsentinel.db"
    model_path: str = "models/isolation_forest_v1.joblib"
    model_version: str = "iforest-v1.1.0"
    ml_n_estimators: int = Field(default=200, ge=10, le=2000)
    ml_random_state: int = 2026
    ml_contamination: str = "auto"
    ml_max_samples: str = "auto"
    ml_max_features: float = Field(default=1.0, gt=0, le=1)
    ml_anomaly_reason_threshold: float = Field(default=0.95, ge=0, le=1)
    ml_high_risk_threshold: float = Field(default=0.90, ge=0, le=1)
    rule_version: str = "rules_v1"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    api_key_secret: str = ""
    session_signing_secret: str = ""
    analyst_email: str = ""
    analyst_password_hash: str = ""
    rate_limit_per_minute: int = 120
    rules_only_fallback: bool = True
    rule_score_weight: float = Field(default=0.7, ge=0)
    ml_score_weight: float = Field(default=0.3, ge=0)
    rule_weights_json: str = '{"NEW_BENEFICIARY":20,"UNUSUAL_AMOUNT":20,"NEW_DEVICE":15,"RECENT_ACCOUNT_RECOVERY":15,"HIGH_VELOCITY":10,"BENEFICIARY_RISK":15,"NETWORK_RISK":10,"BEHAVIOURAL_DEVIATION":10}'

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_hybrid_weights(self):
        if self.rule_score_weight + self.ml_score_weight <= 0:
            raise ValueError("At least one hybrid scoring weight must be greater than zero")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
