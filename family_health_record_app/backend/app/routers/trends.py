from uuid import UUID
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models.member import MemberProfile
from ..models.observation import ExamRecord, Observation, DerivedMetric

router = APIRouter(prefix="/members", tags=["trends"])


@router.get("/{member_id}/trends")
async def get_trends(member_id: UUID, metric: str, db: AsyncSession = Depends(get_db)):
    member = await db.scalar(
        select(MemberProfile).where(
            MemberProfile.id == member_id,
            MemberProfile.is_deleted.is_(False)
        )
    )
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")

    trend_stmt = (
        select(
            ExamRecord.exam_date,
            Observation.value_numeric,
            Observation.reference_range,
            Observation.is_abnormal,
            Observation.side,
        )
        .join(Observation, Observation.exam_record_id == ExamRecord.id)
        .where(ExamRecord.member_id == member_id, Observation.metric_code == metric)
        .order_by(ExamRecord.exam_date.asc())
    )
    trend_rows = (await db.execute(trend_stmt)).all()
    series = [
        {
            "date": row.exam_date.isoformat(),
            "value": row.value_numeric,
            "side": row.side,
        }
        for row in trend_rows
    ]
    reference_range = next((row.reference_range for row in trend_rows if row.reference_range), None)
    alert_status = "warning" if any(row.is_abnormal for row in trend_rows) else "normal"

    # 按 exam_date 分组，只比较不同日期的数据
    dates = sorted(set(row.exam_date for row in trend_rows))
    
    comparison = None
    if len(dates) >= 2:
        # 获取最新和上次检查的所有 observation
        latest_date = dates[-1]
        previous_date = dates[-2]
        
        latest_rows = [row for row in trend_rows if row.exam_date == latest_date]
        previous_rows = [row for row in trend_rows if row.exam_date == previous_date]
        
        # 比较相同 side 的值，如果没有 side 则比较第一个值
        if latest_rows and previous_rows:
            # 尝试匹配相同 side
            for side in ['left', 'right', None]:
                latest_val = next((r.value_numeric for r in latest_rows if r.side == side), None)
                previous_val = next((r.value_numeric for r in previous_rows if r.side == side), None)
                if latest_val is not None and previous_val is not None:
                    comparison = {
                        "current": latest_val,
                        "previous": previous_val,
                        "delta": round(latest_val - previous_val, 3),
                    }
                    break
            # 如果无法匹配 side，使用第一个值
            if comparison is None:
                latest_val = latest_rows[0].value_numeric
                previous_val = previous_rows[0].value_numeric
                comparison = {
                    "current": latest_val,
                    "previous": previous_val,
                    "delta": round(latest_val - previous_val, 3),
                }

    return {
        "metric": metric,
        "series": series,
        "reference_range": reference_range,
        "alert_status": alert_status,
        "comparison": comparison,
    }


@router.get("/{member_id}/vision-dashboard")
async def get_vision_dashboard(member_id: UUID, db: AsyncSession = Depends(get_db)):
    member = await db.scalar(
        select(MemberProfile).where(
            MemberProfile.id == member_id,
            MemberProfile.is_deleted.is_(False)
        )
    )
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")

    axial_stmt = (
        select(ExamRecord.exam_date, Observation.value_numeric, Observation.side, Observation.reference_range, Observation.is_abnormal)
        .join(Observation, Observation.exam_record_id == ExamRecord.id)
        .where(ExamRecord.member_id == member_id, Observation.metric_code == "axial_length")
        .order_by(ExamRecord.exam_date.asc())
    )
    axial_rows = (await db.execute(axial_stmt)).all()

    vision_stmt = (
        select(ExamRecord.exam_date, Observation.value_text, Observation.value_numeric, Observation.side, Observation.reference_range, Observation.is_abnormal)
        .join(Observation, Observation.exam_record_id == ExamRecord.id)
        .where(ExamRecord.member_id == member_id, Observation.metric_code == "vision_acuity")
        .order_by(ExamRecord.exam_date.asc())
    )
    vision_rows = (await db.execute(vision_stmt)).all()

    derived = await db.scalar(
        select(DerivedMetric).where(
            DerivedMetric.member_id == member_id,
            DerivedMetric.metric_category == "axial_growth_deviation",
        )
    )

    # 计算眼轴年增长率
    growth_rate = None
    if len(axial_rows) >= 2:
        # 获取所有不同日期
        dates = sorted(set(row.exam_date for row in axial_rows))
        if len(dates) >= 2:
            first_date = dates[0]
            last_date = dates[-1]
            
            # 计算时间差（年）
            days_diff = (last_date - first_date).days
            years_diff = days_diff / 365.25
            
            if years_diff > 0:
                # 获取第一个日期的平均值
                first_rows = [row for row in axial_rows if row.exam_date == first_date]
                first_avg = sum(r.value_numeric for r in first_rows) / len(first_rows)
                
                # 获取最后一个日期的平均值
                last_rows = [row for row in axial_rows if row.exam_date == last_date]
                last_avg = sum(r.value_numeric for r in last_rows) / len(last_rows)
                
                # 计算年增长率
                growth_rate = round((last_avg - first_avg) / years_diff, 2)

    return {
        "member_id": str(member_id),
        "member_type": member.member_type,
        "baseline_age_months": member.date_of_birth,
        "axial_length": {
            "series": [
                {"date": row.exam_date.isoformat(), "value": row.value_numeric, "side": row.side}
                for row in axial_rows
            ],
            "reference_range": next((row.reference_range for row in axial_rows if row.reference_range), None),
            "alert_status": "warning" if any(row.is_abnormal for row in axial_rows) else "normal",
            "growth_rate": growth_rate,
        },
        "vision_acuity": {
            "series": [
                {"date": row.exam_date.isoformat(), "value": row.value_text or row.value_numeric, "side": row.side}
                for row in vision_rows
            ],
        },
        "growth_deviation": derived.value_json if derived else None,
    }


