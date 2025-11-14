"""
Application Tracking System (ATS) Models

Tracks the complete job application lifecycle including interviews, offers, and events.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import enum

from ..database import Base


class ApplicationStatus(str, enum.Enum):
    """Valid application status transitions"""
    DISCOVERED = "discovered"  # Job found
    ANALYZING = "analyzing"  # Analysis in progress
    ANALYZED = "analyzed"  # Analysis complete
    READY_TO_APPLY = "ready_to_apply"  # Documents generated, ready to submit
    APPLIED = "applied"  # Application submitted
    SCREENING = "screening"  # Initial screening (phone/email)
    INTERVIEW_SCHEDULED = "interview_scheduled"  # Interview scheduled
    INTERVIEWING = "interviewing"  # In interview process
    OFFER_RECEIVED = "offer_received"  # Offer received
    OFFER_ACCEPTED = "offer_accepted"  # Offer accepted
    OFFER_REJECTED = "offer_rejected"  # Offer rejected
    REJECTED = "rejected"  # Application rejected
    WITHDRAWN = "withdrawn"  # Application withdrawn
    ARCHIVED = "archived"  # Archived (no longer active)


class InterviewType(str, enum.Enum):
    """Types of interviews"""
    PHONE_SCREEN = "phone_screen"
    VIDEO_SCREEN = "video_screen"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"
    ONSITE = "onsite"
    FINAL = "final"
    OTHER = "other"


class InterviewOutcome(str, enum.Enum):
    """Interview outcomes"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class OfferStatus(str, enum.Enum):
    """Offer statuses"""
    PENDING_REVIEW = "pending_review"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApplicationEvent(Base):
    """
    Track all events in the application lifecycle
    """
    __tablename__ = "application_events"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    event_type = Column(String, nullable=False)  # status_change, note_added, interview_scheduled, etc.
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional event data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job = relationship("Job", back_populates="events")


class Interview(Base):
    """
    Interview tracking
    """
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Interview details
    interview_type = Column(SQLEnum(InterviewType), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    location = Column(String, nullable=True)  # Physical address or video link
    is_virtual = Column(Boolean, default=False)

    # Participants
    interviewer_names = Column(String, nullable=True)  # Comma-separated
    interviewer_titles = Column(String, nullable=True)  # Comma-separated
    interviewer_emails = Column(String, nullable=True)  # Comma-separated

    # Preparation
    preparation_notes = Column(Text, nullable=True)
    questions_to_ask = Column(JSON, nullable=True)  # Array of questions
    key_points_to_mention = Column(JSON, nullable=True)  # Array of talking points

    # Outcome
    outcome = Column(SQLEnum(InterviewOutcome), default=InterviewOutcome.PENDING)
    feedback = Column(Text, nullable=True)
    performance_rating = Column(Integer, nullable=True)  # 1-5 scale
    notes = Column(Text, nullable=True)

    # Calendar integration
    calendar_event_id = Column(String, nullable=True)  # Google Calendar event ID

    # Reminders
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Calendar integration
    calendar_event_id = Column(String, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="interviews")


class Offer(Base):
    """
    Job offer tracking and negotiation
    """
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Offer details
    salary = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    salary_period = Column(String, default="annual")  # annual, hourly
    bonus = Column(Float, nullable=True)
    equity = Column(String, nullable=True)  # Stock options, RSUs, etc.
    sign_on_bonus = Column(Float, nullable=True)

    # Benefits
    benefits_summary = Column(Text, nullable=True)
    vacation_days = Column(Integer, nullable=True)
    healthcare_details = Column(Text, nullable=True)
    retirement_details = Column(Text, nullable=True)
    other_benefits = Column(JSON, nullable=True)

    # Terms
    start_date = Column(DateTime, nullable=True)
    remote_policy = Column(String, nullable=True)  # remote, hybrid, onsite
    relocation_assistance = Column(Boolean, default=False)
    offer_expiration_date = Column(DateTime, nullable=True)

    # Status and negotiation
    status = Column(SQLEnum(OfferStatus), default=OfferStatus.PENDING_REVIEW)
    received_date = Column(DateTime, default=datetime.utcnow)
    response_deadline = Column(DateTime, nullable=True)

    # Negotiation tracking
    negotiation_notes = Column(Text, nullable=True)
    counter_offers = Column(JSON, nullable=True)  # Array of counter-offer details
    negotiation_history = Column(JSON, nullable=True)  # Timeline of negotiation

    # Decision
    decision_date = Column(DateTime, nullable=True)
    decision_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Market comparison
    market_rate_comparison = Column(JSON, nullable=True)  # How this compares to market
    other_offers_comparison = Column(JSON, nullable=True)  # Compare with other offers

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="offers")


class ApplicationNote(Base):
    """
    Notes and communications related to the application
    """
    __tablename__ = "application_notes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    note_type = Column(String, nullable=False)  # general, communication, follow_up, etc.
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)

    # Communication tracking
    is_communication = Column(Boolean, default=False)
    communication_direction = Column(String, nullable=True)  # inbound, outbound
    communication_method = Column(String, nullable=True)  # email, phone, linkedin, etc.
    contact_person = Column(String, nullable=True)

    # Follow-up tracking
    requires_follow_up = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    follow_up_completed = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="notes")
