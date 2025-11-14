"""
Company Research API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..services.research_service import get_research_service
from ..models.research import (
    CompanyProfile as ProfileModel,
    CompanyNews as NewsModel,
    CompanyInsight as InsightModel,
    ResearchLog as LogModel
)
from ..schemas.research import (
    ResearchRequest,
    ResearchResult,
    CompanyProfile,
    CompanyNews,
    CompanyInsight,
    ResearchLog,
    QuickResearchResponse,
    ResearchDashboard,
    ResearchSummary
)


router = APIRouter()


# ==================== Company Research ====================

@router.post("/research", response_model=ResearchResult)
async def research_company(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Research a company using safe, legal data sources

    Gathers company information from:
    - Public APIs (Clearbit, Crunchbase via RapidAPI)
    - Glassdoor ratings (via API, not scraping)
    - Recent news articles
    - Tech stack detection
    - Public company data

    Does NOT scrape LinkedIn or violate any terms of service.
    """
    try:
        service = get_research_service(db)
        result = await service.research_company(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error researching company: {str(e)}"
        )


@router.get("/companies", response_model=List[CompanyProfile])
async def get_companies(
    limit: int = Query(100, le=500),
    min_rating: Optional[float] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get researched companies

    Optionally filter by rating and industry.
    """
    try:
        query = db.query(ProfileModel)

        if min_rating:
            query = query.filter(ProfileModel.glassdoor_rating >= min_rating)

        if industry:
            query = query.filter(ProfileModel.industry.ilike(f"%{industry}%"))

        companies = query.order_by(ProfileModel.last_researched.desc()).limit(limit).all()
        return companies
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving companies: {str(e)}"
        )


@router.get("/companies/{company_id}", response_model=CompanyProfile)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed company profile
    """
    try:
        company = db.query(ProfileModel).filter(ProfileModel.id == company_id).first()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        return company
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving company: {str(e)}"
        )


@router.get("/companies/name/{company_name}", response_model=CompanyProfile)
async def get_company_by_name(
    company_name: str,
    db: Session = Depends(get_db)
):
    """
    Get company profile by name
    """
    try:
        company = db.query(ProfileModel).filter(
            ProfileModel.company_name.ilike(f"%{company_name}%")
        ).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company '{company_name}' not found. Research it first."
            )

        return company
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving company: {str(e)}"
        )


# ==================== Company News ====================

@router.get("/companies/{company_id}/news", response_model=List[CompanyNews])
async def get_company_news(
    company_id: int,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recent news for a company
    """
    try:
        news = db.query(NewsModel).filter(
            NewsModel.company_id == company_id
        ).order_by(NewsModel.published_date.desc()).limit(limit).all()

        return news
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving news: {str(e)}"
        )


# ==================== Company Insights ====================

@router.get("/companies/{company_id}/insights", response_model=List[CompanyInsight])
async def get_company_insights(
    company_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get generated insights for a company

    Insights include:
    - Talking points for interviews
    - Culture indicators
    - Growth opportunities
    - Potential concerns
    """
    try:
        query = db.query(InsightModel).filter(InsightModel.company_id == company_id)

        if active_only:
            query = query.filter(InsightModel.is_active == True)

        insights = query.order_by(InsightModel.relevance_score.desc()).all()
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving insights: {str(e)}"
        )


# ==================== Quick Research ====================

@router.get("/quick/{company_name}", response_model=QuickResearchResponse)
async def quick_research(
    company_name: str,
    db: Session = Depends(get_db)
):
    """
    Get quick research summary

    Fast endpoint for basic company info during job application.
    """
    try:
        service = get_research_service(db)
        summary = service.get_company_summary(company_name)

        if not summary:
            # Trigger research if not found
            request = ResearchRequest(
                company_name=company_name,
                research_depth="quick",
                include_news=False,
                include_ratings=True,
                include_tech_stack=False,
                include_financials=False
            )
            result = await service.research_company(request)
            summary = service.get_company_summary(company_name)

        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not research company"
            )

        # Generate talking points from insights
        profile = db.query(ProfileModel).filter(
            ProfileModel.company_name.ilike(f"%{company_name}%")
        ).first()

        insights = db.query(InsightModel).filter(
            InsightModel.company_id == profile.id,
            InsightModel.is_active == True
        ).all() if profile else []

        talking_points = [i.suggested_talking_point for i in insights if i.suggested_talking_point]

        return QuickResearchResponse(
            company_name=summary["company_name"],
            industry=summary["industry"],
            size=summary["size"],
            rating=summary["rating"],
            culture_score=summary["culture_score"],
            quick_facts=[f for f in summary["quick_facts"] if f],
            talking_points=talking_points,
            recent_news_headline=summary["recent_news"].title if summary.get("recent_news") else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during quick research: {str(e)}"
        )


