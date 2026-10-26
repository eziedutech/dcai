"""Citizenship Coach output (spec section 8.3)."""

import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.text import CoachText, sentence_count


def _max_two_sentences(text: str) -> str:
    if sentence_count(text) > 2:
        raise ValueError("child_nudge must be at most two sentences")
    return text


# Tone rules (spec 8.3): never blame the child, never tell a parent to punish.
_BLAME = re.compile(
    # "bukan salahmu" / "not your fault" comfort the child, so the negated form is allowed.
    r"(?<!bukan )\b(?:salahmu|salah kamu)\b|\b(?:kamu salah|kamu bodoh|ceroboh)\b"
    r"|(?<!not )\byour fault\b|\byou should have known\b",
    re.I,
)
_PUNISH = re.compile(
    r"\b(hukum\w*|sita\w*|menyita|larang\w*|marahi\w*|punish\w*|take away (the|their) phone|ban)\b",
    re.I,
)


def _no_blame(text: str) -> str:
    if _BLAME.search(text):
        raise ValueError("child text must not blame the child")
    return text


def _no_punishment(text: str) -> str:
    if _PUNISH.search(text):
        raise ValueError("advice must not tell a parent to punish or forbid")
    return text


Line = Annotated[CoachText, StringConstraints(max_length=240)]
# Starters and the "do" list are what a parent acts on: no punishment there. The "dont" list
# may name punishment, because that is where "do not punish" belongs.
ActLine = Annotated[Line, AfterValidator(_no_punishment)]


class ParentInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    what_we_see: Annotated[CoachText, StringConstraints(max_length=400)]
    why_it_matters: Annotated[CoachText, StringConstraints(max_length=400)]
    conversation_starters: list[ActLine] = Field(min_length=3, max_length=3)
    do: list[ActLine] = Field(min_length=1, max_length=4)
    dont: list[Line] = Field(min_length=1, max_length=4)


class MicroLesson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[CoachText, StringConstraints(max_length=80)]
    body: Annotated[CoachText, StringConstraints(max_length=600), AfterValidator(_no_blame)]


class CoachOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    child_nudge: Annotated[
        CoachText,
        StringConstraints(max_length=280),
        AfterValidator(_max_two_sentences),
        AfterValidator(_no_blame),
    ]
    parent_insight: ParentInsight
    # Required but nullable, so strict JSON schema modes accept it.
    micro_lesson: MicroLesson | None
