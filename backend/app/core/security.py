from __future__ import annotations

from dataclasses import dataclass
import hmac
import json
import re

from fastapi import Depends, Header, HTTPException
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.tenancy import LEGACY_INSTITUTION_ID, validate_institution_id

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class TenantPrincipal:
    institution_id: str
    subject: str
    auth_type: str
    role: str = "integration"


def _auth_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": message}})


def _api_clients() -> dict[str, str]:
    try:
        value = json.loads(settings.institution_api_keys_json or "{}")
        if not isinstance(value, dict):
            raise ValueError("expected an object")
        clients = {}
        for institution_id, key in value.items():
            validate_institution_id(str(institution_id))
            if not isinstance(key, str) or not key:
                raise ValueError("institution API keys must be non-empty strings")
            if key in clients.values():
                raise ValueError("each institution must have a distinct API key")
            clients[str(institution_id)] = key
        if settings.api_key_secret and settings.api_key_secret in clients.values():
            raise ValueError("legacy and institution API keys must be distinct")
        return clients
    except (ValueError, TypeError, json.JSONDecodeError):
        raise _auth_error(503, "AUTH_CONFIGURATION_INVALID", "Institution API credentials are misconfigured.")


def require_api_key(
    x_api_key: str | None = Depends(api_key_header),
    authorization: str | None = Header(default=None),
) -> TenantPrincipal:
    if authorization and authorization.startswith("Bearer "):
        from app.api.routes.auth import verify_session_token
        claims = verify_session_token(authorization[7:])
        institution_id = claims.get("institution_id", LEGACY_INSTITUTION_ID)
        try:
            if institution_id != LEGACY_INSTITUTION_ID:
                validate_institution_id(institution_id)
        except (TypeError, ValueError):
            raise _auth_error(401, "SESSION_EXPIRED", "Sign in again to continue.")
        return TenantPrincipal(institution_id, claims["sub"], "bearer", "analyst")

    clients = _api_clients()
    if settings.api_key_secret:
        clients.setdefault(LEGACY_INSTITUTION_ID, settings.api_key_secret)
    supplied = x_api_key or ""
    for institution_id, secret in clients.items():
        if hmac.compare_digest(supplied, secret):
            return TenantPrincipal(institution_id, f"api:{institution_id}", "api_key")
    if not clients and settings.app_env.lower() not in {"production", "prod"}:
        return TenantPrincipal(LEGACY_INSTITUTION_ID, "local-development", "development")
    if not clients:
        raise _auth_error(503, "AUTH_NOT_CONFIGURED", "Protected API access is not configured.")
    raise _auth_error(401, "INVALID_API_KEY", "A valid institution API key is required.")
