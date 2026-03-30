from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import uuid

from .db import get_db, engine
from .models.base import Base
# 确保所有模型已加载
from .models.member import Account, MemberProfile
from .models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from .models.observation import ExamRecord, Observation

app = FastAPI(title="家庭健康检查单管理 API", version="v1.0.0")

# 配置 CORS，支持本地 Next.js 开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # 原型阶段自动化同步数据库 (慎用)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "v1.2.0"}

# --------------------------------------------------------------------------
# 模块化路由占位 (后续可迁移至 Routers 目录)
# ------------------------------------

@app.post("/api/v1/members", response_model=Dict[str, Any])
async def create_member(data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    # 模拟创建成员逻辑
    return {"id": str(uuid.uuid4()), "status": "created"}

@app.get("/api/v1/members", response_model=List[Dict[str, Any]])
async def list_members(db: AsyncSession = Depends(get_db)):
    # 模拟列表返回
    return [{"id": str(uuid.uuid4()), "name": "测试成员", "member_type": "child"}]

@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # 实际应包含: 脱敏 -> 上传 MinIO -> 创建 DocumentRecord
    return {"document_id": str(uuid.uuid4()), "status": "uploaded"}

@app.get("/api/v1/members/{member_id}/trends")
async def get_trends(member_id: uuid.UUID, metric: str, db: AsyncSession = Depends(get_db)):
    # 返回符合 PRD 要求的趋势数据结构
    return {
        "metric": metric,
        "series": [
            {"date": "2026-01-01", "value": 24.1},
            {"date": "2026-03-30", "value": 24.35}
        ],
        "reference_range": "22.5-25.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
