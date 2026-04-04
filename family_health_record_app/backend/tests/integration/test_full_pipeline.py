"""
全链路集成测试 — 使用真实测试图片 01.jpg
覆盖：创建成员 → 上传图片 → 提交OCR → 审核通过 → 趋势查询 → Dashboard 数据验证

这个测试模拟真实用户从上传检查单到看到数据的完整流程。
OCR 结果被 mock（避免依赖外部 AI 服务），但图片上传、文件存储、审核流程、数据持久化全部走真实代码路径。
"""
import os
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models.base import Base
from app.models.member import MemberProfile
from app.models.document import DocumentRecord
from app.models.observation import ExamRecord, Observation

# 测试图片路径
TEST_IMAGE_PATH = Path(__file__).parent.parent / "01.jpg"


@pytest.fixture
async def full_pipeline_env():
    """完整的测试环境，包含数据库和 HTTP 客户端。"""
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


@pytest.mark.asyncio
async def test_full_pipeline_upload_to_dashboard(full_pipeline_env, monkeypatch):
    """
    [TC-INT-001] 全链路集成测试：使用真实图片 01.jpg
    流程：创建成员 → 上传 01.jpg → 提交 OCR → 审核通过 → 查询趋势 → 验证 Dashboard 数据
    """
    client, session_factory = full_pipeline_env

    # 验证测试图片存在
    assert TEST_IMAGE_PATH.exists(), f"测试图片不存在: {TEST_IMAGE_PATH}"
    image_size = TEST_IMAGE_PATH.stat().st_size
    assert image_size > 0, "测试图片为空"

    # ========== Step 1: 创建成员 ==========
    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "小明",
            "gender": "male",
            "date_of_birth": "2018-06-15",
            "member_type": "child",
        },
    )
    assert member_resp.status_code == 201
    member = member_resp.json()
    member_id = member["id"]
    assert member["name"] == "小明"
    assert member["member_type"] == "child"

    # ========== Step 2: 上传真实图片 01.jpg ==========
    with open(TEST_IMAGE_PATH, "rb") as f:
        upload_resp = await client.post(
            "/api/v1/documents/upload",
            data={"member_id": member_id},
            files={"file": ("01.jpg", f, "image/jpeg")},
        )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    doc_id = upload_data["document_id"]
    assert upload_data["status"] == "uploaded"

    # 验证文件已存储（有 file_url）
    assert upload_data["file_url"], "上传后应返回 file_url"

    # ========== Step 3: Mock OCR 结果并提交 ==========
    # Mock OCR 返回真实医疗数据（模拟 01.jpg 的识别结果）
    async def fake_ocr_approved(*args, **kwargs):
        return {
            "status": "approved",
            "data": {
                "document_id": doc_id,
                "raw_json": {"exam_date": "2026-04-01"},
                "processed_items": {
                    "exam_date": "2026-04-01",
                    "observations": [
                        {"metric_code": "axial_length", "value_numeric": 23.50, "unit": "mm", "side": "left"},
                        {"metric_code": "axial_length", "value_numeric": 23.80, "unit": "mm", "side": "right"},
                        {"metric_code": "vision_acuity", "value_numeric": 0.8, "unit": "", "side": "left"},
                        {"metric_code": "vision_acuity", "value_numeric": 0.7, "unit": "", "side": "right"},
                        {"metric_code": "height", "value_numeric": 125.5, "unit": "cm"},
                        {"metric_code": "weight", "value_numeric": 24.3, "unit": "kg"},
                    ],
                },
                "confidence_score": 0.92,
                "rule_conflict_details": None,
            },
        }

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_ocr_approved)

    submit_resp = await client.post(f"/api/v1/documents/{doc_id}/submit-ocr")
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    # approved 状态直接持久化，文档状态变为 persisted
    assert submit_data["status"] == "persisted"

    # ========== Step 4: 验证数据已持久化 ==========
    async with session_factory() as session:
        # 验证 ExamRecord 已创建
        records = (await session.scalars(select(ExamRecord))).all()
        assert len(records) == 1
        record = records[0]
        assert str(record.member_id) == member_id
        assert record.exam_date.isoformat() == "2026-04-01"

        # 验证 Observations 已创建
        observations = (await session.scalars(select(Observation))).all()
        assert len(observations) == 6

        # 验证眼轴数据（左右眼）
        axial_obs = [o for o in observations if o.metric_code == "axial_length"]
        assert len(axial_obs) == 2
        left_axial = next(o for o in axial_obs if o.side == "left")
        right_axial = next(o for o in axial_obs if o.side == "right")
        assert left_axial.value_numeric == 23.50
        assert right_axial.value_numeric == 23.80

        # 验证身高体重
        height_obs = next(o for o in observations if o.metric_code == "height")
        assert height_obs.value_numeric == 125.5
        weight_obs = next(o for o in observations if o.metric_code == "weight")
        assert weight_obs.value_numeric == 24.3

    # ========== Step 5: 查询趋势数据 ==========
    trend_resp = await client.get(
        f"/api/v1/members/{member_id}/trends?metric=axial_length"
    )
    assert trend_resp.status_code == 200
    trend_data = trend_resp.json()
    assert trend_data["metric"] == "axial_length"
    assert len(trend_data["series"]) == 2  # 左右眼各一条

    # 验证趋势数据包含左右眼
    sides = {s["side"] for s in trend_data["series"]}
    assert "left" in sides
    assert "right" in sides

    # ========== Step 6: 查询 Dashboard 数据 ==========
    vision_resp = await client.get(
        f"/api/v1/members/{member_id}/vision-dashboard"
    )
    assert vision_resp.status_code == 200
    vision_data = vision_resp.json()
    assert vision_data["member_type"] == "child"
    assert len(vision_data["axial_length"]["series"]) == 2
    assert len(vision_data["vision_acuity"]["series"]) == 2

    growth_resp = await client.get(
        f"/api/v1/members/{member_id}/growth-dashboard"
    )
    assert growth_resp.status_code == 200
    growth_data = growth_resp.json()
    assert len(growth_data["height"]["series"]) == 1
    assert len(growth_data["weight"]["series"]) == 1

    # ========== Step 7: 验证成员列表中的 last_check_date ==========
    list_resp = await client.get("/api/v1/members")
    assert list_resp.status_code == 200
    members = list_resp.json()
    assert len(members) == 1
    assert members[0]["last_check_date"] == "2026-04-01"
    assert members[0]["pending_review_count"] == 0  # approved 状态无待审核


