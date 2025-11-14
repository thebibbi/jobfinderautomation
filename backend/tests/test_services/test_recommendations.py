"""
Tests for Recommendation Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.recommendation_service import RecommendationService
from app.models.recommendations import (
    UserPreference, JobRecommendation, RecommendationFeedback,
    RecommendationDigest, SimilarJob
)
from app.models.job import Job
from app.models.application import ApplicationEvent


class TestRecommendationGeneration:
    """Test recommendation generation algorithms"""

    def test_get_recommendations_with_no_jobs(self, db_session):
        """Should handle no available jobs gracefully"""
        service = RecommendationService(db_session)

        recommendations = service.get_recommendations(limit=10)

        assert len(recommendations) == 0

    def test_get_recommendations_basic(self, db_session, create_test_job):
        """Should generate basic recommendations"""
        # Create test jobs
        job1 = create_test_job(title="Senior Python Developer", company="TechCorp")
        job2 = create_test_job(title="Junior Python Developer", company="StartupCo")
        job3 = create_test_job(title="Data Scientist", company="DataInc")

        service = RecommendationService(db_session)

        recommendations = service.get_recommendations(
            limit=3,
            algorithm="content_based"
        )

        assert len(recommendations) <= 3
        assert all(isinstance(r, JobRecommendation) for r in recommendations)
        assert all(r.recommendation_score >= 0 for r in recommendations)
        assert all(r.confidence >= 0 for r in recommendations)

    def test_content_based_filtering(self, db_session, create_test_job):
        """Should use content-based filtering correctly"""
        # Create jobs
        job1 = create_test_job(title="Python Developer", company="TechCorp", location="Remote")
        job2 = create_test_job(title="Java Developer", company="JavaInc", location="New York")

        # Create user preferences
        pref1 = UserPreference(
            preference_type="job_title_keyword",
            preference_value="python",
            preference_score=0.9,
            confidence=0.8,
            learned_from="applications",
            sample_size=5
        )
        pref2 = UserPreference(
            preference_type="remote",
            preference_value="true",
            preference_score=0.8,
            confidence=0.7,
            learned_from="applications",
            sample_size=3
        )
        db_session.add_all([pref1, pref2])
        db_session.commit()

        service = RecommendationService(db_session)

        recommendations = service.get_recommendations(
            limit=10,
            algorithm="content_based"
        )

        # Python + Remote job should score higher
        scores = {r.job_id: r.recommendation_score for r in recommendations}
        assert scores[job1.id] > scores[job2.id]

    def test_collaborative_filtering_with_history(self, db_session, create_test_job):
        """Should use collaborative filtering with application history"""
        # Create jobs
        job1 = create_test_job(title="Python Dev", company="A")
        job2 = create_test_job(title="Python Engineer", company="B")
        job3 = create_test_job(title="Java Dev", company="C")

        # Create application history
        event1 = ApplicationEvent(
            job_id=job1.id,
            event_type="status_change",
            old_status="discovered",
            new_status="applied"
        )
        event2 = ApplicationEvent(
            job_id=job2.id,
            event_type="status_change",
            old_status="discovered",
            new_status="applied"
        )
        db_session.add_all([event1, event2])
        db_session.commit()

        service = RecommendationService(db_session)

        # Collaborative filtering should use history
        recommendations = service.get_recommendations(
            limit=10,
            algorithm="collaborative",
            filter_applied=True  # Don't recommend already applied jobs
        )

        # Should not recommend already applied jobs
        recommended_ids = [r.job_id for r in recommendations]
        assert job1.id not in recommended_ids
        assert job2.id not in recommended_ids

    def test_hybrid_recommendations(self, db_session, create_test_job):
        """Should combine collaborative and content-based filtering"""
        # Create jobs
        job1 = create_test_job(title="Python Developer", company="TechCorp")
        job2 = create_test_job(title="Java Developer", company="JavaCorp")

        # Create preference for Python
        pref = UserPreference(
            preference_type="job_title_keyword",
            preference_value="python",
            preference_score=0.9,
            confidence=0.8,
            learned_from="applications",
            sample_size=5
        )
        db_session.add(pref)
        db_session.commit()

        service = RecommendationService(db_session)

        recommendations = service.get_recommendations(
            limit=10,
            algorithm="hybrid"
        )

        # Should have recommendations
        assert len(recommendations) > 0
        assert all(r.match_factors is not None for r in recommendations)

    def test_min_score_filtering(self, db_session, create_test_job):
        """Should filter recommendations by minimum score"""
        # Create jobs
        job1 = create_test_job(title="Python Dev", company="A")
        job2 = create_test_job(title="Java Dev", company="B")

        # Create strong Python preference
        pref = UserPreference(
            preference_type="job_title_keyword",
            preference_value="python",
            preference_score=0.9,
            confidence=0.9,
            learned_from="applications",
            sample_size=10
        )
        db_session.add(pref)
        db_session.commit()

        service = RecommendationService(db_session)

        # Request only high-scoring recommendations
        recommendations = service.get_recommendations(
            limit=10,
            algorithm="content_based",
            min_score=80.0
        )

        # All recommendations should meet minimum score
        assert all(r.recommendation_score >= 80.0 for r in recommendations)

    def test_recommendation_expiration(self, db_session, create_test_job):
        """Should set expiration dates on recommendations"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        service = RecommendationService(db_session)

        recommendations = service.get_recommendations(limit=1)

        assert len(recommendations) == 1
        assert recommendations[0].expires_at is not None
        # Should expire in 14 days
        days_until_expiry = (recommendations[0].expires_at - datetime.utcnow()).days
        assert 13 <= days_until_expiry <= 15


