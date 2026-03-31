import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.base import Base
from backend.app.models.member import Account, MemberProfile
from backend.app.models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from backend.app.models.observation import ExamRecord, Observation, DerivedMetric
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
async def test_create_account_and_member(db_session: AsyncSession):
    # 1. 创建账号
    account = Account(phone_or_email="test@example.com")
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    
    assert account.id is not None
    
    # 2. 创建成员
    member = MemberProfile(
        account_id=account.id,
        name="Little Bob",
        gender="male",
        date_of_birth=date(2020, 1, 1),
        member_type="child"
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    
    assert member.name == "Little Bob"
    assert member.member_type == "child"
