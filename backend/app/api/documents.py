from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.document import Document
from ..schemas.document import DocumentResponse

router = APIRouter()


@router.get("/job/{job_id}", response_model=List[DocumentResponse])
async def get_job_documents(job_id: int, db: Session = Depends(get_db)):
    """Get all documents for a specific job"""
    documents = db.query(Document).filter(Document.job_id == job_id).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a specific document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
