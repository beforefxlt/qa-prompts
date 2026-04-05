"""BUG-051: 成人成员详情页无数据趋势展示 - 回归测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import get_db
from app.models.base import Base


@pytest.fixture
async def route_env():
    """测试环境 fixture"""
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
async def test_adult_member_can_get_trend_data(route_env):
    """BUG-051 回归测试: 成人成员应能获取趋势数据"""
    client, _ = route_env
    
    # 1. 创建成人成员
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "TestAdult",
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "member_type": "adult",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    mid = data["id"]
    assert data["member_type"] == "adult"
    
    # 2. 验证趋势 API 对成人成员返回数据（不是空响应）
    resp_vision = await client.get(f"/api/v1/members/{mid}/vision-dashboard")
    assert resp_vision.status_code == 200
    vision_data = resp_vision.json()
    assert "axial_length" in vision_data
    assert "vision_acuity" in vision_data
    
    resp_growth = await client.get(f"/api/v1/members/{mid}/growth-dashboard")
    assert resp_growth.status_code == 200
    growth_data = resp_growth.json()
    assert "height" in growth_data
    assert "weight" in growth_data
    
    # 3. 验证血检指标 API 对成人成员返回数据
    resp_blood = await client.get(f"/api/v1/members/{mid}/blood-dashboard")
    assert resp_blood.status_code == 200
    blood_data = resp_blood.json()
    assert "glucose" in blood_data
    assert "tc" in blood_data
    assert "tg" in blood_data
    assert "hdl" in blood_data
    assert "ldl" in blood_data
    assert "hemoglobin" in blood_data
    assert "hba1c" in blood_data
