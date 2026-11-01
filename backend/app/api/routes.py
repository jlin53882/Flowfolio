from __future__ import annotations

import io
import json
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse, Response
from PIL import Image
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.errors import DomainError
from ..db.models import PortfolioMedia
from ..db.session import get_db
from ..infrastructure.backup import create_backup
from ..infrastructure.exports import quote_csv_bytes, quote_pdf_bytes, safe_filename
from ..schemas import (
    PortfolioCreate,
    PortfolioPatch,
    PracticeCreate,
    PracticePatch,
    QuoteCreate,
    QuotePatch,
    TodoCreate,
    TodoPatch,
    WorkCreate,
    WorkPatch,
)
from ..services import (
    _load_quote,
    analytics,
    create_portfolio,
    create_practice,
    create_todo,
    create_work,
    dashboard,
    delete_portfolio,
    delete_practice,
    delete_quote,
    delete_todo,
    delete_work,
    duplicate_quote,
    export_data,
    get_media,
    get_portfolio,
    get_work,
    list_portfolio,
    list_practice,
    list_quotes,
    list_todos,
    list_works,
    portfolio_to_dict,
    quote_to_dict,
    save_quote,
    update_portfolio,
    update_practice,
    update_todo,
    update_work,
    work_to_dict,
)

router = APIRouter(prefix="/api/v1")


@router.get("/dashboard")
def read_dashboard(month: str, selected_date: date | None = None, db: Session = Depends(get_db)):
    try:
        return dashboard(db, month, selected_date or date.today())
    except ValueError as exc:
        raise DomainError("月份格式必須是 YYYY-MM", 422, "invalid_month") from exc


