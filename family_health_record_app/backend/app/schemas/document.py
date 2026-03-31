from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str


class DocumentResponse(BaseModel):
    id: str
    member_id: str
    status: str
    file_url: Optional[str]
    desensitized_url: Optional[str]
    uploaded_at: Optional[str]
