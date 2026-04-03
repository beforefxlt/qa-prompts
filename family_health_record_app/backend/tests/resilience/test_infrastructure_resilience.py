"""
P3 基建容灾测试
覆盖: MinIO 不可用、OCR 超时、磁盘权限异常、网络断开
"""
import io
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models.base import Base
from app.models.member import MemberProfile
from app.models.document import DocumentRecord, OCRExtractionResult, ReviewTask


@pytest.fixture
async def test_env():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory
    app.dependency_overrides.clear()
    await engine.dispose()


async def _create_member(client):
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "容灾测试成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    return resp.json()["id"]


async def _upload_document(client, member_id, content=b"dummy"):
    resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("test.jpg", content, "image/jpeg")},
    )
    return resp.json()["document_id"]


@pytest.mark.asyncio
async def test_ocr_timeout_returns_error(test_env, monkeypatch):
    """[TC-P3-003] OCR 接口超时 (>30s) 应返回 500 错误，不阻塞主流程。"""
    client, session_factory = test_env
    member_id = await _create_member(client)
    document_id = await _upload_document(client, member_id)

    # Return error dict (simulating what the orchestrator does after catching TimeoutError)
    async def fake_timeout(*args, **kwargs):
        return {
            "status": "error",
            "message": "AI Processing Timeout: OCR API timeout after 30s",
        }

    from app.services.ocr_orchestrator import ocr_orchestrator
    monkeypatch.setattr(ocr_orchestrator, "process_document", fake_timeout)

    resp = await client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    assert resp.status_code == 500
    assert "timeout" in resp.text.lower() or "failed" in resp.text.lower()


@pytest.mark.asyncio
async def test_ocr_api_unavailable_returns_error(test_env, monkeypatch):
    """[TC-P3-005] OCR 服务完全不可用时应返回 500 错误。"""
    client, session_factory = test_env
    member_id = await _create_member(client)
    document_id = await _upload_document(client, member_id)

    async def fake_unavailable(*args, **kwargs):
        return {
            "status": "error",
            "message": "AI 识别服务连接异常",
        }

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_unavailable)

    resp = await client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    assert resp.status_code == 500


    # 文档记录已创建，状态为 uploaded
    resp = await client.get(f"/api/v1/documents/{document_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "uploaded"


@pytest.mark.asyncio
async def test_upload_unsupported_format_returns_400(test_env):
    """[TC-P2-007, TC-P2-008] 上传 .txt/.docx/.bmp 等非支持格式应返回 400"""
    client, session_factory = test_env
    member_id = await _create_member(client)
    
    # 测试 .txt 格式
    resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("test.txt", b"text content", "text/plain")},
    )
    # 现在已补齐拦截逻辑，应返回 400
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_empty_file_returns_400(test_env):
    """[TC-P2-007] 上传 0 字节文件应返回 400"""
    client, session_factory = test_env
    member_id = await _create_member(client)
    
    # 上传空文件
    resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    # 现在已补齐拦截逻辑，应返回 400
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_desensitize_non_image_returns_original(test_env, monkeypatch):
    """脱敏函数对非图片数据应返回原始字节，不抛出异常。"""
    from app.services.image_processor import desensitize_image

    result = desensitize_image(b"not an image at all")
    assert result == b"not an image at all"


@pytest.mark.asyncio
async def test_concurrent_upload_unique_filenames(test_env):
    """并发上传同名文件应生成唯一文件名，不互相覆盖。"""
    client, session_factory = test_env
    member_id = await _create_member(client)

    # 上传两个同名文件
    resp1 = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("same_name.jpg", b"content1", "image/jpeg")},
    )
    resp2 = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("same_name.jpg", b"content2", "image/jpeg")},
    )

    assert resp1.status_code == 201
    assert resp2.status_code == 201

    doc1_id = resp1.json()["document_id"]
    doc2_id = resp2.json()["document_id"]

    # 两个文档 ID 不同
    assert doc1_id != doc2_id

    # 两个文档的 file_url 不同
    doc1 = await client.get(f"/api/v1/documents/{doc1_id}")
    doc2 = await client.get(f"/api/v1/documents/{doc2_id}")
    assert doc1.json()["file_url"] != doc2.json()["file_url"]


@pytest.mark.asyncio
async def test_submit_ocr_on_nonexistent_document_returns_404(test_env):
    """对不存在的文档提交 OCR 应返回 404。"""
    client, session_factory = test_env
    fake_id = "00000000-0000-0000-0000-000000000099"
    resp = await client.post(f"/api/v1/documents/{fake_id}/submit-ocr")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_review_task_idempotent(test_env, monkeypatch):
    """同一文档重复提交 OCR 不应创建多个 review_task。"""
    client, session_factory = test_env
    member_id = await _create_member(client)
    document_id = await _upload_document(client, member_id)

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

    # 重复提交 3 次
    for _ in range(3):
        resp = await client.post(f"/api/v1/documents/{document_id}/submit-ocr")
        assert resp.status_code == 200

    # 验证只创建了 1 个 review_task
    async with session_factory() as session:
        from uuid import UUID
        tasks = (await session.scalars(
            select(ReviewTask).where(ReviewTask.document_id == UUID(document_id))
        )).all()
        assert len(tasks) == 1


@pytest.mark.asyncio
async def test_member_not_found_returns_404(test_env):
    """查询不存在的成员应返回 404。"""
    client, session_factory = test_env
    fake_id = "00000000-0000-0000-0000-000000000001"

    resp = await client.get(f"/api/v1/members/{fake_id}")
    assert resp.status_code == 404

    resp = await client.put(f"/api/v1/members/{fake_id}", json={"name": "test"})
    assert resp.status_code == 404

    resp = await client.delete(f"/api/v1/members/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_deleted_member_not_in_list(test_env):
    """软删除的成员不应出现在成员列表中。"""
    client, session_factory = test_env
    member_id = await _create_member(client)

    # 确认在列表中
    resp = await client.get("/api/v1/members")
    assert len(resp.json()) == 1

    # 删除
    resp = await client.delete(f"/api/v1/members/{member_id}")
    assert resp.status_code == 204

    # 确认不在列表中
    resp = await client.get("/api/v1/members")
    assert len(resp.json()) == 0

    # 但直接查询仍返回 404（因为 is_deleted=true）
    resp = await client.get(f"/api/v1/members/{member_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_empty_member_name_rejected(test_env):
    """[TC-P2-010] 空姓名的成员创建请求应被拒绝 (422)。"""
    client, session_factory = test_env
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    assert resp.status_code == 422
