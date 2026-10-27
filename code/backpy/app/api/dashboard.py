"""Read endpoints for the parent dashboard. Levels, patterns, events and insight; never
message text, which is not stored anywhere."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbDep, GuardianDep, owned_child
from app.dashboard import queries
from app.dashboard.queries import ConversationSummary, DeviceStatus, EventOut, InsightOut, Overview

router = APIRouter(tags=["dashboard"])

Days = Annotated[int, Query(ge=1, le=90)]


@router.get("/children/{child_id}/overview")
def overview(child_id: uuid.UUID, db: DbDep, guardian: GuardianDep, days: Days = 7) -> Overview:
    return queries.overview(db, owned_child(db, guardian, child_id), days, guardian.language)


@router.get("/children/{child_id}/conversations")
def conversations(
    child_id: uuid.UUID, db: DbDep, guardian: GuardianDep, days: Days = 30
) -> list[ConversationSummary]:
    return queries.conversations(db, owned_child(db, guardian, child_id), days)


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
    return queries.insights(db, owned_child(db, guardian, child_id), limit, guardian.language)


@router.get("/children/{child_id}/protection")
def protection(child_id: uuid.UUID, db: DbDep, guardian: GuardianDep) -> list[DeviceStatus]:
    return queries.device_status(db, owned_child(db, guardian, child_id))
