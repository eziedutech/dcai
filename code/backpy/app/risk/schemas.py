"""Stage 2 output: the structured risk assessment (spec section 8.1)."""

import re
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.text import ModelText


class Level(StrEnum):
    AMAN = "aman"
    PERHATIAN = "perhatian"
    WASPADA = "waspada"
    MENDESAK = "mendesak"


# Inclusive lower bounds. Initial values from the spec, to be tuned on the dev split only.
LEVEL_FLOORS: tuple[tuple[int, Level], ...] = (
    (85, Level.MENDESAK),
    (60, Level.WASPADA),
    (30, Level.PERHATIAN),
    (0, Level.AMAN),
)


_MARKER = re.compile(r"\[(TELEPON|EMAIL|KARTU|ALAMAT|AKUN|NAMA|SEKOLAH)\]")


def level_for(score: int) -> Level:
    for floor, level in LEVEL_FLOORS:
        if score >= floor:
            return level
    raise ValueError("score below 0")


class Pattern(StrEnum):
    """Behaviour categories, at pattern level, never a phrase list."""

    MEMBANGUN_KEDEKATAN = "membangun_kedekatan"  # rapport building or excessive praise
    MEMINTA_KERAHASIAAN = "meminta_kerahasiaan"
    PINDAH_KANAL = "pindah_kanal"  # moving to a private channel
    MEMINTA_DATA_PRIBADI = "meminta_data_pribadi"  # personal data or photos
    MENAWARKAN_HADIAH = "menawarkan_hadiah"
    MENGUJI_BATAS = "menguji_batas"
    MENEKAN_MENGANCAM = "menekan_mengancam"


class Confidence(StrEnum):
    RENDAH = "rendah"
    SEDANG = "sedang"
    TINGGI = "tinggi"


class TrajectoryStatus(StrEnum):
    STABIL = "stabil"
    MENINGKAT = "meningkat"


class Trajectory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TrajectoryStatus
    reason: Annotated[ModelText, StringConstraints(max_length=200)]


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_score: int = Field(ge=0, le=100)
    level: Level
    patterns_observed: list[Pattern] = Field(max_length=len(Pattern))
    trajectory: Trajectory
    rationale_for_parent: Annotated[ModelText, StringConstraints(max_length=400)]
    confidence: Confidence

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.level != level_for(self.risk_score):
            raise ValueError("level does not match risk_score band")
        if len(set(self.patterns_observed)) != len(self.patterns_observed):
            raise ValueError("patterns_observed has duplicates")
        # A masking marker in the parent text means the model quoted a message.
        if _MARKER.search(self.rationale_for_parent) or _MARKER.search(self.trajectory.reason):
            raise ValueError("parent text must not quote messages or markers")
        return self
