from datetime import datetime
from uuid import UUID
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_db
from ..models.member import MemberProfile
from ..models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from ..models.observation import ExamRecord, Observation, DerivedMetric

router = APIRouter(prefix="/review-tasks", tags=["review"])


class ReviewTaskResponse(BaseModel):
    id: str
    document_id: str
    status: str
    audit_trail: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ReviewApprovalRequest(BaseModel):
    revised_items: Optional[List[Dict[str, Any]]] = None


class ReviewTaskListItem(BaseModel):
    id: str
    document_id: str
    status: str
    created_at: Optional[str]


@router.get("", response_model=List[ReviewTaskListItem])
async def list_review_tasks(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ReviewTask)
        .where(ReviewTask.status.in_(["pending", "draft"]))
        .order_by(ReviewTask.created_at.desc())
    )
    tasks = (await db.scalars(stmt)).all()
    return [
        ReviewTaskListItem(
            id=str(t.id),
            document_id=str(t.document_id),
            status=t.status,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in tasks
    ]


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_review_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ReviewTask)
        .options(selectinload(ReviewTask.document))
        .where(ReviewTask.id == task_id)
    )
    task = await db.scalar(stmt)
    if task is None:
        raise HTTPException(status_code=404, detail="审核任务不存在")

    ocr_result = await db.scalar(
        select(OCRExtractionResult).where(OCRExtractionResult.document_id == task.document_id)
    )

    # 获取脱敏图片URL
    image_url = None
    if task.document and task.document.desensitized_url:
        # 返回图片预览API的URL
        image_url = f"/api/v1/documents/{task.document_id}/preview"

    return {
        "id": str(task.id),
        "document_id": str(task.document_id),
        "status": task.status,
        "document_status": task.document.status if task.document else None,
        "ocr_raw_json": ocr_result.raw_json if ocr_result else None,
        "ocr_processed_items": ocr_result.processed_items if ocr_result else None,
        "confidence_score": ocr_result.confidence_score if ocr_result else None,
        "rule_conflict_details": ocr_result.rule_conflict_details if ocr_result else None,
        "audit_trail": task.audit_trail,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "image_url": image_url,
    }


