"""
Skills Gap Analysis Models

Track candidate skills, analyze gaps, and provide learning recommendations.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class SkillLevel(str, enum.Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(str, enum.Enum):
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


class GapSeverity(str, enum.Enum):
    """Severity of skill gap"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CandidateSkill(Base):
    """
    Candidate's current skills and proficiency
    """
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)

    # Skill details
    skill_name = Column(String, nullable=False, index=True)
    skill_category = Column(SQLEnum(SkillCategory), nullable=True)

    # Proficiency
    proficiency_level = Column(SQLEnum(SkillLevel), nullable=False)
    years_experience = Column(Float, nullable=True)  # Years of experience
    confidence_score = Column(Float, nullable=True)  # Self-assessed confidence 0-100

    # Evidence
    projects_used_in = Column(JSON, nullable=True)  # List of project names
    certifications = Column(JSON, nullable=True)  # List of certification names
    last_used_date = Column(DateTime, nullable=True)

    # Learning
    currently_learning = Column(Boolean, default=False)
    target_proficiency = Column(SQLEnum(SkillLevel), nullable=True)

    # Metadata
    added_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class JobSkillRequirement(Base):
    """
    Skills required for a specific job
    """
    __tablename__ = "job_skill_requirements"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Skill details
    skill_name = Column(String, nullable=False, index=True)
    skill_category = Column(SQLEnum(SkillCategory), nullable=True)

    # Requirements
    required_level = Column(SQLEnum(SkillLevel), nullable=False)
    is_required = Column(Boolean, default=True)  # Required vs nice-to-have
    years_required = Column(Float, nullable=True)

    # Importance
    importance_score = Column(Float, nullable=True)  # 0-100, how critical this skill is
    mentioned_count = Column(Integer, default=1)  # How many times mentioned in job posting

    # Metadata
    extracted_from = Column(String, nullable=True)  # Where this was extracted from
    confidence = Column(Float, nullable=True)  # AI confidence in extraction
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("Job", backref="skill_requirements")


class SkillGap(Base):
    """
    Identified gap between candidate skills and job requirements
    """
    __tablename__ = "skill_gaps"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Gap details
    skill_name = Column(String, nullable=False, index=True)
    skill_category = Column(SQLEnum(SkillCategory), nullable=True)

    # Current vs Required
    current_level = Column(SQLEnum(SkillLevel), nullable=True)  # None if skill not possessed
    required_level = Column(SQLEnum(SkillLevel), nullable=False)
    gap_severity = Column(String, nullable=False)  # critical, high, medium, low

    # Impact
    impact_on_application = Column(Float, nullable=False)  # 0-100, how much this affects chances
    is_dealbreaker = Column(Boolean, default=False)

    # Learning estimate
    estimated_learning_time_hours = Column(Integer, nullable=True)
    difficulty_level = Column(String, nullable=True)  # easy, moderate, challenging

    # Status
    is_acknowledged = Column(Boolean, default=False)
    is_learning = Column(Boolean, default=False)
    target_completion_date = Column(DateTime, nullable=True)

    # Metadata
    identified_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", backref="skill_gaps")


class LearningResource(Base):
    """
    Learning resources for skill development
    """
    __tablename__ = "learning_resources"

    id = Column(Integer, primary_key=True, index=True)

    # Resource details
    skill_name = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False)  # course, tutorial, book, documentation, project
    resource_title = Column(String, nullable=False)
    resource_url = Column(String, nullable=True)

    # Provider
    provider = Column(String, nullable=True)  # Udemy, Coursera, YouTube, etc.
    is_free = Column(Boolean, default=False)
    cost = Column(Float, nullable=True)

    # Details
    duration_hours = Column(Integer, nullable=True)
    difficulty_level = Column(String, nullable=True)  # beginner, intermediate, advanced
    target_proficiency = Column(SQLEnum(SkillLevel), nullable=True)

    # Quality indicators
    rating = Column(Float, nullable=True)  # 0-5
    review_count = Column(Integer, nullable=True)
    completion_rate = Column(Float, nullable=True)  # Percentage

    # Relevance
    relevance_score = Column(Float, nullable=True)  # How relevant to candidate's goals
    popularity_score = Column(Float, nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    prerequisites = Column(JSON, nullable=True)
    skills_covered = Column(JSON, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningPlan(Base):
    """
    Personalized learning plan for skill development
    """
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)  # Optional: targeted for specific job

    # Plan details
    plan_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_role = Column(String, nullable=True)

    # Skills to learn
    skills = Column(JSON, nullable=False)  # Array of {skill_name, current_level, target_level}

    # Timeline
    start_date = Column(DateTime, nullable=True)
    target_completion_date = Column(DateTime, nullable=True)
    estimated_hours_total = Column(Integer, nullable=True)
    estimated_hours_per_week = Column(Integer, nullable=True)

    # Progress
    current_progress = Column(Float, default=0.0)  # 0-100%
    skills_completed = Column(Integer, default=0)
    skills_in_progress = Column(Integer, default=0)
    skills_not_started = Column(Integer, default=0)

    # Status
    status = Column(String, default="draft")  # draft, active, completed, abandoned
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    job = relationship("Job", backref="learning_plans")


class SkillProgress(Base):
    """
    Track progress in learning specific skills
    """
    __tablename__ = "skill_progress"

    id = Column(Integer, primary_key=True, index=True)
    learning_plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=True)

    # Skill details
    skill_name = Column(String, nullable=False, index=True)
    starting_level = Column(SQLEnum(SkillLevel), nullable=True)
    target_level = Column(SQLEnum(SkillLevel), nullable=False)
    current_level = Column(SQLEnum(SkillLevel), nullable=True)

    # Progress
    progress_percentage = Column(Float, default=0.0)  # 0-100
    hours_invested = Column(Float, default=0.0)
    estimated_hours_remaining = Column(Integer, nullable=True)

    # Resources completed
    resources_completed = Column(JSON, nullable=True)  # Array of resource IDs
    resources_in_progress = Column(JSON, nullable=True)

    # Milestones
    milestones = Column(JSON, nullable=True)  # Array of {name, completed, date}
    last_activity_date = Column(DateTime, nullable=True)

    # Assessment
    self_assessment_score = Column(Float, nullable=True)  # 0-100
    assessment_notes = Column(Text, nullable=True)

    # Status
    status = Column(String, default="not_started")  # not_started, in_progress, completed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    learning_plan = relationship("LearningPlan", backref="skill_progress_items")


