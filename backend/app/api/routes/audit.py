from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import TenantPrincipal, require_api_key
from app.core.tenancy import external_identifier
from app.db.database import get_db
from app.db.models import AuditLog

router = APIRouter(prefix="/v1/audit", tags=["audit"], dependencies=[Depends(require_api_key)])


def _public_metadata(value, db: Session, institution_id: str, key: str | None = None):
    if isinstance(value, dict):
        return {name: _public_metadata(item, db, institution_id, name) for name, item in value.items()}
    if isinstance(value, list):
        return [_public_metadata(item, db, institution_id, key) for item in value]
    kinds = {"transaction_id": "transaction", "account_id": "account", "beneficiary_id": "beneficiary", "device_id": "device"}
    if isinstance(value, str) and key in kinds:
        return external_identifier(db, institution_id, kinds[key], value)
    return value


@router.get("")
def list_audit_events(principal: TenantPrincipal = Depends(require_api_key), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)):
    events = list(db.scalars(select(AuditLog).where(AuditLog.institution_id == principal.institution_id).order_by(AuditLog.created_at.desc()).limit(limit)))
    return {"items": [{
        "event": event.event, "actor": event.actor, "entity_type": event.entity_type,
        "entity_id": event.entity_id, "metadata": _public_metadata(event.metadata_json, db, principal.institution_id),
        "created_at": event.created_at,
    } for event in events], "count": len(events)}
