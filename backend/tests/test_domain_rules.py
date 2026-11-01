from decimal import Decimal

from app.domain.metrics import aggregate_months, completion_rate
from app.domain.pricing import QuoteLine, calculate_quote


def test_quote_rounding_and_deposit_are_authoritative():
    totals = calculate_quote(
        [
            QuoteLine("設計", Decimal("2"), Decimal("1000")),
            QuoteLine("校稿", Decimal("1"), Decimal("333")),
        ],
        Decimal("5"),
        30,
    )
    assert totals.subtotal == Decimal("2333")
    assert totals.tax == Decimal("117")
    assert totals.total == Decimal("2450")
    assert totals.deposit == Decimal("735")
    assert totals.balance == Decimal("1715")


def test_dashboard_does_not_mix_work_minutes_and_practice_seconds():
    rows = aggregate_months(
        [(__import__("datetime").date(2026, 11, 2), 5000, 90)],
        [(__import__("datetime").date(2026, 11, 2), 1800)],
        months=1,
    )
    assert rows[0]["income"] == 5000
    assert rows[0]["work_minutes"] == 90
    assert rows[0]["practice_seconds"] == 1800


def test_completion_rate_empty_and_normal():
    assert completion_rate(0, 0) == 0
    assert completion_rate(4, 3) == 75
