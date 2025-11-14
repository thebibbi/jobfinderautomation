"""
Analytics and Learning API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..services.analytics_service import get_analytics_service
from ..models.analytics import (
    ApplicationOutcome as OutcomeModel,
    PredictionAccuracy as AccuracyModel,
    SuccessPattern as PatternModel,
    ScoringWeight as WeightModel,
    AnalyticsInsight as InsightModel,
    LearningEvent as EventModel
)
from ..schemas.analytics import (
    ApplicationOutcomeCreate,
    ApplicationOutcome,
    PredictionAccuracy,
    SuccessPattern,
    ScoringWeight,
    ScoringWeightUpdate,
    AnalyticsInsight,
    LearningEvent,
    LearningStats,
    AnalyticsDashboard
)


router = APIRouter()


# ==================== Outcome Recording ====================

@router.post("/outcomes", response_model=ApplicationOutcome, status_code=status.HTTP_201_CREATED)
async def record_outcome(
    outcome: ApplicationOutcomeCreate,
    db: Session = Depends(get_db)
):
    """
    Record an application outcome for learning

    This helps the system learn from successes and failures.
    """
    try:
        analytics_service = get_analytics_service(db)
        created_outcome = analytics_service.record_outcome(outcome)
        return created_outcome
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording outcome: {str(e)}"
        )


@router.get("/outcomes", response_model=List[ApplicationOutcome])
async def get_outcomes(
    limit: int = Query(100, le=1000),
    outcome_type: Optional[str] = None,
    actual_success: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get application outcomes

    Optionally filter by outcome type or success status.
    """
    try:
        query = db.query(OutcomeModel)

        if outcome_type:
            query = query.filter(OutcomeModel.outcome_type == outcome_type)

        if actual_success is not None:
            query = query.filter(OutcomeModel.actual_success == actual_success)

        outcomes = query.order_by(OutcomeModel.outcome_date.desc()).limit(limit).all()
        return outcomes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving outcomes: {str(e)}"
        )


# ==================== Pattern Analysis ====================

@router.post("/patterns/analyze", response_model=List[SuccessPattern])
async def analyze_patterns(db: Session = Depends(get_db)):
    """
    Trigger pattern analysis

    Analyzes success/failure patterns across all recorded outcomes.
    """
    try:
        analytics_service = get_analytics_service(db)
        patterns = analytics_service.analyze_success_patterns()
        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing patterns: {str(e)}"
        )


@router.get("/patterns", response_model=List[SuccessPattern])
async def get_patterns(
    min_success_rate: Optional[float] = None,
    pattern_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get identified success patterns

    Optionally filter by minimum success rate or pattern type.
    """
    try:
        query = db.query(PatternModel).filter(
            PatternModel.sample_size_sufficient == True
        )

        if min_success_rate:
            query = query.filter(PatternModel.success_rate >= min_success_rate)

        if pattern_type:
            query = query.filter(PatternModel.pattern_type == pattern_type)

        patterns = query.order_by(PatternModel.success_rate.desc()).all()
        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving patterns: {str(e)}"
        )


@router.get("/patterns/top-success", response_model=List[SuccessPattern])
async def get_top_success_patterns(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """
    Get top success patterns

    Returns patterns with highest success rates.
    """
    try:
        patterns = db.query(PatternModel).filter(
            PatternModel.sample_size_sufficient == True,
            PatternModel.success_rate >= 70
        ).order_by(PatternModel.success_rate.desc()).limit(limit).all()

        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving top patterns: {str(e)}"
        )


@router.get("/patterns/improvement-areas", response_model=List[SuccessPattern])
async def get_improvement_areas(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """
    Get areas for improvement

    Returns patterns with low success rates.
    """
    try:
        patterns = db.query(PatternModel).filter(
            PatternModel.sample_size_sufficient == True,
            PatternModel.success_rate <= 30
        ).order_by(PatternModel.success_rate.asc()).limit(limit).all()

        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving improvement areas: {str(e)}"
        )


# ==================== Prediction Accuracy ====================

@router.post("/accuracy/calculate", response_model=PredictionAccuracy)
async def calculate_accuracy(
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Calculate prediction accuracy for a time period

    Returns accuracy metrics including precision, recall, and correlation.
    """
    try:
        analytics_service = get_analytics_service(db)
        accuracy = analytics_service.calculate_prediction_accuracy(period_days)

        if not accuracy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No outcomes found for the specified period"
            )

        return accuracy
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating accuracy: {str(e)}"
        )


