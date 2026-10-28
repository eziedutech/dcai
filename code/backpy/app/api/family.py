"""Time online (scope "waktu"): the parent's settings, daily totals from the phone, requests
for more time, and the family AI (weekly summary, advice, suggested limits).

The phone counts app use and enforces the limits. What reaches the server is minutes per
category per day, minutes during bedtime and the longest session; app names stay on the
phone. A time request carries the child's short reason, masked on the phone and again here.
"""

import asyncio
import logging
import uuid
from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import select

from app.analysis.service import broker
from app.api.deps import DbDep, DeviceDep, GuardianDep, SettingsDep, owned_child
from app.api.devices import _require, notify_config_changed
from app.consent.texts import Scope
from app.db.base import session_factory, utcnow
from app.db.models import ChildProfile, Event, FamilyDigest, Guardian, TimeRequest, UsageDay
from app.family import ai
from app.family.policy import CATEGORIES, ScreenPolicy
from app.family.service import (
    effective_status,
    late_night_events,
    limits_facts,
    policy_for,
    save_policy,
    usage_by_day,
    week_facts,
)
from app.live.broker import child_key, device_key
from app.privacy.mask import mask

log = logging.getLogger("dcai.family")

guardian_router = APIRouter(tags=["family"])
device_router = APIRouter(prefix="/device", tags=["device"])


# ---------------------------------------------------------------- policy


class PolicyOut(BaseModel):
    policy: ScreenPolicy
    is_default: bool


@guardian_router.get("/children/{child_id}/screen-policy")
def get_policy(child_id: uuid.UUID, db: DbDep, guardian: GuardianDep) -> PolicyOut:
    child = owned_child(db, guardian, child_id)
    policy, default = policy_for(db, child)
    return PolicyOut(policy=policy, is_default=default)


@guardian_router.put("/children/{child_id}/screen-policy")
def put_policy(
    child_id: uuid.UUID, body: ScreenPolicy, request: Request, db: DbDep, guardian: GuardianDep
) -> PolicyOut:
    child = owned_child(db, guardian, child_id)
    save_policy(db, child, body)
    db.commit()
    notify_config_changed(request.app.state, db, child.id)
    return PolicyOut(policy=body, is_default=False)


class SuggestionOut(BaseModel):
    policy: ScreenPolicy
    rationale: str
    source: Literal["model", "template"]


@guardian_router.post("/children/{child_id}/screen-policy/suggestion")
async def suggest_policy(
    child_id: uuid.UUID, request: Request, db: DbDep, guardian: GuardianDep
) -> SuggestionOut:
    """A proposal only: nothing changes until the parent saves it."""
    child = owned_child(db, guardian, child_id)
    current, _ = policy_for(db, child)
    facts = limits_facts(db, child)
    policy, rationale, source = await ai.suggest_limits(
        request.app.state.muse, facts, current, child.age_range, guardian.language
    )
    return SuggestionOut(policy=policy, rationale=rationale, source=source)


# ---------------------------------------------------------------- usage


class UsageDayIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: date
    minutes: dict[Literal["video", "game", "sosial", "lain"], Annotated[int, Field(ge=0, le=1440)]]
    bedtime_minutes: Annotated[int, Field(ge=0, le=1440)] = 0
    longest_session: Annotated[int, Field(ge=0, le=1440)] = 0
    session_limits: Annotated[int, Field(ge=0, le=200)] = 0


class UsageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: list[UsageDayIn] = Field(min_length=1, max_length=3)


