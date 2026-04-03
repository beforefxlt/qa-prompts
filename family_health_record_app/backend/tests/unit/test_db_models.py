import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.models.member import MemberProfile
from app.models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from app.models.observation import ExamRecord, Observation, DerivedMetric
from datetime import date

# 使用内存 SQLite 测试
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_member(db_session: AsyncSession):
    """[TC-P1-003, TC-P1-004, TC-P1-005] 验证成员档案模型的创建逻辑。"""
    member = MemberProfile(
        name="Little Bob",
        gender="male",
        date_of_birth=date(2020, 1, 1),
        member_type="child"
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    
    assert member.id is not None
    assert member.name == "Little Bob"
    assert member.member_type == "child"
    assert member.is_deleted is False

@pytest.mark.asyncio
async def test_create_document_record(db_session: AsyncSession):
    """[TC-P1-007, TC-P1-008, TC-P1-009] 验证文档记录（上传状态）的模型创建。"""
    member = MemberProfile(
        name="Test Member",
        gender="female",
        date_of_birth=date(1990, 5, 15),
        member_type="adult"
    )
    db_session.add(member)
    await db_session.flush()

    doc = DocumentRecord(
        member_id=member.id,
        file_url="/uploads/test.jpg",
        desensitized_url="/uploads/desensitized_test.jpg",
        status="uploaded"
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    assert doc.id is not None
    assert doc.member_id == member.id
    assert doc.status == "uploaded"

@pytest.mark.asyncio
async def test_create_ocr_result(db_session: AsyncSession):
    """[TC-P1-026] 验证 OCR 提取结果模型的创建与字段存储。"""
    member = MemberProfile(
        name="OCR Test",
        gender="male",
        date_of_birth=date(2015, 3, 20),
        member_type="child"
    )
    db_session.add(member)
    await db_session.flush()

    doc = DocumentRecord(
        member_id=member.id,
        file_url="/uploads/ocr_test.jpg",
        status="ocr_processing"
    )
    db_session.add(doc)
    await db_session.flush()

    ocr = OCRExtractionResult(
        document_id=doc.id,
        raw_json={"raw": "data"},
        processed_items={"items": []},
        confidence_score=0.95,
        rule_conflict_details=None
    )
    db_session.add(ocr)
    await db_session.commit()
    await db_session.refresh(ocr)

    assert ocr.document_id == doc.id
    assert ocr.confidence_score == 0.95

@pytest.mark.asyncio
async def test_create_review_task_with_null_reviewer(db_session: AsyncSession):
    """[TC-P1-025] 验证人工审核任务模型的创建（初始 reviewer 为空）。"""
    member = MemberProfile(
        name="Review Test",
        gender="female",
        date_of_birth=date(1985, 1, 1),
        member_type="senior"
    )
    db_session.add(member)
    await db_session.flush()

    doc = DocumentRecord(
        member_id=member.id,
        file_url="/uploads/review_test.jpg",
        status="pending_review"
    )
    db_session.add(doc)
    await db_session.flush()

    task = ReviewTask(
        document_id=doc.id,
        status="pending",
        reviewer_id=None,
        audit_trail={"events": []}
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.reviewer_id is None
    assert task.status == "pending"