@router.get("/works")
def read_works(
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    return list_works(db, search, date_from, date_to)


@router.post("/works", status_code=201)
def add_work(payload: WorkCreate, db: Session = Depends(get_db)):
    return create_work(db, payload)


@router.get("/works/{item_id}")
def read_work(item_id: str, db: Session = Depends(get_db)):
    return work_to_dict(get_work(db, item_id))


@router.patch("/works/{item_id}")
def edit_work(item_id: str, payload: WorkPatch, db: Session = Depends(get_db)):
    return update_work(db, item_id, payload)


@router.delete("/works/{item_id}", status_code=204)
def remove_work(item_id: str, db: Session = Depends(get_db)):
    delete_work(db, item_id)
    return Response(status_code=204)


@router.get("/todos")
def read_todos(on_date: date | None = None, db: Session = Depends(get_db)):
    return list_todos(db, on_date)


@router.post("/todos", status_code=201)
def add_todo(payload: TodoCreate, db: Session = Depends(get_db)):
    return create_todo(db, payload)


@router.patch("/todos/{item_id}")
def edit_todo(item_id: str, payload: TodoPatch, db: Session = Depends(get_db)):
    return update_todo(db, item_id, payload)


@router.delete("/todos/{item_id}", status_code=204)
def remove_todo(item_id: str, db: Session = Depends(get_db)):
    delete_todo(db, item_id)
    return Response(status_code=204)


@router.get("/practice")
def read_practice(on_date: date | None = None, db: Session = Depends(get_db)):
    return list_practice(db, on_date)


@router.post("/practice", status_code=201)
def add_practice(payload: PracticeCreate, db: Session = Depends(get_db)):
    return create_practice(db, payload)


@router.patch("/practice/{item_id}")
def edit_practice(item_id: str, payload: PracticePatch, db: Session = Depends(get_db)):
    return update_practice(db, item_id, payload)


@router.delete("/practice/{item_id}", status_code=204)
def remove_practice(item_id: str, db: Session = Depends(get_db)):
    delete_practice(db, item_id)
    return Response(status_code=204)


@router.get("/quotes")
def read_quotes(db: Session = Depends(get_db)):
    return list_quotes(db)


@router.post("/quotes", status_code=201)
def add_quote(payload: QuoteCreate, db: Session = Depends(get_db)):
    return save_quote(db, payload)


@router.get("/quotes/{item_id}")
def read_quote(item_id: str, db: Session = Depends(get_db)):
    return quote_to_dict(_load_quote(db, item_id))


@router.patch("/quotes/{item_id}")
def edit_quote(item_id: str, payload: QuotePatch, db: Session = Depends(get_db)):
    return save_quote(db, payload, item_id)


@router.post("/quotes/{item_id}/duplicate", status_code=201)
def copy_quote(item_id: str, db: Session = Depends(get_db)):
    return duplicate_quote(db, item_id)


@router.get("/quotes/{item_id}/export.pdf")
def export_quote_pdf(item_id: str, db: Session = Depends(get_db)):
    quote = _load_quote(db, item_id)
    filename = f"{safe_filename(quote.quote_number)}.pdf"
    return Response(
        content=quote_pdf_bytes(quote, get_settings()),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/quotes/{item_id}/export.csv")
def export_quote_csv(item_id: str, db: Session = Depends(get_db)):
    quote = _load_quote(db, item_id)
    filename = f"{safe_filename(quote.quote_number)}.csv"
    return Response(
        content=quote_csv_bytes(quote),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/quotes/{item_id}", status_code=204)
def remove_quote(item_id: str, db: Session = Depends(get_db)):
    delete_quote(db, item_id)
    return Response(status_code=204)


@router.get("/portfolio")
def read_portfolio(search: str | None = None, db: Session = Depends(get_db)):
    return list_portfolio(db, search)


@router.post("/portfolio", status_code=201)
def add_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db)):
    return create_portfolio(db, payload)


@router.get("/portfolio/{item_id}")
def read_portfolio_item(item_id: str, db: Session = Depends(get_db)):
    return portfolio_to_dict(get_portfolio(db, item_id))


@router.patch("/portfolio/{item_id}")
def edit_portfolio(item_id: str, payload: PortfolioPatch, db: Session = Depends(get_db)):
    return update_portfolio(db, item_id, payload)


@router.post("/portfolio/{item_id}/media", status_code=201)
async def add_portfolio_media(
    item_id: str, files: list[UploadFile] = File(...), db: Session = Depends(get_db)
):
    item = get_portfolio(db, item_id)
    settings = get_settings()
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    try:
        for file in files:
            if file.content_type not in allowed:
                raise DomainError("只接受 JPG、PNG 或 WebP 圖片", 422, "invalid_media_type")
            data = await file.read()
            if len(data) > 8 * 1024 * 1024:
                raise DomainError("單張圖片不可超過 8 MB", 422, "media_too_large")
            try:
                with Image.open(io.BytesIO(data)) as image:
                    image.verify()
                    width, height = image.size
            except Exception as exc:
                raise DomainError("圖片內容無法驗證", 422, "invalid_media") from exc
            if width > 8000 or height > 8000:
                raise DomainError("圖片尺寸不可超過 8000px", 422, "media_dimensions")
            media_id = str(uuid.uuid4())
            storage_key = f"{item.id}/{media_id}{allowed[file.content_type]}"
            destination = settings.media_dir / storage_key
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            created.append(destination)
            db.add(
                PortfolioMedia(
                    id=media_id,
                    portfolio_item_id=item.id,
                    storage_key=storage_key,
                    original_name=Path(file.filename or "image").name,
                    mime_type=file.content_type,
                    size_bytes=len(data),
                    position=len(item.media),
                    missing=False,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return portfolio_to_dict(get_portfolio(db, item.id))


@router.delete("/portfolio/{item_id}", status_code=204)
def remove_portfolio(item_id: str, db: Session = Depends(get_db)):
    settings = get_settings()
    storage_keys = delete_portfolio(db, item_id)
    for key in storage_keys:
        path = settings.media_dir / key
        try:
            path.resolve().relative_to(settings.media_dir.resolve())
            path.unlink(missing_ok=True)
        except (ValueError, OSError):
            pass
    return Response(status_code=204)


@router.get("/media/{media_id}")
def read_media(media_id: str, db: Session = Depends(get_db)):
    media = get_media(db, media_id)
    settings = get_settings()
    path = (settings.media_dir / media.storage_key).resolve()
    try:
        path.relative_to(settings.media_dir.resolve())
    except ValueError as exc:
        raise DomainError("圖片路徑不合法", 400, "invalid_media_path") from exc
    if not path.is_file():
        raise DomainError("圖片檔案不存在", 404, "media_missing")
    return FileResponse(path, media_type=media.mime_type, filename=media.original_name)


@router.get("/analytics/summary")
def read_analytics(months: int = 6, db: Session = Depends(get_db)):
    return analytics(db, months)


@router.get("/maintenance/export")
def export_all_data(db: Session = Depends(get_db)):
    return Response(
        content=json.dumps(export_data(db), ensure_ascii=False, indent=2).encode("utf-8"),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="flowfolio-export.json"'},
    )


@router.post("/maintenance/backup")
def backup_data():
    return create_backup(get_settings())
