from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Flowfolio SQLite 與媒體一致性備份工具")
    parser.add_argument("--data-dir", type=Path, help="覆寫 FLOWFOLIO_DATA_DIR")
    args = parser.parse_args()
    if args.data_dir:
        os.environ["FLOWFOLIO_DATA_DIR"] = str(args.data_dir)
    from app.core.config import get_settings
    from app.infrastructure.backup import create_backup

    get_settings.cache_clear()
    result = create_backup(get_settings())
    print(f"備份完成：{get_settings().backup_dir / result['archive_name']}")
    print(f"檔案數：{result['file_count']}，資料庫 SHA-256：{result['database_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
