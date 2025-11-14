"""
Tests for Stats API endpoints (AI usage statistics)
"""
import pytest
from unittest.mock import patch, Mock
from fastapi import status


class TestStatsAPIAIEndpoint:
    """Test AI statistics endpoint"""

    def test_get_ai_stats_anthropic_provider(self, client):
        """Test GET /api/v1/stats/ai with Anthropic provider"""
        mock_stats = {
            "provider": "anthropic",
            "config": {
                "model": "claude-3-5-sonnet-20241022"
            },
            "anthropic": {
                "total_api_calls": 50,
                "total_tokens": 125000,
                "average_tokens_per_call": 2500
            }
        }

        with patch('app.api.stats.get_ai_service') as mock_get_ai:
            mock_ai_service = Mock()
            mock_ai_service.get_stats.return_value = mock_stats
            mock_get_ai.return_value = mock_ai_service

            response = client.get("/api/v1/stats/ai")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["stats"]["provider"] == "anthropic"
            assert data["stats"]["anthropic"]["total_api_calls"] == 50

    def test_get_ai_stats_openrouter_provider(self, client):
        """Test GET /api/v1/stats/ai with OpenRouter provider"""
        mock_stats = {
            "provider": "openrouter",
            "config": {
                "use_ensemble": False,
                "use_prescreening": True,
                "max_cost_per_job": 0.5
            },
            "openrouter": {
                "total_api_calls": 127,
                "total_cost": 3.45,
                "models_used": {
                    "meta-llama/llama-3.1-8b-instruct": 100,
                    "anthropic/claude-3.5-sonnet": 27
                },
                "average_cost_per_call": 0.027
            }
        }

        with patch('app.api.stats.get_ai_service') as mock_get_ai:
            mock_ai_service = Mock()
            mock_ai_service.get_stats.return_value = mock_stats
            mock_get_ai.return_value = mock_ai_service

            response = client.get("/api/v1/stats/ai")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["stats"]["provider"] == "openrouter"
            assert data["stats"]["openrouter"]["total_cost"] == 3.45
            assert data["stats"]["config"]["use_prescreening"] is True

    def test_get_ai_stats_with_ensemble_enabled(self, client):
        """Test AI stats when ensemble is enabled"""
        mock_stats = {
            "provider": "openrouter",
            "config": {
                "use_ensemble": True,
                "ensemble_models": [
                    "anthropic/claude-3.5-sonnet",
                    "openai/gpt-4-turbo",
                    "google/gemini-pro-1.5"
                ],
                "use_prescreening": False,
                "max_cost_per_job": 1.0
            },
            "openrouter": {
                "total_api_calls": 75,
                "total_cost": 12.50,
                "models_used": {
                    "anthropic/claude-3.5-sonnet": 25,
                    "openai/gpt-4-turbo": 25,
                    "google/gemini-pro-1.5": 25
                }
            }
        }

        with patch('app.api.stats.get_ai_service') as mock_get_ai:
            mock_ai_service = Mock()
            mock_ai_service.get_stats.return_value = mock_stats
            mock_get_ai.return_value = mock_ai_service

            response = client.get("/api/v1/stats/ai")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["stats"]["config"]["use_ensemble"] is True
            assert len(data["stats"]["config"]["ensemble_models"]) == 3


class TestStatsAPIComprehensiveEndpoint:
    """Test comprehensive stats endpoint"""

    def test_get_all_stats(self, client):
        """Test GET /api/v1/stats/ endpoint"""
        mock_ai_stats = {
            "provider": "openrouter",
            "config": {"use_prescreening": True},
            "openrouter": {"total_api_calls": 100, "total_cost": 2.50}
        }

        with patch('app.api.stats.get_ai_service') as mock_get_ai:
            mock_ai_service = Mock()
            mock_ai_service.get_stats.return_value = mock_ai_stats
            mock_get_ai.return_value = mock_ai_service

            response = client.get("/api/v1/stats/")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "ai" in data
            assert data["ai"]["provider"] == "openrouter"


class TestStatsAPICostTracking:
    """Test cost tracking in stats"""

    def test_cost_savings_from_prescreening(self, client):
        """Test that prescreening cost savings are tracked"""
        mock_stats = {
            "provider": "openrouter",
            "config": {
                "use_prescreening": True,
                "cheap_model_threshold": 60
            },
            "openrouter": {
                "total_api_calls": 150,
                "total_cost": 4.75,
                "prescreening_stats": {
                    "total_prescreening_calls": 100,
                    "passed_threshold": 30,
                    "failed_threshold": 70,
                    "estimated_savings": 10.50  # Money saved by not analyzing 70 jobs
                }
            }
        }

        with patch('app.api.stats.get_ai_service') as mock_get_ai:
            mock_ai_service = Mock()
            mock_ai_service.get_stats.return_value = mock_stats
            mock_get_ai.return_value = mock_ai_service

            response = client.get("/api/v1/stats/ai")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            prescreening = data["stats"]["openrouter"]["prescreening_stats"]
            assert prescreening["failed_threshold"] == 70
            assert prescreening["estimated_savings"] == 10.50

    def test_model_usage_breakdown(self, client):
        """Test model usage breakdown in stats"""
        mock_stats = {
            "provider": "openrouter",
            "config": {},
            "openrouter": {
                "total_api_calls": 127,
                "total_cost": 3.45,
                "models_used": {
                    "meta-llama/llama-3.1-8b-instruct": 100,
                    "anthropic/claude-3.5-sonnet": 27
                },
                "cost_by_model": {
                    "meta-llama/llama-3.1-8b-instruct": 0.20,
                    "anthropic/claude-3.5-sonnet": 3.25
                }
            }
        }

        with patch('app.api.stats.get_ai_service') as mock_get_ai:
            mock_ai_service = Mock()
            mock_ai_service.get_stats.return_value = mock_stats
            mock_get_ai.return_value = mock_ai_service

            response = client.get("/api/v1/stats/ai")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            models_used = data["stats"]["openrouter"]["models_used"]
            assert models_used["meta-llama/llama-3.1-8b-instruct"] == 100
            assert models_used["anthropic/claude-3.5-sonnet"] == 27


class TestStatsAPIErrorHandling:
    """Test error handling in stats API"""

    def test_stats_service_error(self, client):
        """Test handling of service errors"""
        with patch('app.api.stats.get_ai_service') as mock_get_ai:
            mock_ai_service = Mock()
            mock_ai_service.get_stats.side_effect = Exception("Service error")
            mock_get_ai.return_value = mock_ai_service

            response = client.get("/api/v1/stats/ai")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