@device_router.post("/usage", status_code=status.HTTP_204_NO_CONTENT)
def device_usage(body: UsageIn, request: Request, db: DbDep, device: DeviceDep) -> None:
    """Totals for today (and the days not sent yet), replacing what the phone sent before."""
    _require(db, device, Scope.WAKTU)
    today = date.today()
    events: list[tuple[str, str]] = []
    for d in body.days:
        if not (today - timedelta(days=3) <= d.day <= today + timedelta(days=1)):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "day out of range")
        row = db.scalar(
            select(UsageDay).where(UsageDay.device_id == device.id, UsageDay.day == d.day)
        )
        minutes = {c: d.minutes.get(c, 0) for c in CATEGORIES}
        if row is None:
            row = UsageDay(
                child_id=device.child_id, device_id=device.id, day=d.day, minutes=minutes
            )
            db.add(row)
        row.minutes = minutes
        row.bedtime_minutes = d.bedtime_minutes
        row.longest_session = d.longest_session
        row.session_limits = d.session_limits
        row.updated_at = utcnow()
        events += late_night_events(db, device.child_id, d.bedtime_minutes)
    for kind, level in events[:1]:
        db.add(Event(child_id=device.child_id, kind=kind, level=level))
    db.commit()
    for kind, level in events[:1]:
        broker(request.app.state).publish(
            child_key(device.child_id), "event", {"kind": kind, "level": level}
        )


@guardian_router.get("/children/{child_id}/usage")
def child_usage(
    child_id: uuid.UUID, db: DbDep, guardian: GuardianDep, days: int = 14
) -> list[dict]:
    child = owned_child(db, guardian, child_id)
    return usage_by_day(db, child.id, max(1, min(days, 31)))


# ---------------------------------------------------------------- time requests


class RequestContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    used_today: Annotated[int, Field(ge=0, le=1440)] = 0
    limit_today: Annotated[int, Field(ge=0, le=1440)] | None = None
    category: Literal["video", "game", "sosial", "lain"] | None = None
    minutes_to_bedtime: Annotated[int, Field(ge=-1440, le=1440)] | None = None


class TimeRequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minutes: Annotated[int, Field(ge=5, le=120)]
    reason: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] = ""
    context: RequestContext = Field(default_factory=RequestContext)


class TimeRequestOut(BaseModel):
    id: str
    minutes: int
    reason: str
    status: str
    granted_minutes: int
    advice: dict | None
    context: dict
    created_at: str
    decided_at: str | None


def _out(r: TimeRequest) -> TimeRequestOut:
    return TimeRequestOut(
        id=str(r.id),
        minutes=r.minutes,
        reason=r.reason,
        status=effective_status(r),
        granted_minutes=r.granted_minutes,
        advice=r.advice,
        context=r.context or {},
        created_at=r.created_at.isoformat(),
        decided_at=r.decided_at.isoformat() if r.decided_at else None,
    )


@device_router.post("/time-requests", status_code=status.HTTP_201_CREATED)
async def device_time_request(
    body: TimeRequestIn,
    request: Request,
    db: DbDep,
    device: DeviceDep,
    settings: SettingsDep,
    wait: bool = False,
) -> TimeRequestOut:
    _require(db, device, Scope.WAKTU)
    child = db.get(ChildProfile, device.child_id)
    assert child is not None
    reason = mask(body.reason, (child.nickname,)).text[:200]
    req = TimeRequest(
        child_id=child.id,
        device_id=device.id,
        minutes=body.minutes,
        reason=reason,
        context=body.context.model_dump(),
    )
    db.add(req)
    db.add(Event(child_id=child.id, kind="permintaan_waktu", level="aman"))
    db.commit()
    db.refresh(req)
    guardian = db.get(Guardian, child.guardian_id)
    language = guardian.language if guardian else "id"
    job = _advise(request.app.state, settings.database_url, req.id, language)
    if wait:
        await job
    else:
        # Kept referenced until done, so the task is not collected mid-way.
        tasks = getattr(request.app.state, "family_tasks", None)
        if tasks is None:
            tasks = request.app.state.family_tasks = set()
        task = asyncio.create_task(job)
        tasks.add(task)
        task.add_done_callback(tasks.discard)
    db.refresh(req)
    return _out(req)


