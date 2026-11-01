from __future__ import annotations

import io

from PIL import Image


def test_work_todo_practice_and_dashboard(client):
    work = client.post(
        "/api/v1/works",
        json={
            "date": "2026-11-02",
            "name": "網站整理",
            "type": "設計",
            "income": "12000",
            "hours": "2.5",
        },
    )
    assert work.status_code == 201
    practice = client.post(
        "/api/v1/practice",
        json={
            "date": "2026-11-02",
            "piece": "Nocturne",
            "duration_seconds": 1800,
            "notes": "慢速練習",
        },
    )
    assert practice.status_code == 201
    todo = client.post(
        "/api/v1/todos",
        json={"date": "2026-11-02", "title": "寄出檔案", "time": "14:30", "location": "家"},
    )
    assert todo.status_code == 201
    dashboard = client.get("/api/v1/dashboard?month=2026-11&selected_date=2026-11-02")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["income"] == "12000"
    assert body["work_minutes"] == 150
    assert body["practice_seconds"] == 1800
    assert body["completion_rate"] == 33


def test_quote_unique_number_duplicate_and_exports(client):
    payload = {
        "quote_number": "Q-TEST-001",
        "client_name": "測試客戶",
        "quote_date": "2026-11-02",
        "tax_rate_percent": "5",
        "deposit_percent": 30,
        "items": [{"description": "網站規劃", "quantity": "1", "unit_price": "10000"}],
    }
    created = client.post("/api/v1/quotes", json=payload)
    assert created.status_code == 201
    quote_id = created.json()["id"]
    conflict = client.post("/api/v1/quotes", json=payload)
    assert conflict.status_code == 409
    assert created.json()["totals"]["total"] == "10500"
    duplicate = client.post(f"/api/v1/quotes/{quote_id}/duplicate")
    assert duplicate.status_code == 201
    assert duplicate.json()["quote_number"] != "Q-TEST-001"
    pdf = client.get(f"/api/v1/quotes/{quote_id}/export.pdf")
    csv = client.get(f"/api/v1/quotes/{quote_id}/export.csv")
    assert pdf.status_code == 200 and pdf.headers["content-type"].startswith("application/pdf")
    assert csv.status_code == 200 and "attachment" in csv.headers["content-disposition"]


def test_portfolio_upload_is_id_based_and_validated(client):
    created = client.post(
        "/api/v1/portfolio",
        json={"date": "2026-11-02", "project": "封面設計", "category": "設計", "content": "測試"},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]
    image = Image.new("RGB", (12, 12), "#0f766e")
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    uploaded = client.post(
        f"/api/v1/portfolio/{item_id}/media",
        files={"files": ("cover.png", stream.getvalue(), "image/png")},
    )
    assert uploaded.status_code == 201
    media_url = uploaded.json()["media"][0]["url"]
    media = client.get(media_url)
    assert media.status_code == 200
    assert media.headers["content-type"] == "image/png"
