from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app


def test_scenario_records_are_available_from_transaction_and_audit_apis(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "api_key_secret", "")
    monkeypatch.setattr(settings, "app_env", "development")
    try:
        with TestClient(app) as client:
            decision = client.post("/v1/sandbox/scenario", json={"scenario": "normal"})
            assert decision.status_code == 200
            transaction_id = decision.json()["transaction_id"]
            transaction = client.get(f"/v1/transactions/{transaction_id}")
            assert transaction.status_code == 200
            assert transaction.json()["risk_decision"] is not None
            listing = client.get("/v1/transactions?limit=10")
            assert listing.status_code == 200
            assert any(item["transaction_id"] == transaction_id for item in listing.json()["items"])
            audit = client.get("/v1/audit?limit=10")
            assert audit.status_code == 200
            assert any(item["metadata"].get("transaction_id") == transaction_id for item in audit.json()["items"])
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()
