"""
Analytics and Learning Models

Tracks application outcomes and learns from success/failure patterns.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class ApplicationOutcome(Base):
    """
    Track final outcomes of applications for learning
    """
    __tablename__ = "application_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Outcome tracking
    outcome_type = Column(String, nullable=False)  # interview_success, offer_received, offer_accepted, rejected
    outcome_stage = Column(String, nullable=False)  # screening, interview, offer
    outcome_date = Column(DateTime, default=datetime.utcnow)

    # Original prediction
    predicted_match_score = Column(Float, nullable=True)
    predicted_should_apply = Column(Boolean, nullable=True)

    # Actual result
    actual_success = Column(Boolean, nullable=False)

    # Details
    rejection_reason = Column(String, nullable=True)  # not_qualified, other_candidate, company_decision, etc.
    interview_count = Column(Integer, default=0)
    days_to_outcome = Column(Integer, nullable=True)  # Days from application to outcome

    # Feedback
    feedback_notes = Column(Text, nullable=True)

    # Job characteristics for pattern analysis
    job_characteristics = Column(JSON, nullable=True)  # Snapshot of job features at time of application

    # Relationships
    job = relationship("Job", backref="outcomes")

    created_at = Column(DateTime, default=datetime.utcnow)


class PredictionAccuracy(Base):
    """
    Track prediction accuracy over time
    """
    __tablename__ = "prediction_accuracy"

    id = Column(Integer, primary_key=True, index=True)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Accuracy metrics
    total_predictions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)  # Predicted success, actual failure
    false_negatives = Column(Integer, default=0)  # Predicted failure, actual success

    accuracy_percentage = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)  # Of predicted successes, how many were correct
    recall = Column(Float, nullable=True)  # Of actual successes, how many did we predict

    # Score analysis
    avg_predicted_score_success = Column(Float, nullable=True)
    avg_predicted_score_failure = Column(Float, nullable=True)
    score_correlation = Column(Float, nullable=True)  # Correlation between score and success

    created_at = Column(DateTime, default=datetime.utcnow)


class SuccessPattern(Base):
    """
    Identified patterns in successful applications
    """
    __tablename__ = "success_patterns"

    id = Column(Integer, primary_key=True, index=True)

    # Pattern identification
    pattern_type = Column(String, nullable=False)  # company_size, industry, remote_policy, etc.
    pattern_value = Column(String, nullable=False)

    # Success metrics
    applications_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)

    # Statistical significance
    confidence_score = Column(Float, nullable=True)
    sample_size_sufficient = Column(Boolean, default=False)

    # Insights
    insight_description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)

    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScoringWeight(Base):
    """
    Adjustable weights for scoring algorithm
    """
    __tablename__ = "scoring_weights"

    id = Column(Integer, primary_key=True, index=True)

    # Weight identification
    weight_name = Column(String, unique=True, nullable=False)  # skills_match, experience_match, etc.
    weight_category = Column(String, nullable=False)  # technical, cultural, experience, etc.

    # Weight values
    current_weight = Column(Float, nullable=False)
    initial_weight = Column(Float, nullable=False)
    min_weight = Column(Float, default=0.0)
    max_weight = Column(Float, default=1.0)

    # Learning metrics
    adjustment_count = Column(Integer, default=0)
    last_adjusted = Column(DateTime, nullable=True)
    adjustment_history = Column(JSON, nullable=True)  # History of weight changes

    # Performance
    correlation_with_success = Column(Float, nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalyticsInsight(Base):
    """
    Generated insights from analytics
    """
    __tablename__ = "analytics_insights"

    id = Column(Integer, primary_key=True, index=True)

    # Insight details
    insight_type = Column(String, nullable=False)  # success_pattern, improvement_area, trend, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    # Importance
    priority = Column(String, default="medium")  # high, medium, low
    confidence_level = Column(Float, nullable=True)  # 0-100

    # Action
    actionable = Column(Boolean, default=False)
    recommended_action = Column(Text, nullable=True)

    # Supporting data
    supporting_data = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)

    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class LearningEvent(Base):
    """
    Track learning algorithm adjustments
    """
    __tablename__ = "learning_events"

    id = Column(Integer, primary_key=True, index=True)

    # Event details
    event_type = Column(String, nullable=False)  # weight_adjustment, pattern_discovered, threshold_changed
    description = Column(Text, nullable=False)

    # Changes made
    changes = Column(JSON, nullable=True)  # What was changed
    reason = Column(Text, nullable=True)  # Why it was changed

    # Impact metrics (if available)
    expected_impact = Column(String, nullable=True)
    actual_impact = Column(Float, nullable=True)  # Measured after sufficient time

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
