"""create selling tables

Revision ID: 4ed3531f2a5e
Revises: 76241be00f1b
Create Date: 2022-12-14 22:41:16.215287

"""
import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps

# revision identifiers, used by Alembic.
revision = "4ed3531f2a5e"
down_revision = "76241be00f1b"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_receivings_table() -> None:
    op.create_table(
        "receivings",
        sa.Column("receiving_no", sa.String(10), primary_key=True, comment="受注NO"),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="selling",
    )  # FIXME:

    op.execute(
        """
        CREATE TRIGGER receivings_modified
            BEFORE UPDATE
            ON selling.receivings
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 受注番号の自動採番
    op.execute(
        """
        CREATE FUNCTION selling.create_receivings() RETURNS TRIGGER AS $$
        BEGIN
            NEW.receiving_no:='RO-'||to_char(nextval('selling.receiving_no_seed'),'FM0000000');
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_receivings
            BEFORE INSERT
            ON selling.receivings
            FOR EACH ROW
        EXECUTE PROCEDURE selling.create_receivings();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    op.execute("CREATE SEQUENCE selling.receiving_no_seed START 1;")
    op.execute("CREATE SEQUENCE selling.shipping_no_seed START 1;")
    create_receivings_table()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS selling.receivings CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.receiving_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.shipping_no_seed CASCADE;")
