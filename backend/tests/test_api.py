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
    goal = client.post(
        "/api/v1/goals",
        json={
            "title": "完成閱讀計畫",
            "category": "學習",
            "target_value": "10",
            "current_value": "3",
            "unit": "本",
            "due_date": "2026-11-02",
        },
    )
    assert goal.status_code == 201
    dashboard = client.get("/api/v1/dashboard?month=2026-11&selected_date=2026-11-02")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["income"] == "12000"
    assert body["work_minutes"] == 150
    assert body["practice_seconds"] == 1800
    assert body["completion_rate"] == 25
    goal_items = [item for item in body["daily"] if item["kind"] == "goal"]
    assert len(goal_items) == 1
    assert goal_items[0]["title"] == "完成閱讀計畫"
    assert goal_items[0]["current_value"] == "3"


def test_work_can_be_recorded_for_an_entire_month(client):
    response = client.post(
        "/api/v1/works",
        json={
            "month": "2026-11",
            "day": 0,
            "name": "整月志工服務",
            "type": "志工",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["month"] == "2026-11"
    assert body["day"] == 0
    assert body["date"] == "2026-11-01"
    assert body["income"] == "0"
    assert body["hours"] == "0"


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


def test_goal_progress_can_be_manually_updated_and_completed(client):
    created = client.post(
        "/api/v1/goals",
        json={
            "title": "完成閱讀計畫",
            "category": "學習",
            "description": "每週讀完一本書",
            "target_value": "10",
            "current_value": "2.5",
            "unit": "本",
            "due_date": "2026-12-31",
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "active"
    assert created.json()["progress_percent"] == 25
    goal_id = created.json()["id"]

    simple = client.post(
        "/api/v1/goals",
        json={"title": "整理生活清單", "category": "生活", "due_date": "2026-12-01"},
    )
    assert simple.status_code == 201
    assert simple.json()["current_value"] == "0"
    assert simple.json()["target_value"] == "1"
    assert simple.json()["unit"] == "項"

    progressed = client.post(
        f"/api/v1/goals/{goal_id}/progress",
        json={"current_value": "10", "record_date": "2026-11-03", "note": "完成最後一本"},
    )
    assert progressed.status_code == 200
    assert progressed.json()["status"] == "completed"
    assert progressed.json()["progress_percent"] == 100
    assert progressed.json()["completed_at"]
    assert progressed.json()["progress_logs"][0]["note"] == "完成最後一本"

    completed = client.get("/api/v1/goals?status=completed")
    assert completed.status_code == 200
    assert [item["id"] for item in completed.json()] == [goal_id]


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
