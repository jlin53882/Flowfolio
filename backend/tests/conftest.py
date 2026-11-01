from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("FLOWFOLIO_DATA_DIR", str(data_dir))
    from app.core.config import get_settings
    from app.db.session import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    get_engine.cache_clear()
    get_settings.cache_clear()
