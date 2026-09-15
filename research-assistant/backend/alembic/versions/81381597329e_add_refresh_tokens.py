"""add refresh tokens

Revision ID: 81381597329e
Revises: bb110c1fce90
Create Date: 2026-08-15 23:21:36.751723

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "81381597329e"

down_revision: Union[str, Sequence[str], None] = "bb110c1fce90"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create refresh_tokens table."""

    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "token",
            sa.String(length=512),
            nullable=False,
        ),
        sa.Column(
            "is_revoked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_refresh_tokens_token"),
        "refresh_tokens",
        ["token"],
        unique=True,
    )


def downgrade() -> None:
    """Drop refresh_tokens table."""

    op.drop_index(
        op.f("ix_refresh_tokens_token"),
        table_name="refresh_tokens",
    )

    op.drop_table("refresh_tokens")