class TestPreferenceLearning:
    """Test preference learning from user behavior"""

    def test_learn_from_application(self, db_session, create_test_job):
        """Should learn preferences when user applies to a job"""
        job = create_test_job(
            title="Senior Python Developer",
            company="TechCorp",
            location="Remote"
        )

        service = RecommendationService(db_session)
        service.learn_from_application(job.id)

        # Should have learned preferences
        preferences = db_session.query(UserPreference).all()
        assert len(preferences) > 0

        # Should learn company preference
        company_pref = db_session.query(UserPreference).filter(
            UserPreference.preference_type == "company",
            UserPreference.preference_value == "TechCorp"
        ).first()
        assert company_pref is not None
        assert company_pref.preference_score > 0.5

        # Should learn remote preference
        remote_pref = db_session.query(UserPreference).filter(
            UserPreference.preference_type == "remote",
            UserPreference.preference_value == "true"
        ).first()
        assert remote_pref is not None

    def test_learn_from_click(self, db_session, create_test_job):
        """Should learn preferences from clicks (weaker signal)"""
        job = create_test_job(
            title="Python Developer",
            company="ClickCorp",
            location="New York"
        )

        service = RecommendationService(db_session)
        service.learn_from_click(job.id)

        # Should have learned preferences
        company_pref = db_session.query(UserPreference).filter(
            UserPreference.preference_type == "company",
            UserPreference.preference_value == "ClickCorp"
        ).first()
        assert company_pref is not None
        # Click should give lower score than application
        assert company_pref.preference_score < 0.5

    def test_learn_from_dismissal(self, db_session, create_test_job):
        """Should learn negative preferences from dismissals"""
        job = create_test_job(
            title="Java Developer",
            company="JavaCorp",
            location="On-site"
        )

        # First create a positive preference
        pref = UserPreference(
            preference_type="company",
            preference_value="JavaCorp",
            preference_score=0.7,
            confidence=0.6,
            learned_from="applications",
            sample_size=2
        )
        db_session.add(pref)
        db_session.commit()

        initial_score = pref.preference_score

        service = RecommendationService(db_session)
        service.learn_from_dismissal(job.id, "not interested")

        # Should have decreased preference
        db_session.refresh(pref)
        assert pref.preference_score < initial_score

    def test_preference_confidence_increases(self, db_session, create_test_job):
        """Should increase confidence with more data points"""
        job = create_test_job(title="Python Dev", company="TechCorp")

        service = RecommendationService(db_session)

        # Learn multiple times
        for _ in range(5):
            service.learn_from_application(job.id)

        pref = db_session.query(UserPreference).filter(
            UserPreference.preference_type == "company",
            UserPreference.preference_value == "TechCorp"
        ).first()

        assert pref.sample_size >= 5
        assert pref.confidence > 0.3  # Should have increased from initial

    def test_preference_score_bounds(self, db_session):
        """Should keep preference scores within 0-1 range"""
        service = RecommendationService(db_session)

        # Try to push score above 1
        for _ in range(10):
            service._update_preference("company", "TestCorp", 0.5, "applications")

        pref = db_session.query(UserPreference).filter(
            UserPreference.preference_value == "TestCorp"
        ).first()

        assert 0.0 <= pref.preference_score <= 1.0


