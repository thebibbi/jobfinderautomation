"""
Tests for Recommendations API
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.models.recommendations import (
    UserPreference, JobRecommendation, RecommendationFeedback
)
from app.models.job import Job


class TestGenerateRecommendations:
    """Test recommendation generation endpoint"""

    def test_generate_recommendations_success(self, client, db_session, create_test_job):
        """Should generate recommendations successfully"""
        # Create test jobs
        job1 = create_test_job(title="Python Developer", company="TechCorp")
        job2 = create_test_job(title="Java Developer", company="JavaInc")

        # Create preferences
        pref = UserPreference(
            preference_type="job_title_keyword",
            preference_value="python",
            preference_score=0.8,
            confidence=0.7,
            learned_from="applications",
            sample_size=3
        )
        db_session.add(pref)
        db_session.commit()

        response = client.post("/api/v1/recommendations/generate", json={
            "limit": 10,
            "algorithm": "hybrid",
            "include_reasons": True,
            "filter_applied": False,
            "min_score": 50.0
        })

        assert response.status_code == 200
        data = response.json()

        assert "recommendations" in data
        assert "total_available" in data
        assert "algorithm_used" in data
        assert "preferences_learned" in data

        assert data["algorithm_used"] == "hybrid"
        assert data["preferences_learned"] > 0
        assert len(data["recommendations"]) > 0

        # Check recommendation structure
        rec = data["recommendations"][0]
        assert "job_id" in rec
        assert "recommendation_score" in rec
        assert "confidence" in rec
        assert "job_title" in rec
        assert "company" in rec

    def test_generate_recommendations_collaborative(self, client, db_session, create_test_job):
        """Should generate recommendations using collaborative filtering"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        response = client.post("/api/v1/recommendations/generate", json={
            "limit": 5,
            "algorithm": "collaborative"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["algorithm_used"] == "collaborative"

    def test_generate_recommendations_content_based(self, client, db_session, create_test_job):
        """Should generate recommendations using content-based filtering"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        response = client.post("/api/v1/recommendations/generate", json={
            "limit": 5,
            "algorithm": "content_based"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["algorithm_used"] == "content_based"

    def test_generate_recommendations_min_score(self, client, db_session, create_test_job):
        """Should filter by minimum score"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        response = client.post("/api/v1/recommendations/generate", json={
            "limit": 10,
            "min_score": 80.0
        })

        assert response.status_code == 200
        data = response.json()

        # All recommendations should meet minimum score
        for rec in data["recommendations"]:
            assert rec["recommendation_score"] >= 80.0

    def test_generate_recommendations_no_jobs(self, client, db_session):
        """Should handle case with no jobs"""
        response = client.post("/api/v1/recommendations/generate", json={
            "limit": 10
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 0


class TestGetRecommendations:
    """Test get active recommendations endpoint"""

    def test_get_active_recommendations(self, client, db_session, create_test_job):
        """Should get active recommendations"""
        job1 = create_test_job(title="Python Developer", company="TechCorp")
        job2 = create_test_job(title="Java Developer", company="JavaInc")

        # Create recommendations
        rec1 = JobRecommendation(
            job_id=job1.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="pending"
        )
        rec2 = JobRecommendation(
            job_id=job2.id,
            recommendation_score=75.0,
            confidence=0.7,
            status="viewed"
        )
        db_session.add_all([rec1, rec2])
        db_session.commit()

        response = client.get("/api/v1/recommendations/")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert all("job_title" in rec for rec in data)

    def test_get_recommendations_by_status(self, client, db_session, create_test_job):
        """Should filter recommendations by status"""
        job1 = create_test_job(title="Python Developer", company="TechCorp")
        job2 = create_test_job(title="Java Developer", company="JavaInc")

        rec1 = JobRecommendation(
            job_id=job1.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="pending"
        )
        rec2 = JobRecommendation(
            job_id=job2.id,
            recommendation_score=75.0,
            confidence=0.7,
            status="dismissed"
        )
        db_session.add_all([rec1, rec2])
        db_session.commit()

        response = client.get("/api/v1/recommendations/?status=pending")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["status"] == "pending"

    def test_get_recommendations_excludes_expired(self, client, db_session, create_test_job):
        """Should exclude expired recommendations"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        # Expired recommendation
        expired_rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="pending",
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(expired_rec)
        db_session.commit()

        response = client.get("/api/v1/recommendations/")

        assert response.status_code == 200
        data = response.json()

        # Should not include expired recommendation
        assert len(data) == 0


class TestRecommendationActions:
    """Test recommendation action endpoints"""

    def test_mark_viewed(self, client, db_session, create_test_job):
        """Should mark recommendation as viewed"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="pending"
        )
        db_session.add(rec)
        db_session.commit()

        response = client.post(f"/api/v1/recommendations/{rec.id}/view")

        assert response.status_code == 200

        # Check updated
        db_session.refresh(rec)
        assert rec.status == "viewed"
        assert rec.viewed_at is not None

    def test_mark_clicked(self, client, db_session, create_test_job):
        """Should mark recommendation as clicked"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="pending"
        )
        db_session.add(rec)
        db_session.commit()

        response = client.post(f"/api/v1/recommendations/{rec.id}/click")

        assert response.status_code == 200

        # Check updated
        db_session.refresh(rec)
        assert rec.status == "clicked"
        assert rec.clicked_at is not None
        assert rec.viewed_at is not None  # Should also mark as viewed

    def test_mark_applied(self, client, db_session, create_test_job):
        """Should mark recommendation as applied"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="viewed"
        )
        db_session.add(rec)
        db_session.commit()

        response = client.post(f"/api/v1/recommendations/{rec.id}/apply")

        assert response.status_code == 200

        # Check updated
        db_session.refresh(rec)
        assert rec.was_applied == True
        assert rec.status == "applied"

        # Should have learned from application
        preferences = db_session.query(UserPreference).all()
        assert len(preferences) > 0

    def test_dismiss_recommendation(self, client, db_session, create_test_job):
        """Should dismiss recommendation"""
        job = create_test_job(title="Java Developer", company="JavaInc")

        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=70.0,
            confidence=0.6,
            status="viewed"
        )
        db_session.add(rec)
        db_session.commit()

        response = client.post(
            f"/api/v1/recommendations/{rec.id}/dismiss",
            params={"reason": "Wrong technology"}
        )

        assert response.status_code == 200

        # Check updated
        db_session.refresh(rec)
        assert rec.status == "dismissed"
        assert rec.dismissed_at is not None
        assert rec.dismissal_reason == "Wrong technology"

    def test_action_on_nonexistent_recommendation(self, client, db_session):
        """Should return 404 for nonexistent recommendation"""
        response = client.post("/api/v1/recommendations/99999/view")

        assert response.status_code == 404


