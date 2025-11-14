"""
Company Research Models

Stores automated company research data.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class CompanyProfile(Base):
    """
    Company profile with aggregated research data
    """
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # Company identification
    company_name = Column(String, unique=True, nullable=False, index=True)
    domain = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    company_size = Column(String, nullable=True)  # startup, small, medium, large, enterprise

    # Location
    headquarters = Column(String, nullable=True)
    locations = Column(JSON, nullable=True)  # Array of locations

    # Overview
    description = Column(Text, nullable=True)
    founded_year = Column(Integer, nullable=True)
    company_type = Column(String, nullable=True)  # public, private, nonprofit

    # Ratings & Reviews
    glassdoor_rating = Column(Float, nullable=True)
    glassdoor_review_count = Column(Integer, nullable=True)
    indeed_rating = Column(Float, nullable=True)
    indeed_review_count = Column(Integer, nullable=True)

    # Financials
    funding_total = Column(Float, nullable=True)
    funding_stage = Column(String, nullable=True)  # seed, series_a, series_b, etc.
    valuation = Column(Float, nullable=True)
    revenue_range = Column(String, nullable=True)

    # Culture indicators
    benefits = Column(JSON, nullable=True)
    remote_policy = Column(String, nullable=True)
    work_life_balance_rating = Column(Float, nullable=True)
    culture_values_rating = Column(Float, nullable=True)

    # Technology stack
    tech_stack = Column(JSON, nullable=True)  # Array of technologies
    tech_stack_detected_from = Column(String, nullable=True)

    # Social & Web presence
    website = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    twitter_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)

    # Employee data
    employee_count = Column(Integer, nullable=True)
    employee_growth_rate = Column(Float, nullable=True)  # Percentage
    hiring_status = Column(String, nullable=True)  # actively_hiring, stable, layoffs

    # Research metadata
    last_researched = Column(DateTime, nullable=True)
    research_completeness = Column(Float, nullable=True)  # 0-100%
    data_sources = Column(JSON, nullable=True)  # Which APIs/sources were used

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    news = relationship("CompanyNews", back_populates="company", cascade="all, delete-orphan")
    research_logs = relationship("ResearchLog", back_populates="company", cascade="all, delete-orphan")


class CompanyNews(Base):
    """
    Recent company news articles
    """
    __tablename__ = "company_news"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_profiles.id"), nullable=False)

    # Article details
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    source = Column(String, nullable=True)
    published_date = Column(DateTime, nullable=True)

    # Categorization
    category = Column(String, nullable=True)  # funding, product, hiring, etc.
    sentiment = Column(String, nullable=True)  # positive, negative, neutral
    relevance_score = Column(Float, nullable=True)  # How relevant to job search

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("CompanyProfile", back_populates="news")


class ResearchLog(Base):
    """
    Log of research activities and API calls
    """
    __tablename__ = "research_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_profiles.id"), nullable=False)

    # Research details
    research_type = Column(String, nullable=False)  # profile, news, ratings, tech_stack
    data_source = Column(String, nullable=False)  # rapidapi, crunchbase, clearbit, etc.

    # Result
    success = Column(Boolean, default=True)
    data_retrieved = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)

    # API usage
    api_endpoint = Column(String, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)  # If applicable

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("CompanyProfile", back_populates="research_logs")


class CompanyInsight(Base):
    """
    Generated insights about company for job application
    """
    __tablename__ = "company_insights"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_profiles.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)

    # Insight details
    insight_type = Column(String, nullable=False)  # talking_point, concern, opportunity
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    # Relevance
    relevance_score = Column(Float, nullable=True)  # How relevant to candidate
    confidence = Column(Float, nullable=True)  # Confidence in insight

    # Application strategy
    how_to_use = Column(Text, nullable=True)  # How to use this in application/interview
    suggested_talking_point = Column(Text, nullable=True)

    # Supporting data
    supporting_data = Column(JSON, nullable=True)
    sources = Column(JSON, nullable=True)  # URLs or references

    # Metadata
    generated_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    company = relationship("CompanyProfile", foreign_keys=[company_id])
    job = relationship("Job", foreign_keys=[job_id])


class TechStackMatch(Base):
    """
    Match between candidate skills and company tech stack
    """
    __tablename__ = "tech_stack_matches"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_profiles.id"), nullable=False)

    # Technology
    technology = Column(String, nullable=False)
    category = Column(String, nullable=True)  # language, framework, database, etc.

    # Match details
    candidate_has_experience = Column(Boolean, default=False)
    candidate_proficiency = Column(String, nullable=True)  # beginner, intermediate, expert
    years_experience = Column(Float, nullable=True)

    # Company usage
    importance_to_company = Column(String, nullable=True)  # core, supporting, experimental
    detected_from = Column(String, nullable=True)  # job_posting, github, stackshare

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("CompanyProfile", foreign_keys=[company_id])


class CompanyComparison(Base):
    """
    Comparison between multiple companies
    """
    __tablename__ = "company_comparisons"

    id = Column(Integer, primary_key=True, index=True)

    # Comparison details
    comparison_name = Column(String, nullable=False)
    company_ids = Column(JSON, nullable=False)  # Array of company IDs being compared

    # Comparison dimensions
    comparison_criteria = Column(JSON, nullable=False)  # What's being compared
    comparison_results = Column(JSON, nullable=True)  # Results by dimension

    # Winner/Recommendation
    recommended_company_id = Column(Integer, nullable=True)
    recommendation_reason = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
