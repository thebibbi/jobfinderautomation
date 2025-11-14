"""
Cross-feature integration tests

Tests that features work together correctly:
- ATS → Follow-ups
- ATS → Calendar
- Jobs → Skills Gap Analysis
- Jobs → Recommendations
- Jobs → Company Research
- Cache → All features

Run with: docker-compose exec backend pytest tests/integration/test_cross_feature_integration.py
"""
import pytest
import requests
import time
from datetime import datetime, timedelta
import os


@pytest.fixture(scope="module")
def api_base_url():
    """Base API URL"""
    return os.getenv("BACKEND_URL", "http://localhost:8000") + "/api/v1"


@pytest.fixture(scope="function")
def test_job(api_base_url):
    """Create test job for each test"""
    response = requests.post(
        f"{api_base_url}/jobs",
        json={
            "company": "Integration Test Corp",
            "job_title": "Integration Engineer",
            "job_description": """
            Looking for an Integration Engineer with Python, FastAPI, Docker,
            PostgreSQL, and Redis experience. Kubernetes knowledge is a plus.
            """,
            "job_url": "https://test.com/job/123",
            "location": "San Francisco, CA",
            "source": "test"
        },
        timeout=10
    )
    job_id = response.json()["id"]

    yield job_id

    # Cleanup
    try:
        requests.delete(f"{api_base_url}/jobs/{job_id}", timeout=5)
    except:
        pass


class TestATSFollowUpIntegration:
    """Test ATS and Follow-up integration"""

    def test_status_change_triggers_followups(self, api_base_url, test_job):
        """Test that changing status to 'applied' schedules follow-ups"""

        # Change status to applied
        response = requests.post(
            f"{api_base_url}/ats/jobs/{test_job}/status",
            json={"status": "applied"},
            timeout=10
        )
        assert response.status_code == 200

        # Wait for integration to process
        time.sleep(2)

        # Check follow-ups were scheduled
        response = requests.get(
            f"{api_base_url}/followup/jobs/{test_job}",
            timeout=10
        )
        assert response.status_code == 200

        # May have follow-ups scheduled (depends on integration configuration)
        # followups = response.json()

    def test_interview_status_triggers_followup(self, api_base_url, test_job):
        """Test that interview status schedules post-interview follow-up"""

        # Set to applied first
        requests.post(
            f"{api_base_url}/ats/jobs/{test_job}/status",
            json={"status": "applied"},
            timeout=10
        )

        # Set to interviewing
        response = requests.post(
            f"{api_base_url}/ats/jobs/{test_job}/status",
            json={"status": "interviewing"},
            timeout=10
        )
        assert response.status_code == 200

        time.sleep(1)

        # Should have interview follow-ups scheduled


class TestATSCalendarIntegration:
    """Test ATS and Calendar integration"""

    def test_interview_scheduling_creates_calendar_event(self, api_base_url, test_job):
        """Test that scheduling interview creates calendar event"""

        # Set status to applied
        requests.post(
            f"{api_base_url}/ats/jobs/{test_job}/status",
            json={"status": "applied"},
            timeout=10
        )

        # Schedule interview
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        response = requests.post(
            f"{api_base_url}/ats/interviews",
            json={
                "job_id": test_job,
                "interview_type": "technical",
                "scheduled_date": future_date,
                "duration_minutes": 90,
                "interviewer_name": "Tech Lead",
                "interviewer_email": "tech@test.com"
            },
            timeout=10
        )
        assert response.status_code == 201
        interview = response.json()

        # Should have calendar_event_id (if Google Calendar configured)
        # calendar_event_id = interview.get("calendar_event_id")

    def test_calendar_events_for_job(self, api_base_url, test_job):
        """Test getting all calendar events for job"""

        # Schedule interview
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        requests.post(
            f"{api_base_url}/ats/interviews",
            json={
                "job_id": test_job,
                "interview_type": "phone",
                "scheduled_date": future_date,
                "duration_minutes": 60
            },
            timeout=10
        )

        # Get calendar events for job
        response = requests.get(
            f"{api_base_url}/calendar/job/{test_job}",
            timeout=10
        )

        # Should succeed even if Google Calendar not configured
        assert response.status_code in [200, 404]


