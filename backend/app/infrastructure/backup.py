from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from ..core.config import Settings


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(settings: Settings) -> dict[str, object]:
    database_path = settings.database_path
    if not database_path.is_file():
        raise FileNotFoundError("資料庫尚未建立，無法備份")
    settings.backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"flowfolio-backup-{timestamp}.zip"
    final_archive = settings.backup_dir / archive_name

    with tempfile.TemporaryDirectory(prefix="flowfolio-backup-") as temp_dir:
        root = Path(temp_dir)
        database_copy = root / "flowfolio.db"
        with (
            sqlite3.connect(database_path) as source,
            sqlite3.connect(database_copy) as destination,
        ):
            source.backup(destination)
        media_source = settings.media_dir
        media_target = root / "media"
        if media_source.is_dir():
            shutil.copytree(media_source, media_target)
        else:
            media_target.mkdir()
        files = [path for path in root.rglob("*") if path.is_file()]
        manifest = {
            "version": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "database_sha256": sha256_file(database_copy),
            "file_count": len(files),
            "files": [
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256_file(path),
                    "size": path.stat().st_size,
                }
                for path in files
                if path.name != "manifest.json"
            ],
        }
        (root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary_archive = settings.backup_dir / f".{archive_name}.tmp"
        with zipfile.ZipFile(temporary_archive, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in root.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(root).as_posix())
        temporary_archive.replace(final_archive)
    return {**manifest, "archive_name": archive_name}
