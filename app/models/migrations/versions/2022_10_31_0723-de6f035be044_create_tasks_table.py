"""create tasks table

Revision ID: de6f035be044
Revises: 307da1eafeaa
Create Date: 2022-10-31 07:23:41.753128

"""
import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps
from app.models.segment_values import TaskStatus

# revision identifiers, used by Alembic.
revision = "de6f035be044"
down_revision = "307da1eafeaa"
branch_labels = None
depends_on = None


def create_tasks_table() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True, comment="タスクID"),
        sa.Column("title", sa.String(30), nullable=False, comment="タイトル"),
        sa.Column("description", sa.Text, nullable=True, comment="内容"),
        sa.Column("asaignee_id", sa.String(3), nullable=True, comment="担当者ID"),
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


def upgrade() -> None:
    create_tasks_table()


def downgrade() -> None:
    op.drop_table("tasks", schema="todo")
    op.execute("DROP TYPE IF EXISTS todo.status;")
