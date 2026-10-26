"""Consent checks. Analysis for a child runs only while the latest record for the scope
is a grant (spec section 10)."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.consent.texts import Scope
from app.db.models import ConsentRecord


def active_scopes(db: Session, child_id: uuid.UUID) -> set[Scope]:
    """Scopes whose most recent record is a grant. Records are append-only, so the newest
    record per scope decides."""
    rows = db.scalars(
        select(ConsentRecord)
        .where(ConsentRecord.child_id == child_id)
        .order_by(ConsentRecord.created_at, ConsentRecord.id)
    ).all()
    state: dict[Scope, bool] = {}
    for row in rows:
        for scope in row.scopes:
            state[Scope(scope)] = row.action == "grant"
    return {scope for scope, granted in state.items() if granted}


def has_consent(db: Session, child_id: uuid.UUID, scope: Scope) -> bool:
    return scope in active_scopes(db, child_id)
