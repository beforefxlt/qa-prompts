"""
路由层测试 - 覆盖 members/documents/review/trends 的 API 端点
目标: 将整体覆盖率从 52% 提升到 80%+
"""
from uuid import uuid4, UUID
from datetime import date

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
from app.models.observation import ExamRecord, Observation, DerivedMetric


@pytest.fixture
async def route_env():
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


async def _create_member(client, name="测试成员"):
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": name,
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    return resp.json()


async def _upload_document(client, member_id):
    resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("test.jpg", b"test-image-content", "image/jpeg")},
    )
    return resp.json()


# ==================== Members Router Tests ====================

@pytest.mark.asyncio
async def test_create_adult_member(route_env):
    """[TC-P1-004] 创建 member_type=adult 的成人成员"""
    client, _ = route_env
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "成人成员",
            "gender": "female",
            "date_of_birth": "1990-01-01",
            "member_type": "adult",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "成人成员"
    assert data["member_type"] == "adult"
    assert data["gender"] == "female"


@pytest.mark.asyncio
async def test_create_senior_member(route_env):
    """[TC-P1-005] 创建 member_type=senior 的老人成员"""
    client, _ = route_env
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "老人成员",
            "gender": "male",
            "date_of_birth": "1960-01-01",
            "member_type": "senior",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "老人成员"
    assert data["member_type"] == "senior"
    assert data["gender"] == "male"


@pytest.mark.asyncio
async def test_create_member_empty_name_returns_400(route_env):
    """[TC-P2-010] 创建成员时 name 为空应返回 400"""
    client, _ = route_env
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    # 添加了 min_length=1 校验后，空姓名应返回 422
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_members_list_empty(route_env):
    """[TC-P1-016] 空成员列表应返回空数组"""
    client, _ = route_env
    resp = await client.get("/api/v1/members")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_members_list_excludes_deleted(route_env):
    """[TC-P1-019] 成员列表不应包含已软删除的成员 (验证软删除状态下列表过滤)"""
    client, _ = route_env
    m1 = await _create_member(client, "保留成员")
    m2 = await _create_member(client, "删除成员")

    await client.delete(f"/api/v1/members/{m2['id']}")

    resp = await client.get("/api/v1/members")
    members = resp.json()
    assert len(members) == 1
    assert members[0]["id"] == m1["id"]


