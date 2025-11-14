"""
Tests for AI Service (provider-agnostic abstraction layer)
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.ai_service import AIService, get_ai_service
from app.config import settings


class TestAIServiceProviderSelection:
    """Test provider selection and initialization"""

    def test_get_ai_service_singleton(self):
        """Test that get_ai_service returns singleton"""
        service1 = get_ai_service()
        service2 = get_ai_service()
        assert service1 is service2

    @patch('app.services.ai_service.settings')
    def test_anthropic_provider_initialization(self, mock_settings):
        """Test initialization with Anthropic provider"""
        mock_settings.AI_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_API_KEY = "test-key"

        with patch('app.services.ai_service.get_claude_service') as mock_get_claude:
            mock_get_claude.return_value = Mock()
            service = AIService()

            assert service.provider == "anthropic"
            assert service.claude_service is not None
            assert service.openrouter_service is None

    @patch('app.services.ai_service.settings')
    def test_openrouter_provider_initialization(self, mock_settings):
        """Test initialization with OpenRouter provider"""
        mock_settings.AI_PROVIDER = "openrouter"
        mock_settings.OPENROUTER_API_KEY = "test-key"

        with patch('app.services.ai_service.get_openrouter_service') as mock_get_openrouter:
            mock_get_openrouter.return_value = Mock()
            service = AIService()

            assert service.provider == "openrouter"
            assert service.openrouter_service is not None


class TestAIServiceAnalysisStrategies:
    """Test different analysis strategies"""

    @pytest.mark.asyncio
    async def test_claude_direct_analysis(self, sample_job_data, sample_analysis_result):
        """Test direct Claude API analysis"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"

            with patch('app.services.ai_service.get_claude_service') as mock_get_claude:
                mock_claude = AsyncMock()
                mock_claude.analyze_job_fit.return_value = sample_analysis_result
                mock_get_claude.return_value = mock_claude

                service = AIService()
                result = await service.analyze_job_fit(
                    job_description=sample_job_data["job_description"],
                    company=sample_job_data["company"],
                    job_title=sample_job_data["job_title"]
                )

                assert result["match_score"] == 85
                assert result["should_apply"] is True
                mock_claude.analyze_job_fit.assert_called_once()

    @pytest.mark.asyncio
    async def test_two_tier_analysis_high_score(self, sample_job_data, sample_analysis_result):
        """Test two-tier analysis when prescreening passes threshold"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "openrouter"
            mock_settings.USE_CHEAP_PRESCREENING = True
            mock_settings.CHEAP_MODEL_THRESHOLD = 60
            mock_settings.PRESCREENING_MODEL = "meta-llama/llama-3.1-8b-instruct"
            mock_settings.ANALYSIS_MODEL = "anthropic/claude-3.5-sonnet"
            mock_settings.MAX_COST_PER_JOB = 0.50

            with patch('app.services.ai_service.get_openrouter_service') as mock_get_openrouter:
                mock_openrouter = AsyncMock()

                # Prescreening returns score above threshold
                prescreening_result = sample_analysis_result.copy()
                prescreening_result["match_score"] = 75
                prescreening_result["prescreening_only"] = True

                # Final analysis returns full results
                final_result = sample_analysis_result.copy()
                final_result["match_score"] = 85
                final_result["used_prescreening"] = True

                mock_openrouter.analyze_job_with_model.side_effect = [
                    prescreening_result,  # First call: prescreening
                    final_result  # Second call: full analysis
                ]

                mock_get_openrouter.return_value = mock_openrouter

                service = AIService()
                result = await service.analyze_job_fit(
                    job_description=sample_job_data["job_description"],
                    company=sample_job_data["company"],
                    job_title=sample_job_data["job_title"],
                    use_prescreening=True
                )

                # Should have called analyze_job_with_model twice
                assert mock_openrouter.analyze_job_with_model.call_count == 2
                assert result["match_score"] == 85

    @pytest.mark.asyncio
    async def test_two_tier_analysis_low_score(self, sample_job_data_low_match, sample_low_score_analysis):
        """Test two-tier analysis when prescreening fails threshold"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "openrouter"
            mock_settings.USE_CHEAP_PRESCREENING = True
            mock_settings.CHEAP_MODEL_THRESHOLD = 60
            mock_settings.PRESCREENING_MODEL = "meta-llama/llama-3.1-8b-instruct"
            mock_settings.MAX_COST_PER_JOB = 0.50

            with patch('app.services.ai_service.get_openrouter_service') as mock_get_openrouter:
                mock_openrouter = AsyncMock()

                # Prescreening returns score below threshold
                prescreening_result = sample_low_score_analysis.copy()
                prescreening_result["match_score"] = 45
                prescreening_result["prescreening_only"] = True

                mock_openrouter.analyze_job_with_model.return_value = prescreening_result
                mock_get_openrouter.return_value = mock_openrouter

                service = AIService()
                result = await service.analyze_job_fit(
                    job_description=sample_job_data_low_match["job_description"],
                    company=sample_job_data_low_match["company"],
                    job_title=sample_job_data_low_match["job_title"],
                    use_prescreening=True
                )

                # Should only call prescreening model (once)
                assert mock_openrouter.analyze_job_with_model.call_count == 1
                assert result["match_score"] == 45
                assert result["should_apply"] is False

    @pytest.mark.asyncio
    async def test_ensemble_analysis(self, sample_job_data):
        """Test ensemble analysis with multiple models"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "openrouter"
            mock_settings.ENABLE_ENSEMBLE = True
            mock_settings.ENSEMBLE_MODELS = "anthropic/claude-3.5-sonnet,openai/gpt-4-turbo,google/gemini-pro-1.5"
            mock_settings.ensemble_models_list = [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4-turbo",
                "google/gemini-pro-1.5"
            ]

            with patch('app.services.ai_service.get_openrouter_service') as mock_get_openrouter:
                mock_openrouter = AsyncMock()

                ensemble_result = {
                    "match_score": 82,
                    "should_apply": True,
                    "ensemble_results": {
                        "individual_scores": [85, 78, 83],
                        "average_score": 82,
                        "confidence": "high",
                        "agreement": "strong"
                    }
                }

                mock_openrouter.ensemble_analysis.return_value = ensemble_result
                mock_get_openrouter.return_value = mock_openrouter

                service = AIService()
                result = await service.analyze_job_fit(
                    job_description=sample_job_data["job_description"],
                    company=sample_job_data["company"],
                    job_title=sample_job_data["job_title"],
                    use_ensemble=True
                )

                assert result["match_score"] == 82
                assert "ensemble_results" in result
                assert result["ensemble_results"]["confidence"] == "high"
                mock_openrouter.ensemble_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self, sample_job_data, sample_analysis_result):
        """Test automatic fallback when primary model fails"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "openrouter"
            mock_settings.ANALYSIS_MODEL = "anthropic/claude-3.5-sonnet"
            mock_settings.FALLBACK_MODEL = "google/gemini-pro-1.5"

            with patch('app.services.ai_service.get_openrouter_service') as mock_get_openrouter:
                mock_openrouter = AsyncMock()

                fallback_result = sample_analysis_result.copy()
                fallback_result["used_fallback"] = True
                fallback_result["fallback_model"] = "google/gemini-pro-1.5"

                mock_openrouter.analyze_with_fallback.return_value = fallback_result
                mock_get_openrouter.return_value = mock_openrouter

                service = AIService()
                result = await service.analyze_job_fit(
                    job_description=sample_job_data["job_description"],
                    company=sample_job_data["company"],
                    job_title=sample_job_data["job_title"]
                )

                assert result["match_score"] == 85
                mock_openrouter.analyze_with_fallback.assert_called_once()


