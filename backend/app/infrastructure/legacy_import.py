from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import Settings
from ..db.models import (
    LegacyImportItem,
    LegacyImportRun,
    PortfolioItem,
    PortfolioMedia,
    PracticeRecord,
    Todo,
    WorkRecord,
)
from ..domain.pricing import money_to_minor
from ..services import parse_time

LEGACY_CATEGORIES = ("works", "todos", "practice", "portfolio")
ALLOWED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_hash(item: object) -> str:
    raw = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(raw).hexdigest()


def parse_date(value: object) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(str(value)[:10])


def decimal(value: object, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value or 0))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} 不是有效數字") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field} 必須是非負有限數字")
    return parsed


def _candidate_media(raw_path: object, media_root: Path | None) -> Path | None:
    if not raw_path or not media_root:
        return None
    root = media_root.expanduser().resolve()
    raw = Path(str(raw_path))
    candidates = [raw] if raw.is_absolute() else [root / raw]
    candidates.append(root / raw.name)
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if root == resolved or root in resolved.parents:
            if resolved.is_file() and resolved.suffix.lower() in ALLOWED_IMAGE_TYPES:
                return resolved
    return None


def _validate_image(path: Path) -> tuple[str, int]:
    with Image.open(path) as image:
        image.verify()
        if image.width > 8000 or image.height > 8000:
            raise ValueError("圖片尺寸超過 8000px 限制")
        mime = ALLOWED_IMAGE_TYPES.get(path.suffix.lower())
        if not mime:
            raise ValueError("不支援的圖片格式")
    return mime, path.stat().st_size


def inspect_source(source: Path) -> tuple[dict[str, Any], str]:
    if not source.is_file():
        raise FileNotFoundError(f"找不到來源 JSON：{source}")
    source_hash = sha256_file(source)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"來源 JSON 無法安全解析：{exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("來源 JSON 頂層必須是物件")
    normalized: dict[str, Any] = {}
    missing = []
    for category in LEGACY_CATEGORIES:
        if category not in payload:
            missing.append(category)
            normalized[category] = []
        elif not isinstance(payload[category], list):
            raise ValueError(f"來源欄位 {category} 必須是陣列")
        else:
            normalized[category] = payload[category]
    normalized["missing_categories"] = missing
    return normalized, source_hash


def _report_template(source: Path, source_hash: str, dry_run: bool) -> dict[str, Any]:
    return {
        "source": str(source),
        "source_sha256": source_hash,
        "dry_run": dry_run,
        "categories": {},
        "warnings": [],
        "errors": [],
        "media": {"found": 0, "missing": 0, "bytes": 0},
    }


