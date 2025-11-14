"""
Application Tracking System (ATS) Service

Handles job application lifecycle, status transitions, interviews, and offers.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from loguru import logger

from ..models.job import Job
from ..models.application import (
    ApplicationEvent,
    Interview,
    Offer,
    ApplicationNote,
    ApplicationStatus,
    InterviewType,
    InterviewOutcome,
    OfferStatus
)
from ..schemas.application import (
    InterviewCreate,
    InterviewUpdate,
    OfferCreate,
    OfferUpdate,
    OfferNegotiation,
    ApplicationNoteCreate,
    ApplicationNoteUpdate
)


class ATSService:
    """Application Tracking System Service"""

    # Define valid status transitions
    VALID_TRANSITIONS = {
        ApplicationStatus.DISCOVERED: [
            ApplicationStatus.ANALYZING,
            ApplicationStatus.ARCHIVED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.ANALYZING: [
            ApplicationStatus.ANALYZED,
            ApplicationStatus.ARCHIVED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.ANALYZED: [
            ApplicationStatus.READY_TO_APPLY,
            ApplicationStatus.ARCHIVED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.READY_TO_APPLY: [
            ApplicationStatus.APPLIED,
            ApplicationStatus.ARCHIVED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.APPLIED: [
            ApplicationStatus.SCREENING,
            ApplicationStatus.INTERVIEW_SCHEDULED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.SCREENING: [
            ApplicationStatus.INTERVIEW_SCHEDULED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.INTERVIEW_SCHEDULED: [
            ApplicationStatus.INTERVIEWING,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.INTERVIEWING: [
            ApplicationStatus.INTERVIEW_SCHEDULED,  # More interviews
            ApplicationStatus.OFFER_RECEIVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.OFFER_RECEIVED: [
            ApplicationStatus.OFFER_ACCEPTED,
            ApplicationStatus.OFFER_REJECTED,
            ApplicationStatus.WITHDRAWN
        ],
        ApplicationStatus.OFFER_ACCEPTED: [
            ApplicationStatus.ARCHIVED
        ],
        ApplicationStatus.OFFER_REJECTED: [
            ApplicationStatus.ARCHIVED
        ],
        ApplicationStatus.REJECTED: [
            ApplicationStatus.ARCHIVED
        ],
        ApplicationStatus.WITHDRAWN: [
            ApplicationStatus.ARCHIVED
        ],
        ApplicationStatus.ARCHIVED: []  # No transitions from archived
    }

    def __init__(self, db: Session):
        self.db = db

    # ==================== Status Management ====================

    def validate_status_transition(self, current_status: str, new_status: str) -> bool:
        """
        Validate if status transition is allowed

        Args:
            current_status: Current application status
            new_status: Desired new status

        Returns:
            True if transition is valid, False otherwise
        """
        try:
            current = ApplicationStatus(current_status)
            new = ApplicationStatus(new_status)
        except ValueError:
            return False

        return new in self.VALID_TRANSITIONS.get(current, [])

    def update_job_status(
        self,
        job_id: int,
        new_status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update job status with validation and event tracking

        Args:
            job_id: Job ID
            new_status: New status
            notes: Optional notes about the status change

        Returns:
            Status update result

        Raises:
            ValueError: If job not found or invalid transition
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        old_status = job.status

        # Validate transition
        if not self.validate_status_transition(old_status, new_status):
            raise ValueError(
                f"Invalid status transition from {old_status} to {new_status}. "
                f"Valid transitions: {[s.value for s in self.VALID_TRANSITIONS.get(ApplicationStatus(old_status), [])]}"
            )

        # Update job status
        job.status = new_status
        job.updated_at = datetime.utcnow()

        # Set applied_date if applicable
        if new_status == ApplicationStatus.APPLIED.value and not job.applied_date:
            job.applied_date = datetime.utcnow()

        # Create event
        event = ApplicationEvent(
            job_id=job_id,
            event_type="status_change",
            old_status=old_status,
            new_status=new_status,
            description=notes,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(job)

        logger.info(f"📊 Job {job_id} status updated: {old_status} → {new_status}")

        return {
            "success": True,
            "job_id": job_id,
            "old_status": old_status,
            "new_status": new_status,
            "message": f"Status updated from {old_status} to {new_status}"
        }

    def get_application_timeline(self, job_id: int) -> Dict[str, Any]:
        """
        Get complete application timeline

        Args:
            job_id: Job ID

        Returns:
            Timeline with events, interviews, offers, notes
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        events = self.db.query(ApplicationEvent).filter(
            ApplicationEvent.job_id == job_id
        ).order_by(ApplicationEvent.created_at.desc()).all()

        interviews = self.db.query(Interview).filter(
            Interview.job_id == job_id
        ).order_by(Interview.scheduled_date.desc()).all()

        offers = self.db.query(Offer).filter(
            Offer.job_id == job_id
        ).order_by(Offer.received_date.desc()).all()

        notes = self.db.query(ApplicationNote).filter(
            ApplicationNote.job_id == job_id
        ).order_by(ApplicationNote.created_at.desc()).all()

        return {
            "job_id": job_id,
            "company": job.company,
            "job_title": job.job_title,
            "current_status": job.status,
            "events": events,
            "interviews": interviews,
            "offers": offers,
            "notes": notes,
            "created_at": job.created_at,
            "last_updated": job.updated_at
        }

    # ==================== Interview Management ====================

    def schedule_interview(self, interview_data: InterviewCreate) -> Interview:
        """
        Schedule an interview

        Args:
            interview_data: Interview details

        Returns:
            Created interview
        """
        job = self.db.query(Job).filter(Job.id == interview_data.job_id).first()
        if not job:
            raise ValueError(f"Job {interview_data.job_id} not found")

        # Create interview
        interview = Interview(
            **interview_data.model_dump()
        )
        self.db.add(interview)

        # Update job status if appropriate
        if job.status == ApplicationStatus.APPLIED.value:
            job.status = ApplicationStatus.INTERVIEW_SCHEDULED.value

        # Create event
        event = ApplicationEvent(
            job_id=interview_data.job_id,
            event_type="interview_scheduled",
            description=f"{interview_data.interview_type.value} interview scheduled for {interview_data.scheduled_date}",
            metadata={
                "interview_type": interview_data.interview_type.value,
                "scheduled_date": interview_data.scheduled_date.isoformat(),
                "is_virtual": interview_data.is_virtual
            }
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(interview)

        logger.info(f"📅 Interview scheduled for job {interview_data.job_id}: {interview_data.interview_type.value}")

        return interview

    def update_interview(
        self,
        interview_id: int,
        interview_data: InterviewUpdate
    ) -> Interview:
        """
        Update interview details

        Args:
            interview_id: Interview ID
            interview_data: Updated interview data

        Returns:
            Updated interview
        """
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        # Update fields
        update_data = interview_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(interview, field, value)

        interview.updated_at = datetime.utcnow()

        # If outcome is set and not pending, mark as completed
        if interview_data.outcome and interview_data.outcome != InterviewOutcome.PENDING:
            interview.completed_at = datetime.utcnow()

            # Create event
            event = ApplicationEvent(
                job_id=interview.job_id,
                event_type="interview_completed",
                description=f"Interview completed with outcome: {interview_data.outcome.value}",
                metadata={
                    "interview_type": interview.interview_type.value,
                    "outcome": interview_data.outcome.value,
                    "performance_rating": interview_data.performance_rating
                }
            )
            self.db.add(event)

        self.db.commit()
        self.db.refresh(interview)

        logger.info(f"📝 Interview {interview_id} updated")

        return interview

    def get_upcoming_interviews(
        self,
        days_ahead: int = 7
    ) -> List[Interview]:
        """
        Get upcoming interviews

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming interviews
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)

        interviews = self.db.query(Interview).filter(
            Interview.scheduled_date >= datetime.utcnow(),
            Interview.scheduled_date <= cutoff_date,
            Interview.outcome == InterviewOutcome.PENDING
        ).order_by(Interview.scheduled_date).all()

        return interviews

    # ==================== Offer Management ====================

    def record_offer(self, offer_data: OfferCreate) -> Offer:
        """
        Record a job offer

        Args:
            offer_data: Offer details

        Returns:
            Created offer
        """
        job = self.db.query(Job).filter(Job.id == offer_data.job_id).first()
        if not job:
            raise ValueError(f"Job {offer_data.job_id} not found")

        # Create offer
        offer = Offer(
            **offer_data.model_dump()
        )
        self.db.add(offer)

        # Update job status
        job.status = ApplicationStatus.OFFER_RECEIVED.value

        # Create event
        event = ApplicationEvent(
            job_id=offer_data.job_id,
            event_type="offer_received",
            description=f"Job offer received: ${offer_data.salary:,.0f} {offer_data.salary_period}",
            metadata={
                "salary": offer_data.salary,
                "currency": offer_data.currency,
                "bonus": offer_data.bonus,
                "equity": offer_data.equity
            }
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(offer)

        logger.info(f"💰 Offer recorded for job {offer_data.job_id}: ${offer_data.salary:,.0f}")

        return offer

    def update_offer(
        self,
        offer_id: int,
        offer_data: OfferUpdate
    ) -> Offer:
        """
        Update offer details

        Args:
            offer_id: Offer ID
            offer_data: Updated offer data

        Returns:
            Updated offer
        """
        offer = self.db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise ValueError(f"Offer {offer_id} not found")

        # Update fields
        update_data = offer_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(offer, field, value)

        offer.updated_at = datetime.utcnow()

        # If status changed to accepted/rejected, update job status
        if offer_data.status:
            job = self.db.query(Job).filter(Job.id == offer.job_id).first()
            if offer_data.status == OfferStatus.ACCEPTED:
                job.status = ApplicationStatus.OFFER_ACCEPTED.value
                offer.decision_date = datetime.utcnow()
            elif offer_data.status == OfferStatus.REJECTED:
                job.status = ApplicationStatus.OFFER_REJECTED.value
                offer.decision_date = datetime.utcnow()

            # Create event
            event = ApplicationEvent(
                job_id=offer.job_id,
                event_type="offer_decision",
                description=f"Offer {offer_data.status.value}",
                metadata={"decision": offer_data.status.value}
            )
            self.db.add(event)

        self.db.commit()
        self.db.refresh(offer)

        logger.info(f"📋 Offer {offer_id} updated")

        return offer

    def add_negotiation(
        self,
        offer_id: int,
        negotiation_data: OfferNegotiation
    ) -> Offer:
        """
        Add negotiation entry to offer

        Args:
            offer_id: Offer ID
            negotiation_data: Negotiation details

        Returns:
            Updated offer
        """
        offer = self.db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise ValueError(f"Offer {offer_id} not found")

        # Add counter-offer
        counter_offer = {
            "timestamp": datetime.utcnow().isoformat(),
            "salary": negotiation_data.counter_salary,
            "bonus": negotiation_data.counter_bonus,
            "equity": negotiation_data.counter_equity,
            "notes": negotiation_data.counter_notes
        }

        if offer.counter_offers is None:
            offer.counter_offers = []
        offer.counter_offers.append(counter_offer)

        # Update status to negotiating
        offer.status = OfferStatus.NEGOTIATING
        offer.updated_at = datetime.utcnow()

        # Create event
        event = ApplicationEvent(
            job_id=offer.job_id,
            event_type="offer_negotiation",
            description=f"Counter-offer submitted: ${negotiation_data.counter_salary:,.0f}",
            metadata=counter_offer
        )
        self.db.add(event)

        self.db.commit()
        self.db.refresh(offer)

        logger.info(f"💼 Negotiation added to offer {offer_id}")

        return offer

    # ==================== Notes Management ====================

    def add_note(self, note_data: ApplicationNoteCreate) -> ApplicationNote:
        """
        Add note to application

        Args:
            note_data: Note details

        Returns:
            Created note
        """
        job = self.db.query(Job).filter(Job.id == note_data.job_id).first()
        if not job:
            raise ValueError(f"Job {note_data.job_id} not found")

        note = ApplicationNote(
            **note_data.model_dump()
        )
        self.db.add(note)

        # Create event if it's a communication
        if note_data.is_communication:
            event = ApplicationEvent(
                job_id=note_data.job_id,
                event_type="communication",
                description=f"{note_data.communication_direction} {note_data.communication_method} with {note_data.contact_person}",
                metadata={
                    "note_type": note_data.note_type,
                    "communication_method": note_data.communication_method
                }
            )
            self.db.add(event)

        self.db.commit()
        self.db.refresh(note)

        logger.info(f"📝 Note added to job {note_data.job_id}")

        return note

    def update_note(
        self,
        note_id: int,
        note_data: ApplicationNoteUpdate
    ) -> ApplicationNote:
        """
        Update note

        Args:
            note_id: Note ID
            note_data: Updated note data

        Returns:
            Updated note
        """
        note = self.db.query(ApplicationNote).filter(ApplicationNote.id == note_id).first()
        if not note:
            raise ValueError(f"Note {note_id} not found")

        update_data = note_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)

        note.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(note)

        return note

    # ==================== Statistics ====================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get application statistics

        Returns:
            Statistics about applications
        """
        total = self.db.query(Job).count()

        # Count by status
        status_counts = {}
        for status in ApplicationStatus:
            count = self.db.query(Job).filter(Job.status == status.value).count()
            if count > 0:
                status_counts[status.value] = count

        # Interview stats
        interviews_scheduled = self.db.query(Interview).filter(
            Interview.outcome == InterviewOutcome.PENDING
        ).count()

        interviews_completed = self.db.query(Interview).filter(
            Interview.outcome.in_([InterviewOutcome.PASSED, InterviewOutcome.FAILED])
        ).count()

        # Offer stats
        offers_received = self.db.query(Offer).count()
        offers_accepted = self.db.query(Offer).filter(
            Offer.status == OfferStatus.ACCEPTED
        ).count()

        # Calculate success rate
        success_rate = None
        total_concluded = self.db.query(Job).filter(
            Job.status.in_([
                ApplicationStatus.OFFER_ACCEPTED.value,
                ApplicationStatus.OFFER_REJECTED.value,
                ApplicationStatus.REJECTED.value
            ])
        ).count()

        if total_concluded > 0:
            success_rate = (offers_accepted / total_concluded) * 100

        return {
            "total_applications": total,
            "by_status": status_counts,
            "interviews_scheduled": interviews_scheduled,
            "interviews_completed": interviews_completed,
            "offers_received": offers_received,
            "offers_accepted": offers_accepted,
            "success_rate": round(success_rate, 2) if success_rate else None
        }


# Singleton instance
_ats_service: Optional[ATSService] = None


def get_ats_service(db: Session) -> ATSService:
    """Get ATS service instance"""
    return ATSService(db)
