"""
Application Tracking System (ATS) API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services.ats_service import get_ats_service
from ..services.integration_service import integrate_status_change
from ..schemas.application import (
    StatusUpdate,
    StatusUpdateResponse,
    InterviewCreate,
    InterviewUpdate,
    Interview,
    OfferCreate,
    OfferUpdate,
    OfferNegotiation,
    Offer,
    ApplicationNoteCreate,
    ApplicationNoteUpdate,
    ApplicationNote,
    ApplicationTimeline,
    ApplicationStatistics
)


router = APIRouter()


# ==================== Status Management ====================

@router.post("/jobs/{job_id}/status", response_model=StatusUpdateResponse)
async def update_job_status(
    job_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update job application status

    Validates status transitions and creates event tracking.
    Triggers integrations: follow-ups, calendar, WebSocket notifications.
    """
    try:
        ats_service = get_ats_service(db)
        result = ats_service.update_job_status(
            job_id=job_id,
            new_status=status_update.status.value,
            notes=status_update.notes
        )

        # Trigger integrations (follow-ups, calendar, WebSocket)
        await integrate_status_change(
            db=db,
            job_id=job_id,
            old_status=result["old_status"],
            new_status=result["new_status"]
        )

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating status: {str(e)}"
        )


@router.get("/jobs/{job_id}/timeline", response_model=ApplicationTimeline)
async def get_application_timeline(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get complete application timeline

    Returns all events, interviews, offers, and notes for a job.
    """
    try:
        ats_service = get_ats_service(db)
        timeline = ats_service.get_application_timeline(job_id)
        return timeline
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving timeline: {str(e)}"
        )


# ==================== Interview Management ====================

@router.post("/interviews", response_model=Interview, status_code=status.HTTP_201_CREATED)
async def schedule_interview(
    interview: InterviewCreate,
    db: Session = Depends(get_db)
):
    """
    Schedule a new interview

    Creates interview record and updates job status appropriately.
    """
    try:
        ats_service = get_ats_service(db)
        created_interview = ats_service.schedule_interview(interview)
        return created_interview
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling interview: {str(e)}"
        )


@router.put("/interviews/{interview_id}", response_model=Interview)
async def update_interview(
    interview_id: int,
    interview: InterviewUpdate,
    db: Session = Depends(get_db)
):
    """
    Update interview details

    Can update scheduling, preparation notes, or record outcome.
    """
    try:
        ats_service = get_ats_service(db)
        updated_interview = ats_service.update_interview(interview_id, interview)
        return updated_interview
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating interview: {str(e)}"
        )


@router.get("/interviews/upcoming", response_model=List[Interview])
async def get_upcoming_interviews(
    days_ahead: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get upcoming interviews

    Returns interviews scheduled within the specified number of days.
    """
    try:
        ats_service = get_ats_service(db)
        interviews = ats_service.get_upcoming_interviews(days_ahead)
        return interviews
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interviews: {str(e)}"
        )


@router.get("/jobs/{job_id}/interviews", response_model=List[Interview])
async def get_job_interviews(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all interviews for a specific job
    """
    from ..models.application import Interview as InterviewModel

    try:
        interviews = db.query(InterviewModel).filter(
            InterviewModel.job_id == job_id
        ).order_by(InterviewModel.scheduled_date.desc()).all()
        return interviews
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interviews: {str(e)}"
        )


# ==================== Offer Management ====================

@router.post("/offers", response_model=Offer, status_code=status.HTTP_201_CREATED)
async def record_offer(
    offer: OfferCreate,
    db: Session = Depends(get_db)
):
    """
    Record a job offer

    Creates offer record and updates job status to offer_received.
    """
    try:
        ats_service = get_ats_service(db)
        created_offer = ats_service.record_offer(offer)
        return created_offer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording offer: {str(e)}"
        )


@router.put("/offers/{offer_id}", response_model=Offer)
async def update_offer(
    offer_id: int,
    offer: OfferUpdate,
    db: Session = Depends(get_db)
):
    """
    Update offer details

    Can update terms, status, or record decision.
    """
    try:
        ats_service = get_ats_service(db)
        updated_offer = ats_service.update_offer(offer_id, offer)
        return updated_offer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating offer: {str(e)}"
        )


@router.post("/offers/{offer_id}/negotiate", response_model=Offer)
async def add_negotiation(
    offer_id: int,
    negotiation: OfferNegotiation,
    db: Session = Depends(get_db)
):
    """
    Add negotiation entry to offer

    Records counter-offer and updates offer status to negotiating.
    """
    try:
        ats_service = get_ats_service(db)
        updated_offer = ats_service.add_negotiation(offer_id, negotiation)
        return updated_offer
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding negotiation: {str(e)}"
        )


@router.get("/jobs/{job_id}/offers", response_model=List[Offer])
async def get_job_offers(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all offers for a specific job
    """
    from ..models.application import Offer as OfferModel

    try:
        offers = db.query(OfferModel).filter(
            OfferModel.job_id == job_id
        ).order_by(OfferModel.received_date.desc()).all()
        return offers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving offers: {str(e)}"
        )


# ==================== Notes Management ====================

@router.post("/notes", response_model=ApplicationNote, status_code=status.HTTP_201_CREATED)
async def add_note(
    note: ApplicationNoteCreate,
    db: Session = Depends(get_db)
):
    """
    Add note to job application

    Can be general note, communication record, or follow-up reminder.
    """
    try:
        ats_service = get_ats_service(db)
        created_note = ats_service.add_note(note)
        return created_note
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding note: {str(e)}"
        )


@router.put("/notes/{note_id}", response_model=ApplicationNote)
async def update_note(
    note_id: int,
    note: ApplicationNoteUpdate,
    db: Session = Depends(get_db)
):
    """
    Update note
    """
    try:
        ats_service = get_ats_service(db)
        updated_note = ats_service.update_note(note_id, note)
        return updated_note
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating note: {str(e)}"
        )


@router.get("/jobs/{job_id}/notes", response_model=List[ApplicationNote])
async def get_job_notes(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all notes for a specific job
    """
    from ..models.application import ApplicationNote as NoteModel

    try:
        notes = db.query(NoteModel).filter(
            NoteModel.job_id == job_id
        ).order_by(NoteModel.created_at.desc()).all()
        return notes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving notes: {str(e)}"
        )


# ==================== Statistics ====================

@router.get("/statistics", response_model=ApplicationStatistics)
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get application statistics

    Returns counts by status, interview stats, offer stats, and success rate.
    """
    try:
        ats_service = get_ats_service(db)
        stats = ats_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )
