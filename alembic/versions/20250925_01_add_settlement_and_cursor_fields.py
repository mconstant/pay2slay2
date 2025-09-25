"""add settlement cursor and payout retry fields

Revision ID: 20250925_01
Revises: 7e240cba5ed4
Create Date: 2025-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20250925_01"
down_revision: str | Sequence[str] | None = "7e240cba5ed4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Users table additions
    op.add_column(
        "users",
        sa.Column("last_settled_kill_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("users", sa.Column("last_settlement_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("region_code", sa.String(length=8), nullable=True))
    op.add_column("users", sa.Column("abuse_flags", sa.String(length=500), nullable=True))
    # RewardAccrual unique constraint
    op.create_unique_constraint(
        "uq_accrual_user_epoch", "reward_accruals", ["user_id", "epoch_minute"]
    )
    # Payout retry/audit columns
    op.add_column(
        "payouts", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column("payouts", sa.Column("first_attempt_at", sa.DateTime(), nullable=True))
    op.add_column("payouts", sa.Column("last_attempt_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("payouts", "last_attempt_at")
    op.drop_column("payouts", "first_attempt_at")
    op.drop_column("payouts", "attempt_count")
    op.drop_constraint("uq_accrual_user_epoch", "reward_accruals", type_="unique")
    op.drop_column("users", "abuse_flags")
    op.drop_column("users", "region_code")
    op.drop_column("users", "last_settlement_at")
    op.drop_column("users", "last_settled_kill_count")
