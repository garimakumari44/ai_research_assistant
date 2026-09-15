"""remove organization and add user full name

Revision ID: aba4b7d2a99d
Revises: d46f14574d69
Create Date: 2026-08-16 12:08:23.713571

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ----------------------------------------------------------------------
# Revision identifiers
# ----------------------------------------------------------------------

revision: str = "aba4b7d2a99d"
down_revision: Union[str, Sequence[str], None] = "d46f14574d69"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ----------------------------------------------------------------------
# Upgrade
# ----------------------------------------------------------------------

def upgrade() -> None:
    """Upgrade database schema."""

    # --------------------------------------------------------------
    # 1. Add full_name to users
    # --------------------------------------------------------------

    op.add_column(
        "users",
        sa.Column(
            "full_name",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # --------------------------------------------------------------
    # 2. Remove the foreign key from users
    #
    # This MUST happen before dropping the organizations table.
    # --------------------------------------------------------------

    op.drop_constraint(
        "users_organization_id_fkey",
        "users",
        type_="foreignkey",
    )

    # --------------------------------------------------------------
    # 3. Remove the organization_id index
    # --------------------------------------------------------------

    op.drop_index(
        "ix_users_organization_id",
        table_name="users",
    )

    # --------------------------------------------------------------
    # 4. Remove organization_id from users
    # --------------------------------------------------------------

    op.drop_column(
        "users",
        "organization_id",
    )

    # --------------------------------------------------------------
    # 5. Remove organizations table
    # --------------------------------------------------------------

    op.drop_index(
        "ix_organizations_id",
        table_name="organizations",
    )

    op.drop_table(
        "organizations",
    )


# ----------------------------------------------------------------------
# Downgrade
# ----------------------------------------------------------------------

def downgrade() -> None:
    """Downgrade database schema."""

    # --------------------------------------------------------------
    # 1. Recreate organizations table
    # --------------------------------------------------------------

    op.create_table(
        "organizations",
        sa.Column(
            "id",
            sa.INTEGER(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="organizations_pkey",
        ),
        sa.UniqueConstraint(
            "name",
            name="organizations_name_key",
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
    )

    # --------------------------------------------------------------
    # 2. Recreate organizations index
    # --------------------------------------------------------------

    op.create_index(
        "ix_organizations_id",
        "organizations",
        ["id"],
        unique=False,
    )

    # --------------------------------------------------------------
    # 3. Recreate users.organization_id
    #
    # NOTE:
    # This column is NOT nullable because that was the original
    # schema definition.
    # --------------------------------------------------------------

    op.add_column(
        "users",
        sa.Column(
            "organization_id",
            sa.INTEGER(),
            autoincrement=False,
            nullable=False,
        ),
    )

    # --------------------------------------------------------------
    # 4. Recreate foreign key
    # --------------------------------------------------------------

    op.create_foreign_key(
        "users_organization_id_fkey",
        "users",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # --------------------------------------------------------------
    # 5. Recreate users.organization_id index
    # --------------------------------------------------------------

    op.create_index(
        "ix_users_organization_id",
        "users",
        ["organization_id"],
        unique=False,
    )

    # --------------------------------------------------------------
    # 6. Remove full_name
    # --------------------------------------------------------------

    op.drop_column(
        "users",
        "full_name",
    )