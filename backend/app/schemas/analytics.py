"""
Analytics Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== Application Outcome ====================

class ApplicationOutcomeCreate(BaseModel):
    """Create application outcome record"""
    job_id: int
    outcome_type: str  # interview_success, offer_received, offer_accepted, rejected
    outcome_stage: str  # screening, interview, offer
    actual_success: bool
    rejection_reason: Optional[str] = None
    interview_count: int = 0
    days_to_outcome: Optional[int] = None
    feedback_notes: Optional[str] = None


class ApplicationOutcome(BaseModel):
    """Application outcome response"""
    id: int
    job_id: int
    outcome_type: str
    outcome_stage: str
    outcome_date: datetime
    predicted_match_score: Optional[float]
    predicted_should_apply: Optional[bool]
    actual_success: bool
    rejection_reason: Optional[str]
    interview_count: int
    days_to_outcome: Optional[int]
    feedback_notes: Optional[str]
    job_characteristics: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Prediction Accuracy ====================

class PredictionAccuracy(BaseModel):
    """Prediction accuracy metrics"""
    id: int
    period_start: datetime
    period_end: datetime
    total_predictions: int
    correct_predictions: int
    false_positives: int
    false_negatives: int
    accuracy_percentage: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    avg_predicted_score_success: Optional[float]
    avg_predicted_score_failure: Optional[float]
    score_correlation: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Success Pattern ====================

class SuccessPattern(BaseModel):
    """Success pattern response"""
    id: int
    pattern_type: str
    pattern_value: str
    applications_count: int
    success_count: int
    success_rate: Optional[float]
    confidence_score: Optional[float]
    sample_size_sufficient: bool
    insight_description: Optional[str]
    recommendation: Optional[str]
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Scoring Weight ====================

class ScoringWeightUpdate(BaseModel):
    """Update scoring weight"""
    new_weight: float = Field(..., ge=0.0, le=1.0)
    reason: str


class ScoringWeight(BaseModel):
    """Scoring weight response"""
    id: int
    weight_name: str
    weight_category: str
    current_weight: float
    initial_weight: float
    min_weight: float
    max_weight: float
    adjustment_count: int
    last_adjusted: Optional[datetime]
    adjustment_history: Optional[List[Dict[str, Any]]]
    correlation_with_success: Optional[float]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Analytics Insight ====================

class AnalyticsInsightCreate(BaseModel):
    """Create analytics insight"""
    insight_type: str
    title: str
    description: str
    priority: str = "medium"
    confidence_level: Optional[float] = None
    actionable: bool = False
    recommended_action: Optional[str] = None
    supporting_data: Optional[Dict[str, Any]] = None


class AnalyticsInsight(BaseModel):
    """Analytics insight response"""
    id: int
    insight_type: str
    title: str
    description: str
    priority: str
    confidence_level: Optional[float]
    actionable: bool
    recommended_action: Optional[str]
    supporting_data: Optional[Dict[str, Any]]
    is_active: bool
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    generated_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Learning Event ====================

class LearningEvent(BaseModel):
    """Learning event response"""
    id: int
    event_type: str
    description: str
    changes: Optional[Dict[str, Any]]
    reason: Optional[str]
    expected_impact: Optional[str]
    actual_impact: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Analytics Dashboard ====================

class AnalyticsDashboard(BaseModel):
    """Complete analytics dashboard data"""

    # Overall metrics
    total_applications: int
    total_outcomes_recorded: int

    # Success metrics
    overall_success_rate: Optional[float]
    interview_success_rate: Optional[float]
    offer_success_rate: Optional[float]

    # Prediction accuracy
    current_accuracy: Optional[PredictionAccuracy]
    accuracy_trend: List[float]  # Last N periods

    # Top patterns
    top_success_patterns: List[SuccessPattern]
    top_failure_patterns: List[SuccessPattern]

    # Recent insights
    active_insights: List[AnalyticsInsight]

    # Scoring weights
    current_weights: List[ScoringWeight]

    # Learning progress
    recent_learning_events: List[LearningEvent]
    learning_enabled: bool


class LearningStats(BaseModel):
    """Learning system statistics"""
    total_outcomes_learned_from: int
    total_adjustments_made: int
    current_accuracy: Optional[float]
    accuracy_improvement: Optional[float]  # Compared to baseline
    patterns_discovered: int
    insights_generated: int
    last_learning_run: Optional[datetime]
    learning_status: str  # active, paused, insufficient_data


class ImprovementSuggestion(BaseModel):
    """Suggestion for improving application strategy"""
    suggestion_type: str  # focus_area, avoid_pattern, timing, approach
    title: str
    description: str
    expected_impact: str  # high, medium, low
    supporting_evidence: List[str]
    action_steps: List[str]
    priority: int = Field(..., ge=1, le=10)


class AnalyticsReport(BaseModel):
    """Comprehensive analytics report"""
    report_period: str
    period_start: datetime
    period_end: datetime

    # Summary
    summary: Dict[str, Any]

    # Key insights
    key_insights: List[str]

    # Success analysis
    success_analysis: Dict[str, Any]

    # Failure analysis
    failure_analysis: Dict[str, Any]

    # Recommendations
    recommendations: List[ImprovementSuggestion]

    # Trends
    trends: Dict[str, List[float]]

    generated_at: datetime
