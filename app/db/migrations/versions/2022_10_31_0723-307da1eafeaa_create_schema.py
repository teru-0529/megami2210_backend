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


def upgrade() -> None:
    op.execute("CREATE SCHEMA todo;")
    create_updated_at_trigger()


def downgrade() -> None:
    op.execute("DROP FUNCTION set_modified_at;")
    op.execute("DROP SCHEMA todo;")