@router.post("/{task_id}/approve", response_model=Dict[str, Any])
async def approve_review_task(
    task_id: UUID,
    data: ReviewApprovalRequest = ReviewApprovalRequest(),
    db: AsyncSession = Depends(get_db),
):
    task = await db.scalar(
        select(ReviewTask).options(selectinload(ReviewTask.document)).where(ReviewTask.id == task_id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="审核任务不存在")

    if task.status not in ("pending", "draft"):
        raise HTTPException(status_code=409, detail="审核任务状态不允许通过")

    document = task.document
    ocr_result = await db.scalar(
        select(OCRExtractionResult).where(OCRExtractionResult.document_id == document.id)
    )

    if ocr_result is None:
        raise HTTPException(status_code=400, detail="OCR 结果不存在")

    processed_items = ocr_result.processed_items or {}

    if data.revised_items:
        existing_observations = processed_items.get("observations", [])
        
        # Handle exam_date revision separately
        for revised in data.revised_items:
            metric_code = revised.get("metric_code")
            if metric_code == "exam_date" and "value" in revised:
                processed_items["exam_date"] = revised["value"]
                continue
                
            side = revised.get("side")
            for obs in existing_observations:
                if obs.get("metric_code") == metric_code and obs.get("side") == side:
                    if "value_numeric" in revised:
                        obs["value_numeric"] = revised["value_numeric"]
                    if "unit" in revised:
                        obs["unit"] = revised["unit"]

        audit_event = {
            "action": "manual_revision",
            "timestamp": datetime.now().isoformat(),
            "revisions": data.revised_items,
        }
    else:
        audit_event = {
            "action": "approved_without_changes",
            "timestamp": datetime.now().isoformat(),
        }

    audit_trail = task.audit_trail or {"events": []}
    audit_trail["events"].append(audit_event)
    task.audit_trail = audit_trail
    task.status = "approved"

    try:
        exam_date = datetime.fromisoformat(processed_items["exam_date"]).date()
    except Exception:
        task.status = "rejected"
        document.status = "rule_conflict"
        await db.flush()
        return {"task_id": str(task.id), "status": "rejected", "reason": "exam_date_invalid"}

    existing_exam_record = await db.scalar(
        select(ExamRecord).where(ExamRecord.document_id == document.id)
    )
    if existing_exam_record is None:
        from ..routers.documents import _calculate_baseline_age_months, _build_axial_growth_payload

        member = await db.scalar(
            select(DocumentRecord.member_id).where(DocumentRecord.id == document.id)
        )
        if member is None:
            raise HTTPException(status_code=404, detail="成员不存在")

        member_profile = await db.scalar(
            select(MemberProfile).where(MemberProfile.id == member)
        )
        if member_profile is None:
            raise HTTPException(status_code=404, detail="成员不存在")

        exam_record = ExamRecord(
            document_id=document.id,
            member_id=member,
            exam_date=exam_date,
            institution_name=processed_items.get("institution"),
            baseline_age_months=_calculate_baseline_age_months(member_profile.date_of_birth, exam_date),
        )
        db.add(exam_record)
        await db.flush()
    else:
        exam_record = existing_exam_record

    for obs_data in processed_items.get("observations", []):
        existing_observation = await db.scalar(
            select(Observation).where(
                Observation.exam_record_id == exam_record.id,
                Observation.metric_code == obs_data["metric_code"],
                Observation.side == obs_data.get("side"),
            )
        )
        if existing_observation is None:
            db.add(
                Observation(
                    exam_record_id=exam_record.id,
                    metric_code=obs_data["metric_code"],
                    value_numeric=obs_data["value_numeric"],
                    unit=obs_data["unit"],
                    side=obs_data.get("side"),
                    confidence_score=1.0,
                )
            )
        else:
            existing_observation.value_numeric = obs_data["value_numeric"]
            existing_observation.unit = obs_data["unit"]
            existing_observation.confidence_score = 1.0

    growth_payload = _build_axial_growth_payload(processed_items.get("observations", []))
    if growth_payload:
        existing_derived = await db.scalar(
            select(DerivedMetric).where(
                DerivedMetric.member_id == exam_record.member_id,
                DerivedMetric.metric_category == "axial_growth_deviation",
            )
        )
        if existing_derived is None:
            db.add(
                DerivedMetric(
                    member_id=exam_record.member_id,
                    metric_category="axial_growth_deviation",
                    value_numeric=growth_payload["deviation_vs_reference"],
                    value_json=growth_payload,
                    algorithm_version="axial_growth_v1",
                )
            )
        else:
            existing_derived.value_numeric = growth_payload["deviation_vs_reference"]
            existing_derived.value_json = growth_payload
            existing_derived.algorithm_version = "axial_growth_v1"

    document.status = "persisted"
    await db.flush()

    return {"task_id": str(task.id), "status": "approved", "document_status": "persisted"}


@router.post("/{task_id}/reject", response_model=Dict[str, Any])
async def reject_review_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    task = await db.scalar(
        select(ReviewTask).options(selectinload(ReviewTask.document)).where(ReviewTask.id == task_id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="审核任务不存在")

    if task.status not in ("pending", "draft"):
        raise HTTPException(status_code=409, detail="审核任务状态不允许退回")

    task.status = "rejected"
    if task.document:
        task.document.status = "review_rejected"

    audit_trail = task.audit_trail or {"events": []}
    audit_trail["events"].append({
        "action": "rejected",
        "timestamp": datetime.now().isoformat(),
    })
    task.audit_trail = audit_trail

    await db.flush()
    return {"task_id": str(task.id), "status": "rejected", "document_status": "review_rejected"}


@router.post("/{task_id}/save-draft", response_model=Dict[str, Any])
async def save_draft_review_task(
    task_id: UUID,
    data: ReviewApprovalRequest = ReviewApprovalRequest(),
    db: AsyncSession = Depends(get_db),
):
    task = await db.scalar(
        select(ReviewTask).options(selectinload(ReviewTask.document)).where(ReviewTask.id == task_id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="审核任务不存在")

    if task.status not in ("pending", "draft"):
        raise HTTPException(status_code=409, detail="审核任务状态不允许保存草稿")

    ocr_result = await db.scalar(
        select(OCRExtractionResult).where(OCRExtractionResult.document_id == task.document_id)
    )

    if data.revised_items and ocr_result:
        processed_items = ocr_result.processed_items or {}
        existing_observations = processed_items.get("observations", [])
        for revised in data.revised_items:
            metric_code = revised.get("metric_code")
            side = revised.get("side")
            for obs in existing_observations:
                if obs.get("metric_code") == metric_code and obs.get("side") == side:
                    if "value_numeric" in revised:
                        obs["value_numeric"] = revised["value_numeric"]
                    if "unit" in revised:
                        obs["unit"] = revised["unit"]

        ocr_result.processed_items = processed_items

    audit_trail = task.audit_trail or {"events": []}
    audit_trail["events"].append({
        "action": "draft_saved",
        "timestamp": datetime.now().isoformat(),
    })
    task.audit_trail = audit_trail
    task.status = "draft"

    await db.flush()
    return {"task_id": str(task.id), "status": "draft"}
