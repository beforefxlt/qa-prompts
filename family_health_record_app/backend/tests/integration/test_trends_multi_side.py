import pytest
from uuid import uuid4
from datetime import date

from app.models.member import MemberProfile
from app.models.observation import ExamRecord, Observation

@pytest.mark.asyncio
async def test_trends_multi_side_comparison(route_env):
    """验证趋势接口的多 side 比较逻辑 (BUG-031 修复验证)"""
    client, session_factory = route_env
    
    # 1. 创建成员
    member_id = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=member_id,
            name="测试记录",
            gender="male",
            date_of_birth=date(2020, 1, 1),
            member_type="child"
        ))
        
        # 2. 创建两次检查记录 (包含左右眼)
        # 上次检查 (2026-03-01)
        prev_exam_id = uuid4()
        session.add(ExamRecord(
            id=prev_exam_id, 
            member_id=member_id, 
            exam_date=date(2026, 3, 1),
            document_id=uuid4(),
            baseline_age_months=72
        ))
        await session.flush()
        session.add_all([
            Observation(id=uuid4(), exam_record_id=prev_exam_id, metric_code="axial_length", value_numeric=23.0, unit="mm", side="left"),
            Observation(id=uuid4(), exam_record_id=prev_exam_id, metric_code="axial_length", value_numeric=24.0, unit="mm", side="right")
        ])
        
        # 当前检查 (2026-04-01)
        curr_exam_id = uuid4()
        session.add(ExamRecord(
            id=curr_exam_id, 
            member_id=member_id, 
            exam_date=date(2026, 4, 1),
            document_id=uuid4(),
            baseline_age_months=73
        ))
        await session.flush()
        session.add_all([
            Observation(id=uuid4(), exam_record_id=curr_exam_id, metric_code="axial_length", value_numeric=23.5, unit="mm", side="left"),
            Observation(id=uuid4(), exam_record_id=curr_exam_id, metric_code="axial_length", value_numeric=24.2, unit="mm", side="right")
        ])
        await session.commit()
    
    # 3. 请求趋势接口
    response = await client.get(f"/api/v1/members/{member_id}/trends?metric=axial_length")
    assert response.status_code == 200
    data = response.json()
    
    # 4. 验证 comparison 结构 (应支持多 side)
    comp = data.get("comparison")
    assert comp is not None
    assert "left" in comp
    assert "right" in comp
    
    # 左眼: 23.5 - 23.0 = 0.5
    assert comp["left"]["current"] == 23.5
    assert comp["left"]["previous"] == 23.0
    assert comp["left"]["delta"] == 0.5
    
    # 右眼: 24.2 - 24.0 = 0.2
    assert comp["right"]["current"] == 24.2
    assert comp["right"]["previous"] == 24.0
    assert comp["right"]["delta"] == 0.2

@pytest.mark.asyncio
async def test_trends_single_value_comparison(route_env):
    """验证单值指标 (如身高) 的比较逻辑"""
    client, session_factory = route_env
    
    # 1. 创建成员
    member_id = uuid4()
    async with session_factory() as session:
        session.add(MemberProfile(
            id=member_id,
            name="单值测试",
            gender="female",
            date_of_birth=date(2020, 1, 1),
            member_type="child"
        ))
        
        # 2. 创建两次检查 (无 side)
        exam1_id = uuid4()
        session.add(ExamRecord(
            id=exam1_id, 
            member_id=member_id, 
            exam_date=date(2026, 1, 1),
            document_id=uuid4(),
            baseline_age_months=70
        ))
        await session.flush()
        session.add(Observation(id=uuid4(), exam_record_id=exam1_id, metric_code="height", value_numeric=110.0, unit="cm", side=None))
        
        exam2_id = uuid4()
        session.add(ExamRecord(
            id=exam2_id, 
            member_id=member_id, 
            exam_date=date(2026, 2, 1),
            document_id=uuid4(),
            baseline_age_months=71
        ))
        await session.flush()
        session.add(Observation(id=uuid4(), exam_record_id=exam2_id, metric_code="height", value_numeric=112.0, unit="cm", side=None))
        await session.commit()
    
    # 3. 请求接口
    response = await client.get(f"/api/v1/members/{member_id}/trends?metric=height")
    assert response.status_code == 200
    data = response.json()
    
    # 4. 验证 comparison
    comp = data.get("comparison")
    assert comp is not None
    assert "value" in comp
    assert comp["value"]["current"] == 112.0
    assert comp["value"]["previous"] == 110.0
    assert comp["value"]["delta"] == 2.0
