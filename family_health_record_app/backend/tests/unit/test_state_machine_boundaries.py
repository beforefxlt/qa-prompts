from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.document import ReviewTask


@pytest.mark.asyncio
async def test_rule_conflict_generates_single_review_task(state_client, monkeypatch):
    client, session_factory = state_client

    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "冲突成员",
            "gender": "female",
            "date_of_birth": "2018-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("conflict.jpg", b"conflict", "image/jpeg")},
    )
    document_id = UUID(upload_resp.json()["document_id"])

    async def fake_conflict(*args, **kwargs):
        return {
            "status": "rule_conflict",
            "data": {
                "document_id": document_id,
                "raw_json": {"exam_date": "2026-03-31"},
                "processed_items": {"exam_date": "2026-03-31", "observations": []},
                "confidence_score": 0.7,
                "rule_conflict_details": {"error": ["mock conflict"]},
            },
        }

    from app.services import ocr_orchestrator as ocr_module

    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_conflict)

    first = await client.post(f"/api/v1/documents/{str(document_id)}/submit-ocr")
    second = await client.post(f"/api/v1/documents/{str(document_id)}/submit-ocr")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "rule_conflict"
    assert second.json()["status"] == "rule_conflict"

    async with session_factory() as session:
        tasks = (await session.scalars(select(ReviewTask).where(ReviewTask.document_id == document_id))).all()
        assert len(tasks) == 1


@pytest.mark.asyncio
async def test_invalid_exam_date_from_ocr_should_not_500(state_client, monkeypatch):
    client, _ = state_client

    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "日期异常成员",
            "gender": "male",
            "date_of_birth": "2018-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("invalid-date.jpg", b"invalid-date", "image/jpeg")},
    )
    document_id = UUID(upload_resp.json()["document_id"])

    async def fake_bad_payload(*args, **kwargs):
        return {
            "status": "approved",
            "data": {
                "document_id": document_id,
                "raw_json": {"exam_date": "2026/03/31"},
                "processed_items": {
                    "exam_date": "not-a-date",
                    "institution": "Mock Hospital",
                    "observations": [{"metric_code": "height", "value_numeric": 128.0, "unit": "cm"}],
                },
                "confidence_score": 0.8,
                "rule_conflict_details": None,
            },
        }

    from app.services import ocr_orchestrator as ocr_module

    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_bad_payload)

    resp = await client.post(f"/api/v1/documents/{str(document_id)}/submit-ocr")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rule_conflict"
