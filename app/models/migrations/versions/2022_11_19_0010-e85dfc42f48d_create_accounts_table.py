"""create accounts table

Revision ID: e85dfc42f48d
Revises: de6f035be044
Create Date: 2022-11-19 00:10:53.096333

"""
from alembic import op
import sqlalchemy as sa

from app.models.migrations.util import timestamps
from app.models.segment_values import AccountTypes


# revision identifiers, used by Alembic.
revision = "e85dfc42f48d"
down_revision = "de6f035be044"
branch_labels = None
depends_on = None


def create_profiles_table() -> None:
    profiles_table = op.create_table(
        "profiles",
        sa.Column("account_id", sa.String(5), primary_key=True, comment="アカウントID"),
        sa.Column(
            "user_name",
            sa.String(20),
            unique=True,
            nullable=False,
            index=True,
            comment="氏名",
        ),
        sa.Column(
            "nickname",
            sa.String(20),
            unique=True,
            nullable=False,
            index=True,
            comment="ニックネーム",
        ),
        *timestamps(),
        schema="account",
    )
    op.execute(
        """
        CREATE TRIGGER profiles_modified
            BEFORE UPDATE
            ON account.profiles
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    op.bulk_insert(
        profiles_table,
        [
            {"account_id": "T-001", "user_name": "佐藤晃章", "nickname": "てるあき"},
            {"account_id": "T-002", "user_name": "佐藤陽子", "nickname": "ようこ"},
            {"account_id": "T-003", "user_name": "佐藤拓弥", "nickname": "たくみ"},
        ],
    )


def create_authes_table() -> None:
    authes_table = op.create_table(
        "authes",
        sa.Column("account_id", sa.String(5), primary_key=True, comment="アカウントID"),
        sa.Column(
            "email", sa.Text, unique=True, nullable=False, index=True, comment="メールアドレス"
        ),
        sa.Column(
            "verified_email",
            sa.Boolean,
            nullable=False,
            server_default="False",
            comment="メール送達確認済み",
        ),
        sa.Column("solt", sa.Text, nullable=False, comment="ソルト"),
        sa.Column("password", sa.Text, nullable=False, comment="パスワード(HASH済)"),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="False",
            comment="初期パスワード変更済み",
        ),
        sa.Column(
            "accopunt_type",
            sa.Enum(*AccountTypes.list(), name="accopunt_type", schema="account"),
            nullable=False,
            server_default=AccountTypes.general,
            index=True,
            comment="アカウント種別",
        ),
        *timestamps(),
        schema="account",
    )
    op.execute(
        """
        CREATE TRIGGER authes_modified
            BEFORE UPDATE
            ON account.authes
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    op.create_foreign_key(
        "fk_account_id",
        "authes",
        "profiles",
        ["account_id"],
        ["account_id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
        source_schema="account",
        referent_schema="account",
    )

    op.bulk_insert(
        authes_table,
        [
            {
                "account_id": "T-001",
                "email": "teruaki@sato.com",
                "verified_email": True,
                "solt": "100",
                "password": "password",
                "is_active": True,
                "accopunt_type": AccountTypes.administrator,
            },
            {
                "account_id": "T-002",
                "email": "yoko@sato.com",
                "verified_email": False,
                "solt": "100",
                "password": "password",
                "is_active": True,
                "accopunt_type": AccountTypes.general,
            },
            {
                "account_id": "T-003",
                "email": "takumi@sato.com",
                "verified_email": False,
                "solt": "100",
                "password": "password",
                "is_active": True,
                "accopunt_type": AccountTypes.general,
            },
        ],
    )


def create_watch_tasks_table() -> None:
    op.create_table(
        "watch_tasks",
        sa.Column("account_id", sa.String(5), primary_key=True, comment="アカウントID"),
        sa.Column("task_id", sa.Integer, primary_key=True, index=True, comment="タスクID"),
        sa.Column(
            "note",
            sa.Text,
            nullable=True,
            comment="ノート",
        ),
        *timestamps(),
        schema="account",
    )
    op.execute(
        """
        CREATE TRIGGER watch_tasks_modified
            BEFORE UPDATE
            ON account.watch_tasks
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    op.create_foreign_key(
        "fk_account_id",
        "watch_tasks",
        "profiles",
        ["account_id"],
        ["account_id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
        source_schema="account",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_task_id",
        "watch_tasks",
        "tasks",
        ["task_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
        source_schema="account",
        referent_schema="todo",
    )


def upgrade() -> None:
    create_profiles_table()
    create_authes_table()
    create_watch_tasks_table()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS account.watch_tasks CASCADE;")
    op.execute("DROP TABLE IF EXISTS account.authes CASCADE;")
    op.execute("DROP TABLE IF EXISTS account.profiles CASCADE;")
    # op.drop_table("watch_tasks", schema="account")
    # op.drop_table("authes", schema="account")
    # op.drop_table("profiles", schema="account")
    op.execute("DROP TYPE IF EXISTS account.accopunt_type;")
