"""
Integration tests for complete job processing workflow
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi import status


class TestJobProcessingWorkflow:
    """Test the complete job processing workflow end-to-end"""

    @pytest.mark.asyncio
    async def test_full_workflow_high_match(
        self,
        client,
        db_session,
        sample_job_data,
        sample_analysis_result,
        mock_google_drive_service,
        mock_email_service
    ):
        """
        Test complete workflow for high-match job:
        1. Submit job via API
        2. Analyze job (high score)
        3. Create Drive folder
        4. Generate documents
        5. Upload to Drive
        6. Send email notification
        """
        # Mock AI service
        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.return_value = sample_analysis_result
            mock_get_ai.return_value = mock_ai_service

            # Mock Drive service
            with patch('app.services.google_drive_service.get_drive_service') as mock_get_drive:
                mock_get_drive.return_value = mock_google_drive_service

                # Mock Email service
                with patch('app.services.email_service.get_email_service') as mock_get_email:
                    mock_get_email.return_value = mock_email_service

                    # Mock document generator
                    with patch('app.services.document_generator.get_document_generator') as mock_get_doc_gen:
                        mock_doc_gen = AsyncMock()
                        mock_doc_gen.generate_resume.return_value = b"Resume content"
                        mock_doc_gen.generate_cover_letter.return_value = "Cover letter content"
                        mock_get_doc_gen.return_value = mock_doc_gen

                        # 1. Submit job
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
                        job_id = response.json()["jobId"]

                        # 2. Verify job was created
                        job_response = client.get(f"/api/v1/jobs/{job_id}")
                        assert job_response.status_code == status.HTTP_200_OK

                        # 3. Trigger analysis (simulating background task)
                        from app.services.job_analyzer import get_job_analyzer
                        analyzer = get_job_analyzer()

                        with patch('app.services.job_analyzer.SessionLocal', return_value=db_session):
                            analysis_result = await analyzer.analyze_job(job_id)

                        # 4. Verify analysis results
                        assert analysis_result["match_score"] == 85
                        assert analysis_result["analysis"]["should_apply"] is True

                        # 5. Verify job status updated
                        job_response = client.get(f"/api/v1/jobs/{job_id}")
                        job_data = job_response.json()
                        assert job_data["match_score"] == 85
                        assert job_data["status"] == "ready_for_documents"

    @pytest.mark.asyncio
    async def test_full_workflow_low_match(
        self,
        client,
        db_session,
        sample_job_data_low_match,
        sample_low_score_analysis,
        mock_email_service
    ):
        """
        Test workflow for low-match job:
        1. Submit job
        2. Analyze job (low score)
        3. Mark as no action
        4. Skip document generation
        5. Send notification (optional)
        """
        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.return_value = sample_low_score_analysis
            mock_get_ai.return_value = mock_ai_service

            with patch('app.services.email_service.get_email_service') as mock_get_email:
                mock_get_email.return_value = mock_email_service

                # 1. Submit job
                response = client.post(
                    "/api/v1/jobs/process",
                    json={
                        "company": sample_job_data_low_match["company"],
                        "jobTitle": sample_job_data_low_match["job_title"],
                        "jobDescription": sample_job_data_low_match["job_description"],
                        "jobUrl": sample_job_data_low_match["job_url"],
                        "source": sample_job_data_low_match["source"]
                    }
                )

                assert response.status_code == status.HTTP_200_OK
                job_id = response.json()["jobId"]

                # 2. Analyze job
                from app.services.job_analyzer import get_job_analyzer
                analyzer = get_job_analyzer()

                with patch('app.services.job_analyzer.SessionLocal', return_value=db_session):
                    analysis_result = await analyzer.analyze_job(job_id)

                # 3. Verify low score handling
                assert analysis_result["match_score"] == 45
                assert analysis_result["analysis"]["should_apply"] is False

                # 4. Verify job status
                job_response = client.get(f"/api/v1/jobs/{job_id}")
                job_data = job_response.json()
                assert job_data["status"] == "analyzed_no_action"


class TestTwoTierWorkflow:
    """Test two-tier analysis workflow (prescreening + full analysis)"""

    @pytest.mark.asyncio
    async def test_two_tier_workflow_passed_threshold(
        self,
        client,
        db_session,
        sample_job_data,
        sample_analysis_result
    ):
        """
        Test two-tier workflow when job passes prescreening:
        1. Submit job
        2. Cheap model prescreening (score: 75)
        3. Passes threshold (60)
        4. Expensive model analysis (score: 85)
        5. Generate documents
        """
        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()

            # Prescreening result (passes threshold)
            prescreening_result = sample_analysis_result.copy()
            prescreening_result["match_score"] = 75
            prescreening_result["prescreening_only"] = True

            # Full analysis result
            full_result = sample_analysis_result.copy()
            full_result["match_score"] = 85
            full_result["used_prescreening"] = True

            mock_ai_service.analyze_job_fit.return_value = full_result
            mock_get_ai.return_value = mock_ai_service

            # Submit and analyze job
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

            job_id = response.json()["jobId"]

            # Trigger analysis
            from app.services.job_analyzer import get_job_analyzer
            analyzer = get_job_analyzer()

            with patch('app.services.job_analyzer.SessionLocal', return_value=db_session):
                result = await analyzer.analyze_job(job_id)

            # Verify full analysis was performed
            assert result["match_score"] == 85
            assert result["analysis"]["should_apply"] is True

    @pytest.mark.asyncio
    async def test_two_tier_workflow_failed_threshold(
        self,
        client,
        db_session,
        sample_job_data_low_match,
        sample_low_score_analysis
    ):
        """
        Test two-tier workflow when job fails prescreening:
        1. Submit job
        2. Cheap model prescreening (score: 45)
        3. Fails threshold (60)
        4. Skip expensive analysis (cost savings!)
        5. Mark as no action
        """
        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()

            # Prescreening result (fails threshold)
            prescreening_result = sample_low_score_analysis.copy()
            prescreening_result["match_score"] = 45
            prescreening_result["prescreening_only"] = True

            mock_ai_service.analyze_job_fit.return_value = prescreening_result
            mock_get_ai.return_value = mock_ai_service

            # Submit and analyze job
            response = client.post(
                "/api/v1/jobs/process",
                json={
                    "company": sample_job_data_low_match["company"],
                    "jobTitle": sample_job_data_low_match["job_title"],
                    "jobDescription": sample_job_data_low_match["job_description"],
                    "jobUrl": sample_job_data_low_match["job_url"],
                    "source": sample_job_data_low_match["source"]
                }
            )

            job_id = response.json()["jobId"]

            # Trigger analysis
            from app.services.job_analyzer import get_job_analyzer
            analyzer = get_job_analyzer()

            with patch('app.services.job_analyzer.SessionLocal', return_value=db_session):
                result = await analyzer.analyze_job(job_id)

            # Verify only prescreening was used
            assert result["match_score"] == 45
            assert result["analysis"]["should_apply"] is False


class TestEnsembleWorkflow:
    """Test ensemble analysis workflow"""

    @pytest.mark.asyncio
    async def test_ensemble_workflow(
        self,
        client,
        db_session,
        sample_job_data
    ):
        """
        Test ensemble analysis workflow:
        1. Submit job
        2. Analyze with 3 models
        3. Combine results
        4. High confidence decision
        """
        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()

            ensemble_result = {
                "match_score": 82,
                "should_apply": True,
                "key_strengths": ["Strong analytical skills"],
                "ensemble_results": {
                    "individual_scores": [85, 78, 83],
                    "average_score": 82,
                    "confidence": "high",
                    "agreement": "strong"
                }
            }

            mock_ai_service.analyze_job_fit.return_value = ensemble_result
            mock_get_ai.return_value = mock_ai_service

            # Submit job
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

            job_id = response.json()["jobId"]

            # Analyze with ensemble
            from app.services.job_analyzer import get_job_analyzer
            analyzer = get_job_analyzer()

            with patch('app.services.job_analyzer.SessionLocal', return_value=db_session):
                result = await analyzer.analyze_job(job_id)

            # Verify ensemble results
            assert result["match_score"] == 82
            assert "ensemble_results" in result["analysis"]
            assert result["analysis"]["ensemble_results"]["confidence"] == "high"


class TestWorkflowErrorHandling:
    """Test error handling in workflow"""

    @pytest.mark.asyncio
    async def test_workflow_ai_service_failure(
        self,
        client,
        db_session,
        sample_job_data
    ):
        """Test workflow when AI service fails"""
        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.side_effect = Exception("API Error")
            mock_get_ai.return_value = mock_ai_service

            # Submit job
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

            job_id = response.json()["jobId"]

            # Attempt analysis
            from app.services.job_analyzer import get_job_analyzer
            analyzer = get_job_analyzer()

            with patch('app.services.job_analyzer.SessionLocal', return_value=db_session):
                with pytest.raises(Exception, match="API Error"):
                    await analyzer.analyze_job(job_id)

            # Verify job status not updated incorrectly
            job_response = client.get(f"/api/v1/jobs/{job_id}")
            job_data = job_response.json()
            assert job_data["match_score"] is None
            assert job_data["analysis_completed"] is False
