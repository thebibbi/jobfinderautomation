"""
Skills Gap Analysis API

Endpoints for skill management, gap analysis, and learning recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from ..database import get_db
from ..schemas.skills import (
    CandidateSkillCreate, CandidateSkillUpdate, CandidateSkill,
    SkillGapAnalysisRequest, SkillGapAnalysisResult, SkillGapSummary,
    LearningResourceCreate, LearningResource,
    LearningPlanCreate, LearningPlan,
    SkillProgressCreate, SkillProgressUpdate, SkillProgress,
    SkillAssessmentCreate, SkillAssessment,
    SkillProfile, LearningDashboard,
    ResourceRecommendationRequest, ResourceRecommendations,
    SkillTrend
)
from ..services.skills_service import SkillsService
from ..models.skills import (
    CandidateSkill as CandidateSkillModel,
    LearningResource as LearningResourceModel,
    LearningPlan as LearningPlanModel,
    SkillProgress as SkillProgressModel,
    SkillAssessment as SkillAssessmentModel,
    SkillGapAnalysis,
    SkillTrend as SkillTrendModel,
    SkillLevel, SkillCategory
)


router = APIRouter()


# ==================== Candidate Skills ====================

@router.get("/candidate", response_model=List[CandidateSkill])
def get_candidate_skills(
    category: Optional[str] = None,
    level: Optional[str] = None,
    currently_learning: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get candidate's skills"""
    try:
        query = db.query(CandidateSkillModel).filter(
            CandidateSkillModel.is_active == True
        )

        if category:
            query = query.filter(CandidateSkillModel.skill_category == category)

        if level:
            query = query.filter(CandidateSkillModel.proficiency_level == level)

        if currently_learning is not None:
            query = query.filter(CandidateSkillModel.currently_learning == currently_learning)

        skills = query.order_by(CandidateSkillModel.proficiency_level.desc()).all()

        return skills

    except Exception as e:
        logger.error(f"Error fetching candidate skills: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidate", response_model=CandidateSkill)
