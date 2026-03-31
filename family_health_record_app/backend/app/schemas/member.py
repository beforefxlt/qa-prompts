from pydantic import BaseModel
from datetime import date
from typing import Optional
from uuid import UUID


class MemberCreate(BaseModel):
    name: str
    gender: str
    date_of_birth: date
    member_type: str


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    member_type: Optional[str] = None


class MemberResponse(BaseModel):
    id: UUID
    name: str
    gender: str
    date_of_birth: date
    member_type: str

    class Config:
        from_attributes = True
