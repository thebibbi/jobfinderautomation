"""
Job Recommendations Service

ML-based job recommendation system with collaborative filtering,
content-based filtering, and hybrid approaches.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from loguru import logger

from ..models.recommendations import (
    UserPreference, JobRecommendation, RecommendationFeedback,
    RecommendationDigest, SimilarJob, RecommendationModel, RecommendationMetrics
)
from ..models.job import Job
from ..models.application import ApplicationEvent
from ..schemas.recommendations import (
    JobRecommendationCreate, RecommendationFeedbackCreate,
    DigestCreate, SimilarJobCreate
)


class RecommendationService:
    """Job recommendation service"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Core Recommendation Methods ====================

    def get_recommendations(
        self,
        limit: int = 10,
        algorithm: str = "hybrid",
        include_reasons: bool = True,
        filter_applied: bool = False,
        min_score: float = 60.0
    ) -> List[JobRecommendation]:
        """
        Get personalized job recommendations

        Args:
            limit: Maximum number of recommendations
            algorithm: collaborative, content_based, or hybrid
            include_reasons: Include explanation
            filter_applied: Filter out already applied jobs
            min_score: Minimum recommendation score
        """
        logger.info(f"Generating recommendations using {algorithm} algorithm")

        # Get candidate jobs
        query = self.db.query(Job).filter(Job.is_active == True)

        if filter_applied:
            # Exclude jobs with application events
            applied_job_ids = self.db.query(ApplicationEvent.job_id).distinct()
            query = query.filter(~Job.id.in_(applied_job_ids))

        candidate_jobs = query.all()

        if not candidate_jobs:
            logger.warning("No candidate jobs found for recommendations")
            return []

        # Generate scores based on algorithm
        if algorithm == "collaborative":
            scored_jobs = self._collaborative_filtering(candidate_jobs)
        elif algorithm == "content_based":
            scored_jobs = self._content_based_filtering(candidate_jobs)
        else:  # hybrid
            scored_jobs = self._hybrid_recommendations(candidate_jobs)

        # Filter by minimum score
        scored_jobs = [(job, score, reasons, factors) for job, score, reasons, factors in scored_jobs if score >= min_score]

        # Sort by score and limit
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        scored_jobs = scored_jobs[:limit]

        # Create recommendation records
        recommendations = []
        for job, score, reasons, factors in scored_jobs:
            # Check if recommendation already exists
            existing = self.db.query(JobRecommendation).filter(
                JobRecommendation.job_id == job.id,
                JobRecommendation.status == "pending"
            ).first()

            if existing:
                # Update existing
                existing.recommendation_score = score
                existing.recommendation_reasons = reasons if include_reasons else None
                existing.match_factors = factors
                existing.recommended_at = datetime.utcnow()
                recommendations.append(existing)
            else:
                # Create new
                recommendation = JobRecommendation(
                    job_id=job.id,
                    recommendation_score=score,
                    confidence=self._calculate_confidence(job, score),
                    recommendation_reasons=reasons if include_reasons else None,
                    match_factors=factors,
                    status="pending",
                    recommended_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=14)
                )
                self.db.add(recommendation)
                recommendations.append(recommendation)

        self.db.commit()
        return recommendations

    # ==================== Recommendation Algorithms ====================

    def _collaborative_filtering(self, candidate_jobs: List[Job]) -> List[Tuple[Job, float, Dict, Dict]]:
        """
        Collaborative filtering based on similar user behavior

        "Users who applied to job X also applied to job Y"
        """
        logger.info("Running collaborative filtering")
        scored_jobs = []

        # Get user's application history
        user_applied_jobs = self.db.query(ApplicationEvent.job_id).filter(
            ApplicationEvent.event_type == "status_change",
            ApplicationEvent.new_status.in_(["applied", "interviewing", "offer_received"])
        ).all()
        user_applied_job_ids = [job_id for (job_id,) in user_applied_jobs]

        if not user_applied_job_ids:
            # No history, fall back to content-based
            logger.info("No application history, falling back to popularity")
            return self._content_based_filtering(candidate_jobs)

        for job in candidate_jobs:
            if job.id in user_applied_job_ids:
                continue

            # Find jobs frequently applied to together with user's jobs
            similar_users_jobs = self.db.query(
                ApplicationEvent.job_id,
                func.count(ApplicationEvent.id).label("frequency")
            ).filter(
                ApplicationEvent.event_type == "status_change",
                ApplicationEvent.new_status.in_(["applied", "interviewing"]),
                ApplicationEvent.job_id != job.id
            ).group_by(ApplicationEvent.job_id).all()

            # Calculate score based on overlap
            overlap_count = sum(1 for job_id, _ in similar_users_jobs if job_id in user_applied_job_ids)
            max_possible = len(user_applied_job_ids)

            if max_possible > 0:
                base_score = (overlap_count / max_possible) * 100
            else:
                base_score = 50.0

            # Boost by recency
            if job.posted_date:
                days_old = (datetime.utcnow() - job.posted_date).days
                recency_boost = max(0, 10 - (days_old / 7))  # Up to 10 points for recent jobs
                base_score += recency_boost

            reasons = {
                "algorithm": "collaborative_filtering",
                "overlap_with_applied": overlap_count,
                "total_applied": max_possible,
                "similar_users_applied": len(similar_users_jobs)
            }

            factors = {
                "base_score": base_score,
                "recency_boost": recency_boost if job.posted_date else 0
            }

            scored_jobs.append((job, min(base_score, 100.0), reasons, factors))

        return scored_jobs

    def _content_based_filtering(self, candidate_jobs: List[Job]) -> List[Tuple[Job, float, Dict, Dict]]:
        """
        Content-based filtering based on job attributes and user preferences
        """
        logger.info("Running content-based filtering")
        scored_jobs = []

        # Get user preferences
        preferences = self.db.query(UserPreference).filter(
            UserPreference.is_active == True
        ).all()

        preference_dict = defaultdict(list)
        for pref in preferences:
            preference_dict[pref.preference_type].append({
                "value": pref.preference_value,
                "score": pref.preference_score,
                "confidence": pref.confidence
            })

        for job in candidate_jobs:
            score = 50.0  # Base score
            reasons = {"algorithm": "content_based", "matches": []}
            factors = {}

            # Match company preferences
            if job.company and "company" in preference_dict:
                for pref in preference_dict["company"]:
                    if pref["value"].lower() in job.company.lower():
                        boost = pref["score"] * pref["confidence"] * 20
                        score += boost
                        reasons["matches"].append(f"Preferred company: {job.company}")
                        factors["company_match"] = boost

            # Match location preferences
            if job.location and "location" in preference_dict:
                for pref in preference_dict["location"]:
                    if pref["value"].lower() in job.location.lower():
                        boost = pref["score"] * pref["confidence"] * 15
                        score += boost
                        reasons["matches"].append(f"Preferred location: {job.location}")
                        factors["location_match"] = boost

            # Match remote preferences
            if "remote" in preference_dict:
                remote_pref = preference_dict["remote"][0]
                if remote_pref["value"] == "true" and job.location and "remote" in job.location.lower():
                    boost = remote_pref["score"] * remote_pref["confidence"] * 15
                    score += boost
                    reasons["matches"].append("Remote work preferred")
                    factors["remote_match"] = boost

            # Match job title keywords
            if job.title and "job_title_keyword" in preference_dict:
                for pref in preference_dict["job_title_keyword"]:
                    if pref["value"].lower() in job.title.lower():
                        boost = pref["score"] * pref["confidence"] * 10
                        score += boost
                        reasons["matches"].append(f"Title keyword: {pref['value']}")
                        factors[f"keyword_{pref['value']}"] = boost

            # Penalize if job has low match score
            if hasattr(job, 'match_score') and job.match_score:
                if job.match_score < 60:
                    penalty = (60 - job.match_score) * 0.3
                    score -= penalty
                    factors["match_score_penalty"] = -penalty
                elif job.match_score > 80:
                    boost = (job.match_score - 80) * 0.5
                    score += boost
                    reasons["matches"].append(f"High match score: {job.match_score}")
                    factors["match_score_boost"] = boost

            # Boost recent postings
            if job.posted_date:
                days_old = (datetime.utcnow() - job.posted_date).days
                if days_old < 7:
                    boost = 10
                    score += boost
                    reasons["matches"].append("Recently posted")
                    factors["recency_boost"] = boost

            scored_jobs.append((job, min(max(score, 0), 100.0), reasons, factors))

        return scored_jobs

    def _hybrid_recommendations(self, candidate_jobs: List[Job]) -> List[Tuple[Job, float, Dict, Dict]]:
        """
        Hybrid approach combining collaborative and content-based filtering
        """
        logger.info("Running hybrid recommendations")

        # Get both sets of scores
        collaborative_scores = {job.id: (score, reasons, factors)
                              for job, score, reasons, factors in self._collaborative_filtering(candidate_jobs)}
        content_scores = {job.id: (score, reasons, factors)
                         for job, score, reasons, factors in self._content_based_filtering(candidate_jobs)}

        scored_jobs = []

        for job in candidate_jobs:
            collab_score, collab_reasons, collab_factors = collaborative_scores.get(job.id, (0, {}, {}))
            content_score, content_reasons, content_factors = content_scores.get(job.id, (50, {}, {}))

            # Weighted average (60% content, 40% collaborative)
            # Content-based is more reliable when we have preferences
            final_score = (content_score * 0.6) + (collab_score * 0.4)

            # Combine reasons
            reasons = {
                "algorithm": "hybrid",
                "content_based_score": content_score,
                "collaborative_score": collab_score,
                "content_matches": content_reasons.get("matches", []),
                "collaborative_overlap": collab_reasons.get("overlap_with_applied", 0)
            }

            # Combine factors
            factors = {
                **content_factors,
                **{f"collab_{k}": v for k, v in collab_factors.items()},
                "content_weight": 0.6,
                "collaborative_weight": 0.4
            }

            scored_jobs.append((job, final_score, reasons, factors))

        return scored_jobs

    # ==================== Preference Learning ====================

    def learn_from_application(self, job_id: int):
        """Learn user preferences from application behavior"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        logger.info(f"Learning preferences from job application: {job.title}")

        # Learn company preference
        if job.company:
            self._update_preference("company", job.company, 0.7, "applications")

        # Learn location preference
        if job.location:
            self._update_preference("location", job.location, 0.6, "applications")

            # Learn remote preference
            if "remote" in job.location.lower():
                self._update_preference("remote", "true", 0.8, "applications")

        # Learn job title keywords
        if job.title:
            # Extract common keywords (simplified - in production use NLP)
            keywords = ["senior", "lead", "engineer", "manager", "developer", "architect"]
            for keyword in keywords:
                if keyword.lower() in job.title.lower():
                    self._update_preference("job_title_keyword", keyword, 0.5, "applications")

        self.db.commit()

    def learn_from_click(self, job_id: int):
        """Learn from job clicks (weaker signal than application)"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        logger.info(f"Learning preferences from job click: {job.title}")

        if job.company:
            self._update_preference("company", job.company, 0.3, "clicks")

        if job.location:
            self._update_preference("location", job.location, 0.2, "clicks")

        self.db.commit()

    def learn_from_dismissal(self, job_id: int, reason: Optional[str] = None):
        """Learn from job dismissals (negative signal)"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        logger.info(f"Learning preferences from job dismissal: {job.title}")

        # Decrease preference scores
        if job.company:
            self._update_preference("company", job.company, -0.2, "dismissals")

        if reason and "location" in reason.lower() and job.location:
            self._update_preference("location", job.location, -0.3, "dismissals")

        self.db.commit()

    def _update_preference(
        self,
        preference_type: str,
        preference_value: str,
        score_delta: float,
        learned_from: str
    ):
        """Update or create user preference"""
        # Find existing preference
        pref = self.db.query(UserPreference).filter(
            UserPreference.preference_type == preference_type,
            UserPreference.preference_value == preference_value
        ).first()

        if pref:
            # Update existing
            old_score = pref.preference_score
            new_score = max(0.0, min(1.0, old_score + score_delta))

            # Update with exponential moving average for confidence
            pref.preference_score = new_score
            pref.sample_size += 1
            pref.confidence = min(1.0, pref.confidence + (0.1 * (1 - pref.confidence)))
            pref.last_updated = datetime.utcnow()

            logger.debug(f"Updated preference {preference_type}={preference_value}: {old_score:.2f} -> {new_score:.2f}")
        else:
            # Create new
            pref = UserPreference(
                preference_type=preference_type,
                preference_value=preference_value,
                preference_score=max(0.0, min(1.0, 0.5 + score_delta)),
                confidence=0.3,  # Low initial confidence
                learned_from=learned_from,
                sample_size=1,
                is_active=True
            )
            self.db.add(pref)
            logger.debug(f"Created preference {preference_type}={preference_value}")

    # ==================== Feedback ====================

    def record_feedback(
        self,
        recommendation_id: int,
        feedback_type: str,
        feedback_text: Optional[str] = None,
        rating: Optional[int] = None
    ) -> RecommendationFeedback:
        """Record user feedback on recommendation"""
        recommendation = self.db.query(JobRecommendation).filter(
            JobRecommendation.id == recommendation_id
        ).first()

        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        # Create feedback
        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            feedback_type=feedback_type,
            feedback_text=feedback_text,
            rating=rating
        )
        self.db.add(feedback)

        # Update recommendation based on feedback
        if rating:
            recommendation.user_rating = rating

        if feedback_type == "not_helpful":
            # Learn from negative feedback
            self.learn_from_dismissal(recommendation.job_id, feedback_text)
        elif feedback_type == "helpful":
            # Boost these preferences
            self.learn_from_click(recommendation.job_id)

        self.db.commit()
        return feedback

    # ==================== Similar Jobs ====================

    def find_similar_jobs(self, job_id: int, limit: int = 5) -> List[SimilarJob]:
        """Find jobs similar to the given job"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return []

        logger.info(f"Finding similar jobs to: {job.title}")

        # Check cache first
        cached = self.db.query(SimilarJob).filter(
            SimilarJob.job_id == job_id,
            SimilarJob.calculated_at > datetime.utcnow() - timedelta(days=7)
        ).all()

        if cached:
            return cached[:limit]

        # Calculate similarities
        candidate_jobs = self.db.query(Job).filter(
            Job.id != job_id,
            Job.is_active == True
        ).all()

        similarities = []
        for candidate in candidate_jobs:
            score, factors = self._calculate_similarity(job, candidate)
            if score > 0.5:  # Minimum threshold
                similarities.append((candidate, score, factors))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        similarities = similarities[:limit]

        # Create records
        similar_jobs = []
        for candidate, score, factors in similarities:
            similar = SimilarJob(
                job_id=job_id,
                similar_job_id=candidate.id,
                similarity_score=score,
                similarity_factors=factors,
                calculated_at=datetime.utcnow()
            )
            self.db.add(similar)
            similar_jobs.append(similar)

        self.db.commit()
        return similar_jobs

    def _calculate_similarity(self, job1: Job, job2: Job) -> Tuple[float, Dict[str, Any]]:
        """Calculate similarity between two jobs"""
        factors = {}
        score = 0.0

        # Title similarity (simple word overlap)
        if job1.title and job2.title:
            words1 = set(job1.title.lower().split())
            words2 = set(job2.title.lower().split())
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            score += overlap * 0.4
            factors["title_overlap"] = overlap

        # Company match
        if job1.company and job2.company and job1.company.lower() == job2.company.lower():
            score += 0.2
            factors["same_company"] = True

        # Location match
        if job1.location and job2.location and job1.location.lower() == job2.location.lower():
            score += 0.15
            factors["same_location"] = True

        # Match score similarity
        if job1.match_score and job2.match_score:
            score_diff = abs(job1.match_score - job2.match_score)
            if score_diff < 10:
                score += 0.15
                factors["similar_match_score"] = True

        # Recency similarity
        if job1.posted_date and job2.posted_date:
            days_diff = abs((job1.posted_date - job2.posted_date).days)
            if days_diff < 14:
                score += 0.1
                factors["similar_posting_time"] = True

        return min(score, 1.0), factors

    # ==================== Digests ====================

    def generate_daily_digest(self) -> Optional[RecommendationDigest]:
        """Generate daily recommendation digest"""
        logger.info("Generating daily digest")

        # Get top recommendations from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        recommendations = self.db.query(JobRecommendation).filter(
            JobRecommendation.recommended_at >= yesterday,
            JobRecommendation.status == "pending"
        ).order_by(desc(JobRecommendation.recommendation_score)).limit(10).all()

        if not recommendations:
            logger.info("No new recommendations for digest")
            return None

        # Get previous digest to find new opportunities
        prev_digest = self.db.query(RecommendationDigest).filter(
            RecommendationDigest.digest_type == "daily"
        ).order_by(desc(RecommendationDigest.digest_date)).first()

        prev_job_ids = set(prev_digest.job_ids) if prev_digest else set()
        current_job_ids = [rec.job_id for rec in recommendations]
        new_opportunities = len(set(current_job_ids) - prev_job_ids)

        # Generate highlights
        highlights = {
            "avg_score": sum(r.recommendation_score for r in recommendations) / len(recommendations),
            "top_companies": list(set(r.job.company for r in recommendations[:5] if r.job.company)),
            "locations": list(set(r.job.location for r in recommendations if r.job.location))[:5]
        }

        # Create digest
        digest = RecommendationDigest(
            digest_type="daily",
            digest_date=datetime.utcnow(),
            job_ids=current_job_ids,
            total_recommendations=len(recommendations),
            top_recommendation_id=recommendations[0].id if recommendations else None,
            highlights=highlights,
            new_opportunities=new_opportunities,
            sent=False
        )
        self.db.add(digest)
        self.db.commit()

        return digest

    # ==================== Utilities ====================

    def _calculate_confidence(self, job: Job, score: float) -> float:
        """Calculate confidence in recommendation"""
        # Start with base confidence from score
        confidence = score / 100.0

        # Boost confidence if we have more data
        preferences_count = self.db.query(UserPreference).filter(
            UserPreference.is_active == True
        ).count()

        if preferences_count > 10:
            confidence = min(1.0, confidence + 0.1)
        if preferences_count > 20:
            confidence = min(1.0, confidence + 0.1)

        # Reduce confidence for very new jobs (less data)
        if job.posted_date:
            days_old = (datetime.utcnow() - job.posted_date).days
            if days_old < 1:
                confidence *= 0.8

        return max(0.0, min(1.0, confidence))

    def calculate_metrics(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> RecommendationMetrics:
        """Calculate recommendation system metrics"""
        recommendations = self.db.query(JobRecommendation).filter(
            JobRecommendation.recommended_at >= period_start,
            JobRecommendation.recommended_at <= period_end
        ).all()

        total = len(recommendations)
        if total == 0:
            # Return empty metrics
            metrics = RecommendationMetrics(
                period_start=period_start,
                period_end=period_end,
                total_recommendations=0,
                recommendations_viewed=0,
                recommendations_clicked=0,
                recommendations_applied=0,
                recommendations_dismissed=0
            )
            self.db.add(metrics)
            self.db.commit()
            return metrics

        viewed = sum(1 for r in recommendations if r.viewed_at)
        clicked = sum(1 for r in recommendations if r.clicked_at)
        applied = sum(1 for r in recommendations if r.was_applied)
        dismissed = sum(1 for r in recommendations if r.dismissed_at)

        # Calculate rates
        ctr = (clicked / viewed * 100) if viewed > 0 else 0
        app_rate = (applied / clicked * 100) if clicked > 0 else 0
        dismiss_rate = (dismissed / total * 100) if total > 0 else 0

        # Quality metrics
        avg_score = sum(r.recommendation_score for r in recommendations) / total
        ratings = [r.user_rating for r in recommendations if r.user_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        # Diversity metrics
        companies = set(r.job.company for r in recommendations if r.job and r.job.company)
        # Note: industries would require job.industry field

        metrics = RecommendationMetrics(
            period_start=period_start,
            period_end=period_end,
            total_recommendations=total,
            recommendations_viewed=viewed,
            recommendations_clicked=clicked,
            recommendations_applied=applied,
            recommendations_dismissed=dismissed,
            click_through_rate=ctr,
            application_rate=app_rate,
            dismissal_rate=dismiss_rate,
            avg_recommendation_score=avg_score,
            avg_user_rating=avg_rating,
            unique_companies=len(companies)
        )

        self.db.add(metrics)
        self.db.commit()
        return metrics
