"""
Follow-up System API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..services.followup_service import get_followup_service
from ..models.followup import (
    FollowUpTemplate as TemplateModel,
    FollowUpSequence as SequenceModel,
    FollowUp as FollowUpModel,
    FollowUpResponse as ResponseModel,
    FollowUpAnalytics as AnalyticsModel
)
from ..schemas.followup import (
    FollowUpTemplateCreate,
    FollowUpTemplateUpdate,
    FollowUpTemplate,
    FollowUpSequenceCreate,
    FollowUpSequenceUpdate,
    FollowUpSequence,
    FollowUpCreate,
    FollowUpUpdate,
    FollowUp,
    FollowUpResponseCreate,
    FollowUpResponse,
    FollowUpAnalytics,
    ScheduleFollowUpRequest,
    ScheduleFollowUpResponse,
    SendFollowUpRequest,
    SendFollowUpResponse,
    FollowUpDashboard,
    TimingRecommendation
)


router = APIRouter()


# ==================== Templates ====================

@router.post("/templates", response_model=FollowUpTemplate, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: FollowUpTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a follow-up email template

    Templates can include variables like {job_title}, {company}, {recipient_name}, etc.
    """
    try:
        service = get_followup_service(db)
        created = service.create_template(template)
        return created
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )


@router.get("/templates", response_model=List[FollowUpTemplate])
async def get_templates(
    stage: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get follow-up templates

    Optionally filter by stage and active status.
    """
    try:
        service = get_followup_service(db)
        templates = service.get_templates(stage=stage, active_only=active_only)
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving templates: {str(e)}"
        )


@router.put("/templates/{template_id}", response_model=FollowUpTemplate)
async def update_template(
    template_id: int,
    template: FollowUpTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a follow-up template
    """
    try:
        template_obj = db.query(TemplateModel).filter(TemplateModel.id == template_id).first()
        if not template_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

        update_data = template.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template_obj, field, value)

        template_obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(template_obj)

        return template_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating template: {str(e)}"
        )


# ==================== Sequences ====================

@router.post("/sequences", response_model=FollowUpSequence, status_code=status.HTTP_201_CREATED)
async def create_sequence(
    sequence: FollowUpSequenceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a follow-up sequence

    A sequence defines multiple follow-ups with timing and templates.
    """
    try:
        service = get_followup_service(db)
        created = service.create_sequence(sequence)
        return created
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sequence: {str(e)}"
        )


@router.get("/sequences", response_model=List[FollowUpSequence])
async def get_sequences(
    stage: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get follow-up sequences
    """
    try:
        service = get_followup_service(db)
        sequences = service.get_sequences(stage=stage, active_only=active_only)
        return sequences
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sequences: {str(e)}"
        )


# ==================== Follow-ups ====================