@router.get("/accuracy/history", response_model=List[PredictionAccuracy])
async def get_accuracy_history(
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db)
):
    """
    Get prediction accuracy history

    Returns historical accuracy metrics over time.
    """
    try:
        accuracy_records = db.query(AccuracyModel).order_by(
            AccuracyModel.period_start.desc()
        ).limit(limit).all()

        return accuracy_records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving accuracy history: {str(e)}"
        )


# ==================== Scoring Weights ====================

@router.get("/weights", response_model=List[ScoringWeight])
async def get_scoring_weights(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get current scoring weights

    Returns all weights used in the matching algorithm.
    """
    try:
        query = db.query(WeightModel)

        if active_only:
            query = query.filter(WeightModel.is_active == True)

        weights = query.order_by(WeightModel.current_weight.desc()).all()
        return weights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving weights: {str(e)}"
        )


@router.put("/weights/{weight_name}", response_model=ScoringWeight)
async def update_scoring_weight(
    weight_name: str,
    weight_update: ScoringWeightUpdate,
    db: Session = Depends(get_db)
):
    """
    Manually update a scoring weight

    Allows manual adjustment of algorithm weights.
    """
    try:
        weight = db.query(WeightModel).filter(
            WeightModel.weight_name == weight_name
        ).first()

        if not weight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Weight '{weight_name}' not found"
            )

        old_weight = weight.current_weight
        weight.current_weight = weight_update.new_weight
        weight.adjustment_count += 1
        weight.last_adjusted = datetime.utcnow()

        # Update history
        if weight.adjustment_history is None:
            weight.adjustment_history = []
        weight.adjustment_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "old_weight": old_weight,
            "new_weight": weight_update.new_weight,
            "reason": weight_update.reason,
            "manual": True
        })

        # Log learning event
        from ..models.analytics import LearningEvent
        event = LearningEvent(
            event_type="weight_adjustment",
            description=f"Manually adjusted {weight_name} from {old_weight:.2f} to {weight_update.new_weight:.2f}",
            changes={"weight": weight_name, "old": old_weight, "new": weight_update.new_weight},
            reason=weight_update.reason
        )
        db.add(event)

        db.commit()
        db.refresh(weight)

        return weight
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating weight: {str(e)}"
        )


@router.post("/weights/adjust", response_model=dict)
async def adjust_weights_automatically(db: Session = Depends(get_db)):
    """
    Trigger automatic weight adjustment

    The system will analyze outcomes and adjust weights accordingly.
    """
    try:
        analytics_service = get_analytics_service(db)
        result = analytics_service.adjust_scoring_weights()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adjusting weights: {str(e)}"
        )


# ==================== Insights ====================

@router.post("/insights/generate", response_model=List[AnalyticsInsight])
async def generate_insights(db: Session = Depends(get_db)):
    """
    Generate new insights from analytics data

    Analyzes patterns and outcomes to create actionable insights.
    """
    try:
        analytics_service = get_analytics_service(db)
        insights = analytics_service.generate_insights()
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating insights: {str(e)}"
        )


@router.get("/insights", response_model=List[AnalyticsInsight])
async def get_insights(
    active_only: bool = True,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get analytics insights

    Returns actionable insights generated from data analysis.
    """
    try:
        query = db.query(InsightModel)

        if active_only:
            query = query.filter(InsightModel.is_active == True)

        if priority:
            query = query.filter(InsightModel.priority == priority)

        insights = query.order_by(
            InsightModel.generated_at.desc()
        ).all()

        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving insights: {str(e)}"
        )