async def _advise(state, database_url: str, request_id: uuid.UUID, language: str) -> None:
    """Advice for the parent, then a live update. A failure leaves the request without
    advice; the parent can still decide."""
    with session_factory(database_url)() as db:
        req = db.get(TimeRequest, request_id)
        if req is None:
            return
        payload = {"minutes": req.minutes, "reason_masked": req.reason, **(req.context or {})}
        advice, source = await ai.time_advice(state.muse, payload, language)
        req.advice = {**advice.model_dump(), "source": source}
        db.commit()
        broker(state).publish(
            child_key(req.child_id), "time_request", _out(req).model_dump(mode="json")
        )


@device_router.get("/time-requests")
def device_time_requests(db: DbDep, device: DeviceDep) -> list[TimeRequestOut]:
    _require(db, device, Scope.WAKTU)
    rows = db.scalars(
        select(TimeRequest)
        .where(TimeRequest.device_id == device.id)
        .order_by(TimeRequest.created_at.desc())
        .limit(5)
    ).all()
    return [_out(r) for r in rows]


@guardian_router.get("/children/{child_id}/time-requests")
def child_time_requests(
    child_id: uuid.UUID, db: DbDep, guardian: GuardianDep
) -> list[TimeRequestOut]:
    child = owned_child(db, guardian, child_id)
    rows = db.scalars(
        select(TimeRequest)
        .where(TimeRequest.child_id == child.id)
        .order_by(TimeRequest.created_at.desc())
        .limit(20)
    ).all()
    return [_out(r) for r in rows]


class DecisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approve: bool
    minutes: Annotated[int, Field(ge=1, le=120)] | None = None


@guardian_router.post("/time-requests/{request_id}/decision")
def decide(
    request_id: uuid.UUID, body: DecisionIn, request: Request, db: DbDep, guardian: GuardianDep
) -> TimeRequestOut:
    req = db.get(TimeRequest, request_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    owned_child(db, guardian, req.child_id)
    if effective_status(req) != "menunggu":
        raise HTTPException(status.HTTP_409_CONFLICT, "request already closed")
    req.status = "diizinkan" if body.approve else "ditolak"
    req.granted_minutes = min(body.minutes or req.minutes, 120) if body.approve else 0
    req.decided_at = utcnow()
    db.commit()
    if req.device_id is not None:
        broker(request.app.state).publish(
            device_key(req.device_id),
            "time_decision",
            {"request_id": str(req.id), "approved": body.approve, "minutes": req.granted_minutes},
        )
    return _out(req)


# ---------------------------------------------------------------- weekly digest


class DigestOut(BaseModel):
    week_start: str
    output: dict
    source: str
    created_at: str


def _digest_out(d: FamilyDigest) -> DigestOut:
    return DigestOut(
        week_start=d.week_start.isoformat(),
        output=d.output,
        source=d.source,
        created_at=d.created_at.isoformat(),
    )


@guardian_router.get("/children/{child_id}/digest")
def latest_digest(child_id: uuid.UUID, db: DbDep, guardian: GuardianDep) -> DigestOut | None:
    child = owned_child(db, guardian, child_id)
    row = db.scalar(
        select(FamilyDigest)
        .where(FamilyDigest.child_id == child.id)
        .order_by(FamilyDigest.created_at.desc())
        .limit(1)
    )
    return _digest_out(row) if row else None


@guardian_router.post("/children/{child_id}/digest", status_code=status.HTTP_201_CREATED)
async def make_digest(
    child_id: uuid.UUID, request: Request, db: DbDep, guardian: GuardianDep
) -> DigestOut:
    """Writes this week's summary. At most once per hour per child."""
    child = owned_child(db, guardian, child_id)
    recent = db.scalar(
        select(FamilyDigest)
        .where(
            FamilyDigest.child_id == child.id,
            FamilyDigest.created_at >= utcnow() - timedelta(hours=1),
        )
        .order_by(FamilyDigest.created_at.desc())
        .limit(1)
    )
    if recent is not None:
        return _digest_out(recent)
    facts = week_facts(db, child)
    result = await ai.weekly_digest(request.app.state.muse, facts, guardian.language)
    today = date.today()
    row = FamilyDigest(
        child_id=child.id,
        week_start=today - timedelta(days=today.weekday()),
        output=result.output.model_dump(),
        source=result.source,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _digest_out(row)
