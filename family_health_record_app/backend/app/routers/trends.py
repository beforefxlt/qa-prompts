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
            Observation.id.label("observation_id"),
            Observation.exam_record_id,
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
            "exam_record_id": row.exam_record_id,
            "observation_id": row.observation_id,
        }
        for row in trend_rows
    ]
    reference_range = next((row.reference_range for row in trend_rows if row.reference_range), None)
    alert_status = "warning" if any(row.is_abnormal for row in trend_rows) else "normal"

    # 按 exam_date 分组，只比较不同日期的数据
    dates = sorted(set(row.exam_date for row in trend_rows))
    
    comparison = None
    if len(dates) >= 2:
        latest_date = dates[-1]
        previous_date = dates[-2]
        
        latest_rows = [row for row in trend_rows if row.exam_date == latest_date]
        previous_rows = [row for row in trend_rows if row.exam_date == previous_date]
        
        comparison = {}
        for side in ["left", "right"]:
            latest_val = next((r.value_numeric for r in latest_rows if r.side == side), None)
            previous_val = next((r.value_numeric for r in previous_rows if r.side == side), None)
            
            if latest_val is not None and previous_val is not None:
                comparison[side] = {
                    "current": latest_val,
                    "previous": previous_val,
                    "delta": round(latest_val - previous_val, 3),
                }
        
        # 针对无 side 的指标 (如身高)
        val_latest = next((r.value_numeric for r in latest_rows if r.side is None), None)
        val_previous = next((r.value_numeric for r in previous_rows if r.side is None), None)
        if val_latest is not None and val_previous is not None:
            comparison["value"] = {
                "current": val_latest,
                "previous": val_previous,
                "delta": round(val_latest - val_previous, 3),
            }
            
        if not comparison:
            comparison = None

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

    # 计算最近两次检查的左右眼对比
    axial_comparison = None
    if len(axial_rows) >= 2:
        dates = sorted(set(row.exam_date for row in axial_rows))
        if len(dates) >= 2:
            latest_date = dates[-1]
            previous_date = dates[-2]
            
            latest_rows = [row for row in axial_rows if row.exam_date == latest_date]
            previous_rows = [row for row in axial_rows if row.exam_date == previous_date]
            
            axial_comparison = {"left": None, "right": None}
            
            for side in ["left", "right"]:
                latest_val = next((r.value_numeric for r in latest_rows if r.side == side), None)
                previous_val = next((r.value_numeric for r in previous_rows if r.side == side), None)
                
                if latest_val is not None and previous_val is not None:
                    axial_comparison[side] = {
                        "current": latest_val,
                        "previous": previous_val,
                        "delta": round(latest_val - previous_val, 3),
                    }
            
            # 如果左右眼都没有数据，设为 null
            if axial_comparison["left"] is None and axial_comparison["right"] is None:
                axial_comparison = None

    # 计算视力最近两次检查的左右眼对比
    # vision_acuity 的 value 可能来自 value_text (字符串) 或 value_numeric，需统一转为 float
    def _parse_vision_value(row):
        if row.value_numeric is not None:
            return row.value_numeric
        if row.value_text is not None:
            try:
                return float(row.value_text)
            except (ValueError, TypeError):
                return None
        return None

    vision_comparison = None
    if len(vision_rows) >= 2:
        dates = sorted(set(row.exam_date for row in vision_rows))
        if len(dates) >= 2:
            latest_date = dates[-1]
            previous_date = dates[-2]
            
            latest_rows = [row for row in vision_rows if row.exam_date == latest_date]
            previous_rows = [row for row in vision_rows if row.exam_date == previous_date]
            
            vision_comparison = {"left": None, "right": None}
            
            for side in ["left", "right"]:
                latest_val = next((_parse_vision_value(r) for r in latest_rows if r.side == side), None)
                previous_val = next((_parse_vision_value(r) for r in previous_rows if r.side == side), None)
                
                if latest_val is not None and previous_val is not None:
                    vision_comparison[side] = {
                        "current": latest_val,
                        "previous": previous_val,
                        "delta": round(latest_val - previous_val, 3),
                    }
            
            # 如果左右眼都没有数据，设为 null
            if vision_comparison["left"] is None and vision_comparison["right"] is None:
                vision_comparison = None

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
            "comparison": axial_comparison,
        },
        "vision_acuity": {
            "series": [
                {"date": row.exam_date.isoformat(), "value": row.value_text or row.value_numeric, "side": row.side}
                for row in vision_rows
            ],
            "reference_range": next((row.reference_range for row in vision_rows if row.reference_range), None),
            "alert_status": "warning" if any(row.is_abnormal for row in vision_rows) else "normal",
            "comparison": vision_comparison,
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


def _build_single_comparison(rows):
    """计算单维度指标（如身高/体重）最近两次检查对比"""
    if len(rows) < 2:
        return None
    
    dates = sorted(set(row.exam_date for row in rows))
    if len(dates) < 2:
        return None
    
    latest_date = dates[-1]
    previous_date = dates[-2]
    
    latest_val = next((r.value_numeric for r in rows if r.exam_date == latest_date), None)
    previous_val = next((r.value_numeric for r in rows if r.exam_date == previous_date), None)
    
    if latest_val is not None and previous_val is not None:
        return {
            "current": latest_val,
            "previous": previous_val,
            "delta": round(latest_val - previous_val, 3),
        }
    return None


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
            "comparison": _build_single_comparison(height_rows),
        },
        "weight": {
            "series": [
                {"date": row.exam_date.isoformat(), "value": row.value_numeric}
                for row in weight_rows
            ],
            "reference_range": next((row.reference_range for row in weight_rows if row.reference_range), None),
            "alert_status": "warning" if any(row.is_abnormal for row in weight_rows) else "normal",
            "growth_rate": _calculate_growth_rate(weight_rows),
            "comparison": _build_single_comparison(weight_rows),
        },
    }


BLOOD_METRICS = ["glucose", "tc", "tg", "hdl", "ldl", "hemoglobin", "hba1c"]


@router.get("/{member_id}/blood-dashboard")
async def get_blood_dashboard(member_id: UUID, db: AsyncSession = Depends(get_db)):
    """成人/老人血液指标看板"""
    member = await db.scalar(
        select(MemberProfile).where(
            MemberProfile.id == member_id,
            MemberProfile.is_deleted.is_(False)
        )
    )
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")

    result = {
        "member_id": str(member_id),
        "member_type": member.member_type,
    }

    for metric in BLOOD_METRICS:
        stmt = (
            select(ExamRecord.exam_date, Observation.value_numeric, Observation.reference_range, Observation.is_abnormal)
            .join(Observation, Observation.exam_record_id == ExamRecord.id)
            .where(ExamRecord.member_id == member_id, Observation.metric_code == metric)
            .order_by(ExamRecord.exam_date.asc())
        )
        rows = (await db.execute(stmt)).all()

        result[metric] = {
            "series": [
                {"date": row.exam_date.isoformat(), "value": row.value_numeric}
                for row in rows
            ],
            "reference_range": next((row.reference_range for row in rows if row.reference_range), None),
            "alert_status": "warning" if any(row.is_abnormal for row in rows) else "normal",
            "comparison": _build_single_comparison(rows),
        }

    return result