def add_candidate_skill(
    skill: CandidateSkillCreate,
    db: Session = Depends(get_db)
):
    """Add a new skill to candidate profile"""
    try:
        # Check if skill already exists
        existing = db.query(CandidateSkillModel).filter(
            func.lower(CandidateSkillModel.skill_name) == skill.skill_name.lower(),
            CandidateSkillModel.is_active == True
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Skill '{skill.skill_name}' already exists"
            )

        new_skill = CandidateSkillModel(**skill.dict())
        db.add(new_skill)
        db.commit()
        db.refresh(new_skill)

        return new_skill

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding candidate skill: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/candidate/{skill_id}", response_model=CandidateSkill)
def update_candidate_skill(
    skill_id: int,
    skill_update: CandidateSkillUpdate,
    db: Session = Depends(get_db)
):
    """Update candidate skill"""
    try:
        skill = db.query(CandidateSkillModel).filter(
            CandidateSkillModel.id == skill_id
        ).first()

        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")

        # Update fields
        update_data = skill_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(skill, field, value)

        skill.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(skill)

        return skill

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate skill: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/candidate/{skill_id}")
def delete_candidate_skill(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """Delete (deactivate) candidate skill"""
    try:
        skill = db.query(CandidateSkillModel).filter(
            CandidateSkillModel.id == skill_id
        ).first()

        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")

        skill.is_active = False
        db.commit()

        return {"message": "Skill deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate skill: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidate/profile", response_model=SkillProfile)
def get_skill_profile(db: Session = Depends(get_db)):
    """Get complete skill profile"""
    try:
        skills = db.query(CandidateSkillModel).filter(
            CandidateSkillModel.is_active == True
        ).all()

        # Count by category
        skills_by_category = {}
        for skill in skills:
            cat = skill.skill_category.value if skill.skill_category else "other"
            skills_by_category[cat] = skills_by_category.get(cat, 0) + 1

        # Count by level
        skills_by_level = {}
        for skill in skills:
            level = skill.proficiency_level.value
            skills_by_level[level] = skills_by_level.get(level, 0) + 1

        # Top skills (expert level)
        top_skills = [s for s in skills if s.proficiency_level == SkillLevel.EXPERT][:5]

        # Currently learning
        learning = [s for s in skills if s.currently_learning]

        # All certifications
        all_certs = []
        for skill in skills:
            if skill.certifications:
                all_certs.extend(skill.certifications)

        # Average confidence
        confidences = [s.confidence_score for s in skills if s.confidence_score]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Profile completeness
        completeness = 0
        if skills:
            completeness += 40
        if any(s.years_experience for s in skills):
            completeness += 20
        if any(s.certifications for s in skills):
            completeness += 20
        if any(s.projects_used_in for s in skills):
            completeness += 20

        return SkillProfile(
            total_skills=len(skills),
            skills_by_category=skills_by_category,
            skills_by_level=skills_by_level,
            top_skills=top_skills,
            currently_learning=learning,
            certifications=list(set(all_certs)),
            avg_confidence=avg_confidence,
            profile_completeness=completeness
        )

    except Exception as e:
        logger.error(f"Error getting skill profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Skill Gap Analysis ====================

@router.post("/gap-analysis", response_model=SkillGapAnalysisResult)
def analyze_skill_gaps(
    request: SkillGapAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze skill gaps for a specific job"""
    try:
        service = SkillsService(db)

        result = service.analyze_skill_gaps(
            job_id=request.job_id,
            include_resources=request.include_resource_suggestions
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing skill gaps: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gap-analysis/{job_id}", response_model=SkillGapAnalysisResult)
def get_skill_gap_analysis(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get existing skill gap analysis"""
    try:
        analysis = db.query(SkillGapAnalysis).filter(
            SkillGapAnalysis.job_id == job_id
        ).order_by(SkillGapAnalysis.analysis_date.desc()).first()

        if not analysis:
            raise HTTPException(status_code=404, detail="No analysis found for this job")

        # Convert to response format
        from ..models.job import Job
        job = db.query(Job).filter(Job.id == job_id).first()

        return SkillGapAnalysisResult(
            job_id=job_id,
            job_title=job.title if job else "Unknown",
            company=job.company if job and job.company else "Unknown",
            total_skills_required=analysis.total_skills_required,
            skills_matched=analysis.skills_matched,
            skills_partial_match=analysis.skills_partial_match,
            skills_missing=analysis.skills_missing,
            overall_match_score=analysis.overall_match_score,
            required_skills_score=analysis.required_skills_score,
            nice_to_have_score=analysis.nice_to_have_score,
            critical_gaps=analysis.critical_gaps,
            high_priority_gaps=analysis.high_priority_gaps,
            medium_priority_gaps=analysis.medium_priority_gaps,
            low_priority_gaps=analysis.low_priority_gaps,
            matched_skills=analysis.matched_skills or [],
            partial_skills=analysis.partial_skills or [],
            missing_skills=analysis.missing_skills or [],
            recommendation=analysis.recommendation,
            recommendation_reason=analysis.recommendation_reason or "",
            learning_priority=analysis.learning_priority or [],
            total_learning_hours=analysis.total_learning_hours,
            estimated_ready_date=analysis.estimated_ready_date,
            strength_areas=analysis.strength_areas or [],
            improvement_areas=analysis.improvement_areas or [],
            analysis_date=analysis.analysis_date
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching skill gap analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gap-analysis/summary/all", response_model=List[SkillGapSummary])
def get_all_gap_summaries(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get summaries of all skill gap analyses"""
    try:
        analyses = db.query(SkillGapAnalysis).order_by(
            SkillGapAnalysis.analysis_date.desc()
        ).limit(limit).all()

        summaries = []
        for analysis in analyses:
            top_gaps = (analysis.learning_priority or [])[:3]

            summaries.append(SkillGapSummary(
                job_id=analysis.job_id,
                overall_match_score=analysis.overall_match_score,
                skills_matched=analysis.skills_matched,
                skills_missing=analysis.skills_missing,
                critical_gaps=analysis.critical_gaps,
                recommendation=analysis.recommendation,
                top_3_gaps=top_gaps
            ))

        return summaries

    except Exception as e:
        logger.error(f"Error fetching gap summaries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Learning Resources ====================

@router.get("/resources", response_model=List[LearningResource])
def get_learning_resources(
    skill_name: Optional[str] = None,
    is_free: Optional[bool] = None,
    difficulty: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get learning resources"""
    try:
        from sqlalchemy import func

        query = db.query(LearningResourceModel)

        if skill_name:
            query = query.filter(
                func.lower(LearningResourceModel.skill_name) == skill_name.lower()
            )

        if is_free is not None:
            query = query.filter(LearningResourceModel.is_free == is_free)

        if difficulty:
            query = query.filter(LearningResourceModel.difficulty_level == difficulty)

        resources = query.order_by(
            LearningResourceModel.rating.desc()
        ).limit(limit).all()

        return resources

    except Exception as e:
        logger.error(f"Error fetching learning resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resources", response_model=LearningResource)
def add_learning_resource(
    resource: LearningResourceCreate,
    db: Session = Depends(get_db)
):
    """Add a new learning resource"""
    try:
        new_resource = LearningResourceModel(**resource.dict())
        db.add(new_resource)
        db.commit()
        db.refresh(new_resource)

        return new_resource

    except Exception as e:
        logger.error(f"Error adding learning resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resources/recommendations", response_model=ResourceRecommendations)
def get_resource_recommendations(
    request: ResourceRecommendationRequest,
    db: Session = Depends(get_db)
):
    """Get personalized resource recommendations"""
    try:
        service = SkillsService(db)

        result = service.get_resource_recommendations(
            skill_name=request.skill_name,
            current_level=request.current_level,
            target_level=request.target_level,
            max_cost=request.max_cost,
            only_free=request.only_free
        )

        return ResourceRecommendations(**result)

    except Exception as e:
        logger.error(f"Error getting resource recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Learning Plans ====================

@router.get("/learning-plans", response_model=List[LearningPlan])
def get_learning_plans(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get learning plans"""
    try:
        query = db.query(LearningPlanModel).filter(
            LearningPlanModel.is_active == True
        )

        if status:
            query = query.filter(LearningPlanModel.status == status)

        plans = query.order_by(LearningPlanModel.created_at.desc()).all()

        return plans

    except Exception as e:
        logger.error(f"Error fetching learning plans: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning-plans", response_model=LearningPlan)
def create_learning_plan(
    plan: LearningPlanCreate,
    db: Session = Depends(get_db)
):
    """Create a new learning plan"""
    try:
        service = SkillsService(db)

        new_plan = service.create_learning_plan(
            job_id=plan.job_id,
            plan_name=plan.plan_name,
            skills=[skill.dict() for skill in plan.skills],
            hours_per_week=plan.estimated_hours_per_week or 10
        )

        return new_plan

    except Exception as e:
        logger.error(f"Error creating learning plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning-plans/{plan_id}", response_model=LearningPlan)
def get_learning_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """Get specific learning plan"""
    try:
        plan = db.query(LearningPlanModel).filter(
            LearningPlanModel.id == plan_id
        ).first()

        if not plan:
            raise HTTPException(status_code=404, detail="Learning plan not found")

        return plan

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching learning plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Skill Progress ====================

@router.post("/progress", response_model=SkillProgress)
def create_skill_progress(
    progress: SkillProgressCreate,
    db: Session = Depends(get_db)
):
    """Start tracking progress on a skill"""
    try:
        new_progress = SkillProgressModel(**progress.dict())
        db.add(new_progress)
        db.commit()
        db.refresh(new_progress)

        return new_progress

    except Exception as e:
        logger.error(f"Error creating skill progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/progress/{progress_id}", response_model=SkillProgress)
def update_progress(
    progress_id: int,
    update: SkillProgressUpdate,
    db: Session = Depends(get_db)
):
    """Update skill learning progress"""
    try:
        service = SkillsService(db)

        updated_progress = service.update_skill_progress(
            skill_progress_id=progress_id,
            hours_invested=update.hours_invested,
            progress_percentage=update.progress_percentage,
            completed_resources=update.resources_completed
        )

        return updated_progress

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating skill progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Skill Assessments ====================

@router.post("/assessments", response_model=SkillAssessment)
def create_skill_assessment(
    assessment: SkillAssessmentCreate,
    db: Session = Depends(get_db)
):
    """Create a skill assessment"""
    try:
        new_assessment = SkillAssessmentModel(**assessment.dict())
        db.add(new_assessment)
        db.commit()
        db.refresh(new_assessment)

        return new_assessment

    except Exception as e:
        logger.error(f"Error creating skill assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessments/{skill_name}", response_model=List[SkillAssessment])
def get_skill_assessments(
    skill_name: str,
    db: Session = Depends(get_db)
):
    """Get assessment history for a skill"""
    try:
        from sqlalchemy import func

        assessments = db.query(SkillAssessmentModel).filter(
            func.lower(SkillAssessmentModel.skill_name) == skill_name.lower()
        ).order_by(SkillAssessmentModel.assessment_date.desc()).all()

        return assessments

    except Exception as e:
        logger.error(f"Error fetching skill assessments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Skill Trends ====================

@router.get("/trends", response_model=List[SkillTrend])
def get_skill_trends(
    category: Optional[str] = None,
    hot_skills_only: bool = False,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get skill market trends"""
    try:
        query = db.query(SkillTrendModel)

        if category:
            query = query.filter(SkillTrendModel.skill_category == category)

        if hot_skills_only:
            query = query.filter(SkillTrendModel.hot_skill == True)

        trends = query.order_by(
            SkillTrendModel.demand_score.desc()
        ).limit(limit).all()

        return trends

    except Exception as e:
        logger.error(f"Error fetching skill trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Dashboard ====================

@router.get("/dashboard", response_model=LearningDashboard)
def get_learning_dashboard(db: Session = Depends(get_db)):
    """Get learning progress dashboard"""
    try:
        # Active plans
        active_plans = db.query(LearningPlanModel).filter(
            LearningPlanModel.status == "active",
            LearningPlanModel.is_active == True
        ).all()

        # Progress stats
        all_progress = db.query(SkillProgressModel).all()
        total_hours = sum(p.hours_invested for p in all_progress)
        in_progress = sum(1 for p in all_progress if p.status == "in_progress")
        completed = sum(1 for p in all_progress if p.status == "completed")

        # Current week hours
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_progress = [p for p in all_progress if p.last_activity_date and p.last_activity_date >= week_ago]
        current_week_hours = sum(p.hours_invested for p in week_progress)

        # Overall progress
        if active_plans:
            overall_progress = sum(p.current_progress for p in active_plans) / len(active_plans)
        else:
            overall_progress = 0

        # Recent achievements (completed skills in last 30 days)
        month_ago = datetime.utcnow() - timedelta(days=30)
        recent_completed = [p for p in all_progress if p.completed_at and p.completed_at >= month_ago]
        recent_achievements = [
            {
                "skill": p.skill_name,
                "completed_date": p.completed_at.isoformat(),
                "hours_invested": p.hours_invested
            }
            for p in recent_completed[:5]
        ]

        # Upcoming milestones
        upcoming_milestones = []
        for plan in active_plans:
            if plan.target_completion_date:
                upcoming_milestones.append({
                    "plan_name": plan.plan_name,
                    "target_date": plan.target_completion_date.isoformat(),
                    "progress": plan.current_progress
                })

        return LearningDashboard(
            active_plans=active_plans,
            total_hours_invested=total_hours,
            skills_in_progress=in_progress,
            skills_completed=completed,
            current_week_hours=current_week_hours,
            overall_progress=overall_progress,
            recent_achievements=recent_achievements,
            upcoming_milestones=upcoming_milestones
        )

    except Exception as e:
        logger.error(f"Error fetching learning dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
