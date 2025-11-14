"""
Follow-up Service

Manages automated follow-up sequences and email generation.
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from loguru import logger
import re

from ..models.job import Job
from ..models.followup import (
    FollowUpTemplate,
    FollowUpSequence,
    FollowUp,
    FollowUpResponse as FollowUpResponseModel,
    FollowUpAnalytics as AnalyticsModel,
    FollowUpStage,
    FollowUpStatus
)
from ..schemas.followup import (
    FollowUpTemplateCreate,
    FollowUpSequenceCreate,
    FollowUpCreate,
    ScheduleFollowUpRequest,
    FollowUpResponseCreate
)


class FollowUpService:
    """Follow-up Service"""

    # Default templates
    DEFAULT_TEMPLATES = {
        "post_application_1": {
            "template_name": "post_application_follow_up_1",
            "stage": "post_application",
            "sequence_position": 1,
            "subject_template": "Following up on {job_title} application",
            "body_template": """Hi {recipient_name},

I wanted to follow up on my application for the {job_title} position at {company}. I'm very excited about the opportunity to contribute to your team.

Since submitting my application, I've been following {company}'s recent work on {relevant_news}, and I'm even more enthusiastic about the role.

I'd love to discuss how my background in {key_skill_1} and {key_skill_2} could help your team achieve {company_goal}.

Would you have 15 minutes this week for a brief conversation?

Best regards,
{candidate_name}""",
            "days_after_previous": 3,
            "tone": "professional"
        },
        "post_interview_1": {
            "template_name": "post_interview_thank_you",
            "stage": "post_interview",
            "sequence_position": 1,
            "subject_template": "Thank you for the {job_title} interview",
            "body_template": """Hi {interviewer_name},

Thank you for taking the time to speak with me today about the {job_title} position. I really enjoyed our conversation about {discussion_topic}.

Our discussion about {specific_point} was particularly interesting, and it reinforced my excitement about the role.

I'm confident that my experience with {relevant_experience} would allow me to make an immediate impact on {company_challenge}.

I look forward to hearing about next steps!

Best regards,
{candidate_name}""",
            "days_after_previous": 0,  # Send same day
            "tone": "friendly"
        },
        "post_interview_2": {
            "template_name": "post_interview_follow_up",
            "stage": "post_interview",
            "sequence_position": 2,
            "subject_template": "Checking in about {job_title}",
            "body_template": """Hi {interviewer_name},

I hope this message finds you well. I wanted to check in regarding the {job_title} position we discussed on {interview_date}.

I remain very interested in the opportunity and would love to move forward in the process.

Please let me know if there's any additional information I can provide.

Best regards,
{candidate_name}""",
            "days_after_previous": 7,
            "tone": "professional"
        },
        "no_response": {
            "template_name": "no_response_follow_up",
            "stage": "no_response",
            "sequence_position": 1,
            "subject_template": "Still interested in {job_title}",
            "body_template": """Hi {recipient_name},

I wanted to reach out one more time regarding the {job_title} position at {company}.

I understand you're likely very busy, but I remain very interested in this opportunity. I believe my {key_strength} would be valuable to your team.

If the position has been filled or the timeline has changed, I completely understand. Otherwise, I'd love to connect briefly.

