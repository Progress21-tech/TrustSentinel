from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.db.models import TenantIdentifier
from app.main import app


def test_institution_keys_isolate_identifiers_history_and_transaction_reads(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "api_key_secret", "")
    monkeypatch.setattr(settings, "institution_api_keys_json", '{"bank-a":"secret-a","bank-b":"secret-b"}')
    headers_a, headers_b = {"X-API-Key": "secret-a"}, {"X-API-Key": "secret-b"}
    base = {"account_id": "shared-account", "beneficiary_id": "shared-beneficiary",
            "device_id": "shared-device", "amount": 25000, "currency": "NGN", "channel": "mobile_app"}
    try:
        with TestClient(app) as client:
            a_first = client.post("/v1/risk/score", headers=headers_a, json={**base, "transaction_id": "shared-transaction"})
            assert a_first.status_code == 200, a_first.text
            assert a_first.json()["transaction_id"] == "shared-transaction"
            assert a_first.json()["data_completeness"]["status"] == "cold_start"
            a_second = client.post("/v1/risk/score", headers=headers_a, json={**base, "transaction_id": "a-only-transaction"})
            assert a_second.status_code == 200, a_second.text
            assert a_second.json()["data_completeness"]["status"] == "history_available"
            b_first = client.post("/v1/risk/score", headers=headers_b, json={**base, "transaction_id": "shared-transaction"})
            assert b_first.status_code == 200, b_first.text
            assert b_first.json()["data_completeness"]["status"] == "cold_start"
            assert b_first.json()["assessment_id"] != a_first.json()["assessment_id"]
            assert client.get("/v1/transactions/a-only-transaction", headers=headers_b).status_code == 404
            assert client.get("/v1/transactions/shared-transaction", headers=headers_a).status_code == 200
            assert client.get("/v1/transactions/shared-transaction", headers=headers_b).status_code == 200
            assert client.get("/v1/transactions", headers=headers_a).json()["count"] == 2
            assert client.get("/v1/transactions", headers=headers_b).json()["count"] == 1
        with session_factory() as db:
            mappings = list(db.scalars(select(TenantIdentifier).where(TenantIdentifier.entity_type == "transaction", TenantIdentifier.external_id == "shared-transaction")))
            assert len(mappings) == 2
            assert mappings[0].internal_id != mappings[1].internal_id
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_unknown_institution_key_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key_secret", "")
    monkeypatch.setattr(settings, "institution_api_keys_json", '{"bank-a":"secret-a"}')
    with TestClient(app) as client:
        assert client.get("/v1/metrics/summary", headers={"X-API-Key": "secret-b"}).status_code == 401
