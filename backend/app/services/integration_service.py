"""
Integration Orchestrator Service

Connects all features to work together seamlessly.
Handles cross-feature workflows and event propagation.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session

from .calendar_service import get_calendar_service
from .websocket_service import (
    notify_job_analyzed, notify_application_status_changed,
    notify_new_recommendations, notify_interview_scheduled,
    notify_skill_gap_completed, notify_follow_up_due
)
from .recommendation_service import RecommendationService
from .skills_service import SkillsService
from .research_service import ResearchService
from .followup_service import FollowUpService
from .ats_service import ATSService
from .cache_service import get_cache, CacheNamespace, CacheTTL


class IntegrationOrchestrator:
    """
    Orchestrates workflows across all features
    """

    def __init__(self, db: Session):
        self.db = db
        self.cache = get_cache()

    # ==================== Job Lifecycle Integration ====================

    async def on_job_created(self, job_id: int, auto_process: bool = True):
        """
        Handle new job creation

        Triggers:
        - Company research (if enabled)
        - Skills gap analysis (if enabled)
        - Recommendation generation update
        - WebSocket notification

        Args:
            job_id: ID of newly created job
            auto_process: Whether to automatically trigger analysis
        """
        logger.info(f"Integration: Processing new job {job_id}")

        try:
            from ..models.job import Job

            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return

            # 1. Auto-research company (async, cached)
            if job.company and auto_process:
                try:
                    research_service = ResearchService(self.db)
                    # Check cache first
                    cached = self.cache.get(
                        CacheNamespace.COMPANY_RESEARCH,
                        f"company:{job.company}"
                    )
                    if not cached:
                        logger.info(f"Auto-researching company: {job.company}")
                        research_service.research_company(job.company, auto_cache=True)
                except Exception as e:
                    logger.error(f"Company research failed: {e}")

            # 2. Skills gap analysis (if we have candidate skills)
            if auto_process:
                try:
                    skills_service = SkillsService(self.db)
                    # Check if we have candidate skills
                    from ..models.skills import CandidateSkill
                    has_skills = self.db.query(CandidateSkill).filter(
                        CandidateSkill.is_active == True
                    ).first()

                    if has_skills:
                        logger.info(f"Auto-analyzing skills gap for job {job_id}")
                        analysis = skills_service.analyze_skill_gaps(job_id, include_resources=False)

                        # Notify via WebSocket
                        await notify_skill_gap_completed(
                            job_id=job_id,
                            overall_match=analysis.overall_match_score
                        )
                except Exception as e:
                    logger.error(f"Skills gap analysis failed: {e}")

            # 3. Invalidate recommendations cache (new job available)
            self.cache.delete_pattern(CacheNamespace.RECOMMENDATIONS, "*")

            logger.info(f"Job {job_id} integration complete")

        except Exception as e:
            logger.error(f"Error in on_job_created integration: {e}")

    async def on_job_analyzed(
        self,
        job_id: int,
        match_score: float,
        recommendation: str,
        generate_docs: bool = True
    ):
        """
        Handle job analysis completion

        Triggers:
        - Document generation (if score >= 70)
        - Recommendation update
        - WebSocket notification
        - Cache storage

        Args:
            job_id: Job ID
            match_score: Match score (0-100)
            recommendation: Analysis recommendation
            generate_docs: Whether to generate documents
        """
        logger.info(f"Integration: Job {job_id} analyzed (score: {match_score})")

        try:
            # 1. Send WebSocket notification
            await notify_job_analyzed(
                job_id=job_id,
                match_score=match_score,
                recommendation=recommendation
            )

            # 2. Cache analysis result
            from ..models.analysis import Analysis
            analysis = self.db.query(Analysis).filter(
                Analysis.job_id == job_id
            ).order_by(Analysis.created_at.desc()).first()

            if analysis:
                self.cache.set(
                    CacheNamespace.JOB_ANALYSIS,
                    f"job:{job_id}",
                    {
                        "match_score": match_score,
                        "recommendation": recommendation,
                        "analyzed_at": analysis.created_at.isoformat()
                    },
                    ttl_seconds=CacheTTL.LONG
                )

            # 3. Update recommendations (learn from this job)
            if match_score >= 70:
                rec_service = RecommendationService(self.db)
                rec_service.learn_from_click(job_id)

            logger.info(f"Job {job_id} post-analysis integration complete")

        except Exception as e:
            logger.error(f"Error in on_job_analyzed integration: {e}")

    # ==================== Application Tracking Integration ====================

    async def on_application_status_changed(
        self,
        job_id: int,
        old_status: str,
        new_status: str,
        interview_data: Optional[Dict] = None
    ):
        """
        Handle application status changes

        Triggers:
        - Follow-up scheduling
        - Calendar event creation (for interviews)
        - WebSocket notification
        - Recommendation learning

        Args:
            job_id: Job ID
            old_status: Previous status
            new_status: New status
            interview_data: Interview details if scheduling interview
        """
        logger.info(f"Integration: Job {job_id} status change: {old_status} → {new_status}")

        try:
            from ..models.job import Job

            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return

            # 1. Send WebSocket notification
            await notify_application_status_changed(
                job_id=job_id,
                old_status=old_status,
                new_status=new_status
            )

            # 2. Schedule follow-ups based on status
            followup_service = FollowUpService(self.db)

            if new_status == "applied":
                # Schedule post-application follow-up sequence
                logger.info(f"Scheduling post-application follow-ups for job {job_id}")
                followup_service.schedule_followup_sequence(
                    job_id=job_id,
                    sequence_name="post_application",
                    variables={
                        "job_title": job.title,
                        "company": job.company or "the company"
                    }
                )

            elif new_status == "interviewing":
                # Schedule post-interview follow-up
                logger.info(f"Scheduling post-interview follow-ups for job {job_id}")
                followup_service.schedule_followup_sequence(
                    job_id=job_id,
                    sequence_name="post_interview",
                    variables={
                        "job_title": job.title,
                        "company": job.company or "the company"
                    }
                )

            # 3. Create calendar event if interview scheduled
            if new_status == "interview_scheduled" and interview_data:
                calendar = get_calendar_service()

                event = calendar.create_interview_event(
                    job_title=job.title,
                    company=job.company or "Unknown Company",
                    interview_type=interview_data.get("interview_type", "phone"),
                    start_time=interview_data.get("scheduled_date"),
                    duration_minutes=interview_data.get("duration_minutes", 60),
                    location=interview_data.get("location"),
                    interviewer_email=interview_data.get("interviewer_email"),
                    notes=interview_data.get("notes")
                )

                if event:
                    # Store event ID in interview record
                    from ..models.application import Interview
                    interview = self.db.query(Interview).filter(
                        Interview.job_id == job_id,
                        Interview.scheduled_date == interview_data.get("scheduled_date")
                    ).first()

                    if interview:
                        interview.calendar_event_id = event.get("id")
                        self.db.commit()

                    # Notify via WebSocket
                    await notify_interview_scheduled(
                        job_id=job_id,
                        interview_data=interview_data
                    )

            # 4. Learn from outcomes
            rec_service = RecommendationService(self.db)

            if new_status in ["applied", "interviewing", "offer_received"]:
                # Positive signal - learn preferences
                rec_service.learn_from_application(job_id)

            elif new_status in ["rejected", "withdrawn"]:
                # Negative signal
                rec_service.learn_from_dismissal(job_id, reason=f"Status: {new_status}")

            # 5. Invalidate relevant caches
            self.cache.delete(CacheNamespace.JOB_DETAILS, f"job:{job_id}")
            self.cache.delete_pattern(CacheNamespace.STATS, "*")

            logger.info(f"Application status change integration complete")

        except Exception as e:
            logger.error(f"Error in on_application_status_changed integration: {e}")

    # ==================== Recommendation Integration ====================

    async def on_recommendations_generated(
        self,
        count: int,
        top_recommendations: list
    ):
        """
        Handle new recommendations generation

        Triggers:
        - WebSocket notification
        - Cache update
        - Digest creation (if appropriate)

        Args:
            count: Number of recommendations
            top_recommendations: Top recommendation details
        """
        logger.info(f"Integration: {count} new recommendations generated")

        try:
            # 1. Send WebSocket notification
            await notify_new_recommendations(
                count=count,
                top_recommendations=top_recommendations
            )

            # 2. Cache top recommendations
            self.cache.set(
                CacheNamespace.RECOMMENDATIONS,
                "latest",
                {
                    "count": count,
                    "top": top_recommendations,
                    "generated_at": datetime.utcnow().isoformat()
                },
                ttl_seconds=CacheTTL.MEDIUM
            )

            logger.info("Recommendations integration complete")

        except Exception as e:
            logger.error(f"Error in on_recommendations_generated integration: {e}")

    # ==================== Follow-up Integration ====================

    async def on_follow_up_due(
        self,
        follow_up_id: int,
        job_id: int
    ):
        """
        Handle follow-up due notification

        Triggers:
        - WebSocket notification
        - Calendar reminder (if not exists)

        Args:
            follow_up_id: Follow-up ID
            job_id: Associated job ID
        """
        logger.info(f"Integration: Follow-up {follow_up_id} due for job {job_id}")

        try:
            from ..models.job import Job
            from ..models.followup import FollowUp

            job = self.db.query(Job).filter(Job.id == job_id).first()
            follow_up = self.db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()

            if job and follow_up:
                # Send WebSocket notification
                await notify_follow_up_due(
                    follow_up_id=follow_up_id,
                    job_title=job.title,
                    company=job.company or "Unknown"
                )

            logger.info("Follow-up due integration complete")

        except Exception as e:
            logger.error(f"Error in on_follow_up_due integration: {e}")

    # ==================== Utility Methods ====================

    async def trigger_daily_recommendations(self):
        """
        Generate daily recommendations and digest

        Called by scheduler/cron job
        """
        logger.info("Integration: Generating daily recommendations")

        try:
            rec_service = RecommendationService(self.db)

            # Generate recommendations
            recommendations = rec_service.get_recommendations(
                limit=10,
                algorithm="hybrid",
                include_reasons=True,
                filter_applied=True,
                min_score=60.0
            )

            if recommendations:
                # Create digest
                digest = rec_service.generate_daily_digest()

                # Notify
                top_recs = [
                    {
                        "job_id": r.job_id,
                        "score": r.recommendation_score
                    }
                    for r in recommendations[:5]
                ]

                await self.on_recommendations_generated(
                    count=len(recommendations),
                    top_recommendations=top_recs
                )

            logger.info("Daily recommendations complete")

        except Exception as e:
            logger.error(f"Error in trigger_daily_recommendations: {e}")

    async def process_new_job_batch(self, job_ids: list):
        """
        Process multiple new jobs efficiently

        Args:
            job_ids: List of job IDs to process
        """
        logger.info(f"Integration: Batch processing {len(job_ids)} jobs")

        for job_id in job_ids:
            await self.on_job_created(job_id, auto_process=True)

        # Generate recommendations after batch
        await self.trigger_daily_recommendations()

        logger.info("Batch processing complete")


# Helper functions for easy integration

async def integrate_job_created(db: Session, job_id: int, auto_process: bool = True):
    """Convenience function for job creation integration"""
    orchestrator = IntegrationOrchestrator(db)
    await orchestrator.on_job_created(job_id, auto_process)


async def integrate_job_analyzed(
    db: Session,
    job_id: int,
    match_score: float,
    recommendation: str
):
    """Convenience function for job analysis integration"""
    orchestrator = IntegrationOrchestrator(db)
    await orchestrator.on_job_analyzed(job_id, match_score, recommendation)


async def integrate_status_change(
    db: Session,
    job_id: int,
    old_status: str,
    new_status: str,
    interview_data: Optional[Dict] = None
):
    """Convenience function for status change integration"""
    orchestrator = IntegrationOrchestrator(db)
    await orchestrator.on_application_status_changed(
        job_id, old_status, new_status, interview_data
    )
