"""Audit trail: who did what, by id only."""

import uuid

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def record(db: Session, actor: str, action: str, target: uuid.UUID | str | None = None) -> None:
    db.add(AuditLog(actor=actor, action=action, target=None if target is None else str(target)))


def guardian_actor(guardian_id: uuid.UUID) -> str:
    return f"guardian:{guardian_id}"
