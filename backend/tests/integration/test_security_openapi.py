from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import require_api_key
from app.db.database import Base, get_db
from app.main import app


def test_openapi_declares_api_key_for_protected_routes_and_keeps_health_public():
    schema = app.openapi()

    assert schema["components"]["securitySchemes"]["APIKeyHeader"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }
    for path, path_item in schema["paths"].items():
        if path.startswith("/v1/"):
            operations = [item for item in path_item.values() if isinstance(item, dict) and "operationId" in item]
            assert operations, f"No OpenAPI operations found for {path}"
            assert all(item.get("security") == [{"APIKeyHeader": []}] for item in operations), path
    assert "security" not in schema["paths"]["/health"]["get"]
    assert "security" not in schema["paths"]["/ready"]["get"]


def test_protected_scenario_requires_configured_key_and_allows_valid_key(monkeypatch):
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
    monkeypatch.setattr(settings, "api_key_secret", "test-secret-from-settings")
    try:
        with TestClient(app) as client:
            assert client.post("/v1/sandbox/scenario", json={"scenario": "normal"}).status_code == 401
            assert client.post(
                "/v1/sandbox/scenario",
                json={"scenario": "normal"},
                headers={"X-API-Key": "incorrect"},
            ).status_code == 401
            response = client.post(
                "/v1/sandbox/scenario",
                json={"scenario": "normal"},
                headers={"X-API-Key": "test-secret-from-settings"},
            )
            assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_empty_configured_secret_preserves_open_access(monkeypatch):
    monkeypatch.setattr(settings, "api_key_secret", "")
    assert require_api_key(None) is None
