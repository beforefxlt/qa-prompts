from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, UUID as UUIDType, ForeignKey, Date, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base


class MemberProfile(Base):
    __tablename__ = "member_profiles"

    id: Mapped[UUID] = mapped_column(UUIDType(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(20))
    date_of_birth: Mapped[date] = mapped_column(Date())
    member_type: Mapped[str] = mapped_column(String(50))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    documents: Mapped[List["DocumentRecord"]] = relationship("DocumentRecord", back_populates="member")
    exam_records: Mapped[List["ExamRecord"]] = relationship("ExamRecord", back_populates="member")
    review_tasks: Mapped[List["ReviewTask"]] = relationship("ReviewTask", back_populates="reviewer")
    derived_metrics: Mapped[List["DerivedMetric"]] = relationship("DerivedMetric", back_populates="member")
