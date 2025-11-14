"""
Job Recommendations API

Endpoints for ML-based job recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from ..database import get_db
from ..schemas.recommendations import (
    RecommendationRequest, RecommendationResponse, JobRecommendationWithDetails,
    RecommendationFeedbackCreate, RecommendationFeedback,
    RecommendationDigest, DigestWithJobs, SimilarJobWithDetails,
    RecommendationDashboard, RecommendationMetrics, PreferenceUpdate,
    UserPreference
)
from ..services.recommendation_service import RecommendationService
from ..models.recommendations import JobRecommendation as JobRecommendationModel
from ..models.recommendations import SimilarJob as SimilarJobModel
from ..models.job import Job


router = APIRouter()


@router.post("/generate", response_model=RecommendationResponse)
def generate_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate personalized job recommendations

    Uses ML algorithms to recommend the best jobs based on user preferences
    and behavior.
    """
    try:
        service = RecommendationService(db)

        recommendations = service.get_recommendations(
            limit=request.limit,
            algorithm=request.algorithm,
            include_reasons=request.include_reasons,
            filter_applied=request.filter_applied,
            min_score=request.min_score
        )

        # Get full job details
        recommendations_with_details = []
        for rec in recommendations:
            job = db.query(Job).filter(Job.id == rec.job_id).first()
            if job:
                rec_detail = JobRecommendationWithDetails(
                    id=rec.id,
                    job_id=rec.job_id,
                    recommendation_score=rec.recommendation_score,
                    confidence=rec.confidence,
                    recommendation_reasons=rec.recommendation_reasons,
                    match_factors=rec.match_factors,
                    status=rec.status,
                    viewed_at=rec.viewed_at,
                    clicked_at=rec.clicked_at,
                    dismissed_at=rec.dismissed_at,
                    dismissal_reason=rec.dismissal_reason,
                    user_rating=rec.user_rating,
                    was_applied=rec.was_applied,
                    recommended_at=rec.recommended_at,
                    expires_at=rec.expires_at,
                    job_title=job.title,
                    company=job.company or "Unknown",
                    location=job.location,
                    salary_range=job.salary_range,
                    job_url=job.url
                )
                recommendations_with_details.append(rec_detail)

        # Get preferences count
        preferences_count = db.query(UserPreference).filter(
            UserPreference.is_active == True
        ).count()

        return RecommendationResponse(
            recommendations=recommendations_with_details,
            total_available=len(recommendations_with_details),
            algorithm_used=request.algorithm,
            generated_at=datetime.utcnow(),
            preferences_learned=preferences_count
        )

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[JobRecommendationWithDetails])
def get_active_recommendations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get active recommendations"""
    try:
        query = db.query(JobRecommendationModel)

        if status:
            query = query.filter(JobRecommendationModel.status == status)
        else:
            query = query.filter(JobRecommendationModel.status.in_(["pending", "viewed"]))

        # Get non-expired recommendations
        query = query.filter(
            (JobRecommendationModel.expires_at == None) |
            (JobRecommendationModel.expires_at > datetime.utcnow())
        )

        recommendations = query.order_by(
            JobRecommendationModel.recommendation_score.desc()
        ).limit(limit).all()

        # Add job details
        result = []
        for rec in recommendations:
            job = db.query(Job).filter(Job.id == rec.job_id).first()
            if job:
                result.append(JobRecommendationWithDetails(
                    id=rec.id,
                    job_id=rec.job_id,
                    recommendation_score=rec.recommendation_score,
                    confidence=rec.confidence,
                    recommendation_reasons=rec.recommendation_reasons,
                    match_factors=rec.match_factors,
                    status=rec.status,
                    viewed_at=rec.viewed_at,
                    clicked_at=rec.clicked_at,
                    dismissed_at=rec.dismissed_at,
                    dismissal_reason=rec.dismissal_reason,
                    user_rating=rec.user_rating,
                    was_applied=rec.was_applied,
                    recommended_at=rec.recommended_at,
                    expires_at=rec.expires_at,
                    job_title=job.title,
                    company=job.company or "Unknown",
                    location=job.location,
                    salary_range=job.salary_range,
                    job_url=job.url
                ))

        return result

    except Exception as e:
        logger.error(f"Error fetching recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{recommendation_id}/view")
def mark_recommendation_viewed(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """Mark recommendation as viewed"""
    try:
        rec = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.id == recommendation_id
        ).first()

        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        if not rec.viewed_at:
            rec.viewed_at = datetime.utcnow()
            rec.status = "viewed"
            db.commit()

        return {"message": "Recommendation marked as viewed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking recommendation viewed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{recommendation_id}/click")
def mark_recommendation_clicked(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """Mark recommendation as clicked"""
    try:
        rec = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.id == recommendation_id
        ).first()

        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        # Mark as viewed and clicked
        if not rec.viewed_at:
            rec.viewed_at = datetime.utcnow()

        if not rec.clicked_at:
            rec.clicked_at = datetime.utcnow()
            rec.status = "clicked"

            # Learn from click
            service = RecommendationService(db)
            service.learn_from_click(rec.job_id)

        db.commit()

        return {"message": "Recommendation marked as clicked"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking recommendation clicked: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{recommendation_id}/apply")
def mark_recommendation_applied(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """Mark recommendation as applied"""
    try:
        rec = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.id == recommendation_id
        ).first()

        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        rec.was_applied = True
        rec.status = "applied"

        # Learn from application
        service = RecommendationService(db)
        service.learn_from_application(rec.job_id)

        db.commit()

        return {"message": "Recommendation marked as applied"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking recommendation applied: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{recommendation_id}/dismiss")
def dismiss_recommendation(
    recommendation_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Dismiss a recommendation"""
    try:
        rec = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.id == recommendation_id
        ).first()

        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        rec.dismissed_at = datetime.utcnow()
        rec.dismissal_reason = reason
        rec.status = "dismissed"

        # Learn from dismissal
        service = RecommendationService(db)
        service.learn_from_dismissal(rec.job_id, reason)

        db.commit()

        return {"message": "Recommendation dismissed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=RecommendationFeedback)
def submit_feedback(
    feedback: RecommendationFeedbackCreate,
    db: Session = Depends(get_db)
):
    """Submit feedback on a recommendation"""
    try:
        service = RecommendationService(db)

        result = service.record_feedback(
            recommendation_id=feedback.recommendation_id,
            feedback_type=feedback.feedback_type,
            feedback_text=feedback.feedback_text,
            rating=feedback.rating
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{job_id}", response_model=List[SimilarJobWithDetails])
def get_similar_jobs(
    job_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Find jobs similar to the given job"""
    try:
        service = RecommendationService(db)
        similar_jobs = service.find_similar_jobs(job_id, limit)

        # Add job details
        result = []
        for similar in similar_jobs:
            job = db.query(Job).filter(Job.id == similar.similar_job_id).first()
            if job:
                result.append(SimilarJobWithDetails(
                    id=similar.id,
                    job_id=similar.job_id,
                    similar_job_id=similar.similar_job_id,
                    similarity_score=similar.similarity_score,
                    similarity_factors=similar.similarity_factors,
                    calculated_at=similar.calculated_at,
                    similar_job_title=job.title,
                    similar_job_company=job.company or "Unknown",
                    similar_job_location=job.location
                ))

        return result

    except Exception as e:
        logger.error(f"Error finding similar jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/digest/daily", response_model=DigestWithJobs)
def get_daily_digest(
    date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get daily recommendation digest"""
    try:
        from ..models.recommendations import RecommendationDigest as DigestModel

        # Default to today
        if not date:
            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Find digest for this date
        digest = db.query(DigestModel).filter(
            DigestModel.digest_type == "daily",
            DigestModel.digest_date >= date,
            DigestModel.digest_date < date + timedelta(days=1)
        ).first()

        if not digest:
            # Generate new digest
            service = RecommendationService(db)
            digest = service.generate_daily_digest()

            if not digest:
                raise HTTPException(status_code=404, detail="No recommendations for digest")

        # Get job details
        jobs = []
        for job_id in digest.job_ids:
            rec = db.query(JobRecommendationModel).filter(
                JobRecommendationModel.job_id == job_id
            ).first()

            if rec:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    jobs.append(JobRecommendationWithDetails(
                        id=rec.id,
                        job_id=rec.job_id,
                        recommendation_score=rec.recommendation_score,
                        confidence=rec.confidence,
                        recommendation_reasons=rec.recommendation_reasons,
                        match_factors=rec.match_factors,
                        status=rec.status,
                        viewed_at=rec.viewed_at,
                        clicked_at=rec.clicked_at,
                        dismissed_at=rec.dismissed_at,
                        dismissal_reason=rec.dismissal_reason,
                        user_rating=rec.user_rating,
                        was_applied=rec.was_applied,
                        recommended_at=rec.recommended_at,
                        expires_at=rec.expires_at,
                        job_title=job.title,
                        company=job.company or "Unknown",
                        location=job.location,
                        salary_range=job.salary_range,
                        job_url=job.url
                    ))

        return DigestWithJobs(
            id=digest.id,
            digest_type=digest.digest_type,
            digest_date=digest.digest_date,
            job_ids=digest.job_ids,
            total_recommendations=digest.total_recommendations,
            top_recommendation_id=digest.top_recommendation_id,
            highlights=digest.highlights,
            new_opportunities=digest.new_opportunities,
            sent=digest.sent,
            sent_at=digest.sent_at,
            opened=digest.opened,
            opened_at=digest.opened_at,
            created_at=digest.created_at,
            jobs=jobs
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily digest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences", response_model=List[UserPreference])
def get_user_preferences(
    preference_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get learned user preferences"""
    try:
        from ..models.recommendations import UserPreference as UserPreferenceModel

        query = db.query(UserPreferenceModel).filter(
            UserPreferenceModel.is_active == True
        )

        if preference_type:
            query = query.filter(UserPreferenceModel.preference_type == preference_type)

        preferences = query.order_by(
            UserPreferenceModel.preference_score.desc()
        ).all()

        return preferences

    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/update")
def update_preference(
    update: PreferenceUpdate,
    db: Session = Depends(get_db)
):
    """Manually update user preference"""
    try:
        from ..models.recommendations import UserPreference as UserPreferenceModel

        # Find existing preference
        pref = db.query(UserPreferenceModel).filter(
            UserPreferenceModel.preference_type == update.preference_type,
            UserPreferenceModel.preference_value == update.preference_value
        ).first()

        if not pref:
            # Create new
            if update.action == "set" and update.strength:
                pref = UserPreferenceModel(
                    preference_type=update.preference_type,
                    preference_value=update.preference_value,
                    preference_score=update.strength,
                    confidence=0.8,  # Higher confidence for explicit preferences
                    learned_from="explicit",
                    sample_size=1,
                    is_active=True
                )
                db.add(pref)
            else:
                raise HTTPException(status_code=404, detail="Preference not found")
        else:
            # Update existing
            if update.action == "increase":
                pref.preference_score = min(1.0, pref.preference_score + 0.1)
            elif update.action == "decrease":
                pref.preference_score = max(0.0, pref.preference_score - 0.1)
            elif update.action == "set" and update.strength is not None:
                pref.preference_score = update.strength

            pref.last_updated = datetime.utcnow()
            pref.confidence = min(1.0, pref.confidence + 0.1)

        db.commit()

        return {"message": "Preference updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preference: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=RecommendationMetrics)
def get_recommendation_metrics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get recommendation system metrics"""
    try:
        service = RecommendationService(db)

        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        metrics = service.calculate_metrics(period_start, period_end)

        return metrics

    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", response_model=RecommendationDashboard)
def get_dashboard(
    db: Session = Depends(get_db)
):
    """Get recommendation dashboard data"""
    try:
        from ..models.recommendations import (
            UserPreference as UserPreferenceModel,
            RecommendationModel as RecommendationModelDB
        )

        # Count by status
        active = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.status.in_(["pending", "viewed", "clicked"])
        ).count()

        pending = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.status == "pending"
        ).count()

        viewed = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.status == "viewed"
        ).count()

        applied = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.was_applied == True
        ).count()

        dismissed = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.status == "dismissed"
        ).count()

        # Performance metrics
        all_recs = db.query(JobRecommendationModel).all()
        avg_score = sum(r.recommendation_score for r in all_recs) / len(all_recs) if all_recs else 0

        ratings = [r.user_rating for r in all_recs if r.user_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        viewed_count = sum(1 for r in all_recs if r.viewed_at)
        clicked_count = sum(1 for r in all_recs if r.clicked_at)
        ctr = (clicked_count / viewed_count * 100) if viewed_count > 0 else 0

        applied_count = sum(1 for r in all_recs if r.was_applied)
        app_rate = (applied_count / clicked_count * 100) if clicked_count > 0 else 0

        # Top recommendations
        top_recs = db.query(JobRecommendationModel).filter(
            JobRecommendationModel.status.in_(["pending", "viewed"])
        ).order_by(
            JobRecommendationModel.recommendation_score.desc()
        ).limit(5).all()

        top_with_details = []
        for rec in top_recs:
            job = db.query(Job).filter(Job.id == rec.job_id).first()
            if job:
                top_with_details.append(JobRecommendationWithDetails(
                    id=rec.id,
                    job_id=rec.job_id,
                    recommendation_score=rec.recommendation_score,
                    confidence=rec.confidence,
                    recommendation_reasons=rec.recommendation_reasons,
                    match_factors=rec.match_factors,
                    status=rec.status,
                    viewed_at=rec.viewed_at,
                    clicked_at=rec.clicked_at,
                    dismissed_at=rec.dismissed_at,
                    dismissal_reason=rec.dismissal_reason,
                    user_rating=rec.user_rating,
                    was_applied=rec.was_applied,
                    recommended_at=rec.recommended_at,
                    expires_at=rec.expires_at,
                    job_title=job.title,
                    company=job.company or "Unknown",
                    location=job.location,
                    salary_range=job.salary_range,
                    job_url=job.url
                ))

        # Recent feedback
        recent_feedback = db.query(RecommendationFeedback).filter(
            RecommendationFeedback.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()

        # Preferences learned
        preferences = db.query(UserPreferenceModel).filter(
            UserPreferenceModel.is_active == True
        ).count()

        # Active model
        active_model = db.query(RecommendationModelDB).filter(
            RecommendationModelDB.is_active == True
        ).first()

        return RecommendationDashboard(
            active_recommendations=active,
            pending_recommendations=pending,
            viewed_recommendations=viewed,
            applied_recommendations=applied,
            dismissed_recommendations=dismissed,
            avg_recommendation_score=avg_score,
            avg_user_rating=avg_rating,
            click_through_rate=ctr,
            application_rate=app_rate,
            top_recommendations=top_with_details,
            recent_feedback_count=recent_feedback,
            preferences_learned=preferences,
            active_model=active_model
        )

    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
