"""create donations table

Revision ID: 002_create_donations_table
Revises: 001_create_users_table
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_create_donations_table"
down_revision: str | None = "001_create_users_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "donations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("donor_id", sa.String(length=36), nullable=False),
        sa.Column("food_name", sa.String(length=120), nullable=False),
        sa.Column("food_type", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("quantity_unit", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prepared_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pickup_address", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["donor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_donations_donor_id"), "donations", ["donor_id"], unique=False)
    op.create_index(op.f("ix_donations_status"), "donations", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_donations_status"), table_name="donations")
    op.drop_index(op.f("ix_donations_donor_id"), table_name="donations")
    op.drop_table("donations")