@router.put("/insights/{insight_id}/acknowledge")
async def acknowledge_insight(
    insight_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark an insight as acknowledged

    Indicates that you've reviewed and acted on the insight.
    """
    try:
        insight = db.query(InsightModel).filter(InsightModel.id == insight_id).first()

        if not insight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insight {insight_id} not found"
            )

        from datetime import datetime
        insight.acknowledged = True
        insight.acknowledged_at = datetime.utcnow()
        db.commit()

        return {"success": True, "message": "Insight acknowledged"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error acknowledging insight: {str(e)}"
        )


# ==================== Learning Events ====================

@router.get("/learning/events", response_model=List[LearningEvent])
async def get_learning_events(
    limit: int = Query(50, le=500),
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get learning system events

    Returns history of learning algorithm adjustments.
    """
    try:
        query = db.query(EventModel)

        if event_type:
            query = query.filter(EventModel.event_type == event_type)

        events = query.order_by(EventModel.created_at.desc()).limit(limit).all()
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving learning events: {str(e)}"
        )


# ==================== Statistics ====================

@router.get("/stats", response_model=LearningStats)
async def get_learning_stats(db: Session = Depends(get_db)):
    """
    Get learning system statistics

    Returns overall learning system health and progress metrics.
    """
    try:
        analytics_service = get_analytics_service(db)
        stats = analytics_service.get_learning_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving learning stats: {str(e)}"
        )


# ==================== Dashboard ====================

@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(db: Session = Depends(get_db)):
    """
    Get complete analytics dashboard

    Returns comprehensive analytics data for dashboard display.
    """
    try:
        from ..models.job import Job

        analytics_service = get_analytics_service(db)

        # Get overall metrics
        total_applications = db.query(Job).count()
        total_outcomes = db.query(OutcomeModel).count()

        # Success rates
        outcomes = db.query(OutcomeModel).all()
        overall_success = sum(1 for o in outcomes if o.actual_success) / len(outcomes) * 100 if outcomes else None

        interview_outcomes = [o for o in outcomes if o.outcome_stage == "interview"]
        interview_success = sum(1 for o in interview_outcomes if o.actual_success) / len(interview_outcomes) * 100 if interview_outcomes else None

        offer_outcomes = [o for o in outcomes if o.outcome_stage == "offer"]
        offer_success = sum(1 for o in offer_outcomes if o.actual_success) / len(offer_outcomes) * 100 if offer_outcomes else None

        # Get current accuracy
        current_accuracy = db.query(AccuracyModel).order_by(
            AccuracyModel.created_at.desc()
        ).first()

        # Accuracy trend
        accuracy_history = db.query(AccuracyModel).order_by(
            AccuracyModel.period_start.asc()
        ).limit(10).all()
        accuracy_trend = [a.accuracy_percentage for a in accuracy_history if a.accuracy_percentage]

        # Top patterns
        top_success = db.query(PatternModel).filter(
            PatternModel.sample_size_sufficient == True,
            PatternModel.success_rate >= 70
        ).order_by(PatternModel.success_rate.desc()).limit(5).all()

        top_failure = db.query(PatternModel).filter(
            PatternModel.sample_size_sufficient == True,
            PatternModel.success_rate <= 30
        ).order_by(PatternModel.success_rate.asc()).limit(5).all()

        # Active insights
        active_insights = db.query(InsightModel).filter(
            InsightModel.is_active == True
        ).order_by(InsightModel.generated_at.desc()).limit(10).all()

        # Current weights
        current_weights = db.query(WeightModel).filter(
            WeightModel.is_active == True
        ).all()

        # Recent learning events
        recent_events = db.query(EventModel).order_by(
            EventModel.created_at.desc()
        ).limit(10).all()

        # Learning stats
        learning_stats = analytics_service.get_learning_stats()

        dashboard = AnalyticsDashboard(
            total_applications=total_applications,
            total_outcomes_recorded=total_outcomes,
            overall_success_rate=overall_success,
            interview_success_rate=interview_success,
            offer_success_rate=offer_success,
            current_accuracy=current_accuracy,
            accuracy_trend=accuracy_trend,
            top_success_patterns=top_success,
            top_failure_patterns=top_failure,
            active_insights=active_insights,
            current_weights=current_weights,
            recent_learning_events=recent_events,
            learning_enabled=learning_stats["learning_status"] == "active"
        )

        return dashboard
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard: {str(e)}"
        )
