from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models.job import Job
from ..services.job_analyzer import get_job_analyzer
from ..schemas.analysis import AnalysisRequest, AnalysisResponse

router = APIRouter()


@router.post("/{job_id}", response_model=AnalysisResponse)
async def analyze_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze a job posting for candidate fit

    This will:
    1. Use Claude to analyze the job description
    2. Score the match (0-100)
    3. Identify strengths and gaps
    4. Provide tailoring recommendations
    5. Update job record with results
    """
    # Check if job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if already analyzed
    if job.analysis_completed:
        return {
            "job_id": job.id,
            "match_score": job.match_score,
            "analysis": job.analysis_results,
            "message": "Job already analyzed. Returning cached results."
        }

    try:
        # Perform analysis
        analyzer = get_job_analyzer()
        result = await analyzer.analyze_job(job_id)

        return {
            "job_id": result["job_id"],
            "match_score": result["match_score"],
            "analysis": result["analysis"],
            "message": "Analysis completed successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing job: {str(e)}"
        )


@router.post("/{job_id}/re-analyze", response_model=AnalysisResponse)
async def re_analyze_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Force re-analysis of a job (ignores cached results)"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Reset analysis flags
    job.analysis_completed = False
    job.match_score = None
    job.analysis_results = None
    db.commit()

    # Run analysis
    analyzer = get_job_analyzer()
    result = await analyzer.analyze_job(job_id)

    return {
        "job_id": result["job_id"],
        "match_score": result["match_score"],
        "analysis": result["analysis"],
        "message": "Re-analysis completed successfully"
    }
