from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Job Details
    job_id = Column(String, unique=True, index=True)  # External job ID
    company = Column(String, index=True)
    job_title = Column(String, index=True)
    job_description = Column(Text)
    job_url = Column(String)

    # Location & Meta
    location = Column(String)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    remote_type = Column(String)  # remote, hybrid, onsite
    job_type = Column(String)  # full-time, part-time, contract

    # Source
    source = Column(String)  # linkedin, indeed, manual, etc.
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # Analysis
    match_score = Column(Float, nullable=True)
    analysis_completed = Column(Boolean, default=False)
    analysis_date = Column(DateTime, nullable=True)
    analysis_results = Column(JSON, nullable=True)

    # Status Tracking
    status = Column(String, default="discovered")  # discovered, analyzed, documents_generated, applied, rejected, interview, offer
    applied_date = Column(DateTime, nullable=True)

    # Google Drive Integration
    drive_folder_id = Column(String, nullable=True)
    drive_folder_url = Column(String, nullable=True)

    # Relationships
    documents = relationship("Document", back_populates="job")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Job {self.company} - {self.job_title}>"
