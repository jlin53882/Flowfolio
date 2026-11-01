from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Flowfolio 舊 JSON 與圖片安全匯入工具")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="只產生報告，不寫入資料庫或媒體目錄")
    mode.add_argument("--apply", action="store_true", help="確認後寫入新的 Flowfolio 資料目錄")
    parser.add_argument("--source", required=True, type=Path, help="舊 records.json 路徑")
    parser.add_argument("--media-root", type=Path, help="允許搜尋舊圖片的目錄")
    parser.add_argument(
        "--report", type=Path, default=Path("reports/legacy-import.json"), help="報告輸出路徑"
    )
    parser.add_argument("--data-dir", type=Path, help="覆寫 FLOWFOLIO_DATA_DIR")
    args = parser.parse_args()
    if args.data_dir:
        os.environ["FLOWFOLIO_DATA_DIR"] = str(args.data_dir)

    from app.core.config import get_settings
    from app.db.migrate import upgrade_database
    from app.db.session import get_engine
    from app.infrastructure.legacy_import import run_legacy_import
    from sqlalchemy.orm import Session

    get_settings.cache_clear()
    get_engine.cache_clear()
    settings = get_settings()
    upgrade_database()
    dry_run = not args.apply
    with Session(get_engine()) as db:
        report = run_legacy_import(
            db,
            settings,
            args.source.resolve(),
            args.media_root.resolve() if args.media_root else None,
            dry_run=dry_run,
            report_path=args.report.resolve(),
        )
    print(f"匯入報告：{args.report.resolve()}")
    for category, values in report["categories"].items():
        print(
            f"{category}: 來源 {values['source']}，預計匯入 {values['would_import']}，"
            f"已匯入 {values['imported']}，略過 {values['skipped']}，錯誤 {len(values['errors'])}"
        )
    print("模式：預覽（未寫入）" if dry_run else "模式：正式匯入")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
