"""Add secure_config table

Revision ID: 20250209_01_secure_config
Revises: 20250925_04_abuse_flags
Create Date: 2025-02-09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20250209_01_secure_config"
down_revision: str | None = "20250925_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "secure_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("encrypted_value", sa.String(500), nullable=False),
        sa.Column("set_by", sa.String(255), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("secure_config")
