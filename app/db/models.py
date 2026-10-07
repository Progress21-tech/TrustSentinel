from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    risk_profile: Mapped[str] = mapped_column(String(40), default="NORMAL")
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    accounts: Mapped[list["Account"]] = relationship(back_populates="customer")


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_recovery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_device_change_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    customer: Mapped[Customer] = relationship(back_populates="accounts")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    beneficiary_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    beneficiary_id: Mapped[str] = mapped_column(String(80), index=True)
    device_id: Mapped[str] = mapped_column(String(80), index=True)
    amount: Mapped[float] = mapped_column(Numeric(16, 2))
    currency: Mapped[str] = mapped_column(String(8), default="NGN")
    channel: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), default="EVALUATED")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RiskSignal(Base):
    __tablename__ = "risk_signals"
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[str] = mapped_column(String(100), unique=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(50))
    source_feature: Mapped[str] = mapped_column(String(60))
    signal_value: Mapped[float] = mapped_column(Float)
    severity: Mapped[int] = mapped_column(Integer)
    evidence: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RiskDecision(Base):
    __tablename__ = "risk_decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[str] = mapped_column(String(100), unique=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id"), index=True)
    rule_score: Mapped[float] = mapped_column(Float)
    ml_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float)
    risk_band: Mapped[str] = mapped_column(String(20))
    recommended_action: Mapped[str] = mapped_column(String(20))
    reason_codes: Mapped[list] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(40))
    rule_version: Mapped[str] = mapped_column(String(40))
    latency_ms: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    outcome: Mapped[str | None] = mapped_column(String(30), nullable=True)
    analyst_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Intervention(Base):
    __tablename__ = "interventions"
    id: Mapped[int] = mapped_column(primary_key=True)
    intervention_id: Mapped[str] = mapped_column(String(100), unique=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id"), index=True)
    action: Mapped[str] = mapped_column(String(20))
    customer_response: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(80))
    event: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(100), index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
