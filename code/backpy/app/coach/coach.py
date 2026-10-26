"""Citizenship Coach: turns an assessment into a nudge for the child, insight for the
parent and an optional one-minute lesson (spec section 8.3).

Input is the level, the patterns, which side showed them, the age range and the language.
Never message text. If the model fails or breaks a rule, fixed templates answer, so every
level always gets all three outputs. Help channels come from verified configuration and
are attached by code, never written by the model.
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import StrEnum

from app.coach.channels import load_channels
from app.coach.schemas import CoachOutput
from app.llm import LLMClient, LLMError, LLMOutputInvalid, Usage
from app.risk.schemas import Level, Pattern
from app.scenarios.schema import ChildLabel

log = logging.getLogger("dcai.coach")

_MIXED_EN = re.compile(r"\b(kamu|anak|ya|dong|nggak)\b", re.I)


class Situation(StrEnum):
    APPROACH = "approach"  # a contact shows approach patterns toward the child
    BULLIED = "bullied"  # the child is the target of bullying or threats
    BULLYING = "bullying"  # the child's own messages are hurtful
    SHARED_DATA = "shared_data"  # the child gave away personal data
    DISTRESS = "distress"  # the child expresses distress: support first
    GENERAL = "general"


_PEER_HARM = {ChildLabel.PERUNDUNGAN, ChildLabel.KATA_KASAR, Pattern.MENEKAN_MENGANCAM}


def situation(contact_labels: set[str], child_labels: set[str], support_needed: bool) -> Situation:
    """Pick the most important situation. Distress first: support comes before scoring."""
    if support_needed or ChildLabel.MENYAKITI_DIRI in child_labels:
        return Situation.DISTRESS
    approach = contact_labels & {str(p) for p in Pattern if p != Pattern.MENEKAN_MENGANCAM}
    if approach:
        return Situation.APPROACH
    if contact_labels & {str(x) for x in _PEER_HARM}:
        return Situation.BULLIED
    if child_labels & {str(x) for x in _PEER_HARM}:
        return Situation.BULLYING
    if ChildLabel.BERBAGI_DATA_PRIBADI in child_labels:
        return Situation.SHARED_DATA
    return Situation.GENERAL


SYSTEM = """\
Role: a warm digital-citizenship companion for a child and their parent. You receive a \
risk level, behaviour patterns, the situation, the child's age range and the language. \
You never see the conversation.

Write JSON only:
- child_nudge: at most two short sentences to the child, friendly, without blame, suited \
to the age range, offering one clear action. In Indonesian address the child as "kamu"; \
in English as "you". Never mix the two languages.
- parent_insight: what_we_see (the pattern, never quotes), why_it_matters, exactly three \
conversation_starters the parent can say to the child, do (one to four), dont (one to four).
- micro_lesson: a one-minute digital citizenship lesson linked to the situation, or null \
for level aman.

Rules:
- Never blame or shame the child. Never tell the parent to punish, forbid, take the phone \
or read the child's chats. Put such things only in "dont" as what to avoid.
- Never write a phone number, a website or an app name. If help is needed, say "kanal \
bantuan di bawah" / "the help channels below"; the app shows verified channels itself.
- Never use the long dash characters (em dash, en dash). Normal hyphens stay where the \
spelling needs them, as in "hati-hati", "akhir-akhir ini", "tiba-tiba". Plain sentences.
- Situation "distress": support first. Warm words, encourage talking to a trusted adult \
today, no analysis of the child, never mention methods or details of harm.
- Situation "bullying": the child wrote hurtful messages. Guide toward empathy and repair, \
still without shaming.
- Level "mendesak": tell the parent to keep evidence (screenshots), not to confront the \
other person directly, and to report through the platform and local authorities.
- Use the requested language for every field."""


@dataclass(frozen=True)
class CoachResult:
    output: CoachOutput
    situation: Situation
    source: str  # model | template
    help_channels: tuple[str, ...]
    usage: Usage | None


async def coach(
    client: LLMClient,
    *,
    level: Level,
    patterns: list[str],
    contact_labels: set[str],
    child_labels: set[str],
    support_needed: bool,
    age_range: str,
    language: str,
) -> CoachResult:
    sit = situation(contact_labels, child_labels, support_needed)
    channels = (
        tuple(load_channels().lines(language, distress=sit == Situation.DISTRESS))
        if _needs_channels(level, sit)
        else ()
    )
    payload = json.dumps(
        {
            "level": level.value,
            "situation": sit.value,
            "patterns": sorted(patterns),
            "child_age_range": age_range,
            "language": "Indonesian" if language == "id" else "English",
        },
        ensure_ascii=False,
    )
    try:
        result = await client.complete_json(
            purpose="coach",
            system=SYSTEM,
            user=payload,
            schema=CoachOutput,
            max_tokens=3000,
            # Coach output is long; Fireworks timed out at 20 s on every coach call.
            timeout=45.0,
        )
        out = result.value
        if language == "en" and _MIXED_EN.search(out.model_dump_json()):
            raise LLMOutputInvalid("coach: English output mixed with Indonesian")
        if level == Level.AMAN:
            out = out.model_copy(update={"micro_lesson": None})
        return CoachResult(out, sit, "model", channels, result.usage)
    except LLMError as exc:
        log.warning("coach_unavailable error=%s situation=%s", type(exc).__name__, sit.value)
        from app.coach.templates import template

        return CoachResult(template(sit, level, language), sit, "template", channels, None)


def _needs_channels(level: Level, sit: Situation) -> bool:
    return sit == Situation.DISTRESS or level in (Level.WASPADA, Level.MENDESAK)
