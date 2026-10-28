"""Time online on the server: the child's policy, daily totals, late-night signals, and
the aggregate facts the family AI reads."""

from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.db.models import (
    ChildProfile,
    Conversation,
    Event,
    RiskAssessment,
    ScreenPolicyRow,
    TimeRequest,
    UsageDay,
)
from app.family.policy import CATEGORIES, ScreenPolicy, defaults_for_age

# Minutes online during bedtime on one day before the parent is told.
LATE_NIGHT_MINUTES = 15
# Kinds that mean the child may need support, for the combined late-night signal.
_SUPPORT_KINDS = ("dukungan_dibutuhkan",)
_HIGH_LEVELS = ("waspada", "mendesak")
_LEVEL_ORDER = ("aman", "perhatian", "waspada", "mendesak")


def policy_for(db: Session, child: ChildProfile) -> tuple[ScreenPolicy, bool]:
    """(policy, is_default)."""
    row = db.get(ScreenPolicyRow, child.id)
    if row is None:
        return defaults_for_age(child.age_range), True
    return ScreenPolicy.model_validate(row.policy), False


def save_policy(db: Session, child: ChildProfile, policy: ScreenPolicy) -> None:
    row = db.get(ScreenPolicyRow, child.id)
    data = policy.model_dump(mode="json")
    if row is None:
        db.add(ScreenPolicyRow(child_id=child.id, policy=data))
    else:
        row.policy = data
        row.updated_at = utcnow()


def usage_by_day(db: Session, child_id: uuid.UUID, days: int) -> list[dict]:
    """One entry per day with data, phones combined, oldest first."""
    since = date.today() - timedelta(days=days - 1)
    rows = db.scalars(
        select(UsageDay).where(UsageDay.child_id == child_id, UsageDay.day >= since)
    ).all()
    merged: dict[date, dict] = {}
    for r in rows:
        d = merged.setdefault(
            r.day,
            {"minutes": dict.fromkeys(CATEGORIES, 0), "bedtime": 0, "longest": 0, "limits": 0},
        )
        for c in CATEGORIES:
            d["minutes"][c] += int((r.minutes or {}).get(c, 0))
        d["bedtime"] += r.bedtime_minutes
        d["longest"] = max(d["longest"], r.longest_session)
        d["limits"] += r.session_limits
    return [
        {
            "day": day.isoformat(),
            "weekend": day.isoweekday() >= 6,
            "minutes": v["minutes"],
            "total": sum(v["minutes"].values()),
            "bedtime_minutes": v["bedtime"],
            "longest_session": v["longest"],
            "session_limits": v["limits"],
        }
        for day, v in sorted(merged.items())
    ]


def late_night_events(
    db: Session, child_id: uuid.UUID, bedtime_minutes: int
) -> list[tuple[str, str]]:
    """Events for a day with time online during bedtime: (kind, level). Told at most once
    in 20 hours; stronger when the child also showed a need for support or a chat reached
    waspada in the last 7 days."""
    if bedtime_minutes < LATE_NIGHT_MINUTES:
        return []
    now = utcnow()
    recent = db.scalar(
        select(Event.id).where(
            Event.child_id == child_id,
            Event.kind.in_(("jam_tidur_terlewati", "larut_malam_dan_dukungan")),
            Event.created_at >= now - timedelta(hours=20),
        )
    )
    if recent is not None:
        return []
    week = now - timedelta(days=7)
    support = db.scalar(
        select(Event.id).where(
            Event.child_id == child_id, Event.kind.in_(_SUPPORT_KINDS), Event.created_at >= week
        )
    )
    high = db.scalar(
        select(RiskAssessment.id)
        .join(Conversation, Conversation.id == RiskAssessment.conversation_id)
        .where(
            Conversation.child_id == child_id,
            RiskAssessment.level.in_(_HIGH_LEVELS),
            RiskAssessment.created_at >= week,
        )
    )
    if support is not None or high is not None:
        return [("larut_malam_dan_dukungan", "waspada")]
    return [("jam_tidur_terlewati", "perhatian")]


def week_facts(db: Session, child: ChildProfile) -> dict:
    """Aggregates for the weekly digest. Counts and minutes only."""
    since = utcnow() - timedelta(days=7)
    kinds = Counter(
        db.scalars(
            select(Event.kind).where(Event.child_id == child.id, Event.created_at >= since)
        ).all()
    )
    levels: dict[str, str] = defaultdict(lambda: "aman")
    for created, level in db.execute(
        select(RiskAssessment.created_at, RiskAssessment.level)
        .join(Conversation, Conversation.id == RiskAssessment.conversation_id)
        .where(Conversation.child_id == child.id, RiskAssessment.created_at >= since)
    ).all():
        day = created.date().isoformat()
        if _LEVEL_ORDER.index(level) > _LEVEL_ORDER.index(levels[day]):
            levels[day] = level
    requests = db.execute(
        select(TimeRequest.status, func.count())
        .where(TimeRequest.child_id == child.id, TimeRequest.created_at >= since)
        .group_by(TimeRequest.status)
    ).all()
    policy, _ = policy_for(db, child)
    return {
        "child_age_range": child.age_range,
        "events": dict(sorted(kinds.items())),
        "highest_level_per_day": dict(sorted(levels.items())),
        "usage_days": usage_by_day(db, child.id, 7),
        "time_requests": sum(n for _, n in requests),
        "time_requests_by_status": {s: n for s, n in requests},
        "limits": {
            "daily_school": policy.daily_limit_school,
            "daily_weekend": policy.daily_limit_weekend,
            "bedtime_school_start": policy.bedtime_school.start,
        },
    }


def limits_facts(db: Session, child: ChildProfile) -> dict:
    """Two weeks of averages, school days and weekends apart, for suggested limits."""
    days = usage_by_day(db, child.id, 14)

    def avg(rows: list[dict], key) -> int:
        return round(sum(key(r) for r in rows) / len(rows)) if rows else 0

    out = {"days_recorded": len(days)}
    for label, rows in (
        ("school_days", [d for d in days if not d["weekend"]]),
        ("weekends", [d for d in days if d["weekend"]]),
    ):
        out[label] = {
            "average_total": avg(rows, lambda r: r["total"]),
            "average_per_category": {
                c: avg(rows, lambda r, c=c: r["minutes"][c]) for c in CATEGORIES
            },
            "average_bedtime_minutes": avg(rows, lambda r: r["bedtime_minutes"]),
            "longest_session": max((r["longest_session"] for r in rows), default=0),
        }
    return out


EXPIRY = timedelta(hours=3)


def effective_status(req: TimeRequest) -> str:
    if req.status == "menunggu" and utcnow() - req.created_at > EXPIRY:
        return "kedaluwarsa"
    return req.status
