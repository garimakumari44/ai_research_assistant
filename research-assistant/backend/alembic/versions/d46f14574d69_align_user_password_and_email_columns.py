"""align user password and email columns

Revision ID: d46f14574d69
Revises: 81381597329e
Create Date: 2026-08-16

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d46f14574d69"

down_revision: Union[str, Sequence[str], None] = "81381597329e"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Align the users table with the current User SQLAlchemy model.

    Current SQLAlchemy model expects:

        email            VARCHAR(255)
        hashed_password  VARCHAR(255)

    The previous migration created:

        email            VARCHAR(320)
        password_hash    VARCHAR(255)

    Therefore:
        password_hash -> hashed_password
        email VARCHAR(320) -> VARCHAR(255)
    """

    # ------------------------------------------------------------------
    # Rename password_hash -> hashed_password
    # ------------------------------------------------------------------
    op.alter_column(
        "users",
        "password_hash",
        new_column_name="hashed_password",
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )

    # ------------------------------------------------------------------
    # Align email length with SQLAlchemy model
    # ------------------------------------------------------------------
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=320),
        type_=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade() -> None:
    """
    Restore the previous users schema.
    """

    # ------------------------------------------------------------------
    # Restore email length
    # ------------------------------------------------------------------
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        type_=sa.String(length=320),
        existing_nullable=False,
    )

    # ------------------------------------------------------------------
    # Rename hashed_password -> password_hash
    # ------------------------------------------------------------------
    op.alter_column(
        "users",
        "hashed_password",
        new_column_name="password_hash",
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )
