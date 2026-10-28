"""Tables (spec section 9).

No table has a column for raw conversation text. The privacy claim "parents receive
insight, not conversations" is enforced by this schema, and a test fails if a text-like
column appears. The only excerpt storage is evidence_excerpt: encrypted, for `mendesak`
only, with an expiry.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Date,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime, utcnow


def _id() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def _created() -> Mapped[datetime]:
    return mapped_column(UTCDateTime, default=utcnow, nullable=False)


class Guardian(Base):
    __tablename__ = "guardian"

    id: Mapped[uuid.UUID] = _id()
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="id")
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = _created()

    children: Mapped[list[ChildProfile]] = relationship(
        back_populates="guardian", cascade="all, delete-orphan", passive_deletes=True
    )


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id: Mapped[uuid.UUID] = _id()
    guardian_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("guardian.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SHA-256 of the token; the token itself is never stored.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = _created()


class ChildProfile(Base):
    __tablename__ = "child_profile"

    id: Mapped[uuid.UUID] = _id()
    guardian_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("guardian.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nickname: Mapped[str] = mapped_column(String(40), nullable=False)
    # A range, never a full date of birth.
    age_range: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = _created()

    guardian: Mapped[Guardian] = relationship(back_populates="children")


class ConsentRecord(Base):
    """Append-only. A database trigger refuses UPDATE (migration 0001). Withdrawal is a new
    row with action=revoke. Rows go only when the child's data is erased."""

    __tablename__ = "consent_record"

    id: Mapped[uuid.UUID] = _id()
    guardian_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("guardian.id", ondelete="CASCADE"), nullable=False
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text_version: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(8), nullable=False)  # grant | revoke
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    age_range: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = _created()


class PairingCode(Base):
    """A short code the guardian reads off the dashboard and types on the child's phone.
    Stored as a hash, single use, expires in minutes."""

    __tablename__ = "pairing_code"

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = _created()


class Device(Base):
    """The child's phone running dcAI Guardian. Authenticates with an opaque token stored
    only as a SHA-256 hash; revoking or erasing the child ends it."""

    __tablename__ = "device"

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    platform: Mapped[str] = mapped_column(String(10), nullable=False)
    app_version: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # Last reported state of each protection service, e.g. {"accessibility": true}.
    services: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    paired_at: Mapped[datetime] = _created()
    last_seen_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class Conversation(Base):
    __tablename__ = "conversation"
    __table_args__ = (
        UniqueConstraint("device_id", "thread_key", name="uq_conversation_device_thread"),
    )

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    # Set for conversations reported by a phone. thread_key is an opaque hash made on the
    # phone (the chat title never leaves it); app is the package name, e.g. com.whatsapp.
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("device.id", ondelete="SET NULL", name="fk_conversation_device_id")
    )
    thread_key: Mapped[str | None] = mapped_column(String(64))
    app: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime] = _created()


class RiskAssessment(Base):
    __tablename__ = "risk_assessment"

    id: Mapped[uuid.UUID] = _id()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    patterns: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    trajectory: Mapped[str] = mapped_column(String(10), nullable=False)
    # Model-written explanation of the pattern, schema-forbidden from quoting messages.
    rationale: Mapped[str] = mapped_column(String(400), nullable=False)
    confidence: Mapped[str] = mapped_column(String(8), nullable=False)
    # Which model (or "rules") produced it; never a hardcoded version in code.
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = _created()


class Event(Base):
    __tablename__ = "event"
    __table_args__ = (Index("ix_event_child_created", "child_id", "created_at"),)

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(40), nullable=False)  # e.g. data_pribadi_dicegah
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = _created()


class Insight(Base):
    __tablename__ = "insight"

    id: Mapped[uuid.UUID] = _id()
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risk_assessment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    child_nudge: Mapped[str] = mapped_column(String(280), nullable=False)
    parent_insight: Mapped[dict] = mapped_column(JSON, nullable=False)
    micro_lesson: Mapped[dict | None] = mapped_column(JSON)
    # approach | bullied | bullying | shared_data | distress | general
    situation: Mapped[str | None] = mapped_column(String(12))
    source: Mapped[str | None] = mapped_column(String(8))  # model | template
    created_at: Mapped[datetime] = _created()


class EvidenceExcerpt(Base):
    __tablename__ = "evidence_excerpt"

    id: Mapped[uuid.UUID] = _id()
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risk_assessment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Masked excerpt, encrypted with EVIDENCE_ENC_KEY. Only for level mendesak.
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = _created()


class ImageSignal(Base):
    """The label of an image judged on the phone (or later in the cloud). Never pixels."""

    __tablename__ = "image_signal"
    __table_args__ = (Index("ix_image_signal_child_created", "child_id", "created_at"),)

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("device.id", ondelete="SET NULL")
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversation.id", ondelete="SET NULL")
    )
    trigger: Mapped[str] = mapped_column(String(12), nullable=False)
    sender: Mapped[str | None] = mapped_column(String(8))
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(12), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = _created()


class DetectionFeedback(Base):
    """A detection a parent confirmed as wrong, on the child's phone. Only the signal
    (kind, category, score, model version) arrives: no image, no text, and no child or
    device id, so it serves model improvement without being about a person."""

    __tablename__ = "detection_feedback"

    id: Mapped[uuid.UUID] = _id()
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = _created()


class ScreenPolicyRow(Base):
    """The parent's time settings for one child: limits, bedtime, short-video breaks."""

    __tablename__ = "screen_policy"

    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), primary_key=True
    )
    policy: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = _created()


class UsageDay(Base):
    """Minutes per app category for one day on one phone, counted on the phone. No app
    names, no timeline: only totals, minutes during bedtime and the longest session."""

    __tablename__ = "usage_day"
    __table_args__ = (UniqueConstraint("device_id", "day", name="uq_usage_day_device_day"),)

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("device.id", ondelete="CASCADE"), nullable=False
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    # {"video": 42, "game": 30, "sosial": 18, "lain": 25}
    minutes: Mapped[dict] = mapped_column(JSON, nullable=False)
    bedtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_session: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    session_limits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = _created()


class TimeRequest(Base):
    """A child asking for more time. The reason is the child's note to the parent, masked
    on the phone and again here, at most 200 characters."""

    __tablename__ = "time_request"
    __table_args__ = (Index("ix_time_request_child_created", "child_id", "created_at"),)

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("device.id", ondelete="SET NULL")
    )
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # menunggu | diizinkan | ditolak | kedaluwarsa
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="menunggu")
    granted_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    advice: Mapped[dict | None] = mapped_column(JSON)
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = _created()


class FamilyDigest(Base):
    """The weekly summary for a parent, written from aggregates only."""

    __tablename__ = "family_digest"

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    output: Mapped[dict] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = _created()


class AuditLog(Base):
    """Who did what. Kept after a child's data is erased, so it holds ids, never names."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = _id()
    actor: Mapped[str] = mapped_column(String(60), nullable=False)  # guardian:<id> | system
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    target: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = _created()
