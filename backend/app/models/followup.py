"""
Follow-up System Models

Tracks and automates follow-up communications.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class FollowUpStage(str, enum.Enum):
    """Follow-up stages"""
    POST_APPLICATION = "post_application"
    POST_INTERVIEW = "post_interview"
    POST_OFFER = "post_offer"
    NO_RESPONSE = "no_response"
    NETWORKING = "networking"


class FollowUpStatus(str, enum.Enum):
    """Follow-up status"""
    SCHEDULED = "scheduled"
    SENT = "sent"
    OPENED = "opened"
    RESPONDED = "responded"
    BOUNCED = "bounced"
    CANCELLED = "cancelled"


class FollowUpTemplate(Base):
    """
    Email templates for different follow-up scenarios
    """
    __tablename__ = "followup_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template identification
    template_name = Column(String, unique=True, nullable=False)
    stage = Column(String, nullable=False)  # FollowUpStage
    sequence_position = Column(Integer, default=1)  # 1st, 2nd, 3rd follow-up

    # Template content
    subject_template = Column(String, nullable=False)
    body_template = Column(Text, nullable=False)

    # Timing
    days_after_previous = Column(Integer, default=3)  # Days to wait after previous action

    # Tone and style
    tone = Column(String, default="professional")  # professional, friendly, casual
    include_value_add = Column(Boolean, default=True)  # Include additional value (article, insight)

    # Metadata
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)  # Percentage that got responses

    # Template variables available
    available_variables = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FollowUpSequence(Base):
    """
    Follow-up sequence configuration for different scenarios
    """
    __tablename__ = "followup_sequences"

    id = Column(Integer, primary_key=True, index=True)

    # Sequence identification
    sequence_name = Column(String, unique=True, nullable=False)
    stage = Column(String, nullable=False)  # FollowUpStage
    description = Column(Text, nullable=True)

    # Sequence steps (template IDs in order)
    template_ids = Column(JSON, nullable=False)  # Array of template IDs

    # Timing strategy
    timing_strategy = Column(String, default="fixed")  # fixed, exponential, optimal

    # Stop conditions
    stop_on_response = Column(Boolean, default=True)
    max_follow_ups = Column(Integer, default=3)

    # Performance
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    response_rate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FollowUp(Base):
    """
    Individual follow-up instance
    """
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Follow-up details
    stage = Column(String, nullable=False)  # FollowUpStage
    sequence_id = Column(Integer, ForeignKey("followup_sequences.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("followup_templates.id"), nullable=True)
    sequence_position = Column(Integer, default=1)

    # Recipient
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=True)
    recipient_title = Column(String, nullable=True)

    # Email content
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    personalization_data = Column(JSON, nullable=True)  # Data used for personalization

    # Scheduling
    scheduled_date = Column(DateTime, nullable=False)
    sent_date = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(String, default=FollowUpStatus.SCHEDULED.value)
    opened_date = Column(DateTime, nullable=True)
    responded_date = Column(DateTime, nullable=True)
    response_text = Column(Text, nullable=True)

    # Email tracking
    email_id = Column(String, nullable=True)  # External email service ID
    tracking_data = Column(JSON, nullable=True)  # Open/click tracking

    # Next follow-up
    next_followup_id = Column(Integer, ForeignKey("followups.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", backref="followups")
    sequence = relationship("FollowUpSequence")
    template = relationship("FollowUpTemplate")
    next_followup = relationship("FollowUp", remote_side=[id], foreign_keys=[next_followup_id])


class FollowUpResponse(Base):
    """
    Track responses to follow-ups
    """
    __tablename__ = "followup_responses"

    id = Column(Integer, primary_key=True, index=True)
    followup_id = Column(Integer, ForeignKey("followups.id"), nullable=False)

    # Response details
    response_date = Column(DateTime, default=datetime.utcnow)
    response_type = Column(String, nullable=False)  # positive, negative, neutral, question
    response_text = Column(Text, nullable=True)

    # Sentiment analysis
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    sentiment_label = Column(String, nullable=True)  # positive, negative, neutral

    # Action taken
    action_required = Column(Boolean, default=False)
    action_taken = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    followup = relationship("FollowUp", backref="responses")


class FollowUpAnalytics(Base):
    """
    Analytics for follow-up effectiveness
    """
    __tablename__ = "followup_analytics"

    id = Column(Integer, primary_key=True, index=True)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Overall metrics
    total_sent = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_responded = Column(Integer, default=0)

    open_rate = Column(Float, nullable=True)
    response_rate = Column(Float, nullable=True)

    # By stage
    metrics_by_stage = Column(JSON, nullable=True)

    # By template
    metrics_by_template = Column(JSON, nullable=True)

    # Timing analysis
    avg_response_time_hours = Column(Float, nullable=True)
    best_send_time = Column(String, nullable=True)  # e.g., "Tuesday 10:00 AM"
    best_send_day = Column(String, nullable=True)

    # Sequence analysis
    avg_followups_to_response = Column(Float, nullable=True)
    most_effective_sequence = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