def run_legacy_import(
    db: Session,
    settings: Settings,
    source: Path,
    media_root: Path | None = None,
    dry_run: bool = True,
    report_path: Path | None = None,
) -> dict[str, Any]:
    payload, source_hash = inspect_source(source)
    report = _report_template(source, source_hash, dry_run)
    if payload["missing_categories"]:
        report["warnings"].append(f"來源缺少欄位：{', '.join(payload['missing_categories'])}")
    for category in LEGACY_CATEGORIES:
        items = payload[category]
        category_report = {
            "source": len(items),
            "would_import": 0,
            "imported": 0,
            "skipped": 0,
            "errors": [],
        }
        report["categories"][category] = category_report
        for index, raw in enumerate(items):
            if not isinstance(raw, dict):
                category_report["errors"].append({"index": index, "reason": "資料列不是物件"})
                continue
            stable_hash = content_hash(raw)
            existing = db.scalar(
                select(LegacyImportItem).where(
                    LegacyImportItem.source_sha256 == source_hash,
                    LegacyImportItem.category == category,
                    LegacyImportItem.source_index == index,
                    LegacyImportItem.content_sha256 == stable_hash,
                    LegacyImportItem.status == "imported",
                )
            )
            if existing:
                category_report["skipped"] += 1
                continue
            copied: list[Path] = []
            try:
                if category == "works":
                    work_date = parse_date(raw.get("date"))
                    item = WorkRecord(
                        date=work_date,
                        record_month=work_date.strftime("%Y-%m"),
                        record_day=work_date.day,
                        name=str(raw.get("name") or raw.get("title") or "未命名工作").strip(),
                        work_type=str(raw.get("type") or "一般").strip(),
                        income_minor=money_to_minor(decimal(raw.get("income", 0), "收入"), "收入"),
                        work_minutes=int(
                            (decimal(raw.get("hours", 0), "工作時數") * 60).quantize(Decimal("1"))
                        ),
                        notes=str(raw.get("notes") or "").strip(),
                        completed=bool(raw.get("completed", False)),
                    )
                    if not dry_run:
                        db.add(item)
                        db.flush()
                        target_id = item.id
                elif category == "todos":
                    item = Todo(
                        date=parse_date(raw.get("date")),
                        time=parse_time(raw.get("time")),
                        location=str(raw.get("location") or "").strip(),
                        title=str(raw.get("title") or raw.get("name") or "未命名待辦").strip(),
                        completed=bool(raw.get("completed", False)),
                    )
                    if not dry_run:
                        db.add(item)
                        db.flush()
                        target_id = item.id
                elif category == "practice":
                    if raw.get("duration_seconds") is not None:
                        duration_seconds = int(decimal(raw["duration_seconds"], "練習秒數"))
                    elif raw.get("duration") is not None:
                        duration_seconds = int(
                            (decimal(raw["duration"], "練習分鐘") * 60).quantize(Decimal("1"))
                        )
                    else:
                        duration_seconds = int(
                            (decimal(raw.get("hours", 0), "練習時數") * 3600).quantize(Decimal("1"))
                        )
                    item = PracticeRecord(
                        date=parse_date(raw.get("date")),
                        piece=str(raw.get("piece") or raw.get("title") or "未命名曲目").strip(),
                        duration_seconds=max(0, duration_seconds),
                        notes=str(raw.get("notes") or "").strip(),
                        completed=bool(raw.get("completed", True)),
                    )
                    if not dry_run:
                        db.add(item)
                        db.flush()
                        target_id = item.id
                else:
                    item = PortfolioItem(
                        date=parse_date(raw.get("date")),
                        time=parse_time(raw.get("time")),
                        project=str(raw.get("project") or raw.get("title") or "未命名作品").strip(),
                        category=str(raw.get("category") or "未分類").strip(),
                        content=str(raw.get("content") or raw.get("description") or "").strip(),
                    )
                    image_paths = raw.get("images") or []
                    if not isinstance(image_paths, list):
                        image_paths = [image_paths]
                    resolved_images = []
                    for image_path in image_paths:
                        resolved = _candidate_media(image_path, media_root)
                        if not resolved:
                            report["media"]["missing"] += 1
                            report["warnings"].append(
                                f"作品第 {index + 1} 筆圖片不存在：{image_path}"
                            )
                            continue
                        mime, size = _validate_image(resolved)
                        resolved_images.append((resolved, mime, size))
                        report["media"]["found"] += 1
                        report["media"]["bytes"] += size
                    if not dry_run:
                        db.add(item)
                        db.flush()
                        target_id = item.id
                        for position, (resolved, mime, size) in enumerate(resolved_images):
                            digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
                            storage_key = f"{item.id}/{digest}{resolved.suffix.lower()}"
                            destination = settings.media_dir / storage_key
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(resolved, destination)
                            copied.append(destination)
                            db.add(
                                PortfolioMedia(
                                    portfolio_item_id=item.id,
                                    storage_key=storage_key,
                                    original_name=resolved.name,
                                    mime_type=mime,
                                    size_bytes=size,
                                    position=position,
                                    missing=False,
                                )
                            )
                if dry_run:
                    category_report["would_import"] += 1
                else:
                    db.add(
                        LegacyImportItem(
                            source_sha256=source_hash,
                            category=category,
                            source_index=index,
                            content_sha256=stable_hash,
                            target_id=locals().get("target_id"),
                            status="imported",
                            detail="",
                        )
                    )
                    category_report["imported"] += 1
            except (ValueError, OSError, InvalidOperation) as exc:
                for copied_file in copied:
                    copied_file.unlink(missing_ok=True)
                if not dry_run:
                    db.rollback()
                category_report["errors"].append({"index": index, "reason": str(exc)})
                report["errors"].append(f"{category}[{index}]：{exc}")
    if not dry_run:
        db.add(
            LegacyImportRun(
                source_path=str(source),
                source_sha256=source_hash,
                dry_run=False,
                report_json=json.dumps(report, ensure_ascii=False),
            )
        )
        db.commit()
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
