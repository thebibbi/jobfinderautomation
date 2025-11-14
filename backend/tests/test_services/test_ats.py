"""
Tests for Application Tracking System (ATS) Service
"""
import pytest
from datetime import datetime, timedelta
from app.services.ats_service import ATSService
from app.models.application import (
    ApplicationStatus,
    InterviewType,
    InterviewOutcome,
    OfferStatus
)
from app.schemas.application import (
    InterviewCreate,
    InterviewUpdate,
    OfferCreate,
    OfferUpdate,
    OfferNegotiation,
    ApplicationNoteCreate
)


class TestStatusTransitions:
    """Test status transition validation and updates"""

    def test_valid_status_transitions(self, db_session):
        """Test that valid status transitions are allowed"""
        ats = ATSService(db_session)

        # Test various valid transitions
        assert ats.validate_status_transition("discovered", "analyzing") is True
        assert ats.validate_status_transition("analyzed", "ready_to_apply") is True
        assert ats.validate_status_transition("applied", "interview_scheduled") is True
        assert ats.validate_status_transition("interviewing", "offer_received") is True
        assert ats.validate_status_transition("offer_received", "offer_accepted") is True

    def test_invalid_status_transitions(self, db_session):
        """Test that invalid status transitions are rejected"""
        ats = ATSService(db_session)

        # Can't skip from discovered directly to interview
        assert ats.validate_status_transition("discovered", "interview_scheduled") is False

        # Can't go back from offer to applied
        assert ats.validate_status_transition("offer_received", "applied") is False

        # Can't transition from archived
        assert ats.validate_status_transition("archived", "discovered") is False

    def test_update_job_status_valid(self, db_session, create_test_job):
        """Test updating job status with valid transition"""
        job = create_test_job(status="discovered")
        ats = ATSService(db_session)

        result = ats.update_job_status(
            job_id=job.id,
            new_status="analyzing",
            notes="Starting analysis"
        )

        assert result["success"] is True
        assert result["old_status"] == "discovered"
        assert result["new_status"] == "analyzing"

        # Verify job was updated
        db_session.refresh(job)
        assert job.status == "analyzing"

    def test_update_job_status_invalid(self, db_session, create_test_job):
        """Test updating job status with invalid transition"""
        job = create_test_job(status="discovered")
        ats = ATSService(db_session)

        with pytest.raises(ValueError, match="Invalid status transition"):
            ats.update_job_status(
                job_id=job.id,
                new_status="interview_scheduled"
            )

    def test_update_job_status_not_found(self, db_session):
        """Test updating non-existent job"""
        ats = ATSService(db_session)

        with pytest.raises(ValueError, match="Job .* not found"):
            ats.update_job_status(
                job_id=99999,
                new_status="analyzing"
            )

    def test_applied_date_set_automatically(self, db_session, create_test_job):
        """Test that applied_date is set when status changes to applied"""
        job = create_test_job(status="ready_to_apply")
        ats = ATSService(db_session)

        # Verify applied_date is initially None
        assert job.applied_date is None

        ats.update_job_status(job_id=job.id, new_status="applied")

        # Verify applied_date was set
        db_session.refresh(job)
        assert job.applied_date is not None
        assert isinstance(job.applied_date, datetime)


