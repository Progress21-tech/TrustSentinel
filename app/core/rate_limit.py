from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()

async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/health" or request.url.path == "/ready":
        return await call_next(request)
    client = request.client.host if request.client else "unknown"
    now = monotonic()
    with _lock:
        bucket = _hits[client]
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        if len(bucket) >= max(1, settings.rate_limit_per_minute):
            return JSONResponse(status_code=429, content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Request rate limit exceeded."}}, headers={"Retry-After": "60"})
        bucket.append(now)
    return await call_next(request)
