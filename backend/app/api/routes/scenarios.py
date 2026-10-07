from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import require_api_key
from app.db.database import get_db
from app.schemas.risk import ScenarioRequest
from app.services.demo_service import run_scenario

router = APIRouter(prefix="/v1/sandbox", tags=["sandbox"])


@router.post("/scenario", dependencies=[Depends(require_api_key)], summary="Run a deterministic demo scenario")
def scenario(request: ScenarioRequest, db: Session = Depends(get_db)):
    return run_scenario(db, request.scenario)
