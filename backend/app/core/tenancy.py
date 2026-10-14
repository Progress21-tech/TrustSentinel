from __future__ import annotations

import hashlib
import re
from sqlalchemy import select
from sqlalchemy.orm import Session

INSTITUTION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
LEGACY_INSTITUTION_ID = "default"


def validate_institution_id(value: str) -> str:
    if not INSTITUTION_ID_RE.fullmatch(value) or value == LEGACY_INSTITUTION_ID:
        raise ValueError("Institution IDs must be 1-32 safe ASCII characters; 'default' is reserved for legacy data.")
    return value


def _stable_internal_id(institution_id: str, entity_type: str, external_id: str) -> str:
    material = f"cerviqon-id-v1\0{institution_id}\0{entity_type}\0{external_id}".encode("utf-8")
    return "cvr_" + hashlib.sha256(material).hexdigest()


def resolve_identifier(db: Session, institution_id: str, entity_type: str, external_id: str,
                       legacy_model=None, legacy_field: str | None = None) -> str:
    from app.db.models import TenantIdentifier

    mapping = db.scalar(select(TenantIdentifier).where(
        TenantIdentifier.institution_id == institution_id,
        TenantIdentifier.entity_type == entity_type,
        TenantIdentifier.external_id == external_id,
    ))
    if mapping:
        return mapping.internal_id

    internal_id = _stable_internal_id(institution_id, entity_type, external_id)
    # Existing single-tenant rows retain their historical identifiers after migration.
    if institution_id == LEGACY_INSTITUTION_ID and legacy_model is not None and legacy_field:
        column = getattr(legacy_model, legacy_field)
        legacy = db.scalar(select(legacy_model).where(
            legacy_model.institution_id == institution_id,
            column == external_id,
        ))
        if legacy:
            internal_id = external_id

    db.add(TenantIdentifier(institution_id=institution_id, entity_type=entity_type,
        external_id=external_id, internal_id=internal_id))
    db.flush()
    return internal_id


def external_identifier(db: Session, institution_id: str, entity_type: str, internal_id: str) -> str:
    from app.db.models import TenantIdentifier

    mapping = db.scalar(select(TenantIdentifier).where(
        TenantIdentifier.institution_id == institution_id,
        TenantIdentifier.entity_type == entity_type,
        TenantIdentifier.internal_id == internal_id,
    ))
    return mapping.external_id if mapping else internal_id
