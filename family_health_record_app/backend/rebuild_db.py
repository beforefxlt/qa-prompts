import asyncio
import os
from app.db import engine
from app.models.base import Base
# 确保所有模型都被导入以进行元数据注册
from app.models.member import MemberProfile
from app.models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from app.models.observation import ExamRecord, Observation, DerivedMetric

async def rebuild_db():
    print("正在清空并重建数据库...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库重建成功。")

if __name__ == "__main__":
    asyncio.run(rebuild_db())
