"""Add donation_ledger table for tracking cumulative donations.

Revision ID: 20260212_01_donation_ledger
Revises: 20250209_01_secure_config
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260212_01_donation_ledger"
down_revision: str | None = "20250209_01_secure_config"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "donation_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("amount_ban", sa.Numeric(18, 8), nullable=False),
        sa.Column("blocks_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(32), nullable=False, server_default="receive"),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("donation_ledger")
