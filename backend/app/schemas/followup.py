"""
Follow-up System Schemas
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== Templates ====================

class FollowUpTemplateBase(BaseModel):
    """Base template data"""
    template_name: str
    stage: str
    sequence_position: int = 1
    subject_template: str
    body_template: str
    days_after_previous: int = 3
    tone: str = "professional"
    include_value_add: bool = True


class FollowUpTemplateCreate(FollowUpTemplateBase):
    """Create template"""
    available_variables: Optional[List[str]] = None


class FollowUpTemplateUpdate(BaseModel):
    """Update template"""
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    days_after_previous: Optional[int] = None
    tone: Optional[str] = None
    is_active: Optional[bool] = None


class FollowUpTemplate(FollowUpTemplateBase):
    """Template response"""
    id: int
    is_active: bool
    usage_count: int
    success_rate: Optional[float]
    available_variables: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Sequences ====================

class FollowUpSequenceBase(BaseModel):
    """Base sequence data"""
    sequence_name: str
    stage: str
    description: Optional[str] = None
    timing_strategy: str = "fixed"
    stop_on_response: bool = True
    max_follow_ups: int = 3


class FollowUpSequenceCreate(FollowUpSequenceBase):
    """Create sequence"""
    template_ids: List[int]


class FollowUpSequenceUpdate(BaseModel):
    """Update sequence"""
    description: Optional[str] = None
    template_ids: Optional[List[int]] = None
    timing_strategy: Optional[str] = None
    max_follow_ups: Optional[int] = None
    is_active: Optional[bool] = None


class FollowUpSequence(FollowUpSequenceBase):
    """Sequence response"""
    id: int
    template_ids: List[int]
    is_active: bool
    usage_count: int
    response_rate: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Follow-ups ====================

class FollowUpCreate(BaseModel):
    """Create follow-up"""
    job_id: int
    stage: str
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    recipient_title: Optional[str] = None
    sequence_id: Optional[int] = None
    template_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    personalization_data: Optional[Dict[str, Any]] = None


class FollowUpUpdate(BaseModel):
    """Update follow-up"""
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    response_text: Optional[str] = None


class FollowUp(BaseModel):
    """Follow-up response"""
    id: int
    job_id: int
    stage: str
    sequence_id: Optional[int]
    template_id: Optional[int]
    sequence_position: int
    recipient_email: str
    recipient_name: Optional[str]
    recipient_title: Optional[str]
    subject: str
    body: str
    personalization_data: Optional[Dict[str, Any]]
    scheduled_date: datetime
    sent_date: Optional[datetime]
    status: str
    opened_date: Optional[datetime]
    responded_date: Optional[datetime]
    response_text: Optional[str]
    email_id: Optional[str]
    tracking_data: Optional[Dict[str, Any]]
    next_followup_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Responses ====================

class FollowUpResponseCreate(BaseModel):
    """Create follow-up response"""
    followup_id: int
    response_type: str  # positive, negative, neutral, question
    response_text: Optional[str] = None
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    action_required: bool = False


class FollowUpResponse(BaseModel):
    """Follow-up response"""
    id: int
    followup_id: int
    response_date: datetime
    response_type: str
    response_text: Optional[str]
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    action_required: bool
    action_taken: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Analytics ====================

class FollowUpAnalytics(BaseModel):
    """Follow-up analytics"""
    id: int
    period_start: datetime
    period_end: datetime
    total_sent: int
    total_opened: int
    total_responded: int
    open_rate: Optional[float]
    response_rate: Optional[float]
    metrics_by_stage: Optional[Dict[str, Any]]
    metrics_by_template: Optional[Dict[str, Any]]
    avg_response_time_hours: Optional[float]
    best_send_time: Optional[str]
    best_send_day: Optional[str]
    avg_followups_to_response: Optional[float]
    most_effective_sequence: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Dashboards ====================

class FollowUpDashboard(BaseModel):
    """Follow-up dashboard data"""

    # Overview
    pending_followups: int
    sent_today: int
    responses_today: int

    # Performance
    overall_response_rate: Optional[float]
    avg_response_time_hours: Optional[float]

    # Upcoming
    upcoming_followups: List[FollowUp]

    # Recent activity
    recent_sent: List[FollowUp]
    recent_responses: List[FollowUpResponse]

    # Best practices
    best_send_time: Optional[str]
    best_performing_template: Optional[FollowUpTemplate]
    best_performing_sequence: Optional[FollowUpSequence]


class ScheduleFollowUpRequest(BaseModel):
    """Request to schedule follow-up sequence"""
    job_id: int
    stage: str
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    recipient_title: Optional[str] = None
    sequence_name: Optional[str] = None  # Use specific sequence
    custom_data: Optional[Dict[str, Any]] = None  # Additional personalization


class ScheduleFollowUpResponse(BaseModel):
    """Response after scheduling"""
    success: bool
    followups_scheduled: int
    followup_ids: List[int]
    next_followup_date: Optional[datetime]
    message: str


class SendFollowUpRequest(BaseModel):
    """Request to send follow-up immediately"""
    followup_id: int
    override_schedule: bool = False


class SendFollowUpResponse(BaseModel):
    """Response after sending"""
    success: bool
    followup_id: int
    sent_date: datetime
    email_id: Optional[str]
    message: str


class TimingRecommendation(BaseModel):
    """Timing recommendation for follow-ups"""
    stage: str
    recommended_days_after: int
    recommended_time_of_day: str
    recommended_day_of_week: str
    confidence: float
    based_on_samples: int
    reasoning: str
