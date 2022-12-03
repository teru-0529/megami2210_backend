"""create tasks table

Revision ID: e85dfc42f48d
Revises: de6f035be044
Create Date: 2022-11-19 00:10:53.096333

"""
import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps
from app.models.segment_values import TaskStatus

# revision identifiers, used by Alembic.
revision = "e85dfc42f48d"
down_revision = "de6f035be044"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_tasks_table() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True, comment="タスクID"),
        # sa.Column(
        #     "registrant_id", sa.String(5), nullable=True, comment="登録者ID"
        # ),  # FIXME:
        sa.Column("title", sa.String(30), nullable=False, comment="タイトル"),
        sa.Column("description", sa.Text, nullable=True, comment="内容"),
        sa.Column("asaignee_id", sa.String(5), nullable=True, comment="担当者ID"),
        sa.Column(
            "status",
            sa.Enum(*TaskStatus.list(), name="status", schema="todo"),
            nullable=False,
            server_default=TaskStatus.todo,
            index=True,
            comment="タスクステータス",
        ),
        sa.Column(
            "is_significant",
            sa.Boolean,
            nullable=False,
            server_default="False",
            comment="重要タスク",
        ),
        sa.Column(
            "deadline",
            sa.Date,
            nullable=True,
            comment="締切日",
        ),
        *timestamps(),
        schema="todo",
    )
    op.execute(
        """
        CREATE TRIGGER tasks_modified
            BEFORE UPDATE
            ON todo.tasks
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    # op.create_foreign_key(
    #     "fk_registrant_id",
    #     "tasks",
    #     "profiles",
    #     ["registrant_id"],
    #     ["account_id"],
    #     ondelete="SET NULL",
    #     source_schema="todo",
    #     referent_schema="account",
    # )  # FIXME:
    # op.create_foreign_key(
    #     "fk_asaignee_id",
    #     "tasks",
    #     "profiles",
    #     ["asaignee_id"],
    #     ["account_id"],
    #     ondelete="SET NULL",
    #     source_schema="todo",
    #     referent_schema="account",
    # )  # FIXME:


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_watcher_table() -> None:
    op.create_table(
        "watcher",
        sa.Column("watcher_id", sa.String(5), primary_key=True, comment="観測者ID"),
        sa.Column("task_id", sa.Integer, primary_key=True, index=True, comment="タスクID"),
        sa.Column(
            "note",
            sa.Text,
            nullable=True,
            comment="ノート",
        ),
        *timestamps(),
        schema="todo",
    )
    op.execute(
        """
        CREATE TRIGGER watcher_modified
            BEFORE UPDATE
            ON todo.watcher
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    op.create_foreign_key(
        "fk_account_id",
        "watcher",
        "profiles",
        ["watcher_id"],
        ["account_id"],
        ondelete="CASCADE",
        source_schema="todo",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_task_id",
        "watcher",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
        source_schema="todo",
        referent_schema="todo",
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    create_tasks_table()
    create_watcher_table()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS todo.watcher CASCADE;")
    op.execute("DROP TABLE IF EXISTS todo.tasks CASCADE;")
    op.execute("DROP TYPE IF EXISTS todo.status;")