@pytest.mark.asyncio
async def test_members_get_single(route_env):
    """[TC-P1-017] 获取单个成员详情"""
    client, _ = route_env
    member = await _create_member(client, "详情成员")

    resp = await client.get(f"/api/v1/members/{member['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "详情成员"
    assert data["gender"] == "male"
    assert data["member_type"] == "child"


@pytest.mark.asyncio
async def test_members_get_deleted_returns_404(route_env):
    """获取已删除成员应返回 404"""
    client, _ = route_env
    member = await _create_member(client, "待删成员")
    await client.delete(f"/api/v1/members/{member['id']}")

    resp = await client.get(f"/api/v1/members/{member['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_members_update_partial(route_env):
    """[TC-P1-018] 部分更新成员信息"""
    client, _ = route_env
    member = await _create_member(client, "原名")

    resp = await client.put(
        f"/api/v1/members/{member['id']}",
        json={"name": "新名", "member_type": "adult"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "新名"
    assert data["member_type"] == "adult"
    # 未更新的字段应保持不变
    assert data["gender"] == "male"


@pytest.mark.asyncio
async def test_members_update_nonexistent(route_env):
    """[TC-P2-017] 更新不存在的成员应返回 404"""
    client, _ = route_env
    resp = await client.put(
        "/api/v1/members/00000000-0000-0000-0000-000000000099",
        json={"name": "test"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_members_delete_nonexistent(route_env):
    """删除不存在的成员应返回 404"""
    client, _ = route_env
    resp = await client.delete("/api/v1/members/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404


# ==================== Documents Router Tests ====================

@pytest.mark.asyncio
async def test_document_upload_without_member_id(route_env):
    """不指定 member_id 时应自动关联第一个成员"""
    client, _ = route_env
    member = await _create_member(client)

    resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("auto.jpg", b"content", "image/jpeg")},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "uploaded"


@pytest.mark.asyncio
async def test_document_upload_no_members(route_env):
    """无成员时上传应返回 400"""
    client, _ = route_env
    resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.jpg", b"content", "image/jpeg")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_document_get_nonexistent(route_env):
    """[TC-P2-018] 获取不存在的文档应返回 404"""
    client, _ = route_env
    resp = await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_duplicate_document_returns_duplicate(route_env):
    """[TC-P2-025] 同一成员重复上传相同文件应返回 duplicate 状态"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_id = member["id"]
    
    # 第一次上传
    resp1 = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("test.jpg", b"same-image-content", "image/jpeg")},
    )
    assert resp1.status_code == 201
    assert resp1.json()["status"] == "uploaded"
    
    # 第二次上传相同内容
    resp2 = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("test.jpg", b"same-image-content", "image/jpeg")},
    )
    assert resp2.status_code == 201
    assert resp2.json()["status"] == "duplicate"
    
    # 不同成员上传相同文件应该成功
    member2 = await _create_member(client)
    resp3 = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member2["id"]},
        files={"file": ("test.jpg", b"same-image-content", "image/jpeg")},
    )
    assert resp3.status_code == 201
    assert resp3.json()["status"] == "uploaded"


@pytest.mark.asyncio
async def test_submit_ocr_nonexistent_document(route_env):
    """对不存在的文档提交 OCR 应返回 404"""
    client, _ = route_env
    resp = await client.post("/api/v1/documents/00000000-0000-0000-0000-000000000099/submit-ocr")
    assert resp.status_code == 404


# ==================== Review Router Tests ====================

@pytest.mark.asyncio
async def test_review_tasks_list_empty(route_env):
    """[TC-P1-025] 空审核任务列表应返回空数组"""
    client, _ = route_env
    resp = await client.get("/api/v1/review-tasks")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_review_task_get_nonexistent(route_env):
    """获取不存在的审核任务应返回 404"""
    client, _ = route_env
    resp = await client.get("/api/v1/review-tasks/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_review_approve_nonexistent(route_env):
    """审核不存在的任务应返回 404"""
    client, _ = route_env
    resp = await client.post("/api/v1/review-tasks/00000000-0000-0000-0000-000000000099/approve")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_review_reject_nonexistent(route_env):
    """退回不存在的任务应返回 404"""
    client, _ = route_env
    resp = await client.post("/api/v1/review-tasks/00000000-0000-0000-0000-000000000099/reject")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_review_save_draft_nonexistent(route_env):
    """保存不存在的任务草稿应返回 404"""
    client, _ = route_env
    resp = await client.post("/api/v1/review-tasks/00000000-0000-0000-0000-000000000099/save-draft")
    assert resp.status_code == 404


# ==================== Trends Router Tests ====================

@pytest.mark.asyncio
async def test_trends_empty_data(route_env):
    """无数据时趋势查询应返回空 series"""
    client, _ = route_env
    member = await _create_member(client)

    resp = await client.get(f"/api/v1/members/{member['id']}/trends?metric=axial_length")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metric"] == "axial_length"
    assert data["series"] == []
    assert data["alert_status"] == "normal"


@pytest.mark.asyncio
async def test_trends_with_data(route_env, monkeypatch):
    """[TC-P1-028] 有数据时趋势查询应返回正确的 series 和参考区间"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        exam = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 3, 1),
            baseline_age_months=84,
        )
        session.add(exam)
        await session.flush()

        session.add_all([
            Observation(
                id=uuid4(),
                exam_record_id=exam.id,
                metric_code="axial_length",
                value_numeric=24.35,
                unit="mm",
                side="left",
                is_abnormal=False,
                reference_range="23.0-24.0",
                confidence_score=0.95,
            ),
            Observation(
                id=uuid4(),
                exam_record_id=exam.id,
                metric_code="axial_length",
                value_numeric=23.32,
                unit="mm",
                side="right",
                is_abnormal=False,
                reference_range="23.0-24.0",
                confidence_score=0.95,
            ),
        ])
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/trends?metric=axial_length")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["series"]) == 2
    assert data["reference_range"] == "23.0-24.0"
    assert data["alert_status"] == "normal"


@pytest.mark.asyncio
async def test_trends_with_abnormal_data(route_env, monkeypatch):
    """异常数据时趋势查询应返回 warning 状态"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        exam = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 3, 15),
            baseline_age_months=84,
        )
        session.add(exam)
        await session.flush()

        session.add(
            Observation(
                id=uuid4(),
                exam_record_id=exam.id,
                metric_code="axial_length",
                value_numeric=26.0,
                unit="mm",
                side="left",
                is_abnormal=True,
                reference_range="23.0-24.0",
                confidence_score=0.95,
            )
        )
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/trends?metric=axial_length")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alert_status"] == "warning"


@pytest.mark.asyncio
async def test_trends_comparison_same_date_no_comparison(route_env, monkeypatch):
    """[TC-P4-025] 同一次检查的左右眼不应产生 comparison"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        # 只有 1 次检查，但有左右眼
        exam = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 3, 1),
            baseline_age_months=84,
        )
        session.add(exam)
        await session.flush()

        session.add(
            Observation(
                id=uuid4(),
                exam_record_id=exam.id,
                metric_code="axial_length",
                value_numeric=24.35,
                unit="mm",
                side="right",
                is_abnormal=False,
                confidence_score=0.95,
            )
        )
        session.add(
            Observation(
                id=uuid4(),
                exam_record_id=exam.id,
                metric_code="axial_length",
                value_numeric=23.32,
                unit="mm",
                side="left",
                is_abnormal=False,
                confidence_score=0.95,
            )
        )
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/trends?metric=axial_length")
    assert resp.status_code == 200
    data = resp.json()
    # 只有 1 次检查，不应有 comparison
    assert data["comparison"] is None
    # 但 series 应该有 2 条（左右眼）
    assert len(data["series"]) == 2


@pytest.mark.asyncio
async def test_trends_comparison_data(route_env, monkeypatch):
    """多条数据时应返回对比信息"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        for d, value in [(date(2026, 2, 1), 24.0), (date(2026, 3, 1), 24.5)]:
            exam = ExamRecord(
                id=uuid4(),
                document_id=uuid4(),
                member_id=member_uuid,
                exam_date=d,
                baseline_age_months=84,
            )
            session.add(exam)
            await session.flush()

            session.add(
                Observation(
                    id=uuid4(),
                    exam_record_id=exam.id,
                    metric_code="height",
                    value_numeric=value,
                    unit="cm",
                    is_abnormal=False,
                    confidence_score=0.95,
                )
            )
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/trends?metric=height")
    assert resp.status_code == 200
    data = resp.json()
    assert data["comparison"] is not None
    # 无 side 的指标（如身高）使用 comparison["value"] 结构
    assert data["comparison"]["value"]["delta"] == 0.5


@pytest.mark.asyncio
async def test_vision_dashboard(route_env, monkeypatch):
    """[TC-P1-021, TC-P1-022] 视力仪表盘应返回成员对应的指标数据"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        exam = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 3, 1),
            baseline_age_months=84,
        )
        session.add(exam)
        await session.flush()

        session.add(
            Observation(
                id=uuid4(),
                exam_record_id=exam.id,
                metric_code="axial_length",
                value_numeric=24.35,
                unit="mm",
                side="left",
                is_abnormal=False,
                confidence_score=0.95,
            )
        )
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/vision-dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["member_id"] == member["id"]
    assert data["member_type"] == "child"
    assert "axial_length" in data
    assert len(data["axial_length"]["series"]) == 1


@pytest.mark.asyncio
async def test_growth_dashboard(route_env, monkeypatch):
    """[TC-P1-022] 生长仪表盘应返回身高体重数据"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        exam = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 3, 1),
            baseline_age_months=84,
        )
        session.add(exam)
        await session.flush()

        session.add_all([
            Observation(
                id=uuid4(),
                exam_record_id=exam.id,
                metric_code="height",
                value_numeric=126.0,
                unit="cm",
                is_abnormal=False,
                confidence_score=0.95,
            ),
            Observation(
                id=uuid4(),
                exam_record_id=exam.id,
                metric_code="weight",
                value_numeric=25.0,
                unit="kg",
                is_abnormal=False,
                confidence_score=0.95,
            ),
        ])
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/growth-dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "height" in data
    assert "weight" in data
    assert len(data["height"]["series"]) == 1
    assert len(data["weight"]["series"]) == 1


@pytest.mark.asyncio
async def test_vision_dashboard_nonexistent_member(route_env):
    """不存在的成员视力仪表盘应返回 404"""
    client, _ = route_env
    resp = await client.get("/api/v1/members/00000000-0000-0000-0000-000000000099/vision-dashboard")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_growth_dashboard_nonexistent_member(route_env):
    """不存在的成员生长仪表盘应返回 404"""
    client, _ = route_env
    resp = await client.get("/api/v1/members/00000000-0000-0000-0000-000000000099/growth-dashboard")
    assert resp.status_code == 404


# ==================== Review Workflow Tests ====================

@pytest.mark.asyncio
async def test_review_full_workflow(route_env, monkeypatch):
    """[TC-P1-027] 完整审核流程: 上传 → OCR冲突 → 审核通过 → 写入正式表"""
    client, session_factory = route_env
    member = await _create_member(client)
    doc = await _upload_document(client, member["id"])
    doc_id = doc["document_id"]

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
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_conflict)

    # 提交 OCR
    resp = await client.post(f"/api/v1/documents/{doc_id}/submit-ocr")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rule_conflict"

    # 查看审核任务列表
    resp = await client.get("/api/v1/review-tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 1
    task_id = tasks[0]["id"]

    # 查看审核任务详情
    resp = await client.get(f"/api/v1/review-tasks/{task_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["status"] == "pending"
    assert detail["ocr_processed_items"] is not None

    # 审核通过 (带修订项)
    resp = await client.post(
        f"/api/v1/review-tasks/{task_id}/approve",
        json={
            "revised_items": [
                {"metric_code": "axial_length", "side": "left", "value_numeric": 24.50, "unit": "mm"}
            ]
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # 验证数据已入库 (使用修订后的值)
    async with session_factory() as session:
        obs = (await session.scalars(select(Observation))).all()
        assert len(obs) == 1
        assert obs[0].metric_code == "axial_length"
        assert obs[0].value_numeric == 24.50
        assert obs[0].confidence_score == 1.0  # 人工确认后锁定为 1.0


@pytest.mark.asyncio
async def test_review_reject_workflow(route_env, monkeypatch):
    """审核退回流程"""
    client, session_factory = route_env
    member = await _create_member(client)
    doc = await _upload_document(client, member["id"])
    doc_id = doc["document_id"]

    async def fake_conflict(*args, **kwargs):
        return {
            "status": "rule_conflict",
            "data": {
                "document_id": doc_id,
                "raw_json": {"exam_date": "2026-03-31"},
                "processed_items": {"exam_date": "2026-03-31", "observations": []},
                "confidence_score": 0.7,
                "rule_conflict_details": {"error": ["mock"]},
            },
        }

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_conflict)

    await client.post(f"/api/v1/documents/{doc_id}/submit-ocr")

    resp = await client.get("/api/v1/review-tasks")
    task_id = resp.json()[0]["id"]

    # 退回
    resp = await client.post(f"/api/v1/review-tasks/{task_id}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    # 验证任务不在待审核列表中
    resp = await client.get("/api/v1/review-tasks")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_review_save_draft_workflow(route_env, monkeypatch):
    """保存草稿流程"""
    client, session_factory = route_env
    member = await _create_member(client)
    doc = await _upload_document(client, member["id"])
    doc_id = doc["document_id"]

    async def fake_conflict(*args, **kwargs):
        return {
            "status": "rule_conflict",
            "data": {
                "document_id": doc_id,
                "raw_json": {"exam_date": "2026-03-31"},
                "processed_items": {"exam_date": "2026-03-31", "observations": []},
                "confidence_score": 0.7,
                "rule_conflict_details": {"error": ["mock"]},
            },
        }

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_conflict)

    await client.post(f"/api/v1/documents/{doc_id}/submit-ocr")

    resp = await client.get("/api/v1/review-tasks")
    task_id = resp.json()[0]["id"]

    # 保存草稿
    resp = await client.post(
        f"/api/v1/review-tasks/{task_id}/save-draft",
        json={"revised_items": []},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"

    # 草稿仍在待审核列表中
    resp = await client.get("/api/v1/review-tasks")
    assert len(resp.json()) == 1
    assert resp.json()[0]["status"] == "draft"


@pytest.mark.asyncio
async def test_review_approve_already_approved(route_env):
    """已审核的任务不应重复通过"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        doc = DocumentRecord(
            id=uuid4(),
            member_id=member_uuid,
            file_url="test.jpg",
            status="persisted",
        )
        session.add(doc)
        await session.flush()

        task = ReviewTask(
            id=uuid4(),
            document_id=doc.id,
            status="approved",
            audit_trail={"events": []},
        )
        session.add(task)
        await session.commit()
        task_id = str(task.id)

    resp = await client.post(f"/api/v1/review-tasks/{task_id}/approve")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_review_reject_already_approved(route_env):
    """已审核的任务不应被退回"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        doc = DocumentRecord(
            id=uuid4(),
            member_id=member_uuid,
            file_url="test.jpg",
            status="persisted",
        )
        session.add(doc)
        await session.flush()

        task = ReviewTask(
            id=uuid4(),
            document_id=doc.id,
            status="approved",
            audit_trail={"events": []},
        )
        session.add(task)
        await session.commit()
        task_id = str(task.id)

    resp = await client.post(f"/api/v1/review-tasks/{task_id}/reject")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_vision_dashboard_returns_vision_acuity_comparison(route_env, monkeypatch):
    """vision-dashboard 应返回 vision_acuity 的 comparison 字段"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        exam1 = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 1, 1),
            baseline_age_months=84,
        )
        session.add(exam1)
        await session.flush()

        exam2 = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 3, 1),
            baseline_age_months=86,
        )
        session.add(exam2)
        await session.flush()

        session.add_all([
            Observation(id=uuid4(), exam_record_id=exam1.id, metric_code="vision_acuity", value_numeric=0.8, unit="decimal", side="left", is_abnormal=False, confidence_score=1.0),
            Observation(id=uuid4(), exam_record_id=exam1.id, metric_code="vision_acuity", value_numeric=1.0, unit="decimal", side="right", is_abnormal=False, confidence_score=1.0),
            Observation(id=uuid4(), exam_record_id=exam2.id, metric_code="vision_acuity", value_numeric=0.9, unit="decimal", side="left", is_abnormal=False, confidence_score=1.0),
            Observation(id=uuid4(), exam_record_id=exam2.id, metric_code="vision_acuity", value_numeric=1.0, unit="decimal", side="right", is_abnormal=False, confidence_score=1.0),
        ])
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/vision-dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "vision_acuity" in data
    assert "comparison" in data["vision_acuity"]
    assert data["vision_acuity"]["comparison"] is not None
    assert "left" in data["vision_acuity"]["comparison"]
    assert "right" in data["vision_acuity"]["comparison"]
    assert data["vision_acuity"]["comparison"]["left"]["current"] == 0.9
    assert data["vision_acuity"]["comparison"]["left"]["previous"] == 0.8
    assert data["vision_acuity"]["comparison"]["left"]["delta"] == 0.1
    assert data["vision_acuity"]["comparison"]["right"]["current"] == 1.0
    assert data["vision_acuity"]["comparison"]["right"]["previous"] == 1.0
    assert data["vision_acuity"]["comparison"]["right"]["delta"] == 0.0


