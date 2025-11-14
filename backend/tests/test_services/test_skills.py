"""
Tests for Skills Gap Analysis Service
"""
import pytest
from datetime import datetime, timedelta

from app.services.skills_service import SkillsService
from app.models.skills import (
    CandidateSkill, JobSkillRequirement, SkillGap, LearningResource,
    LearningPlan, SkillProgress, SkillLevel, SkillCategory, GapSeverity
)
from app.models.job import Job


class TestSkillGapAnalysis:
    """Test skill gap analysis functionality"""

    def test_analyze_gaps_perfect_match(self, db_session, create_test_job):
        """Should identify perfect skill matches"""
        # Create job with requirements
        job = create_test_job(title="Python Developer", company="TechCorp")

        req1 = JobSkillRequirement(
            job_id=job.id,
            skill_name="Python",
            skill_category=SkillCategory.PROGRAMMING_LANGUAGE,
            required_level=SkillLevel.INTERMEDIATE,
            is_required=True,
            importance_score=90
        )
        req2 = JobSkillRequirement(
            job_id=job.id,
            skill_name="Django",
            skill_category=SkillCategory.FRAMEWORK,
            required_level=SkillLevel.BEGINNER,
            is_required=True,
            importance_score=75
        )
        db_session.add_all([req1, req2])

        # Create candidate skills (perfect match)
        skill1 = CandidateSkill(
            skill_name="Python",
            skill_category=SkillCategory.PROGRAMMING_LANGUAGE,
            proficiency_level=SkillLevel.ADVANCED,
            years_experience=3.0,
            confidence_score=90
        )
        skill2 = CandidateSkill(
            skill_name="Django",
            skill_category=SkillCategory.FRAMEWORK,
            proficiency_level=SkillLevel.INTERMEDIATE,
            years_experience=2.0,
            confidence_score=85
        )
        db_session.add_all([skill1, skill2])
        db_session.commit()

        service = SkillsService(db_session)

        result = service.analyze_skill_gaps(job.id, include_resources=False)

        assert result.job_id == job.id
        assert result.total_skills_required == 2
        assert result.skills_matched == 2
        assert result.skills_missing == 0
        assert result.overall_match_score > 80
        assert result.recommendation == "apply_now"

    def test_analyze_gaps_with_missing_skills(self, db_session, create_test_job):
        """Should identify missing skills"""
        job = create_test_job(title="Full Stack Developer", company="WebCo")

        # Add requirements
        req1 = JobSkillRequirement(
            job_id=job.id,
            skill_name="Python",
            required_level=SkillLevel.INTERMEDIATE,
            is_required=True
        )
        req2 = JobSkillRequirement(
            job_id=job.id,
            skill_name="React",
            required_level=SkillLevel.INTERMEDIATE,
            is_required=True
        )
        req3 = JobSkillRequirement(
            job_id=job.id,
            skill_name="Docker",
            required_level=SkillLevel.BEGINNER,
            is_required=False
        )
        db_session.add_all([req1, req2, req3])

        # Only add Python skill
        skill1 = CandidateSkill(
            skill_name="Python",
            proficiency_level=SkillLevel.ADVANCED,
            years_experience=3.0
        )
        db_session.add(skill1)
        db_session.commit()

        service = SkillsService(db_session)

        result = service.analyze_skill_gaps(job.id, include_resources=False)

        assert result.skills_matched == 1
        assert result.skills_missing == 2
        assert result.critical_gaps >= 1  # Missing required React
        assert any("React" in gap.skill_name for gap in result.missing_skills)
        assert result.recommendation in ["learn_first", "reconsider"]

    def test_analyze_gaps_partial_match(self, db_session, create_test_job):
        """Should identify partial skill matches"""
        job = create_test_job(title="Senior Python Developer", company="TechCorp")

        req = JobSkillRequirement(
            job_id=job.id,
            skill_name="Python",
            required_level=SkillLevel.EXPERT,
            is_required=True
        )
        db_session.add(req)

        # Candidate has Python but not at expert level
        skill = CandidateSkill(
            skill_name="Python",
            proficiency_level=SkillLevel.INTERMEDIATE,
            years_experience=2.0
        )
        db_session.add(skill)
        db_session.commit()

        service = SkillsService(db_session)

        result = service.analyze_skill_gaps(job.id, include_resources=False)

        assert result.skills_matched == 0
        assert result.skills_partial_match == 1
        assert len(result.partial_skills) == 1
        assert result.partial_skills[0].skill_name == "Python"
        assert result.partial_skills[0].candidate_level == SkillLevel.INTERMEDIATE
        assert result.partial_skills[0].required_level == SkillLevel.EXPERT

    def test_learning_time_estimation(self, db_session):
        """Should estimate learning time correctly"""
        service = SkillsService(db_session)

        # Beginner to Intermediate
        hours1 = service._estimate_learning_time(
            SkillLevel.BEGINNER,
            SkillLevel.INTERMEDIATE
        )
        assert hours1 == 40

        # Beginner to Expert
        hours2 = service._estimate_learning_time(
            SkillLevel.BEGINNER,
            SkillLevel.EXPERT
        )
        assert hours2 == 300

        # None (not possessed) to Intermediate
        hours3 = service._estimate_learning_time(
            None,
            SkillLevel.INTERMEDIATE
        )
        assert hours3 > 0

    def test_gap_severity_calculation(self, db_session):
        """Should calculate gap severity correctly"""
        service = SkillsService(db_session)

        # Missing required advanced skill
        severity1 = service._calculate_gap_severity(
            None,
            SkillLevel.ADVANCED,
            is_required=True
        )
        assert severity1 == GapSeverity.CRITICAL

        # Has beginner, needs expert
        severity2 = service._calculate_gap_severity(
            SkillLevel.BEGINNER,
            SkillLevel.EXPERT,
            is_required=True
        )
        assert severity2 == GapSeverity.HIGH

        # Missing nice-to-have
        severity3 = service._calculate_gap_severity(
            None,
            SkillLevel.BEGINNER,
            is_required=False
        )
        assert severity3 == GapSeverity.MEDIUM


