"""Citizenship Coach output (spec section 8.3)."""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.text import CoachText, sentence_count


def _max_two_sentences(text: str) -> str:
    if sentence_count(text) > 2:
        raise ValueError("child_nudge must be at most two sentences")
    return text


Line = Annotated[CoachText, StringConstraints(max_length=240)]


class ParentInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    what_we_see: Annotated[CoachText, StringConstraints(max_length=400)]
    why_it_matters: Annotated[CoachText, StringConstraints(max_length=400)]
    conversation_starters: list[Line] = Field(min_length=3, max_length=3)
    do: list[Line] = Field(min_length=1, max_length=4)
    dont: list[Line] = Field(min_length=1, max_length=4)


class MicroLesson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[CoachText, StringConstraints(max_length=80)]
    body: Annotated[CoachText, StringConstraints(max_length=600)]


class CoachOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    child_nudge: Annotated[
        CoachText, StringConstraints(max_length=280), AfterValidator(_max_two_sentences)
    ]
    parent_insight: ParentInsight
    # Required but nullable, so strict JSON schema modes accept it.
    micro_lesson: MicroLesson | None
