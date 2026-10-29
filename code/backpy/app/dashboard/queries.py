"""What a guardian can read about one child: overview, conversations, events, insight.

The same functions serve the dashboard endpoints and the Ask dcAI tools, so the assistant
can never see more than the dashboard shows. Nothing here holds message text; there is
none to hold.
"""

import uuid
from collections import Counter
from datetime import datetime, timedelta

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.consent.service import active_scopes
from app.db.base import utcnow
from app.db.models import (
    ChildProfile,
    Conversation,
    Device,
    Event,
    ImageSignal,
    Insight,
    RiskAssessment,
)
from app.guide.guide import Situation, help_channels
from app.risk.schemas import Level

_RANK = {lvl.value: i for i, lvl in enumerate(Level)}
# Protection is on when dcAI is running and reporting in from the phone. The persistent
# notification is shown the whole time the service runs, so it stands for "dcAI is active";
# other services (keyboard, accessibility) are additional and shown per device.
REQUIRED_SERVICES = ("notification",)


class ConversationSummary(BaseModel):
    conversation_id: str
    assessment_id: str
    app: str | None
    channel: str
    level: str
    risk_score: int
    patterns: list[str]
    confidence: str
    rationale_for_parent: str
    started_at: datetime
    updated_at: datetime


class EventOut(BaseModel):
    id: str
    kind: str
    level: str
    created_at: datetime


class InsightOut(BaseModel):
    id: str
    conversation_id: str
    app: str | None
    level: str
    patterns: list[str]
    situation: str | None
    source: str | None
    # The language child_nudge, parent_insight and micro_lesson are in.
    language: str
    # What the child was told, so the parent knows what the child has already heard.
    child_nudge: str
    parent_insight: dict
    micro_lesson: dict | None
    # Verified channels from configuration (never model-written), for waspada and above.
    help_channels: list[str]
    created_at: datetime


class DeviceStatus(BaseModel):
    device_id: str
    name: str
    protection_on: bool
    services: dict[str, bool]
    last_seen_at: datetime | None


class Overview(BaseModel):
    child_id: str
    nickname: str
    age_range: str
    consent_scopes: list[str]
    # Highest current level among conversations active in the window.
    level: str
    window_days: int
    conversations_active: int
    conversations_needing_attention: int
    events_by_kind: dict[str, int]
    sensitive_images_blurred: int
    devices: list[DeviceStatus]
    latest_insight: InsightOut | None


def _latest_assessments(db: Session, child_id: uuid.UUID, since: datetime | None = None):
    """(conversation, latest assessment) per conversation of this child. The score never
    drops, so the latest assessment is also the highest."""
    latest = (
        select(
            RiskAssessment.conversation_id,
            func.max(RiskAssessment.created_at).label("at"),
        )
        .join(Conversation, Conversation.id == RiskAssessment.conversation_id)
        .where(Conversation.child_id == child_id)
        .group_by(RiskAssessment.conversation_id)
        .subquery()
    )
    q = (
        select(Conversation, RiskAssessment)
        .join(latest, latest.c.conversation_id == Conversation.id)
        .join(
            RiskAssessment,
            (RiskAssessment.conversation_id == latest.c.conversation_id)
            & (RiskAssessment.created_at == latest.c.at),
        )
        .order_by(RiskAssessment.created_at.desc())
    )
    if since is not None:
        q = q.where(RiskAssessment.created_at >= since)
    seen: set[uuid.UUID] = set()
    for conv, ra in db.execute(q).all():
        if conv.id not in seen:  # two assessments in the same instant: keep one
            seen.add(conv.id)
            yield conv, ra