@pytest.mark.asyncio
async def test_full_pipeline_with_review_workflow(full_pipeline_env, monkeypatch):
    """
    [TC-INT-002] 全链路集成测试：带审核流程
    流程：创建成员 → 上传 01.jpg → 提交 OCR（产生 rule_conflict）→ 审核通过 → 验证数据
    """
    client, session_factory = full_pipeline_env

    assert TEST_IMAGE_PATH.exists(), f"测试图片不存在: {TEST_IMAGE_PATH}"

    # ========== Step 1: 创建成员 ==========
    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "小红",
            "gender": "female",
            "date_of_birth": "2019-03-20",
            "member_type": "child",
        },
    )
    assert member_resp.status_code == 201
    member_id = member_resp.json()["id"]

    # ========== Step 2: 上传真实图片 ==========
    with open(TEST_IMAGE_PATH, "rb") as f:
        upload_resp = await client.post(
            "/api/v1/documents/upload",
            data={"member_id": member_id},
            files={"file": ("01.jpg", f, "image/jpeg")},
        )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["document_id"]

    # ========== Step 3: Mock OCR 返回 rule_conflict（需要审核）==========
    async def fake_ocr_conflict(*args, **kwargs):
        return {
            "status": "rule_conflict",
            "data": {
                "document_id": doc_id,
                "raw_json": {"exam_date": "2026-04-02"},
                "processed_items": {
                    "exam_date": "2026-04-02",
                    "observations": [
                        {"metric_code": "axial_length", "value_numeric": 24.00, "unit": "mm", "side": "left"},
                        {"metric_code": "axial_length", "value_numeric": 24.20, "unit": "mm", "side": "right"},
                        {"metric_code": "height", "value_numeric": 128.0, "unit": "cm"},
                    ],
                },
                "confidence_score": 0.72,
                "rule_conflict_details": {"warning": ["数值超出正常范围"]},
            },
        }

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_ocr_conflict)

    submit_resp = await client.post(f"/api/v1/documents/{doc_id}/submit-ocr")
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "rule_conflict"

    # ========== Step 4: 验证待审核任务已创建 ==========
    tasks_resp = await client.get("/api/v1/review-tasks")
    assert tasks_resp.status_code == 200
    tasks = tasks_resp.json()
    assert len(tasks) == 1
    task_id = tasks[0]["id"]
    assert tasks[0]["status"] == "pending"

    # 验证成员有待审核计数（使用 list 接口，返回 MemberResponse 包含 pending_review_count）
    list_resp = await client.get("/api/v1/members")
    assert list_resp.status_code == 200
    members = list_resp.json()
    test_member = next(m for m in members if m["id"] == member_id)
    assert test_member["pending_review_count"] == 1

    # ========== Step 5: 查看审核任务详情 ==========
    detail_resp = await client.get(f"/api/v1/review-tasks/{task_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["status"] == "pending"
    assert detail["confidence_score"] == 0.72
    assert len(detail["ocr_processed_items"]["observations"]) == 3

    # ========== Step 6: 审核通过（带修订）==========
    approve_resp = await client.post(
        f"/api/v1/review-tasks/{task_id}/approve",
        json={
            "revised_items": [
                {"metric_code": "axial_length", "side": "left", "value_numeric": 24.10, "unit": "mm"},
                {"metric_code": "axial_length", "side": "right", "value_numeric": 24.30, "unit": "mm"},
                {"metric_code": "height", "value_numeric": 128.5, "unit": "cm"},
            ]
        },
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # ========== Step 7: 验证审核通过后数据已持久化 ==========
    # 待审核计数归零（使用 list 接口）
    list_resp = await client.get("/api/v1/members")
    assert list_resp.status_code == 200
    members = list_resp.json()
    test_member = next(m for m in members if m["id"] == member_id)
    assert test_member["pending_review_count"] == 0

    # 审核任务不在待审核列表中
    tasks_resp = await client.get("/api/v1/review-tasks")
    assert len(tasks_resp.json()) == 0

    # 数据已入库
    async with session_factory() as session:
        observations = (await session.scalars(select(Observation))).all()
        assert len(observations) == 3

        # 验证使用的是修订后的值
        left_axial = next(o for o in observations if o.metric_code == "axial_length" and o.side == "left")
        assert left_axial.value_numeric == 24.10  # 修订值
        assert left_axial.confidence_score == 1.0  # 人工确认后锁定

    # ========== Step 8: 趋势数据验证 ==========
    trend_resp = await client.get(
        f"/api/v1/members/{member_id}/trends?metric=axial_length"
    )
    assert trend_resp.status_code == 200
    trend_data = trend_resp.json()
    assert len(trend_data["series"]) == 2

    # ========== Step 9: 重复上传检测 ==========
    with open(TEST_IMAGE_PATH, "rb") as f:
        dup_resp = await client.post(
            "/api/v1/documents/upload",
            data={"member_id": member_id},
            files={"file": ("01.jpg", f, "image/jpeg")},
        )
    assert dup_resp.status_code == 201
    assert dup_resp.json()["status"] == "duplicate"