class TestFeedback:
    """Test recommendation feedback system"""

    def test_record_positive_feedback(self, db_session, create_test_job):
        """Should record positive feedback"""
        job = create_test_job(title="Python Dev", company="TechCorp")

        # Create recommendation
        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="viewed"
        )
        db_session.add(rec)
        db_session.commit()

        service = RecommendationService(db_session)

        feedback = service.record_feedback(
            recommendation_id=rec.id,
            feedback_type="helpful",
            rating=5
        )

        assert feedback.recommendation_id == rec.id
        assert feedback.rating == 5

        # Should have learned from positive feedback
        db_session.refresh(rec)
        assert rec.user_rating == 5

    def test_record_negative_feedback(self, db_session, create_test_job):
        """Should record negative feedback and learn"""
        job = create_test_job(title="Java Dev", company="JavaCorp")

        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=75.0,
            confidence=0.7,
            status="viewed"
        )
        db_session.add(rec)
        db_session.commit()

        service = RecommendationService(db_session)

        feedback = service.record_feedback(
            recommendation_id=rec.id,
            feedback_type="not_helpful",
            feedback_text="Wrong technology stack",
            rating=1
        )

        assert feedback.feedback_type == "not_helpful"
        assert feedback.rating == 1

    def test_feedback_invalid_recommendation(self, db_session):
        """Should raise error for invalid recommendation ID"""
        service = RecommendationService(db_session)

        with pytest.raises(ValueError, match="not found"):
            service.record_feedback(
                recommendation_id=99999,
                feedback_type="helpful"
            )


class TestSimilarJobs:
    """Test similar job finding"""

    def test_find_similar_jobs(self, db_session, create_test_job):
        """Should find similar jobs"""
        job1 = create_test_job(
            title="Senior Python Developer",
            company="TechCorp",
            location="Remote"
        )
        job2 = create_test_job(
            title="Senior Python Engineer",
            company="TechCorp",
            location="Remote"
        )
        job3 = create_test_job(
            title="Junior Java Developer",
            company="JavaInc",
            location="New York"
        )

        service = RecommendationService(db_session)

        similar = service.find_similar_jobs(job1.id, limit=5)

        # Should find similar jobs
        assert len(similar) > 0

        # Job2 should be more similar than Job3
        similar_ids = [s.similar_job_id for s in similar]
        if job2.id in similar_ids and job3.id in similar_ids:
            job2_idx = similar_ids.index(job2.id)
            job3_idx = similar_ids.index(job3.id)
            assert job2_idx < job3_idx  # Job2 should come first

    def test_similarity_calculation(self, db_session, create_test_job):
        """Should calculate similarity correctly"""
        job1 = create_test_job(
            title="Python Developer",
            company="TechCorp",
            location="Remote"
        )
        job2 = create_test_job(
            title="Python Developer",
            company="TechCorp",
            location="Remote"
        )

        service = RecommendationService(db_session)

        score, factors = service._calculate_similarity(job1, job2)

        # Identical jobs should have high similarity
        assert score > 0.5
        assert "title_overlap" in factors
        assert factors.get("same_company") == True
        assert factors.get("same_location") == True

    def test_similar_jobs_caching(self, db_session, create_test_job):
        """Should cache similar job results"""
        job1 = create_test_job(title="Python Developer", company="A")
        job2 = create_test_job(title="Python Engineer", company="B")

        service = RecommendationService(db_session)

        # First call - calculates
        similar1 = service.find_similar_jobs(job1.id, limit=5)

        # Second call - should use cache
        similar2 = service.find_similar_jobs(job1.id, limit=5)

        assert len(similar1) == len(similar2)
        assert [s.similar_job_id for s in similar1] == [s.similar_job_id for s in similar2]


