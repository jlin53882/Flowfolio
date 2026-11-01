from pathlib import Path

from alembic import command
from alembic.config import Config

from ..core.config import get_settings


def upgrade_database() -> None:
    """執行已追蹤的 Alembic migration，啟動時不靜默退回 create_all。"""
    get_settings().resolved_data_dir.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
    command.upgrade(config, "head")
