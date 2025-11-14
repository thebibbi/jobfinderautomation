from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentBase(BaseModel):
    job_id: int
    document_type: str
    title: str
    content: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    drive_file_id: Optional[str]
    drive_file_url: Optional[str]
    generated_by: str
    version: int
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True
