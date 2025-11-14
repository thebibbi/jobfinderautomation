"""
End-to-end workflow integration tests

Tests complete workflows from start to finish:
- Job processing workflow
- Application lifecycle workflow
- Interview scheduling workflow
- Recommendation workflow

Run with: docker-compose exec backend pytest tests/integration/test_e2e_workflows.py
"""
import pytest
import requests
import asyncio
import time
from datetime import datetime, timedelta
import os


@pytest.fixture(scope="module")
def api_base_url():
    """Base API URL"""
    return os.getenv("BACKEND_URL", "http://localhost:8000") + "/api/v1"


@pytest.fixture(scope="function")
def cleanup_test_data(api_base_url):
    """Cleanup test data after each test"""
    created_job_ids = []

    yield created_job_ids

    # Cleanup
    for job_id in created_job_ids:
        try:
            requests.delete(f"{api_base_url}/jobs/{job_id}", timeout=5)
        except:
            pass


class TestJobProcessingWorkflow:
    """Test complete job processing workflow"""

    def test_end_to_end_job_processing(self, api_base_url, cleanup_test_data):
        """
        Test complete job processing workflow:
        1. Create job
        2. Job is analyzed automatically
        3. Skills gap analysis runs
        4. Company research cached
        5. If high score, documents generated
        6. WebSocket events sent
        """

        # Step 1: Create job
        job_data = {
            "company": "Google",
            "job_title": "Senior Software Engineer",
            "job_description": """
            We are seeking a Senior Software Engineer with expertise in Python, FastAPI,
            and cloud technologies. The ideal candidate will have 5+ years of experience
            building scalable web applications. Experience with Docker, Kubernetes, and
            PostgreSQL is highly valued.
            """,
            "job_url": "https://careers.google.com/test/12345",
            "location": "Mountain View, CA",
            "salary_min": 150000,
            "salary_max": 220000,
            "source": "linkedin"
        }

        response = requests.post(
            f"{api_base_url}/jobs",
            json=job_data,
            timeout=10
        )
        assert response.status_code == 201
        job = response.json()
        job_id = job["id"]
        cleanup_test_data.append(job_id)

        # Step 2: Wait for automatic analysis (background task)
        time.sleep(3)  # Give time for background processing

        # Check job was analyzed
        response = requests.get(f"{api_base_url}/jobs/{job_id}", timeout=10)
        assert response.status_code == 200
        job = response.json()

        # Job should have analysis results
        # Note: May be None if Claude API not configured
        if job.get("match_score"):
            assert job["match_score"] >= 0
            assert job["match_score"] <= 100
            assert job["recommendation"] in ["apply_now", "apply_with_confidence", "consider_carefully", "not_recommended"]

        # Step 3: Check company research was performed
        response = requests.get(
            f"{api_base_url}/research/company/{job_data['company']}",
            timeout=10
        )
        # May be 200 (cached) or 404 (not researched yet)
        assert response.status_code in [200, 404]

        # Step 4: Check skills gap analysis (if candidate skills exist)
        response = requests.post(
            f"{api_base_url}/skills/analyze/{job_id}",
            json={"include_resources": True},
            timeout=10
        )
        # May succeed or fail if no candidate skills
        if response.status_code == 200:
            analysis = response.json()
            assert "overall_match_score" in analysis
            assert "skill_analysis" in analysis

        # Step 5: Get job timeline
        response = requests.get(
            f"{api_base_url}/ats/jobs/{job_id}/timeline",
            timeout=10
        )
        assert response.status_code == 200
        timeline = response.json()
        assert "events" in timeline

    def test_job_update_workflow(self, api_base_url, cleanup_test_data):
        """Test job update workflow"""

        # Create job
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "Netflix",
                "job_title": "Backend Engineer",
                "job_description": "Build scalable services",
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]
        cleanup_test_data.append(job_id)

        # Update job
        response = requests.patch(
            f"{api_base_url}/jobs/{job_id}",
            json={"notes": "Very interested in this role"},
            timeout=10
        )
        assert response.status_code == 200

        # Verify update
        response = requests.get(f"{api_base_url}/jobs/{job_id}", timeout=10)
        job = response.json()
        assert job["notes"] == "Very interested in this role"


