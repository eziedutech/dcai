"""Citizenship Guide: turns an assessment into a nudge for the child, insight for the
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

from app.guide.channels import load_channels
from app.guide.schemas import GuideOutput
from app.llm import LLMClient, LLMError, LLMOutputInvalid, Usage
from app.risk.schemas import Level, Pattern
from app.scenarios.schema import ChildLabel

log = logging.getLogger("dcai.guide")

_MIXED_EN = re.compile(r"\b(kamu|anak|ya|dong|nggak)\b", re.I)


class Situation(StrEnum):
    APPROACH = "approach"  # a contact shows approach patterns toward the child
    # An invitation to a fight, drugs, alcohol or a weapon, from either side. The value
    # fits the insight.situation column (12 characters).
    DANGEROUS_INVITE = "dangerous"
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
    if ChildLabel.AJAKAN_BERBAHAYA in contact_labels | child_labels:
        return Situation.DANGEROUS_INVITE
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
- child_nudge: at most two short sentences to the child, friendly and without blame, suited \
to the age range. Open with one concrete action that names what to do (for example: stop \
this chat for now, do not reply, you can say no, you do not have to keep it secret) and who \
to turn to (talk to a parent or a trusted adult); keep any reassurance brief and after the \
action, never as the whole message and never a vague "pause" without saying what to pause. \
(Exception: situation "distress" opens with warm support, per its rule below.) In Indonesian \
address the child as "kamu"; in English as "you". Never mix the two languages.
- parent_insight: what_we_see (one short, plain sentence naming the pattern, never quotes), \
why_it_matters (one short sentence on why it matters for this child), exactly three \
conversation_starters the parent can say to the child (short and natural), do (one to four) \
and dont (one to four), each a short, plain phrase.
- micro_lesson: a one-minute digital citizenship lesson linked to the situation, or null \
for level aman.

Rules:
- Be brief, plain and firm: short sentences a busy parent reads at a glance. No filler, no \
hedging (avoid "mungkin", "dapat", "sehingga perlu diperhatikan", "may", "might"), and no \
"misalnya"/"for example" lists in the parent text.
- Never blame or shame the child. Never tell the parent to punish, forbid, take the phone \
or read the child's chats. Put such things only in "dont" as what to avoid.
- Never write a phone number, a website or an app name. If help is needed, say "kanal \
bantuan di bawah" / "the help channels below"; the app shows verified channels itself.
- Never use the long dash characters (em dash, en dash). Normal hyphens stay where the \
spelling needs them, as in "hati-hati", "akhir-akhir ini", "tiba-tiba". Plain sentences.
- Situation "distress": support first. Warm words, encourage talking to a trusted adult \
today, no analysis of the child, never mention methods or details of harm.
- Situation "dangerous": someone invited the child, or the child invited others, to a \
fight, drugs, alcohol or carrying a weapon. Help the child say no and step away safely, \
with an easy excuse and a trusted adult to tell; no blame, no lecture. Give the parent \
calm conversation starters about friends and pressure, never punishment or interrogation.
- Situation "bullying": the child wrote hurtful messages. Guide toward empathy and repair, \
still without shaming.
- Level "mendesak": tell the parent to keep evidence (screenshots), not to confront the \
other person directly, and to report through the platform and local authorities.
- Use the requested language for every field."""


@dataclass(frozen=True)
class GuideResult:
    output: GuideOutput
    situation: Situation
    source: str  # model | template
    help_channels: tuple[str, ...]
    usage: Usage | None


async def guide(
    client: LLMClient,
    *,
    level: Level,
    patterns: list[str],
    contact_labels: set[str],
    child_labels: set[str],
    support_needed: bool,
    age_range: str,
    language: str,
) -> GuideResult:
    sit = situation(contact_labels, child_labels, support_needed)
    channels = help_channels(level, sit, language)
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
            purpose="guide",
            system=SYSTEM,
            user=payload,
            schema=GuideOutput,
            max_tokens=3000,
            # Guide output is long; Fireworks timed out at 20 s on every guide call.
            timeout=45.0,
        )
        out = result.value
        if language == "en" and _MIXED_EN.search(out.model_dump_json()):
            raise LLMOutputInvalid("guide: English output mixed with Indonesian")
        if level == Level.AMAN:
            out = out.model_copy(update={"micro_lesson": None})
        return GuideResult(out, sit, "model", channels, result.usage)
    except LLMError as exc:
        log.warning("guide_unavailable error=%s situation=%s", type(exc).__name__, sit.value)
        from app.guide.templates import template

        return GuideResult(template(sit, level, language), sit, "template", channels, None)


def instant(
    *,
    level: Level,
    contact_labels: set[str],
    child_labels: set[str],
    support_needed: bool,
    language: str,
) -> GuideResult:
    """The reviewed template for this situation, at once and without a model. Sent to the
    phone with the new level so the child is guided while the model's Guide is written."""
    from app.guide.templates import template

    sit = situation(contact_labels, child_labels, support_needed)
    return GuideResult(
        template(sit, level, language), sit, "template", help_channels(level, sit, language), None
    )


def help_channels(level: Level, sit: Situation, language: str) -> tuple[str, ...]:
    """Verified help lines for this moment, from configuration; empty below waspada."""
    if sit == Situation.DISTRESS or level in (Level.WASPADA, Level.MENDESAK):
        return tuple(load_channels().lines(language, distress=sit == Situation.DISTRESS))
    return ()