class TestInterviewManagement:
    """Test interview scheduling and management"""

    def test_schedule_interview(self, db_session, create_test_job):
        """Test scheduling an interview"""
        job = create_test_job(status="applied")
        ats = ATSService(db_session)

        interview_data = InterviewCreate(
            job_id=job.id,
            interview_type=InterviewType.PHONE_SCREEN,
            scheduled_date=datetime.utcnow() + timedelta(days=2),
            duration_minutes=30,
            is_virtual=True,
            interviewer_names="Jane Smith",
            interviewer_titles="Hiring Manager"
        )

        interview = ats.schedule_interview(interview_data)

        assert interview.id is not None
        assert interview.job_id == job.id
        assert interview.interview_type == InterviewType.PHONE_SCREEN
        assert interview.outcome == InterviewOutcome.PENDING

        # Verify job status updated
        db_session.refresh(job)
        assert job.status == ApplicationStatus.INTERVIEW_SCHEDULED.value

    def test_schedule_interview_nonexistent_job(self, db_session):
        """Test scheduling interview for non-existent job"""
        ats = ATSService(db_session)

        interview_data = InterviewCreate(
            job_id=99999,
            interview_type=InterviewType.TECHNICAL,
            scheduled_date=datetime.utcnow() + timedelta(days=2)
        )

        with pytest.raises(ValueError, match="Job .* not found"):
            ats.schedule_interview(interview_data)

    def test_update_interview(self, db_session, create_test_job):
        """Test updating interview details"""
        job = create_test_job(status="applied")
        ats = ATSService(db_session)

        # Create interview
        interview_data = InterviewCreate(
            job_id=job.id,
            interview_type=InterviewType.TECHNICAL,
            scheduled_date=datetime.utcnow() + timedelta(days=2)
        )
        interview = ats.schedule_interview(interview_data)

        # Update interview
        update_data = InterviewUpdate(
            outcome=InterviewOutcome.PASSED,
            performance_rating=4,
            feedback="Great technical skills"
        )
        updated = ats.update_interview(interview.id, update_data)

        assert updated.outcome == InterviewOutcome.PASSED
        assert updated.performance_rating == 4
        assert updated.feedback == "Great technical skills"
        assert updated.completed_at is not None

    def test_get_upcoming_interviews(self, db_session, create_test_job):
        """Test retrieving upcoming interviews"""
        job1 = create_test_job(job_id="job1", status="applied")
        job2 = create_test_job(job_id="job2", status="applied")
        ats = ATSService(db_session)

        # Schedule interviews
        interview1 = InterviewCreate(
            job_id=job1.id,
            interview_type=InterviewType.PHONE_SCREEN,
            scheduled_date=datetime.utcnow() + timedelta(days=1)
        )
        interview2 = InterviewCreate(
            job_id=job2.id,
            interview_type=InterviewType.TECHNICAL,
            scheduled_date=datetime.utcnow() + timedelta(days=3)
        )
        interview3 = InterviewCreate(
            job_id=job1.id,
            interview_type=InterviewType.PANEL,
            scheduled_date=datetime.utcnow() + timedelta(days=10)  # Outside 7-day window
        )

        ats.schedule_interview(interview1)
        ats.schedule_interview(interview2)
        ats.schedule_interview(interview3)

        # Get upcoming interviews (default 7 days)
        upcoming = ats.get_upcoming_interviews(days_ahead=7)

        assert len(upcoming) == 2  # Only first two within 7 days
        assert all(i.outcome == InterviewOutcome.PENDING for i in upcoming)


class TestOfferManagement:
    """Test offer recording and negotiation"""

    def test_record_offer(self, db_session, create_test_job):
        """Test recording a job offer"""
        job = create_test_job(status="interviewing")
        ats = ATSService(db_session)

        offer_data = OfferCreate(
            job_id=job.id,
            salary=100000,
            currency="USD",
            bonus=10000,
            equity="1000 RSUs",
            vacation_days=20
        )

        offer = ats.record_offer(offer_data)

        assert offer.id is not None
        assert offer.salary == 100000
        assert offer.status == OfferStatus.PENDING_REVIEW

        # Verify job status updated
        db_session.refresh(job)
        assert job.status == ApplicationStatus.OFFER_RECEIVED.value

    def test_record_offer_nonexistent_job(self, db_session):
        """Test recording offer for non-existent job"""
        ats = ATSService(db_session)

        offer_data = OfferCreate(
            job_id=99999,
            salary=100000
        )

        with pytest.raises(ValueError, match="Job .* not found"):
            ats.record_offer(offer_data)

    def test_update_offer(self, db_session, create_test_job):
        """Test updating offer details"""
        job = create_test_job(status="interviewing")
        ats = ATSService(db_session)

        # Create offer
        offer_data = OfferCreate(
            job_id=job.id,
            salary=100000
        )
        offer = ats.record_offer(offer_data)

        # Update offer
        update_data = OfferUpdate(
            salary=110000,
            status=OfferStatus.ACCEPTED,
            decision_notes="Great opportunity!"
        )
        updated = ats.update_offer(offer.id, update_data)

        assert updated.salary == 110000
        assert updated.status == OfferStatus.ACCEPTED
        assert updated.decision_date is not None

        # Verify job status updated
        db_session.refresh(job)
        assert job.status == ApplicationStatus.OFFER_ACCEPTED.value

    def test_add_negotiation(self, db_session, create_test_job):
        """Test adding negotiation to offer"""
        job = create_test_job(status="interviewing")
        ats = ATSService(db_session)

        # Create offer
        offer_data = OfferCreate(
            job_id=job.id,
            salary=100000,
            bonus=5000
        )
        offer = ats.record_offer(offer_data)

        # Add negotiation
        negotiation = OfferNegotiation(
            counter_salary=110000,
            counter_bonus=10000,
            counter_notes="Based on market research and my experience"
        )
        updated = ats.add_negotiation(offer.id, negotiation)

        assert updated.status == OfferStatus.NEGOTIATING
        assert updated.counter_offers is not None
        assert len(updated.counter_offers) == 1
        assert updated.counter_offers[0]["salary"] == 110000


