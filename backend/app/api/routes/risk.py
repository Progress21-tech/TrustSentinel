from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.security import require_api_key
from app.db.database import get_db
from app.schemas.risk import RiskRequest, RiskResponse
from app.services.risk_service import score_transaction

router = APIRouter(prefix="/v1/risk", tags=["risk"])


@router.post("/score", response_model=RiskResponse, dependencies=[Depends(require_api_key)], summary="Score a transaction", description="Calculates contextual features, deterministic rules and (when trained artifact exists) an Isolation Forest anomaly score. Returns an explainable recommendation. No payment is executed.")
def score(request: RiskRequest, http_request: Request, db: Session = Depends(get_db)):
    return score_transaction(db, request, getattr(http_request.state, "request_id", None))
