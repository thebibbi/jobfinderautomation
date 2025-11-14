from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from loguru import logger

from ..database import get_db
from ..models.job import Job
from ..schemas.job import JobCreate, JobResponse, JobUpdate, JobList, JobFromExtension, JobProcessResponse

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
):
    """Create a new job entry"""
    # Check if job already exists
    existing_job = db.query(Job).filter(Job.job_url == job_data.job_url).first()
    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job already exists in database"
        )

    # Create job
    job = Job(**job_data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get("/", response_model=JobList)
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """List all jobs with optional filters"""
    query = db.query(Job)

    if status_filter:
        query = query.filter(Job.status == status_filter)

    if min_score is not None:
        query = query.filter(Job.match_score >= min_score)

    total = query.count()
    jobs = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "jobs": jobs,
        "skip": skip,
        "limit": limit
    }


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: Session = Depends(get_db)
):
    """Update job details"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Update fields
    for field, value in job_update.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    db.delete(job)
    db.commit()

    return None


@router.post("/process", response_model=JobProcessResponse)
async def process_job_from_extension(
    job_data: JobFromExtension,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process a job from browser extension

    This is the main endpoint called by the Chrome extension.
    It will:
    1. Save job to database
    2. Trigger analysis
    3. If score >= threshold, generate documents
    4. Upload to Google Drive
    5. Send email notification
    """
    try:
        # Check if job already exists
        existing_job = db.query(Job).filter(Job.job_url == job_data.jobUrl).first()

        if existing_job:
            return {
                "success": True,
                "jobId": existing_job.id,
                "matchScore": existing_job.match_score or 0,
                "message": "Job already processed",
                "driveUrl": existing_job.drive_folder_url,
                "status": existing_job.status
            }

        # Create job record
        job = Job(
            job_id=f"{job_data.source}_{hash(job_data.jobUrl)}",
            company=job_data.company,
            job_title=job_data.jobTitle,
            job_description=job_data.jobDescription,
            job_url=job_data.jobUrl,
            location=job_data.location or "Unknown",
            salary_min=None,
            salary_max=None,
            source=job_data.source,
            status="processing"
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        # Queue async processing
        from ..tasks.job_tasks import process_job_complete_workflow
        background_tasks.add_task(process_job_complete_workflow, job.id)

        return {
            "success": True,
            "jobId": job.id,
            "matchScore": 0,  # Will be calculated
            "message": "Job queued for processing",
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"❌ Error processing job from extension: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing job: {str(e)}"
        )
