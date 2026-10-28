"""The AI that helps a parent with time online: a weekly summary, advice on a time request,
and suggested limits. Muse Spark writes; code checks; a fixed text stands in when the model
is unavailable. Inputs are aggregates and masked text only, and the child is "the child",
never a name. The parent always decides.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.family.policy import ScreenPolicy, Session, defaults_for_age
from app.guide.schemas import ActLine
from app.llm.base import LLMClient, LLMError
from app.text import GuideText

log = logging.getLogger("dcai.family")

Short = Annotated[GuideText, StringConstraints(max_length=240)]
Long = Annotated[GuideText, StringConstraints(max_length=700)]
Clock = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]

_RULES = (
    "Rules: warm and practical, never blame the child, never suggest punishment, taking the "
    "phone away or forbidding. Do not cite research, statistics, health guidelines or "
    "experts; speak only from the numbers given. No links, phone numbers or names. Plain "
    "sentences, no dashes. Write in {language}."
)


def _language(code: str) -> str:
    return "Indonesian" if code == "id" else "English"


# ---------------------------------------------------------------- weekly digest


class Digest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: Annotated[GuideText, StringConstraints(max_length=120)]
    summary: Long
    highlights: list[Short] = Field(min_length=2, max_length=4)
    conversation_starters: list[ActLine] = Field(min_length=3, max_length=3)
    suggestion: ActLine


DIGEST_SYSTEM = (
    "Role: a family guide to healthy digital habits for parents of children aged 10 to 17. Input: "
    "one week of aggregate numbers for one child: safety events by kind, the highest risk "
    "level per day, minutes online per category per day, minutes online during bedtime, "
    "the longest continuous session and time requests. Task: a short weekly summary for "
    "the parent: what stands out, what went well, three conversation starters, and one "
    "gentle suggestion. If safety events and late-night use appear together, say so with "
    "care. " + _RULES
)


@dataclass
class DigestResult:
    output: Digest
    source: str  # model | template


async def weekly_digest(client: LLMClient, facts: dict, language: str) -> DigestResult:
    payload = json.dumps({**facts, "language": _language(language)}, ensure_ascii=False)
    try:
        result = await client.complete_json(
            purpose="digest",
            system=DIGEST_SYSTEM.format(language=_language(language)),
            user=payload,
            schema=Digest,
            max_tokens=2500,
            timeout=45.0,
        )
        return DigestResult(result.value, "model")
    except LLMError as exc:
        log.warning("digest_unavailable error=%s", type(exc).__name__)
        return DigestResult(digest_template(facts, language), "template")


def _hm(minutes: float, language: str) -> str:
    h, m = divmod(round(minutes), 60)
    if language == "id":
        return f"{h} jam {m} menit" if h else f"{m} menit"
    return f"{h} h {m} min" if h else f"{m} min"


def digest_template(facts: dict, language: str) -> Digest:
    days = facts.get("usage_days") or []
    avg = sum(d["total"] for d in days) / len(days) if days else 0
    late = sum(d["bedtime_minutes"] for d in days)
    events = sum((facts.get("events") or {}).values())
    if language == "id":
        return Digest(
            headline="Ringkasan minggu ini",
            summary=(
                f"Rata-rata waktu online {_hm(avg, 'id')} per hari selama {len(days)} hari "
                f"tercatat. Ada {events} kejadian keselamatan minggu ini."
            ),
            highlights=[
                f"Waktu online di jam tidur: {_hm(late, 'id')} dalam seminggu.",
                f"Permintaan tambahan waktu: {facts.get('time_requests', 0)}.",
            ],
            conversation_starters=[
                "Aplikasi apa yang paling seru minggu ini?",
                "Kapan waktu yang paling enak buat istirahat dari ponsel?",
                "Ada hal di internet yang bikin kamu bingung minggu ini?",
            ],
            suggestion="Ajak anak memilih bersama satu kebiasaan kecil untuk minggu depan.",
        )
    return Digest(
        headline="This week at a glance",
        summary=(
            f"Average time online was {_hm(avg, 'en')} a day over {len(days)} recorded "
            f"days. There were {events} safety events this week."
        ),
        highlights=[
            f"Time online during bedtime: {_hm(late, 'en')} this week.",
            f"Requests for more time: {facts.get('time_requests', 0)}.",
        ],
        conversation_starters=[
            "Which app was the most fun this week?",
            "When is the best time to take a break from the phone?",
            "Did anything online confuse you this week?",
        ],
        suggestion="Choose one small habit together for next week.",
    )


# ---------------------------------------------------------------- time request advice


class TimeAdvice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary_for_parent: Short
    recommendation: Literal["izinkan", "sebagian", "tunda"]
    suggested_minutes: Annotated[int, Field(ge=0, le=120)]
    rationale: Short


ADVICE_SYSTEM = (
    "Role: helps a parent decide on a child's request for more time online. Input: the "
    "child's masked reason, the minutes asked, minutes used today and today's limit, the "
    "category, and minutes until bedtime. Task: summarise the request in one sentence, then "
    "recommend izinkan (allow), sebagian (part of it, with suggested_minutes) or tunda (not "
    "now), with one sentence why. Respect bedtime; schoolwork reasons count for more. "
    "suggested_minutes is 0 for tunda. The parent decides. " + _RULES
)


async def time_advice(client: LLMClient, request: dict, language: str) -> tuple[TimeAdvice, str]:
    payload = json.dumps({**request, "language": _language(language)}, ensure_ascii=False)
    try:
        result = await client.complete_json(
            purpose="time_advice",
            system=ADVICE_SYSTEM.format(language=_language(language)),
            user=payload,
            schema=TimeAdvice,
            max_tokens=1200,
            timeout=30.0,
        )
        advice = result.value
        if advice.recommendation == "tunda":
            advice = advice.model_copy(update={"suggested_minutes": 0})
        else:
            advice = advice.model_copy(
                update={"suggested_minutes": min(advice.suggested_minutes, request["minutes"])}
            )
        return advice, "model"
    except LLMError as exc:
        log.warning("time_advice_unavailable error=%s", type(exc).__name__)
        return advice_template(request, language), "template"


def advice_template(request: dict, language: str) -> TimeAdvice:
    asked = request["minutes"]
    to_bed = request.get("minutes_to_bedtime")
    near_bed = to_bed is not None and to_bed < asked
    rec = "tunda" if to_bed is not None and to_bed <= 0 else "sebagian" if near_bed else "izinkan"
    minutes = 0 if rec == "tunda" else max(0, min(asked, to_bed)) if near_bed else asked
    if language == "id":
        why = {
            "tunda": "Sudah masuk jam tidur.",
            "sebagian": "Waktu yang diminta melewati jam tidur.",
            "izinkan": "Permintaan masih dalam batas hari ini.",
        }[rec]
        return TimeAdvice(
            summary_for_parent=f"Anak meminta tambahan {asked} menit.",
            recommendation=rec,
            suggested_minutes=minutes,
            rationale=why,
        )
    why = {
        "tunda": "It is already bedtime.",
        "sebagian": "The time asked runs past bedtime.",
        "izinkan": "The request fits within today.",
    }[rec]
    return TimeAdvice(
        summary_for_parent=f"The child asks for {asked} more minutes.",
        recommendation=rec,
        suggested_minutes=minutes,
        rationale=why,
    )


# ---------------------------------------------------------------- suggested limits


class SuggestedLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daily_limit_school: Annotated[int, Field(ge=30, le=600)]
    daily_limit_weekend: Annotated[int, Field(ge=30, le=720)]
    video: Annotated[int, Field(ge=10, le=600)]
    game: Annotated[int, Field(ge=10, le=600)]
    sosial: Annotated[int, Field(ge=10, le=600)]
    bedtime_school_start: Clock
    bedtime_weekend_start: Clock
    session_limit_minutes: Annotated[int, Field(ge=15, le=120)]
    rationale: Long


LIMITS_SYSTEM = (
    "Role: helps a parent set starting limits for time online. Input: the child's age range, "
    "two weeks of average minutes per category on school days and weekends, minutes online "
    "during bedtime, the longest sessions, and the current settings. Task: suggest daily "
    "limits, category limits, bedtime start times and a short-video session limit that are a "
    "realistic next step from what the child does now: change gradually, not all at once. "
    "Explain in two or three sentences. " + _RULES
)


async def suggest_limits(
    client: LLMClient, facts: dict, current: ScreenPolicy, age_range: str, language: str
) -> tuple[ScreenPolicy, str, str]:
    """(policy to propose, rationale, source). Unspecified fields keep the current values."""
    payload = json.dumps(
        {
            **facts,
            "age_range": age_range,
            "current": current.model_dump(mode="json"),
            "language": _language(language),
        },
        ensure_ascii=False,
    )
    try:
        result = await client.complete_json(
            purpose="suggest_limits",
            system=LIMITS_SYSTEM.format(language=_language(language)),
            user=payload,
            schema=SuggestedLimits,
            max_tokens=1500,
            timeout=30.0,
        )
        s = result.value
        policy = current.model_copy(
            update={
                "daily_limit_school": s.daily_limit_school,
                "daily_limit_weekend": s.daily_limit_weekend,
                "category_limits": {
                    **current.category_limits,
                    "video": s.video,
                    "game": s.game,
                    "sosial": s.sosial,
                },
                "bedtime_school": current.bedtime_school.model_copy(
                    update={"start": s.bedtime_school_start}
                ),
                "bedtime_weekend": current.bedtime_weekend.model_copy(
                    update={"start": s.bedtime_weekend_start}
                ),
                "session": _session(current.session, s.session_limit_minutes),
            }
        )
        return ScreenPolicy.model_validate(policy.model_dump()), s.rationale, "model"
    except (LLMError, ValueError) as exc:
        log.warning("suggest_limits_unavailable error=%s", type(exc).__name__)
        rationale = (
            "Ini pengaturan awal dcAI untuk rentang usia ini. Sesuaikan bersama anak."
            if language == "id"
            else "These are dcAI's starting settings for this age range. Adjust them together."
        )
        return defaults_for_age(age_range), rationale, "template"


def _session(current: Session, limit: int) -> Session:
    nudge = min(current.nudge_minutes, limit - 5)
    return current.model_copy(update={"limit_minutes": limit, "nudge_minutes": max(5, nudge)})
