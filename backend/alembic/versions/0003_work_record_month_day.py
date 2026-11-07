"""新增工作紀錄的年月與日欄位，支援日為 0 的整月紀錄。"""

import sqlalchemy as sa
from alembic import op

revision = "0003_work_record_month_day"
down_revision = "0002_goal_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "work_records",
        sa.Column("record_month", sa.String(7), nullable=False, server_default=""),
    )
    op.add_column(
        "work_records",
        sa.Column("record_day", sa.Integer(), nullable=False, server_default="1"),
    )
    op.execute(
        "UPDATE work_records "
        "SET record_month = strftime('%Y-%m', date), "
        "record_day = CAST(strftime('%d', date) AS INTEGER)"
    )
    op.create_index("ix_work_records_record_month", "work_records", ["record_month"])


def downgrade() -> None:
    op.drop_index("ix_work_records_record_month", table_name="work_records")
    op.drop_column("work_records", "record_day")
    op.drop_column("work_records", "record_month")
