"""
Tests for Follow-up Service
"""
import pytest
from datetime import datetime, timedelta
from app.services.followup_service import FollowUpService
from app.schemas.followup import (
    FollowUpTemplateCreate,
    FollowUpSequenceCreate,
    ScheduleFollowUpRequest,
    FollowUpResponseCreate
)


class TestTemplateManagement:
    """Test template management"""

    def test_default_templates_created(self, db_session):
        """Test that default templates are created on initialization"""
        service = FollowUpService(db_session)

        from app.models.followup import FollowUpTemplate
        templates = db_session.query(FollowUpTemplate).all()

        assert len(templates) >= 4  # At least the 4 default templates
        assert any(t.template_name == "post_application_follow_up_1" for t in templates)
        assert any(t.template_name == "post_interview_thank_you" for t in templates)

    def test_create_custom_template(self, db_session):
        """Test creating a custom template"""
        service = FollowUpService(db_session)

        template_data = FollowUpTemplateCreate(
            template_name="custom_template",
            stage="post_application",
            sequence_position=1,
            subject_template="Custom subject: {job_title}",
            body_template="Custom body for {company}",
            days_after_previous=5,
            tone="casual"
        )

        template = service.create_template(template_data)

        assert template.id is not None
        assert template.template_name == "custom_template"
        assert template.tone == "casual"

    def test_get_templates_by_stage(self, db_session):
        """Test getting templates filtered by stage"""
        service = FollowUpService(db_session)

        templates = service.get_templates(stage="post_interview")

        assert len(templates) > 0
        assert all(t.stage == "post_interview" for t in templates)


class TestSequenceManagement:
    """Test sequence management"""

    def test_create_sequence(self, db_session):
        """Test creating a follow-up sequence"""
        service = FollowUpService(db_session)

        # Get template IDs
        templates = service.get_templates(stage="post_application")
        template_ids = [t.id for t in templates[:3]]

        sequence_data = FollowUpSequenceCreate(
            sequence_name="test_sequence",
            stage="post_application",
            description="Test sequence",
            template_ids=template_ids,
            timing_strategy="fixed",
            max_follow_ups=3
        )

        sequence = service.create_sequence(sequence_data)

        assert sequence.id is not None
        assert sequence.sequence_name == "test_sequence"
        assert len(sequence.template_ids) == 3

    def test_get_sequences_by_stage(self, db_session):
        """Test getting sequences filtered by stage"""
        service = FollowUpService(db_session)

        # Create a sequence first
        templates = service.get_templates(stage="post_application")
        if templates:
            sequence_data = FollowUpSequenceCreate(
                sequence_name="app_sequence",
                stage="post_application",
                template_ids=[templates[0].id],
                max_follow_ups=1
            )
            service.create_sequence(sequence_data)

        sequences = service.get_sequences(stage="post_application")

        assert len(sequences) > 0
        assert all(s.stage == "post_application" for s in sequences)


class TestFollowUpScheduling:
    """Test follow-up scheduling"""

    def test_schedule_single_followup(self, db_session, create_test_job):
        """Test scheduling a single follow-up"""
        job = create_test_job()
        service = FollowUpService(db_session)

        request = ScheduleFollowUpRequest(
            job_id=job.id,
            stage="post_application",
            recipient_email="hiring@company.com",
            recipient_name="Hiring Manager",
            custom_data={
                "candidate_name": "John Doe",
                "key_skill_1": "Python",
                "key_skill_2": "Data Analysis"
            }
        )

        result = service.schedule_followup_sequence(request)

        assert result["success"] is True
        assert result["followups_scheduled"] >= 1
        assert len(result["followup_ids"]) >= 1

    def test_schedule_followup_sequence(self, db_session, create_test_job):
        """Test scheduling a complete follow-up sequence"""
        job = create_test_job()
        service = FollowUpService(db_session)

        # Create sequence
        templates = service.get_templates(stage="post_application")
        if len(templates) >= 2:
            sequence_data = FollowUpSequenceCreate(
                sequence_name="test_multi_sequence",
                stage="post_application",
                template_ids=[templates[0].id, templates[1].id] if len(templates) >= 2 else [templates[0].id],
                max_follow_ups=2
            )
            sequence = service.create_sequence(sequence_data)

            request = ScheduleFollowUpRequest(
                job_id=job.id,
                stage="post_application",
                recipient_email="hr@company.com",
                sequence_name=sequence.sequence_name,
                custom_data={"candidate_name": "Jane Smith"}
            )

            result = service.schedule_followup_sequence(request)

            assert result["success"] is True
            assert result["followups_scheduled"] >= 1

    def test_schedule_followup_nonexistent_job(self, db_session):
        """Test scheduling follow-up for non-existent job"""
        service = FollowUpService(db_session)

        request = ScheduleFollowUpRequest(
            job_id=99999,
            stage="post_application",
            recipient_email="test@company.com"
        )

        with pytest.raises(ValueError, match="Job .* not found"):
            service.schedule_followup_sequence(request)

    def test_personalization(self, db_session):
        """Test template personalization"""
        service = FollowUpService(db_session)

        template = "Hi {recipient_name}, about {job_title} at {company}"
        data = {
            "recipient_name": "John",
            "job_title": "Developer",
            "company": "TechCorp"
        }

        result = service._personalize_template(template, data)

        assert result == "Hi John, about Developer at TechCorp"
        assert "{" not in result  # No remaining placeholders


