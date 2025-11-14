"""
Google Calendar API

Endpoints for calendar integration and event management.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.calendar_service import get_calendar_service
from ..models.application import Interview


router = APIRouter()


class InterviewScheduleRequest(BaseModel):
    """Request to schedule an interview"""
    job_id: int
    interview_type: str
    start_time: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    interviewer_email: Optional[str] = None
    notes: Optional[str] = None


class FollowUpReminderRequest(BaseModel):
    """Request to create follow-up reminder"""
    job_id: int
    follow_up_type: str
    reminder_time: datetime
    notes: Optional[str] = None


class DeadlineReminderRequest(BaseModel):
    """Request to create deadline reminder"""
    job_id: int
    deadline: datetime
    job_url: Optional[str] = None


@router.post("/interview")
def schedule_interview(
    request: InterviewScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule an interview in Google Calendar

    Creates a calendar event with reminders and optionally
    invites the interviewer.
    """
    try:
        from ..models.job import Job

        # Get job details
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        calendar = get_calendar_service()

        # Create calendar event
        event = calendar.create_interview_event(
            job_title=job.title,
            company=job.company or "Unknown Company",
            interview_type=request.interview_type,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            location=request.location,
            interviewer_email=request.interviewer_email,
            notes=request.notes
        )

        if not event:
            raise HTTPException(
                status_code=500,
                detail="Failed to create calendar event"
            )

        # Store calendar event ID in database
        interview = Interview(
            job_id=request.job_id,
            interview_type=request.interview_type,
            scheduled_date=request.start_time,
            location=request.location,
            interviewer_name=request.interviewer_email,
            notes=request.notes,
            calendar_event_id=event.get('id')
        )
        db.add(interview)
        db.commit()

        return {
            "message": "Interview scheduled successfully",
            "event_id": event.get('id'),
            "event_link": event.get('htmlLink'),
            "interview_id": interview.id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/follow-up-reminder")
def create_follow_up_reminder(
    request: FollowUpReminderRequest,
    db: Session = Depends(get_db)
):
    """
    Create a follow-up reminder in Google Calendar

    Sets up a reminder event to follow up on an application.
    """
    try:
        from ..models.job import Job

        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        calendar = get_calendar_service()

        event = calendar.create_follow_up_reminder(
            job_title=job.title,
            company=job.company or "Unknown Company",
            follow_up_type=request.follow_up_type,
            reminder_time=request.reminder_time,
            notes=request.notes
        )

        if not event:
            raise HTTPException(
                status_code=500,
                detail="Failed to create follow-up reminder"
            )

        return {
            "message": "Follow-up reminder created",
            "event_id": event.get('id'),
            "event_link": event.get('htmlLink')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating follow-up reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deadline-reminder")
def create_deadline_reminder(
    request: DeadlineReminderRequest,
    db: Session = Depends(get_db)
):
    """
    Create an application deadline reminder

    Creates an all-day event for application deadlines.
    """
    try:
        from ..models.job import Job

        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        calendar = get_calendar_service()

        event = calendar.create_application_deadline(
            job_title=job.title,
            company=job.company or "Unknown Company",
            deadline=request.deadline,
            job_url=request.job_url or job.url
        )

        if not event:
            raise HTTPException(
                status_code=500,
                detail="Failed to create deadline reminder"
            )

        return {
            "message": "Deadline reminder created",
            "event_id": event.get('id'),
            "event_link": event.get('htmlLink')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating deadline reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
def get_upcoming_events(
    days: int = 7,
    limit: int = 10
):
    """Get upcoming calendar events"""
    try:
        calendar = get_calendar_service()
        events = calendar.get_upcoming_events(days_ahead=days, max_results=limit)

        return {
            "count": len(events),
            "events": events
        }

    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}")
def get_events_for_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get all calendar events for a specific job"""
    try:
        from ..models.job import Job

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        calendar = get_calendar_service()
        events = calendar.get_events_for_job(
            job_title=job.title,
            company=job.company or "Unknown"
        )

        return {
            "job_id": job_id,
            "job_title": job.title,
            "company": job.company,
            "event_count": len(events),
            "events": events
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/event/{event_id}")
def delete_calendar_event(event_id: str):
    """Delete a calendar event"""
    try:
        calendar = get_calendar_service()
        success = calendar.delete_event(event_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete event"
            )

        return {"message": "Event deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def calendar_health_check():
    """Check if calendar service is available"""
    calendar = get_calendar_service()

    return {
        "available": calendar.service is not None,
        "authenticated": calendar.credentials is not None if calendar.service else False
    }
