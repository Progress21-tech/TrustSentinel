import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import cases, health, metrics, risk, scenarios, transactions
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.rate_limit import rate_limit_middleware
from app.db.database import Base, engine
from app.db import models  # noqa: F401

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(message)s")
logger = logging.getLogger("trustsentinel")
app = FastAPI(title="TrustSentinel API", version=settings.app_version,
    description="Synthetic-data prototype for contextual social-engineering risk assessment. Scores are advisory; the service does not move or block real funds.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list or [], allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"])
register_error_handlers(app)
app.middleware("http")(rate_limit_middleware)

@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info({"request_id": request_id, "endpoint": request.url.path, "status_code": response.status_code,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3)})
    return response

app.include_router(health.router)
app.include_router(risk.router)
app.include_router(scenarios.router)
app.include_router(transactions.router)
app.include_router(cases.router)
app.include_router(metrics.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
