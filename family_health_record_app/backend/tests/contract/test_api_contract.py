from uuid import UUID
from datetime import datetime

import pytest


@pytest.mark.asyncio
async def test_api_contract_and_status_flow(test_client, monkeypatch):
    async def fake_ocr(*args, **kwargs):
        return {
            "status": "approved",
            "data": {
                "document_id": args[0] if args else None,
                "raw_json": {
                    "exam_date": "2026-03-31",
                    "institution": "Mock Hospital",
                    "observations": [
                        {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "left"},
                        {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "right"},
                    ],
                },
                "processed_items": {
                    "exam_date": "2026-03-31",
                    "institution": "Mock Hospital",
                    "observations": [
                        {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "left"},
                        {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "right"},
                    ],
                },
                "confidence_score": 0.95,
                "rule_conflict_details": None,
            },
        }

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_ocr)

    member_resp = await test_client.post(
        "/api/v1/members",
        json={
            "name": "契约成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    assert member_resp.status_code == 201
    member_data = member_resp.json()
    assert set(member_data.keys()) == {"id", "name", "gender", "date_of_birth", "member_type"}

    list_resp = await test_client.get("/api/v1/members")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    upload_resp = await test_client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_data["id"]},
        files={"file": ("contract.jpg", b"contract", "image/jpeg")},
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert "document_id" in upload_data
    assert upload_data["status"] == "uploaded"
    document_id = upload_data["document_id"]

    document_before_resp = await test_client.get(f"/api/v1/documents/{document_id}")
    assert document_before_resp.status_code == 200
    document_before_data = document_before_resp.json()
    assert set(document_before_data.keys()) == {"id", "member_id", "status", "file_url", "desensitized_url", "uploaded_at"}
    assert document_before_data["status"] == "uploaded"

    submit_resp = await test_client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    assert set(submit_data.keys()) == {"document_id", "status"}
    assert submit_data["status"] in {"rule_conflict", "persisted"}

    document_after_resp = await test_client.get(f"/api/v1/documents/{document_id}")
    assert document_after_resp.status_code == 200
    document_after_data = document_after_resp.json()
    assert document_after_data["status"] == submit_data["status"]

    trends_resp = await test_client.get(f"/api/v1/members/{member_data['id']}/trends?metric=axial_length")
    assert trends_resp.status_code == 200
    trends_data = trends_resp.json()
    assert set(trends_data.keys()) == {"metric", "series", "reference_range", "alert_status", "comparison"}
    assert trends_data["metric"] == "axial_length"

    UUID(member_data["id"])
    UUID(document_id)


@pytest.mark.asyncio
async def test_trends_nonexistent_member_returns_404(test_client):
    missing_member_id = "00000000-0000-0000-0000-000000000001"
    resp = await test_client.get(f"/api/v1/members/{missing_member_id}/trends?metric=axial_length")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_submit_ocr_idempotent_without_duplicate_observation(test_client, monkeypatch):
    async def fake_ocr(*args, **kwargs):
        return {
            "status": "approved",
            "data": {
                "document_id": args[0] if args else None,
                "raw_json": {
                    "exam_date": "2026-03-31",
                    "observations": [
                        {"metric_code": "height", "value_numeric": 126.0, "unit": "cm"},
                    ],
                },
                "processed_items": {
                    "exam_date": "2026-03-31",
                    "observations": [
                        {"metric_code": "height", "value_numeric": 126.0, "unit": "cm"},
                    ],
                },
                "confidence_score": 0.95,
                "rule_conflict_details": None,
            },
        }

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_ocr)

    member_resp = await test_client.post(
        "/api/v1/members",
        json={
            "name": "幂等成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]

    upload_resp = await test_client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("idem.jpg", b"idem", "image/jpeg")},
    )
    document_id = upload_resp.json()["document_id"]

    first_submit = await test_client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    second_submit = await test_client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    assert first_submit.status_code == 200
    assert second_submit.status_code == 200
    assert first_submit.json()["status"] == "persisted"
    assert second_submit.json()["status"] == "persisted"

    trend_resp = await test_client.get(f"/api/v1/members/{member_id}/trends?metric=height")
    assert trend_resp.status_code == 200
    trend_data = trend_resp.json()
    assert len(trend_data["series"]) == 1


@pytest.mark.asyncio
async def test_member_update(test_client):
    member_resp = await test_client.post(
        "/api/v1/members",
        json={
            "name": "更新测试成员",
            "gender": "female",
            "date_of_birth": "2020-06-15",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]

    update_resp = await test_client.put(
        f"/api/v1/members/{member_id}",
        json={"name": "更新后的名字"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "更新后的名字"


@pytest.mark.asyncio
async def test_member_soft_delete(test_client):
    member_resp = await test_client.post(
        "/api/v1/members",
        json={
            "name": "待删除成员",
            "gender": "male",
            "date_of_birth": "2015-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]

    delete_resp = await test_client.delete(f"/api/v1/members/{member_id}")
    assert delete_resp.status_code == 204

    list_resp = await test_client.get("/api/v1/members")
    assert all(m["id"] != member_id for m in list_resp.json())

    get_resp = await test_client.get(f"/api/v1/members/{member_id}")
    assert get_resp.status_code == 404
