from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from ..core.config import Settings
from ..db.models import Quote
from ..services import quote_totals


def safe_filename(value: str, fallback: str = "flowfolio") -> str:
    cleaned = re.sub(r"[^\w\-\u4e00-\u9fff ]+", "", value, flags=re.UNICODE).strip()
    return cleaned[:80] or fallback


def csv_safe(value: object) -> str:
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def quote_csv_bytes(quote: Quote) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["報價單編號", "客戶", "日期", "項目", "數量", "單價（TWD）", "小計（TWD）"])
    for item in quote.items:
        quantity = item.quantity_milliunits / 1000
        subtotal = round(quantity * item.unit_price_minor)
        writer.writerow(
            [
                csv_safe(quote.quote_number),
                csv_safe(quote.client_name),
                quote.quote_date.isoformat(),
                csv_safe(item.description),
                quantity,
                item.unit_price_minor,
                subtotal,
            ]
        )
    totals = quote_totals(quote)
    writer.writerow([])
    writer.writerow(["小計", totals["subtotal"]])
    writer.writerow(["稅額", totals["tax"]])
    writer.writerow(["總額", totals["total"]])
    writer.writerow(["訂金", totals["deposit"]])
    writer.writerow(["尾款", totals["balance"]])
    return output.getvalue().encode("utf-8-sig")


def _pdf_font(settings: Settings) -> str:
    if settings.pdf_font:
        font_path = Path(settings.pdf_font).expanduser()
        if font_path.is_file():
            try:
                pdfmetrics.registerFont(TTFont("FlowfolioCJK", str(font_path)))
                return "FlowfolioCJK"
            except Exception:
                pass
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:
        return "Helvetica"


def quote_pdf_bytes(quote: Quote, settings: Settings) -> bytes:
    output = io.BytesIO()
    document = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    font = _pdf_font(settings)
    totals = quote_totals(quote)

    document.setTitle(f"{quote.quote_number} 報價單")
    document.setFont(font, 22)
    document.drawString(48, height - 64, "Flowfolio 報價單")
    document.setFont(font, 10)
    document.drawRightString(width - 48, height - 52, f"單號：{quote.quote_number}")
    document.drawRightString(width - 48, height - 68, f"日期：{quote.quote_date.isoformat()}")
    document.drawString(48, height - 108, f"致客戶：{quote.client_name}")

    y = height - 150
    document.setFont(font, 10)
    document.line(48, y + 12, width - 48, y + 12)
    document.drawString(56, y - 4, "服務項目")
    document.drawRightString(360, y - 4, "數量")
    document.drawRightString(450, y - 4, "單價")
    document.drawRightString(width - 56, y - 4, "小計")
    y -= 28
    for item in quote.items:
        if y < 120:
            document.showPage()
            document.setFont(font, 10)
            y = height - 60
        quantity = item.quantity_milliunits / 1000
        subtotal = round(quantity * item.unit_price_minor)
        document.drawString(56, y, item.description[:48])
        document.drawRightString(360, y, f"{quantity:g}")
        document.drawRightString(450, y, f"{item.unit_price_minor:,}")
        document.drawRightString(width - 56, y, f"{subtotal:,}")
        y -= 22

    y -= 4
    document.line(320, y + 8, width - 48, y + 8)
    for label, value in (
        ("小計", totals["subtotal"]),
        ("稅額", totals["tax"]),
        ("總額", totals["total"]),
        ("訂金", totals["deposit"]),
        ("尾款", totals["balance"]),
    ):
        document.drawString(330, y - 4, label)
        document.drawRightString(width - 56, y - 4, f"TWD {value}")
        y -= 20
    if quote.notes:
        document.drawString(48, 70, f"備註：{quote.notes[:100]}")
    document.save()
    return output.getvalue()
