"""school module: aggregate dashboard tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-30 14:30:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "school",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "school_staff",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("password_hash", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["school.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_school_staff_school_id", "school_staff", ["school_id"])
    op.create_table(
        "classroom",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("join_code_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["school.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("join_code_hash"),
    )
    op.create_index("ix_classroom_school_id", "classroom", ["school_id"])
    op.create_table(
        "class_membership",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("classroom_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classroom.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_id"], ["child_profile.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classroom_id", "child_id", name="uq_class_membership"),
    )
    op.create_index("ix_class_membership_classroom_id", "class_membership", ["classroom_id"])
    op.create_index("ix_class_membership_child_id", "class_membership", ["child_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("class_membership")
    op.drop_table("classroom")
    op.drop_table("school_staff")
    op.drop_table("school")