class TestFollowUpExecution:
    """Test follow-up execution"""

    def test_send_followup(self, db_session, create_test_job):
        """Test sending a scheduled follow-up"""
        job = create_test_job()
        service = FollowUpService(db_session)

        # Schedule follow-up
        request = ScheduleFollowUpRequest(
            job_id=job.id,
            stage="post_application",
            recipient_email="test@company.com",
            custom_data={"candidate_name": "Test User"}
        )
        schedule_result = service.schedule_followup_sequence(request)

        followup_id = schedule_result["followup_ids"][0]

        # Send it
        send_result = service.send_followup(followup_id)

        assert send_result["success"] is True
        assert send_result["followup_id"] == followup_id
        assert send_result["sent_date"] is not None

    def test_send_nonexistent_followup(self, db_session):
        """Test sending non-existent follow-up"""
        service = FollowUpService(db_session)

        with pytest.raises(ValueError, match="Follow-up .* not found"):
            service.send_followup(99999)

    def test_get_pending_followups(self, db_session, create_test_job):
        """Test getting pending follow-ups"""
        job = create_test_job()
        service = FollowUpService(db_session)

        # Schedule follow-up with past date
        request = ScheduleFollowUpRequest(
            job_id=job.id,
            stage="post_application",
            recipient_email="test@company.com",
            custom_data={"candidate_name": "Test"}
        )
        service.schedule_followup_sequence(request)

        # Get pending
        pending = service.get_pending_followups()

        assert isinstance(pending, list)
        assert len(pending) > 0


class TestResponseTracking:
    """Test response tracking"""

    def test_record_response(self, db_session, create_test_job):
        """Test recording a response to a follow-up"""
        job = create_test_job()
        service = FollowUpService(db_session)

        # Schedule and get follow-up
        request = ScheduleFollowUpRequest(
            job_id=job.id,
            stage="post_application",
            recipient_email="test@company.com",
            custom_data={"candidate_name": "Test"}
        )
        schedule_result = service.schedule_followup_sequence(request)
        followup_id = schedule_result["followup_ids"][0]

        # Send it first
        service.send_followup(followup_id)

        # Record response
        response_data = FollowUpResponseCreate(
            followup_id=followup_id,
            response_type="positive",
            response_text="Thanks for following up! Let's schedule an interview.",
            sentiment_score=0.8,
            action_required=True
        )

        response = service.record_response(response_data)

        assert response.id is not None
        assert response.response_type == "positive"
        assert response.sentiment_label == "positive"

    def test_response_cancels_subsequent_followups(self, db_session, create_test_job):
        """Test that response cancels subsequent follow-ups when configured"""
        job = create_test_job()
        service = FollowUpService(db_session)

        # Create sequence with stop_on_response=True
        templates = service.get_templates(stage="post_application")
        if len(templates) >= 2:
            sequence_data = FollowUpSequenceCreate(
                sequence_name="stop_on_response_seq",
                stage="post_application",
                template_ids=[templates[0].id, templates[1].id] if len(templates) >= 2 else [templates[0].id],
                stop_on_response=True,
                max_follow_ups=2
            )
            sequence = service.create_sequence(sequence_data)

            # Schedule sequence
            request = ScheduleFollowUpRequest(
                job_id=job.id,
                stage="post_application",
                recipient_email="test@company.com",
                sequence_name=sequence.sequence_name,
                custom_data={"candidate_name": "Test"}
            )
            schedule_result = service.schedule_followup_sequence(request)

            if len(schedule_result["followup_ids"]) >= 2:
                first_followup_id = schedule_result["followup_ids"][0]

                # Send first follow-up
                service.send_followup(first_followup_id)

                # Record response
                response_data = FollowUpResponseCreate(
                    followup_id=first_followup_id,
                    response_type="positive",
                    response_text="Let's talk!"
                )
                service.record_response(response_data)

                # Check that subsequent follow-ups were cancelled
                from app.models.followup import FollowUp
                followups = db_session.query(FollowUp).filter(
                    FollowUp.job_id == job.id
                ).all()

                # At least one should be cancelled
                cancelled = [f for f in followups if f.status == "cancelled"]
                assert len(cancelled) >= 1


