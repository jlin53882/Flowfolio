from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import get_settings


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False, "timeout": 5},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def get_db() -> Generator[Session, None, None]:
    with sessionmaker(bind=get_engine(), expire_on_commit=False, class_=Session)() as session:
        yield session
