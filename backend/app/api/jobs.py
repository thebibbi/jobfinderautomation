from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from loguru import logger

from ..database import get_db
from ..models.job import Job
from ..schemas.job import JobCreate, JobResponse, JobUpdate, JobList, JobFromExtension, JobProcessResponse
from ..services.integration_service import integrate_job_created
from ..services.google_drive_service import get_drive_service
from ..services.ai_service import AIService

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

    # Trigger integrations (company research, skills gap, etc.)
    await integrate_job_created(db, job.id, auto_process=True)

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


@router.get("/drive/list")
async def list_drive_files(folder_id: Optional[str] = None):
    """
    List files from Google Drive folder

    This helps users see what files are available to import
    """
    try:
        drive_service = get_drive_service()
        files = drive_service.list_files_in_folder(
            folder_id=folder_id,
            mime_type='application/vnd.google-apps.document'  # Only Google Docs
        )

        return {
            "success": True,
            "files": files,
            "count": len(files)
        }

    except Exception as e:
        logger.error(f"❌ Error listing Drive files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )


@router.post("/import-from-drive/{file_id}")
async def import_job_from_drive(
    file_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Import a job description from Google Drive

    This will:
    1. Download the file content from Drive
    2. Use AI to extract job information
    3. Create a job record
    4. Analyze the job
    """
    try:
        drive_service = get_drive_service()
        ai_service = AIService()

        # Get file metadata
        file_meta = drive_service.get_file_metadata(file_id)
        file_name = file_meta.get('name', 'Unknown')

        logger.info(f"📥 Importing job from Drive: {file_name}")

        # Download content
        jd_content = drive_service.download_file_content(file_id)

        if not jd_content or len(jd_content.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="File content is too short or empty"
            )

        # Use AI to extract job details from the JD
        extraction_prompt = f"""
You are extracting structured job information from a job description.

Job Description:
{jd_content}

Extract and return ONLY a JSON object with these fields:
- company: Company name (string)
- job_title: Job title (string)
- location: Location (string, or "Remote" if remote)
- job_description: Full job description (string, preserve original text)

Return ONLY valid JSON, no markdown, no explanations.
"""

        response = await ai_service.generate(extraction_prompt)

        # Parse AI response
        import json
        import re

        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            job_data = json.loads(json_match.group())
        else:
            # Fallback: create basic job with JD as description
            job_data = {
                "company": file_name.split('-')[0].strip() if '-' in file_name else "Unknown Company",
                "job_title": file_name.split('-')[1].strip() if len(file_name.split('-')) > 1 else "Unknown Position",
                "location": "Unknown",
                "job_description": jd_content
            }

        # Check if job already exists
        existing_job = db.query(Job).filter(
            Job.company == job_data['company'],
            Job.job_title == job_data['job_title']
        ).first()

        if existing_job:
            return {
                "success": True,
                "job_id": existing_job.id,
                "message": "Job already exists",
                "job": existing_job
            }

        # Create job record
        job = Job(
            company=job_data.get('company', 'Unknown Company'),
            job_title=job_data.get('job_title', 'Unknown Position'),
            job_description=job_data.get('job_description', jd_content),
            location=job_data.get('location'),
            source='google_drive',
            status='imported',
            drive_file_id=file_id,
            drive_file_url=file_meta.get('webViewLink')
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"✅ Created job from Drive: {job.company} - {job.job_title}")

        # Queue async processing (analysis, etc.)
        await integrate_job_created(db, job.id, auto_process=True)

        return {
            "success": True,
            "job_id": job.id,
            "message": f"Successfully imported: {job.job_title} at {job.company}",
            "job": job
        }

    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse AI response: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract job information from file"
        )
    except Exception as e:
        logger.error(f"❌ Error importing from Drive: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error importing job: {str(e)}"
        )
