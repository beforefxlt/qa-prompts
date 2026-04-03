import pytest
from uuid import uuid4
from datetime import date, timedelta
from sqlalchemy import select

from app.models.member import MemberProfile
from app.models.observation import ExamRecord, Observation


# ==================== CREATE 测试 ====================

@pytest.mark.asyncio
async def test_manual_exam_creation(route_env):
    """验证手动录入功能"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="手动测试员", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "institution_name": "测试机构",
        "observations": [
            {"metric_code": "height", "value_numeric": 125.5, "unit": "cm", "side": None}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 201
    
    async with session_factory() as session:
        exams = (await session.scalars(select(ExamRecord))).all()
        assert len(exams) == 1
        assert exams[0].document_id is None
        obs = (await session.scalars(select(Observation))).all()
        assert len(obs) == 1
        assert obs[0].value_numeric == 125.5

@pytest.mark.asyncio
async def test_manual_exam_multi_observations(route_env):
    """验证多指标同时录入（含左右眼）"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="多指标测试", gender="female", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "institution_name": "儿童医院",
        "observations": [
            {"metric_code": "height", "value_numeric": 125.5, "unit": "cm", "side": None},
            {"metric_code": "weight", "value_numeric": 25.0, "unit": "kg", "side": None},
            {"metric_code": "axial_length", "value_numeric": 23.5, "unit": "mm", "side": "left"},
            {"metric_code": "axial_length", "value_numeric": 23.2, "unit": "mm", "side": "right"},
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 201
    
    async with session_factory() as session:
        obs = (await session.scalars(select(Observation))).all()
        assert len(obs) == 4
        metrics = {o.metric_code: o for o in obs}
        assert metrics["height"].value_numeric == 125.5
        assert metrics["weight"].value_numeric == 25.0
        assert metrics["axial_length"].side in ("left", "right")

@pytest.mark.asyncio
async def test_manual_exam_member_not_found(route_env):
    """验证成员不存在时返回 404"""
    client, _ = route_env
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "height", "value_numeric": 125.5, "unit": "cm"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{uuid4()}/manual-exams", json=payload)
    assert resp.status_code == 404
    assert "成员资料不存在" in resp.text

@pytest.mark.asyncio
async def test_manual_exam_deleted_member(route_env):
    """验证对已删除成员录入返回 400"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="已删除成员", gender="male", date_of_birth=date(2018, 1, 1),
            member_type="child", is_deleted=True
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "height", "value_numeric": 125.5, "unit": "cm"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 400
    assert "成员已删除" in resp.text

@pytest.mark.asyncio
async def test_manual_exam_future_date_rejected(route_env):
    """验证未来日期被拒绝"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="日期测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    future_date = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "exam_date": future_date,
        "observations": [
            {"metric_code": "height", "value_numeric": 125.5, "unit": "cm"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422
    assert "不能晚于当前系统时间" in resp.text


# ==================== SANITY CHECK 测试 ====================

@pytest.mark.asyncio
async def test_manual_exam_sanity_check_height(route_env):
    """验证身高合理性校验 (30-250cm)"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="拦截测试", gender="female", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "height", "value_numeric": 1000.0, "unit": "cm"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422
    assert "超出常规合理范围" in resp.text

@pytest.mark.asyncio
async def test_manual_exam_sanity_check_height_too_low(route_env):
    """验证身高过低值被拒绝 (<30cm)"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="低值测试", gender="female", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "height", "value_numeric": 10.0, "unit": "cm"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_manual_exam_sanity_check_axial_length(route_env):
    """验证眼轴合理性校验 (15-35mm)"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="眼轴测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "axial_length", "value_numeric": 100.0, "unit": "mm"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422
    assert "超出常规合理范围" in resp.text

@pytest.mark.asyncio
async def test_manual_exam_sanity_check_weight(route_env):
    """验证体重合理性校验 (2-500kg)"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="体重测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "weight", "value_numeric": 0.5, "unit": "kg"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422
    assert "超出常规合理范围" in resp.text

@pytest.mark.asyncio
async def test_manual_exam_boundary_values_accepted(route_env):
    """验证边界值被接受（身高30和250，眼轴15和35，体重2和500）"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="边界测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "height", "value_numeric": 30.0, "unit": "cm"},
            {"metric_code": "height", "value_numeric": 250.0, "unit": "cm"},
            {"metric_code": "axial_length", "value_numeric": 15.0, "unit": "mm"},
            {"metric_code": "axial_length", "value_numeric": 35.0, "unit": "mm"},
            {"metric_code": "weight", "value_numeric": 2.0, "unit": "kg"},
            {"metric_code": "weight", "value_numeric": 500.0, "unit": "kg"},
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 201


# ==================== 默认值/零值拦截测试 (BUG-034 回归) ====================

@pytest.mark.asyncio
async def test_manual_exam_zero_value_rejected(route_env):
    """验证 value_numeric=0 被拒绝（前端默认值场景回归测试）"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="零值测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "height", "value_numeric": 0, "unit": "cm"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422
    assert "超出常规合理范围" in resp.text


@pytest.mark.asyncio
async def test_manual_exam_negative_value_rejected(route_env):
    """验证负数值被拒绝"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="负值测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        await session.commit()
    
    payload = {
        "exam_date": "2026-04-01",
        "observations": [
            {"metric_code": "height", "value_numeric": -10.0, "unit": "cm"}
        ]
    }
    resp = await client.post(f"/api/v1/records/members/{mid}/manual-exams", json=payload)
    assert resp.status_code == 422


# ==================== UPDATE (PATCH) 测试 ====================

@pytest.mark.asyncio
async def test_update_observation_success(route_env):
    """验证成功更新单条指标"""
    client, session_factory = route_env
    
    mid = uuid4()
    oid = uuid4()
    eid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="更新测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 3, 1), document_id=None, baseline_age_months=96))
        session.add(Observation(id=oid, exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm", is_abnormal=False))
        await session.commit()
    
    resp = await client.patch(f"/api/v1/records/observations/{oid}", json={"value_numeric": 125.5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "updated"
    assert str(data["id"]) == str(oid)
    
    async with session_factory() as session:
        obs = await session.get(Observation, oid)
        assert obs.value_numeric == 125.5
        assert obs.confidence_score == 1.0

@pytest.mark.asyncio
async def test_update_observation_not_found(route_env):
    """验证更新不存在的指标返回 404"""
    client, _ = route_env
    
    resp = await client.patch(f"/api/v1/records/observations/{uuid4()}", json={"value_numeric": 100.0})
    assert resp.status_code == 404
    assert "指标记录不存在" in resp.text

@pytest.mark.asyncio
async def test_update_observation_out_of_range(route_env):
    """验证更新值超出通用范围 (0-1000) 被拒绝"""
    client, session_factory = route_env
    
    mid = uuid4()
    oid = uuid4()
    eid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="范围测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 3, 1), document_id=None, baseline_age_months=96))
        session.add(Observation(id=oid, exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm", is_abnormal=False))
        await session.commit()
    
    resp = await client.patch(f"/api/v1/records/observations/{oid}", json={"value_numeric": 5000.0})
    assert resp.status_code == 422
    assert "数值越界" in resp.text

@pytest.mark.asyncio
async def test_update_observation_negative_value_rejected(route_env):
    """验证更新负数值被拒绝"""
    client, session_factory = route_env
    
    mid = uuid4()
    oid = uuid4()
    eid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="负值测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 3, 1), document_id=None, baseline_age_months=96))
        session.add(Observation(id=oid, exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm", is_abnormal=False))
        await session.commit()
    
    resp = await client.patch(f"/api/v1/records/observations/{oid}", json={"value_numeric": -1.0})
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_update_observation_sanity_check(route_env):
    """验证更新时执行业务合理性校验 (PATCH 拦截)"""
    client, session_factory = route_env
    
    mid = uuid4()
    oid = uuid4()
    eid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=mid, name="业务校验测试", gender="male", date_of_birth=date(2018, 1, 1), member_type="child"
        ))
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 3, 1), document_id=None, baseline_age_months=96))
        # 原本是 height 120cm
        session.add(Observation(id=oid, exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm", is_abnormal=False))
        await session.commit()
    
    # 修改为 1000cm (超出 30-250cm 范围)
    resp = await client.patch(f"/api/v1/records/observations/{oid}", json={"value_numeric": 1000.0})
    assert resp.status_code == 422
    assert "超出常规合理范围" in resp.text


# ==================== DELETE 测试 ====================

@pytest.mark.asyncio
async def test_exam_record_deletion_cascade(route_env):
    """验证级联删除功能"""
    client, session_factory = route_env
    
    mid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(id=mid, name="删除测试", gender="male", date_of_birth=date(2020, 1, 1), member_type="child"))
        eid = uuid4()
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 3, 1), document_id=None, baseline_age_months=72))
        session.add(Observation(id=uuid4(), exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm", is_abnormal=False))
        await session.commit()
        
    resp = await client.delete(f"/api/v1/records/exam-records/{eid}")
    assert resp.status_code == 204
    
    async with session_factory() as session:
        exams = (await session.scalars(select(ExamRecord))).all()
        assert len(exams) == 0
        obs = (await session.scalars(select(Observation))).all()
        assert len(obs) == 0

@pytest.mark.asyncio
async def test_delete_exam_record_not_found(route_env):
    """验证删除不存在的记录返回 404"""
    client, _ = route_env
    
    resp = await client.delete(f"/api/v1/records/exam-records/{uuid4()}")
    assert resp.status_code == 404
    assert "检查记录不存在" in resp.text

@pytest.mark.asyncio
async def test_delete_exam_cascade_multiple_observations(route_env):
    """验证删除含多条 observation 的 exam 记录时全部级联删除"""
    client, session_factory = route_env
    
    mid = uuid4()
    eid = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(id=mid, name="级联测试", gender="male", date_of_birth=date(2020, 1, 1), member_type="child"))
        session.add(ExamRecord(id=eid, member_id=mid, exam_date=date(2026, 3, 1), document_id=None, baseline_age_months=72))
        session.add(Observation(id=uuid4(), exam_record_id=eid, metric_code="height", value_numeric=120.0, unit="cm", is_abnormal=False))
        session.add(Observation(id=uuid4(), exam_record_id=eid, metric_code="weight", value_numeric=25.0, unit="kg", is_abnormal=False))
        session.add(Observation(id=uuid4(), exam_record_id=eid, metric_code="axial_length", value_numeric=23.5, unit="mm", side="left", is_abnormal=False))
        await session.commit()
    
    resp = await client.delete(f"/api/v1/records/exam-records/{eid}")
    assert resp.status_code == 204
    
    async with session_factory() as session:
        exams = (await session.scalars(select(ExamRecord))).all()
        assert len(exams) == 0
        obs = (await session.scalars(select(Observation))).all()
        assert len(obs) == 0
