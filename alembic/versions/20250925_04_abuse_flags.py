"""abuse flags table

Revision ID: 20250925_04
Revises: 20250925_03
Create Date: 2025-09-25
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250925_04"
down_revision = "20250925_03"
branch_labels = None
depends_on = None


def upgrade() -> None:  # pragma: no cover
    op.create_table(
        "abuse_flags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
        ),
        sa.Column("flag_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column("detail", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_abuse_user_created", "abuse_flags", ["user_id", "created_at"])


def downgrade() -> None:  # pragma: no cover
    op.drop_index("ix_abuse_user_created", table_name="abuse_flags")
    op.drop_table("abuse_flags")
