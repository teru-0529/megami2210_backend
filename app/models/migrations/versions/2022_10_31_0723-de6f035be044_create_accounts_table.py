"""create accounts table

Revision ID: de6f035be044
Revises: 307da1eafeaa
Create Date: 2022-10-31 07:23:41.753128

"""
import os
import pathlib
import sys

import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps
from app.models.segment_values import AccountTypes

dir = str(pathlib.Path(__file__).resolve().parents[4])
sys.path.append(os.path.join(dir, ".venv", "lib", "python3.11", "site-packages"))
from app.services import auth_service  # noqa:E402

# revision identifiers, used by Alembic.
revision = "de6f035be044"
down_revision = "307da1eafeaa"
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
            comment="アクティベート済み",
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
            {
                "account_id": "T-901",
                "user_name": "西郷隆盛",
                "nickname": "西郷どん",
                "email": "saigo@bakumatsu.com",
                "verified_email": True,
                "account_type": AccountTypes.administrator,
                "is_active": True,
            },
            {
                "account_id": "T-902",
                "user_name": "木戸孝允",
                "nickname": "桂小五郎",
                "email": "kido@bakumatsu.com",
                "verified_email": False,
                "account_type": AccountTypes.general,
                "is_active": True,
            },
            {
                "account_id": "T-903",
                "user_name": "大久保利通",
                "nickname": None,
                "email": "okubo@bakumatsu.com",
                "verified_email": False,
                "account_type": AccountTypes.general,
                "is_active": False,
            },
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
        sa.Column("solt", sa.Text, nullable=False, comment="ソルト"),
        sa.Column("password", sa.Text, nullable=False, comment="パスワード(HASH済)"),
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
        ondelete="CASCADE",
        source_schema="account",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_email",
        "authes",
        "profiles",
        ["email"],
        ["email"],
        onupdate="CASCADE",
        ondelete="CASCADE",
        source_schema="account",
        referent_schema="account",
    )

    # 初期登録アカウントのパスワードのHash化処理
    hash_password, solt = auth_service.create_hash_password(
        plaintext_password="password"
    )

    op.bulk_insert(
        authes_table,
        [
            {
                "account_id": "T-901",
                "email": "saigo@bakumatsu.com",
                "solt": solt,
                "password": hash_password,
            },
            {
                "account_id": "T-902",
                "email": "kido@bakumatsu.com",
                "solt": solt,
                "password": hash_password,
            },
            {
                "account_id": "T-903",
                "email": "okubo@bakumatsu.com",
                "solt": solt,
                "password": hash_password,
            },
        ],
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    create_profiles_table()
    create_authes_table()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS account.authes CASCADE;")
    op.execute("DROP TABLE IF EXISTS account.profiles CASCADE;")
    op.execute("DROP TYPE IF EXISTS account.accopunt_type;")
