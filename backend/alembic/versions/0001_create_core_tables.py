"""建立 Flowfolio 第一版核心資料表。"""

import sqlalchemy as sa
from alembic import op

revision = "0001_create_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quotes",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("quote_number", sa.String(80), nullable=False),
        sa.Column("client_name", sa.String(200), nullable=False),
        sa.Column("quote_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("tax_rate_bps", sa.Integer(), nullable=False),
        sa.Column("deposit_percent", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("tax_rate_bps >= 0 AND tax_rate_bps <= 10000", name="quote_tax_rate"),
        sa.CheckConstraint(
            "deposit_percent >= 0 AND deposit_percent <= 100", name="quote_deposit_percent"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quotes"),
        sa.UniqueConstraint("quote_number", name="uq_quotes_quote_number"),
    )
    op.create_index("ix_quotes_quote_number", "quotes", ["quote_number"], unique=False)
    op.create_index("ix_quotes_status", "quotes", ["status"], unique=False)

    op.create_table(
        "quote_items",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("quote_id", sa.String(36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("quantity_milliunits", sa.Integer(), nullable=False),
        sa.Column("unit_price_minor", sa.Integer(), nullable=False),
        sa.CheckConstraint("quantity_milliunits >= 0", name="quote_item_quantity"),
        sa.CheckConstraint("unit_price_minor >= 0", name="quote_item_price"),
        sa.ForeignKeyConstraint(
            ["quote_id"], ["quotes.id"], name="fk_quote_items_quote_id_quotes", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quote_items"),
    )
    op.create_index("ix_quote_items_quote_id", "quote_items", ["quote_id"], unique=False)

    op.create_table(
        "work_records",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("work_type", sa.String(80), nullable=False),
        sa.Column("income_minor", sa.Integer(), nullable=False),
        sa.Column("work_minutes", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("quote_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("income_minor >= 0", name="work_income"),
        sa.CheckConstraint("work_minutes >= 0", name="work_minutes"),
        sa.ForeignKeyConstraint(
            ["quote_id"], ["quotes.id"], name="fk_work_records_quote_id_quotes", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_work_records"),
    )
    op.create_index("ix_work_records_date", "work_records", ["date"], unique=False)

    op.create_table(
        "todos",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=True),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_todos"),
    )
    op.create_index("ix_todos_date", "todos", ["date"], unique=False)

    op.create_table(
        "practice_records",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("piece", sa.String(200), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_practice_records"),
    )
    op.create_index("ix_practice_records_date", "practice_records", ["date"], unique=False)

    op.create_table(
        "portfolio_items",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=True),
        sa.Column("project", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_items"),
    )
    op.create_index("ix_portfolio_items_date", "portfolio_items", ["date"], unique=False)
    op.create_index("ix_portfolio_items_category", "portfolio_items", ["category"], unique=False)

    op.create_table(
        "portfolio_media",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("portfolio_item_id", sa.String(36), nullable=False),
        sa.Column("storage_key", sa.String(200), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("missing", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["portfolio_item_id"],
            ["portfolio_items.id"],
            name="fk_portfolio_media_portfolio_item_id_portfolio_items",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_media"),
        sa.UniqueConstraint("storage_key", name="uq_portfolio_media_storage_key"),
    )
    op.create_index(
        "ix_portfolio_media_portfolio_item_id",
        "portfolio_media",
        ["portfolio_item_id"],
        unique=False,
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("key", name="pk_app_settings"),
    )

    op.create_table(
        "legacy_import_runs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("report_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_legacy_import_runs"),
    )
    op.create_index(
        "ix_legacy_import_runs_source_sha256", "legacy_import_runs", ["source_sha256"], unique=False
    )

    op.create_table(
        "legacy_import_items",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("source_index", sa.Integer(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "category IN ('works', 'todos', 'practice', 'portfolio')", name="legacy_category"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_legacy_import_items"),
    )


def downgrade() -> None:
    op.drop_table("legacy_import_items")
    op.drop_index("ix_legacy_import_runs_source_sha256", table_name="legacy_import_runs")
    op.drop_table("legacy_import_runs")
    op.drop_table("app_settings")
    op.drop_index("ix_portfolio_media_portfolio_item_id", table_name="portfolio_media")
    op.drop_table("portfolio_media")
    op.drop_index("ix_portfolio_items_category", table_name="portfolio_items")
    op.drop_index("ix_portfolio_items_date", table_name="portfolio_items")
    op.drop_table("portfolio_items")
    op.drop_index("ix_practice_records_date", table_name="practice_records")
    op.drop_table("practice_records")
    op.drop_index("ix_todos_date", table_name="todos")
    op.drop_table("todos")
    op.drop_index("ix_work_records_date", table_name="work_records")
    op.drop_table("work_records")
    op.drop_index("ix_quote_items_quote_id", table_name="quote_items")
    op.drop_table("quote_items")
    op.drop_index("ix_quotes_status", table_name="quotes")
    op.drop_index("ix_quotes_quote_number", table_name="quotes")
    op.drop_table("quotes")
