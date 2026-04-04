"""
契约验证测试 - 补充默认值/边界值路径覆盖

针对 API_CONTRACT.md 中定义的数值区间约束，补充缺失的测试用例：
1. 手动录入端点未覆盖的指标（glucose, ldl, hemoglobin, hba1c）
2. PATCH /observations 端点的边界值测试

对应 API_CONTRACT.md v2.4.0 数值约束表
"""
import pytest
from uuid import uuid4
from datetime import date
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models.base import Base
from app.models.member import MemberProfile


@pytest.fixture
async def state_client():
    """返回 (client, session_factory) 联合 fixture"""
    TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        TEST_DB_URL,
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


# ==================== 手动录入 - 其他指标边界测试 ====================

@pytest.mark.asyncio
async def test_manual_exam_glucose_accepted(state_client):
    """验证血糖合理值被接受 (0.1-50.0 mmol/L)"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="血糖测试", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "institution_name": "社区医院",
        "observations": [
            {"metric_code": "glucose", "value_numeric": 5.6, "unit": "mmol/L"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 201, f"血糖正常值被拒绝: {resp.text}"


@pytest.mark.asyncio
async def test_manual_exam_glucose_too_high_rejected(state_client):
    """验证血糖过高值被拒绝 (>50.0 mmol/L) - 对应 API_CONTRACT glucose max=50.0"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="血糖过高", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "glucose", "value_numeric": 100.0, "unit": "mmol/L"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_manual_exam_glucose_too_low_rejected(state_client):
    """验证血糖过低值被拒绝 (<0.1 mmol/L) - 对应 API_CONTRACT glucose min=0.1"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="血糖过低", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "glucose", "value_numeric": 0.01, "unit": "mmol/L"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_manual_exam_ldl_accepted(state_client):
    """验证低密度脂蛋白合理值被接受 (0.1-10.0 mmol/L)"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="LDL测试", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "ldl", "value_numeric": 3.0, "unit": "mmol/L"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 201, f"LDL正常值被拒绝: {resp.text}"


@pytest.mark.asyncio
async def test_manual_exam_ldl_out_of_range(state_client):
    """验证 LDL 越界值被拒绝 - 对应 API_CONTRACT ldl 0.1-10.0"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="LDL越界", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    # 测试超过上限
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "ldl", "value_numeric": 15.0, "unit": "mmol/L"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_manual_exam_hemoglobin_accepted(state_client):
    """验证血红蛋白合理值被接受 (30-250 g/L)"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="血红蛋白测试", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "hemoglobin", "value_numeric": 135.0, "unit": "g/L"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 201, f"血红蛋白正常值被拒绝: {resp.text}"


@pytest.mark.asyncio
async def test_manual_exam_hemoglobin_out_of_range(state_client):
    """验证血红蛋白越界值被拒绝 - 对应 API_CONTRACT hemoglobin 30-250"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="血红蛋白越界", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    # 测试超过上限
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "hemoglobin", "value_numeric": 300.0, "unit": "g/L"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_manual_exam_hba1c_accepted(state_client):
    """验证糖化血红蛋白合理值被接受 (3.0-15.0%)"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="HbA1c测试", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "hba1c", "value_numeric": 5.6, "unit": "%"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 201, f"HbA1c正常值被拒绝: {resp.text}"


@pytest.mark.asyncio
async def test_manual_exam_hba1c_out_of_range(state_client):
    """验证 HbA1c 越界值被拒绝 - 对应 API_CONTRACT hba1c 3.0-15.0"""
    client, session_factory = state_client
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="HbA1c越界", gender="male", date_of_birth=date(1980, 1, 1), member_type="adult"
        ))
        await session.commit()
    
    # 测试超过上限
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "hba1c", "value_numeric": 20.0, "unit": "%"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422


# ==================== PATCH /observations 边界测试 ====================
# 注意：ObservationUpdate schema 已校验 0.0 < v <= 1000.0
# check_metric_sanity 进一步校验具体 metric_code 的范围
# 以下测试验证路由层的 metric_code 特定校验

@pytest.mark.asyncio
async def test_patch_observation_zero_rejected_by_schema(state_client):
    """验证 PATCH 观测值被 Schema 层拒绝 0 - 对应 0 < v (ObservationUpdate)"""
    client, session_factory = state_client
    
    mid = uuid4()
    eid = uuid4()
    oid = uuid4()
    
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="PATCH零值", gender="male", date_of_birth=date(2010, 1, 1), member_type="child"
        ))
        from app.models.observation import ExamRecord, Observation
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 1, 1), baseline_age_months=180))
        session.add(Observation(
            id=oid, exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm"
        ))
        await session.commit()
    
    resp = await client.patch(f"/api/v1/records/observations/{oid}", json={"value_numeric": 0})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_observation_negative_rejected_by_schema(state_client):
    """验证 PATCH 观测值被 Schema 层拒绝负数"""
    client, session_factory = state_client
    
    mid = uuid4()
    eid = uuid4()
    oid = uuid4()
    
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="PATCH负数", gender="male", date_of_birth=date(2010, 1, 1), member_type="child"
        ))
        from app.models.observation import ExamRecord, Observation
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 1, 1), baseline_age_months=180))
        session.add(Observation(
            id=oid, exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm"
        ))
        await session.commit()
    
    resp = await client.patch(f"/api/v1/records/observations/{oid}", json={"value_numeric": -10.0})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_observation_over_max_rejected_by_schema(state_client):
    """验证 PATCH 观测值被 Schema 层拒绝超过 1000"""
    client, session_factory = state_client
    
    mid = uuid4()
    eid = uuid4()
    oid = uuid4()
    
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="PATCH超限", gender="male", date_of_birth=date(2010, 1, 1), member_type="child"
        ))
        from app.models.observation import ExamRecord, Observation
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 1, 1), baseline_age_months=180))
        session.add(Observation(
            id=oid, exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm"
        ))
        await session.commit()
    
    resp = await client.patch(f"/api/v1/records/observations/{oid}", json={"value_numeric": 1001.0})
    assert resp.status_code == 422


# ==================== 创建成员默认值测试 ====================

@pytest.mark.asyncio
async def test_create_member_empty_name_rejected(state_client):
    """验证空名字被拒绝 - 对应 MemberCreate min_length=1"""
    client, session_factory = state_client
    
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "",  # 空字符串
            "gender": "male",
            "date_of_birth": "2010-01-01",
            "member_type": "child"
        }
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_member_missing_required_field(state_client):
    """验证缺少必填字段被拒绝"""
    client, session_factory = state_client
    
    # 缺少 gender
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "测试成员",
            "date_of_birth": "2010-01-01",
            "member_type": "child"
        }
    )
    assert resp.status_code == 422


# ==================== 补充说明 ====================
"""
本测试文件覆盖的契约路径：

1. 手动录入端点 (POST /manual-exams):
   - ✅ glucose: 0.1-50.0 mmol/L
   - ✅ ldl: 0.1-10.0 mmol/L  
   - ✅ hemoglobin: 30-250 g/L
   - ✅ hba1c: 3.0-15.0%
   - ✅ height: 30-250 cm (已有)
   - ✅ weight: 2-500 kg (已有)
   - ✅ axial_length: 15-35 mm (已有)

2. PATCH /observations 端点:
   - ✅ 0 < value_numeric <= 1000.0

3. 创建成员端点:
   - ✅ name min_length=1

对应 API_CONTRACT.md v2.4.0 数值约束表
"""