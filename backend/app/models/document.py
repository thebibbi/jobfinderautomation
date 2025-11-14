from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base


class DocumentType(str, enum.Enum):
    JOB_DESCRIPTION = "job_description"
    RESUME = "resume"
    COVER_LETTER_CONVERSATIONAL = "cover_letter_conversational"
    COVER_LETTER_FORMAL = "cover_letter_formal"
    ANALYSIS_REPORT = "analysis_report"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer, ForeignKey("jobs.id"))

    document_type = Column(SQLEnum(DocumentType))
    title = Column(String)
    content = Column(Text)

    # Google Drive
    drive_file_id = Column(String, nullable=True)
    drive_file_url = Column(String, nullable=True)

    # Generation metadata
    generated_by = Column(String, default="claude")  # claude, manual, template
    generation_prompt = Column(Text, nullable=True)

    # Version control
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.document_type} for Job {self.job_id}>"
