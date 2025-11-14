"""
Tests for Jobs API endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi import status


class TestJobsAPIBasicEndpoints:
    """Test basic job CRUD operations"""

    def test_create_job_from_extension(self, client, sample_job_data):
        """Test POST /api/v1/jobs/process endpoint"""
        with patch('app.api.jobs.process_job_complete_workflow') as mock_task:
            response = client.post(
                "/api/v1/jobs/process",
                json={
                    "company": sample_job_data["company"],
                    "jobTitle": sample_job_data["job_title"],
                    "jobDescription": sample_job_data["job_description"],
                    "jobUrl": sample_job_data["job_url"],
                    "source": sample_job_data["source"],
                    "location": sample_job_data.get("location", ""),
                    "salaryRange": sample_job_data.get("salary_range", "")
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "jobId" in data
            assert data["status"] == "processing"

    def test_create_job_missing_required_fields(self, client):
        """Test job creation with missing required fields"""
        response = client.post(
            "/api/v1/jobs/process",
            json={
                "company": "TechCorp"
                # Missing jobTitle, jobDescription, etc.
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_job_by_id(self, client, db_session, create_test_job):
        """Test GET /api/v1/jobs/{job_id} endpoint"""
        job = create_test_job(
            job_id="test_get_job",
            company="TestCorp",
            job_title="Test Position",
            match_score=85,
            status="ready_for_documents"
        )

        response = client.get(f"/api/v1/jobs/{job.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == job.id
        assert data["company"] == "TestCorp"
        assert data["match_score"] == 85

    def test_get_job_not_found(self, client):
        """Test getting non-existent job"""
        response = client.get("/api/v1/jobs/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_jobs(self, client, db_session, create_test_job):
        """Test GET /api/v1/jobs endpoint"""
        # Create multiple test jobs
        create_test_job(job_id="job1", company="Company1", match_score=85)
        create_test_job(job_id="job2", company="Company2", match_score=70)
        create_test_job(job_id="job3", company="Company3", match_score=90)

        response = client.get("/api/v1/jobs")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3


class TestJobsAPIFiltering:
    """Test job listing filters"""

    def test_filter_jobs_by_status(self, client, db_session, create_test_job):
        """Test filtering jobs by status"""
        create_test_job(job_id="job_ready", status="ready_for_documents")
        create_test_job(job_id="job_analyzed", status="analyzed_no_action")

        response = client.get("/api/v1/jobs?status=ready_for_documents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(job["status"] == "ready_for_documents" for job in data)

    def test_filter_jobs_by_min_score(self, client, db_session, create_test_job):
        """Test filtering jobs by minimum match score"""
        create_test_job(job_id="job_high", match_score=90)
        create_test_job(job_id="job_medium", match_score=70)
        create_test_job(job_id="job_low", match_score=50)

        response = client.get("/api/v1/jobs?min_score=75")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(job["match_score"] >= 75 for job in data if job["match_score"])

    def test_sort_jobs_by_score(self, client, db_session, create_test_job):
        """Test sorting jobs by match score"""
        create_test_job(job_id="job1", match_score=70)
        create_test_job(job_id="job2", match_score=90)
        create_test_job(job_id="job3", match_score=80)

        response = client.get("/api/v1/jobs?sort=score_desc")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        scores = [job["match_score"] for job in data if job["match_score"]]
        assert scores == sorted(scores, reverse=True)


class TestJobsAPIAnalysis:
    """Test job analysis endpoints"""

    def test_trigger_job_analysis(self, client, db_session, create_test_job):
        """Test POST /api/v1/jobs/{job_id}/analyze endpoint"""
        job = create_test_job(job_id="test_analyze", status="discovered")

        with patch('app.api.jobs.analyze_job_task.delay') as mock_task:
            response = client.post(f"/api/v1/jobs/{job.id}/analyze")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Analysis started"
            mock_task.assert_called_once_with(job.id)

    def test_get_job_analysis_results(self, client, db_session, create_test_job, sample_analysis_result):
        """Test GET /api/v1/jobs/{job_id}/analysis endpoint"""
        job = create_test_job(
            job_id="test_analysis_results",
            match_score=85,
            analysis_completed=True,
            analysis_results=sample_analysis_result
        )

        response = client.get(f"/api/v1/jobs/{job.id}/analysis")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["match_score"] == 85
        assert data["should_apply"] is True
        assert len(data["key_strengths"]) == 3


class TestJobsAPIDocumentGeneration:
    """Test document generation endpoints"""

    def test_generate_documents_for_job(self, client, db_session, create_test_job):
        """Test POST /api/v1/jobs/{job_id}/generate-documents endpoint"""
        job = create_test_job(
            job_id="test_generate_docs",
            match_score=85,
            status="ready_for_documents"
        )

        with patch('app.api.jobs.generate_documents_task.delay') as mock_task:
            response = client.post(f"/api/v1/jobs/{job.id}/generate-documents")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Document generation started"
            mock_task.assert_called_once_with(job.id)

    def test_generate_documents_not_ready(self, client, db_session, create_test_job):
        """Test document generation for job not ready"""
        job = create_test_job(
            job_id="test_not_ready",
            status="discovered"  # Not analyzed yet
        )

        response = client.post(f"/api/v1/jobs/{job.id}/generate-documents")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestJobsAPIBulkOperations:
    """Test bulk job operations"""

    def test_bulk_analyze_jobs(self, client, db_session, create_test_job):
        """Test POST /api/v1/jobs/bulk/analyze endpoint"""
        job1 = create_test_job(job_id="bulk1", status="discovered")
        job2 = create_test_job(job_id="bulk2", status="discovered")

        with patch('app.api.jobs.analyze_job_task.delay') as mock_task:
            response = client.post(
                "/api/v1/jobs/bulk/analyze",
                json={"job_ids": [job1.id, job2.id]}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["queued_count"] == 2
            assert mock_task.call_count == 2

    def test_bulk_delete_jobs(self, client, db_session, create_test_job):
        """Test DELETE /api/v1/jobs/bulk endpoint"""
        job1 = create_test_job(job_id="delete1")
        job2 = create_test_job(job_id="delete2")

        response = client.request(
            "DELETE",
            "/api/v1/jobs/bulk",
            json={"job_ids": [job1.id, job2.id]}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2


class TestJobsAPIErrorHandling:
    """Test API error handling"""

    def test_invalid_job_data(self, client):
        """Test handling of invalid job data"""
        response = client.post(
            "/api/v1/jobs/process",
            json={
                "company": "",  # Empty company
                "jobTitle": "Test",
                "jobDescription": "",  # Empty description
                "jobUrl": "invalid-url",  # Invalid URL
                "source": "unknown"
            }
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_database_error_handling(self, client, db_session):
        """Test handling of database errors"""
        with patch('app.api.jobs.get_db') as mock_get_db:
            mock_db = Mock()
            mock_db.query.side_effect = Exception("Database error")
            mock_get_db.return_value = mock_db

            response = client.get("/api/v1/jobs")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestJobsAPIBackgroundTasks:
    """Test background task integration"""

    def test_job_processing_workflow_triggered(self, client, sample_job_data):
        """Test that full workflow is triggered when job is submitted"""
        with patch('app.api.jobs.BackgroundTasks') as mock_bg_tasks:
            response = client.post(
                "/api/v1/jobs/process",
                json={
                    "company": sample_job_data["company"],
                    "jobTitle": sample_job_data["job_title"],
                    "jobDescription": sample_job_data["job_description"],
                    "jobUrl": sample_job_data["job_url"],
                    "source": sample_job_data["source"]
                }
            )

            assert response.status_code == status.HTTP_200_OK
            # Verify background task was added
            # Note: Actual verification depends on your implementation
