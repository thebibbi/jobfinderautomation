import httpx
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime
import csv
from pathlib import Path

from ..config import settings


class OpenRouterService:
    """
    Service for interacting with OpenRouter API
    Supports multiple LLM providers through unified interface
    """

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/jobautomation",  # Optional
            "X-Title": "Job Automation System",  # Optional
        }

        # Cost tracking
        self.total_cost = 0.0
        self.api_calls = 0

        # Load reference materials (same as Claude service)
        self.skills_path = Path(__file__).parent.parent.parent.parent / "skills" / "job-match-analyzer"
        self._load_reference_materials()

    def _load_reference_materials(self):
        """Load all CSV reference materials"""
        try:
            self.experience_inventory = self._load_csv(self.skills_path / "experience_inventory.csv")
            self.skills_taxonomy = self._load_csv(self.skills_path / "skills_taxonomy.csv")
            self.corporate_translation = self._load_csv(self.skills_path / "corporate_translation.csv")
            self.achievement_library = self._load_csv(self.skills_path / "achievement_library.csv")

            # Load skill instructions
            skill_md_path = self.skills_path / "SKILL.md"
            if skill_md_path.exists():
                with open(skill_md_path, 'r') as f:
                    self.skill_instructions = f.read()
            else:
                self.skill_instructions = ""

            logger.info("✅ Reference materials loaded for OpenRouter")
        except Exception as e:
            logger.error(f"❌ Error loading reference materials: {e}")
            raise

    def _load_csv(self, path: Path) -> List[Dict[str, Any]]:
        """Load CSV file into list of dicts"""
        if not path.exists():
            logger.warning(f"⚠️ CSV file not found: {path}")
            return []

        with open(path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def _format_reference_materials(self) -> str:
        """Format reference materials for prompt"""
        return f"""
<reference_materials>

<skill_instructions>
{self.skill_instructions}
</skill_instructions>

<experience_inventory>
{json.dumps(self.experience_inventory, indent=2)}
</experience_inventory>

<skills_taxonomy>
{json.dumps(self.skills_taxonomy, indent=2)}
</skills_taxonomy>

<corporate_translation>
{json.dumps(self.corporate_translation, indent=2)}
</corporate_translation>

<achievement_library>
{json.dumps(self.achievement_library, indent=2)}
</achievement_library>

</reference_materials>
"""

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 8000,
        temperature: float = 0.7,
        track_cost: bool = True
    ) -> Dict[str, Any]:
        """
        Make a chat completion request to OpenRouter

        Args:
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            track_cost: Whether to track API cost

        Returns:
            Response dict with content and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }

                logger.info(f"🤖 Calling OpenRouter with model: {model}")

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )

                response.raise_for_status()
                result = response.json()

                # Extract content
                content = result["choices"][0]["message"]["content"]

                # Track cost if enabled
                if track_cost and settings.ENABLE_COST_TRACKING:
                    usage = result.get("usage", {})
                    self._track_api_call(model, usage)

                self.api_calls += 1

                return {
                    "content": content,
                    "model": model,
                    "usage": result.get("usage", {}),
                    "id": result.get("id"),
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ OpenRouter API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Error calling OpenRouter: {e}")
            raise

    def _track_api_call(self, model: str, usage: Dict[str, int]):
        """Track API call costs"""
        # OpenRouter provides cost in the response, or you can estimate
        # For now, we'll log the usage
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        logger.info(f"📊 API Call - Model: {model}, Tokens: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})")

        # You can implement detailed cost calculation based on model pricing
        # OpenRouter pricing: https://openrouter.ai/models

    async def analyze_job_with_model(
        self,
        model: str,
        job_description: str,
        company: str,
        job_title: str,
        prompt_template: str
    ) -> Dict[str, Any]:
        """
        Analyze job fit using a specific model

        Args:
            model: OpenRouter model identifier
            job_description: Full job description
            company: Company name
            job_title: Job title
            prompt_template: Analysis prompt template

        Returns:
            Analysis results dict
        """
        try:
            # Build full prompt
            full_prompt = f"""
{self._format_reference_materials()}

<job_details>
<company>{company}</company>
<job_title>{job_title}</job_title>
<job_description>
{job_description}
</job_description>
</job_details>

