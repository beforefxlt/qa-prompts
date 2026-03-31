import pytest
import pytest_asyncio
from uuid import UUID
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models.base import Base
from app.models.member import Account, MemberProfile
from app.models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from app.models.observation import ExamRecord, Observation, DerivedMetric


@pytest_asyncio.fixture
async def state_client():
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
        yield client, session_factory
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_rule_conflict_generates_single_review_task(state_client, monkeypatch):
    client, session_factory = state_client

    member_resp = await client.post(
        "/api/v1/members",
        json={
            "phone_or_email": "rule-conflict@test.com",
            "name": "冲突成员",
            "gender": "female",
            "date_of_birth": "2018-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("conflict.jpg", b"conflict", "image/jpeg")},
    )
    document_id = UUID(upload_resp.json()["document_id"])

    async def fake_conflict(*args, **kwargs):
        return {
            "status": "rule_conflict",
            "data": {
                "document_id": document_id,
                "raw_json": {"exam_date": "2026-03-31"},
                "processed_items": {"exam_date": "2026-03-31", "observations": []},
                "confidence_score": 0.7,
                "rule_conflict_details": {"error": ["mock conflict"]},
            },
        }

    from app.services import ocr_orchestrator as ocr_module

    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_conflict)

    first = await client.post(f"/api/v1/documents/{str(document_id)}/submit-ocr")
    second = await client.post(f"/api/v1/documents/{str(document_id)}/submit-ocr")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "rule_conflict"
    assert second.json()["status"] == "rule_conflict"

    async with session_factory() as session:
        tasks = (await session.scalars(select(ReviewTask).where(ReviewTask.document_id == document_id))).all()
        assert len(tasks) == 1


@pytest.mark.asyncio
async def test_invalid_exam_date_from_ocr_should_not_500(state_client, monkeypatch):
    client, _ = state_client

    member_resp = await client.post(
        "/api/v1/members",
        json={
            "phone_or_email": "invalid-date@test.com",
            "name": "日期异常成员",
            "gender": "male",
            "date_of_birth": "2018-01-01",
            "member_type": "child",
        },
    )
    member_id = member_resp.json()["id"]
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": ("invalid-date.jpg", b"invalid-date", "image/jpeg")},
    )
    document_id = UUID(upload_resp.json()["document_id"])

    async def fake_bad_payload(*args, **kwargs):
        return {
            "status": "approved",
            "data": {
                "document_id": document_id,
                "raw_json": {"exam_date": "2026/03/31"},
                "processed_items": {
                    "exam_date": "not-a-date",
                    "institution": "Mock Hospital",
                    "observations": [{"metric_code": "height", "value_numeric": 128.0, "unit": "cm"}],
                },
                "confidence_score": 0.8,
                "rule_conflict_details": None,
            },
        }

    from app.services import ocr_orchestrator as ocr_module

    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_bad_payload)

    resp = await client.post(f"/api/v1/documents/{str(document_id)}/submit-ocr")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rule_conflict"
