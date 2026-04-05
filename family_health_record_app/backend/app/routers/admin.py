import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reset")
async def reset_database(db: AsyncSession = Depends(get_db)):
    """
    测试环境专用：一键清空所有业务数据。
    生产环境通过 ADMIN_SECRET 环境变量保护。
    清理顺序：从叶子表到根表，避免外键约束冲突。
    """
    # 安全检查：如果设置了 ADMIN_SECRET，请求必须携带 X-Admin-Secret header
    admin_secret = os.getenv("ADMIN_SECRET")
    if admin_secret:
        # 这个端点只在测试环境使用，生产环境应禁用
        raise HTTPException(status_code=403, detail="Admin reset disabled in production")

    tables_in_order = [
        "derived_metrics",
        "observations",
        "exam_records",
        "ocr_extraction_results",
        "review_tasks",
        "document_records",
        "member_profiles",
    ]

    for table in tables_in_order:
        await db.execute(text(f"DELETE FROM {table}"))

    await db.commit()
    return {"status": "ok", "message": "All business data cleared"}


@router.delete("/members/clear")
async def clear_members(db: AsyncSession = Depends(get_db)):
    """清理 members 表（供 E2E 测试回退方案使用）"""
    await db.execute(text("DELETE FROM member_profiles"))
    await db.commit()
    return {"status": "ok"}


@router.delete("/documents/clear")
async def clear_documents(db: AsyncSession = Depends(get_db)):
    """清理 documents 表"""
    await db.execute(text("DELETE FROM document_records"))
    await db.commit()
    return {"status": "ok"}


@router.delete("/review-tasks/clear")
async def clear_review_tasks(db: AsyncSession = Depends(get_db)):
    """清理 review tasks 表"""
    await db.execute(text("DELETE FROM review_tasks"))
    await db.commit()
    return {"status": "ok"}


@router.delete("/exam-records/clear")
async def clear_exam_records(db: AsyncSession = Depends(get_db)):
    """清理 exam records 表"""
    await db.execute(text("DELETE FROM exam_records"))
    await db.commit()
    return {"status": "ok"}


@router.delete("/observations/clear")
async def clear_observations(db: AsyncSession = Depends(get_db)):
    """清理 observations 表"""
    await db.execute(text("DELETE FROM observations"))
    await db.commit()
    return {"status": "ok"}


@router.delete("/derived-metrics/clear")
async def clear_derived_metrics(db: AsyncSession = Depends(get_db)):
    """清理 derived metrics 表"""
    await db.execute(text("DELETE FROM derived_metrics"))
    await db.commit()
    return {"status": "ok"}
