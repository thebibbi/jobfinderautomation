"""
Job Recommendations Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== User Preferences ====================

class UserPreferenceBase(BaseModel):
    """Base user preference"""
    preference_type: str
    preference_value: str
    preference_score: float = Field(ge=0.0, le=1.0)


class UserPreferenceCreate(UserPreferenceBase):
    """Create user preference"""
    learned_from: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class UserPreference(UserPreferenceBase):
    """User preference response"""
    id: int
    confidence: float
    learned_from: str
    sample_size: int
    is_active: bool
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Job Recommendations ====================

class JobRecommendationBase(BaseModel):
    """Base recommendation"""
    job_id: int
    recommendation_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)


class JobRecommendationCreate(JobRecommendationBase):
    """Create recommendation"""
    recommendation_reasons: Optional[Dict[str, Any]] = None
    match_factors: Optional[Dict[str, Any]] = None


class JobRecommendation(JobRecommendationBase):
    """Recommendation response"""
    id: int
    recommendation_reasons: Optional[Dict[str, Any]]
    match_factors: Optional[Dict[str, Any]]
    status: str
    viewed_at: Optional[datetime]
    clicked_at: Optional[datetime]
    dismissed_at: Optional[datetime]
    dismissal_reason: Optional[str]
    user_rating: Optional[int]
    was_applied: bool
    recommended_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobRecommendationWithDetails(JobRecommendation):
    """Recommendation with job details"""
    job_title: str
    company: str
    location: Optional[str]
    salary_range: Optional[str]
    job_url: Optional[str]


# ==================== Recommendation Feedback ====================

class RecommendationFeedbackBase(BaseModel):
    """Base feedback"""
    feedback_type: str
    feedback_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class RecommendationFeedbackCreate(RecommendationFeedbackBase):
    """Create feedback"""
    recommendation_id: int


class RecommendationFeedback(RecommendationFeedbackBase):
    """Feedback response"""
    id: int
    recommendation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Recommendation Request ====================

class RecommendationRequest(BaseModel):
    """Request for recommendations"""
    limit: int = Field(default=10, ge=1, le=50)
    algorithm: str = Field(default="hybrid")  # collaborative, content_based, hybrid
    include_reasons: bool = True
    filter_applied: bool = False  # Filter out already applied jobs
    min_score: float = Field(default=60.0, ge=0.0, le=100.0)


class RecommendationResponse(BaseModel):
    """Recommendation response"""
    recommendations: List[JobRecommendationWithDetails]
    total_available: int
    algorithm_used: str
    generated_at: datetime
    preferences_learned: int


# ==================== Recommendation Digest ====================

class DigestBase(BaseModel):
    """Base digest"""
    digest_type: str  # daily, weekly
    digest_date: datetime


class DigestCreate(DigestBase):
    """Create digest"""
    job_ids: List[int]
    total_recommendations: int
    top_recommendation_id: Optional[int] = None
    highlights: Optional[Dict[str, Any]] = None
    new_opportunities: int = 0


class RecommendationDigest(DigestBase):
    """Digest response"""
    id: int
    job_ids: List[int]
    total_recommendations: int
    top_recommendation_id: Optional[int]
    highlights: Optional[Dict[str, Any]]
    new_opportunities: int
    sent: bool
    sent_at: Optional[datetime]
    opened: bool
    opened_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DigestWithJobs(RecommendationDigest):
    """Digest with full job details"""
    jobs: List[JobRecommendationWithDetails]


# ==================== Similar Jobs ====================

class SimilarJobBase(BaseModel):
    """Base similar job"""
    job_id: int
    similar_job_id: int
    similarity_score: float = Field(ge=0.0, le=1.0)


class SimilarJobCreate(SimilarJobBase):
    """Create similar job"""
    similarity_factors: Optional[Dict[str, Any]] = None


class SimilarJob(SimilarJobBase):
    """Similar job response"""
    id: int
    similarity_factors: Optional[Dict[str, Any]]
    calculated_at: datetime

    class Config:
        from_attributes = True


class SimilarJobWithDetails(SimilarJob):
    """Similar job with details"""
    similar_job_title: str
    similar_job_company: str
    similar_job_location: Optional[str]


# ==================== Recommendation Model ====================

class RecommendationModelBase(BaseModel):
    """Base model metadata"""
    model_name: str
    model_version: str
    model_type: str


class RecommendationModelCreate(RecommendationModelBase):
    """Create model"""
    trained_on_samples: int
    training_date: datetime
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    ndcg_score: Optional[float] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_importance: Optional[Dict[str, Any]] = None


class RecommendationModel(RecommendationModelBase):
    """Model response"""
    id: int
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    ndcg_score: Optional[float]
    trained_on_samples: int
    training_date: datetime
    is_active: bool
    is_production: bool
    hyperparameters: Optional[Dict[str, Any]]
    feature_importance: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Recommendation Metrics ====================

class RecommendationMetrics(BaseModel):
    """Metrics response"""
    id: int
    period_start: datetime
    period_end: datetime
    total_recommendations: int
    recommendations_viewed: int
    recommendations_clicked: int
    recommendations_applied: int
    recommendations_dismissed: int
    click_through_rate: Optional[float]
    application_rate: Optional[float]
    dismissal_rate: Optional[float]
    avg_recommendation_score: Optional[float]
    avg_user_rating: Optional[float]
    unique_companies: Optional[int]
    unique_industries: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Dashboard ====================

class RecommendationDashboard(BaseModel):
    """Dashboard data"""
    active_recommendations: int
    pending_recommendations: int
    viewed_recommendations: int
    applied_recommendations: int
    dismissed_recommendations: int

    # Performance
    avg_recommendation_score: float
    avg_user_rating: Optional[float]
    click_through_rate: float
    application_rate: float

    # Top recommendations
    top_recommendations: List[JobRecommendationWithDetails]

    # Recent activity
    recent_feedback_count: int
    preferences_learned: int

    # Model info
    active_model: Optional[RecommendationModel]


# ==================== Preference Update ====================

class PreferenceUpdate(BaseModel):
    """Update user preferences"""
    preference_type: str
    preference_value: str
    action: str  # increase, decrease, set
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
