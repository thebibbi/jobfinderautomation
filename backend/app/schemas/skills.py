"""
Skills Gap Analysis Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class SkillLevel(str, Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(str, Enum):
    """Skill categories"""
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    DEVOPS = "devops"
    SOFT_SKILL = "soft_skill"
    TOOL = "tool"
    METHODOLOGY = "methodology"
    OTHER = "other"


class GapSeverity(str, Enum):
    """Severity of skill gap"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ==================== Candidate Skills ====================

class CandidateSkillBase(BaseModel):
    """Base candidate skill"""
    skill_name: str
    skill_category: Optional[SkillCategory] = None
    proficiency_level: SkillLevel
    years_experience: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=100)


class CandidateSkillCreate(CandidateSkillBase):
    """Create candidate skill"""
    projects_used_in: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    last_used_date: Optional[datetime] = None
    currently_learning: bool = False
    target_proficiency: Optional[SkillLevel] = None


class CandidateSkillUpdate(BaseModel):
    """Update candidate skill"""
    proficiency_level: Optional[SkillLevel] = None
    years_experience: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=100)
    projects_used_in: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    last_used_date: Optional[datetime] = None
    currently_learning: Optional[bool] = None
    target_proficiency: Optional[SkillLevel] = None


class CandidateSkill(CandidateSkillBase):
    """Candidate skill response"""
    id: int
    projects_used_in: Optional[List[str]]
    certifications: Optional[List[str]]
    last_used_date: Optional[datetime]
    currently_learning: bool
    target_proficiency: Optional[SkillLevel]
    added_date: datetime
    last_updated: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ==================== Job Skill Requirements ====================

class JobSkillRequirementBase(BaseModel):
    """Base job skill requirement"""
    skill_name: str
    skill_category: Optional[SkillCategory] = None
    required_level: SkillLevel
    is_required: bool = True


class JobSkillRequirementCreate(JobSkillRequirementBase):
    """Create job skill requirement"""
    job_id: int
    years_required: Optional[float] = None
    importance_score: Optional[float] = Field(None, ge=0, le=100)
    mentioned_count: int = 1
    extracted_from: Optional[str] = None
    confidence: Optional[float] = None


class JobSkillRequirement(JobSkillRequirementBase):
    """Job skill requirement response"""
    id: int
    job_id: int
    years_required: Optional[float]
    importance_score: Optional[float]
    mentioned_count: int
    extracted_from: Optional[str]
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Skill Gaps ====================

class SkillGapBase(BaseModel):
    """Base skill gap"""
    skill_name: str
    skill_category: Optional[SkillCategory] = None
    current_level: Optional[SkillLevel] = None
    required_level: SkillLevel
    gap_severity: GapSeverity


class SkillGapCreate(SkillGapBase):
    """Create skill gap"""
    job_id: int
    impact_on_application: float = Field(ge=0, le=100)
    is_dealbreaker: bool = False
    estimated_learning_time_hours: Optional[int] = None
    difficulty_level: Optional[str] = None


class SkillGap(SkillGapBase):
    """Skill gap response"""
    id: int
    job_id: int
    impact_on_application: float
    is_dealbreaker: bool
    estimated_learning_time_hours: Optional[int]
    difficulty_level: Optional[str]
    is_acknowledged: bool
    is_learning: bool
    target_completion_date: Optional[datetime]
    identified_date: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ==================== Learning Resources ====================

class LearningResourceBase(BaseModel):
    """Base learning resource"""
    skill_name: str
    resource_type: str
    resource_title: str
    resource_url: Optional[str] = None


class LearningResourceCreate(LearningResourceBase):
    """Create learning resource"""
    provider: Optional[str] = None
    is_free: bool = False
    cost: Optional[float] = None
    duration_hours: Optional[int] = None
    difficulty_level: Optional[str] = None
    target_proficiency: Optional[SkillLevel] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = None
    description: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    skills_covered: Optional[List[str]] = None