class TestLearningResources:
    """Test learning resource functionality"""

    def test_find_learning_resources(self, db_session):
        """Should find relevant learning resources"""
        # Create resources
        res1 = LearningResource(
            skill_name="Python",
            resource_type="course",
            resource_title="Python for Beginners",
            resource_url="https://example.com/python-basics",
            provider="Udemy",
            is_free=False,
            cost=49.99,
            duration_hours=20,
            difficulty_level="beginner",
            target_proficiency=SkillLevel.BEGINNER,
            rating=4.5,
            relevance_score=90
        )
        res2 = LearningResource(
            skill_name="Python",
            resource_type="course",
            resource_title="Advanced Python",
            resource_url="https://example.com/python-advanced",
            provider="Coursera",
            is_free=False,
            cost=79.99,
            duration_hours=40,
            difficulty_level="advanced",
            target_proficiency=SkillLevel.ADVANCED,
            rating=4.8,
            relevance_score=95
        )
        db_session.add_all([res1, res2])
        db_session.commit()

        service = SkillsService(db_session)

        resources = service._find_learning_resources(
            "Python",
            SkillLevel.BEGINNER,
            SkillLevel.INTERMEDIATE,
            limit=5
        )

        assert len(resources) > 0
        assert any(r.resource_title == "Python for Beginners" for r in resources)

    def test_resource_recommendations(self, db_session):
        """Should provide resource recommendations"""
        # Create resources
        res1 = LearningResource(
            skill_name="React",
            resource_type="course",
            resource_title="React Basics",
            is_free=True,
            duration_hours=10,
            difficulty_level="beginner",
            rating=4.3
        )
        res2 = LearningResource(
            skill_name="React",
            resource_type="course",
            resource_title="React Advanced",
            is_free=False,
            cost=59.99,
            duration_hours=30,
            difficulty_level="advanced",
            rating=4.7
        )
        db_session.add_all([res1, res2])
        db_session.commit()

        service = SkillsService(db_session)

        result = service.get_resource_recommendations(
            skill_name="React",
            current_level=None,
            target_level=SkillLevel.INTERMEDIATE,
            only_free=True
        )

        assert result["skill_name"] == "React"
        assert result["free_options_count"] > 0
        assert all(r.is_free for r in result["recommended_resources"])


class TestLearningPlans:
    """Test learning plan functionality"""

    def test_create_learning_plan(self, db_session, create_test_job):
        """Should create a learning plan"""
        job = create_test_job(title="Full Stack Developer", company="WebCo")

        service = SkillsService(db_session)

        skills = [
            {
                "skill_name": "React",
                "current_level": None,
                "target_level": SkillLevel.INTERMEDIATE,
                "priority": 1,
                "estimated_hours": 40
            },
            {
                "skill_name": "Node.js",
                "current_level": SkillLevel.BEGINNER,
                "target_level": SkillLevel.ADVANCED,
                "priority": 2,
                "estimated_hours": 80
            }
        ]

        plan = service.create_learning_plan(
            job_id=job.id,
            plan_name="Full Stack Learning Path",
            skills=skills,
            hours_per_week=10
        )

        assert plan.id is not None
        assert plan.plan_name == "Full Stack Learning Path"
        assert plan.job_id == job.id
        assert plan.estimated_hours_total == 120
        assert plan.skills_not_started == 2
        assert plan.status == "active"

    def test_learning_plan_timeline(self, db_session):
        """Should calculate completion timeline"""
        service = SkillsService(db_session)

        skills = [
            {
                "skill_name": "Python",
                "target_level": SkillLevel.INTERMEDIATE,
                "estimated_hours": 40
            }
        ]

        plan = service.create_learning_plan(
            job_id=None,
            plan_name="Python Learning",
            skills=skills,
            hours_per_week=10
        )

        # Should complete in 4 weeks
        weeks = (plan.target_completion_date - plan.start_date).days / 7
        assert 3.5 <= weeks <= 4.5


