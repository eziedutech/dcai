"""Synthetic conversation scenarios (spec section 11). Every file in data/scenarios must
pass this schema; `python -m app.scenarios.validate` checks them all."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.risk.schemas import Level, Pattern


class Group(StrEnum):
    WAJAR = "wajar"  # ordinary chat: measures false alarms
    KASUS_SULIT = "kasus_sulit"  # looks similar but is benign: tests caution
    PERUNDUNGAN = "perundungan"  # peer bullying
    DATA_PRIBADI = "data_pribadi"  # the child shares personal data
    PENDEKATAN_BERISIKO = "pendekatan_berisiko"  # staged risky approach by a stranger
    MENYAKITI_DIRI = "menyakiti_diri"  # non-explicit self-harm topic: support response
    KENAKALAN = "kenakalan"  # invitations to fights, drugs, alcohol or weapons


class ChildLabel(StrEnum):
    """Labels for messages the child writes, or peer behaviour that is not grooming."""

    PERUNDUNGAN = "perundungan"
    KATA_KASAR = "kata_kasar"
    BERBAGI_DATA_PRIBADI = "berbagi_data_pribadi"
    MENYAKITI_DIRI = "menyakiti_diri"
    # Invites or pushes someone toward a fight (tawuran), drugs, illegal pills, alcohol or
    # carrying a sharp weapon. Either side: a child can also invite others.
    AJAKAN_BERBAHAYA = "ajakan_berbahaya"


Label = Pattern | ChildLabel


class Sender(StrEnum):
    CHILD = "child"
    CONTACT = "contact"


class Channel(StrEnum):
    GAME_CHAT = "game_chat"
    DM = "dm"
    GRUP_SEKOLAH = "grup_sekolah"
    KELUARGA = "keluarga"


class ContactRole(StrEnum):
    TEMAN_SEKOLAH = "teman_sekolah"
    KELUARGA = "keluarga"
    KAKAK = "kakak"
    GURU = "guru"
    PELATIH = "pelatih"
    TEMAN_ONLINE_LAMA = "teman_online_lama"
    TAK_DIKENAL = "tak_dikenal"


class AgeRange(StrEnum):
    A8_10 = "8-10"
    A11_13 = "11-13"
    A14_17 = "14-17"


class Language(StrEnum):
    ID = "id"
    EN = "en"
    CAMPUR = "campur"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sender: Sender = Field(alias="from")
    text: Annotated[str, StringConstraints(min_length=1, max_length=280)]
    labels: list[Label] = Field(default_factory=list, max_length=4)


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ReviewStatus = ReviewStatus.DRAFT
    reviewer: str | None = None
    reviewed_at: str | None = None
    note: str | None = None


# Expected levels per group (spec section 11 table).
_GROUP_LEVELS: dict[Group, set[Level]] = {
    Group.WAJAR: {Level.AMAN},
    Group.KASUS_SULIT: {Level.AMAN, Level.PERHATIAN},
    Group.PERUNDUNGAN: {Level.PERHATIAN, Level.WASPADA},
    Group.DATA_PRIBADI: {Level.PERHATIAN},
    Group.PENDEKATAN_BERISIKO: {Level.WASPADA, Level.MENDESAK},
    Group.MENYAKITI_DIRI: {Level.AMAN, Level.PERHATIAN, Level.WASPADA, Level.MENDESAK},
    Group.KENAKALAN: {Level.WASPADA, Level.MENDESAK},
}


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: Annotated[str, StringConstraints(pattern=r"^[a-z_]+-\d{3}$")]
    group: Group
    title: Annotated[str, StringConstraints(min_length=3, max_length=100)]
    channel: Channel
    contact_role: ContactRole
    child_age_range: AgeRange
    language: Language
    expected_final_level: Level
    # 1-based index of the message where risk should start rising; None if it never should.
    risk_starts_at: int | None = Field(ge=1)
    expects_support_response: bool = False
    messages: list[Message] = Field(min_length=8, max_length=15)
    notes: Annotated[str, StringConstraints(max_length=400)] = ""
    synthetic: bool = True
    review: Review = Field(default_factory=Review)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if not self.synthetic:
            raise ValueError("only synthetic scenarios are allowed")
        if not self.id.startswith(f"{self.group.value}-"):
            raise ValueError("id must start with the group name")
        if self.expected_final_level not in _GROUP_LEVELS[self.group]:
            raise ValueError(f"level {self.expected_final_level} not expected for {self.group}")
        if self.risk_starts_at is not None and self.risk_starts_at > len(self.messages):
            raise ValueError("risk_starts_at is past the last message")
        risky = self.expected_final_level != Level.AMAN
        if risky and self.risk_starts_at is None:
            raise ValueError("a risky scenario needs risk_starts_at")
        if self.group == Group.WAJAR and self.risk_starts_at is not None:
            raise ValueError("ordinary chat has no risk start")
        if (self.group == Group.MENYAKITI_DIRI) != self.expects_support_response:
            raise ValueError("expects_support_response is true exactly for menyakiti_diri")
        if self.group == Group.PENDEKATAN_BERISIKO and self.contact_role != ContactRole.TAK_DIKENAL:
            raise ValueError("risky approach scenarios come from an unknown contact")
        labelled = [m for m in self.messages if m.labels]
        if self.group == Group.WAJAR and labelled:
            raise ValueError("ordinary chat messages carry no labels")
        if self.group != Group.WAJAR and self.group != Group.KASUS_SULIT and not labelled:
            raise ValueError("risky groups need at least one labelled message")
        return self
