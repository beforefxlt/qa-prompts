import io
from pathlib import Path
from uuid import UUID

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from PIL import Image

from app.db import get_db
from app.main import app
from app.models.base import Base
from app.models.member import MemberProfile
from app.models.document import DocumentRecord, OCRExtractionResult, ReviewTask
from app.models.observation import ExamRecord, Observation, DerivedMetric


@pytest.fixture
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


def _generate_synthetic_test_images():
    """为 Golden Set 生成合成测试图片（不同尺寸和颜色以模拟不同单据类型）"""
    golden_dir = Path(__file__).parent / "golden_set"
    golden_dir.mkdir(exist_ok=True)

    cases = [
        ("02_normal_axial.png", (200, 200, 200), "Standard axial length report"),
        ("03_height_report.png", (180, 190, 200), "Height-only growth report"),
        ("04_vision_test.png", (210, 205, 195), "Vision acuity report"),
    ]

    for filename, color, note in cases:
        img = Image.new("RGB", (800, 600), color=color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        output = buf.getvalue()
        (golden_dir / filename).write_bytes(output)

    return cases


GENERATED_IMAGES = _generate_synthetic_test_images()


@pytest.fixture
def golden_images():
    return GENERATED_IMAGES


def _make_fake_ocr_result(document_id, exam_date="2026-03-31"):
    return {
        "status": "approved",
        "data": {
            "document_id": document_id,
            "raw_json": {
                "exam_date": exam_date,
                "institution": "Golden Set Hospital",
                "observations": [
                    {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "left"},
                    {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "right"},
                ],
            },
            "processed_items": {
                "exam_date": exam_date,
                "institution": "Golden Set Hospital",
                "observations": [
                    {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "left"},
                    {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "right"},
                ],
            },
            "confidence_score": 0.95,
            "rule_conflict_details": None,
        },
    }


@pytest.mark.asyncio
async def test_golden_set_axial_length_persisted(integration_env, monkeypatch):
    """原始 Golden Set 测试（使用合成图片验证入库逻辑）。"""
    client, session_factory = integration_env

    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": "Golden Kid",
            "gender": "female",
            "date_of_birth": "2018-01-01",
            "member_type": "child",
        },
    )
    assert member_resp.status_code == 201
    member_id = UUID(member_resp.json()["id"])

    # 使用合成图片
    img = Image.new("RGB", (800, 600), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": str(member_id)},
        files={"file": ("golden.jpg", image_bytes, "image/jpeg")},
    )
    assert upload_resp.status_code == 201
    document_id = UUID(upload_resp.json()["document_id"])

    # Mock OCR 返回
    async def fake_ocr(doc_id, file_url, document_type="eye_axial_length"):
        return _make_fake_ocr_result(doc_id)

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_ocr)

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


@pytest.mark.asyncio
@pytest.mark.parametrize("image_name,color,note", GENERATED_IMAGES)
async def test_golden_set_synthetic_upload_and_ocr(integration_env, image_name, color, note, monkeypatch):
    """对 Golden Set 中所有合成图片执行上传和 OCR 流程，验证不 500。"""
    client, session_factory = integration_env

    member_resp = await client.post(
        "/api/v1/members",
        json={
            "name": f"Golden-{image_name}",
            "gender": "female",
            "date_of_birth": "2018-01-01",
            "member_type": "child",
        },
    )
    assert member_resp.status_code == 201
    member_id = member_resp.json()["id"]

    golden_dir = Path(__file__).parent / "golden_set"
    image_bytes = (golden_dir / image_name).read_bytes()
    ext = Path(image_name).suffix.replace(".", "")

    upload_resp = await client.post(
        "/api/v1/documents/upload",
        data={"member_id": member_id},
        files={"file": (image_name, image_bytes, f"image/{ext}")},
    )
    assert upload_resp.status_code == 201
    document_id = upload_resp.json()["document_id"]

    # Mock OCR 返回
    async def fake_ocr(doc_id, file_url, document_type="eye_axial_length"):
        return _make_fake_ocr_result(doc_id)

    from app.services import ocr_orchestrator as ocr_module
    monkeypatch.setattr(ocr_module.ocr_orchestrator, "process_document", fake_ocr)

    ocr_resp = await client.post(f"/api/v1/documents/{document_id}/submit-ocr")
    assert ocr_resp.status_code == 200
    assert ocr_resp.json()["status"] in {"persisted", "rule_conflict"}
