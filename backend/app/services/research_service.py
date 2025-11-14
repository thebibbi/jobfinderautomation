"""
Company Research Service

Automated company research using safe, legal methods.
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from loguru import logger
import httpx
import re

from ..models.research import (
    CompanyProfile as ProfileModel,
    CompanyNews as NewsModel,
    ResearchLog as LogModel,
    CompanyInsight as InsightModel,
    TechStackMatch as TechStackModel
)
from ..schemas.research import (
    ResearchRequest,
    CompanyNewsCreate,
    CompanyInsightCreate
)
from ..config import settings


class ResearchService:
    """Company Research Service"""

    # Data sources priority
    DATA_SOURCES = [
        "clearbit",      # Company data API
        "crunchbase",    # Funding and company info
        "glassdoor_api", # Ratings (via RapidAPI)
        "news_api",      # Recent news
        "builtwith",     # Tech stack detection
        "github",        # If company has public repos
    ]

    def __init__(self, db: Session):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def research_company(
        self,
        request: ResearchRequest
    ) -> Dict[str, Any]:
        """
        Research a company using multiple safe data sources

        Args:
            request: Research request with company name and options

        Returns:
            Research results with profile, news, and insights
        """
        logger.info(f"🔍 Researching company: {request.company_name}")

        # Check if we have recent research
        existing = self.db.query(ProfileModel).filter(
            ProfileModel.company_name.ilike(f"%{request.company_name}%")
        ).first()

        if existing and existing.last_researched:
            days_old = (datetime.utcnow() - existing.last_researched).days
            if days_old < 30 and existing.research_completeness > 70:
                logger.info(f"Using cached research (only {days_old} days old)")
                return self._format_results(existing, request)

        # Get or create profile
        profile = existing or ProfileModel(
            company_name=request.company_name,
            domain=request.domain
        )

        sources_used = []
        completeness = 0

        # Gather data from various sources
        if request.research_depth in ["standard", "deep"]:
            # 1. Company overview
            overview_data = await self._fetch_company_overview(request.company_name, request.domain)
            if overview_data:
                self._update_profile_overview(profile, overview_data)
                sources_used.append("clearbit")
                completeness += 25

            # 2. Ratings and reviews
            if request.include_ratings:
                ratings_data = await self._fetch_ratings(request.company_name)
                if ratings_data:
                    self._update_profile_ratings(profile, ratings_data)
                    sources_used.append("glassdoor_api")
                    completeness += 20

            # 3. Funding and financials
            if request.include_financials:
                financial_data = await self._fetch_financials(request.company_name)
                if financial_data:
                    self._update_profile_financials(profile, financial_data)
                    sources_used.append("crunchbase")
                    completeness += 15

            # 4. Tech stack
            if request.include_tech_stack and request.domain:
                tech_data = await self._detect_tech_stack(request.domain)
                if tech_data:
                    profile.tech_stack = tech_data.get("technologies", [])
                    profile.tech_stack_detected_from = "builtwith"
                    sources_used.append("builtwith")
                    completeness += 15

            # 5. Recent news
            news_items = []
            if request.include_news:
                news_data = await self._fetch_company_news(request.company_name)
                if news_data:
                    news_items = self._create_news_entries(profile, news_data)
                    sources_used.append("news_api")
                    completeness += 15

        else:  # Quick research
            # Just basic info
            overview_data = await self._fetch_company_overview(request.company_name, request.domain)
            if overview_data:
                self._update_profile_overview(profile, overview_data)
                sources_used.append("clearbit")
                completeness += 50

        # Update metadata
        profile.last_researched = datetime.utcnow()
        profile.research_completeness = min(completeness, 100)
        profile.data_sources = sources_used

        if not existing:
            self.db.add(profile)

        self.db.commit()
        self.db.refresh(profile)

        # Generate insights
        insights = self._generate_insights(profile, request.job_id)

        logger.info(f"✅ Research complete: {completeness}% completeness, {len(sources_used)} sources")

        return {
            "success": True,
            "company_profile": profile,
            "news": news_items if request.include_news else [],
            "insights": insights,
            "research_completeness": completeness,
            "sources_used": sources_used
        }

    # ==================== Data Fetching Methods ====================

    async def _fetch_company_overview(
        self,
        company_name: str,
        domain: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch company overview data

        In production, integrate with Clearbit, RapidAPI, or similar
        """
        try:
            # Mock data for now - in production, call actual API
            # Example: Clearbit Company API, RapidAPI Company Data API
            logger.info(f"Fetching overview for {company_name}")

            # Simulated API call
            overview = {
                "name": company_name,
                "domain": domain,
                "description": f"Technology company focused on innovation",
                "industry": "Technology",
                "company_size": "medium",
                "founded_year": 2015,
                "headquarters": "San Francisco, CA",
                "website": f"https://{domain}" if domain else None,
                "employee_count": 250
            }

            # Log research
            self._log_research(
                company_name=company_name,
                research_type="profile",
                data_source="clearbit",
                success=True,
                data=overview
            )

            return overview

        except Exception as e:
            logger.error(f"Error fetching company overview: {e}")
            self._log_research(
                company_name=company_name,
                research_type="profile",
                data_source="clearbit",
                success=False,
                error=str(e)
            )
            return None

    async def _fetch_ratings(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company ratings from Glassdoor, Indeed, etc.

        In production, use RapidAPI Glassdoor API or similar
        """
        try:
            logger.info(f"Fetching ratings for {company_name}")

            # Mock data - in production, call RapidAPI Glassdoor API
            ratings = {
                "glassdoor_rating": 4.2,
                "glassdoor_review_count": 150,
                "work_life_balance_rating": 4.0,
                "culture_values_rating": 4.3,
                "indeed_rating": 4.1,
                "indeed_review_count": 89
            }

            self._log_research(
                company_name=company_name,
                research_type="ratings",
                data_source="glassdoor_api",
                success=True,
                data=ratings
            )

            return ratings

        except Exception as e:
            logger.error(f"Error fetching ratings: {e}")
            self._log_research(
                company_name=company_name,
                research_type="ratings",
                data_source="glassdoor_api",
                success=False,
                error=str(e)
            )
            return None

    async def _fetch_financials(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company financial data

        In production, use Crunchbase API via RapidAPI
        """
        try:
            logger.info(f"Fetching financials for {company_name}")

            # Mock data - in production, call Crunchbase API
            financials = {
                "funding_total": 25000000,
                "funding_stage": "series_b",
                "valuation": 100000000,
                "revenue_range": "10M-50M",
                "employee_growth_rate": 15.5,
                "hiring_status": "actively_hiring"
            }

            self._log_research(
                company_name=company_name,
                research_type="financials",
                data_source="crunchbase",
                success=True,
                data=financials
            )

            return financials

        except Exception as e:
            logger.error(f"Error fetching financials: {e}")
            return None

    async def _detect_tech_stack(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Detect company tech stack

        In production, use BuiltWith API or Wappalyzer
        """
        try:
            logger.info(f"Detecting tech stack for {domain}")

            # Mock data - in production, call BuiltWith API
            tech_stack = {
                "technologies": [
                    "React",
                    "Node.js",
                    "PostgreSQL",
                    "AWS",
                    "Python",
                    "Docker"
                ],
                "categories": {
                    "frontend": ["React"],
                    "backend": ["Node.js", "Python"],
                    "database": ["PostgreSQL"],
                    "infrastructure": ["AWS", "Docker"]
                }
            }

            self._log_research(
                company_name=domain,
                research_type="tech_stack",
                data_source="builtwith",
                success=True,
                data=tech_stack
            )

            return tech_stack

        except Exception as e:
            logger.error(f"Error detecting tech stack: {e}")
            return None

    async def _fetch_company_news(self, company_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch recent company news

        In production, use NewsAPI, Google News API, or similar
        """
        try:
            logger.info(f"Fetching news for {company_name}")

            # Mock data - in production, call NewsAPI
            news = [
                {
                    "title": f"{company_name} raises $15M in Series B funding",
                    "summary": "Company announces major funding round to expand operations",
                    "url": "https://techcrunch.com/article",
                    "source": "TechCrunch",
                    "published_date": datetime.utcnow() - timedelta(days=5),
                    "category": "funding",
                    "sentiment": "positive",
                    "relevance_score": 0.9
                },
                {
                    "title": f"{company_name} launches new product feature",
                    "summary": "Innovative feature to improve customer experience",
                    "url": "https://news.com/article",
                    "source": "Tech News",
                    "published_date": datetime.utcnow() - timedelta(days=12),
                    "category": "product",
                    "sentiment": "positive",
                    "relevance_score": 0.7
                }
            ]

            self._log_research(
                company_name=company_name,
                research_type="news",
                data_source="news_api",
                success=True,
                data={"count": len(news)}
            )

            return news

        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return None

    # ==================== Data Processing ====================

    def _update_profile_overview(self, profile: ProfileModel, data: Dict[str, Any]):
        """Update profile with overview data"""
        profile.domain = data.get("domain") or profile.domain
        profile.description = data.get("description")
        profile.industry = data.get("industry")
        profile.company_size = data.get("company_size")
        profile.founded_year = data.get("founded_year")
        profile.company_type = data.get("company_type")
        profile.headquarters = data.get("headquarters")
        profile.website = data.get("website")
        profile.employee_count = data.get("employee_count")

    def _update_profile_ratings(self, profile: ProfileModel, data: Dict[str, Any]):
        """Update profile with ratings data"""
        profile.glassdoor_rating = data.get("glassdoor_rating")
        profile.glassdoor_review_count = data.get("glassdoor_review_count")
        profile.work_life_balance_rating = data.get("work_life_balance_rating")
        profile.culture_values_rating = data.get("culture_values_rating")
        profile.indeed_rating = data.get("indeed_rating")
        profile.indeed_review_count = data.get("indeed_review_count")

    def _update_profile_financials(self, profile: ProfileModel, data: Dict[str, Any]):
        """Update profile with financial data"""
        profile.funding_total = data.get("funding_total")
        profile.funding_stage = data.get("funding_stage")
        profile.valuation = data.get("valuation")
        profile.revenue_range = data.get("revenue_range")
        profile.employee_growth_rate = data.get("employee_growth_rate")
        profile.hiring_status = data.get("hiring_status")

    def _create_news_entries(
        self,
        profile: ProfileModel,
        news_data: List[Dict[str, Any]]
    ) -> List[NewsModel]:
        """Create news entries"""
        news_items = []

        for news_item in news_data[:10]:  # Limit to 10 most recent
            news = NewsModel(
                company_id=profile.id,
                title=news_item["title"],
                summary=news_item.get("summary"),
                url=news_item.get("url"),
                source=news_item.get("source"),
                published_date=news_item.get("published_date"),
                category=news_item.get("category"),
                sentiment=news_item.get("sentiment"),
                relevance_score=news_item.get("relevance_score")
            )
            self.db.add(news)
            news_items.append(news)

        return news_items

    # ==================== Insights Generation ====================

    def _generate_insights(
        self,
        profile: ProfileModel,
        job_id: Optional[int] = None
    ) -> List[InsightModel]:
        """Generate actionable insights from research data"""
        insights = []

        # Rating insights
        if profile.glassdoor_rating:
            if profile.glassdoor_rating >= 4.0:
                insight = InsightModel(
                    company_id=profile.id,
                    job_id=job_id,
                    insight_type="opportunity",
                    title="High Employee Satisfaction",
                    description=f"Glassdoor rating of {profile.glassdoor_rating}/5.0 indicates strong employee satisfaction",
                    relevance_score=0.8,
                    confidence=0.9,
                    how_to_use="Mention company's positive reputation in cover letter",
                    suggested_talking_point=f"I'm impressed by {profile.company_name}'s {profile.glassdoor_rating} Glassdoor rating"
                )
                self.db.add(insight)
                insights.append(insight)
            elif profile.glassdoor_rating < 3.5:
                insight = InsightModel(
                    company_id=profile.id,
                    job_id=job_id,
                    insight_type="concern",
                    title="Below Average Employee Rating",
                    description=f"Glassdoor rating of {profile.glassdoor_rating}/5.0 is below average",
                    relevance_score=0.7,
                    confidence=0.8,
                    how_to_use="Ask about culture and work environment during interview"
                )
                self.db.add(insight)
                insights.append(insight)

        # Growth insights
        if profile.funding_stage and profile.funding_total:
            insight = InsightModel(
                company_id=profile.id,
                job_id=job_id,
                insight_type="opportunity",
                title=f"Well-Funded Growth Stage Company",
                description=f"Recently raised {profile.funding_stage} funding of ${profile.funding_total:,.0f}",
                relevance_score=0.9,
                confidence=0.95,
                how_to_use="Highlight ability to work in fast-paced growth environment",
                suggested_talking_point="Excited to contribute during this growth phase"
            )
            self.db.add(insight)
            insights.append(insight)

        # Culture insights
        if profile.work_life_balance_rating and profile.work_life_balance_rating >= 4.0:
            insight = InsightModel(
                company_id=profile.id,
                job_id=job_id,
                insight_type="opportunity",
                title="Strong Work-Life Balance",
                description=f"Work-life balance rating of {profile.work_life_balance_rating}/5.0",
                relevance_score=0.75,
                confidence=0.85,
                how_to_use="Shows company values employee well-being"
            )
            self.db.add(insight)
            insights.append(insight)

        return insights

    # ==================== Logging ====================

    def _log_research(
        self,
        company_name: str,
        research_type: str,
        data_source: str,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Log research activity"""
        # Get or create profile first
        profile = self.db.query(ProfileModel).filter(
            ProfileModel.company_name.ilike(f"%{company_name}%")
        ).first()

        if not profile:
            # Create minimal profile
            profile = ProfileModel(company_name=company_name)
            self.db.add(profile)
            self.db.flush()

        log = LogModel(
            company_id=profile.id,
            research_type=research_type,
            data_source=data_source,
            success=success,
            data_retrieved=data,
            error_message=error
        )
        self.db.add(log)

    # ==================== Helper Methods ====================

    def _format_results(
        self,
        profile: ProfileModel,
        request: ResearchRequest
    ) -> Dict[str, Any]:
        """Format cached results"""
        news = self.db.query(NewsModel).filter(
            NewsModel.company_id == profile.id
        ).order_by(NewsModel.published_date.desc()).limit(10).all()

        insights = self.db.query(InsightModel).filter(
            InsightModel.company_id == profile.id,
            InsightModel.is_active == True
        ).all()

        return {
            "success": True,
            "company_profile": profile,
            "news": news,
            "insights": insights,
            "research_completeness": profile.research_completeness,
            "sources_used": profile.data_sources or []
        }

    def get_company_summary(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Get quick summary of company research"""
        profile = self.db.query(ProfileModel).filter(
            ProfileModel.company_name.ilike(f"%{company_name}%")
        ).first()

        if not profile:
            return None

        return {
            "company_name": profile.company_name,
            "industry": profile.industry,
            "size": profile.company_size,
            "rating": profile.glassdoor_rating,
            "culture_score": profile.culture_values_rating,
            "quick_facts": [
                f"Founded in {profile.founded_year}" if profile.founded_year else None,
                f"{profile.employee_count} employees" if profile.employee_count else None,
                f"Based in {profile.headquarters}" if profile.headquarters else None,
                f"{profile.funding_stage} funding" if profile.funding_stage else None
            ],
            "recent_news": self.db.query(NewsModel).filter(
                NewsModel.company_id == profile.id
            ).order_by(NewsModel.published_date.desc()).first()
        }


def get_research_service(db: Session) -> ResearchService:
    """Get research service instance"""
    return ResearchService(db)
