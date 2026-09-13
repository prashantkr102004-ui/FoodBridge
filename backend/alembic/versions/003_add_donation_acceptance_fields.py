"""add donation acceptance fields

Revision ID: 003_add_donation_acceptance_fields
Revises: 002_create_donations_table
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_add_donation_acceptance_fields"
down_revision: str | None = "002_create_donations_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("donations") as batch_op:
        batch_op.add_column(sa.Column("accepted_by_user_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_donations_accepted_by_user_id"),
            ["accepted_by_user_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_donations_accepted_by_user_id_users",
            "users",
            ["accepted_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("donations") as batch_op:
        batch_op.drop_constraint("fk_donations_accepted_by_user_id_users", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_donations_accepted_by_user_id"))
        batch_op.drop_column("accepted_at")
        batch_op.drop_column("accepted_by_user_id")
