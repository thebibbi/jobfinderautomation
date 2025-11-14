"""
Skills Gap Analysis Service

Analyze skill gaps, recommend learning paths, and track progress.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from ..models.skills import (
    CandidateSkill, JobSkillRequirement, SkillGap, LearningResource,
    LearningPlan, SkillProgress, SkillAssessment, SkillGapAnalysis,
    SkillLevel, SkillCategory, GapSeverity
)
from ..models.job import Job
from ..schemas.skills import (
    MatchedSkillDetail, GapSkillDetail, SkillGapAnalysisResult,
    LearningResource as LearningResourceSchema
)


class SkillsService:
    """Skills gap analysis and learning management"""

    # Skill level progression
    SKILL_LEVELS_ORDER = {
        SkillLevel.BEGINNER: 1,
        SkillLevel.INTERMEDIATE: 2,
        SkillLevel.ADVANCED: 3,
        SkillLevel.EXPERT: 4
    }

    # Learning time estimates (hours per level jump)
    LEARNING_HOURS = {
        ("beginner", "intermediate"): 40,
        ("beginner", "advanced"): 120,
        ("beginner", "expert"): 300,
        ("intermediate", "advanced"): 80,
        ("intermediate", "expert"): 200,
        ("advanced", "expert"): 150
    }

    def __init__(self, db: Session):
        self.db = db

    # ==================== Skill Gap Analysis ====================

    def analyze_skill_gaps(
        self,
        job_id: int,
        include_resources: bool = True
    ) -> SkillGapAnalysisResult:
        """
        Comprehensive skill gap analysis for a job

        Args:
            job_id: Job to analyze against
            include_resources: Include learning resource recommendations

        Returns:
            Complete analysis with gaps and recommendations
        """
        logger.info(f"Analyzing skill gaps for job {job_id}")

        # Get job details
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Get job requirements
        job_requirements = self.db.query(JobSkillRequirement).filter(
            JobSkillRequirement.job_id == job_id
        ).all()

        if not job_requirements:
            # Try to extract skills from job description
            job_requirements = self._extract_skills_from_job(job)

        # Get candidate skills
        candidate_skills = self.db.query(CandidateSkill).filter(
            CandidateSkill.is_active == True
        ).all()

        # Create skill map
        candidate_skill_map = {
            skill.skill_name.lower(): skill for skill in candidate_skills
        }

        # Analyze each requirement
        matched_skills = []
        partial_skills = []
        missing_skills = []

        for req in job_requirements:
            skill_name_lower = req.skill_name.lower()
            candidate_skill = candidate_skill_map.get(skill_name_lower)

            if candidate_skill:
                # Calculate match quality
                match_quality = self._compare_skill_levels(
                    candidate_skill.proficiency_level,
                    req.required_level
                )

                if match_quality in ["perfect", "exceeds"]:
                    # Perfect match
                    matched_skills.append(MatchedSkillDetail(
                        skill_name=req.skill_name,
                        required_level=req.required_level,
                        candidate_level=candidate_skill.proficiency_level,
                        match_quality=match_quality,
                        years_required=req.years_required,
                        candidate_years=candidate_skill.years_experience
                    ))
                else:
                    # Partial match - has skill but below required level
                    gap_severity = self._calculate_gap_severity(
                        candidate_skill.proficiency_level,
                        req.required_level,
                        req.is_required
                    )

                    learning_time = self._estimate_learning_time(
                        candidate_skill.proficiency_level,
                        req.required_level
                    )

                    gap_detail = GapSkillDetail(
                        skill_name=req.skill_name,
                        required_level=req.required_level,
                        candidate_level=candidate_skill.proficiency_level,
                        gap_severity=gap_severity,
                        is_required=req.is_required,
                        is_dealbreaker=req.is_required and gap_severity == GapSeverity.CRITICAL,
                        learning_time_hours=learning_time,
                        difficulty=self._estimate_difficulty(
                            candidate_skill.proficiency_level,
                            req.required_level
                        ),
                        resources=[]
                    )

                    partial_skills.append(gap_detail)
            else:
                # Missing skill
                gap_severity = self._calculate_gap_severity(
                    None,
                    req.required_level,
                    req.is_required
                )

                learning_time = self._estimate_learning_time(
                    None,
                    req.required_level
                )

                gap_detail = GapSkillDetail(
                    skill_name=req.skill_name,
                    required_level=req.required_level,
                    candidate_level=None,
                    gap_severity=gap_severity,
                    is_required=req.is_required,
                    is_dealbreaker=req.is_required and gap_severity == GapSeverity.CRITICAL,
                    learning_time_hours=learning_time,
                    difficulty=self._estimate_difficulty(None, req.required_level),
                    resources=[]
                )

                missing_skills.append(gap_detail)

        # Add learning resources if requested
        if include_resources:
            for gap in partial_skills + missing_skills:
                resources = self._find_learning_resources(
                    gap.skill_name,
                    gap.candidate_level,
                    gap.required_level,
                    limit=3
                )
                gap.resources = resources

            for gap in missing_skills:
                resources = self._find_learning_resources(
                    gap.skill_name,
                    None,
                    gap.required_level,
                    limit=3
                )
                gap.resources = resources

        # Calculate scores
        total_required = len(job_requirements)
        matched_count = len(matched_skills)
        partial_count = len(partial_skills)
        missing_count = len(missing_skills)

        # Required vs nice-to-have
        required_skills = [r for r in job_requirements if r.is_required]
        nice_to_have = [r for r in job_requirements if not r.is_required]

        required_matched = sum(1 for m in matched_skills if any(
            m.skill_name.lower() == r.skill_name.lower() for r in required_skills
        ))
        required_total = len(required_skills)

        overall_match_score = ((matched_count + (partial_count * 0.5)) / total_required * 100) if total_required > 0 else 0
        required_skills_score = (required_matched / required_total * 100) if required_total > 0 else 100
        nice_to_have_score = ((matched_count - required_matched) / len(nice_to_have) * 100) if len(nice_to_have) > 0 else 100

        # Count gaps by severity
        all_gaps = partial_skills + missing_skills
        critical_gaps = sum(1 for g in all_gaps if g.gap_severity == GapSeverity.CRITICAL)
        high_gaps = sum(1 for g in all_gaps if g.gap_severity == GapSeverity.HIGH)
        medium_gaps = sum(1 for g in all_gaps if g.gap_severity == GapSeverity.MEDIUM)
        low_gaps = sum(1 for g in all_gaps if g.gap_severity == GapSeverity.LOW)

        # Calculate total learning time
        total_learning_hours = sum(
            gap.learning_time_hours for gap in all_gaps if gap.learning_time_hours
        )

        # Estimate ready date (assuming 10 hours/week)
        estimated_ready_date = None
        if total_learning_hours:
            weeks_needed = total_learning_hours / 10
            estimated_ready_date = datetime.utcnow() + timedelta(weeks=weeks_needed)

        # Generate recommendation
        recommendation, reason = self._generate_recommendation(
            overall_match_score,
            required_skills_score,
            critical_gaps,
            high_gaps,
            total_learning_hours
        )

        # Learning priority (ordered by severity and importance)
        learning_priority = self._prioritize_learning(all_gaps, required_skills)

        # Identify strengths and improvements
        strength_areas = self._identify_strengths(matched_skills, candidate_skills)
        improvement_areas = [gap.skill_name for gap in all_gaps[:5]]  # Top 5

        # Create analysis record
        analysis = SkillGapAnalysis(
            job_id=job_id,
            total_skills_required=total_required,
            skills_matched=matched_count,
            skills_partial_match=partial_count,
            skills_missing=missing_count,
            overall_match_score=overall_match_score,
            required_skills_score=required_skills_score,
            nice_to_have_score=nice_to_have_score,
            critical_gaps=critical_gaps,
            high_priority_gaps=high_gaps,
            medium_priority_gaps=medium_gaps,
            low_priority_gaps=low_gaps,
            total_learning_hours=total_learning_hours,
            estimated_ready_date=estimated_ready_date,
            recommendation=recommendation,
            recommendation_reason=reason,
            learning_priority=learning_priority,
            matched_skills=[m.dict() for m in matched_skills],
            partial_skills=[p.dict() for p in partial_skills],
            missing_skills=[m.dict() for m in missing_skills],
            strength_areas=strength_areas,
            improvement_areas=improvement_areas
        )
        self.db.add(analysis)
        self.db.commit()

        return SkillGapAnalysisResult(
            job_id=job_id,
            job_title=job.title,
            company=job.company or "Unknown",
            total_skills_required=total_required,
            skills_matched=matched_count,
            skills_partial_match=partial_count,
            skills_missing=missing_count,
            overall_match_score=overall_match_score,
            required_skills_score=required_skills_score,
            nice_to_have_score=nice_to_have_score,
            critical_gaps=critical_gaps,
            high_priority_gaps=high_gaps,
            medium_priority_gaps=medium_gaps,
            low_priority_gaps=low_gaps,
            matched_skills=matched_skills,
            partial_skills=partial_skills,
            missing_skills=missing_skills,
            recommendation=recommendation,
            recommendation_reason=reason,
            learning_priority=learning_priority,
            total_learning_hours=total_learning_hours,
            estimated_ready_date=estimated_ready_date,
            strength_areas=strength_areas,
            improvement_areas=improvement_areas,
            analysis_date=datetime.utcnow()
        )

    # ==================== Helper Methods ====================

    def _compare_skill_levels(
        self,
        candidate_level: SkillLevel,
        required_level: SkillLevel
    ) -> str:
        """Compare skill levels"""
        candidate_value = self.SKILL_LEVELS_ORDER[candidate_level]
        required_value = self.SKILL_LEVELS_ORDER[required_level]

        if candidate_value == required_value:
            return "perfect"
        elif candidate_value > required_value:
            return "exceeds"
        elif candidate_value == required_value - 1:
            return "close"
        else:
            return "gap"

    def _calculate_gap_severity(
        self,
        current_level: Optional[SkillLevel],
        required_level: SkillLevel,
        is_required: bool
    ) -> GapSeverity:
        """Calculate severity of skill gap"""
        if current_level is None:
            # Missing skill
            if is_required:
                if required_level in [SkillLevel.ADVANCED, SkillLevel.EXPERT]:
                    return GapSeverity.CRITICAL
                else:
                    return GapSeverity.HIGH
            else:
                return GapSeverity.MEDIUM
        else:
            # Has skill but not at required level
            current_value = self.SKILL_LEVELS_ORDER[current_level]
            required_value = self.SKILL_LEVELS_ORDER[required_level]
            gap = required_value - current_value

            if gap >= 2:
                return GapSeverity.HIGH if is_required else GapSeverity.MEDIUM
            elif gap == 1:
                return GapSeverity.MEDIUM if is_required else GapSeverity.LOW
            else:
                return GapSeverity.LOW

    def _estimate_learning_time(
        self,
        current_level: Optional[SkillLevel],
        target_level: SkillLevel
    ) -> int:
        """Estimate hours needed to bridge gap"""
        if current_level is None:
            current_level = SkillLevel.BEGINNER

        key = (current_level.value, target_level.value)
        return self.LEARNING_HOURS.get(key, 100)  # Default 100 hours

    def _estimate_difficulty(
        self,
        current_level: Optional[SkillLevel],
        target_level: SkillLevel
    ) -> str:
        """Estimate learning difficulty"""
        if current_level is None:
            current_value = 0
        else:
            current_value = self.SKILL_LEVELS_ORDER[current_level]

        target_value = self.SKILL_LEVELS_ORDER[target_level]
        gap = target_value - current_value

        if gap >= 3:
            return "challenging"
        elif gap == 2:
            return "moderate"
        else:
            return "easy"

    def _generate_recommendation(
        self,
        overall_match: float,
        required_match: float,
        critical_gaps: int,
        high_gaps: int,
        learning_hours: int
    ) -> Tuple[str, str]:
        """Generate application recommendation"""
        if critical_gaps > 0:
            return "reconsider", f"Missing {critical_gaps} critical required skills. Consider building these skills first."

        if required_match >= 80 and overall_match >= 70:
            return "apply_now", "Strong match for this position. Apply now!"

        if required_match >= 60 and learning_hours <= 80:
            return "learn_first", f"Good potential match. Consider spending ~{learning_hours} hours learning key skills first."

        if required_match < 50:
            return "reconsider", "Significant skill gaps. This may not be the right role at this time."

        return "learn_first", "Moderate skill gaps. Learning key skills will significantly improve your chances."

    def _prioritize_learning(
        self,
        gaps: List[GapSkillDetail],
        required_skills: List[JobSkillRequirement]
    ) -> List[str]:
        """Prioritize skills to learn"""
        # Score each gap
        scored_gaps = []
        required_names = set(r.skill_name.lower() for r in required_skills)

        for gap in gaps:
            score = 0

            # Severity
            severity_scores = {
                GapSeverity.CRITICAL: 100,
                GapSeverity.HIGH: 75,
                GapSeverity.MEDIUM: 50,
                GapSeverity.LOW: 25
            }
            score += severity_scores[gap.gap_severity]

            # Required vs nice-to-have
            if gap.skill_name.lower() in required_names:
                score += 50

            # Dealbreaker
            if gap.is_dealbreaker:
                score += 100

            # Feasibility (prefer shorter learning times)
            if gap.learning_time_hours:
                if gap.learning_time_hours <= 40:
                    score += 20
                elif gap.learning_time_hours <= 80:
                    score += 10

            scored_gaps.append((gap.skill_name, score))

        # Sort by score
        scored_gaps.sort(key=lambda x: x[1], reverse=True)

        return [name for name, _ in scored_gaps]

    def _identify_strengths(
        self,
        matched_skills: List[MatchedSkillDetail],
        all_candidate_skills: List[CandidateSkill]
    ) -> List[str]:
        """Identify candidate's strength areas"""
        strengths = []

        # Skills where candidate exceeds requirements
        for match in matched_skills:
            if match.match_quality == "exceeds":
                strengths.append(f"Strong {match.skill_name} skills")

        # High proficiency skills
        expert_skills = [s for s in all_candidate_skills if s.proficiency_level == SkillLevel.EXPERT]
        if expert_skills:
            strengths.append(f"Expert in {', '.join(s.skill_name for s in expert_skills[:3])}")

        # Skills with certifications
        certified_skills = [s for s in all_candidate_skills if s.certifications]
        if certified_skills:
            strengths.append(f"Certified in {len(certified_skills)} skills")

        return strengths[:5]  # Top 5

    def _extract_skills_from_job(self, job: Job) -> List[JobSkillRequirement]:
        """
        Extract skills from job description using AI

        In production, this would use NLP/AI to extract skills.
        For now, returns empty list (manual entry required).
        """
        logger.warning(f"No skills extracted for job {job.id}. Manual entry recommended.")
        return []

    # ==================== Learning Resources ====================

    def _find_learning_resources(
        self,
        skill_name: str,
        current_level: Optional[SkillLevel],
        target_level: SkillLevel,
        limit: int = 5
    ) -> List[LearningResourceSchema]:
        """Find relevant learning resources"""
        query = self.db.query(LearningResource).filter(
            func.lower(LearningResource.skill_name) == skill_name.lower()
        )

        # Filter by target proficiency
        if current_level:
            # Want resources that bridge the gap
            query = query.filter(
                LearningResource.target_proficiency.in_([current_level, target_level])
            )
        else:
            # Starting from scratch
            query = query.filter(
                LearningResource.difficulty_level == "beginner"
            )

        # Order by relevance and rating
        resources = query.order_by(
            desc(LearningResource.relevance_score),
            desc(LearningResource.rating)
        ).limit(limit).all()

        return [LearningResourceSchema.from_orm(r) for r in resources]

    def get_resource_recommendations(
        self,
        skill_name: str,
        current_level: Optional[SkillLevel],
        target_level: SkillLevel,
        max_cost: Optional[float] = None,
        only_free: bool = False
    ) -> Dict[str, Any]:
        """Get personalized resource recommendations"""
        query = self.db.query(LearningResource).filter(
            func.lower(LearningResource.skill_name) == skill_name.lower()
        )

        if only_free:
            query = query.filter(LearningResource.is_free == True)
        elif max_cost:
            query = query.filter(
                (LearningResource.is_free == True) |
                (LearningResource.cost <= max_cost)
            )

        # Filter by difficulty
        if current_level is None:
            query = query.filter(LearningResource.difficulty_level == "beginner")
        elif current_level == SkillLevel.BEGINNER:
            query = query.filter(
                LearningResource.difficulty_level.in_(["beginner", "intermediate"])
            )

        resources = query.order_by(
            desc(LearningResource.rating),
            desc(LearningResource.relevance_score)
        ).all()

        # Calculate totals
        total_hours = sum(r.duration_hours or 0 for r in resources)
        total_cost = sum(r.cost or 0 for r in resources if not r.is_free)
        free_count = sum(1 for r in resources if r.is_free)

        # Create learning path (ordered progression)
        learning_path = [r.resource_title for r in sorted(
            resources,
            key=lambda x: (
                {"beginner": 1, "intermediate": 2, "advanced": 3}.get(x.difficulty_level or "beginner", 1)
            )
        )]

        return {
            "skill_name": skill_name,
            "recommended_resources": [LearningResourceSchema.from_orm(r) for r in resources],
            "total_estimated_hours": total_hours,
            "total_cost": total_cost,
            "free_options_count": free_count,
            "learning_path": learning_path
        }

    # ==================== Learning Plans ====================

    def create_learning_plan(
        self,
        job_id: Optional[int],
        plan_name: str,
        skills: List[Dict[str, Any]],
        hours_per_week: int = 10
    ) -> LearningPlan:
        """Create a learning plan"""
        logger.info(f"Creating learning plan: {plan_name}")

        # Calculate total hours
        total_hours = 0
        for skill in skills:
            if 'estimated_hours' in skill:
                total_hours += skill['estimated_hours']
            else:
                # Estimate based on levels
                current = skill.get('current_level')
                target = skill['target_level']
                total_hours += self._estimate_learning_time(current, target)

        # Calculate completion date
        weeks_needed = total_hours / hours_per_week if hours_per_week > 0 else 0
        target_completion = datetime.utcnow() + timedelta(weeks=weeks_needed)

        plan = LearningPlan(
            job_id=job_id,
            plan_name=plan_name,
            skills=skills,
            start_date=datetime.utcnow(),
            target_completion_date=target_completion,
            estimated_hours_total=total_hours,
            estimated_hours_per_week=hours_per_week,
            skills_not_started=len(skills),
            status="active"
        )

        self.db.add(plan)
        self.db.commit()

        return plan

    def update_skill_progress(
        self,
        skill_progress_id: int,
        hours_invested: Optional[float] = None,
        progress_percentage: Optional[float] = None,
        completed_resources: Optional[List[int]] = None
    ) -> SkillProgress:
        """Update progress on a skill"""
        progress = self.db.query(SkillProgress).filter(
            SkillProgress.id == skill_progress_id
        ).first()

        if not progress:
            raise ValueError(f"Skill progress {skill_progress_id} not found")

        if hours_invested is not None:
            progress.hours_invested += hours_invested
            progress.last_activity_date = datetime.utcnow()

        if progress_percentage is not None:
            progress.progress_percentage = progress_percentage

        if completed_resources:
            existing = progress.resources_completed or []
            progress.resources_completed = list(set(existing + completed_resources))

        # Update status
        if progress.progress_percentage >= 100:
            progress.status = "completed"
            progress.completed_at = datetime.utcnow()
        elif progress.progress_percentage > 0:
            progress.status = "in_progress"
            if not progress.started_at:
                progress.started_at = datetime.utcnow()

        self.db.commit()
        return progress