class LearningResource(LearningResourceBase):
    """Learning resource response"""
    id: int
    provider: Optional[str]
    is_free: bool
    cost: Optional[float]
    duration_hours: Optional[int]
    difficulty_level: Optional[str]
    target_proficiency: Optional[SkillLevel]
    rating: Optional[float]
    review_count: Optional[int]
    completion_rate: Optional[float]
    relevance_score: Optional[float]
    popularity_score: Optional[float]
    description: Optional[str]
    prerequisites: Optional[List[str]]
    skills_covered: Optional[List[str]]
    last_updated: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Learning Plans ====================

class SkillToLearn(BaseModel):
    """Skill in learning plan"""
    skill_name: str
    current_level: Optional[SkillLevel] = None
    target_level: SkillLevel
    priority: int = 1
    estimated_hours: Optional[int] = None


class LearningPlanBase(BaseModel):
    """Base learning plan"""
    plan_name: str
    description: Optional[str] = None
    target_role: Optional[str] = None


class LearningPlanCreate(LearningPlanBase):
    """Create learning plan"""
    job_id: Optional[int] = None
    skills: List[SkillToLearn]
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    estimated_hours_per_week: Optional[int] = None


class LearningPlan(LearningPlanBase):
    """Learning plan response"""
    id: int
    job_id: Optional[int]
    skills: List[Dict[str, Any]]
    start_date: Optional[datetime]
    target_completion_date: Optional[datetime]
    estimated_hours_total: Optional[int]
    estimated_hours_per_week: Optional[int]
    current_progress: float
    skills_completed: int
    skills_in_progress: int
    skills_not_started: int
    status: str
    is_active: bool
    created_at: datetime
    last_updated: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Skill Progress ====================

class SkillProgressBase(BaseModel):
    """Base skill progress"""
    skill_name: str
    target_level: SkillLevel


class SkillProgressCreate(SkillProgressBase):
    """Create skill progress"""
    learning_plan_id: Optional[int] = None
    starting_level: Optional[SkillLevel] = None
    estimated_hours_remaining: Optional[int] = None


class SkillProgressUpdate(BaseModel):
    """Update skill progress"""
    current_level: Optional[SkillLevel] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    hours_invested: Optional[float] = None
    resources_completed: Optional[List[int]] = None
    self_assessment_score: Optional[float] = Field(None, ge=0, le=100)
    assessment_notes: Optional[str] = None


class SkillProgress(SkillProgressBase):
    """Skill progress response"""
    id: int
    learning_plan_id: Optional[int]
    starting_level: Optional[SkillLevel]
    current_level: Optional[SkillLevel]
    progress_percentage: float
    hours_invested: float
    estimated_hours_remaining: Optional[int]
    resources_completed: Optional[List[int]]
    resources_in_progress: Optional[List[int]]
    milestones: Optional[List[Dict[str, Any]]]
    last_activity_date: Optional[datetime]
    self_assessment_score: Optional[float]
    assessment_notes: Optional[str]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ==================== Skill Assessment ====================

class SkillAssessmentCreate(BaseModel):
    """Create skill assessment"""
    skill_name: str
    assessment_type: str
    score: float = Field(ge=0, le=100)
    assessed_level: Optional[SkillLevel] = None
    assessment_notes: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    assessment_source: Optional[str] = None


class SkillAssessment(BaseModel):
    """Skill assessment response"""
    id: int
    skill_name: str
    assessment_type: str
    score: float
    assessed_level: Optional[SkillLevel]
    previous_level: Optional[SkillLevel]
    assessment_notes: Optional[str]
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    assessment_source: Optional[str]
    quiz_questions: Optional[int]
    quiz_correct: Optional[int]
    assessment_date: datetime
    assessor: Optional[str]

    class Config:
        from_attributes = True


# ==================== Skill Trends ====================

