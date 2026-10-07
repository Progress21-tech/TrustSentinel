import secrets
from fastapi import Header, HTTPException

from app.core.config import settings


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    # An empty key keeps local development frictionless; configure a secret in hosted environments.
    if settings.api_key_secret and not secrets.compare_digest(x_api_key or "", settings.api_key_secret):
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_API_KEY", "message": "A valid sandbox API key is required."}})
