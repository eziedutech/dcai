"""Read endpoints for the parent dashboard. Levels, patterns, events and insight; never
message text, which is not stored anywhere."""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request

from app.api.deps import DbDep, GuardianDep, owned_child
from app.dashboard import queries
from app.dashboard.queries import ConversationSummary, DeviceStatus, EventOut, InsightOut, Overview
from app.db.models import Insight, RiskAssessment
from app.guide.translate import guide_text, rationale_texts, written_in
from app.risk.schemas import Level

router = APIRouter(tags=["dashboard"])

Days = Annotated[int, Query(ge=1, le=90)]
# The dashboard's display language; the guardian's own language when absent.
Lang = Literal["id", "en"] | None


@router.get("/children/{child_id}/overview")
async def overview(
    child_id: uuid.UUID,
    request: Request,
    db: DbDep,
    guardian: GuardianDep,
    days: Days = 7,
    lang: Lang = None,
) -> Overview:
    target = lang or guardian.language
    ov = queries.overview(db, owned_child(db, guardian, child_id), days, target)
    latest = ov.latest_insight
    ins = db.get(Insight, uuid.UUID(latest.id)) if latest is not None else None
    if latest is not None and ins is not None:
        source = written_in(ins)
        update, actual = {}, source
        if source != target:
            update, actual = await guide_text(
                request.app.state.muse, db, ins, Level(latest.level), source, target
            )
        ov.latest_insight = latest.model_copy(update={**update, "language": actual})
    return ov


@router.get("/children/{child_id}/conversations")
async def conversations(
    child_id: uuid.UUID,
    request: Request,
    db: DbDep,
    guardian: GuardianDep,
    days: Days = 30,
    lang: Lang = None,
) -> list[ConversationSummary]:
    rows = queries.conversations(db, owned_child(db, guardian, child_id), days)
    target = lang or guardian.language
    if target == "id" or not rows:
        return rows
    ids = [uuid.UUID(r.assessment_id) for r in rows]
    found = db.query(RiskAssessment).filter(RiskAssessment.id.in_(ids)).all()
    texts = await rationale_texts(request.app.state.muse, db, found, target)
    return [
        r.model_copy(
            update={"rationale_for_parent": texts.get(r.assessment_id, r.rationale_for_parent)}
        )
        for r in rows
    ]


@router.get("/children/{child_id}/events")
def events(
    child_id: uuid.UUID,
    db: DbDep,
    guardian: GuardianDep,
    days: Days = 30,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[EventOut]:
    return queries.events(db, owned_child(db, guardian, child_id), days, limit)


@router.get("/children/{child_id}/insights")
def insights(
    child_id: uuid.UUID,
    db: DbDep,
    guardian: GuardianDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[InsightOut]:
    rows = queries.insights(db, owned_child(db, guardian, child_id), limit, guardian.language)
    out = []
    for r in rows:
        ins = None if r.language else db.get(Insight, uuid.UUID(r.id))
        out.append(r.model_copy(update={"language": written_in(ins)}) if ins else r)
    return out


@router.get("/children/{child_id}/protection")
def protection(child_id: uuid.UUID, db: DbDep, guardian: GuardianDep) -> list[DeviceStatus]:
    return queries.device_status(db, owned_child(db, guardian, child_id))