class SkillTrend(BaseModel):
    """Skill trend response"""
    id: int
    skill_name: str
    skill_category: Optional[SkillCategory]
    demand_score: float
    growth_rate: Optional[float]
    job_postings_count: Optional[int]
    avg_salary_impact: Optional[float]
    salary_range_min: Optional[float]
    salary_range_max: Optional[float]
    trending_direction: Optional[str]
    hot_skill: bool
    emerging_skill: bool
    commonly_paired_with: Optional[List[str]]
    alternative_skills: Optional[List[str]]
    top_industries: Optional[List[str]]
    top_companies: Optional[List[str]]
    data_date: datetime
    data_source: Optional[str]

    class Config:
        from_attributes = True


# ==================== Skill Gap Analysis ====================

class SkillGapAnalysisRequest(BaseModel):
    """Request for skill gap analysis"""
    job_id: int
    include_learning_recommendations: bool = True
    include_resource_suggestions: bool = True


class MatchedSkillDetail(BaseModel):
    """Details of a matched skill"""
    skill_name: str
    required_level: SkillLevel
    candidate_level: SkillLevel
    match_quality: str  # perfect, exceeds, meets
    years_required: Optional[float]
    candidate_years: Optional[float]


class GapSkillDetail(BaseModel):
    """Details of a skill gap"""
    skill_name: str
    required_level: SkillLevel
    candidate_level: Optional[SkillLevel]
    gap_severity: GapSeverity
    is_required: bool
    is_dealbreaker: bool
    learning_time_hours: Optional[int]
    difficulty: Optional[str]
    resources: List[LearningResource] = []


class SkillGapAnalysisResult(BaseModel):
    """Complete skill gap analysis result"""
    job_id: int
    job_title: str
    company: str

    # Overall metrics
    total_skills_required: int
    skills_matched: int
    skills_partial_match: int
    skills_missing: int
    overall_match_score: float
    required_skills_score: float
    nice_to_have_score: float

    # Gap counts by severity
    critical_gaps: int
    high_priority_gaps: int
    medium_priority_gaps: int
    low_priority_gaps: int

    # Details
    matched_skills: List[MatchedSkillDetail]
    partial_skills: List[GapSkillDetail]
    missing_skills: List[GapSkillDetail]

    # Recommendations
    recommendation: str  # apply_now, learn_first, reconsider
    recommendation_reason: str
    learning_priority: List[str]
    total_learning_hours: Optional[int]
    estimated_ready_date: Optional[datetime]

    # Strengths and improvements
    strength_areas: List[str]
    improvement_areas: List[str]

    # Analysis metadata
    analysis_date: datetime


class SkillGapSummary(BaseModel):
    """Summary of skill gap analysis"""
    job_id: int
    overall_match_score: float
    skills_matched: int
    skills_missing: int
    critical_gaps: int
    recommendation: str
    top_3_gaps: List[str]


# ==================== Skill Profile ====================

class SkillProfile(BaseModel):
    """Complete skill profile for candidate"""
    total_skills: int
    skills_by_category: Dict[str, int]
    skills_by_level: Dict[str, int]
    top_skills: List[CandidateSkill]
    currently_learning: List[CandidateSkill]
    certifications: List[str]
    avg_confidence: float
    profile_completeness: float


# ==================== Learning Dashboard ====================

class LearningDashboard(BaseModel):
    """Learning progress dashboard"""
    active_plans: List[LearningPlan]
    total_hours_invested: float
    skills_in_progress: int
    skills_completed: int
    current_week_hours: float
    overall_progress: float
    recent_achievements: List[Dict[str, Any]]
    upcoming_milestones: List[Dict[str, Any]]


# ==================== Resource Recommendations ====================

class ResourceRecommendationRequest(BaseModel):
    """Request for resource recommendations"""
    skill_name: str
    current_level: Optional[SkillLevel] = None
    target_level: SkillLevel
    max_cost: Optional[float] = None
    preferred_duration_hours: Optional[int] = None
    only_free: bool = False


class ResourceRecommendations(BaseModel):
    """Resource recommendations response"""
    skill_name: str
    recommended_resources: List[LearningResource]
    total_estimated_hours: int
    total_cost: float
    free_options_count: int
    learning_path: List[str]  # Ordered list of resource names
