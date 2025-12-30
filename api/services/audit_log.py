"""Admin audit logging helpers."""

import json
from typing import Any

from sqlalchemy.orm import Session

from api.models import AdminAuditLog


def record_admin_action(
    db: Session,
    *,
    admin_user_id: int,
    action: str,
    target_type: str,
    target_id: str | int,
    metadata: dict[str, Any] | None = None,
) -> AdminAuditLog:
    entry = AdminAuditLog(
        admin_user_id=admin_user_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_logs(db: Session, *, limit: int = 50, offset: int = 0) -> list[AdminAuditLog]:
    return (
        db.query(AdminAuditLog)
        .order_by(AdminAuditLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