class SkillAssessment(Base):
    """
    Skill assessment results and history
    """
    __tablename__ = "skill_assessments"

    id = Column(Integer, primary_key=True, index=True)

    # Assessment details
    skill_name = Column(String, nullable=False, index=True)
    assessment_type = Column(String, nullable=False)  # self, quiz, project, interview, peer

    # Results
    score = Column(Float, nullable=False)  # 0-100
    assessed_level = Column(SQLEnum(SkillLevel), nullable=True)
    previous_level = Column(SQLEnum(SkillLevel), nullable=True)

    # Details
    assessment_notes = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)  # Array of strength areas
    weaknesses = Column(JSON, nullable=True)  # Array of areas to improve

    # Context
    assessment_source = Column(String, nullable=True)
    quiz_questions = Column(Integer, nullable=True)
    quiz_correct = Column(Integer, nullable=True)

    # Metadata
    assessment_date = Column(DateTime, default=datetime.utcnow)
    assessor = Column(String, nullable=True)


class SkillTrend(Base):
    """
    Track market trends for skills
    """
    __tablename__ = "skill_trends"

    id = Column(Integer, primary_key=True, index=True)

    # Skill details
    skill_name = Column(String, nullable=False, index=True)
    skill_category = Column(SQLEnum(SkillCategory), nullable=True)

    # Trend data
    demand_score = Column(Float, nullable=False)  # 0-100
    growth_rate = Column(Float, nullable=True)  # Percentage change
    job_postings_count = Column(Integer, nullable=True)

    # Salary data
    avg_salary_impact = Column(Float, nullable=True)  # Percentage increase
    salary_range_min = Column(Float, nullable=True)
    salary_range_max = Column(Float, nullable=True)

    # Market insights
    trending_direction = Column(String, nullable=True)  # rising, stable, declining
    hot_skill = Column(Boolean, default=False)  # Currently in high demand
    emerging_skill = Column(Boolean, default=False)  # New and growing

    # Related skills
    commonly_paired_with = Column(JSON, nullable=True)  # Skills often required together
    alternative_skills = Column(JSON, nullable=True)  # Similar/alternative skills

    # Industry data
    top_industries = Column(JSON, nullable=True)
    top_companies = Column(JSON, nullable=True)

    # Metadata
    data_date = Column(DateTime, nullable=False)
    data_source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SkillGapAnalysis(Base):
    """
    Complete skill gap analysis for a job application
    """
    __tablename__ = "skill_gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Overall analysis
    total_skills_required = Column(Integer, nullable=False)
    skills_matched = Column(Integer, nullable=False)
    skills_partial_match = Column(Integer, nullable=False)
    skills_missing = Column(Integer, nullable=False)

    # Match score
    overall_match_score = Column(Float, nullable=False)  # 0-100
    required_skills_score = Column(Float, nullable=False)
    nice_to_have_score = Column(Float, nullable=False)

    # Gap severity
    critical_gaps = Column(Integer, default=0)
    high_priority_gaps = Column(Integer, default=0)
    medium_priority_gaps = Column(Integer, default=0)
    low_priority_gaps = Column(Integer, default=0)

    # Learning estimate
    total_learning_hours = Column(Integer, nullable=True)
    estimated_ready_date = Column(DateTime, nullable=True)

    # Recommendations
    recommendation = Column(String, nullable=False)  # apply_now, learn_first, reconsider
    recommendation_reason = Column(Text, nullable=True)
    learning_priority = Column(JSON, nullable=True)  # Ordered list of skills to learn

    # Detailed analysis
    matched_skills = Column(JSON, nullable=True)
    partial_skills = Column(JSON, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    strength_areas = Column(JSON, nullable=True)
    improvement_areas = Column(JSON, nullable=True)

    # Metadata
    analysis_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", backref="skill_gap_analyses")
