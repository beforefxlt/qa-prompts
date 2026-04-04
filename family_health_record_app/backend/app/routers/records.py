from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List

from ..db import get_db
from ..models.member import MemberProfile
from ..models.observation import ExamRecord, Observation
from ..schemas.observation import ManualExamCreate, ObservationUpdate

router = APIRouter(prefix="/records", tags=["Records Management"])
 
def check_metric_sanity(metric: str, v: float):
    """业务逻辑校验：针对不同指标执行合理性区间检查（用于 PATCH 场景）
    
    区间定义对齐 API_CONTRACT.md v2.4.0 数值约束表
    """
    if metric == "axial_length":
        if not (15.0 <= v <= 35.0):
            raise HTTPException(status_code=422, detail=f"眼轴数值 {v} 超出常规合理范围 (15-35mm)")
    elif metric == "height":
        if not (30.0 <= v <= 250.0):
            raise HTTPException(status_code=422, detail=f"身高数值 {v} 超出常规合理范围 (30-250cm)")
    elif metric == "weight":
        if not (2.0 <= v <= 500.0):
            raise HTTPException(status_code=422, detail=f"体重数值 {v} 超出常规合理范围 (2-500kg)")
    elif metric == "glucose":
        if not (0.1 <= v <= 50.0):
            raise HTTPException(status_code=422, detail=f"血糖 {v} 超出常规合理范围 (0.1-50.0 mmol/L)")
    elif metric == "ldl":
        if not (0.1 <= v <= 10.0):
            raise HTTPException(status_code=422, detail=f"低密度脂蛋白 {v} 超出常规合理范围 (0.1-10.0 mmol/L)")
    elif metric == "hemoglobin":
        if not (30.0 <= v <= 250.0):
            raise HTTPException(status_code=422, detail=f"血红蛋白 {v} 超出常规合理范围 (30-250 g/L)")
    elif metric == "hba1c":
        if not (3.0 <= v <= 15.0):
            raise HTTPException(status_code=422, detail=f"糖化血红蛋白 {v} 超出常规合理范围 (3.0-15.0%)")
    return v

@router.post("/members/{member_id}/manual-exams", status_code=201)
async def create_manual_exam_record(
    member_id: UUID, 
    payload: ManualExamCreate, 
    db: AsyncSession = Depends(get_db)
):
    """手动录入一次完整的检查记录"""
    # 1. 验证成员存在
    member = await db.get(MemberProfile, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="成员资料不存在")
    if member.is_deleted:
        raise HTTPException(status_code=400, detail="成员已删除，无法录入")

    # 2. 计算 baseline_age_months
    dob = member.date_of_birth
    ed = payload.exam_date
    baseline_age_months = (ed.year - dob.year) * 12 + (ed.month - dob.month)
    if ed.day < dob.day:
        baseline_age_months -= 1

    # 3. 创建 ExamRecord
    new_exam = ExamRecord(
        member_id=member_id,
        document_id=None,
        exam_date=payload.exam_date,
        institution_name=payload.institution_name,
        baseline_age_months=max(0, baseline_age_months)
    )
    db.add(new_exam)
    await db.flush()

    # 4. 创建 Observations（Pydantic schema 已做区间校验，无需重复）
    for item in payload.observations:
        new_obs = Observation(
            exam_record_id=new_exam.id,
            metric_code=item.metric_code,
            value_numeric=item.value_numeric,
            unit=item.unit,
            side=item.side,
            is_abnormal=False,
            confidence_score=1.0
        )
        db.add(new_obs)
    
    await db.commit()
    return {"id": new_exam.id, "status": "persisted"}

@router.patch("/observations/{observation_id}")
async def update_single_observation(
    observation_id: UUID,
    payload: ObservationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """修改单条指标数值"""
    obs = await db.get(Observation, observation_id)
    if not obs:
        raise HTTPException(status_code=404, detail="指标记录不存在")
    
    # 业务校验：根据原有的 metric_code 校验新数值
    check_metric_sanity(obs.metric_code, payload.value_numeric)
    
    obs.value_numeric = payload.value_numeric
    obs.confidence_score = 1.0  # 修改后置信度为满分
    
    await db.commit()
    return {"id": observation_id, "status": "updated"}

@router.delete("/exam-records/{exam_record_id}", status_code=204)
async def delete_exam_record_cascade(
    exam_record_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    级联删除整次检查及其关联的所有指标
    """
    exam = await db.get(ExamRecord, exam_record_id)
    if not exam:
        raise HTTPException(status_code=404, detail="检查记录不存在")
    
    # 级联删除由 SQLAlchemy 关系处理 (或者我们手动处理)
    # 因为 Observation.exam_record_id 有外键约束，我们直接删除 exam
    await db.delete(exam)
    await db.commit()
    return None