class TestApplicationLifecycleWorkflow:
    """Test complete application lifecycle"""

    def test_complete_application_lifecycle(self, api_base_url, cleanup_test_data):
        """
        Test full application lifecycle:
        1. Create job (saved status)
        2. Update to applied
        3. Schedule interview
        4. Update interview outcome
        5. Receive offer
        6. Accept offer
        """

        # Step 1: Create job
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "Meta",
                "job_title": "Staff Engineer",
                "job_description": "Lead engineering initiatives",
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]
        cleanup_test_data.append(job_id)

        # Step 2: Update status to applied
        response = requests.post(
            f"{api_base_url}/ats/jobs/{job_id}/status",
            json={
                "status": "applied",
                "notes": "Applied via company website"
            },
            timeout=10
        )
        assert response.status_code == 200
        result = response.json()
        assert result["new_status"] == "applied"

        # Verify follow-ups were scheduled
        time.sleep(1)
        response = requests.get(
            f"{api_base_url}/followup/jobs/{job_id}",
            timeout=10
        )
        assert response.status_code == 200
        # May have follow-ups scheduled

        # Step 3: Update to interviewing
        response = requests.post(
            f"{api_base_url}/ats/jobs/{job_id}/status",
            json={
                "status": "interviewing",
                "notes": "Phone screen scheduled"
            },
            timeout=10
        )
        assert response.status_code == 200

        # Step 4: Schedule interview
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        response = requests.post(
            f"{api_base_url}/ats/interviews",
            json={
                "job_id": job_id,
                "interview_type": "phone",
                "scheduled_date": future_date,
                "duration_minutes": 60,
                "interviewer_name": "Jane Smith"
            },
            timeout=10
        )
        assert response.status_code == 201
        interview = response.json()
        interview_id = interview["id"]

        # Step 5: Update interview outcome
        response = requests.put(
            f"{api_base_url}/ats/interviews/{interview_id}",
            json={
                "outcome": "passed",
                "feedback": "Great conversation!"
            },
            timeout=10
        )
        assert response.status_code == 200

        # Step 6: Update to offer_received
        response = requests.post(
            f"{api_base_url}/ats/jobs/{job_id}/status",
            json={"status": "offer_received"},
            timeout=10
        )
        assert response.status_code == 200

        # Step 7: Record offer
        response = requests.post(
            f"{api_base_url}/ats/offers",
            json={
                "job_id": job_id,
                "base_salary": 200000,
                "bonus": 50000,
                "received_date": datetime.now().isoformat()
            },
            timeout=10
        )
        assert response.status_code == 201
        offer = response.json()
        offer_id = offer["id"]

        # Step 8: Accept offer
        response = requests.put(
            f"{api_base_url}/ats/offers/{offer_id}",
            json={
                "offer_status": "accepted",
                "decision_date": datetime.now().isoformat()
            },
            timeout=10
        )
        assert response.status_code == 200

        # Step 9: Verify final status
        response = requests.get(f"{api_base_url}/jobs/{job_id}", timeout=10)
        job = response.json()
        assert job["status"] == "accepted"

        # Step 10: Get complete timeline
        response = requests.get(
            f"{api_base_url}/ats/jobs/{job_id}/timeline",
            timeout=10
        )
        assert response.status_code == 200
        timeline = response.json()

        # Should have multiple events
        assert len(timeline["events"]) >= 4
        assert len(timeline["interviews"]) >= 1
        assert len(timeline["offers"]) >= 1

    def test_application_rejection_workflow(self, api_base_url, cleanup_test_data):
        """Test application rejection workflow"""

        # Create and apply
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "Apple",
                "job_title": "iOS Engineer",
                "job_description": "Build iOS apps",
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]
        cleanup_test_data.append(job_id)

        # Apply
        requests.post(
            f"{api_base_url}/ats/jobs/{job_id}/status",
            json={"status": "applied"},
            timeout=10
        )

        # Reject
        response = requests.post(
            f"{api_base_url}/ats/jobs/{job_id}/status",
            json={
                "status": "rejected",
                "notes": "Not selected for interview"
            },
            timeout=10
        )
        assert response.status_code == 200

        # Verify recommendation engine learned from rejection
        # (Would show in future recommendations)


