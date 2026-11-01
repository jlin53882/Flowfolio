from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )


class Quote(Base, TimestampMixin):
    __tablename__ = "quotes"
    __table_args__ = (
        CheckConstraint("tax_rate_bps >= 0 AND tax_rate_bps <= 10000", name="quote_tax_rate"),
        CheckConstraint(
            "deposit_percent >= 0 AND deposit_percent <= 100", name="quote_deposit_percent"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    quote_number: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quote_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    tax_rate_bps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deposit_percent: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    items: Mapped[list[QuoteItem]] = relationship(
        back_populates="quote", cascade="all, delete-orphan", order_by="QuoteItem.position"
    )
    works: Mapped[list[WorkRecord]] = relationship(back_populates="quote")


class QuoteItem(Base):
    __tablename__ = "quote_items"
    __table_args__ = (
        CheckConstraint("quantity_milliunits >= 0", name="quote_item_quantity"),
        CheckConstraint("unit_price_minor >= 0", name="quote_item_price"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    quote_id: Mapped[str] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity_milliunits: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    unit_price_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quote: Mapped[Quote] = relationship(back_populates="items")


class WorkRecord(Base, TimestampMixin):
    __tablename__ = "work_records"
    __table_args__ = (
        CheckConstraint("income_minor >= 0", name="work_income"),
        CheckConstraint("work_minutes >= 0", name="work_minutes"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    work_type: Mapped[str] = mapped_column(String(80), nullable=False, default="一般")
    income_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    work_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quote_id: Mapped[str | None] = mapped_column(
        ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True
    )

    quote: Mapped[Quote | None] = relationship(back_populates="works")


class Todo(Base, TimestampMixin):
    __tablename__ = "todos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    time: Mapped[str | None] = mapped_column(Time, nullable=True)
    location: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PracticeRecord(Base, TimestampMixin):
    __tablename__ = "practice_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    piece: Mapped[str] = mapped_column(String(200), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PortfolioItem(Base, TimestampMixin):
    __tablename__ = "portfolio_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    time: Mapped[str | None] = mapped_column(Time, nullable=True)
    project: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="未分類", nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)

    media: Mapped[list[PortfolioMedia]] = relationship(
        back_populates="portfolio_item",
        cascade="all, delete-orphan",
        order_by="PortfolioMedia.position",
    )


class PortfolioMedia(Base):
    __tablename__ = "portfolio_media"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_item_id: Mapped[str] = mapped_column(
        ForeignKey("portfolio_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    portfolio_item: Mapped[PortfolioItem] = relationship(back_populates="media")


class AppSetting(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )


class LegacyImportRun(Base):
    __tablename__ = "legacy_import_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    report_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class LegacyImportItem(Base):
    __tablename__ = "legacy_import_items"
    __table_args__ = (
        CheckConstraint(
            "category IN ('works', 'todos', 'practice', 'portfolio')", name="legacy_category"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    source_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
