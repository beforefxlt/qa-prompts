import asyncio
import uuid
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# 导入后端模型 (注意路径)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models.member import MemberProfile
from backend.app.models.document import DocumentRecord
from backend.app.models.observation import ExamRecord, Observation

DATABASE_URL = "sqlite+aiosqlite:///../backend/health_record.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def seed():
    async with async_session_factory() as db:
        # 1. 查找或创建成员
        member_name = "指标测试成员"
        stmt = select(MemberProfile).where(MemberProfile.name == member_name)
        member = await db.scalar(stmt)
        
        if not member:
            member = MemberProfile(
                name=member_name,
                gender="male",
                date_of_birth=date(2018, 1, 1),
                member_type="child"
            )
            db.add(member)
            await db.flush()
        
        print(f"Member ID: {member.id}")
        
        # 2. 为该成员插入3个月的数据
        today = date.today()
        metrics = [
            {"code": "height", "unit": "cm", "values": [120.5, 121.2, 122.0]},
            {"code": "weight", "unit": "kg", "values": [22.1, 22.5, 23.0]},
            {"code": "glucose", "unit": "mmol/L", "values": [4.8, 5.1, 4.9]}
        ]
        
        for i in range(3):
            exam_date = today - timedelta(days=30 * (2 - i)) # 2个月前, 1个月前, 今天
            
            # 创建虚拟 Document
            doc = DocumentRecord(
                member_id=member.id,
                file_url=f"mock_url_{i}.jpg",
                status="persisted"
            )
            db.add(doc)
            await db.flush()
            
            # 创建 ExamRecord
            exam = ExamRecord(
                document_id=doc.id,
                member_id=member.id,
                exam_date=exam_date,
                institution_name="测试体检中心",
                baseline_age_months=72 + i # 约6岁
            )
            db.add(exam)
            await db.flush()
            
            # 插入观测指标
            for m in metrics:
                obs = Observation(
                    exam_record_id=exam.id,
                    metric_code=m["code"],
                    value_numeric=m["values"][i],
                    unit=m["unit"],
                    confidence_score=1.0
                )
                db.add(obs)
        
        await db.commit()
        print("SEED DATA COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    asyncio.run(seed())