def _calculate_growth_rate(rows):
    """计算年增长率，输入为 [(exam_date, value_numeric), ...] 列表"""
    if len(rows) < 2:
        return None
    
    dates = sorted(set(row.exam_date for row in rows))
    if len(dates) < 2:
        return None
    
    first_date = dates[0]
    last_date = dates[-1]
    days_diff = (last_date - first_date).days
    years_diff = days_diff / 365.25
    
    if years_diff <= 0:
        return None
    
    first_rows = [row for row in rows if row.exam_date == first_date]
    first_avg = sum(r.value_numeric for r in first_rows) / len(first_rows)
    
    last_rows = [row for row in rows if row.exam_date == last_date]
    last_avg = sum(r.value_numeric for r in last_rows) / len(last_rows)
    
    return round((last_avg - first_avg) / years_diff, 2)


@router.get("/{member_id}/growth-dashboard")
async def get_growth_dashboard(member_id: UUID, db: AsyncSession = Depends(get_db)):
    member = await db.scalar(
        select(MemberProfile).where(
            MemberProfile.id == member_id,
            MemberProfile.is_deleted.is_(False)
        )
    )
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")

    height_stmt = (
        select(ExamRecord.exam_date, Observation.value_numeric, Observation.reference_range, Observation.is_abnormal)
        .join(Observation, Observation.exam_record_id == ExamRecord.id)
        .where(ExamRecord.member_id == member_id, Observation.metric_code == "height")
        .order_by(ExamRecord.exam_date.asc())
    )
    height_rows = (await db.execute(height_stmt)).all()

    weight_stmt = (
        select(ExamRecord.exam_date, Observation.value_numeric, Observation.reference_range, Observation.is_abnormal)
        .join(Observation, Observation.exam_record_id == ExamRecord.id)
        .where(ExamRecord.member_id == member_id, Observation.metric_code == "weight")
        .order_by(ExamRecord.exam_date.asc())
    )
    weight_rows = (await db.execute(weight_stmt)).all()

    return {
        "member_id": str(member_id),
        "member_type": member.member_type,
        "height": {
            "series": [
                {"date": row.exam_date.isoformat(), "value": row.value_numeric}
                for row in height_rows
            ],
            "reference_range": next((row.reference_range for row in height_rows if row.reference_range), None),
            "alert_status": "warning" if any(row.is_abnormal for row in height_rows) else "normal",
            "growth_rate": _calculate_growth_rate(height_rows),
        },
        "weight": {
            "series": [
                {"date": row.exam_date.isoformat(), "value": row.value_numeric}
                for row in weight_rows
            ],
            "reference_range": next((row.reference_range for row in weight_rows if row.reference_range), None),
            "alert_status": "warning" if any(row.is_abnormal for row in weight_rows) else "normal",
            "growth_rate": _calculate_growth_rate(weight_rows),
        },
    }
