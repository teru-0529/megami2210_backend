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

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


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
            nullable=True,
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
            {"account_id": "T-901", "user_name": "西郷隆盛", "nickname": None},
            {"account_id": "T-902", "user_name": "木戸孝允", "nickname": "桂小五郎"},
            {"account_id": "T-903", "user_name": "大久保利通", "nickname": None},
        ],
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


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
            "account_type",
            sa.Enum(*AccountTypes.list(), name="account_type", schema="account"),
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
                "account_id": "T-901",
                "email": "saigo@bakumatsu.com",
                "verified_email": True,
                "solt": "100",
                "password": "password",
                "is_active": True,
                "account_type": AccountTypes.administrator,
            },
            {
                "account_id": "T-902",
                "email": "kido@bakumatsu.com",
                "verified_email": False,
                "solt": "100",
                "password": "password",
                "is_active": True,
                "account_type": AccountTypes.general,
            },
            {
                "account_id": "T-903",
                "email": "okubo@bakumatsu.com",
                "verified_email": False,
                "solt": "100",
                "password": "password",
                "is_active": True,
                "account_type": AccountTypes.general,
            },
        ],
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_xx_profiles_table() -> None:
    op.create_table(
        "xx_profiles",
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
            nullable=True,
            index=True,
            comment="ニックネーム",
        ),
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
        sa.Column(
            "account_type",
            sa.Enum(*AccountTypes.list(), name="account_type", schema="account"),
            nullable=False,
            server_default=AccountTypes.general,
            index=True,
            comment="アカウント種別",
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="False",
            comment="初期パスワード変更済み",
        ),
        *timestamps(),
        schema="account",
    )
    op.execute(
        """
        CREATE TRIGGER xx_profiles_modified
            BEFORE UPDATE
            ON account.xx_profiles
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_xx_authes_table() -> None:
    op.create_table(
        "xx_authes",
        sa.Column("account_id", sa.String(5), primary_key=True, comment="アカウントID"),
        sa.Column(
            "email", sa.Text, unique=True, nullable=False, index=True, comment="メールアドレス"
        ),
        sa.Column("solt", sa.Text, nullable=False, comment="ソルト"),
        sa.Column("password", sa.Text, nullable=False, comment="パスワード(HASH済)"),
        *timestamps(),
        schema="account",
    )
    op.execute(
        """
        CREATE TRIGGER authes_modified
            BEFORE UPDATE
            ON account.xx_authes
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    op.create_foreign_key(
        "fk_account_id",
        "xx_authes",
        "xx_profiles",
        ["account_id"],
        ["account_id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
        source_schema="account",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_email",
        "xx_authes",
        "xx_profiles",
        ["email"],
        ["email"],
        onupdate="CASCADE",
        ondelete="CASCADE",
        source_schema="account",
        referent_schema="account",
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    create_profiles_table()
    create_authes_table()
    create_watch_tasks_table()

    create_xx_profiles_table()
    create_xx_authes_table()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS account.xx_authes CASCADE;")
    op.execute("DROP TABLE IF EXISTS account.xx_profiles CASCADE;")

    op.execute("DROP TABLE IF EXISTS account.watch_tasks CASCADE;")
    op.execute("DROP TABLE IF EXISTS account.authes CASCADE;")
    op.execute("DROP TABLE IF EXISTS account.profiles CASCADE;")
    # op.drop_table("watch_tasks", schema="account")
    # op.drop_table("authes", schema="account")
    # op.drop_table("profiles", schema="account")
    op.execute("DROP TYPE IF EXISTS account.accopunt_type;")
