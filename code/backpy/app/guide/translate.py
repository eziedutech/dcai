"""The Guide's text in the language the parent reads the dashboard in.

An insight is written once, in the guardian's language at the time. When the dashboard is
shown in the other language:

- a template insight is rendered again from the template in that language, at no cost;
- a model insight is translated once by the reasoning pool, validated by the same schema as
  the Guide itself (no blame, no punishment, no links or phone-like numbers), and kept with
  the insight so the next view needs no call;
- if translation fails, the original text stays.

The model receives the Guide's own output only: patterns and advice, never message text.
"""

import json
import logging
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.orm import Session

from app.db.models import Insight, RiskAssessment
from app.guide.guide import _MIXED_EN, Situation
from app.guide.schemas import GuideOutput
from app.llm import LLMClient, LLMError, LLMOutputInvalid
from app.risk.schemas import Level
from app.text import GuideText

log = logging.getLogger("dcai.guide")

SYSTEM = """You translate a parent's guidance card for a child-safety app. The input is \
JSON with child_nudge, parent_insight and micro_lesson. Translate every text field into the \
target language, keeping the meaning, the warm tone, the number of items in each list and \
the JSON structure. Address the child as "kamu" in Indonesian and "you" in English. Do not \
add advice, links, phone numbers or names. Never mix the two languages. Output ONLY JSON in \
the given schema."""

LANGUAGES = {"id": "Indonesian", "en": "English"}


def _text(ins: Insight) -> dict:
    return {
        "child_nudge": ins.child_nudge,
        "parent_insight": ins.parent_insight,
        "micro_lesson": ins.micro_lesson,
    }


async def guide_text(
    client: LLMClient, db: Session, ins: Insight, level: Level, source_language: str, target: str
) -> tuple[dict, str]:
    """(child_nudge, parent_insight, micro_lesson) in the target language, and the language
    they are actually in (the original's when translation is unavailable)."""
    if target == source_language or target not in LANGUAGES:
        return _text(ins), source_language
    cached = (ins.translations or {}).get(target)
    if cached:
        return cached, target
    if ins.source == "template" and ins.situation:
        from app.guide.templates import template

        out = template(Situation(ins.situation), level, target)
        return _out_text(out, keep_lesson=ins.micro_lesson is not None), target
    try:
        result = await client.complete_json(
            purpose="guide_translate",
            system=SYSTEM,
            user=json.dumps(
                {"target_language": LANGUAGES[target], **_text(ins)}, ensure_ascii=False
            ),
            schema=GuideOutput,
            max_tokens=3000,
            timeout=45.0,
        )
        out = result.value
        if target == "en" and _MIXED_EN.search(out.model_dump_json()):
            raise LLMOutputInvalid("guide_translate: English output mixed with Indonesian")
    except LLMError as exc:
        log.warning("guide_translate_unavailable error=%s", type(exc).__name__)
        return _text(ins), source_language
    text = _out_text(out, keep_lesson=ins.micro_lesson is not None)
    # A new dict, so the JSON column registers the change.
    ins.translations = {**(ins.translations or {}), target: text}
    db.commit()
    return text, target


def _out_text(out: GuideOutput, keep_lesson: bool) -> dict:
    return {
        "child_nudge": out.child_nudge,
        "parent_insight": out.parent_insight.model_dump(),
        "micro_lesson": out.micro_lesson.model_dump() if out.micro_lesson and keep_lesson else None,
    }


# Stage 2 writes the rationale for the parent in Indonesian. For an English dashboard the
# rationales of one list are translated together in one call, at most this many at a time.
RATIONALE_BATCH = 12

RATIONALE_SYSTEM = """You translate short explanations for parents in a child-safety app \
from Indonesian into English. The input is JSON with items, each an id and a text. Return \
the same ids with each text translated, keeping the meaning and length. Do not add advice, \
links, phone numbers or names. Output ONLY JSON in the given schema."""


class _Item(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    text: Annotated[GuideText, StringConstraints(max_length=400)]


class _Items(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[_Item] = Field(max_length=RATIONALE_BATCH)


async def rationale_texts(
    client: LLMClient, db: Session, assessments: list[RiskAssessment], target: str
) -> dict[str, str]:
    """Assessment id to the rationale in the target language; the original where a
    translation is unavailable."""
    out = {str(ra.id): ra.rationale for ra in assessments}
    if target == "id" or target not in LANGUAGES:
        return out
    todo = []
    for ra in assessments:
        cached = (ra.translations or {}).get(target)
        if cached:
            out[str(ra.id)] = cached
        else:
            todo.append(ra)
    todo = todo[:RATIONALE_BATCH]
    if not todo:
        return out
    try:
        result = await client.complete_json(
            purpose="rationale_translate",
            system=RATIONALE_SYSTEM,
            user=json.dumps(
                {"items": [{"id": str(ra.id), "text": ra.rationale} for ra in todo]},
                ensure_ascii=False,
            ),
            schema=_Items,
            max_tokens=2000,
            timeout=45.0,
        )
        if _MIXED_EN.search(result.value.model_dump_json()):
            raise LLMOutputInvalid("rationale_translate: English output mixed with Indonesian")
    except LLMError as exc:
        log.warning("rationale_translate_unavailable error=%s", type(exc).__name__)
        return out
    got = {item.id: item.text for item in result.value.items}
    for ra in todo:
        text = got.get(str(ra.id))
        if text:
            ra.translations = {**(ra.translations or {}), target: text}
            out[str(ra.id)] = text
    db.commit()
    return out
