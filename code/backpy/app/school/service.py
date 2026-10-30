"""Turn a class's members into an aggregate the school may see (proposal 0004).

The only thing that leaves is counts, after k-anonymity. Each child's level and support
flag are read here to be counted and then dropped; they are never returned per child.
"""

import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dashboard.queries import _RANK, _latest_assessments
from app.db.base import utcnow
from app.db.models import ClassMembership, Event
from app.risk.schemas import Level
from app.school.aggregate import GroupCounts, aggregate_group

SUPPORT_EVENT = "dukungan_dibutuhkan"


def _child_level_and_support(db: Session, child_id: uuid.UUID, since) -> tuple[Level, bool]:
    convs = list(_latest_assessments(db, child_id, since))
    level = max(
        (Level(ra.level) for _, ra in convs),
        key=lambda lvl: _RANK[lvl.value],
        default=Level.AMAN,
    )
    support = (
        db.scalar(
            select(Event.id)
            .where(
                Event.child_id == child_id,
                Event.kind == SUPPORT_EVENT,
                Event.created_at >= since,
            )
            .limit(1)
        )
        is not None
    )
    return level, support


def class_counts(db: Session, classroom_id: uuid.UUID, *, days: int = 7) -> GroupCounts:
    """k-anon counts for one class over the window. Reads each consenting member's level and
    support flag, counts them, and returns only the aggregate."""
    since = utcnow() - timedelta(days=days)
    child_ids = db.scalars(
        select(ClassMembership.child_id).where(ClassMembership.classroom_id == classroom_id)
    ).all()
    levels: list[Level] = []
    support: list[bool] = []
    for cid in child_ids:
        lvl, sup = _child_level_and_support(db, cid, since)
        levels.append(lvl)
        support.append(sup)
    return aggregate_group(levels, support)
