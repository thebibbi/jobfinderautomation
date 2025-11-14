"""
Pydantic schemas for Application Tracking System
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ApplicationStatusEnum(str, Enum):
    """Application status values"""
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    READY_TO_APPLY = "ready_to_apply"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWING = "interviewing"
    OFFER_RECEIVED = "offer_received"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_REJECTED = "offer_rejected"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ARCHIVED = "archived"


class InterviewTypeEnum(str, Enum):
    """Interview types"""
    PHONE_SCREEN = "phone_screen"
    VIDEO_SCREEN = "video_screen"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"
    ONSITE = "onsite"
    FINAL = "final"
    OTHER = "other"


class InterviewOutcomeEnum(str, Enum):
    """Interview outcomes"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class OfferStatusEnum(str, Enum):
    """Offer statuses"""
    PENDING_REVIEW = "pending_review"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ==================== Status Update ====================

class StatusUpdate(BaseModel):
    """Request to update job status"""
    status: ApplicationStatusEnum
    notes: Optional[str] = None


class StatusUpdateResponse(BaseModel):
    """Response after status update"""
    success: bool
    job_id: int
    old_status: str
    new_status: str
    message: str


# ==================== Events ====================

class ApplicationEventBase(BaseModel):
    """Base application event"""
    event_type: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ApplicationEventCreate(ApplicationEventBase):
    """Create application event"""
    job_id: int
    old_status: Optional[str] = None
    new_status: Optional[str] = None


class ApplicationEvent(ApplicationEventBase):
    """Application event response"""
    id: int
    job_id: int
    old_status: Optional[str]
    new_status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Interviews ====================

class InterviewBase(BaseModel):
    """Base interview data"""
    interview_type: InterviewTypeEnum
    scheduled_date: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    is_virtual: bool = False
    interviewer_names: Optional[str] = None
    interviewer_titles: Optional[str] = None
    interviewer_emails: Optional[str] = None


class InterviewCreate(InterviewBase):
    """Create interview"""
    job_id: int
    preparation_notes: Optional[str] = None
    questions_to_ask: Optional[List[str]] = None
    key_points_to_mention: Optional[List[str]] = None


class InterviewUpdate(BaseModel):
    """Update interview"""
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    preparation_notes: Optional[str] = None
    questions_to_ask: Optional[List[str]] = None
    key_points_to_mention: Optional[List[str]] = None
    outcome: Optional[InterviewOutcomeEnum] = None
    feedback: Optional[str] = None
    performance_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class Interview(InterviewBase):
    """Interview response"""
    id: int
    job_id: int
    preparation_notes: Optional[str]
    questions_to_ask: Optional[List[str]]
    key_points_to_mention: Optional[List[str]]
    outcome: InterviewOutcomeEnum
    feedback: Optional[str]
    performance_rating: Optional[int]
    notes: Optional[str]
    reminder_sent: bool
    reminder_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    calendar_event_id: Optional[str]

    class Config:
        from_attributes = True


# ==================== Offers ====================

class OfferBase(BaseModel):
    """Base offer data"""
    salary: Optional[float] = None
    currency: str = "USD"
    salary_period: str = "annual"
    bonus: Optional[float] = None
    equity: Optional[str] = None
    sign_on_bonus: Optional[float] = None


class OfferCreate(OfferBase):
    """Create offer"""
    job_id: int
    benefits_summary: Optional[str] = None
    vacation_days: Optional[int] = None
    healthcare_details: Optional[str] = None
    retirement_details: Optional[str] = None
    other_benefits: Optional[Dict[str, Any]] = None
    start_date: Optional[datetime] = None
    remote_policy: Optional[str] = None
    relocation_assistance: bool = False
    offer_expiration_date: Optional[datetime] = None
    response_deadline: Optional[datetime] = None


class OfferUpdate(BaseModel):
    """Update offer"""
    salary: Optional[float] = None
    bonus: Optional[float] = None
    equity: Optional[str] = None
    status: Optional[OfferStatusEnum] = None
    negotiation_notes: Optional[str] = None
    decision_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class OfferNegotiation(BaseModel):
    """Record negotiation action"""
    counter_salary: Optional[float] = None
    counter_bonus: Optional[float] = None
    counter_equity: Optional[str] = None
    counter_notes: str


class Offer(OfferBase):
    """Offer response"""
    id: int
    job_id: int
    benefits_summary: Optional[str]
    vacation_days: Optional[int]
    healthcare_details: Optional[str]
    retirement_details: Optional[str]
    other_benefits: Optional[Dict[str, Any]]
    start_date: Optional[datetime]
    remote_policy: Optional[str]
    relocation_assistance: bool
    offer_expiration_date: Optional[datetime]
    status: OfferStatusEnum
    received_date: datetime
    response_deadline: Optional[datetime]
    negotiation_notes: Optional[str]
    counter_offers: Optional[List[Dict[str, Any]]]
    negotiation_history: Optional[List[Dict[str, Any]]]
    decision_date: Optional[datetime]
    decision_notes: Optional[str]
    rejection_reason: Optional[str]
    market_rate_comparison: Optional[Dict[str, Any]]
    other_offers_comparison: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Notes ====================

class ApplicationNoteBase(BaseModel):
    """Base note data"""
    note_type: str
    title: Optional[str] = None
    content: str


class ApplicationNoteCreate(ApplicationNoteBase):
    """Create note"""
    job_id: int
    is_communication: bool = False
    communication_direction: Optional[str] = None  # inbound, outbound
    communication_method: Optional[str] = None
    contact_person: Optional[str] = None
    requires_follow_up: bool = False
    follow_up_date: Optional[datetime] = None


class ApplicationNoteUpdate(BaseModel):
    """Update note"""
    title: Optional[str] = None
    content: Optional[str] = None
    follow_up_completed: Optional[bool] = None


class ApplicationNote(ApplicationNoteBase):
    """Note response"""
    id: int
    job_id: int
    is_communication: bool
    communication_direction: Optional[str]
    communication_method: Optional[str]
    contact_person: Optional[str]
    requires_follow_up: bool
    follow_up_date: Optional[datetime]
    follow_up_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Application Timeline ====================

class ApplicationTimeline(BaseModel):
    """Complete application timeline"""
    job_id: int
    company: str
    job_title: str
    current_status: str
    events: List[ApplicationEvent]
    interviews: List[Interview]
    offers: List[Offer]
    notes: List[ApplicationNote]
    created_at: datetime
    last_updated: datetime


# ==================== Statistics ====================

class ApplicationStatistics(BaseModel):
    """Application statistics"""
    total_applications: int
    by_status: Dict[str, int]
    interviews_scheduled: int
    interviews_completed: int
    offers_received: int
    offers_accepted: int
    average_time_to_interview_days: Optional[float]
    average_time_to_offer_days: Optional[float]
    success_rate: Optional[float]
