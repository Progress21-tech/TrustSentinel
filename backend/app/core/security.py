import secrets
from fastapi import Depends, Header, HTTPException
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    x_api_key: str | None = Depends(api_key_header),
    authorization: str | None = Header(default=None),
) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        from app.api.routes.auth import verify_session_token

        return verify_session_token(authorization[7:])
    # An empty key keeps local development frictionless; configure a secret in hosted environments.
    if settings.api_key_secret and not secrets.compare_digest(x_api_key or "", settings.api_key_secret):
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_API_KEY", "message": "A valid sandbox API key is required."}})
    if not settings.api_key_secret and settings.app_env.lower() in {"production", "prod"}:
        raise HTTPException(status_code=503, detail={"error": {"code": "AUTH_NOT_CONFIGURED", "message": "Protected API access is not configured."}})
    return None