class TestFeedback:
    """Test feedback endpoints"""

    def test_submit_positive_feedback(self, client, db_session, create_test_job):
        """Should submit positive feedback"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=90.0,
            confidence=0.85,
            status="viewed"
        )
        db_session.add(rec)
        db_session.commit()

        response = client.post("/api/v1/recommendations/feedback", json={
            "recommendation_id": rec.id,
            "feedback_type": "helpful",
            "rating": 5
        })

        assert response.status_code == 200
        data = response.json()

        assert data["recommendation_id"] == rec.id
        assert data["feedback_type"] == "helpful"
        assert data["rating"] == 5

    def test_submit_negative_feedback(self, client, db_session, create_test_job):
        """Should submit negative feedback"""
        job = create_test_job(title="Java Developer", company="JavaInc")

        rec = JobRecommendation(
            job_id=job.id,
            recommendation_score=70.0,
            confidence=0.7,
            status="viewed"
        )
        db_session.add(rec)
        db_session.commit()

        response = client.post("/api/v1/recommendations/feedback", json={
            "recommendation_id": rec.id,
            "feedback_type": "not_helpful",
            "feedback_text": "Wrong skills required",
            "rating": 2
        })

        assert response.status_code == 200
        data = response.json()

        assert data["feedback_type"] == "not_helpful"
        assert data["rating"] == 2

    def test_feedback_invalid_recommendation(self, client, db_session):
        """Should return 404 for invalid recommendation"""
        response = client.post("/api/v1/recommendations/feedback", json={
            "recommendation_id": 99999,
            "feedback_type": "helpful"
        })

        assert response.status_code == 404


class TestSimilarJobs:
    """Test similar jobs endpoint"""

    def test_get_similar_jobs(self, client, db_session, create_test_job):
        """Should get similar jobs"""
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

        response = client.get(f"/api/v1/recommendations/similar/{job1.id}")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            similar = data[0]
            assert "similar_job_id" in similar
            assert "similarity_score" in similar
            assert "similar_job_title" in similar
            assert "similar_job_company" in similar

    def test_get_similar_jobs_limit(self, client, db_session, create_test_job):
        """Should respect limit parameter"""
        job1 = create_test_job(title="Python Developer", company="A")

        # Create many similar jobs
        for i in range(10):
            create_test_job(title=f"Python Developer {i}", company=f"Company{i}")

        response = client.get(f"/api/v1/recommendations/similar/{job1.id}?limit=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data) <= 3


class TestDigest:
    """Test recommendation digest endpoints"""

    def test_get_daily_digest(self, client, db_session, create_test_job):
        """Should get daily digest"""
        job1 = create_test_job(title="Python Developer", company="TechCorp")
        job2 = create_test_job(title="Java Developer", company="JavaInc")

        # Create recent recommendations
        rec1 = JobRecommendation(
            job_id=job1.id,
            recommendation_score=90.0,
            confidence=0.85,
            status="pending",
            recommended_at=datetime.utcnow()
        )
        rec2 = JobRecommendation(
            job_id=job2.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="pending",
            recommended_at=datetime.utcnow()
        )
        db_session.add_all([rec1, rec2])
        db_session.commit()

        response = client.get("/api/v1/recommendations/digest/daily")

        assert response.status_code == 200
        data = response.json()

        assert data["digest_type"] == "daily"
        assert data["total_recommendations"] > 0
        assert len(data["job_ids"]) > 0
        assert "jobs" in data
        assert len(data["jobs"]) > 0

    def test_digest_no_recommendations(self, client, db_session):
        """Should handle no recommendations for digest"""
        response = client.get("/api/v1/recommendations/digest/daily")

        assert response.status_code == 404


class TestPreferences:
    """Test preferences endpoints"""

    def test_get_user_preferences(self, client, db_session):
        """Should get user preferences"""
        # Create preferences
        pref1 = UserPreference(
            preference_type="company",
            preference_value="TechCorp",
            preference_score=0.8,
            confidence=0.7,
            learned_from="applications",
            sample_size=5
        )
        pref2 = UserPreference(
            preference_type="location",
            preference_value="Remote",
            preference_score=0.9,
            confidence=0.85,
            learned_from="applications",
            sample_size=8
        )
        db_session.add_all([pref1, pref2])
        db_session.commit()

        response = client.get("/api/v1/recommendations/preferences")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert all("preference_type" in p for p in data)
        assert all("preference_value" in p for p in data)
        assert all("preference_score" in p for p in data)

    def test_get_preferences_by_type(self, client, db_session):
        """Should filter preferences by type"""
        pref1 = UserPreference(
            preference_type="company",
            preference_value="TechCorp",
            preference_score=0.8,
            confidence=0.7,
            learned_from="applications",
            sample_size=5
        )
        pref2 = UserPreference(
            preference_type="location",
            preference_value="Remote",
            preference_score=0.9,
            confidence=0.85,
            learned_from="applications",
            sample_size=8
        )
        db_session.add_all([pref1, pref2])
        db_session.commit()

        response = client.get("/api/v1/recommendations/preferences?preference_type=company")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["preference_type"] == "company"

    def test_update_preference_increase(self, client, db_session):
        """Should increase preference"""
        pref = UserPreference(
            preference_type="company",
            preference_value="TechCorp",
            preference_score=0.5,
            confidence=0.6,
            learned_from="applications",
            sample_size=2
        )
        db_session.add(pref)
        db_session.commit()

        initial_score = pref.preference_score

        response = client.post("/api/v1/recommendations/preferences/update", json={
            "preference_type": "company",
            "preference_value": "TechCorp",
            "action": "increase"
        })

        assert response.status_code == 200

        db_session.refresh(pref)
        assert pref.preference_score > initial_score

    def test_update_preference_decrease(self, client, db_session):
        """Should decrease preference"""
        pref = UserPreference(
            preference_type="company",
            preference_value="TechCorp",
            preference_score=0.8,
            confidence=0.7,
            learned_from="applications",
            sample_size=3
        )
        db_session.add(pref)
        db_session.commit()

        initial_score = pref.preference_score

        response = client.post("/api/v1/recommendations/preferences/update", json={
            "preference_type": "company",
            "preference_value": "TechCorp",
            "action": "decrease"
        })

        assert response.status_code == 200

        db_session.refresh(pref)
        assert pref.preference_score < initial_score

    def test_update_preference_set(self, client, db_session):
        """Should set preference to specific value"""
        pref = UserPreference(
            preference_type="company",
            preference_value="TechCorp",
            preference_score=0.5,
            confidence=0.6,
            learned_from="applications",
            sample_size=2
        )
        db_session.add(pref)
        db_session.commit()

        response = client.post("/api/v1/recommendations/preferences/update", json={
            "preference_type": "company",
            "preference_value": "TechCorp",
            "action": "set",
            "strength": 0.95
        })

        assert response.status_code == 200

        db_session.refresh(pref)
        assert pref.preference_score == 0.95

    def test_create_new_preference(self, client, db_session):
        """Should create new preference if not exists"""
        response = client.post("/api/v1/recommendations/preferences/update", json={
            "preference_type": "company",
            "preference_value": "NewCorp",
            "action": "set",
            "strength": 0.8
        })

        assert response.status_code == 200

        pref = db_session.query(UserPreference).filter(
            UserPreference.preference_value == "NewCorp"
        ).first()

        assert pref is not None
        assert pref.preference_score == 0.8


class TestMetrics:
    """Test metrics endpoint"""

    def test_get_metrics(self, client, db_session, create_test_job):
        """Should get recommendation metrics"""
        job = create_test_job(title="Python Developer", company="TechCorp")

        # Create recommendations
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
        db_session.add_all([rec1, rec2])
        db_session.commit()

        response = client.get("/api/v1/recommendations/metrics?days=7")

        assert response.status_code == 200
        data = response.json()

        assert "total_recommendations" in data
        assert "recommendations_viewed" in data
        assert "recommendations_clicked" in data
        assert "click_through_rate" in data
        assert data["total_recommendations"] == 2


class TestDashboard:
    """Test dashboard endpoint"""

    def test_get_dashboard(self, client, db_session, create_test_job):
        """Should get recommendation dashboard"""
        job1 = create_test_job(title="Python Developer", company="TechCorp")
        job2 = create_test_job(title="Java Developer", company="JavaInc")

        # Create recommendations with various statuses
        rec1 = JobRecommendation(
            job_id=job1.id,
            recommendation_score=90.0,
            confidence=0.85,
            status="pending"
        )
        rec2 = JobRecommendation(
            job_id=job2.id,
            recommendation_score=85.0,
            confidence=0.8,
            status="viewed"
        )
        db_session.add_all([rec1, rec2])
        db_session.commit()

        response = client.get("/api/v1/recommendations/dashboard")

        assert response.status_code == 200
        data = response.json()

        assert "active_recommendations" in data
        assert "pending_recommendations" in data
        assert "viewed_recommendations" in data
        assert "avg_recommendation_score" in data
        assert "click_through_rate" in data
        assert "top_recommendations" in data
        assert isinstance(data["top_recommendations"], list)

    def test_dashboard_empty_state(self, client, db_session):
        """Should handle empty dashboard"""
        response = client.get("/api/v1/recommendations/dashboard")

        assert response.status_code == 200
        data = response.json()

        assert data["active_recommendations"] == 0
        assert data["pending_recommendations"] == 0
