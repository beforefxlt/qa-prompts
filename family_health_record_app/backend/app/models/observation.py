from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import String, UUID as UUIDType, ForeignKey, Date, Boolean, DateTime, Float, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base


class ExamRecord(Base):
    __tablename__ = "exam_records"

    id: Mapped[UUID] = mapped_column(UUIDType(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("document_records.id"), unique=True, nullable=True)
    member_id: Mapped[UUID] = mapped_column(ForeignKey("member_profiles.id"), index=True)
    exam_date: Mapped[date] = mapped_column(Date())
    institution_name: Mapped[Optional[str]] = mapped_column(String(255))
    baseline_age_months: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    member: Mapped["MemberProfile"] = relationship("MemberProfile", back_populates="exam_records")
    document: Mapped["DocumentRecord"] = relationship("DocumentRecord", back_populates="exam_record")
    observations: Mapped[List["Observation"]] = relationship("Observation", back_populates="exam_record", cascade="all, delete-orphan")


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[UUID] = mapped_column(UUIDType(as_uuid=True), primary_key=True, default=uuid4)
    exam_record_id: Mapped[UUID] = mapped_column(ForeignKey("exam_records.id"), index=True)
    metric_code: Mapped[str] = mapped_column(String(50))
    value_numeric: Mapped[float] = mapped_column(Float)
    value_text: Mapped[Optional[str]] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(20))
    side: Mapped[Optional[str]] = mapped_column(String(10))
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False)
    reference_range: Mapped[Optional[str]] = mapped_column(String(255))
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)

    exam_record: Mapped["ExamRecord"] = relationship("ExamRecord", back_populates="observations")


class DerivedMetric(Base):
    __tablename__ = "derived_metrics"

    id: Mapped[UUID] = mapped_column(UUIDType(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey("member_profiles.id"))
    metric_category: Mapped[str] = mapped_column(String(50))
    value_numeric: Mapped[Optional[float]] = mapped_column(Float)
    value_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    algorithm_version: Mapped[str] = mapped_column(String(50))
    calculation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    member: Mapped["MemberProfile"] = relationship("MemberProfile", back_populates="derived_metrics")
