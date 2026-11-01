from __future__ import annotations

from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, selectinload

from .core.errors import DomainError
from .db.models import (
    AppSetting,
    PortfolioItem,
    PortfolioMedia,
    PracticeRecord,
    Quote,
    QuoteItem,
    Todo,
    WorkRecord,
)
from .domain.metrics import aggregate_months, completion_rate, month_start, next_month
from .domain.pricing import (
    QuoteLine,
    calculate_quote,
    money_to_minor,
    quantity_from_milliunits,
    quantity_to_milliunits,
)
from .schemas import (
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


def money_str(value: int | Decimal) -> str:
    decimal_value = Decimal(value)
    return format(decimal_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP), "f")


def decimal_str(value: Decimal) -> str:
    return format(value.normalize(), "f")


def parse_time(value: str | None) -> time | None:
    if not value:
        return None
    return datetime.strptime(value, "%H:%M").time()


def time_str(value: time | None) -> str | None:
    return value.strftime("%H:%M") if value else None


def work_to_dict(item: WorkRecord) -> dict[str, Any]:
    return {
        "id": item.id,
        "date": item.date.isoformat(),
        "name": item.name,
        "type": item.work_type,
        "income": money_str(item.income_minor),
        "hours": decimal_str(Decimal(item.work_minutes) / Decimal(60)),
        "work_minutes": item.work_minutes,
        "notes": item.notes,
        "completed": item.completed,
        "quote_id": item.quote_id,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def todo_to_dict(item: Todo) -> dict[str, Any]:
    return {
        "id": item.id,
        "date": item.date.isoformat(),
        "time": time_str(item.time),
        "location": item.location,
        "title": item.title,
        "completed": item.completed,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def practice_to_dict(item: PracticeRecord) -> dict[str, Any]:
    return {
        "id": item.id,
        "date": item.date.isoformat(),
        "piece": item.piece,
        "duration_seconds": item.duration_seconds,
        "duration_minutes": round(item.duration_seconds / 60, 1),
        "notes": item.notes,
        "completed": item.completed,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def quote_totals(quote: Quote) -> dict[str, str]:
    lines = [
        QuoteLine(
            description=item.description,
            quantity=quantity_from_milliunits(item.quantity_milliunits),
            unit_price=Decimal(item.unit_price_minor),
        )
        for item in quote.items
    ]
    totals = calculate_quote(
        lines, Decimal(quote.tax_rate_bps) / Decimal(100), quote.deposit_percent
    )
    return {key: money_str(value) for key, value in totals.__dict__.items()}


def quote_to_dict(quote: Quote) -> dict[str, Any]:
    return {
        "id": quote.id,
        "quote_number": quote.quote_number,
        "client_name": quote.client_name,
        "quote_date": quote.quote_date.isoformat(),
        "status": quote.status,
        "tax_rate_percent": decimal_str(Decimal(quote.tax_rate_bps) / Decimal(100)),
        "deposit_percent": quote.deposit_percent,
        "notes": quote.notes,
        "items": [
            {
                "id": item.id,
                "description": item.description,
                "quantity": decimal_str(quantity_from_milliunits(item.quantity_milliunits)),
                "unit_price": money_str(item.unit_price_minor),
                "position": item.position,
            }
            for item in quote.items
        ],
        "totals": quote_totals(quote),
        "created_at": quote.created_at.isoformat(),
        "updated_at": quote.updated_at.isoformat(),
    }


def media_to_dict(item: PortfolioMedia) -> dict[str, Any]:
    return {
        "id": item.id,
        "original_name": item.original_name,
        "mime_type": item.mime_type,
        "size_bytes": item.size_bytes,
        "position": item.position,
        "missing": item.missing,
        "url": f"/api/v1/media/{item.id}",
    }


def portfolio_to_dict(item: PortfolioItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "date": item.date.isoformat(),
        "time": time_str(item.time),
        "project": item.project,
        "category": item.category,
        "content": item.content,
        "media": [media_to_dict(media) for media in item.media],
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _work_minutes(hours: Decimal) -> int:
    return int((hours * 60).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def list_works(
    db: Session,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict[str, Any]]:
    query: Select[tuple[WorkRecord]] = select(WorkRecord).order_by(
        WorkRecord.date.desc(), WorkRecord.created_at.desc()
    )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                WorkRecord.name.ilike(pattern),
                WorkRecord.work_type.ilike(pattern),
                WorkRecord.notes.ilike(pattern),
            )
        )
    if date_from:
        query = query.where(WorkRecord.date >= date_from)
    if date_to:
        query = query.where(WorkRecord.date <= date_to)
    return [work_to_dict(item) for item in db.scalars(query).all()]


def get_work(db: Session, item_id: str) -> WorkRecord:
    item = db.get(WorkRecord, item_id)
    if not item:
        raise DomainError("找不到工作紀錄", 404, "work_not_found")
    return item


def create_work(db: Session, payload: WorkCreate) -> dict[str, Any]:
    item = WorkRecord(
        date=payload.date,
        name=payload.name.strip(),
        work_type=payload.type.strip(),
        income_minor=money_to_minor(payload.income, "收入"),
        work_minutes=_work_minutes(payload.hours),
        notes=payload.notes.strip(),
        quote_id=payload.quote_id,
        completed=payload.completed,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return work_to_dict(item)


def update_work(db: Session, item_id: str, payload: WorkPatch) -> dict[str, Any]:
    item = get_work(db, item_id)
    data = payload.model_dump(exclude_unset=True)
    if "date" in data:
        item.date = data["date"]
    if "name" in data:
        item.name = data["name"].strip()
    if "type" in data:
        item.work_type = data["type"].strip()
    if "income" in data and data["income"] is not None:
        item.income_minor = money_to_minor(data["income"], "收入")
    if "hours" in data and data["hours"] is not None:
        item.work_minutes = _work_minutes(data["hours"])
    if "notes" in data and data["notes"] is not None:
        item.notes = data["notes"].strip()
    if "quote_id" in data:
        item.quote_id = data["quote_id"]
    if "completed" in data and data["completed"] is not None:
        item.completed = data["completed"]
    db.commit()
    db.refresh(item)
    return work_to_dict(item)


def delete_work(db: Session, item_id: str) -> None:
    item = get_work(db, item_id)
    db.delete(item)
    db.commit()


def list_todos(db: Session, on_date: date | None = None) -> list[dict[str, Any]]:
    query = select(Todo).order_by(Todo.date.desc(), Todo.time.asc(), Todo.created_at.desc())
    if on_date:
        query = query.where(Todo.date == on_date)
    return [todo_to_dict(item) for item in db.scalars(query).all()]


def get_todo(db: Session, item_id: str) -> Todo:
    item = db.get(Todo, item_id)
    if not item:
        raise DomainError("找不到待辦事項", 404, "todo_not_found")
    return item


def create_todo(db: Session, payload: TodoCreate) -> dict[str, Any]:
    item = Todo(
        date=payload.date,
        time=parse_time(payload.time),
        location=payload.location.strip(),
        title=payload.title.strip(),
        completed=payload.completed,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return todo_to_dict(item)


def update_todo(db: Session, item_id: str, payload: TodoPatch) -> dict[str, Any]:
    item = get_todo(db, item_id)
    data = payload.model_dump(exclude_unset=True)
    if "date" in data:
        item.date = data["date"]
    if "time" in data:
        item.time = parse_time(data["time"])
    if "location" in data and data["location"] is not None:
        item.location = data["location"].strip()
    if "title" in data and data["title"] is not None:
        item.title = data["title"].strip()
    if "completed" in data and data["completed"] is not None:
        item.completed = data["completed"]
    db.commit()
    db.refresh(item)
    return todo_to_dict(item)


def delete_todo(db: Session, item_id: str) -> None:
    item = get_todo(db, item_id)
    db.delete(item)
    db.commit()


def list_practice(db: Session, on_date: date | None = None) -> list[dict[str, Any]]:
    query = select(PracticeRecord).order_by(
        PracticeRecord.date.desc(), PracticeRecord.created_at.desc()
    )
    if on_date:
        query = query.where(PracticeRecord.date == on_date)
    return [practice_to_dict(item) for item in db.scalars(query).all()]


def get_practice(db: Session, item_id: str) -> PracticeRecord:
    item = db.get(PracticeRecord, item_id)
    if not item:
        raise DomainError("找不到練習紀錄", 404, "practice_not_found")
    return item


def create_practice(db: Session, payload: PracticeCreate) -> dict[str, Any]:
    item = PracticeRecord(
        date=payload.date,
        piece=payload.piece.strip(),
        duration_seconds=payload.duration_seconds,
        notes=payload.notes.strip(),
        completed=payload.completed,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return practice_to_dict(item)


def update_practice(db: Session, item_id: str, payload: PracticePatch) -> dict[str, Any]:
    item = get_practice(db, item_id)
    data = payload.model_dump(exclude_unset=True)
    for field in ("date", "duration_seconds", "completed"):
        if field in data and data[field] is not None:
            setattr(item, field, data[field])
    if "piece" in data and data["piece"] is not None:
        item.piece = data["piece"].strip()
    if "notes" in data and data["notes"] is not None:
        item.notes = data["notes"].strip()
    db.commit()
    db.refresh(item)
    return practice_to_dict(item)


def delete_practice(db: Session, item_id: str) -> None:
    item = get_practice(db, item_id)
    db.delete(item)
    db.commit()


def _load_quote(db: Session, item_id: str) -> Quote:
    quote = db.scalar(select(Quote).options(selectinload(Quote.items)).where(Quote.id == item_id))
    if not quote:
        raise DomainError("找不到報價單", 404, "quote_not_found")
    return quote


def _ensure_quote_number_available(
    db: Session, quote_number: str, current_id: str | None = None
) -> None:
    query = select(Quote).where(Quote.quote_number == quote_number)
    if current_id:
        query = query.where(Quote.id != current_id)
    if db.scalar(query):
        raise DomainError("報價單編號已存在，請換一個編號", 409, "quote_number_conflict")


def _apply_quote_payload(quote: Quote, payload: QuoteCreate | QuotePatch) -> None:
    quote.quote_number = payload.quote_number.strip()
    quote.client_name = payload.client_name.strip()
    quote.quote_date = payload.quote_date
    quote.tax_rate_bps = int(payload.tax_rate_percent * 100)
    quote.deposit_percent = payload.deposit_percent
    quote.notes = payload.notes.strip()


def save_quote(
    db: Session, payload: QuoteCreate | QuotePatch, item_id: str | None = None
) -> dict[str, Any]:
    quote = (
        _load_quote(db, item_id)
        if item_id
        else Quote(quote_number="", client_name="", quote_date=payload.quote_date)
    )
    _ensure_quote_number_available(db, payload.quote_number.strip(), item_id)
    _apply_quote_payload(quote, payload)
    if not item_id:
        db.add(quote)
        db.flush()
    quote.items.clear()
    for position, item in enumerate(payload.items):
        quote.items.append(
            QuoteItem(
                description=item.description.strip(),
                quantity_milliunits=quantity_to_milliunits(item.quantity),
                unit_price_minor=money_to_minor(item.unit_price, "單價"),
                position=position,
            )
        )
    db.commit()
    return quote_to_dict(_load_quote(db, quote.id))


def list_quotes(db: Session) -> list[dict[str, Any]]:
    quotes = db.scalars(
        select(Quote)
        .options(selectinload(Quote.items))
        .order_by(Quote.quote_date.desc(), Quote.created_at.desc())
    ).all()
    return [quote_to_dict(quote) for quote in quotes]


def delete_quote(db: Session, item_id: str) -> None:
    quote = _load_quote(db, item_id)
    db.delete(quote)
    db.commit()


def duplicate_quote(db: Session, item_id: str) -> dict[str, Any]:
    source = _load_quote(db, item_id)
    base = f"{source.quote_number}-COPY"
    number = base
    counter = 2
    while db.scalar(select(Quote).where(Quote.quote_number == number)):
        number = f"{base}-{counter}"
        counter += 1
    payload = QuoteCreate(
        quote_number=number,
        client_name=source.client_name,
        quote_date=date.today(),
        tax_rate_percent=Decimal(source.tax_rate_bps) / Decimal(100),
        deposit_percent=source.deposit_percent,
        notes=source.notes,
        items=[
            {
                "description": item.description,
                "quantity": quantity_from_milliunits(item.quantity_milliunits),
                "unit_price": Decimal(item.unit_price_minor),
            }
            for item in source.items
        ],
    )
    return save_quote(db, payload)


def list_portfolio(db: Session, search: str | None = None) -> list[dict[str, Any]]:
    query = (
        select(PortfolioItem)
        .options(selectinload(PortfolioItem.media))
        .order_by(PortfolioItem.date.desc(), PortfolioItem.time.desc())
    )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                PortfolioItem.project.ilike(pattern),
                PortfolioItem.category.ilike(pattern),
                PortfolioItem.content.ilike(pattern),
            )
        )
    return [portfolio_to_dict(item) for item in db.scalars(query).all()]


def get_portfolio(db: Session, item_id: str) -> PortfolioItem:
    item = db.scalar(
        select(PortfolioItem)
        .options(selectinload(PortfolioItem.media))
        .execution_options(populate_existing=True)
        .where(PortfolioItem.id == item_id)
    )
    if not item:
        raise DomainError("找不到作品", 404, "portfolio_not_found")
    return item


def create_portfolio(db: Session, payload: PortfolioCreate) -> dict[str, Any]:
    item = PortfolioItem(
        date=payload.date,
        time=parse_time(payload.time),
        project=payload.project.strip(),
        category=payload.category.strip() or "未分類",
        content=payload.content.strip(),
    )
    db.add(item)
    db.commit()
    return portfolio_to_dict(get_portfolio(db, item.id))


def update_portfolio(db: Session, item_id: str, payload: PortfolioPatch) -> dict[str, Any]:
    item = get_portfolio(db, item_id)
    data = payload.model_dump(exclude_unset=True)
    if "date" in data:
        item.date = data["date"]
    if "time" in data:
        item.time = parse_time(data["time"])
    for field in ("project", "category", "content"):
        if field in data and data[field] is not None:
            setattr(item, field, data[field].strip())
    db.commit()
    return portfolio_to_dict(get_portfolio(db, item.id))


def delete_portfolio(db: Session, item_id: str) -> list[str]:
    item = get_portfolio(db, item_id)
    storage_keys = [media.storage_key for media in item.media]
    db.delete(item)
    db.commit()
    return storage_keys


def get_media(db: Session, media_id: str) -> PortfolioMedia:
    item = db.get(PortfolioMedia, media_id)
    if not item:
        raise DomainError("找不到圖片", 404, "media_not_found")
    return item


def dashboard(db: Session, month: str, selected_date: date) -> dict[str, Any]:
    start = month_start(month)
    end = next_month(start)
    works = db.scalars(
        select(WorkRecord).where(WorkRecord.date >= start, WorkRecord.date < end)
    ).all()
    practices = db.scalars(
        select(PracticeRecord).where(PracticeRecord.date >= start, PracticeRecord.date < end)
    ).all()
    todos = db.scalars(
        select(Todo).where(Todo.date == selected_date).order_by(Todo.time.asc())
    ).all()
    day_works = db.scalars(
        select(WorkRecord)
        .where(WorkRecord.date == selected_date)
        .order_by(WorkRecord.created_at.desc())
    ).all()
    day_practice = db.scalars(
        select(PracticeRecord)
        .where(PracticeRecord.date == selected_date)
        .order_by(PracticeRecord.created_at.desc())
    ).all()
    day_total = len(todos) + len(day_works) + len(day_practice)
    day_completed = sum(item.completed for item in todos + day_works + day_practice)
    recent_work = db.scalars(
        select(WorkRecord).order_by(WorkRecord.created_at.desc()).limit(5)
    ).all()
    recent_practice = db.scalars(
        select(PracticeRecord).order_by(PracticeRecord.created_at.desc()).limit(5)
    ).all()
    recent = sorted(
        [
            {
                "kind": "work",
                "title": item.name,
                "date": item.date.isoformat(),
                "created_at": item.created_at.isoformat(),
            }
            for item in recent_work
        ]
        + [
            {
                "kind": "practice",
                "title": item.piece,
                "date": item.date.isoformat(),
                "created_at": item.created_at.isoformat(),
            }
            for item in recent_practice
        ],
        key=lambda row: row["created_at"],
        reverse=True,
    )[:8]
    daily = (
        [{"kind": "todo", **todo_to_dict(item)} for item in todos]
        + [{"kind": "work", **work_to_dict(item)} for item in day_works]
        + [{"kind": "practice", **practice_to_dict(item)} for item in day_practice]
    )
    return {
        "month": month,
        "date": selected_date.isoformat(),
        "income": money_str(sum(item.income_minor for item in works)),
        "work_minutes": sum(item.work_minutes for item in works),
        "practice_seconds": sum(item.duration_seconds for item in practices),
        "completion_rate": completion_rate(day_total, day_completed),
        "daily": daily,
        "recent": recent,
    }


def analytics(db: Session, months: int = 6) -> list[dict[str, Any]]:
    months = max(1, min(months, 24))
    works = db.execute(
        select(WorkRecord.date, WorkRecord.income_minor, WorkRecord.work_minutes)
    ).all()
    practices = db.execute(select(PracticeRecord.date, PracticeRecord.duration_seconds)).all()
    return aggregate_months(
        [(row.date, row.income_minor, row.work_minutes) for row in works],
        [(row.date, row.duration_seconds) for row in practices],
        months,
    )


def export_data(db: Session) -> dict[str, Any]:
    return {
        "version": 1,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "works": list_works(db),
        "todos": list_todos(db),
        "practice": list_practice(db),
        "quotes": list_quotes(db),
        "portfolio": list_portfolio(db),
    }


def get_setting(db: Session, key: str, default: str = "") -> str:
    item = db.get(AppSetting, key)
    return item.value if item else default
