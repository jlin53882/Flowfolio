from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta


def month_start(month: str) -> date:
    year, month_number = (int(part) for part in month.split("-"))
    if not 1 <= month_number <= 12:
        raise ValueError("月份格式錯誤")
    return date(year, month_number, 1)


def next_month(start: date) -> date:
    return date(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1)


def month_end(month: str) -> date:
    return next_month(month_start(month)) - timedelta(days=1)


def completion_rate(total: int, completed: int) -> int:
    if total <= 0:
        return 0
    return round(completed / total * 100)


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def aggregate_months(
    works: list[tuple[date, int, int]], practice: list[tuple[date, int]], months: int = 6
) -> list[dict[str, object]]:
    """分開統計工作分鐘與練習秒數，兩者不能混算。"""
    now = datetime.now().date().replace(day=1)
    keys: list[str] = []
    for offset in range(months - 1, -1, -1):
        year = now.year
        month = now.month - offset
        while month <= 0:
            year -= 1
            month += 12
        keys.append(f"{year:04d}-{month:02d}")

    values = defaultdict(lambda: {"income": 0, "work_minutes": 0, "practice_seconds": 0})
    for item_date, income_minor, work_minutes in works:
        bucket = values[month_key(item_date)]
        bucket["income"] += income_minor
        bucket["work_minutes"] += work_minutes
    for item_date, duration_seconds in practice:
        values[month_key(item_date)]["practice_seconds"] += duration_seconds

    return [{"month": key, **values[key]} for key in keys]
