from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MONEY_QUANTUM = Decimal("1")
QUANTITY_QUANTUM = Decimal("0.001")


@dataclass(frozen=True)
class QuoteLine:
    description: str
    quantity: Decimal
    unit_price: Decimal


@dataclass(frozen=True)
class QuoteTotals:
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    deposit: Decimal
    balance: Decimal


def parse_decimal(value: Decimal | str | int | float, field_name: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} 必須是有效數字") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} 必須是有限數字")
    return parsed


def to_money(value: Decimal | str | int | float, field_name: str = "金額") -> Decimal:
    parsed = parse_decimal(value, field_name)
    if parsed < 0:
        raise ValueError(f"{field_name} 不可為負數")
    return parsed.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def to_quantity(value: Decimal | str | int | float) -> Decimal:
    parsed = parse_decimal(value, "數量")
    if parsed < 0:
        raise ValueError("數量不可為負數")
    return parsed.quantize(QUANTITY_QUANTUM, rounding=ROUND_HALF_UP)


def money_to_minor(value: Decimal | str | int | float, field_name: str = "金額") -> int:
    return int(to_money(value, field_name))


def quantity_to_milliunits(value: Decimal | str | int | float) -> int:
    return int(to_quantity(value) * 1000)


def quantity_from_milliunits(value: int) -> Decimal:
    return (Decimal(value) / Decimal(1000)).quantize(QUANTITY_QUANTUM)


def calculate_quote(
    lines: list[QuoteLine], tax_rate_percent: Decimal | str | int | float, deposit_percent: int
) -> QuoteTotals:
    tax_rate = parse_decimal(tax_rate_percent, "稅率")
    if tax_rate < 0 or tax_rate > 100:
        raise ValueError("稅率必須介於 0% 到 100%")
    if not 0 <= deposit_percent <= 100:
        raise ValueError("訂金比例必須介於 0% 到 100%")

    subtotal = sum(
        (to_money(line.quantity * line.unit_price, "項目小計") for line in lines),
        Decimal("0"),
    ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    tax = (subtotal * tax_rate / Decimal(100)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    total = subtotal + tax
    deposit = (total * Decimal(deposit_percent) / Decimal(100)).quantize(
        MONEY_QUANTUM, rounding=ROUND_HALF_UP
    )
    return QuoteTotals(
        subtotal=subtotal, tax=tax, total=total, deposit=deposit, balance=total - deposit
    )
