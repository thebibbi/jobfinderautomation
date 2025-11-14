from typing import Dict, Any
from loguru import logger
from datetime import datetime

from .claude_service import get_claude_service
from ..models.job import Job
from ..database import SessionLocal


class JobAnalyzer:
    """Service for analyzing job postings"""

    def __init__(self):
        self.claude = get_claude_service()

    async def analyze_job(self, job_id: int) -> Dict[str, Any]:
        """
        Analyze a job posting and update database

        Args:
            job_id: ID of job in database

        Returns:
            Analysis results
        """
        db = SessionLocal()
        try:
            # Get job from database
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")

            logger.info(f"🔍 Analyzing job: {job.company} - {job.job_title}")

            # Perform analysis using Claude
            analysis_result = await self.claude.analyze_job_fit(
                job_description=job.job_description,
                company=job.company,
                job_title=job.job_title
            )

            # Update job with analysis results
            job.match_score = analysis_result.get("match_score", 0)
            job.analysis_completed = True
            job.analysis_date = datetime.utcnow()
            job.analysis_results = analysis_result

            # Update status
            if analysis_result.get("should_apply", False):
                job.status = "ready_for_documents"
            else:
                job.status = "analyzed_no_action"

            db.commit()
            db.refresh(job)

            logger.info(f"✅ Analysis complete. Score: {job.match_score}%")

            return {
                "job_id": job.id,
                "match_score": job.match_score,
                "analysis": analysis_result,
                "status": job.status
            }

        except Exception as e:
            logger.error(f"❌ Error analyzing job {job_id}: {e}")
            db.rollback()
            raise
        finally:
            db.close()


# Singleton
_job_analyzer = None

def get_job_analyzer() -> JobAnalyzer:
    global _job_analyzer
    if _job_analyzer is None:
        _job_analyzer = JobAnalyzer()
    return _job_analyzer