# ==================== Research Logs ====================

@router.get("/logs", response_model=List[ResearchLog])
async def get_research_logs(
    company_id: Optional[int] = None,
    data_source: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """
    Get research activity logs

    Useful for debugging and monitoring API usage.
    """
    try:
        query = db.query(LogModel)

        if company_id:
            query = query.filter(LogModel.company_id == company_id)

        if data_source:
            query = query.filter(LogModel.data_source == data_source)

        logs = query.order_by(LogModel.created_at.desc()).limit(limit).all()
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving logs: {str(e)}"
        )


# ==================== Dashboard ====================

@router.get("/dashboard", response_model=ResearchDashboard)
async def get_research_dashboard(db: Session = Depends(get_db)):
    """
    Get research dashboard data

    Overview of all researched companies and recent activity.
    """
    try:
        from datetime import date, timedelta

        # Total companies
        total = db.query(ProfileModel).count()

        # Research this month
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = db.query(ProfileModel).filter(
            ProfileModel.last_researched >= month_start
        ).count()

        # Average completeness
        avg_completeness = db.query(func.avg(ProfileModel.research_completeness)).scalar() or 0

        # Companies needing update (>30 days old)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        needing_update = db.query(ProfileModel).filter(
            or_(
                ProfileModel.last_researched < thirty_days_ago,
                ProfileModel.last_researched.is_(None)
            )
        ).count()

        # Recent research
        recent = db.query(ProfileModel).order_by(
            ProfileModel.last_researched.desc()
        ).limit(10).all()

        # Top rated
        top_rated = db.query(ProfileModel).filter(
            ProfileModel.glassdoor_rating.isnot(None)
        ).order_by(ProfileModel.glassdoor_rating.desc()).limit(10).all()

        # Fastest growing
        fastest_growing = db.query(ProfileModel).filter(
            ProfileModel.employee_growth_rate.isnot(None)
        ).order_by(ProfileModel.employee_growth_rate.desc()).limit(10).all()

        # Recent news
        recent_news = db.query(NewsModel).order_by(
            NewsModel.published_date.desc()
        ).limit(10).all()

        recent_news_count = db.query(NewsModel).filter(
            NewsModel.published_date >= thirty_days_ago
        ).count()

        positive_news = db.query(NewsModel).filter(
            NewsModel.sentiment == "positive",
            NewsModel.published_date >= thirty_days_ago
        ).count()

        from sqlalchemy import func, or_

        dashboard = ResearchDashboard(
            total_companies_researched=total,
            research_this_month=this_month,
            avg_research_completeness=float(avg_completeness),
            companies_needing_update=needing_update,
            recent_research=recent,
            top_rated_companies=top_rated,
            fastest_growing_companies=fastest_growing,
            recent_news_count=recent_news_count,
            positive_news_count=positive_news,
            recent_news=recent_news
        )

        return dashboard
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard: {str(e)}"
        )


# ==================== Summary for Job ====================

@router.get("/summary/{company_name}", response_model=ResearchSummary)
async def get_research_summary_for_job(
    company_name: str,
    job_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get tailored research summary for a specific job application

    Returns actionable insights and talking points.
    """
    try:
        company = db.query(ProfileModel).filter(
            ProfileModel.company_name.ilike(f"%{company_name}%")
        ).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company '{company_name}' not found. Research it first."
            )

        # Get insights
        insights = db.query(InsightModel).filter(
            InsightModel.company_id == company.id,
            InsightModel.is_active == True
        ).all()

        # Categorize insights
        key_highlights = [i.description for i in insights if i.insight_type == "opportunity"]
        concerns = [i.description for i in insights if i.insight_type == "concern"]

        # Culture insights
        culture_insights = []
        if company.work_life_balance_rating:
            culture_insights.append(f"Work-life balance: {company.work_life_balance_rating}/5.0")
        if company.culture_values_rating:
            culture_insights.append(f"Culture & values: {company.culture_values_rating}/5.0")

        # Recent news
        news = db.query(NewsModel).filter(
            NewsModel.company_id == company.id
        ).order_by(NewsModel.published_date.desc()).limit(3).all()

        recent_developments = [n.title for n in news]

        # Tech stack match (simplified)
        tech_match = 75.0 if company.tech_stack else 0.0

        # Talking points
        talking_points = [i.suggested_talking_point for i in insights if i.suggested_talking_point]

        summary = ResearchSummary(
            company_name=company.company_name,
            overall_rating=company.glassdoor_rating,
            key_highlights=key_highlights[:5],
            potential_concerns=concerns[:3],
            culture_insights=culture_insights,
            recent_developments=recent_developments,
            tech_stack_match=tech_match,
            recommended_talking_points=talking_points[:5]
        )

        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )
