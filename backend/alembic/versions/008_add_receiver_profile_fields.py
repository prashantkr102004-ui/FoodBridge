"""add receiver profile fields

Revision ID: 008_add_receiver_profile_fields
Revises: 007_create_notifications_table
Create Date: 2026-09-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_add_receiver_profile_fields"
down_revision: str | None = "007_create_notifications_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("receiver_type", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("receiver_focus", sa.String(length=150), nullable=True))
    op.add_column("users", sa.Column("profile_image_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "profile_image_url")
    op.drop_column("users", "receiver_focus")
    op.drop_column("users", "receiver_type")
