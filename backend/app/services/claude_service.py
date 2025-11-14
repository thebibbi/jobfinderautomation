import anthropic
from typing import Dict, Any, List, Optional
import json
from loguru import logger
import csv
from pathlib import Path

from ..config import settings


class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.MAX_TOKENS

        # Load reference materials
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

            logger.info("✅ Reference materials loaded successfully")
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
        """Format reference materials for Claude"""
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

    async def analyze_job_fit(
        self,
        job_description: str,
        company: str,
        job_title: str
    ) -> Dict[str, Any]:
        """
        Analyze job fit using Claude with reference materials

        Returns:
            {
                "match_score": 0-100,
                "key_strengths": [...],
                "potential_gaps": [...],
                "transferable_skills": [...],
                "recommended_focus_areas": [...],
                "should_apply": bool,
                "reasoning": "...",
                "tailoring_suggestions": {...}
            }
        """
        from ..prompts.job_analysis import JOB_ANALYSIS_PROMPT

        try:
            # Format the complete prompt
            full_prompt = f"""
{self._format_reference_materials()}

<job_details>
<company>{company}</company>
<job_title>{job_title}</job_title>
<job_description>
{job_description}
</job_description>
</job_details>

{JOB_ANALYSIS_PROMPT}
"""

            logger.info(f"🤖 Analyzing job fit for: {company} - {job_title}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": full_prompt
                }]
            )

            # Extract response content
            response_text = response.content[0].text

            # Parse JSON from response
            analysis_result = self._parse_analysis_response(response_text)

            logger.info(f"✅ Analysis complete. Match score: {analysis_result.get('match_score')}%")

            return analysis_result

        except Exception as e:
            logger.error(f"❌ Error analyzing job: {e}")
            raise

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response and extract JSON"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, return structured error
                logger.warning("⚠️ No JSON found in response, returning default structure")
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


# Singleton instance
_claude_service = None

def get_claude_service() -> ClaudeService:
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeService()
    return _claude_service
