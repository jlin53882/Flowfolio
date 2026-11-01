from __future__ import annotations

from datetime import date as DateType
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkCreate(StrictModel):
    date: DateType = Field(default_factory=DateType.today)
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(default="一般", min_length=1, max_length=80)
    income: Decimal = Field(default=Decimal("0"), ge=0)
    hours: Decimal = Field(default=Decimal("0"), ge=0, le=10000)
    notes: str = Field(default="", max_length=5000)
    quote_id: str | None = None
    completed: bool = False


class WorkPatch(StrictModel):
    date: DateType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    type: str | None = Field(default=None, min_length=1, max_length=80)
    income: Decimal | None = Field(default=None, ge=0)
    hours: Decimal | None = Field(default=None, ge=0, le=10000)
    notes: str | None = Field(default=None, max_length=5000)
    quote_id: str | None = None
    completed: bool | None = None


class TodoCreate(StrictModel):
    date: DateType = Field(default_factory=DateType.today)
    time: str | None = Field(default=None, max_length=5)
    location: str = Field(default="", max_length=200)
    title: str = Field(min_length=1, max_length=200)
    completed: bool = False

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value:
            parts = value.split(":")
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                raise ValueError("時間格式必須是 HH:MM")
            hour, minute = map(int, parts)
            if not 0 <= hour <= 23 or not 0 <= minute <= 59:
                raise ValueError("時間格式必須是 HH:MM")
        return value


class TodoPatch(StrictModel):
    date: DateType | None = None
    time: str | None = Field(default=None, max_length=5)
    location: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    completed: bool | None = None


class PracticeCreate(StrictModel):
    date: DateType = Field(default_factory=DateType.today)
    piece: str = Field(min_length=1, max_length=200)
    duration_seconds: int = Field(ge=0, le=24 * 60 * 60)
    notes: str = Field(default="", max_length=5000)
    completed: bool = True


class PracticePatch(StrictModel):
    date: DateType | None = None
    piece: str | None = Field(default=None, min_length=1, max_length=200)
    duration_seconds: int | None = Field(default=None, ge=0, le=24 * 60 * 60)
    notes: str | None = Field(default=None, max_length=5000)
    completed: bool | None = None


class QuoteItemInput(StrictModel):
    description: str = Field(min_length=1, max_length=300)
    quantity: Decimal = Field(gt=0, le=1_000_000)
    unit_price: Decimal = Field(ge=0, le=100_000_000)


class QuoteCreate(StrictModel):
    quote_number: str = Field(min_length=1, max_length=80)
    client_name: str = Field(min_length=1, max_length=200)
    quote_date: DateType = Field(default_factory=DateType.today)
    tax_rate_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    deposit_percent: int = Field(default=30, ge=0, le=100)
    notes: str = Field(default="", max_length=5000)
    items: list[QuoteItemInput] = Field(min_length=1, max_length=100)


class QuotePatch(QuoteCreate):
    pass


class PortfolioCreate(StrictModel):
    date: DateType = Field(default_factory=DateType.today)
    time: str | None = Field(default=None, max_length=5)
    project: str = Field(min_length=1, max_length=200)
    category: str = Field(default="未分類", max_length=100)
    content: str = Field(default="", max_length=10000)


class PortfolioPatch(StrictModel):
    date: DateType | None = None
    time: str | None = Field(default=None, max_length=5)
    project: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=100)
    content: str | None = Field(default=None, max_length=10000)


class BackupResponse(StrictModel):
    created_at: str
    file_count: int
    database_sha256: str
    archive_name: str