def conversations(db: Session, child: ChildProfile, days: int = 30) -> list[ConversationSummary]:
    since = utcnow() - timedelta(days=days)
    return [
        ConversationSummary(
            conversation_id=str(conv.id),
            assessment_id=str(ra.id),
            app=conv.app,
            channel=conv.channel,
            level=ra.level,
            risk_score=ra.score,
            patterns=list(ra.patterns),
            confidence=ra.confidence,
            rationale_for_parent=ra.rationale,
            started_at=conv.started_at,
            updated_at=ra.created_at,
        )
        for conv, ra in _latest_assessments(db, child.id, since)
    ]


def events(db: Session, child: ChildProfile, days: int = 30, limit: int = 100) -> list[EventOut]:
    since = utcnow() - timedelta(days=days)
    rows = db.scalars(
        select(Event)
        .where(Event.child_id == child.id, Event.created_at >= since)
        .order_by(Event.created_at.desc(), Event.id)
        .limit(limit)
    ).all()
    return [
        EventOut(id=str(e.id), kind=e.kind, level=e.level, created_at=e.created_at) for e in rows
    ]


def insights(
    db: Session, child: ChildProfile, limit: int = 20, language: str = "id"
) -> list[InsightOut]:
    rows = db.execute(
        select(Insight, RiskAssessment, Conversation)
        .join(RiskAssessment, RiskAssessment.id == Insight.assessment_id)
        .join(Conversation, Conversation.id == RiskAssessment.conversation_id)
        .where(Conversation.child_id == child.id)
        .order_by(Insight.created_at.desc(), Insight.id)
        .limit(limit)
    ).all()
    return [
        InsightOut(
            id=str(ins.id),
            conversation_id=str(conv.id),
            app=conv.app,
            level=ra.level,
            patterns=list(ra.patterns),
            situation=ins.situation,
            source=ins.source,
            language=ins.language or language,
            child_nudge=ins.child_nudge,
            parent_insight=ins.parent_insight,
            micro_lesson=ins.micro_lesson,
            help_channels=list(
                help_channels(
                    Level(ra.level), Situation(ins.situation or Situation.GENERAL), language
                )
            ),
            created_at=ins.created_at,
        )
        for ins, ra, conv in rows
    ]


def device_status(db: Session, child: ChildProfile) -> list[DeviceStatus]:
    rows = db.scalars(
        select(Device)
        .where(Device.child_id == child.id, Device.revoked_at.is_(None))
        .order_by(Device.paired_at)
    ).all()
    return [
        DeviceStatus(
            device_id=str(d.id),
            name=d.name,
            protection_on=all((d.services or {}).get(s) is True for s in REQUIRED_SERVICES),
            services=d.services or {},
            last_seen_at=d.last_seen_at,
        )
        for d in rows
    ]


def overview(db: Session, child: ChildProfile, days: int = 7, language: str = "id") -> Overview:
    since = utcnow() - timedelta(days=days)
    convs = list(_latest_assessments(db, child.id, since))
    level = max((ra.level for _, ra in convs), key=_RANK.__getitem__, default=Level.AMAN.value)
    kinds = Counter(
        db.scalars(
            select(Event.kind).where(Event.child_id == child.id, Event.created_at >= since)
        ).all()
    )
    blurred = db.scalar(
        select(func.count())
        .select_from(ImageSignal)
        .where(
            ImageSignal.child_id == child.id,
            ImageSignal.created_at >= since,
            ImageSignal.action == "dikaburkan",
        )
    )
    latest = insights(db, child, limit=1, language=language)
    return Overview(
        child_id=str(child.id),
        nickname=child.nickname,
        age_range=child.age_range,
        consent_scopes=sorted(active_scopes(db, child.id)),
        level=level,
        window_days=days,
        conversations_active=len(convs),
        conversations_needing_attention=sum(
            1 for _, ra in convs if _RANK[ra.level] >= _RANK[Level.WASPADA.value]
        ),
        events_by_kind=dict(sorted(kinds.items())),
        sensitive_images_blurred=blurred or 0,
        devices=device_status(db, child),
        latest_insight=latest[0] if latest else None,
    )