class TestAIServiceCoverLetterGeneration:
    """Test cover letter generation"""

    @pytest.mark.asyncio
    async def test_cover_letter_generation_claude(self, sample_job_data, sample_analysis_result):
        """Test cover letter generation with Claude"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"

            with patch('app.services.ai_service.get_claude_service') as mock_get_claude:
                mock_claude = AsyncMock()
                mock_claude.generate_cover_letter.return_value = "Mock cover letter content..."
                mock_get_claude.return_value = mock_claude

                service = AIService()
                result = await service.generate_cover_letter(
                    job_data=sample_job_data,
                    analysis_results=sample_analysis_result,
                    style="conversational"
                )

                assert "Mock cover letter" in result
                mock_claude.generate_cover_letter.assert_called_once()

    @pytest.mark.asyncio
    async def test_cover_letter_generation_openrouter(self, sample_job_data, sample_analysis_result):
        """Test cover letter generation with OpenRouter"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "openrouter"
            mock_settings.COVER_LETTER_MODEL = "anthropic/claude-3.5-sonnet"

            with patch('app.services.ai_service.get_openrouter_service') as mock_get_openrouter:
                mock_openrouter = AsyncMock()
                mock_openrouter.generate_cover_letter.return_value = "Mock OpenRouter cover letter..."
                mock_get_openrouter.return_value = mock_openrouter

                service = AIService()
                result = await service.generate_cover_letter(
                    job_data=sample_job_data,
                    analysis_results=sample_analysis_result,
                    style="formal"
                )

                assert "Mock OpenRouter" in result
                mock_openrouter.generate_cover_letter.assert_called_once()


class TestAIServiceStatistics:
    """Test statistics tracking"""

    def test_get_stats_anthropic_provider(self):
        """Test stats with Anthropic provider"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"

            with patch('app.services.ai_service.get_claude_service') as mock_get_claude:
                mock_claude = Mock()
                mock_claude.get_stats.return_value = {
                    "total_api_calls": 50,
                    "total_tokens": 125000
                }
                mock_get_claude.return_value = mock_claude

                service = AIService()
                stats = service.get_stats()

                assert stats["provider"] == "anthropic"
                assert "anthropic" in stats
                assert stats["anthropic"]["total_api_calls"] == 50

    def test_get_stats_openrouter_provider(self):
        """Test stats with OpenRouter provider"""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "openrouter"
            mock_settings.USE_CHEAP_PRESCREENING = True
            mock_settings.ENABLE_ENSEMBLE = False
            mock_settings.MAX_COST_PER_JOB = 0.50

            with patch('app.services.ai_service.get_openrouter_service') as mock_get_openrouter:
                mock_openrouter = Mock()
                mock_openrouter.get_stats.return_value = {
                    "total_api_calls": 127,
                    "total_cost": 3.45,
                    "models_used": {
                        "meta-llama/llama-3.1-8b-instruct": 100,
                        "anthropic/claude-3.5-sonnet": 27
                    }
                }
                mock_get_openrouter.return_value = mock_openrouter

                service = AIService()
                stats = service.get_stats()

                assert stats["provider"] == "openrouter"
                assert stats["config"]["use_prescreening"] is True
                assert stats["openrouter"]["total_cost"] == 3.45
