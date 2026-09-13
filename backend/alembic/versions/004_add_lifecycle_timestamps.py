"""add lifecycle timestamps

Revision ID: 004_add_lifecycle_timestamps
Revises: 003_add_donation_acceptance_fields
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_add_lifecycle_timestamps"
down_revision: str | None = "003_add_donation_acceptance_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("donations") as batch_op:
        batch_op.add_column(sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("distributed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("donations") as batch_op:
        batch_op.drop_column("distributed_at")
        batch_op.drop_column("collected_at")