@pytest.mark.asyncio
async def test_vision_dashboard_comparison_same_date_no_comparison(route_env, monkeypatch):
    """同次检查的左右眼视力不产生 comparison"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        exam = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 3, 1),
            baseline_age_months=84,
        )
        session.add(exam)
        await session.flush()

        session.add_all([
            Observation(id=uuid4(), exam_record_id=exam.id, metric_code="vision_acuity", value_numeric=0.8, unit="decimal", side="left", is_abnormal=False, confidence_score=1.0),
            Observation(id=uuid4(), exam_record_id=exam.id, metric_code="vision_acuity", value_numeric=1.0, unit="decimal", side="right", is_abnormal=False, confidence_score=1.0),
        ])
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/vision-dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["vision_acuity"]["comparison"] is None


@pytest.mark.asyncio
async def test_vision_dashboard_acuity_string_value_comparison(route_env, monkeypatch):
    """vision_acuity 的 value 为字符串时 comparison 正确计算"""
    client, session_factory = route_env
    member = await _create_member(client)
    member_uuid = UUID(member["id"])

    async with session_factory() as session:
        exam1 = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 1, 1),
            baseline_age_months=84,
        )
        session.add(exam1)
        await session.flush()

        exam2 = ExamRecord(
            id=uuid4(),
            document_id=uuid4(),
            member_id=member_uuid,
            exam_date=date(2026, 3, 1),
            baseline_age_months=86,
        )
        session.add(exam2)
        await session.flush()

        session.add_all([
            Observation(id=uuid4(), exam_record_id=exam1.id, metric_code="vision_acuity", value_numeric=0.8, value_text="0.8", unit="decimal", side="left", is_abnormal=False, confidence_score=1.0),
            Observation(id=uuid4(), exam_record_id=exam2.id, metric_code="vision_acuity", value_numeric=0.9, value_text="0.9", unit="decimal", side="left", is_abnormal=False, confidence_score=1.0),
        ])
        await session.commit()

    resp = await client.get(f"/api/v1/members/{member['id']}/vision-dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["vision_acuity"]["comparison"] is not None
    assert data["vision_acuity"]["comparison"]["left"]["current"] == 0.9
    assert data["vision_acuity"]["comparison"]["left"]["previous"] == 0.8
    assert data["vision_acuity"]["comparison"]["left"]["delta"] == 0.1