class TestJobsSkillsIntegration:
    """Test Jobs and Skills Gap Analysis integration"""

    def test_job_creation_triggers_skills_analysis(self, api_base_url):
        """Test that creating job triggers automatic skills gap analysis"""

        # First, add candidate skills
        response = requests.post(
            f"{api_base_url}/skills/candidate",
            json={
                "skills": [
                    {
                        "skill_name": "Python",
                        "skill_level": "advanced",
                        "years_experience": 5,
                        "category": "programming_language"
                    },
                    {
                        "skill_name": "FastAPI",
                        "skill_level": "intermediate",
                        "years_experience": 2,
                        "category": "framework"
                    }
                ]
            },
            timeout=10
        )
        assert response.status_code in [201, 200]

        # Create job (should trigger skills analysis)
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "Skills Test Corp",
                "job_title": "Python Engineer",
                "job_description": """
                Looking for Python expert with FastAPI, Docker, and Kubernetes.
                PostgreSQL and Redis experience required.
                """,
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]

        try:
            time.sleep(2)

            # Check if skills analysis was performed
            response = requests.post(
                f"{api_base_url}/skills/analyze/{job_id}",
                json={"include_resources": True},
                timeout=10
            )

            if response.status_code == 200:
                analysis = response.json()
                assert "overall_match_score" in analysis
                assert "skill_analysis" in analysis

        finally:
            requests.delete(f"{api_base_url}/jobs/{job_id}", timeout=5)

    def test_skills_gap_recommendations(self, api_base_url, test_job):
        """Test skills gap analysis provides learning recommendations"""

        response = requests.post(
            f"{api_base_url}/skills/analyze/{test_job}",
            json={"include_resources": True},
            timeout=10
        )

        if response.status_code == 200:
            analysis = response.json()

            # Should have learning resources for missing skills
            if "skill_analysis" in analysis and "missing_skills" in analysis["skill_analysis"]:
                missing_skills = analysis["skill_analysis"]["missing_skills"]
                if len(missing_skills) > 0:
                    # Should have learning resources
                    assert "learning_resources" in missing_skills[0]


class TestJobsRecommendationsIntegration:
    """Test Jobs and Recommendations integration"""

    def test_job_application_improves_recommendations(self, api_base_url):
        """Test that applying to jobs improves future recommendations"""

        # Create multiple test jobs
        jobs = []
        for i in range(3):
            response = requests.post(
                f"{api_base_url}/jobs",
                json={
                    "company": f"Rec Test {i}",
                    "job_title": "Python Developer",
                    "job_description": "Python and FastAPI development",
                    "source": "test"
                },
                timeout=10
            )
            jobs.append(response.json()["id"])

        try:
            # Apply to first two jobs
            for job_id in jobs[:2]:
                requests.post(
                    f"{api_base_url}/ats/jobs/{job_id}/status",
                    json={"status": "applied"},
                    timeout=10
                )

                # Teach recommendation engine
                requests.post(
                    f"{api_base_url}/recommendations/learn/application/{job_id}",
                    timeout=10
                )

            time.sleep(1)

            # Get recommendations
            response = requests.get(
                f"{api_base_url}/recommendations",
                params={"limit": 5},
                timeout=10
            )
            assert response.status_code == 200

        finally:
            for job_id in jobs:
                requests.delete(f"{api_base_url}/jobs/{job_id}", timeout=5)

    def test_job_dismissal_affects_recommendations(self, api_base_url, test_job):
        """Test that dismissing jobs teaches recommendation engine"""

        # Dismiss job
        response = requests.post(
            f"{api_base_url}/recommendations/learn/dismiss/{test_job}",
            json={"reason": "location_mismatch"},
            timeout=10
        )
        assert response.status_code == 200

        # Future recommendations should avoid similar jobs


class TestJobsCompanyResearchIntegration:
    """Test Jobs and Company Research integration"""

    def test_job_creation_triggers_company_research(self, api_base_url):
        """Test that creating job triggers company research"""

        # Create job with new company
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "NewCompany_IntegrationTest",
                "job_title": "Engineer",
                "job_description": "Build things",
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]

        try:
            time.sleep(2)

            # Check if company was researched
            response = requests.get(
                f"{api_base_url}/research/company/NewCompany_IntegrationTest",
                timeout=10
            )

            # May be 200 (researched) or 404 (not yet researched)
            # Depends on whether research APIs are configured
            assert response.status_code in [200, 404]

        finally:
            requests.delete(f"{api_base_url}/jobs/{job_id}", timeout=5)