class TestDigests:
    """Test recommendation digests"""

    def test_generate_daily_digest(self, db_session, create_test_job):
        """Should generate daily digest"""
        # Create recent recommendations
        job = create_test_job(title="Python Developer", company="TechCorp")

        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="pending",
            recommended_at=datetime.utcnow()
        )
        db_session.add(rec)
        db_session.commit()

        service = RecommendationService(db_session)

        digest = service.generate_daily_digest()

        assert digest is not None
        assert digest.digest_type == "daily"
        assert len(digest.job_ids) > 0
        assert digest.total_recommendations > 0

    def test_digest_with_no_recommendations(self, db_session):
        """Should handle no new recommendations"""
        service = RecommendationService(db_session)

        digest = service.generate_daily_digest()

        assert digest is None

    def test_digest_highlights(self, db_session, create_test_job):
        """Should include highlights in digest"""
        job1 = create_test_job(title="Python Dev", company="TechCorp", location="Remote")
        job2 = create_test_job(title="Java Dev", company="JavaInc", location="New York")

        rec1 = JobRecommendation(
            job_id=job1.id,
            recommendation_score=90.0,
            confidence=0.85,
            status="pending",
            recommended_at=datetime.utcnow()
        )
        rec2 = JobRecommendation(
            job_id=job2.id,
            recommendation_score=80.0,
            confidence=0.75,
            status="pending",
            recommended_at=datetime.utcnow()
        )
        db_session.add_all([rec1, rec2])
        db_session.commit()

        service = RecommendationService(db_session)

        digest = service.generate_daily_digest()

        assert digest.highlights is not None
        assert "avg_score" in digest.highlights
        assert "top_companies" in digest.highlights


class TestMetrics:
    """Test recommendation metrics"""

    def test_calculate_metrics(self, db_session, create_test_job):
        """Should calculate recommendation metrics"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        # Create recommendations with various statuses
        now = datetime.utcnow()

        rec1 = JobRecommendation(
            job_id=job.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="viewed",
            recommended_at=now - timedelta(days=2),
            viewed_at=now - timedelta(days=2)
        )
        rec2 = JobRecommendation(
            job_id=job.id,
            recommendation_score=90.0,
            confidence=0.85,
            status="clicked",
            recommended_at=now - timedelta(days=1),
            viewed_at=now - timedelta(days=1),
            clicked_at=now - timedelta(days=1)
        )
        rec3 = JobRecommendation(
            job_id=job.id,
            recommendation_score=75.0,
            confidence=0.7,
            status="applied",
            recommended_at=now - timedelta(days=1),
            was_applied=True
        )

        db_session.add_all([rec1, rec2, rec3])
        db_session.commit()

        service = RecommendationService(db_session)

        period_start = now - timedelta(days=7)
        period_end = now

        metrics = service.calculate_metrics(period_start, period_end)

        assert metrics.total_recommendations == 3
        assert metrics.recommendations_viewed > 0
        assert metrics.recommendations_clicked > 0
        assert metrics.recommendations_applied > 0
        assert metrics.avg_recommendation_score > 0

    def test_metrics_empty_period(self, db_session):
        """Should handle period with no recommendations"""
        service = RecommendationService(db_session)

        period_start = datetime.utcnow() - timedelta(days=7)
        period_end = datetime.utcnow()

        metrics = service.calculate_metrics(period_start, period_end)

        assert metrics.total_recommendations == 0
        assert metrics.recommendations_viewed == 0


class TestConfidenceCalculation:
    """Test confidence calculation"""

    def test_confidence_increases_with_preferences(self, db_session, create_test_job):
        """Should increase confidence with more learned preferences"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        # Create many preferences
        for i in range(15):
            pref = UserPreference(
                preference_type="test",
                preference_value=f"value_{i}",
                preference_score=0.7,
                confidence=0.8,
                learned_from="applications",
                sample_size=5
            )
            db_session.add(pref)
        db_session.commit()

        service = RecommendationService(db_session)

        confidence = service._calculate_confidence(job, 80.0)

        # Should have higher confidence with many preferences
        assert confidence > 0.8

    def test_confidence_reduced_for_new_jobs(self, db_session, create_test_job):
        """Should reduce confidence for very new jobs"""
        # Job posted today
        job_new = create_test_job(
            title="Python Developer",
            company="TechCorp",
            posted_date=datetime.utcnow()
        )

        # Job posted a week ago
        job_old = create_test_job(
            title="Java Developer",
            company="JavaInc",
            posted_date=datetime.utcnow() - timedelta(days=7)
        )

        service = RecommendationService(db_session)

        conf_new = service._calculate_confidence(job_new, 80.0)
        conf_old = service._calculate_confidence(job_old, 80.0)

        # New job should have lower confidence
        assert conf_new < conf_old
