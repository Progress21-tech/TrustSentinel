import logging
import re
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import audit, auth, cases, health, metrics, risk, scenarios, transactions
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.rate_limit import rate_limit_middleware
from app.db.database import Base, engine
from app.db import models  # noqa: F401

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(message)s")
logger = logging.getLogger("trustsentinel")
app = FastAPI(title="Cerviqon API", version=settings.app_version,
    description="Synthetic-data prototype for contextual social-engineering risk assessment. Scores are advisory; the service does not move or block real funds.")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {"type": "http", "scheme": "bearer"}
    for path, path_item in schema.get("paths", {}).items():
        if path == "/v1/auth/session":
            for operation in path_item.values():
                if isinstance(operation, dict) and "operationId" in operation:
                    operation["security"] = [{"BearerAuth": []}]
        elif path.startswith("/v1/") and path != "/v1/auth/login":
            for operation in path_item.values():
                if isinstance(operation, dict) and "operationId" in operation:
                    operation["security"] = [{"APIKeyHeader": []}, {"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list or [], allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "X-API-Key", "Authorization", "X-Request-ID"])
register_error_handlers(app)
app.middleware("http")(rate_limit_middleware)

@app.middleware("http")
async def request_observability(request: Request, call_next):
    supplied_request_id = request.headers.get("X-Request-ID", "")
    request_id = supplied_request_id if re.fullmatch(r"[A-Za-z0-9._-]{1,128}", supplied_request_id) else str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info({"request_id": request_id, "endpoint": request.url.path, "status_code": response.status_code,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3)})
    return response

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(risk.router)
app.include_router(scenarios.router)
app.include_router(transactions.router)
app.include_router(cases.router)
app.include_router(metrics.router)
app.include_router(audit.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
