from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
from app.db.database import engine
from app.ml.features import FEATURE_SCHEMA_VERSION
from app.ml.predict import registry

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness check", description="Confirms that the API process is running.")
def health():
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@router.get("/ready", summary="Readiness check")
def readiness():
    if registry.model is None and not settings.rules_only_fallback:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail={"error": {"code": "MODEL_UNAVAILABLE", "message": "The configured policy requires the ML model."}})
    try:
        with engine.connect() as connection: connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "available", "ml_status": "available" if registry.is_available else "unavailable_rules_only",
            "model_version": registry.model_version, "hybrid_policy_version": registry.policy_version if registry.is_available else "rules-only",
            "feature_schema_version": FEATURE_SCHEMA_VERSION}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "A required dependency is unavailable."}})