{prompt_template}
"""

            messages = [
                {"role": "user", "content": full_prompt}
            ]

            # Make API call
            response = await self.chat_completion(
                model=model,
                messages=messages,
                max_tokens=8000,
                temperature=0.5
            )

            # Parse response
            analysis_result = self._parse_analysis_response(response["content"])
            analysis_result["_model_used"] = model
            analysis_result["_tokens_used"] = response.get("usage", {})

            return analysis_result

        except Exception as e:
            logger.error(f"❌ Error analyzing with model {model}: {e}")
            raise

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse model response and extract JSON"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning("⚠️ No JSON found in response")
                return {
                    "match_score": 0,
                    "key_strengths": [],
                    "potential_gaps": [],
                    "should_apply": False,
                    "reasoning": "Unable to parse analysis response",
                    "raw_response": response_text
                }
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing JSON: {e}")
            return {
                "match_score": 0,
                "error": str(e),
                "raw_response": response_text
            }

    async def analyze_with_fallback(
        self,
        job_description: str,
        company: str,
        job_title: str,
        prompt_template: str,
        primary_model: str,
        fallback_model: str
    ) -> Dict[str, Any]:
        """
        Analyze job with primary model, fallback to secondary on failure

        Args:
            job_description: Full job description
            company: Company name
            job_title: Job title
            prompt_template: Analysis prompt
            primary_model: Primary model to use
            fallback_model: Fallback model if primary fails

        Returns:
            Analysis results
        """
        try:
            # Try primary model
            logger.info(f"🎯 Attempting analysis with primary model: {primary_model}")
            result = await self.analyze_job_with_model(
                model=primary_model,
                job_description=job_description,
                company=company,
                job_title=job_title,
                prompt_template=prompt_template
            )
            result["_fallback_used"] = False
            return result

        except Exception as e:
            logger.warning(f"⚠️ Primary model failed: {e}")
            logger.info(f"🔄 Falling back to: {fallback_model}")

            try:
                # Try fallback model
                result = await self.analyze_job_with_model(
                    model=fallback_model,
                    job_description=job_description,
                    company=company,
                    job_title=job_title,
                    prompt_template=prompt_template
                )
                result["_fallback_used"] = True
                result["_fallback_reason"] = str(e)
                return result

            except Exception as fallback_error:
                logger.error(f"❌ Fallback model also failed: {fallback_error}")
                raise

    async def ensemble_analysis(
        self,
        job_description: str,
        company: str,
        job_title: str,
        prompt_template: str,
        models: List[str]
    ) -> Dict[str, Any]:
        """
        Run analysis with multiple models and combine results

        Args:
            job_description: Full job description
            company: Company name
            job_title: Job title
            prompt_template: Analysis prompt
            models: List of models to use

        Returns:
            Combined analysis results
        """
        logger.info(f"🎭 Running ensemble analysis with {len(models)} models")

        results = []

        # Analyze with each model
        for model in models:
            try:
                result = await self.analyze_job_with_model(
                    model=model,
                    job_description=job_description,
                    company=company,
                    job_title=job_title,
                    prompt_template=prompt_template
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"⚠️ Model {model} failed in ensemble: {e}")
                continue

        if not results:
            raise Exception("All models in ensemble failed")

        # Combine results
        combined = self._combine_ensemble_results(results)
        combined["_ensemble_models"] = [r.get("_model_used") for r in results]
        combined["_ensemble_count"] = len(results)

        logger.info(f"✅ Ensemble complete. Combined score: {combined['match_score']}")

        return combined

    def _combine_ensemble_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine multiple analysis results using voting/averaging

        Strategy:
        - Average match scores
        - Combine strengths and gaps (deduplicate)
        - Take majority vote on should_apply
        - Merge all reasoning
        """
        # Average match scores
        scores = [r.get("match_score", 0) for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Combine strengths (deduplicate by strength name)
        all_strengths = []
        for r in results:
            all_strengths.extend(r.get("key_strengths", []))

        # Deduplicate strengths
        unique_strengths = {}
        for s in all_strengths:
            if isinstance(s, dict):
                key = s.get("strength", "")
                if key and key not in unique_strengths:
                    unique_strengths[key] = s

        # Combine gaps
        all_gaps = []
        for r in results:
            all_gaps.extend(r.get("potential_gaps", []))

        unique_gaps = {}
        for g in all_gaps:
            if isinstance(g, dict):
                key = g.get("gap", "")
                if key and key not in unique_gaps:
                    unique_gaps[key] = g

        # Majority vote on should_apply
        should_apply_votes = [r.get("should_apply", False) for r in results]
        should_apply = sum(should_apply_votes) > len(should_apply_votes) / 2

        # Combine reasoning
        all_reasoning = [r.get("reasoning", "") for r in results if r.get("reasoning")]
        combined_reasoning = "\n\n---\n\n".join(all_reasoning)

        return {
            "match_score": round(avg_score, 2),
            "key_strengths": list(unique_strengths.values())[:5],  # Top 5
            "potential_gaps": list(unique_gaps.values())[:3],  # Top 3
            "should_apply": should_apply,
            "reasoning": combined_reasoning,
            "match_level": self._get_match_level(avg_score),
            "ensemble_scores": scores,
            "score_variance": round(max(scores) - min(scores), 2) if scores else 0
        }

    def _get_match_level(self, score: float) -> str:
        """Convert score to match level"""
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 55:
            return "moderate"
        elif score >= 40:
            return "stretch"
        else:
            return "poor"

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_api_calls": self.api_calls,
            "total_cost": round(self.total_cost, 4),
        }


# Singleton
_openrouter_service = None

def get_openrouter_service() -> OpenRouterService:
    global _openrouter_service
    if _openrouter_service is None:
        _openrouter_service = OpenRouterService()
    return _openrouter_service
