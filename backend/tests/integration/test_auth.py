import base64
import hashlib

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import require_api_key
from app.main import app


def _password_hash(password: str) -> str:
    salt = b"trustsentinel-test-salt"
    iterations = 100_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${iterations}${encode(salt)}${encode(digest)}"


def test_login_issues_a_validated_expiring_session(monkeypatch):
    monkeypatch.setattr(settings, "analyst_email", "analyst@example.test")
    monkeypatch.setattr(settings, "analyst_password_hash", _password_hash("correct horse battery staple"))
    monkeypatch.setattr(settings, "session_signing_secret", "test-session-signing-secret-at-least-32")
    with TestClient(app) as client:
        rejected = client.post("/v1/auth/login", json={"email": "analyst@example.test", "password": "incorrect"})
        assert rejected.status_code == 401
        response = client.post("/v1/auth/login", json={"email": "analyst@example.test", "password": "correct horse battery staple"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        session = client.get("/v1/auth/session", headers={"Authorization": f"Bearer {token}"})
        assert session.status_code == 200
        assert session.json()["email"] == "analyst@example.test"
        assert session.json()["role"] == "analyst"
        assert require_api_key(None, f"Bearer {token}") == "analyst@example.test"


def test_invalid_bearer_session_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "session_signing_secret", "test-session-signing-secret-at-least-32")
    with TestClient(app) as client:
        response = client.get("/v1/auth/session", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_production_protected_routes_fail_closed_without_api_key_or_session(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key_secret", "")
    with TestClient(app) as client:
        response = client.get("/v1/metrics/summary")
    assert response.status_code == 503