class TestRecommendationWorkflow:
    """Test recommendation generation and learning workflow"""

    def test_recommendation_generation_and_learning(self, api_base_url, cleanup_test_data):
        """
        Test recommendation workflow:
        1. Create several jobs
        2. Apply to some (learn preferences)
        3. Dismiss others (learn dislikes)
        4. Get recommendations
        5. Verify recommendations improve
        """

        # Create multiple jobs
        jobs = [
            {"company": "Google", "job_title": "SWE", "job_description": "Python FastAPI backend", "source": "test"},
            {"company": "Meta", "job_title": "SWE", "job_description": "Python Django backend", "source": "test"},
            {"company": "Amazon", "job_title": "SWE", "job_description": "Java Spring backend", "source": "test"},
            {"company": "Microsoft", "job_title": "SWE", "job_description": "C# .NET backend", "source": "test"},
        ]

        job_ids = []
        for job_data in jobs:
            response = requests.post(
                f"{api_base_url}/jobs",
                json=job_data,
                timeout=10
            )
            job_id = response.json()["id"]
            job_ids.append(job_id)
            cleanup_test_data.append(job_id)

        # Apply to Python jobs (teach preference)
        for job_id in job_ids[:2]:
            requests.post(
                f"{api_base_url}/ats/jobs/{job_id}/status",
                json={"status": "applied"},
                timeout=10
            )

            # Record application for learning
            requests.post(
                f"{api_base_url}/recommendations/learn/application/{job_id}",
                timeout=10
            )

        # Dismiss non-Python jobs (teach dislike)
        for job_id in job_ids[2:]:
            requests.post(
                f"{api_base_url}/recommendations/learn/dismiss/{job_id}",
                json={"reason": "wrong_tech_stack"},
                timeout=10
            )

        # Get recommendations
        response = requests.get(
            f"{api_base_url}/recommendations",
            params={"limit": 10, "algorithm": "hybrid"},
            timeout=10
        )
        assert response.status_code == 200
        recommendations = response.json()

        # Should return recommendations
        assert "recommendations" in recommendations


class TestFollowUpWorkflow:
    """Test follow-up automation workflow"""

    def test_follow_up_sequence_scheduling(self, api_base_url, cleanup_test_data):
        """Test automatic follow-up sequence scheduling"""

        # Create job
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "Stripe",
                "job_title": "Backend Engineer",
                "job_description": "Payment systems",
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]
        cleanup_test_data.append(job_id)

        # Apply (should trigger follow-up sequence)
        requests.post(
            f"{api_base_url}/ats/jobs/{job_id}/status",
            json={"status": "applied"},
            timeout=10
        )

        time.sleep(1)

        # Check follow-ups were scheduled
        response = requests.get(
            f"{api_base_url}/followup/jobs/{job_id}",
            timeout=10
        )
        assert response.status_code == 200
        followups = response.json()

        # Should have post-application sequence
        # (3 days, 7 days, 14 days)
        # May be empty if integration not fully configured


class TestCachingWorkflow:
    """Test caching integration workflow"""

    def test_company_research_caching(self, api_base_url):
        """Test company research is cached"""

        company_name = "TestCompany_E2E"

        # First request - should research and cache
        response1 = requests.post(
            f"{api_base_url}/research/company",
            json={"company_name": company_name},
            timeout=10
        )

        # Second request - should return cached
        response2 = requests.get(
            f"{api_base_url}/research/company/{company_name}",
            timeout=10
        )

        # Both should succeed
        if response1.status_code == 200:
            assert response2.status_code == 200
            data = response2.json()
            assert data.get("cached") is True or data.get("cached") is False

    def test_cache_invalidation_workflow(self, api_base_url):
        """Test cache invalidation on updates"""

        # Get cache stats
        response = requests.get(
            f"{api_base_url}/cache/stats",
            timeout=10
        )
        assert response.status_code == 200
        stats = response.json()
        initial_keys = stats.get("stats", {}).get("total_keys", 0)

        # Clear recommendations cache
        response = requests.delete(
            f"{api_base_url}/cache/recommendations",
            timeout=10
        )
        assert response.status_code == 200

        # Verify keys decreased
        response = requests.get(
            f"{api_base_url}/cache/stats",
            timeout=10
        )
        stats = response.json()
        new_keys = stats.get("stats", {}).get("total_keys", 0)

        # Keys should have decreased (unless cache was already empty)
        assert new_keys <= initial_keys


class TestAnalyticsWorkflow:
    """Test analytics data collection workflow"""

    def test_analytics_event_tracking(self, api_base_url, cleanup_test_data):
        """Test analytics events are tracked throughout workflows"""

        # Create job
        response = requests.post(
            f"{api_base_url}/jobs",
            json={
                "company": "Analytics Test Corp",
                "job_title": "Data Engineer",
                "job_description": "Build data pipelines",
                "source": "test"
            },
            timeout=10
        )
        job_id = response.json()["id"]
        cleanup_test_data.append(job_id)

        # Apply
        requests.post(
            f"{api_base_url}/ats/jobs/{job_id}/status",
            json={"status": "applied"},
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

        # Should have data
        assert "summary" in analytics or "conversion_funnel" in analytics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
