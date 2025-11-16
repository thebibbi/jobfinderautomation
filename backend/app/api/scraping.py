from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from ..services.scraper_service import get_scraper_service
from ..config import settings

router = APIRouter()


class ScrapeRequest(BaseModel):
    job_titles: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    sources: List[str] = ["linkedin", "indeed"]
    max_per_source: int = 25
    min_semantic_score: float = 40.0
    auto_analyze: bool = False  # Automatically trigger analysis for matched jobs


class TriggerScrapeRequest(BaseModel):
    platform: str  # linkedin, indeed, glassdoor
    keywords: str
    location: Optional[str] = None
    max_results: Optional[int] = 20


@router.post("/search")
async def search_jobs(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Search for jobs across multiple platforms

    This will:
    1. Scrape jobs from specified sources
    2. Perform semantic matching against candidate profile
    3. Save matched jobs to database
    4. Optionally trigger analysis for high-scoring jobs
    """
    try:
        scraper = get_scraper_service()

        # Use defaults if not provided
        job_titles = request.job_titles or settings.job_titles_list
        locations = request.locations or settings.locations_list

        # Scrape jobs
        jobs = scraper.scrape_jobs(
            job_titles=job_titles,
            locations=locations,
            sources=request.sources,
            max_per_source=request.max_per_source,
            min_semantic_score=request.min_semantic_score
        )

        # Save to database
        created_ids = scraper.save_scraped_jobs(jobs)

        # Optionally trigger analysis
        if request.auto_analyze and created_ids:
            from ..tasks.job_tasks import analyze_job_task
            for job_id in created_ids:
                background_tasks.add_task(analyze_job_task, job_id)

        return {
            "success": True,
            "total_scraped": len(jobs),
            "saved_to_database": len(created_ids),
            "job_ids": created_ids,
            "message": f"Found {len(jobs)} jobs, saved {len(created_ids)} new ones"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping jobs: {str(e)}"
        )


@router.post("/trigger")
async def trigger_scrape(request: TriggerScrapeRequest, background_tasks: BackgroundTasks):
    """
    Trigger a job scraping task (called from the UI modal)
    
    This endpoint matches the frontend ScrapeJobsModal format
    """
    try:
        from ..tasks.job_tasks import scrape_jobs_task
        
        # Convert keywords to list of job titles
        job_titles = [title.strip() for title in request.keywords.split(',')]
        locations = [request.location] if request.location else []
        
        # Start scraping task in background
        task_id = f"scrape_{request.platform}_{hash(request.keywords)}"
        
        background_tasks.add_task(
            scrape_jobs_task,
            job_titles=job_titles,
            locations=locations,
            sources=[request.platform],
            max_per_source=request.max_results or 20
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Scraping started for {request.keywords} on {request.platform}",
            "details": {
                "platform": request.platform,
                "keywords": request.keywords,
                "location": request.location,
                "max_results": request.max_results
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting scrape task: {str(e)}"
        )


@router.get("/status/{task_id}")
async def get_scrape_status(task_id: str):
    """Get status of a scraping task"""
    # TODO: Implement task status tracking with Celery or Redis
    return {
        "task_id": task_id,
        "status": "running",
        "message": "Scraping in progress..."
    }


@router.get("/supported-sources")
async def get_supported_sources():
    """Get list of supported job boards"""
    return {
        "sources": [
            {"id": "linkedin", "name": "LinkedIn", "status": "active"},
            {"id": "indeed", "name": "Indeed", "status": "active"},
            {"id": "glassdoor", "name": "Glassdoor", "status": "coming_soon"}
        ]
    }
