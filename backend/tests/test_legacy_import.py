from __future__ import annotations

import json

from app.core.config import get_settings
from app.db.migrate import upgrade_database
from app.db.session import get_engine
from app.infrastructure.legacy_import import run_legacy_import
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def test_legacy_import_dry_run_and_repeat_is_idempotent(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("FLOWFOLIO_DATA_DIR", str(data_dir))
    get_settings.cache_clear()
    get_engine.cache_clear()
    source = tmp_path / "records.json"
    source.write_text(
        json.dumps(
            {
                "works": [{"date": "2026-11-01", "name": "舊工作", "income": 100, "hours": 1}],
                "practice": [],
                "portfolio": [],
                "todos": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    upgrade_database()
    with Session(get_engine()) as db:
        preview = run_legacy_import(db, get_settings(), source, dry_run=True)
        assert preview["categories"]["works"]["would_import"] == 1
        assert (
            db.execute(
                select(func.count()).select_from(
                    __import__("app.db.models", fromlist=["WorkRecord"]).WorkRecord
                )
            ).scalar_one()
            == 0
        )
        applied = run_legacy_import(db, get_settings(), source, dry_run=False)
        assert applied["categories"]["works"]["imported"] == 1
        repeated = run_legacy_import(db, get_settings(), source, dry_run=False)
        assert repeated["categories"]["works"]["skipped"] == 1
        assert (
            db.execute(
                select(func.count()).select_from(
                    __import__("app.db.models", fromlist=["WorkRecord"]).WorkRecord
                )
            ).scalar_one()
            == 1
        )
