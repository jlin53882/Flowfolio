"""新增跨類型目標與進度紀錄資料表。"""

import sqlalchemy as sa
from alembic import op

revision = "0002_goal_tracking"
down_revision = "0001_create_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_value", sa.Numeric(12, 3), nullable=False),
        sa.Column("current_value", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("target_value > 0", name="goal_target_value"),
        sa.CheckConstraint("current_value >= 0", name="goal_current_value"),
        sa.CheckConstraint("status IN ('active', 'completed')", name="goal_status"),
        sa.PrimaryKeyConstraint("id", name="pk_goals"),
    )
    op.create_index("ix_goals_category", "goals", ["category"], unique=False)
    op.create_index("ix_goals_due_date", "goals", ["due_date"], unique=False)
    op.create_index("ix_goals_status", "goals", ["status"], unique=False)

    op.create_table(
        "goal_progress_logs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column("current_value", sa.Numeric(12, 3), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["goal_id"],
            ["goals.id"],
            name="fk_goal_progress_logs_goal_id_goals",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_goal_progress_logs"),
    )
    op.create_index(
        "ix_goal_progress_logs_goal_id", "goal_progress_logs", ["goal_id"], unique=False
    )
    op.create_index(
        "ix_goal_progress_logs_record_date", "goal_progress_logs", ["record_date"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_goal_progress_logs_record_date", table_name="goal_progress_logs")
    op.drop_index("ix_goal_progress_logs_goal_id", table_name="goal_progress_logs")
    op.drop_table("goal_progress_logs")
    op.drop_index("ix_goals_status", table_name="goals")
    op.drop_index("ix_goals_due_date", table_name="goals")
    op.drop_index("ix_goals_category", table_name="goals")
    op.drop_table("goals")
