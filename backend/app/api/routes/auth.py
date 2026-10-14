import base64
import hashlib
import hmac
import json
import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.tenancy import LEGACY_INSTITUTION_ID, validate_institution_id

router = APIRouter(prefix="/v1/auth", tags=["authentication"])
SESSION_SECONDS = 8 * 60 * 60


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=1, max_length=1024)


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _password_matches(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac("sha256", password.encode(), _decode(salt), int(iterations))
        return hmac.compare_digest(_b64(derived), expected)
    except (ValueError, TypeError):
        return False


def issue_session(email: str, institution_id: str = LEGACY_INSTITUTION_ID) -> str:
    payload = _b64(json.dumps({"sub": email, "institution_id": institution_id, "exp": int(time.time()) + SESSION_SECONDS}, separators=(",", ":")).encode())
    signature = hmac.new(settings.session_signing_secret.encode(), payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{_b64(signature)}"


def verify_session_token(token: str) -> dict:
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(settings.session_signing_secret.encode(), payload.encode(), hashlib.sha256).digest()
        if len(settings.session_signing_secret) < 32 or not hmac.compare_digest(_decode(signature), expected):
            raise ValueError("signature")
        claims = json.loads(_decode(payload))
        if int(claims["exp"]) <= int(time.time()) or not isinstance(claims["sub"], str):
            raise ValueError("expiry")
        claims.setdefault("institution_id", LEGACY_INSTITUTION_ID)
        if claims["institution_id"] != LEGACY_INSTITUTION_ID:
            validate_institution_id(claims["institution_id"])
        return claims
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail={"error": {"code": "SESSION_EXPIRED", "message": "Sign in again to continue."}})


@router.post("/login")
def login(request: LoginRequest):
    if len(settings.session_signing_secret) < 32:
        raise HTTPException(status_code=503, detail={"error": {"code": "AUTH_NOT_CONFIGURED", "message": "Analyst sign-in is not configured."}})
    institution_id = settings.analyst_institution_id
    try:
        if institution_id != LEGACY_INSTITUTION_ID:
            validate_institution_id(institution_id)
    except ValueError:
        raise HTTPException(status_code=503, detail={"error": {"code": "AUTH_CONFIGURATION_INVALID", "message": "Analyst institution assignment is misconfigured."}})
    configured_email = settings.analyst_email
    configured_hash = settings.analyst_password_hash
    users = settings.analyst_users_json
    if users and users != "{}":
        try:
            configured = json.loads(users)
            if not isinstance(configured, dict):
                raise ValueError("analyst users must be a JSON object")
            matched = next(((email, value) for email, value in configured.items() if isinstance(email, str) and email.casefold() == request.email.casefold()), None)
            entry = matched[1] if matched else None
            if isinstance(entry, dict):
                configured_email = matched[0]
                configured_hash = entry.get("password_hash", "")
                institution_id = entry.get("institution_id", "")
                if institution_id != LEGACY_INSTITUTION_ID:
                    validate_institution_id(institution_id)
            else:
                configured_email = ""
                configured_hash = ""
        except (ValueError, TypeError, json.JSONDecodeError):
            raise HTTPException(status_code=503, detail={"error": {"code": "AUTH_CONFIGURATION_INVALID", "message": "Analyst accounts are misconfigured."}})
    if not configured_email or not configured_hash:
        if users and users != "{}":
            raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."}})
        raise HTTPException(status_code=503, detail={"error": {"code": "AUTH_NOT_CONFIGURED", "message": "Analyst sign-in is not configured."}})
    candidate_email = request.email.casefold()
    expected_email = configured_email.casefold()
    valid_email = candidate_email.isascii() and expected_email.isascii() and hmac.compare_digest(candidate_email, expected_email)
    valid_password = _password_matches(request.password, configured_hash)
    if not (valid_email and valid_password):
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."}})
    return {"access_token": issue_session(configured_email, institution_id), "token_type": "bearer", "expires_in": SESSION_SECONDS}


@router.get("/session")
def session(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": {"code": "SESSION_EXPIRED", "message": "Sign in again to continue."}})
    claims = verify_session_token(authorization[7:])
    email = claims["sub"]
    return {"email": email, "display_name": email.split("@", 1)[0], "role": "analyst", "institution_id": claims["institution_id"]}
