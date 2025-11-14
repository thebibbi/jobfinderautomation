from sentence_transformers import SentenceTransformer, util
import numpy as np
from typing import List, Dict, Any, Tuple
from loguru import logger
import torch

from ..config import settings


class SemanticMatcher:
    """
    Semantic matching service for job-candidate alignment
    Uses sentence transformers to compute similarity
    """

    def __init__(self):
        # Use a model optimized for semantic search
        self.model_name = 'all-MiniLM-L6-v2'  # Fast and effective
        logger.info(f"🤖 Loading semantic model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

        # Cache for candidate profile embedding
        self._candidate_embedding = None
        self._candidate_profile = None

    def _build_candidate_profile(self) -> str:
        """
        Build comprehensive candidate profile from reference materials
        """
        from pathlib import Path
        import csv

        skills_path = Path(__file__).parent.parent.parent.parent / "skills" / "job-match-analyzer"

        profile_parts = []

        # Load experience inventory
        try:
            with open(skills_path / "experience_inventory.csv", 'r') as f:
                reader = csv.DictReader(f)
                experiences = list(reader)
                profile_parts.append("EXPERIENCE:")
                for exp in experiences:
                    profile_parts.append(f"- {exp.get('role', '')} at {exp.get('organization', '')}: {exp.get('responsibilities', '')}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load experience inventory: {e}")

        # Load skills taxonomy
        try:
            with open(skills_path / "skills_taxonomy.csv", 'r') as f:
                reader = csv.DictReader(f)
                skills = list(reader)
                profile_parts.append("\nSKILLS:")
                skill_list = [s.get('skill', '') for s in skills if s.get('skill')]
                profile_parts.append(", ".join(skill_list))
        except Exception as e:
            logger.warning(f"⚠️ Could not load skills taxonomy: {e}")

        # Load achievements
        try:
            with open(skills_path / "achievement_library.csv", 'r') as f:
                reader = csv.DictReader(f)
                achievements = list(reader)
                profile_parts.append("\nACHIEVEMENTS:")
                for ach in achievements[:10]:  # Top 10 achievements
                    profile_parts.append(f"- {ach.get('achievement', '')}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load achievements: {e}")

        # Add target roles and preferences
        profile_parts.append("\nTARGET ROLES:")
        profile_parts.append("Business Analyst, Operations Analyst, Operations Manager, Risk Analyst, Product Manager, L&D Manager")

        profile_parts.append("\nCAREER TRANSITION:")
        profile_parts.append("Transitioning from education sector to corporate roles. Strong quantitative background with Masters in Mathematics. Experience in data analysis, project management, stakeholder communication, and process improvement.")

        return "\n".join(profile_parts)

    def get_candidate_embedding(self) -> np.ndarray:
        """Get or create candidate profile embedding"""
        if self._candidate_embedding is None:
            profile = self._build_candidate_profile()
            logger.info("🔄 Creating candidate profile embedding...")
            self._candidate_embedding = self.model.encode(
                profile,
                convert_to_tensor=True,
                show_progress_bar=False
            )
            self._candidate_profile = profile
            logger.info("✅ Candidate embedding created")

        return self._candidate_embedding

    def compute_job_similarity(
        self,
        job_title: str,
        job_description: str,
        company: str = ""
    ) -> float:
        """
        Compute semantic similarity between job and candidate

        Returns:
            Similarity score (0-100)
        """
        try:
            # Build job text
            job_text = f"JOB TITLE: {job_title}\n"
            if company:
                job_text += f"COMPANY: {company}\n"
            job_text += f"DESCRIPTION: {job_description}"

            # Get embeddings
            candidate_emb = self.get_candidate_embedding()
            job_emb = self.model.encode(
                job_text,
                convert_to_tensor=True,
                show_progress_bar=False
            )

            # Compute cosine similarity
            similarity = util.cos_sim(candidate_emb, job_emb)[0][0].item()

            # Convert to 0-100 scale
            score = similarity * 100

            logger.debug(f"📊 Semantic similarity for '{job_title}': {score:.2f}%")

            return score

        except Exception as e:
            logger.error(f"❌ Error computing similarity: {e}")
            return 0.0

    def rank_jobs(
        self,
        jobs: List[Dict[str, Any]],
        min_score: float = 30.0
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank jobs by semantic similarity

        Args:
            jobs: List of job dictionaries with 'job_title' and 'job_description'
            min_score: Minimum similarity score to include

        Returns:
            List of (job, score) tuples, sorted by score descending
        """
        scored_jobs = []

        for job in jobs:
            score = self.compute_job_similarity(
                job_title=job.get('job_title', ''),
                job_description=job.get('job_description', ''),
                company=job.get('company', '')
            )

            if score >= min_score:
                scored_jobs.append((job, score))

        # Sort by score descending
        scored_jobs.sort(key=lambda x: x[1], reverse=True)

        return scored_jobs


# Singleton
_semantic_matcher = None

def get_semantic_matcher() -> SemanticMatcher:
    global _semantic_matcher
    if _semantic_matcher is None:
        _semantic_matcher = SemanticMatcher()
    return _semantic_matcher