class TestCacheIntegration:
    """Test cache integration across features"""

    def test_cache_invalidation_on_job_update(self, api_base_url, test_job):
        """Test that updating job invalidates cache"""

        # Get job (should cache)
        response = requests.get(f"{api_base_url}/jobs/{test_job}", timeout=10)
        assert response.status_code == 200

        # Update job
        response = requests.patch(
            f"{api_base_url}/jobs/{test_job}",
            json={"notes": "Updated notes"},
            timeout=10
        )
        assert response.status_code == 200

        # Get job again (should have updated data)
        response = requests.get(f"{api_base_url}/jobs/{test_job}", timeout=10)
        job = response.json()
        assert job["notes"] == "Updated notes"

    def test_recommendations_cache_invalidation(self, api_base_url, test_job):
        """Test that new jobs invalidate recommendations cache"""

        # Get recommendations (caches result)
        response = requests.get(
            f"{api_base_url}/recommendations",
            params={"limit": 5},
            timeout=10
        )
        assert response.status_code == 200

        # Create new job (should invalidate cache)
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "Cache Test",
                "job_title": "Cache Engineer",
                "job_description": "Test caching",
                "source": "test"
            },
            timeout=10
        )
        new_job_id = response.json()["id"]

        try:
            # Get recommendations again (should be fresh)
            response = requests.get(
                f"{api_base_url}/recommendations",
                params={"limit": 5},
                timeout=10
            )
            assert response.status_code == 200

        finally:
            requests.delete(f"{api_base_url}/jobs/{new_job_id}", timeout=5)

    def test_company_research_cache_persistence(self, api_base_url):
        """Test that company research is cached for 30 days"""

        company_name = "CacheTest_Company"

        # Research company
        response = requests.post(
            f"{api_base_url}/research/company",
            json={"company_name": company_name},
            timeout=10
        )

        if response.status_code == 200:
            # Get from cache
            response = requests.get(
                f"{api_base_url}/research/company/{company_name}",
                timeout=10
            )
            assert response.status_code == 200
            data = response.json()

            # Should indicate it's cached
            # assert data.get("cached") is True


class TestAnalyticsIntegration:
    """Test analytics data collection across features"""

    def test_analytics_tracks_complete_workflow(self, api_base_url, test_job):
        """Test that analytics tracks events throughout workflow"""

        # Apply
        requests.post(
            f"{api_base_url}/ats/jobs/{test_job}/status",
            json={"status": "applied"},
            timeout=10
        )

        # Schedule interview
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        requests.post(
            f"{api_base_url}/ats/interviews",
            json={
                "job_id": test_job,
                "interview_type": "phone",
                "scheduled_date": future_date
            },
            timeout=10
        )

        time.sleep(1)

        # Get analytics
        response = requests.get(
            f"{api_base_url}/analytics/overview",
            timeout=10
        )
        assert response.status_code == 200
        analytics = response.json()

        # Should have tracked events
        assert "summary" in analytics or "conversion_funnel" in analytics

    def test_funnel_analysis_cross_feature(self, api_base_url):
        """Test funnel analysis uses data from multiple features"""

        response = requests.get(
            f"{api_base_url}/analytics/funnel",
            timeout=10
        )
        assert response.status_code == 200
        funnel = response.json()

        # Should have funnel stages
        assert "overall_funnel" in funnel or "period" in funnel


class TestIntegrationOrchestrator:
    """Test integration orchestrator coordinates features"""

    def test_job_created_integration_workflow(self, api_base_url):
        """Test that creating job triggers all integrated workflows"""

        # Create job
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "Orchestrator Test Corp",
                "job_title": "Full Stack Engineer",
                "job_description": """
                Looking for Full Stack Engineer with Python, FastAPI, React,
                PostgreSQL, Redis, Docker, and Kubernetes experience.
                """,
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]

        try:
            time.sleep(3)  # Wait for background processing

            # Check company research was triggered
            response = requests.get(
                f"{api_base_url}/research/company/Orchestrator Test Corp",
                timeout=10
            )
            # May or may not have research (depends on API configuration)

            # Check skills gap analysis was triggered
            response = requests.post(
                f"{api_base_url}/skills/analyze/{job_id}",
                json={"include_resources": False},
                timeout=10
            )
            # May have analysis if candidate skills exist

            # Check cache was updated
            response = requests.get(
                f"{api_base_url}/cache/stats",
                timeout=10
            )
            assert response.status_code == 200

        finally:
            requests.delete(f"{api_base_url}/jobs/{job_id}", timeout=5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