Best regards,
{candidate_name}""",
            "days_after_previous": 5,
            "tone": "friendly"
        }
    }

    def __init__(self, db: Session):
        self.db = db
        self._ensure_default_templates()

    def _ensure_default_templates(self):
        """Ensure default templates exist"""
        for template_data in self.DEFAULT_TEMPLATES.values():
            existing = self.db.query(FollowUpTemplate).filter(
                FollowUpTemplate.template_name == template_data["template_name"]
            ).first()

            if not existing:
                template = FollowUpTemplate(**template_data)
                self.db.add(template)

        self.db.commit()

    # ==================== Template Management ====================

    def create_template(self, template_data: FollowUpTemplateCreate) -> FollowUpTemplate:
        """Create a follow-up template"""
        template = FollowUpTemplate(**template_data.model_dump())
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        logger.info(f"✉️ Created follow-up template: {template.template_name}")
        return template

    def get_templates(
        self,
        stage: Optional[str] = None,
        active_only: bool = True
    ) -> List[FollowUpTemplate]:
        """Get follow-up templates"""
        query = self.db.query(FollowUpTemplate)

        if stage:
            query = query.filter(FollowUpTemplate.stage == stage)

        if active_only:
            query = query.filter(FollowUpTemplate.is_active == True)

        return query.order_by(FollowUpTemplate.stage, FollowUpTemplate.sequence_position).all()

    # ==================== Sequence Management ====================

    def create_sequence(self, sequence_data: FollowUpSequenceCreate) -> FollowUpSequence:
        """Create a follow-up sequence"""
        sequence = FollowUpSequence(**sequence_data.model_dump())
        self.db.add(sequence)
        self.db.commit()
        self.db.refresh(sequence)

        logger.info(f"📋 Created follow-up sequence: {sequence.sequence_name}")
        return sequence

    def get_sequences(
        self,
        stage: Optional[str] = None,
        active_only: bool = True
    ) -> List[FollowUpSequence]:
        """Get follow-up sequences"""
        query = self.db.query(FollowUpSequence)

        if stage:
            query = query.filter(FollowUpSequence.stage == stage)

        if active_only:
            query = query.filter(FollowUpSequence.is_active == True)

        return query.all()

    # ==================== Follow-up Scheduling ====================

    def schedule_followup_sequence(
        self,
        request: ScheduleFollowUpRequest
    ) -> Dict[str, Any]:
        """
        Schedule a complete follow-up sequence

        Args:
            request: Scheduling request

        Returns:
            Scheduling result with follow-up IDs
        """
        job = self.db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise ValueError(f"Job {request.job_id} not found")

        # Get sequence (specific or default for stage)
        if request.sequence_name:
            sequence = self.db.query(FollowUpSequence).filter(
                FollowUpSequence.sequence_name == request.sequence_name,
                FollowUpSequence.is_active == True
            ).first()
        else:
            sequence = self.db.query(FollowUpSequence).filter(
                FollowUpSequence.stage == request.stage,
                FollowUpSequence.is_active == True
            ).first()

        if sequence:
            return self._schedule_sequence(job, sequence, request)
        else:
            # No sequence found, schedule single follow-up with default template
            return self._schedule_single_followup(job, request)

    def _schedule_sequence(
        self,
        job: Job,
        sequence: FollowUpSequence,
        request: ScheduleFollowUpRequest
    ) -> Dict[str, Any]:
        """Schedule all follow-ups in a sequence"""
        followup_ids = []
        current_date = datetime.utcnow()

        previous_followup = None

        for i, template_id in enumerate(sequence.template_ids):
            template = self.db.query(FollowUpTemplate).filter(
                FollowUpTemplate.id == template_id
            ).first()

            if not template:
                logger.warning(f"Template {template_id} not found in sequence")
                continue

            # Calculate scheduled date
            if i == 0:
                scheduled_date = current_date
            else:
                days_delay = template.days_after_previous
                if sequence.timing_strategy == "exponential":
                    days_delay = days_delay * (2 ** i)  # Exponential backoff
                elif sequence.timing_strategy == "optimal":
                    days_delay = self._get_optimal_timing(request.stage, i + 1)

                scheduled_date = current_date + timedelta(days=days_delay)

            # Personalize email
            personalization_data = {
                "job_title": job.job_title,
                "company": job.company,
                "candidate_name": request.custom_data.get("candidate_name", "Your Name") if request.custom_data else "Your Name",
                "recipient_name": request.recipient_name or "there",
                **(request.custom_data or {})
            }

            subject = self._personalize_template(template.subject_template, personalization_data)
            body = self._personalize_template(template.body_template, personalization_data)

            # Create follow-up
            followup = FollowUp(
                job_id=job.id,
                stage=request.stage,
                sequence_id=sequence.id,
                template_id=template.id,
                sequence_position=i + 1,
                recipient_email=request.recipient_email,
                recipient_name=request.recipient_name,
                recipient_title=request.recipient_title,
                subject=subject,
                body=body,
                personalization_data=personalization_data,
                scheduled_date=scheduled_date,
                status=FollowUpStatus.SCHEDULED.value
            )

            self.db.add(followup)
            self.db.flush()  # Get ID without committing

            # Link to previous follow-up
            if previous_followup:
                previous_followup.next_followup_id = followup.id

            followup_ids.append(followup.id)
            previous_followup = followup

        self.db.commit()

        # Update sequence usage
        sequence.usage_count += 1
        self.db.commit()

        logger.info(f"📅 Scheduled {len(followup_ids)} follow-ups for job {job.id}")

        return {
            "success": True,
            "followups_scheduled": len(followup_ids),
            "followup_ids": followup_ids,
            "next_followup_date": current_date if followup_ids else None,
            "message": f"Scheduled {len(followup_ids)} follow-ups"
        }

    def _schedule_single_followup(
        self,
        job: Job,
        request: ScheduleFollowUpRequest
    ) -> Dict[str, Any]:
        """Schedule a single follow-up without sequence"""
        # Get first template for stage
        template = self.db.query(FollowUpTemplate).filter(
            FollowUpTemplate.stage == request.stage,
            FollowUpTemplate.is_active == True,
            FollowUpTemplate.sequence_position == 1
        ).first()

        if not template:
            raise ValueError(f"No template found for stage: {request.stage}")

        personalization_data = {
            "job_title": job.job_title,
            "company": job.company,
            "candidate_name": request.custom_data.get("candidate_name", "Your Name") if request.custom_data else "Your Name",
            "recipient_name": request.recipient_name or "there",
            **(request.custom_data or {})
        }

        subject = self._personalize_template(template.subject_template, personalization_data)
        body = self._personalize_template(template.body_template, personalization_data)

        followup = FollowUp(
            job_id=job.id,
            stage=request.stage,
            template_id=template.id,
            sequence_position=1,
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            recipient_title=request.recipient_title,
            subject=subject,
            body=body,
            personalization_data=personalization_data,
            scheduled_date=datetime.utcnow(),
            status=FollowUpStatus.SCHEDULED.value
        )

        self.db.add(followup)
        self.db.commit()
        self.db.refresh(followup)

        return {
            "success": True,
            "followups_scheduled": 1,
            "followup_ids": [followup.id],
            "next_followup_date": followup.scheduled_date,
            "message": "Scheduled 1 follow-up"
        }

    def _personalize_template(self, template: str, data: Dict[str, Any]) -> str:
        """Replace template variables with actual data"""
        result = template

        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # Replace any remaining placeholders with empty string
        result = re.sub(r'\{[^}]+\}', '', result)

        return result

    def _get_optimal_timing(self, stage: str, position: int) -> int:
        """Get optimal timing based on historical data"""
        # Simplified - in production, analyze actual response patterns
        timing_map = {
            "post_application": [3, 7, 14],  # Days for 1st, 2nd, 3rd follow-up
            "post_interview": [0, 7, 14],
            "no_response": [5, 10, 15]
        }

        defaults = timing_map.get(stage, [3, 7, 14])
        return defaults[min(position - 1, len(defaults) - 1)]

    # ==================== Follow-up Execution ====================

    def send_followup(self, followup_id: int) -> Dict[str, Any]:
        """
        Send a scheduled follow-up

        Args:
            followup_id: Follow-up ID

        Returns:
            Send result
        """
        followup = self.db.query(FollowUp).filter(FollowUp.id == followup_id).first()
        if not followup:
            raise ValueError(f"Follow-up {followup_id} not found")

        # In production, integrate with email service (SendGrid, etc.)
        # For now, just mark as sent
        followup.status = FollowUpStatus.SENT.value
        followup.sent_date = datetime.utcnow()
        followup.email_id = f"mock_email_{followup_id}"

        self.db.commit()
        self.db.refresh(followup)

        logger.info(f"📧 Sent follow-up {followup_id} to {followup.recipient_email}")

        return {
            "success": True,
            "followup_id": followup_id,
            "sent_date": followup.sent_date,
            "email_id": followup.email_id,
            "message": "Follow-up sent successfully"
        }

    def get_pending_followups(self) -> List[FollowUp]:
        """Get follow-ups ready to be sent"""
        return self.db.query(FollowUp).filter(
            FollowUp.status == FollowUpStatus.SCHEDULED.value,
            FollowUp.scheduled_date <= datetime.utcnow()
        ).all()

    # ==================== Response Tracking ====================

    def record_response(self, response_data: FollowUpResponseCreate) -> FollowUpResponseModel:
        """Record a response to a follow-up"""
        followup = self.db.query(FollowUp).filter(
            FollowUp.id == response_data.followup_id
        ).first()

        if not followup:
            raise ValueError(f"Follow-up {response_data.followup_id} not found")

        # Create response record
        response = FollowUpResponseModel(**response_data.model_dump())
        self.db.add(response)

        # Update follow-up status
        followup.status = FollowUpStatus.RESPONDED.value
        followup.responded_date = datetime.utcnow()
        followup.response_text = response_data.response_text

        # Determine sentiment label
        if response_data.sentiment_score:
            if response_data.sentiment_score > 0.3:
                response.sentiment_label = "positive"
            elif response_data.sentiment_score < -0.3:
                response.sentiment_label = "negative"
            else:
                response.sentiment_label = "neutral"

        # Cancel subsequent follow-ups if sequence should stop on response
        if followup.sequence_id:
            sequence = self.db.query(FollowUpSequence).filter(
                FollowUpSequence.id == followup.sequence_id
            ).first()

            if sequence and sequence.stop_on_response:
                self._cancel_subsequent_followups(followup)

        self.db.commit()
        self.db.refresh(response)

        logger.info(f"✅ Recorded response to follow-up {response_data.followup_id}")

        return response

    def _cancel_subsequent_followups(self, followup: FollowUp):
        """Cancel subsequent follow-ups in sequence"""
        if followup.next_followup_id:
            next_followup = self.db.query(FollowUp).filter(
                FollowUp.id == followup.next_followup_id
            ).first()

            if next_followup and next_followup.status == FollowUpStatus.SCHEDULED.value:
                next_followup.status = FollowUpStatus.CANCELLED.value
                self._cancel_subsequent_followups(next_followup)  # Recursive

    # ==================== Analytics ====================

    def calculate_analytics(self, period_days: int = 30) -> AnalyticsModel:
        """Calculate follow-up analytics"""
        period_start = datetime.utcnow() - timedelta(days=period_days)
        period_end = datetime.utcnow()

        followups = self.db.query(FollowUp).filter(
            FollowUp.sent_date >= period_start,
            FollowUp.sent_date <= period_end
        ).all()

        if not followups:
            return None

        total_sent = len(followups)
        total_opened = sum(1 for f in followups if f.opened_date)
        total_responded = sum(1 for f in followups if f.responded_date)

        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else None
        response_rate = (total_responded / total_sent * 100) if total_sent > 0 else None

        # Calculate average response time
        response_times = []
        for f in followups:
            if f.sent_date and f.responded_date:
                hours = (f.responded_date - f.sent_date).total_seconds() / 3600
                response_times.append(hours)

        avg_response_time = sum(response_times) / len(response_times) if response_times else None

        # Create analytics record
        analytics = AnalyticsModel(
            period_start=period_start,
            period_end=period_end,
            total_sent=total_sent,
            total_opened=total_opened,
            total_responded=total_responded,
            open_rate=open_rate,
            response_rate=response_rate,
            avg_response_time_hours=avg_response_time
        )

        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)

        return analytics


def get_followup_service(db: Session) -> FollowUpService:
    """Get follow-up service instance"""
    return FollowUpService(db)