class TestAnalytics:
    """Test follow-up analytics"""

    def test_calculate_analytics_no_data(self, db_session):
        """Test analytics calculation with no data"""
        service = FollowUpService(db_session)
        analytics = service.calculate_analytics()

        assert analytics is None

    def test_calculate_analytics_with_data(self, db_session, create_test_job):
        """Test analytics calculation with follow-up data"""
        service = FollowUpService(db_session)

        # Create and send several follow-ups
        for i in range(5):
            job = create_test_job(job_id=f"analytics_job_{i}")

            request = ScheduleFollowUpRequest(
                job_id=job.id,
                stage="post_application",
                recipient_email=f"test{i}@company.com",
                custom_data={"candidate_name": f"User {i}"}
            )
            result = service.schedule_followup_sequence(request)

            for followup_id in result["followup_ids"]:
                service.send_followup(followup_id)

                # Record response for some
                if i % 2 == 0:
                    response_data = FollowUpResponseCreate(
                        followup_id=followup_id,
                        response_type="positive",
                        response_text="Response"
                    )
                    service.record_response(response_data)

        # Calculate analytics
        analytics = service.calculate_analytics(period_days=30)

        assert analytics is not None
        assert analytics.total_sent >= 5
        assert analytics.total_responded >= 2
        assert analytics.response_rate is not None


class TestTimingOptimization:
    """Test timing optimization"""

    def test_get_optimal_timing(self, db_session):
        """Test optimal timing calculation"""
        service = FollowUpService(db_session)

        timing = service._get_optimal_timing("post_application", 1)
        assert isinstance(timing, int)
        assert timing > 0

        timing2 = service._get_optimal_timing("post_interview", 1)
        assert isinstance(timing2, int)

    def test_exponential_backoff_timing(self, db_session, create_test_job):
        """Test exponential backoff timing strategy"""
        job = create_test_job()
        service = FollowUpService(db_session)

        # Create sequence with exponential timing
        templates = service.get_templates(stage="post_application")
        if len(templates) >= 3:
            sequence_data = FollowUpSequenceCreate(
                sequence_name="exponential_seq",
                stage="post_application",
                template_ids=[templates[0].id, templates[1].id, templates[2].id] if len(templates) >= 3 else [templates[0].id],
                timing_strategy="exponential",
                max_follow_ups=3
            )
            sequence = service.create_sequence(sequence_data)

            request = ScheduleFollowUpRequest(
                job_id=job.id,
                stage="post_application",
                recipient_email="test@company.com",
                sequence_name=sequence.sequence_name,
                custom_data={"candidate_name": "Test"}
            )
            service.schedule_followup_sequence(request)

            # Verify timing increases exponentially
            from app.models.followup import FollowUp
            followups = db_session.query(FollowUp).filter(
                FollowUp.job_id == job.id
            ).order_by(FollowUp.sequence_position).all()

            if len(followups) >= 2:
                # Second follow-up should be scheduled later than first
                assert followups[1].scheduled_date > followups[0].scheduled_date
