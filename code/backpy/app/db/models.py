"""Tables (spec section 9).

No table has a column for raw conversation text. The privacy claim "parents receive
insight, not conversations" is enforced by this schema, and a test fails if a text-like
column appears. The only excerpt storage is evidence_excerpt: encrypted, for `mendesak`
only, with an expiry.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Index, Integer, LargeBinary, String, Uuid
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


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[uuid.UUID] = _id()
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
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


class AuditLog(Base):
    """Who did what. Kept after a child's data is erased, so it holds ids, never names."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = _id()
    actor: Mapped[str] = mapped_column(String(60), nullable=False)  # guardian:<id> | system
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    target: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = _created()
