"""
[BUG-031] 首页成员卡片显示"尚无记录"的 UT 覆盖
验证 list_members 接口正确返回 last_check_date 和 pending_review_count
"""
import pytest
from datetime import date
from uuid import UUID


@pytest.mark.asyncio
async def test_list_members_returns_last_check_date(state_client):
    """
    验证：成员有检查记录时，list_members 返回 last_check_date
    """
    client, session_factory = state_client
    
    # 1. 创建成员
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "小明",
            "gender": "male",
            "date_of_birth": "2018-06-15",
            "member_type": "child",
        },
    )
    assert resp.status_code == 201
    member_id = resp.json()["id"]
    
    # 2. 无检查记录时，last_check_date 为 null
    list_resp = await client.get("/api/v1/members")
    assert list_resp.status_code == 200
    members = list_resp.json()
    target = [m for m in members if m["id"] == member_id][0]
    assert target["last_check_date"] is None
    
    # 3. 创建 DocumentRecord + ExamRecord
    from app.models.document import DocumentRecord
    from app.models.observation import ExamRecord
    from app.models.member import MemberProfile
    from sqlalchemy import select
    
    async with session_factory() as session:
        member = await session.scalar(
            select(MemberProfile).where(MemberProfile.id == UUID(member_id))
        )
        doc = DocumentRecord(
            member_id=member.id,
            file_url="test_001.jpg",
            status="approved",
        )
        session.add(doc)
        await session.flush()
        
        exam = ExamRecord(
            document_id=doc.id,
            member_id=member.id,
            exam_date=date(2026, 3, 29),
            baseline_age_months=93,
        )
        session.add(exam)
        await session.commit()
    
    # 4. 再次查询，last_check_date 应为 2026-03-29
    list_resp2 = await client.get("/api/v1/members")
    assert list_resp2.status_code == 200
    members2 = list_resp2.json()
    target2 = [m for m in members2 if m["id"] == member_id][0]
    assert target2["last_check_date"] == "2026-03-29"


@pytest.mark.asyncio
async def test_list_members_returns_pending_review_count(state_client):
    """
    验证：成员有待审核任务时，list_members 返回 pending_review_count > 0
    """
    client, session_factory = state_client
    
    # 1. 创建成员
    resp = await client.post(
        "/api/v1/members",
        json={
            "name": "小红",
            "gender": "female",
            "date_of_birth": "2019-01-01",
            "member_type": "child",
        },
    )
    assert resp.status_code == 201
    member_id = resp.json()["id"]
    
    # 2. 无待审核时，pending_review_count 为 0
    list_resp = await client.get("/api/v1/members")
    assert list_resp.status_code == 200
    members = list_resp.json()
    target = [m for m in members if m["id"] == member_id][0]
    assert target["pending_review_count"] == 0
    
    # 3. 创建 DocumentRecord + ReviewTask
    from app.models.document import DocumentRecord, ReviewTask
    from app.models.member import MemberProfile
    from sqlalchemy import select
    
    async with session_factory() as session:
        member = await session.scalar(
            select(MemberProfile).where(MemberProfile.id == UUID(member_id))
        )
        doc = DocumentRecord(
            member_id=member.id,
            file_url="test_002.jpg",
            status="pending_review",
        )
        session.add(doc)
        await session.flush()
        
        task = ReviewTask(
            document_id=doc.id,
            status="pending",
        )
        session.add(task)
        await session.commit()
    
    # 4. 再次查询，pending_review_count 应为 1
    list_resp2 = await client.get("/api/v1/members")
    assert list_resp2.status_code == 200
    members2 = list_resp2.json()
    target2 = [m for m in members2 if m["id"] == member_id][0]
    assert target2["pending_review_count"] == 1
