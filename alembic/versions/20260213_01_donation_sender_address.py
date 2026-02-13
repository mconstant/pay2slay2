"""Add sender_address column to donation_ledger.

Revision ID: 20260213_01_donation_sender
Revises: 20260212_01_donation_ledger
Create Date: 2026-02-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260213_01_donation_sender"
down_revision: str | None = "20260212_01_donation_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("donation_ledger", sa.Column("sender_address", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("donation_ledger", "sender_address")
