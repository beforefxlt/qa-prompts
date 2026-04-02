from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, UUID as UUIDType, ForeignKey, DateTime, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id: Mapped[UUID] = mapped_column(UUIDType(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey("member_profiles.id"), index=True)
    file_url: Mapped[str] = mapped_column(String(512))
    desensitized_url: Mapped[Optional[str]] = mapped_column(String(512))
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    member: Mapped["MemberProfile"] = relationship("MemberProfile", back_populates="documents")
    ocr_result: Mapped[Optional["OCRExtractionResult"]] = relationship("OCRExtractionResult", back_populates="document")
    review_task: Mapped[Optional["ReviewTask"]] = relationship("ReviewTask", back_populates="document")
    exam_record: Mapped[Optional["ExamRecord"]] = relationship("ExamRecord", back_populates="document")


class OCRExtractionResult(Base):
    __tablename__ = "ocr_extraction_results"

    id: Mapped[UUID] = mapped_column(UUIDType(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("document_records.id"), unique=True)
    raw_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    processed_items: Mapped[Dict[str, Any]] = mapped_column(JSON)
    confidence_score: Mapped[float] = mapped_column(Float)
    rule_conflict_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["DocumentRecord"] = relationship("DocumentRecord", back_populates="ocr_result")


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[UUID] = mapped_column(UUIDType(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("document_records.id"))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    reviewer_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("member_profiles.id"), nullable=True)
    audit_trail: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    document: Mapped["DocumentRecord"] = relationship("DocumentRecord", back_populates="review_task")
    reviewer: Mapped[Optional["MemberProfile"]] = relationship("MemberProfile", back_populates="review_tasks")
