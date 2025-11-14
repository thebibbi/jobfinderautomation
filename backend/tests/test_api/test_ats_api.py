"""
Tests for Application Tracking System (ATS) API Endpoints
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta


class TestStatusAPI:
    """Test status update endpoints"""

    def test_update_job_status_valid(self, client, db_session, create_test_job):
        """Test POST /api/v1/ats/jobs/{job_id}/status with valid transition"""
        job = create_test_job(status="discovered")

        response = client.post(
            f"/api/v1/ats/jobs/{job.id}/status",
            json={
                "status": "analyzing",
                "notes": "Starting analysis"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["old_status"] == "discovered"
        assert data["new_status"] == "analyzing"

    def test_update_job_status_invalid_transition(self, client, db_session, create_test_job):
        """Test status update with invalid transition"""
        job = create_test_job(status="discovered")

        response = client.post(
            f"/api/v1/ats/jobs/{job.id}/status",
            json={
                "status": "interview_scheduled"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid status transition" in response.json()["detail"]

    def test_update_job_status_not_found(self, client, db_session):
        """Test status update for non-existent job"""
        response = client.post(
            "/api/v1/ats/jobs/99999/status",
            json={
                "status": "analyzing"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_application_timeline(self, client, db_session, create_test_job):
        """Test GET /api/v1/ats/jobs/{job_id}/timeline"""
        job = create_test_job(status="discovered")

        # Update status to create events
        client.post(
            f"/api/v1/ats/jobs/{job.id}/status",
            json={"status": "analyzing"}
        )

        # Get timeline
        response = client.get(f"/api/v1/ats/jobs/{job.id}/timeline")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == job.id
        assert data["company"] == job.company
        assert "events" in data
        assert len(data["events"]) > 0


class TestInterviewAPI:
    """Test interview management endpoints"""

    def test_schedule_interview(self, client, db_session, create_test_job):
        """Test POST /api/v1/ats/interviews"""
        job = create_test_job(status="applied")

        scheduled_date = (datetime.utcnow() + timedelta(days=2)).isoformat()

        response = client.post(
            "/api/v1/ats/interviews",
            json={
                "job_id": job.id,
                "interview_type": "phone_screen",
                "scheduled_date": scheduled_date,
                "duration_minutes": 30,
                "is_virtual": True,
                "interviewer_names": "Jane Smith",
                "interviewer_titles": "Hiring Manager"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["job_id"] == job.id
        assert data["interview_type"] == "phone_screen"
        assert data["outcome"] == "pending"

    def test_schedule_interview_invalid_job(self, client, db_session):
        """Test scheduling interview for non-existent job"""
        scheduled_date = (datetime.utcnow() + timedelta(days=2)).isoformat()

        response = client.post(
            "/api/v1/ats/interviews",
            json={
                "job_id": 99999,
                "interview_type": "technical",
                "scheduled_date": scheduled_date
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_interview(self, client, db_session, create_test_job):
        """Test PUT /api/v1/ats/interviews/{interview_id}"""
        job = create_test_job(status="applied")
        scheduled_date = (datetime.utcnow() + timedelta(days=2)).isoformat()

        # Create interview
        create_response = client.post(
            "/api/v1/ats/interviews",
            json={
                "job_id": job.id,
                "interview_type": "technical",
                "scheduled_date": scheduled_date
            }
        )
        interview_id = create_response.json()["id"]

        # Update interview
        response = client.put(
            f"/api/v1/ats/interviews/{interview_id}",
            json={
                "outcome": "passed",
                "performance_rating": 5,
                "feedback": "Excellent technical skills"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["outcome"] == "passed"
        assert data["performance_rating"] == 5

    def test_get_upcoming_interviews(self, client, db_session, create_test_job):
        """Test GET /api/v1/ats/interviews/upcoming"""
        job = create_test_job(status="applied")
        scheduled_date = (datetime.utcnow() + timedelta(days=2)).isoformat()

        # Schedule interview
        client.post(
            "/api/v1/ats/interviews",
            json={
                "job_id": job.id,
                "interview_type": "phone_screen",
                "scheduled_date": scheduled_date
            }
        )

        # Get upcoming interviews
        response = client.get("/api/v1/ats/interviews/upcoming?days_ahead=7")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_job_interviews(self, client, db_session, create_test_job):
        """Test GET /api/v1/ats/jobs/{job_id}/interviews"""
        job = create_test_job(status="applied")
        scheduled_date = (datetime.utcnow() + timedelta(days=2)).isoformat()

        # Schedule interview
        client.post(
            "/api/v1/ats/interviews",
            json={
                "job_id": job.id,
                "interview_type": "technical",
                "scheduled_date": scheduled_date
            }
        )

        # Get job interviews
        response = client.get(f"/api/v1/ats/jobs/{job.id}/interviews")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["job_id"] == job.id


class TestOfferAPI:
    """Test offer management endpoints"""

    def test_record_offer(self, client, db_session, create_test_job):
        """Test POST /api/v1/ats/offers"""
        job = create_test_job(status="interviewing")

        response = client.post(
            "/api/v1/ats/offers",
            json={
                "job_id": job.id,
                "salary": 100000,
                "currency": "USD",
                "bonus": 10000,
                "equity": "1000 RSUs",
                "vacation_days": 20
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["job_id"] == job.id
        assert data["salary"] == 100000
        assert data["status"] == "pending_review"

    def test_record_offer_invalid_job(self, client, db_session):
        """Test recording offer for non-existent job"""
        response = client.post(
            "/api/v1/ats/offers",
            json={
                "job_id": 99999,
                "salary": 100000
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_offer(self, client, db_session, create_test_job):
        """Test PUT /api/v1/ats/offers/{offer_id}"""
        job = create_test_job(status="interviewing")

        # Create offer
        create_response = client.post(
            "/api/v1/ats/offers",
            json={
                "job_id": job.id,
                "salary": 100000
            }
        )
        offer_id = create_response.json()["id"]

        # Update offer
        response = client.put(
            f"/api/v1/ats/offers/{offer_id}",
            json={
                "status": "accepted",
                "decision_notes": "Great opportunity!"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "accepted"
        assert data["decision_notes"] == "Great opportunity!"

    def test_add_negotiation(self, client, db_session, create_test_job):
        """Test POST /api/v1/ats/offers/{offer_id}/negotiate"""
        job = create_test_job(status="interviewing")

        # Create offer
        create_response = client.post(
            "/api/v1/ats/offers",
            json={
                "job_id": job.id,
                "salary": 100000,
                "bonus": 5000
            }
        )
        offer_id = create_response.json()["id"]

        # Add negotiation
        response = client.post(
            f"/api/v1/ats/offers/{offer_id}/negotiate",
            json={
                "counter_salary": 110000,
                "counter_bonus": 10000,
                "counter_notes": "Based on market research"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "negotiating"
        assert data["counter_offers"] is not None
        assert len(data["counter_offers"]) == 1

    def test_get_job_offers(self, client, db_session, create_test_job):
        """Test GET /api/v1/ats/jobs/{job_id}/offers"""
        job = create_test_job(status="interviewing")

        # Create offer
        client.post(
            "/api/v1/ats/offers",
            json={
                "job_id": job.id,
                "salary": 100000
            }
        )

        # Get job offers
        response = client.get(f"/api/v1/ats/jobs/{job.id}/offers")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["job_id"] == job.id


class TestNotesAPI:
    """Test notes management endpoints"""

    def test_add_note(self, client, db_session, create_test_job):
        """Test POST /api/v1/ats/notes"""
        job = create_test_job()

        response = client.post(
            "/api/v1/ats/notes",
            json={
                "job_id": job.id,
                "note_type": "general",
                "title": "First Impressions",
                "content": "Company culture seems great"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["job_id"] == job.id
        assert data["note_type"] == "general"
        assert data["title"] == "First Impressions"

    def test_add_communication_note(self, client, db_session, create_test_job):
        """Test adding a communication record"""
        job = create_test_job()

        response = client.post(
            "/api/v1/ats/notes",
            json={
                "job_id": job.id,
                "note_type": "communication",
                "content": "Spoke with hiring manager",
                "is_communication": True,
                "communication_direction": "inbound",
                "communication_method": "phone",
                "contact_person": "Jane Smith"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_communication"] is True
        assert data["contact_person"] == "Jane Smith"

    def test_update_note(self, client, db_session, create_test_job):
        """Test PUT /api/v1/ats/notes/{note_id}"""
        job = create_test_job()

        # Create note
        create_response = client.post(
            "/api/v1/ats/notes",
            json={
                "job_id": job.id,
                "note_type": "general",
                "content": "Initial note"
            }
        )
        note_id = create_response.json()["id"]

        # Update note
        response = client.put(
            f"/api/v1/ats/notes/{note_id}",
            json={
                "content": "Updated note content"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Updated note content"

    def test_get_job_notes(self, client, db_session, create_test_job):
        """Test GET /api/v1/ats/jobs/{job_id}/notes"""
        job = create_test_job()

        # Add note
        client.post(
            "/api/v1/ats/notes",
            json={
                "job_id": job.id,
                "note_type": "general",
                "content": "Test note"
            }
        )

        # Get job notes
        response = client.get(f"/api/v1/ats/jobs/{job.id}/notes")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestStatisticsAPI:
    """Test statistics endpoint"""

    def test_get_statistics(self, client, db_session, create_test_job):
        """Test GET /api/v1/ats/statistics"""
        # Create jobs in various statuses
        create_test_job(job_id="job1", status="discovered")
        create_test_job(job_id="job2", status="applied")
        create_test_job(job_id="job3", status="interviewing")

        response = client.get("/api/v1/ats/statistics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_applications" in data
        assert "by_status" in data
        assert "interviews_scheduled" in data
        assert "offers_received" in data
        assert data["total_applications"] >= 3

    def test_get_statistics_empty(self, client, db_session):
        """Test statistics with no applications"""
        response = client.get("/api/v1/ats/statistics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_applications"] == 0


class TestCompleteWorkflow:
    """Test complete ATS workflow"""

    def test_full_application_lifecycle(self, client, db_session, create_test_job):
        """
        Test complete application lifecycle:
        1. Discover job
        2. Analyze
        3. Apply
        4. Schedule interview
        5. Receive offer
        6. Accept offer
        """
        job = create_test_job(status="discovered")

        # 1. Analyze
        response = client.post(
            f"/api/v1/ats/jobs/{job.id}/status",
            json={"status": "analyzing"}
        )
        assert response.status_code == status.HTTP_200_OK

        # 2. Mark as analyzed
        response = client.post(
            f"/api/v1/ats/jobs/{job.id}/status",
            json={"status": "analyzed"}
        )
        assert response.status_code == status.HTTP_200_OK

        # 3. Ready to apply
        response = client.post(
            f"/api/v1/ats/jobs/{job.id}/status",
            json={"status": "ready_to_apply"}
        )
        assert response.status_code == status.HTTP_200_OK

        # 4. Applied
        response = client.post(
            f"/api/v1/ats/jobs/{job.id}/status",
            json={"status": "applied"}
        )
        assert response.status_code == status.HTTP_200_OK

        # 5. Schedule interview
        scheduled_date = (datetime.utcnow() + timedelta(days=2)).isoformat()
        response = client.post(
            "/api/v1/ats/interviews",
            json={
                "job_id": job.id,
                "interview_type": "technical",
                "scheduled_date": scheduled_date
            }
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 6. Interview completed, move to offer
        response = client.post(
            f"/api/v1/ats/jobs/{job.id}/status",
            json={"status": "interviewing"}
        )
        assert response.status_code == status.HTTP_200_OK

        # 7. Record offer
        response = client.post(
            "/api/v1/ats/offers",
            json={
                "job_id": job.id,
                "salary": 120000,
                "bonus": 15000
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        offer_id = response.json()["id"]

        # 8. Accept offer
        response = client.put(
            f"/api/v1/ats/offers/{offer_id}",
            json={"status": "accepted"}
        )
        assert response.status_code == status.HTTP_200_OK

        # 9. Verify final timeline
        response = client.get(f"/api/v1/ats/jobs/{job.id}/timeline")
        assert response.status_code == status.HTTP_200_OK
        timeline = response.json()
        assert timeline["current_status"] == "offer_accepted"
        assert len(timeline["events"]) > 0
        assert len(timeline["interviews"]) >= 1
        assert len(timeline["offers"]) >= 1
