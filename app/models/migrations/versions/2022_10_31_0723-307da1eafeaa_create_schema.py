"""create schema

Revision ID: 307da1eafeaa
Revises:
Create Date: 2022-10-31 07:23:04.853106

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "307da1eafeaa"
down_revision = None
branch_labels = None
depends_on = None


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_updated_at_trigger() -> None:
    op.execute(
        """
        CREATE FUNCTION set_modified_at() RETURNS TRIGGER AS $$
        BEGIN
            NEW.modified_at := now();
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    op.execute("CREATE SCHEMA selling;")
    op.execute("CREATE SCHEMA purchase;")
    op.execute("CREATE SCHEMA inventory;")
    op.execute("CREATE SCHEMA mst;")
    op.execute("CREATE SCHEMA todo;")
    op.execute("CREATE SCHEMA account;")
    create_updated_at_trigger()


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS set_modified_at CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS todo CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS account CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS mst CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS inventory CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS purchase CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS selling CASCADE;")
