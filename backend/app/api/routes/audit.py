from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db.database import get_db
from app.db.models import AuditLog

router = APIRouter(prefix="/v1/audit", tags=["audit"], dependencies=[Depends(require_api_key)])


@router.get("")
def list_audit_events(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)):
    events = list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)))
    return {"items": [{
        "event": event.event, "actor": event.actor, "entity_type": event.entity_type,
        "entity_id": event.entity_id, "metadata": event.metadata_json,
        "created_at": event.created_at,
    } for event in events], "count": len(events)}
