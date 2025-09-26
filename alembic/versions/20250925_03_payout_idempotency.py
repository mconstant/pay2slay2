"""add payout idempotency key

Revision ID: 20250925_03
Revises: 20250925_02
Create Date: 2025-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20250925_03"
down_revision: str | Sequence[str] | None = "20250925_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:  # pragma: no cover
    op.add_column("payouts", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.create_index("ix_payout_idempotency_key", "payouts", ["idempotency_key"], unique=False)


def downgrade() -> None:  # pragma: no cover
    op.drop_index("ix_payout_idempotency_key", table_name="payouts")
    op.drop_column("payouts", "idempotency_key")
