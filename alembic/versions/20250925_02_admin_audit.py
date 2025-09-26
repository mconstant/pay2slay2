"""add admin audit table

Revision ID: 20250925_02
Revises: 20250925_01
Create Date: 2025-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20250925_02"
down_revision: str | Sequence[str] | None = "20250925_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:  # pragma: no cover - migration
    op.create_table(
        "admin_audit",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("action", sa.String(length=64), nullable=False, index=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True, index=True),
        sa.Column("target_type", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.String(length=200), nullable=True),
        sa.Column("detail", sa.String(length=2000), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )
    op.create_index("ix_admin_audit_action_created", "admin_audit", ["action", "created_at"])


def downgrade() -> None:  # pragma: no cover - migration
    op.drop_index("ix_admin_audit_action_created", table_name="admin_audit")
    op.drop_table("admin_audit")
