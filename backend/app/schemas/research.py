"""
Company Research Schemas
"""
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== Company Profile ====================

class CompanyProfileBase(BaseModel):
    """Base company profile data"""
    company_name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None


class CompanyProfileCreate(CompanyProfileBase):
    """Create company profile"""
    pass


class CompanyProfile(CompanyProfileBase):
    """Company profile response"""
    id: int
    headquarters: Optional[str]
    locations: Optional[List[str]]
    description: Optional[str]
    founded_year: Optional[int]
    company_type: Optional[str]
    glassdoor_rating: Optional[float]
    glassdoor_review_count: Optional[int]
    indeed_rating: Optional[float]
    indeed_review_count: Optional[int]
    funding_total: Optional[float]
    funding_stage: Optional[str]
    valuation: Optional[float]
    revenue_range: Optional[str]
    benefits: Optional[List[str]]
    remote_policy: Optional[str]
    work_life_balance_rating: Optional[float]
    culture_values_rating: Optional[float]
    tech_stack: Optional[List[str]]
    tech_stack_detected_from: Optional[str]
    website: Optional[str]
    linkedin_url: Optional[str]
    twitter_url: Optional[str]
    github_url: Optional[str]
    employee_count: Optional[int]
    employee_growth_rate: Optional[float]
    hiring_status: Optional[str]
    last_researched: Optional[datetime]
    research_completeness: Optional[float]
    data_sources: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Company News ====================

class CompanyNewsBase(BaseModel):
    """Base news data"""
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None


class CompanyNewsCreate(CompanyNewsBase):
    """Create news entry"""
    company_id: int
    published_date: Optional[datetime] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None
    relevance_score: Optional[float] = None


class CompanyNews(CompanyNewsBase):
    """News response"""
    id: int
    company_id: int
    published_date: Optional[datetime]
    category: Optional[str]
    sentiment: Optional[str]
    relevance_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Research Log ====================

class ResearchLog(BaseModel):
    """Research log response"""
    id: int
    company_id: int
    research_type: str
    data_source: str
    success: bool
    data_retrieved: Optional[Dict[str, Any]]
    error_message: Optional[str]
    api_endpoint: Optional[str]
    response_time_ms: Optional[int]
    cost: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Company Insight ====================

class CompanyInsightCreate(BaseModel):
    """Create insight"""
    company_id: int
    job_id: Optional[int] = None
    insight_type: str
    title: str
    description: str
    relevance_score: Optional[float] = None
    confidence: Optional[float] = None
    how_to_use: Optional[str] = None
    suggested_talking_point: Optional[str] = None
    supporting_data: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None


class CompanyInsight(BaseModel):
    """Insight response"""
    id: int
    company_id: int
    job_id: Optional[int]
    insight_type: str
    title: str
    description: str
    relevance_score: Optional[float]
    confidence: Optional[float]
    how_to_use: Optional[str]
    suggested_talking_point: Optional[str]
    supporting_data: Optional[Dict[str, Any]]
    sources: Optional[List[str]]
    generated_date: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ==================== Research Requests ====================

class ResearchRequest(BaseModel):
    """Request to research a company"""
    company_name: str
    domain: Optional[str] = None
    job_id: Optional[int] = None
    research_depth: str = "standard"  # quick, standard, deep
    include_news: bool = True
    include_ratings: bool = True
    include_tech_stack: bool = True
    include_financials: bool = True


class ResearchResult(BaseModel):
    """Research result"""
    success: bool
    company_profile: Optional[CompanyProfile]
    news: List[CompanyNews]
    insights: List[CompanyInsight]
    research_completeness: float
    sources_used: List[str]
    error_message: Optional[str] = None


# ==================== Tech Stack ====================

class TechStackMatch(BaseModel):
    """Tech stack match"""
    id: int
    company_id: int
    technology: str
    category: Optional[str]
    candidate_has_experience: bool
    candidate_proficiency: Optional[str]
    years_experience: Optional[float]
    importance_to_company: Optional[str]
    detected_from: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Company Comparison ====================

class CompanyComparisonCreate(BaseModel):
    """Create company comparison"""
    comparison_name: str
    company_ids: List[int]
    comparison_criteria: List[str]  # ratings, culture, growth, tech_stack, etc.


class CompanyComparison(BaseModel):
    """Company comparison response"""
    id: int
    comparison_name: str
    company_ids: List[int]
    comparison_criteria: List[str]
    comparison_results: Optional[Dict[str, Any]]
    recommended_company_id: Optional[int]
    recommendation_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Research Dashboard ====================

class ResearchDashboard(BaseModel):
    """Research dashboard data"""
    total_companies_researched: int
    research_this_month: int
    avg_research_completeness: float
    companies_needing_update: int

    # Recent research
    recent_research: List[CompanyProfile]

    # Top companies
    top_rated_companies: List[CompanyProfile]
    fastest_growing_companies: List[CompanyProfile]

    # News summary
    recent_news_count: int
    positive_news_count: int
    recent_news: List[CompanyNews]


class ResearchSummary(BaseModel):
    """Summary of company research for a job"""
    company_name: str
    overall_rating: Optional[float]
    key_highlights: List[str]
    potential_concerns: List[str]
    culture_insights: List[str]
    recent_developments: List[str]
    tech_stack_match: float  # Percentage match
    recommended_talking_points: List[str]


class QuickResearchResponse(BaseModel):
    """Quick research response for job application"""
    company_name: str
    industry: Optional[str]
    size: Optional[str]
    rating: Optional[float]
    culture_score: Optional[float]
    quick_facts: List[str]
    talking_points: List[str]
    recent_news_headline: Optional[str]
