import os
import shutil
import uuid
import logging
import hashlib
from datetime import date
from uuid import UUID
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_db
from ..models.member import MemberProfile
from ..models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from ..models.observation import ExamRecord, Observation, DerivedMetric
from ..schemas.document import DocumentUploadResponse, DocumentResponse
from ..services.image_processor import desensitize_image

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Lazy-load MinIO client (graceful fallback to local storage)
_storage_client = None

def get_storage_client():
    global _storage_client
    if _storage_client is None:
        try:
            from ..services.storage_client import storage_client
            _storage_client = storage_client
            logger.info("MinIO storage client initialized")
        except Exception as e:
            logger.warning(f"MinIO unavailable, using local storage: {e}")
            _storage_client = None
    return _storage_client

router = APIRouter(prefix="/documents", tags=["documents"])


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
    elif existing_task.status == "rejected":
        existing_task.status = "pending"
        existing_task.audit_trail = {"events": [{"action": reason}]}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    member_id: Optional[UUID] = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    target_member_id = member_id
    if target_member_id is None:
        first_member = await db.scalar(
            select(MemberProfile)
            .where(MemberProfile.is_deleted.is_(False))
            .order_by(MemberProfile.created_at.asc())
        )
        if first_member is None:
            raise HTTPException(status_code=400, detail="未找到可用成员，请先创建成员")
        target_member_id = first_member.id
    else:
        member = await db.scalar(
            select(MemberProfile).where(
                MemberProfile.id == target_member_id,
                MemberProfile.is_deleted.is_(False)
            )
        )
        if member is None:
            raise HTTPException(status_code=404, detail="成员不存在")

    # 1. 基础校验：空文件、格式、大小 (TC-P2-007, TC-P2-008)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

    original_filename = file.filename or "unknown.jpg"
    ext = os.path.splitext(original_filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}。仅支持 JPG, PNG, PDF")

    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="上传的文件不能为空")
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件过大 ({file_size} bytes)。最大限制为 10MB")

    # 生成唯一文件名防止并发覆盖
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    # 检查重复上传：计算文件哈希，如果同一成员已上传过相同文件则跳过
    file_hash = hashlib.sha256(file_content).hexdigest()
    existing_doc = await db.scalar(
        select(DocumentRecord).where(
            DocumentRecord.member_id == target_member_id,
            DocumentRecord.file_hash == file_hash,
            DocumentRecord.status.in_(["uploaded", "persisted", "rule_conflict", "approved"]),
        )
    )
    if existing_doc:
        logger.info(f"Duplicate upload detected for member {target_member_id}, hash {file_hash[:8]}...")
        return DocumentUploadResponse(
            document_id=str(existing_doc.id),
            status="duplicate",
            message="该检查单已上传过，请勿重复上传",
        )
    
    # 尝试上传到 MinIO，失败则存本地
    storage_client = get_storage_client()
    logger.info(f"Storage client: {storage_client}")
    if storage_client:
        try:
            # 上传原图到 MinIO
            logger.info(f"Uploading to MinIO: original/{unique_filename}")
            file_url = storage_client.upload_file(file_content, f"original/{unique_filename}", "image/jpeg")
            logger.info(f"Uploaded to MinIO: {file_url}")
            
            # 脱敏后上传
            desensitized_bytes = desensitize_image(file_content)
            desensitized_filename = f"{uuid.uuid4().hex}.webp"
            desensitized_url = storage_client.upload_file(desensitized_bytes, f"desensitized/{desensitized_filename}", "image/webp")
            
            logger.info(f"Document {unique_filename} uploaded to MinIO")
        except Exception as e:
            logger.error(f"MinIO upload failed, falling back to local: {e}")
            # Fallback to local storage
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            file_url = file_path
            desensitized_url = None
    else:
        # Local storage fallback
        logger.warning("No storage client, using local storage")
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        file_url = file_path
        desensitized_url = None

    document = DocumentRecord(
        member_id=target_member_id,
        file_url=file_url,
        desensitized_url=desensitized_url,
        file_hash=file_hash,
        status="uploaded",
    )
    db.add(document)
    await db.flush()
    return DocumentUploadResponse(
        document_id=str(document.id),
        status=document.status,
        file_url=file_url,
        desensitized_url=desensitized_url,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: UUID, db: AsyncSession = Depends(get_db)):
    document = await db.scalar(select(DocumentRecord).where(DocumentRecord.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="检查单不存在")
    return DocumentResponse(
        id=str(document.id),
        member_id=str(document.member_id),
        status=document.status,
        file_url=document.file_url,
        desensitized_url=document.desensitized_url,
        uploaded_at=document.uploaded_at.isoformat() if document.uploaded_at else None,
    )


@router.get("/{document_id}/preview")
async def preview_document(document_id: UUID, db: AsyncSession = Depends(get_db)):
    """预览文档脱敏图片"""
    from fastapi.responses import Response
    
    document = await db.scalar(select(DocumentRecord).where(DocumentRecord.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="检查单不存在")
    
    if not document.desensitized_url:
        raise HTTPException(status_code=404, detail="脱敏图片不存在")
    
    # 从 MinIO 获取图片
    from ..services.storage_client import storage_client, storage_settings
    
    # 处理 URL 格式
    file_url = document.desensitized_url
    if file_url.startswith(f"{storage_settings.MINIO_BUCKET}/"):
        file_key = file_url[len(f"{storage_settings.MINIO_BUCKET}/"):]
    else:
        file_key = file_url
    
    try:
        image_bytes = storage_client.get_file(file_key)
        # 强制设置 content_type 确保浏览器渲染
        return Response(content=image_bytes, media_type="image/webp", headers={"Cache-Control": "no-cache"})
    except Exception as e:
        # 本地回退逻辑：如果 MinIO 404/网络不通，尝试从备份目录读取
        try:
            local_path = os.path.join("uploads", os.path.basename(file_key))
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return Response(content=f.read(), media_type="image/webp")
        except:
            pass
        logger.error(f"获取脱敏图片失败: {e}")
        raise HTTPException(status_code=404, detail="图片不可用")


@router.post("/{document_id}/submit-ocr", response_model=Dict[str, Any])
async def submit_ocr(document_id: UUID, document_type: str = "eye_axial_length", db: AsyncSession = Depends(get_db)):
    stmt = select(DocumentRecord).options(
        selectinload(DocumentRecord.member)
    ).where(DocumentRecord.id == document_id)
    document = await db.scalar(stmt)
    if document is None:
        raise HTTPException(status_code=404, detail="检查单不存在")

    from ..services.ocr_orchestrator import ocr_orchestrator

    result = await ocr_orchestrator.process_document(document.id, document.file_url, document_type)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "AI processing failed"))

    ocr_data = result["data"]

    existing_ocr = await db.scalar(
        select(OCRExtractionResult).where(OCRExtractionResult.document_id == document.id)
    )
    if existing_ocr is None:
        existing_ocr = OCRExtractionResult(
            document_id=document.id,
            raw_json=ocr_data["raw_json"],
            processed_items=ocr_data["processed_items"],
            confidence_score=ocr_data["confidence_score"],
            rule_conflict_details=ocr_data["rule_conflict_details"],
        )
        db.add(existing_ocr)
    else:
        existing_ocr.raw_json = ocr_data["raw_json"]
        existing_ocr.processed_items = ocr_data["processed_items"]
        existing_ocr.confidence_score = ocr_data["confidence_score"]
        existing_ocr.rule_conflict_details = ocr_data["rule_conflict_details"]

    document.status = result["status"]
    if result["status"] == "rule_conflict":
        await _ensure_review_task(db, document, "auto_created_from_rule_conflict")
    elif result["status"] == "approved":
        processed_items = ocr_data["processed_items"]
        try:
            # 强化解析逻辑：处理类似 "YYYY-MM-DD" 或带有说明字样的 JSON
            exam_date_str = processed_items.get("exam_date")
            if not exam_date_str and "date" in processed_items:
                exam_date_str = processed_items["date"]
            
            # 如果 OCR 返回的是复杂结构，尝试提取字符串
            if isinstance(exam_date_str, dict):
                exam_date_str = exam_date_str.get("value") or list(exam_date_str.values())[0]

            if not exam_date_str:
                raise ValueError("Missing exam_date")
            
            # 清理可能的额外字符 (仅保留 YYYY-MM-DD 部分)
            import re
            match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", str(exam_date_str))
            if match:
                exam_date = date.fromisoformat(match.group(1))
            else:
                exam_date = date.fromisoformat(str(exam_date_str))
        except Exception as e:
            logger.warning(f"解析检查日期失败: {e}, processed_items: {processed_items}")
            document.status = "rule_conflict"
            existing_ocr.rule_conflict_details = {"error": [f"exam_date_invalid: {str(e)}"]}
            await _ensure_review_task(db, document, "auto_created_from_invalid_exam_date")
            return {"document_id": str(document.id), "status": document.status}

        existing_exam_record = await db.scalar(
            select(ExamRecord).where(ExamRecord.document_id == document.id)
        )
        if existing_exam_record is None:
            member = await db.scalar(
                select(MemberProfile).where(MemberProfile.id == document.member_id)
            )
            if member is None:
                raise HTTPException(status_code=404, detail="成员不存在")

            exam_record = ExamRecord(
                document_id=document.id,
                member_id=document.member_id,
                exam_date=exam_date,
                institution_name=processed_items.get("institution"),
                baseline_age_months=_calculate_baseline_age_months(member.date_of_birth, exam_date),
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
                        confidence_score=ocr_data["confidence_score"],
                    )
                )
            else:
                existing_observation.value_numeric = obs_data["value_numeric"]
                existing_observation.unit = obs_data["unit"]
                existing_observation.confidence_score = ocr_data["confidence_score"]

        growth_payload = _build_axial_growth_payload(processed_items.get("observations", []))
        if growth_payload:
            existing_derived = await db.scalar(
                select(DerivedMetric).where(
                    DerivedMetric.member_id == document.member_id,
                    DerivedMetric.metric_category == "axial_growth_deviation",
                )
            )
            if existing_derived is None:
                db.add(
                    DerivedMetric(
                        member_id=document.member_id,
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

    return {"document_id": str(document.id), "status": document.status}


@router.get("/records/{record_id}", response_model=Dict[str, Any])
async def get_exam_record(record_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ExamRecord)
        .options(
            selectinload(ExamRecord.observations),
            selectinload(ExamRecord.document)
        )
        .where(ExamRecord.id == record_id)
    )
    record = await db.scalar(stmt)
    if record is None:
        raise HTTPException(status_code=404, detail="检查记录不存在")
    
    return {
        "id": str(record.id),
        "exam_date": record.exam_date.isoformat(),
        "institution": record.institution_name,
        "document": {
            "id": str(record.document.id),
            "desensitized_url": record.document.desensitized_url,
            "file_url": record.document.file_url,
        } if record.document else None,
        "observations": [
            {
                "metric_code": obs.metric_code,
                "value_numeric": obs.value_numeric,
                "value_text": obs.value_text,
                "unit": obs.unit,
                "side": obs.side,
                "is_abnormal": obs.is_abnormal,
            }
            for obs in record.observations
        ]
    }

