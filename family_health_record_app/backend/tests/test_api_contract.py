from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models.base import Base
from app.models.member import Account, MemberProfile
from app.models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from app.models.observation import ExamRecord, Observation, DerivedMetric


@pytest_asyncio.fixture
async def contract_client():
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
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_api_contract_and_status_flow(contract_client: AsyncClient):
    member_resp = await contract_client.post(
        "/api/v1/members",
        json={
            "phone_or_email": "contract@test.com",
            "name": "契约成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    assert member_resp.status_code == 201
    member_data = member_resp.json()
    assert set(member_data.keys()) == {"id", "account_id", "name", "gender", "date_of_birth", "member_type"}

    list_resp = await contract_client.get("/api/v1/members")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    upload_resp = await contract_client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_data["id"]},
        files={"file": ("contract.jpg", b"contract", "image/jpeg")},
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert set(upload_data.keys()) == {"document_id", "status"}
    assert upload_data["status"] == "uploaded"
    document_id = upload_data["document_id"]

    document_before_resp = await contract_client.get(f"/api/v1/documents/{document_id}")
    assert document_before_resp.status_code == 200
    document_before_data = document_before_resp.json()
    assert set(document_before_data.keys()) == {"id", "member_id", "status", "file_url", "desensitized_url", "uploaded_at"}
    assert document_before_data["status"] == "uploaded"

    submit_resp = await contract_client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    assert set(submit_data.keys()) == {"document_id", "status"}
    assert submit_data["status"] in {"rule_conflict", "persisted"}

    document_after_resp = await contract_client.get(f"/api/v1/documents/{document_id}")
    assert document_after_resp.status_code == 200
    document_after_data = document_after_resp.json()
    assert document_after_data["status"] == submit_data["status"]

    trends_resp = await contract_client.get(f"/api/v1/members/{member_data['id']}/trends?metric=axial_length")
    assert trends_resp.status_code == 200
    trends_data = trends_resp.json()
    assert set(trends_data.keys()) == {"metric", "series", "reference_range", "alert_status"}
    assert trends_data["metric"] == "axial_length"

    UUID(member_data["id"])
    UUID(member_data["account_id"])
    UUID(document_id)


@pytest.mark.asyncio
async def test_trends_nonexistent_member_returns_404(contract_client: AsyncClient):
    missing_member_id = "00000000-0000-0000-0000-000000000001"
    resp = await contract_client.get(f"/api/v1/members/{missing_member_id}/trends?metric=axial_length")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_submit_ocr_idempotent_without_duplicate_observation(contract_client: AsyncClient):
    member_resp = await contract_client.post(
        "/api/v1/members",
        json={
            "phone_or_email": "idempotent@test.com",
            "name": "幂等成员",
            "gender": "male",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]

    upload_resp = await contract_client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("idem.jpg", b"idem", "image/jpeg")},
    )
    document_id = upload_resp.json()["document_id"]

    first_submit = await contract_client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    second_submit = await contract_client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    assert first_submit.status_code == 200
    assert second_submit.status_code == 200
    assert first_submit.json()["status"] == "persisted"
    assert second_submit.json()["status"] == "persisted"

    trend_resp = await contract_client.get(f"/api/v1/members/{member_id}/trends?metric=height")
    assert trend_resp.status_code == 200
    trend_data = trend_resp.json()
    assert len(trend_data["series"]) == 1
