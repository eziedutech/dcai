"""Time online settings a parent sets for a child, and the defaults per age range.

The phone enforces them; the server stores them and sends them in the device config.
Defaults are dcAI's starting points for a family to adjust, not health guidance.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Category = Literal["video", "game", "sosial", "lain"]
CATEGORIES: tuple[str, ...] = ("video", "game", "sosial", "lain")

Clock = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
PackageName = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$", max_length=100)
]
Minutes = Annotated[int, Field(ge=0, le=1440)]


class Bedtime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    start: Clock = "21:00"
    end: Clock = "05:30"


class Session(BaseModel):
    """Breaks from endless short video and feeds, by continuous minutes in one app."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    nudge_minutes: Annotated[int, Field(ge=5, le=180)] = 20
    limit_minutes: Annotated[int, Field(ge=10, le=240)] = 40
    break_minutes: Annotated[int, Field(ge=1, le=60)] = 5

    @model_validator(mode="after")
    def _nudge_before_limit(self) -> Session:
        if self.nudge_minutes >= self.limit_minutes:
            raise ValueError("nudge_minutes must be below limit_minutes")
        return self


class ScreenPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    # 1 = Monday ... 7 = Sunday.
    school_days: list[Annotated[int, Field(ge=1, le=7)]] = Field(
        default_factory=lambda: [1, 2, 3, 4, 5], max_length=7
    )
    # None means no daily limit.
    daily_limit_school: Minutes | None = 150
    daily_limit_weekend: Minutes | None = 210
    category_limits: dict[Category, Minutes | None] = Field(
        default_factory=lambda: {"video": 60, "game": 60, "sosial": 60, "lain": None}
    )
    bedtime_school: Bedtime = Field(default_factory=Bedtime)
    bedtime_weekend: Bedtime = Field(default_factory=lambda: Bedtime(start="22:00", end="06:30"))
    wind_down_minutes: Annotated[int, Field(ge=0, le=60)] = 15
    session: Session = Field(default_factory=Session)
    # Always open, also at bedtime and after a limit (study, maps, calls to parents).
    always_allowed: list[PackageName] = Field(default_factory=list, max_length=30)


def defaults_for_age(age_range: str) -> ScreenPolicy:
    """dcAI's starting settings per age range, for the parent to adjust."""
    if age_range == "10-12":
        return ScreenPolicy(
            daily_limit_school=120,
            daily_limit_weekend=180,
            category_limits={"video": 45, "game": 45, "sosial": 30, "lain": None},
            bedtime_school=Bedtime(start="20:30", end="05:30"),
            bedtime_weekend=Bedtime(start="21:30", end="06:30"),
            session=Session(nudge_minutes=15, limit_minutes=30, break_minutes=5),
        )
    if age_range == "16-17":
        return ScreenPolicy(
            daily_limit_school=180,
            daily_limit_weekend=240,
            category_limits={"video": 90, "game": 90, "sosial": 90, "lain": None},
            bedtime_school=Bedtime(start="22:30", end="05:30"),
            bedtime_weekend=Bedtime(start="23:00", end="07:00"),
            session=Session(nudge_minutes=25, limit_minutes=50, break_minutes=5),
        )
    return ScreenPolicy(
        bedtime_school=Bedtime(start="21:30", end="05:30"),
        bedtime_weekend=Bedtime(start="22:30", end="06:30"),
    )


_HHMM = re.compile(r"^(\d\d):(\d\d)$")


def to_minutes(clock: str) -> int:
    m = _HHMM.match(clock)
    assert m
    return int(m.group(1)) * 60 + int(m.group(2))