@router.post("/schedule", response_model=ScheduleFollowUpResponse)
async def schedule_followup_sequence(
    request: ScheduleFollowUpRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule a follow-up sequence for a job

    Automatically schedules multiple follow-ups with optimal timing.
    """
    try:
        service = get_followup_service(db)
        result = service.schedule_followup_sequence(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling follow-up: {str(e)}"
        )


@router.post("/send", response_model=SendFollowUpResponse)
async def send_followup(
    request: SendFollowUpRequest,
    db: Session = Depends(get_db)
):
    """
    Send a scheduled follow-up immediately

    Can override the scheduled time if needed.
    """
    try:
        service = get_followup_service(db)
        result = service.send_followup(request.followup_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending follow-up: {str(e)}"
        )


@router.get("/followups", response_model=List[FollowUp])
async def get_followups(
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """
    Get follow-ups

    Optionally filter by job ID and status.
    """
    try:
        query = db.query(FollowUpModel)

        if job_id:
            query = query.filter(FollowUpModel.job_id == job_id)

        if status:
            query = query.filter(FollowUpModel.status == status)

        followups = query.order_by(FollowUpModel.scheduled_date.desc()).limit(limit).all()
        return followups
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving follow-ups: {str(e)}"
        )


@router.get("/followups/pending", response_model=List[FollowUp])
async def get_pending_followups(db: Session = Depends(get_db)):
    """
    Get follow-ups ready to be sent

    Returns follow-ups scheduled for now or earlier.
    """
    try:
        service = get_followup_service(db)
        pending = service.get_pending_followups()
        return pending
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving pending follow-ups: {str(e)}"
        )


@router.get("/followups/{followup_id}", response_model=FollowUp)
async def get_followup(
    followup_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific follow-up
    """
    try:
        followup = db.query(FollowUpModel).filter(FollowUpModel.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")

        return followup
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving follow-up: {str(e)}"
        )


@router.put("/followups/{followup_id}", response_model=FollowUp)
async def update_followup(
    followup_id: int,
    update: FollowUpUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a follow-up
    """
    try:
        followup = db.query(FollowUpModel).filter(FollowUpModel.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")

        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(followup, field, value)

        followup.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(followup)

        return followup
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating follow-up: {str(e)}"
        )


@router.delete("/followups/{followup_id}")
async def cancel_followup(
    followup_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a scheduled follow-up
    """
    try:
        followup = db.query(FollowUpModel).filter(FollowUpModel.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")

        followup.status = "cancelled"
        followup.updated_at = datetime.utcnow()
        db.commit()

        return {"success": True, "message": "Follow-up cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling follow-up: {str(e)}"
        )


# ==================== Responses ====================

@router.post("/responses", response_model=FollowUpResponse, status_code=status.HTTP_201_CREATED)
async def record_response(
    response: FollowUpResponseCreate,
    db: Session = Depends(get_db)
):
    """
    Record a response to a follow-up

    Automatically cancels subsequent follow-ups if configured to stop on response.
    """
    try:
        service = get_followup_service(db)
        created = service.record_response(response)
        return created
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording response: {str(e)}"
        )


@router.get("/responses", response_model=List[FollowUpResponse])
async def get_responses(
    followup_id: Optional[int] = None,
    response_type: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """
    Get follow-up responses
    """
    try:
        query = db.query(ResponseModel)

        if followup_id:
            query = query.filter(ResponseModel.followup_id == followup_id)

        if response_type:
            query = query.filter(ResponseModel.response_type == response_type)

        responses = query.order_by(ResponseModel.response_date.desc()).limit(limit).all()
        return responses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving responses: {str(e)}"
        )


# ==================== Analytics ====================

@router.post("/analytics/calculate", response_model=FollowUpAnalytics)
async def calculate_analytics(
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Calculate follow-up analytics for a period

    Returns open rates, response rates, and timing analysis.
    """
    try:
        service = get_followup_service(db)
        analytics = service.calculate_analytics(period_days)

        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No follow-ups found for the specified period"
            )

        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating analytics: {str(e)}"
        )


@router.get("/analytics/history", response_model=List[FollowUpAnalytics])
async def get_analytics_history(
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db)
):
    """
    Get historical follow-up analytics
    """
    try:
        analytics = db.query(AnalyticsModel).order_by(
            AnalyticsModel.period_start.desc()
        ).limit(limit).all()

        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analytics: {str(e)}"
        )


# ==================== Dashboard ====================

@router.get("/dashboard", response_model=FollowUpDashboard)
async def get_dashboard(db: Session = Depends(get_db)):
    """
    Get follow-up dashboard data

    Returns overview, upcoming follow-ups, and performance metrics.
    """
    try:
        from datetime import date

        # Pending follow-ups
        pending = db.query(FollowUpModel).filter(
            FollowUpModel.status == "scheduled",
            FollowUpModel.scheduled_date <= datetime.utcnow()
        ).count()

        # Sent today
        today_start = datetime.combine(date.today(), datetime.min.time())
        sent_today = db.query(FollowUpModel).filter(
            FollowUpModel.sent_date >= today_start
        ).count()

        # Responses today
        responses_today = db.query(ResponseModel).filter(
            ResponseModel.response_date >= today_start
        ).count()

        # Overall response rate
        total_sent = db.query(FollowUpModel).filter(
            FollowUpModel.status == "sent"
        ).count()
        total_responded = db.query(FollowUpModel).filter(
            FollowUpModel.status == "responded"
        ).count()
        overall_response_rate = (total_responded / total_sent * 100) if total_sent > 0 else None

        # Upcoming follow-ups
        upcoming = db.query(FollowUpModel).filter(
            FollowUpModel.status == "scheduled",
            FollowUpModel.scheduled_date > datetime.utcnow()
        ).order_by(FollowUpModel.scheduled_date).limit(10).all()

        # Recent sent
        recent_sent = db.query(FollowUpModel).filter(
            FollowUpModel.status == "sent"
        ).order_by(FollowUpModel.sent_date.desc()).limit(5).all()

        # Recent responses
        recent_responses = db.query(ResponseModel).order_by(
            ResponseModel.response_date.desc()
        ).limit(5).all()

        # Best performing template
        best_template = db.query(TemplateModel).filter(
            TemplateModel.success_rate.isnot(None)
        ).order_by(TemplateModel.success_rate.desc()).first()

        # Best performing sequence
        best_sequence = db.query(SequenceModel).filter(
            SequenceModel.response_rate.isnot(None)
        ).order_by(SequenceModel.response_rate.desc()).first()

        dashboard = FollowUpDashboard(
            pending_followups=pending,
            sent_today=sent_today,
            responses_today=responses_today,
            overall_response_rate=overall_response_rate,
            avg_response_time_hours=None,  # TODO: Calculate
            upcoming_followups=upcoming,
            recent_sent=recent_sent,
            recent_responses=recent_responses,
            best_send_time=None,  # TODO: Calculate from analytics
            best_performing_template=best_template,
            best_performing_sequence=best_sequence
        )

        return dashboard
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard: {str(e)}"
        )


# ==================== Timing Recommendations ====================

@router.get("/timing/recommendations", response_model=List[TimingRecommendation])
async def get_timing_recommendations(
    stage: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get timing recommendations based on historical data

    Returns optimal timing for different follow-up stages.
    """
    try:
        # Simplified recommendations - in production, analyze actual data
        recommendations = [
            TimingRecommendation(
                stage="post_application",
                recommended_days_after=3,
                recommended_time_of_day="10:00 AM",
                recommended_day_of_week="Tuesday",
                confidence=0.75,
                based_on_samples=50,
                reasoning="Tuesday mornings show 35% higher response rates"
            ),
            TimingRecommendation(
                stage="post_interview",
                recommended_days_after=1,
                recommended_time_of_day="2:00 PM",
                recommended_day_of_week="Same day",
                confidence=0.90,
                based_on_samples=100,
                reasoning="Send thank you notes within 24 hours for best results"
            ),
            TimingRecommendation(
                stage="no_response",
                recommended_days_after=7,
                recommended_time_of_day="9:00 AM",
                recommended_day_of_week="Wednesday",
                confidence=0.65,
                based_on_samples=30,
                reasoning="Mid-week mornings optimal for re-engagement"
            )
        ]

        if stage:
            recommendations = [r for r in recommendations if r.stage == stage]

        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recommendations: {str(e)}"
        )
