from typing import Dict, Any
from loguru import logger

from ..config import settings
from .claude_service import get_claude_service
from .openrouter_service import get_openrouter_service


class AIService:
    """
    Unified AI service that routes between different providers
    Implements intelligent model selection and cost optimization
    """

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.claude_service = None
        self.openrouter_service = None

        # Initialize appropriate service
        if self.provider == "anthropic":
            self.claude_service = get_claude_service()
            logger.info("🤖 Using Anthropic Claude directly")
        elif self.provider == "openrouter":
            self.openrouter_service = get_openrouter_service()
            logger.info("🌐 Using OpenRouter multi-provider")
        else:
            logger.warning(f"⚠️ Unknown provider: {self.provider}, defaulting to Claude")
            self.claude_service = get_claude_service()

    async def analyze_job_fit(
        self,
        job_description: str,
        company: str,
        job_title: str,
        use_ensemble: bool = None,
        use_prescreening: bool = None
    ) -> Dict[str, Any]:
        """
        Analyze job fit with intelligent model routing

        Args:
            job_description: Full job description
            company: Company name
            job_title: Job title
            use_ensemble: Override to enable/disable ensemble (None = use config)
            use_prescreening: Override to enable/disable prescreening (None = use config)

        Returns:
            Analysis results with match score and recommendations
        """
        # Use config defaults if not specified
        if use_ensemble is None:
            use_ensemble = settings.ENABLE_ENSEMBLE
        if use_prescreening is None:
            use_prescreening = settings.USE_CHEAP_PRESCREENING

        logger.info(f"🔍 Analyzing job: {company} - {job_title}")
        logger.info(f"   Provider: {self.provider}, Ensemble: {use_ensemble}, Prescreening: {use_prescreening}")

        from ..prompts.job_analysis import JOB_ANALYSIS_PROMPT

        # STRATEGY 1: Two-tier analysis with cheap prescreening
        if use_prescreening and self.provider == "openrouter":
            return await self._two_tier_analysis(
                job_description, company, job_title, JOB_ANALYSIS_PROMPT
            )

        # STRATEGY 2: Ensemble analysis with multiple models
        elif use_ensemble and self.provider == "openrouter":
            return await self._ensemble_analysis(
                job_description, company, job_title, JOB_ANALYSIS_PROMPT
            )

        # STRATEGY 3: Single model with fallback (OpenRouter)
        elif self.provider == "openrouter":
            return await self._openrouter_analysis_with_fallback(
                job_description, company, job_title, JOB_ANALYSIS_PROMPT
            )

        # STRATEGY 4: Direct Claude API (original)
        else:
            return await self._claude_analysis(
                job_description, company, job_title
            )

    async def _two_tier_analysis(
        self,
        job_description: str,
        company: str,
        job_title: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Two-tier analysis: cheap model first, then expensive if promising

        This can save significant costs by filtering out poor matches early
        """
        logger.info("💡 Using two-tier analysis strategy")

        # Tier 1: Quick prescreening with cheap model
        logger.info(f"   Tier 1: Prescreening with {settings.PRESCREENING_MODEL}")

        prescreening_result = await self.openrouter_service.analyze_job_with_model(
            model=settings.PRESCREENING_MODEL,
            job_description=job_description,
            company=company,
            job_title=job_title,
            prompt_template=prompt
        )

        prescreening_score = prescreening_result.get("match_score", 0)
        logger.info(f"   📊 Prescreening score: {prescreening_score}")

        # Check if job passes threshold
        if prescreening_score < settings.CHEAP_MODEL_THRESHOLD:
            logger.info(f"   ⏭️ Job scored below threshold ({settings.CHEAP_MODEL_THRESHOLD}), skipping expensive analysis")
            prescreening_result["_analysis_tier"] = "prescreening_only"
            prescreening_result["_cost_saved"] = True
            return prescreening_result

        # Tier 2: Deep analysis with expensive model
        logger.info(f"   Tier 2: Deep analysis with {settings.ANALYSIS_MODEL}")

        deep_result = await self.openrouter_service.analyze_job_with_model(
            model=settings.ANALYSIS_MODEL,
            job_description=job_description,
            company=company,
            job_title=job_title,
            prompt_template=prompt
        )

        deep_result["_analysis_tier"] = "deep_analysis"
        deep_result["_prescreening_score"] = prescreening_score
        deep_result["_cost_saved"] = False

        return deep_result

    async def _ensemble_analysis(
        self,
        job_description: str,
        company: str,
        job_title: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Ensemble analysis using multiple models

        Combines scores from multiple models for more robust results
        """
        logger.info("🎭 Using ensemble analysis strategy")

        models = settings.ensemble_models_list
        if not models:
            logger.warning("⚠️ No ensemble models configured, falling back to single model")
            return await self._openrouter_analysis_with_fallback(
                job_description, company, job_title, prompt
            )

        result = await self.openrouter_service.ensemble_analysis(
            job_description=job_description,
            company=company,
            job_title=job_title,
            prompt_template=prompt,
            models=models
        )

        result["_strategy"] = "ensemble"
        return result

    async def _openrouter_analysis_with_fallback(
        self,
        job_description: str,
        company: str,
        job_title: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Single model analysis via OpenRouter with fallback

        Uses primary analysis model with fallback to backup model
        """
        logger.info("🎯 Using single model with fallback strategy")

        result = await self.openrouter_service.analyze_with_fallback(
            job_description=job_description,
            company=company,
            job_title=job_title,
            prompt_template=prompt,
            primary_model=settings.ANALYSIS_MODEL,
            fallback_model=settings.FALLBACK_MODEL
        )

        result["_strategy"] = "single_with_fallback"
        return result

    async def _claude_analysis(
        self,
        job_description: str,
        company: str,
        job_title: str
    ) -> Dict[str, Any]:
        """
        Direct Claude API analysis (original implementation)

        Uses Anthropic's Claude API directly
        """
        logger.info("🤖 Using direct Claude API")

        result = await self.claude_service.analyze_job_fit(
            job_description=job_description,
            company=company,
            job_title=job_title
        )

        result["_strategy"] = "claude_direct"
        return result

    async def generate_cover_letter(
        self,
        job_data: Dict[str, Any],
        analysis_results: Dict[str, Any],
        style: str = "conversational"
    ) -> str:
        """
        Generate cover letter using appropriate model

        Uses configured cover letter model or Claude
        """
        from ..prompts.cover_letter import COVER_LETTER_PROMPT
        import json
        from pathlib import Path

        # Load voice profile
        voice_profile_path = Path(__file__).parent.parent.parent.parent / "skills" / "voice_profile.md"
        with open(voice_profile_path, 'r') as f:
            voice_profile = f.read()

        # Get guidance
        guidance = analysis_results.get("cover_letter_guidance", {})

        # Build prompt
        full_prompt = f"""
{voice_profile}

<job_details>
<company>{job_data['company']}</company>
<job_title>{job_data['job_title']}</job_title>
<job_description>
{job_data['job_description']}
</job_description>
</job_details>

<analysis_guidance>
{json.dumps(guidance, indent=2)}
</analysis_guidance>

<style>{style}</style>

{COVER_LETTER_PROMPT}
"""

        if self.provider == "openrouter":
            # Use OpenRouter with cover letter model
            response = await self.openrouter_service.chat_completion(
                model=settings.COVER_LETTER_MODEL,
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=8000,
                temperature=0.7
            )
            return response["content"]
        else:
            # Use Claude directly
            response = self.claude_service.client.messages.create(
                model=self.claude_service.model,
                max_tokens=self.claude_service.max_tokens,
                messages=[{"role": "user", "content": full_prompt}]
            )
            return response.content[0].text

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics from all services"""
        stats = {
            "provider": self.provider,
            "config": {
                "use_ensemble": settings.ENABLE_ENSEMBLE,
                "use_prescreening": settings.USE_CHEAP_PRESCREENING,
                "max_cost_per_job": settings.MAX_COST_PER_JOB,
            }
        }

        if self.openrouter_service:
            stats["openrouter"] = self.openrouter_service.get_stats()

        return stats


# Singleton
_ai_service = None

def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
