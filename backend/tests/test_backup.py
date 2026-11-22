from __future__ import annotations

import sqlite3
import zipfile

import pytest
from app.core.config import get_settings
from app.infrastructure import backup as backup_module


def test_backup_api_creates_archive_with_manifest(client):
    response = client.post("/api/v1/maintenance/backup")
    assert response.status_code == 200, response.text
    archive_name = response.json()["archive_name"]
    archive_path = get_settings().backup_dir / archive_name
    assert archive_path.is_file()
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
    assert {"flowfolio.db", "manifest.json"} <= names


def test_backup_closes_sqlite_connections(client, monkeypatch):
    # Windows 無法刪除仍開啟中的暫存資料庫；確認備份用的連線都已關閉。
    opened: list[sqlite3.Connection] = []
    real_connect = sqlite3.connect

    def tracking_connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(connection)
        return connection

    monkeypatch.setattr(backup_module.sqlite3, "connect", tracking_connect)
    backup_module.create_backup(get_settings())
    assert len(opened) == 2
    for connection in opened:
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("select 1")
