from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional, Any
from uuid import UUID

class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    gender: str = Field(..., pattern="^(male|female)$")
    date_of_birth: date
    member_type: str = Field(..., pattern="^(child|adult|senior)$")

    @field_validator("gender", "member_type", mode="before")
    @classmethod
    def to_lower(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("出生日期不能是未来日期")
        return v

class MemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    gender: Optional[str] = Field(None, pattern="^(male|female)$")
    date_of_birth: Optional[date] = None
    member_type: Optional[str] = Field(None, pattern="^(child|adult|senior)$")

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("出生日期不能是未来日期")
        return v


class MemberResponse(BaseModel):
    id: UUID
    name: str
    gender: str
    date_of_birth: date
    member_type: str
    last_check_date: Optional[str] = None
    pending_review_count: int = 0

    class Config:
        from_attributes = True


class MemberDetailResponse(BaseModel):
    id: UUID
    name: str
    gender: str
    date_of_birth: date
    member_type: str

    class Config:
        from_attributes = True
