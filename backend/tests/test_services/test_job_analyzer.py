"""
Tests for Job Analyzer Service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.services.job_analyzer import JobAnalyzer, get_job_analyzer
from app.models.job import Job


class TestJobAnalyzerBasicFunctionality:
    """Test basic job analyzer functionality"""

    def test_get_job_analyzer_singleton(self):
        """Test that get_job_analyzer returns singleton"""
        analyzer1 = get_job_analyzer()
        analyzer2 = get_job_analyzer()
        assert analyzer1 is analyzer2

    def test_job_analyzer_initialization(self):
        """Test JobAnalyzer initialization"""
        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_get_ai.return_value = Mock()
            analyzer = JobAnalyzer()
            assert analyzer.ai_service is not None


class TestJobAnalysis:
    """Test job analysis workflow"""

    @pytest.mark.asyncio
    async def test_analyze_job_success_high_score(
        self, db_session, create_test_job, sample_job_data, sample_analysis_result
    ):
        """Test successful job analysis with high match score"""
        # Create a test job
        job = create_test_job(
            job_id="test_high_score",
            company=sample_job_data["company"],
            job_title=sample_job_data["job_title"],
            job_description=sample_job_data["job_description"],
            status="discovered"
        )

        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.return_value = sample_analysis_result
            mock_get_ai.return_value = mock_ai_service

            with patch('app.services.job_analyzer.SessionLocal') as mock_session_local:
                mock_session_local.return_value = db_session

                analyzer = JobAnalyzer()
                result = await analyzer.analyze_job(job.id)

                # Verify analysis was performed
                assert result["match_score"] == 85
                assert result["analysis"]["should_apply"] is True

                # Verify job was updated
                db_session.refresh(job)
                assert job.match_score == 85
                assert job.analysis_completed is True
                assert job.analysis_date is not None
                assert job.status == "ready_for_documents"

    @pytest.mark.asyncio
    async def test_analyze_job_success_low_score(
        self, db_session, create_test_job, sample_job_data_low_match, sample_low_score_analysis
    ):
        """Test successful job analysis with low match score"""
        job = create_test_job(
            job_id="test_low_score",
            company=sample_job_data_low_match["company"],
            job_title=sample_job_data_low_match["job_title"],
            job_description=sample_job_data_low_match["job_description"],
            status="discovered"
        )

        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.return_value = sample_low_score_analysis
            mock_get_ai.return_value = mock_ai_service

            with patch('app.services.job_analyzer.SessionLocal') as mock_session_local:
                mock_session_local.return_value = db_session

                analyzer = JobAnalyzer()
                result = await analyzer.analyze_job(job.id)

                # Verify low score handling
                assert result["match_score"] == 45
                assert result["analysis"]["should_apply"] is False

                # Verify job was updated with correct status
                db_session.refresh(job)
                assert job.match_score == 45
                assert job.status == "analyzed_no_action"

    @pytest.mark.asyncio
    async def test_analyze_job_not_found(self, db_session):
        """Test analysis of non-existent job"""
        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_get_ai.return_value = AsyncMock()

            with patch('app.services.job_analyzer.SessionLocal') as mock_session_local:
                mock_session_local.return_value = db_session

                analyzer = JobAnalyzer()

                with pytest.raises(ValueError, match="Job .* not found"):
                    await analyzer.analyze_job(99999)

    @pytest.mark.asyncio
    async def test_analyze_job_ai_service_error(self, db_session, create_test_job, sample_job_data):
        """Test handling of AI service errors"""
        job = create_test_job(
            job_id="test_error",
            company=sample_job_data["company"],
            job_title=sample_job_data["job_title"],
            job_description=sample_job_data["job_description"]
        )

        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.side_effect = Exception("API Error")
            mock_get_ai.return_value = mock_ai_service

            with patch('app.services.job_analyzer.SessionLocal') as mock_session_local:
                mock_session_local.return_value = db_session

                analyzer = JobAnalyzer()

                with pytest.raises(Exception, match="API Error"):
                    await analyzer.analyze_job(job.id)

                # Verify rollback occurred (job not updated)
                db_session.refresh(job)
                assert job.match_score is None
                assert job.analysis_completed is False

    @pytest.mark.asyncio
    async def test_analyze_job_with_ensemble(
        self, db_session, create_test_job, sample_job_data
    ):
        """Test job analysis using ensemble strategy"""
        job = create_test_job(
            job_id="test_ensemble",
            company=sample_job_data["company"],
            job_title=sample_job_data["job_title"],
            job_description=sample_job_data["job_description"]
        )

        ensemble_result = {
            "match_score": 82,
            "should_apply": True,
            "ensemble_results": {
                "individual_scores": [85, 78, 83],
                "average_score": 82,
                "confidence": "high"
            }
        }

        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.return_value = ensemble_result
            mock_get_ai.return_value = mock_ai_service

            with patch('app.services.job_analyzer.SessionLocal') as mock_session_local:
                mock_session_local.return_value = db_session

                analyzer = JobAnalyzer()
                result = await analyzer.analyze_job(job.id)

                # Verify ensemble results
                assert result["match_score"] == 82
                assert "ensemble_results" in result["analysis"]

                db_session.refresh(job)
                assert job.match_score == 82
                assert job.analysis_results["ensemble_results"]["confidence"] == "high"


class TestJobAnalysisDataPersistence:
    """Test data persistence during analysis"""

    @pytest.mark.asyncio
    async def test_analysis_results_stored_correctly(
        self, db_session, create_test_job, sample_job_data, sample_analysis_result
    ):
        """Test that analysis results are stored correctly in database"""
        job = create_test_job(
            job_id="test_persistence",
            company=sample_job_data["company"],
            job_title=sample_job_data["job_title"],
            job_description=sample_job_data["job_description"]
        )

        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.return_value = sample_analysis_result
            mock_get_ai.return_value = mock_ai_service

            with patch('app.services.job_analyzer.SessionLocal') as mock_session_local:
                mock_session_local.return_value = db_session

                analyzer = JobAnalyzer()
                await analyzer.analyze_job(job.id)

                # Verify all fields were updated
                db_session.refresh(job)
                assert job.match_score == sample_analysis_result["match_score"]
                assert job.analysis_completed is True
                assert isinstance(job.analysis_date, datetime)
                assert job.analysis_results == sample_analysis_result
                assert len(job.analysis_results["key_strengths"]) == 3

    @pytest.mark.asyncio
    async def test_analysis_date_timestamp(self, db_session, create_test_job, sample_job_data, sample_analysis_result):
        """Test that analysis date is set correctly"""
        job = create_test_job(
            job_id="test_timestamp",
            company=sample_job_data["company"],
            job_title=sample_job_data["job_title"],
            job_description=sample_job_data["job_description"]
        )

        before_analysis = datetime.utcnow()

        with patch('app.services.job_analyzer.get_ai_service') as mock_get_ai:
            mock_ai_service = AsyncMock()
            mock_ai_service.analyze_job_fit.return_value = sample_analysis_result
            mock_get_ai.return_value = mock_ai_service

            with patch('app.services.job_analyzer.SessionLocal') as mock_session_local:
                mock_session_local.return_value = db_session

                analyzer = JobAnalyzer()
                await analyzer.analyze_job(job.id)

        after_analysis = datetime.utcnow()

        db_session.refresh(job)
        assert before_analysis <= job.analysis_date <= after_analysis