class TestNotesManagement:
    """Test notes and communication tracking"""

    def test_add_general_note(self, db_session, create_test_job):
        """Test adding a general note"""
        job = create_test_job()
        ats = ATSService(db_session)

        note_data = ApplicationNoteCreate(
            job_id=job.id,
            note_type="general",
            title="First Impressions",
            content="Company culture seems great based on interview"
        )

        note = ats.add_note(note_data)

        assert note.id is not None
        assert note.job_id == job.id
        assert note.note_type == "general"
        assert note.is_communication is False

    def test_add_communication_note(self, db_session, create_test_job):
        """Test adding a communication record"""
        job = create_test_job()
        ats = ATSService(db_session)

        note_data = ApplicationNoteCreate(
            job_id=job.id,
            note_type="communication",
            content="Spoke with hiring manager about next steps",
            is_communication=True,
            communication_direction="inbound",
            communication_method="phone",
            contact_person="Jane Smith"
        )

        note = ats.add_note(note_data)

        assert note.is_communication is True
        assert note.communication_direction == "inbound"
        assert note.contact_person == "Jane Smith"

    def test_add_follow_up_note(self, db_session, create_test_job):
        """Test adding a follow-up reminder"""
        job = create_test_job()
        ats = ATSService(db_session)

        follow_up_date = datetime.utcnow() + timedelta(days=3)

        note_data = ApplicationNoteCreate(
            job_id=job.id,
            note_type="follow_up",
            content="Follow up on application status",
            requires_follow_up=True,
            follow_up_date=follow_up_date
        )

        note = ats.add_note(note_data)

        assert note.requires_follow_up is True
        assert note.follow_up_date == follow_up_date
        assert note.follow_up_completed is False

    def test_update_note(self, db_session, create_test_job):
        """Test updating a note"""
        job = create_test_job()
        ats = ATSService(db_session)

        # Create note
        note_data = ApplicationNoteCreate(
            job_id=job.id,
            note_type="general",
            content="Initial note"
        )
        note = ats.add_note(note_data)

        # Update note
        from app.schemas.application import ApplicationNoteUpdate
        update_data = ApplicationNoteUpdate(
            content="Updated note content",
            follow_up_completed=True
        )
        updated = ats.update_note(note.id, update_data)

        assert updated.content == "Updated note content"
        assert updated.follow_up_completed is True


class TestApplicationTimeline:
    """Test complete application timeline"""

    def test_get_application_timeline(self, db_session, create_test_job):
        """Test retrieving complete application timeline"""
        job = create_test_job(status="applied")
        ats = ATSService(db_session)

        # Add various items to timeline
        # 1. Schedule interview
        interview_data = InterviewCreate(
            job_id=job.id,
            interview_type=InterviewType.TECHNICAL,
            scheduled_date=datetime.utcnow() + timedelta(days=2)
        )
        ats.schedule_interview(interview_data)

        # 2. Add note
        note_data = ApplicationNoteCreate(
            job_id=job.id,
            note_type="general",
            content="Excited about this opportunity"
        )
        ats.add_note(note_data)

        # 3. Get timeline
        timeline = ats.get_application_timeline(job.id)

        assert timeline["job_id"] == job.id
        assert timeline["company"] == job.company
        assert len(timeline["events"]) > 0  # Status change events
        assert len(timeline["interviews"]) == 1
        assert len(timeline["notes"]) == 1

    def test_get_timeline_nonexistent_job(self, db_session):
        """Test retrieving timeline for non-existent job"""
        ats = ATSService(db_session)

        with pytest.raises(ValueError, match="Job .* not found"):
            ats.get_application_timeline(99999)


class TestStatistics:
    """Test application statistics"""

    def test_get_statistics(self, db_session, create_test_job):
        """Test retrieving application statistics"""
        # Create jobs in various statuses
        create_test_job(job_id="job1", status="discovered")
        create_test_job(job_id="job2", status="applied")
        create_test_job(job_id="job3", status="interviewing")
        job4 = create_test_job(job_id="job4", status="interviewing")

        ats = ATSService(db_session)

        # Add offer to one job
        offer_data = OfferCreate(
            job_id=job4.id,
            salary=100000
        )
        ats.record_offer(offer_data)

        # Get statistics
        stats = ats.get_statistics()

        assert stats["total_applications"] >= 4
        assert "discovered" in stats["by_status"]
        assert "applied" in stats["by_status"]
        assert stats["offers_received"] >= 1

    def test_empty_statistics(self, db_session):
        """Test statistics with no applications"""
        ats = ATSService(db_session)
        stats = ats.get_statistics()

        assert stats["total_applications"] == 0
        assert len(stats["by_status"]) == 0
        assert stats["interviews_scheduled"] == 0
        assert stats["offers_received"] == 0
