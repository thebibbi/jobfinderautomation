"""
Job Recommendations Models

ML-based job recommendation system.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class UserPreference(Base):
    """
    User preferences learned from behavior
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)

    # Preference category
    preference_type = Column(String, nullable=False)  # company_size, industry, remote, etc.
    preference_value = Column(String, nullable=False)

    # Strength
    preference_score = Column(Float, default=0.5)  # 0-1, how strong this preference is
    confidence = Column(Float, default=0.5)  # How confident we are in this preference

    # Learning
    learned_from = Column(String, nullable=False)  # applications, outcomes, explicit, clicks
    sample_size = Column(Integer, default=1)  # How many data points support this

    # Metadata
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class JobRecommendation(Base):
    """
    Individual job recommendation
    """
    __tablename__ = "job_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Recommendation score
    recommendation_score = Column(Float, nullable=False)  # 0-100
    confidence = Column(Float, nullable=False)  # 0-1

    # Reasoning
    recommendation_reasons = Column(JSON, nullable=True)  # Why this job was recommended
    match_factors = Column(JSON, nullable=True)  # What factors contributed

    # Status
    status = Column(String, default="pending")  # pending, viewed, clicked, applied, dismissed
    viewed_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    dismissal_reason = Column(String, nullable=True)

    # Feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 if user rates it
    was_applied = Column(Boolean, default=False)

    # Metadata
    recommended_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Recommendations can expire

    # Relationships
    job = relationship("Job", backref="recommendations")


class RecommendationFeedback(Base):
    """
    User feedback on recommendations
    """
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("job_recommendations.id"), nullable=False)

    # Feedback type
    feedback_type = Column(String, nullable=False)  # helpful, not_helpful, wrong_skills, etc.
    feedback_text = Column(Text, nullable=True)

    # Rating
    rating = Column(Integer, nullable=True)  # 1-5

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recommendation = relationship("JobRecommendation", backref="feedback")


class RecommendationDigest(Base):
    """
    Daily/weekly digest of recommendations
    """
    __tablename__ = "recommendation_digests"

    id = Column(Integer, primary_key=True, index=True)

    # Digest details
    digest_type = Column(String, nullable=False)  # daily, weekly
    digest_date = Column(DateTime, nullable=False)

    # Content
    job_ids = Column(JSON, nullable=False)  # Array of recommended job IDs
    total_recommendations = Column(Integer, nullable=False)
    top_recommendation_id = Column(Integer, nullable=True)

    # Highlights
    highlights = Column(JSON, nullable=True)  # Key highlights of the digest
    new_opportunities = Column(Integer, default=0)  # New since last digest

    # Delivery
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class SimilarJob(Base):
    """
    Similar job mapping for recommendations
    """
    __tablename__ = "similar_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    similar_job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Similarity
    similarity_score = Column(Float, nullable=False)  # 0-1
    similarity_factors = Column(JSON, nullable=True)  # What makes them similar

    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("Job", foreign_keys=[job_id])
    similar_job = relationship("Job", foreign_keys=[similar_job_id])


class RecommendationModel(Base):
    """
    ML model metadata and versioning
    """
    __tablename__ = "recommendation_models"

    id = Column(Integer, primary_key=True, index=True)

    # Model details
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # collaborative_filtering, content_based, hybrid

    # Performance
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    ndcg_score = Column(Float, nullable=True)  # Normalized Discounted Cumulative Gain

    # Training
    trained_on_samples = Column(Integer, nullable=False)
    training_date = Column(DateTime, nullable=False)

    # Status
    is_active = Column(Boolean, default=False)
    is_production = Column(Boolean, default=False)

    # Metadata
    hyperparameters = Column(JSON, nullable=True)
    feature_importance = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class RecommendationMetrics(Base):
    """
    Track recommendation system performance
    """
    __tablename__ = "recommendation_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Metrics
    total_recommendations = Column(Integer, default=0)
    recommendations_viewed = Column(Integer, default=0)
    recommendations_clicked = Column(Integer, default=0)
    recommendations_applied = Column(Integer, default=0)
    recommendations_dismissed = Column(Integer, default=0)

    # Rates
    click_through_rate = Column(Float, nullable=True)
    application_rate = Column(Float, nullable=True)
    dismissal_rate = Column(Float, nullable=True)

    # Quality
    avg_recommendation_score = Column(Float, nullable=True)
    avg_user_rating = Column(Float, nullable=True)

    # Diversity
    unique_companies = Column(Integer, nullable=True)
    unique_industries = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
