import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models.base import Base
from app.models.member import MemberProfile
from app.models.document import DocumentRecord
from app.models.observation import ExamRecord, Observation

engine = create_async_engine('sqlite+aiosqlite:///./health_record.db', echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def populate_mock_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if member already exists
        result = await session.execute(select(MemberProfile).where(MemberProfile.name == "女儿 (晓萌)"))
        existing_member = result.scalars().first()
        
        if existing_member:
            member = existing_member
        else:
            member = MemberProfile(
                name="女儿 (晓萌)",
                gender="female",
                date_of_birth=date(2018, 5, 20),
                member_type="child"
            )
            session.add(member)
            await session.flush()

        member_id = str(member.id)

        # Clear old exam records for this member to avoid duplicate mock points
        exams_result = await session.execute(select(ExamRecord).where(ExamRecord.member_id == member.id))
        for exam in exams_result.scalars().all():
            await session.delete(exam)
        await session.flush()

        # Insert Mock Data
        exam_dates = [date(2025, 10, 1), date(2026, 1, 15), date(2026, 3, 30)]
        values_left = [22.8, 23.1, 23.5]
        
        for i in range(len(exam_dates)):
            document = DocumentRecord(
                member_id=member.id,
                file_url=f"mock://document_{i}.jpg",
                status="persisted"
            )
            session.add(document)
            await session.flush()

            exam = ExamRecord(
                document_id=document.id,
                member_id=member.id,
                exam_date=exam_dates[i],
                institution_name="Mock Hospital",
                baseline_age_months=(exam_dates[i].year - 2018)*12
            )
            session.add(exam)
            await session.flush()

            obs_left = Observation(
                exam_record_id=exam.id,
                metric_code="axial_length",
                value_numeric=values_left[i],
                unit="mm",
                side="left",
                is_abnormal=False
            )
            session.add(obs_left)

        await session.commit()
        print(f"===MEMBER_ID==={member_id}===")

if __name__ == "__main__":
    asyncio.run(populate_mock_data())
