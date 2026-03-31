import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from backend.app.db import get_db
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.member import Account, MemberProfile
from backend.app.models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from backend.app.models.observation import ExamRecord, Observation, DerivedMetric


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_document_and_trend_flow(client: AsyncClient):
    create_member_resp = await client.post(
        "/api/v1/members",
        json={
            "phone_or_email": "api-flow@test.com",
            "name": "小明",
            "gender": "male",
            "date_of_birth": "2020-01-01",
            "member_type": "child",
        },
    )
    assert create_member_resp.status_code == 201
    member_data = create_member_resp.json()

    list_resp = await client.get("/api/v1/members")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    files = {"file": ("mock.jpg", b"dummy-content", "image/jpeg")}
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_data["id"]},
        files=files,
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert upload_data["status"] == "uploaded"

    trend_resp = await client.get(f"/api/v1/members/{member_data['id']}/trends?metric=axial_length")
    assert trend_resp.status_code == 200
    trend_data = trend_resp.json()
    assert trend_data["metric"] == "axial_length"
    assert trend_data["series"] == []
