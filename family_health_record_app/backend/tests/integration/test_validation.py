import pytest
import io
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_member_invalid_gender(test_client):
    """[TC-P2-011] 验证当性别输入非法值时被拦截。"""
    resp = await test_client.post(
        "/api/v1/members",
        json={
            "name": "Invalid Gender",
            "gender": "unknown",  # 应该是 male 或 female
            "date_of_birth": "2020-01-01",
            "member_type": "child"
        }
    )
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_create_member_future_dob(test_client):
    """[TC-P2-014] 验证当出生日期为未来时间时被拦截。"""
    resp = await test_client.post(
        "/api/v1/members",
        json={
            "name": "Future Bob",
            "gender": "male",
            "date_of_birth": "2099-01-01",
            "member_type": "child"
        }
    )
    assert resp.status_code == 422
    assert "出生日期不能是未来日期" in resp.text

@pytest.mark.asyncio
async def test_upload_unsupported_format(test_client):
    """[TC-P2-007, TC-P2-008] 验证不支持的格式（如 .txt）被拦截。"""
    # 预先创建一个成员
    m_resp = await test_client.post(
        "/api/v1/members",
        json={"name": "File Test", "gender": "male", "date_of_birth": "2010-01-01", "member_type": "child"}
    )
    member_id = m_resp.json()["id"]

    files = {"file": ("test.txt", b"some text content", "text/plain")}
    resp = await test_client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files=files
    )
    assert resp.status_code == 400
    assert "不支持的文件格式" in resp.text

@pytest.mark.asyncio
async def test_upload_empty_file(test_client):
    """[TC-P2-007] 验证上传空文件被拦截。"""
    m_resp = await test_client.post(
        "/api/v1/members",
        json={"name": "Empty File", "gender": "male", "date_of_birth": "2010-01-01", "member_type": "child"}
    )
    member_id = m_resp.json()["id"]

    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    resp = await test_client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files=files
    )
    assert resp.status_code == 400
    assert "不能为空" in resp.text
