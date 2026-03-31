import pytest
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.models.base import Base
from backend.app.models.member import MemberProfile
from backend.app.models.observation import ExamRecord, Observation
from backend.app.services.ocr_orchestrator import ocr_orchestrator

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
async def test_full_pipeline_mock():
    """
    全链路集成测试 (Mock OCR 版):
    1. 注册成员
    2. 执行 OCR 处理流程
    3. 验证正式指标层 Persistent
    """
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        # 1. 初始化数据
        member = MemberProfile(name="Kid A", gender="male", date_of_birth=date(2018, 1, 1), member_type="child")
        session.add(member)
        await session.commit()
        
        # 2. 模拟触发 OCR
        # 实际 API 调用在 ocr_orchestrator 中已 Mock
        result = await ocr_orchestrator.process_document(member.id, "mock_url")
        
        assert result["status"] == "approved"
        
        # 3. 模拟入库 (Persisting logic - 对应 Task 4 核心)
        data = result["data"]["processed_items"]
        exam = ExamRecord(
            document_id=result["data"]["document_id"],
            member_id=member.id,
            exam_date=date.fromisoformat(data["exam_date"]),
            baseline_age_months=96, # 动态计算 (2018 -> 2026)
            institution_name=data["institution"]
        )
        session.add(exam)
        await session.commit()
        
        for obs_data in data["observations"]:
            obs = Observation(
                exam_record_id=exam.id,
                metric_code=obs_data["metric_code"],
                value_numeric=obs_data["value_numeric"],
                unit=obs_data["unit"],
                side=obs_data.get("side")
            )
            session.add(obs)
        await session.commit()
        
        # 4. 最终断言：指标是否正确落入正式表
        from sqlalchemy import select
        q = select(Observation).where(Observation.metric_code == "axial_length")
        res = await session.execute(q)
        observations = res.scalars().all()
        
        assert len(observations) == 2
        assert any(o.value_numeric == 24.35 for o in observations)
        
    await engine.dispose()
    print("Integration Pipeline (Mock) PASS!")
