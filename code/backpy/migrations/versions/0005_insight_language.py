"""insight language and translations, assessment rationale translations

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-29 14:10:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("insight", schema=None) as batch_op:
        batch_op.add_column(sa.Column("language", sa.String(length=2), nullable=True))
        batch_op.add_column(sa.Column("translations", sa.JSON(), nullable=True))
    with op.batch_alter_table("risk_assessment", schema=None) as batch_op:
        batch_op.add_column(sa.Column("translations", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("risk_assessment", schema=None) as batch_op:
        batch_op.drop_column("translations")
    with op.batch_alter_table("insight", schema=None) as batch_op:
        batch_op.drop_column("translations")
        batch_op.drop_column("language")