class TestSkillProgress:
    """Test skill progress tracking"""

    def test_update_skill_progress(self, db_session):
        """Should update skill progress"""
        # Create progress entry
        progress = SkillProgress(
            skill_name="Python",
            starting_level=SkillLevel.BEGINNER,
            target_level=SkillLevel.INTERMEDIATE,
            current_level=SkillLevel.BEGINNER,
            progress_percentage=0,
            hours_invested=0,
            status="not_started"
        )
        db_session.add(progress)
        db_session.commit()

        service = SkillsService(db_session)

        # Update progress
        updated = service.update_skill_progress(
            skill_progress_id=progress.id,
            hours_invested=10,
            progress_percentage=25
        )

        assert updated.hours_invested == 10
        assert updated.progress_percentage == 25
        assert updated.status == "in_progress"
        assert updated.started_at is not None

    def test_complete_skill_progress(self, db_session):
        """Should mark skill as completed"""
        progress = SkillProgress(
            skill_name="React",
            starting_level=None,
            target_level=SkillLevel.INTERMEDIATE,
            progress_percentage=90,
            hours_invested=35,
            status="in_progress"
        )
        db_session.add(progress)
        db_session.commit()

        service = SkillsService(db_session)

        # Complete the skill
        updated = service.update_skill_progress(
            skill_progress_id=progress.id,
            progress_percentage=100
        )

        assert updated.status == "completed"
        assert updated.completed_at is not None


class TestSkillComparison:
    """Test skill level comparison"""

    def test_compare_skill_levels(self, db_session):
        """Should compare skill levels correctly"""
        service = SkillsService(db_session)

        # Perfect match
        assert service._compare_skill_levels(
            SkillLevel.INTERMEDIATE,
            SkillLevel.INTERMEDIATE
        ) == "perfect"

        # Exceeds requirement
        assert service._compare_skill_levels(
            SkillLevel.EXPERT,
            SkillLevel.INTERMEDIATE
        ) == "exceeds"

        # Close to requirement
        assert service._compare_skill_levels(
            SkillLevel.INTERMEDIATE,
            SkillLevel.ADVANCED
        ) == "close"

        # Significant gap
        assert service._compare_skill_levels(
            SkillLevel.BEGINNER,
            SkillLevel.EXPERT
        ) == "gap"


class TestRecommendationGeneration:
    """Test recommendation generation"""

    def test_generate_apply_now_recommendation(self, db_session):
        """Should recommend applying now for strong matches"""
        service = SkillsService(db_session)

        recommendation, reason = service._generate_recommendation(
            overall_match=85,
            required_match=90,
            critical_gaps=0,
            high_gaps=0,
            learning_hours=0
        )

        assert recommendation == "apply_now"
        assert "Strong match" in reason

    def test_generate_learn_first_recommendation(self, db_session):
        """Should recommend learning first for moderate gaps"""
        service = SkillsService(db_session)

        recommendation, reason = service._generate_recommendation(
            overall_match=70,
            required_match=65,
            critical_gaps=0,
            high_gaps=1,
            learning_hours=60
        )

        assert recommendation == "learn_first"
        assert "60" in reason

    def test_generate_reconsider_recommendation(self, db_session):
        """Should recommend reconsidering for large gaps"""
        service = SkillsService(db_session)

        recommendation, reason = service._generate_recommendation(
            overall_match=40,
            required_match=35,
            critical_gaps=2,
            high_gaps=3,
            learning_hours=200
        )

        assert recommendation == "reconsider"


class TestLearningPrioritization:
    """Test learning prioritization"""

    def test_prioritize_learning_by_severity(self, db_session):
        """Should prioritize critical skills first"""
        from app.schemas.skills import GapSkillDetail

        req1 = JobSkillRequirement(
            job_id=1,
            skill_name="Python",
            required_level=SkillLevel.EXPERT,
            is_required=True
        )
        req2 = JobSkillRequirement(
            job_id=1,
            skill_name="Docker",
            required_level=SkillLevel.BEGINNER,
            is_required=False
        )

        gaps = [
            GapSkillDetail(
                skill_name="Docker",
                required_level=SkillLevel.BEGINNER,
                candidate_level=None,
                gap_severity=GapSeverity.LOW,
                is_required=False,
                is_dealbreaker=False,
                learning_time_hours=20,
                difficulty="easy",
                resources=[]
            ),
            GapSkillDetail(
                skill_name="Python",
                required_level=SkillLevel.EXPERT,
                candidate_level=SkillLevel.BEGINNER,
                gap_severity=GapSeverity.CRITICAL,
                is_required=True,
                is_dealbreaker=True,
                learning_time_hours=300,
                difficulty="challenging",
                resources=[]
            )
        ]

        service = SkillsService(db_session)

        priorities = service._prioritize_learning(gaps, [req1, req2])

        # Python should be first (critical)
        assert priorities[0] == "Python"
        assert priorities[1] == "Docker"
