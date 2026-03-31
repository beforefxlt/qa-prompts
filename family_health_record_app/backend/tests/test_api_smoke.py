import pytest


@pytest.mark.asyncio
async def test_member_document_and_trend_flow(test_client):
    create_member_resp = await test_client.post(
        "/api/v1/members",
        json={
            "phone_or_email": "api-flow@test.com",
            "name": "小明",
            "gender": "male",
            "date_of_birth": "2020-01-01",
            "member_type": "child",
        },
    )
    assert create_member_resp.status_code == 201
    member_data = create_member_resp.json()

    list_resp = await test_client.get("/api/v1/members")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    files = {"file": ("mock.jpg", b"dummy-content", "image/jpeg")}
    upload_resp = await test_client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_data["id"]},
        files=files,
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert upload_data["status"] == "uploaded"

    trend_resp = await test_client.get(f"/api/v1/members/{member_data['id']}/trends?metric=axial_length")
    assert trend_resp.status_code == 200
    trend_data = trend_resp.json()
    assert trend_data["metric"] == "axial_length"
    assert trend_data["series"] == []
