import asyncio
import traceback
from uuid import uuid4
from datetime import date
from sqlalchemy import select
from app.db import async_session_factory, engine
from app.models.member import MemberProfile

async def debug_database():
    print("--- 正在诊断数据库连通性 ---")
    try:
        async with async_session_factory() as db:
            # 尝试执行一个简单的查询
            result = await db.execute(select(MemberProfile).limit(1))
            members = result.scalars().all()
            print(f"[SUCCESS] 数据库查询成功，当前成员数: {len(members)}")
    except Exception:
        print("[ERROR] 数据库访问崩溃！报错详情如下：")
        print(traceback.format_exc())

async def debug_api_logic():
    print("\n--- 正在诊断业务路由逻辑 ---")
    try:
        from app.routers.members import list_members
        async with async_session_factory() as db:
            # 手动调用 router 函数
            response = await list_members(db=db)
            print(f"[SUCCESS] 路由函数调用成功，返回条数: {len(response)}")
    except Exception:
        print("[ERROR] 业务路由逻辑崩溃！报错详情如下：")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_database())
    asyncio.run(debug_api_logic())
