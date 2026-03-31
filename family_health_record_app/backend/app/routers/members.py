import os
import shutil
from datetime import date
from uuid import UUID
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_db
from ..models.member import MemberProfile
from ..models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from ..models.observation import ExamRecord, Observation, DerivedMetric
from ..schemas.member import MemberCreate, MemberUpdate, MemberResponse

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

router = APIRouter(prefix="/api/v1/members", tags=["members"])


def _calculate_baseline_age_months(date_of_birth: date, exam_date: date) -> int:
    months = (exam_date.year - date_of_birth.year) * 12 + (exam_date.month - date_of_birth.month)
    if exam_date.day < date_of_birth.day:
        months -= 1
    return max(months, 0)


def _build_axial_growth_payload(observations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    axial_values = {
        item.get("side"): item.get("value_numeric")
        for item in observations
        if item.get("metric_code") == "axial_length" and item.get("side") in {"left", "right"}
    }
    if "left" not in axial_values or "right" not in axial_values:
        return None
    average_axial = (axial_values["left"] + axial_values["right"]) / 2
    return {
        "left": axial_values["left"],
        "right": axial_values["right"],
        "average": round(average_axial, 3),
        "deviation_vs_reference": round(average_axial - 23.0, 3),
    }


async def _ensure_review_task(db: AsyncSession, document: DocumentRecord, reason: str) -> None:
    existing_task = await db.scalar(select(ReviewTask).where(ReviewTask.document_id == document.id))
    if existing_task is None:
        review_task = ReviewTask(
            document_id=document.id,
            status="pending",
            reviewer_id=None,
            audit_trail={"events": [{"action": reason}]},
        )
        db.add(review_task)


@router.get("", response_model=List[MemberResponse])
async def list_members(db: AsyncSession = Depends(get_db)):
    stmt = select(MemberProfile).where(MemberProfile.is_deleted.is_(False)).order_by(MemberProfile.created_at.desc())
    members = (await db.scalars(stmt)).all()
    return [
        MemberResponse(
            id=m.id,
            name=m.name,
            gender=m.gender,
            date_of_birth=m.date_of_birth,
            member_type=m.member_type,
        )
        for m in members
    ]


@router.post("", response_model=MemberResponse, status_code=201)
async def create_member(data: MemberCreate, db: AsyncSession = Depends(get_db)):
    member = MemberProfile(
        name=data.name,
        gender=data.gender,
        date_of_birth=data.date_of_birth,
        member_type=data.member_type,
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return MemberResponse(
        id=member.id,
        name=member.name,
        gender=member.gender,
        date_of_birth=member.date_of_birth,
        member_type=member.member_type,
    )


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(member_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(MemberProfile).where(MemberProfile.id == member_id, MemberProfile.is_deleted.is_(False))
    member = await db.scalar(stmt)
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")
    return MemberResponse(
        id=member.id,
        name=member.name,
        gender=member.gender,
        date_of_birth=member.date_of_birth,
        member_type=member.member_type,
    )


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(member_id: UUID, data: MemberUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(MemberProfile).where(MemberProfile.id == member_id, MemberProfile.is_deleted.is_(False))
    member = await db.scalar(stmt)
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    await db.flush()
    await db.refresh(member)
    return MemberResponse(
        id=member.id,
        name=member.name,
        gender=member.gender,
        date_of_birth=member.date_of_birth,
        member_type=member.member_type,
    )


@router.delete("/{member_id}", status_code=204)
async def delete_member(member_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(MemberProfile).where(MemberProfile.id == member_id, MemberProfile.is_deleted.is_(False))
    member = await db.scalar(stmt)
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")

    member.is_deleted = True
    await db.flush()
