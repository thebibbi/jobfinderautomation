from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class JobBase(BaseModel):
    company: str
    job_title: str
    job_description: str
    job_url: str
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    remote_type: Optional[str] = "unknown"
    job_type: Optional[str] = "full-time"
    source: str = "manual"


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    status: Optional[str] = None
    match_score: Optional[float] = None
    analysis_results: Optional[Dict[str, Any]] = None
    drive_folder_id: Optional[str] = None
    drive_folder_url: Optional[str] = None
    applied_date: Optional[datetime] = None


class JobResponse(JobBase):
    id: int
    job_id: str
    match_score: Optional[float]
    analysis_completed: bool
    status: str
    drive_folder_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobList(BaseModel):
    total: int
    jobs: List[JobResponse]
    skip: int
    limit: int


class JobFromExtension(BaseModel):
    jobTitle: str
    company: str
    location: Optional[str] = None
    jobDescription: str
    jobUrl: str
    salary: Optional[str] = None
    source: str


class JobProcessResponse(BaseModel):
    success: bool
    jobId: int
    matchScore: float
    message: str
    driveUrl: Optional[str] = None
    status: str
