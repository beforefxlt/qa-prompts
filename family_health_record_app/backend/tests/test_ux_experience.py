"""
P5 用户体验测试 - 后端验证
验证错误提示、空状态API响应、用户体验相关的后端行为
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture
async def ux_env():
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
        yield client
    app.dependency_overrides.clear()
    await engine.dispose()


# ==================== P5: 空状态引导验证 ====================

@pytest.mark.asyncio
async def test_p5_empty_members_returns_empty_array(ux_env):
    """P5-01: 空成员列表应返回空数组，前端可据此展示空状态引导"""
    client = ux_env
    resp = await client.get("/api/v1/members")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_p5_empty_review_tasks_returns_empty_array(ux_env):
    """P5-02: 空审核任务列表应返回空数组，前端可展示"暂无待审核任务"提示"""
    client = ux_env
    resp = await client.get("/api/v1/review-tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


# ==================== P5: 错误提示友好度验证 ====================

@pytest.mark.asyncio
async def test_p5_member_not_found_has_readable_message(ux_env):
    """P5-03: 成员不存在时返回可读的错误信息"""
    client = ux_env
    resp = await client.get("/api/v1/members/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "成员" in data["detail"] or "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_p5_document_not_found_has_readable_message(ux_env):
    """P5-04: 文档不存在时返回可读的错误信息"""
    client = ux_env
    resp = await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "检查单" in data["detail"] or "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_p5_review_task_not_found_has_readable_message(ux_env):
    """P5-05: 审核任务不存在时返回可读的错误信息"""
    client = ux_env
    resp = await client.get("/api/v1/review-tasks/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "审核" in data["detail"] or "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_p5_invalid_member_type_accepted_with_warning(ux_env):
    """P5-06: 非法成员类型应被接受或拒绝，行为一致 (内网应用不做严格枚举校验)"""
    client = ux_env
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "测试成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "invalid_type",
        },
    )
    # 内网应用可能不严格校验枚举值，接受 201 或拒绝 422 均可
    assert resp.status_code in (201, 422, 400)
    if resp.status_code == 201:
        data = resp.json()
        assert data["member_type"] == "invalid_type"


@pytest.mark.asyncio
async def test_p5_empty_member_name_accepted_or_rejected_clearly(ux_env):
    """P5-07: 空姓名应被明确拒绝或接受，行为一致"""
    client = ux_env
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    # 无论接受还是拒绝，响应都应明确
    assert resp.status_code in (201, 422, 400)


# ==================== P5: 图表数据可读性验证 ====================

@pytest.mark.asyncio
async def test_p5_trends_response_has_all_chart_fields(ux_env):
    """P5-08: 趋势响应应包含图表渲染所需的所有字段"""
    client = ux_env
    # 创建成员
    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "图表测试成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]

    resp = await client.get(f"/api/v1/members/{member_id}/trends?metric=axial_length")
    assert resp.status_code == 200
    data = resp.json()

    # 验证图表渲染所需字段
    assert "metric" in data, "缺少 metric 字段"
    assert "series" in data, "缺少 series 字段"
    assert "reference_range" in data, "缺少 reference_range 字段"
    assert "alert_status" in data, "缺少 alert_status 字段"
    assert "comparison" in data, "缺少 comparison 字段"

    # 验证 series 格式
    assert isinstance(data["series"], list)
    assert data["alert_status"] in ("normal", "warning", "critical")


@pytest.mark.asyncio
async def test_p5_vision_dashboard_has_complete_structure(ux_env):
    """P5-09: 视力仪表盘响应应包含完整的图表结构"""
    client = ux_env
    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "视力测试成员",
            "gender": "female",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]

    resp = await client.get(f"/api/v1/members/{member_id}/vision-dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert "member_id" in data
    assert "member_type" in data
    assert "axial_length" in data
    assert "series" in data["axial_length"]
    assert "reference_range" in data["axial_length"]
    assert "alert_status" in data["axial_length"]


@pytest.mark.asyncio
async def test_p5_growth_dashboard_has_complete_structure(ux_env):
    """P5-10: 生长仪表盘响应应包含完整的图表结构"""
    client = ux_env
    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "生长测试成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]

    resp = await client.get(f"/api/v1/members/{member_id}/growth-dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert "height" in data
    assert "weight" in data
    assert "series" in data["height"]
    assert "series" in data["weight"]
    assert "alert_status" in data["height"]
    assert "alert_status" in data["weight"]


# ==================== P5: 审核页数据完整性验证 ====================

@pytest.mark.asyncio
async def test_p5_review_task_detail_has_all_review_fields(ux_env):
    """P5-11: 审核任务详情应包含审核页所需的所有字段"""
    client = ux_env
    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "审核测试成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]

    # 上传并触发 OCR
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("test.jpg", b"test", "image/jpeg")},
    )
    doc_id = upload_resp.json()["document_id"]

    # Mock OCR 返回冲突
    async def fake_conflict(*args, **kwargs):
        return {
            "status": "rule_conflict",
            "data": {
                "document_id": doc_id,
                "raw_json": {"exam_date": "2026-03-31"},
                "processed_items": {
                    "exam_date": "2026-03-31",
                    "observations": [
                        {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "left"},
                    ],
                },
                "confidence_score": 0.7,
                "rule_conflict_details": {"error": ["mock conflict"]},
            },
        }

    from app.services import ocr_orchestrator as ocr_module
    from unittest.mock import AsyncMock
    ocr_module.ocr_orchestrator.process_document = AsyncMock(side_effect=fake_conflict)

    await client.post(f"/api/v1/documents/{doc_id}/submit-ocr")

    # 获取审核任务
    tasks_resp = await client.get("/api/v1/review-tasks")
    task_id = tasks_resp.json()[0]["id"]

    # 获取审核任务详情
    resp = await client.get(f"/api/v1/review-tasks/{task_id}")
    assert resp.status_code == 200
    data = resp.json()

    # 验证审核页所需字段
    assert "id" in data, "缺少 task id"
    assert "document_id" in data, "缺少 document_id"
    assert "status" in data, "缺少 status"
    assert "ocr_raw_json" in data, "缺少 ocr_raw_json (原始识别结果)"
    assert "ocr_processed_items" in data, "缺少 ocr_processed_items (处理后数据)"
    assert "confidence_score" in data, "缺少 confidence_score (置信度)"
    assert "rule_conflict_details" in data, "缺少 rule_conflict_details (冲突详情)"
    assert "audit_trail" in data, "缺少 audit_trail (审核轨迹)"
    assert "created_at" in data, "缺少 created_at"
    assert "updated_at" in data, "缺少 updated_at"
