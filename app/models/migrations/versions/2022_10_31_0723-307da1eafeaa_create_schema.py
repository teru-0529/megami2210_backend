"""create schema

Revision ID: 307da1eafeaa
Revises:
Create Date: 2022-10-31 07:23:04.853106

"""
import sqlalchemy as sa
from alembic import op

from app.models.segment_values import DateType


# revision identifiers, used by Alembic.
revision = "307da1eafeaa"
down_revision = None
branch_labels = None
depends_on = None


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_trigger() -> None:
    # 更新日時の設定
    op.execute(
        """
        CREATE FUNCTION set_modified_at() RETURNS TRIGGER AS $$
        BEGIN
            -- 更新日時
            NEW.modified_at := now();
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_business_date_table() -> None:
    business_date_table = op.create_table(
        "business_date",
        sa.Column(
            "date_type",
            sa.Enum(*DateType.list(), name="date_type"),
            primary_key=True,
            server_default=DateType.business_date,
            comment="日付種類",
        ),
        sa.Column("date", sa.Date, nullable=False, comment="日付"),
    )

    op.bulk_insert(
        business_date_table,
        [
            {
                "date": "2024-01-18",
            },
        ],
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    op.execute("CREATE SCHEMA selling;")
    op.execute("CREATE SCHEMA purchase;")
    op.execute("CREATE SCHEMA inventory;")
    op.execute("CREATE SCHEMA mst;")
    op.execute("CREATE SCHEMA todo;")
    op.execute("CREATE SCHEMA account;")
    create_trigger()
    create_business_date_table()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS business_date CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS set_modified_at CASCADE;")
    op.execute("DROP TYPE IF EXISTS date_type;")
    op.execute("DROP SCHEMA IF EXISTS todo CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS account CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS mst CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS inventory CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS purchase CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS selling CASCADE;")
