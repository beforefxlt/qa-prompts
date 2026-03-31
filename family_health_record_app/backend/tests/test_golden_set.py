from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
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
async def integration_env():
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
async def test_golden_set_axial_length_persisted(integration_env):
    client, session_factory = integration_env

    member_resp = await client.post(
        "/api/v1/members",
        json={
            "phone_or_email": "golden@test.com",
            "name": "Golden Kid",
            "gender": "female",
            "date_of_birth": "2018-01-01",
            "member_type": "child",
        },
    )
    assert member_resp.status_code == 201
    member_id = UUID(member_resp.json()["id"])

    image_path = Path(__file__).resolve().parents[2] / "tests" / "01.jpg"
    with image_path.open("rb") as f:
        files = {"file": ("01.jpg", f.read(), "image/jpeg")}
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": str(member_id)},
        files=files,
    )
    assert upload_resp.status_code == 201
    document_id = UUID(upload_resp.json()["document_id"])

    ocr_resp = await client.post(f"/api/v1/documents/{str(document_id)}/submit-ocr")
    assert ocr_resp.status_code == 200
    assert ocr_resp.json()["status"] == "persisted"

    async with session_factory() as session:
        exam_record = await session.scalar(select(ExamRecord).where(ExamRecord.document_id == document_id))
        assert exam_record is not None

        observations = (
            await session.scalars(
                select(Observation)
                .where(Observation.exam_record_id == exam_record.id, Observation.metric_code == "axial_length")
                .order_by(Observation.side.asc())
            )
        ).all()
        assert len(observations) == 2
        values = {obs.side: obs.value_numeric for obs in observations}
        assert values["left"] == 23.32
        assert values["right"] == 24.35

        derived = await session.scalar(
            select(DerivedMetric).where(
                DerivedMetric.member_id == member_id,
                DerivedMetric.metric_category == "axial_growth_deviation",
            )
        )
        assert derived is not None
        assert derived.value_json["left"] == 23.32
        assert derived.value_json["right"] == 24.35
