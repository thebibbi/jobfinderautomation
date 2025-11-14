"""
Analytics and Learning Service

Tracks outcomes, identifies patterns, and adjusts scoring algorithm.
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from loguru import logger
import statistics

from ..models.job import Job
from ..models.analytics import (
    ApplicationOutcome,
    PredictionAccuracy,
    SuccessPattern,
    ScoringWeight,
    AnalyticsInsight,
    LearningEvent
)
from ..models.application import ApplicationStatus
from ..schemas.analytics import (
    ApplicationOutcomeCreate,
    ScoringWeightUpdate,
    AnalyticsInsightCreate
)


class AnalyticsService:
    """Analytics and Learning Service"""

    # Minimum sample size for pattern significance
    MIN_SAMPLE_SIZE = 10

    # Confidence thresholds
    HIGH_CONFIDENCE = 0.8
    MEDIUM_CONFIDENCE = 0.6

    def __init__(self, db: Session):
        self.db = db
        self._ensure_default_weights()

    def _ensure_default_weights(self):
        """Ensure default scoring weights exist"""
        default_weights = [
            {
                "weight_name": "skills_match",
                "weight_category": "technical",
                "current_weight": 0.30,
                "initial_weight": 0.30,
                "description": "Weight for skills matching"
            },
            {
                "weight_name": "experience_match",
                "weight_category": "experience",
                "current_weight": 0.25,
                "initial_weight": 0.25,
                "description": "Weight for experience level matching"
            },
            {
                "weight_name": "culture_fit",
                "weight_category": "cultural",
                "current_weight": 0.20,
                "initial_weight": 0.20,
                "description": "Weight for cultural fit indicators"
            },
            {
                "weight_name": "growth_potential",
                "weight_category": "career",
                "current_weight": 0.15,
                "initial_weight": 0.15,
                "description": "Weight for career growth potential"
            },
            {
                "weight_name": "compensation",
                "weight_category": "practical",
                "current_weight": 0.10,
                "initial_weight": 0.10,
                "description": "Weight for compensation alignment"
            }
        ]

        for weight_data in default_weights:
            existing = self.db.query(ScoringWeight).filter(
                ScoringWeight.weight_name == weight_data["weight_name"]
            ).first()

            if not existing:
                weight = ScoringWeight(**weight_data)
                self.db.add(weight)

        self.db.commit()

    # ==================== Outcome Recording ====================

    def record_outcome(
        self,
        outcome_data: ApplicationOutcomeCreate
    ) -> ApplicationOutcome:
        """
        Record an application outcome for learning

        Args:
            outcome_data: Outcome details

        Returns:
            Created outcome record
        """
        job = self.db.query(Job).filter(Job.id == outcome_data.job_id).first()
        if not job:
            raise ValueError(f"Job {outcome_data.job_id} not found")

        # Capture job characteristics for pattern analysis
        job_characteristics = {
            "company": job.company,
            "job_title": job.job_title,
            "location": job.location,
            "remote_type": job.remote_type,
            "job_type": job.job_type,
            "source": job.source,
            "initial_match_score": job.match_score
        }

        # Create outcome record
        outcome = ApplicationOutcome(
            job_id=outcome_data.job_id,
            outcome_type=outcome_data.outcome_type,
            outcome_stage=outcome_data.outcome_stage,
            actual_success=outcome_data.actual_success,
            rejection_reason=outcome_data.rejection_reason,
            interview_count=outcome_data.interview_count,
            days_to_outcome=outcome_data.days_to_outcome,
            feedback_notes=outcome_data.feedback_notes,
            predicted_match_score=job.match_score,
            predicted_should_apply=job.match_score >= 70 if job.match_score else None,
            job_characteristics=job_characteristics
        )

        self.db.add(outcome)
        self.db.commit()
        self.db.refresh(outcome)

        logger.info(f"📊 Outcome recorded for job {outcome_data.job_id}: {outcome_data.outcome_type}")

        # Trigger learning if enough data
        self._trigger_learning_if_ready()

        return outcome

    # ==================== Pattern Analysis ====================

    def analyze_success_patterns(self) -> List[SuccessPattern]:
        """
        Analyze patterns in successful vs unsuccessful applications

        Returns:
            List of identified patterns
        """
        outcomes = self.db.query(ApplicationOutcome).all()

        if len(outcomes) < self.MIN_SAMPLE_SIZE:
            logger.warning(f"Insufficient data for pattern analysis: {len(outcomes)} outcomes")
            return []

        patterns = []

        # Analyze by various dimensions
        pattern_dimensions = [
            ("company", lambda o: o.job_characteristics.get("company")),
            ("location", lambda o: o.job_characteristics.get("location")),
            ("remote_type", lambda o: o.job_characteristics.get("remote_type")),
            ("job_type", lambda o: o.job_characteristics.get("job_type")),
            ("source", lambda o: o.job_characteristics.get("source")),
            ("score_range", lambda o: self._get_score_range(o.predicted_match_score))
        ]

        for pattern_type, extractor in pattern_dimensions:
            pattern_stats = {}

            for outcome in outcomes:
                value = extractor(outcome)
                if value:
                    if value not in pattern_stats:
                        pattern_stats[value] = {"total": 0, "success": 0}

                    pattern_stats[value]["total"] += 1
                    if outcome.actual_success:
                        pattern_stats[value]["success"] += 1

            # Create pattern records for significant patterns
            for value, stats in pattern_stats.items():
                if stats["total"] >= self.MIN_SAMPLE_SIZE:
                    success_rate = (stats["success"] / stats["total"]) * 100
                    confidence = self._calculate_confidence(stats["total"], success_rate)

                    # Update or create pattern
                    pattern = self.db.query(SuccessPattern).filter(
                        SuccessPattern.pattern_type == pattern_type,
                        SuccessPattern.pattern_value == str(value)
                    ).first()

                    if pattern:
                        pattern.applications_count = stats["total"]
                        pattern.success_count = stats["success"]
                        pattern.success_rate = success_rate
                        pattern.confidence_score = confidence
                        pattern.sample_size_sufficient = True
                        pattern.last_updated = datetime.utcnow()
                    else:
                        pattern = SuccessPattern(
                            pattern_type=pattern_type,
                            pattern_value=str(value),
                            applications_count=stats["total"],
                            success_count=stats["success"],
                            success_rate=success_rate,
                            confidence_score=confidence,
                            sample_size_sufficient=True,
                            insight_description=self._generate_pattern_insight(
                                pattern_type, value, success_rate
                            ),
                            recommendation=self._generate_pattern_recommendation(
                                pattern_type, value, success_rate
                            )
                        )
                        self.db.add(pattern)

                    patterns.append(pattern)

        self.db.commit()
        logger.info(f"🔍 Identified {len(patterns)} success patterns")

        return patterns

    def _get_score_range(self, score: Optional[float]) -> str:
        """Categorize score into range"""
        if score is None:
            return "unknown"
        elif score >= 90:
            return "90-100"
        elif score >= 80:
            return "80-89"
        elif score >= 70:
            return "70-79"
        elif score >= 60:
            return "60-69"
        else:
            return "below-60"

    def _calculate_confidence(self, sample_size: int, success_rate: float) -> float:
        """Calculate confidence score based on sample size and success rate"""
        # Simple confidence calculation
        size_factor = min(sample_size / (self.MIN_SAMPLE_SIZE * 5), 1.0)
        rate_factor = abs(success_rate - 50) / 50  # Distance from 50% (random)

        confidence = (size_factor * 0.6) + (rate_factor * 0.4)
        return round(confidence, 2)

    def _generate_pattern_insight(
        self,
        pattern_type: str,
        pattern_value: str,
        success_rate: float
    ) -> str:
        """Generate human-readable insight from pattern"""
        if success_rate >= 70:
            return f"High success rate ({success_rate:.1f}%) for {pattern_type}: {pattern_value}"
        elif success_rate <= 30:
            return f"Low success rate ({success_rate:.1f}%) for {pattern_type}: {pattern_value}"
        else:
            return f"Average success rate ({success_rate:.1f}%) for {pattern_type}: {pattern_value}"

    def _generate_pattern_recommendation(
        self,
        pattern_type: str,
        pattern_value: str,
        success_rate: float
    ) -> str:
        """Generate actionable recommendation from pattern"""
        if success_rate >= 70:
            return f"Prioritize applications with {pattern_type}: {pattern_value}"
        elif success_rate <= 30:
            return f"Consider avoiding or carefully evaluating {pattern_type}: {pattern_value}"
        else:
            return f"No strong recommendation for {pattern_type}: {pattern_value}"

    # ==================== Prediction Accuracy ====================

    def calculate_prediction_accuracy(
        self,
        period_days: int = 30
    ) -> PredictionAccuracy:
        """
        Calculate prediction accuracy for a time period

        Args:
            period_days: Number of days to analyze

        Returns:
            Prediction accuracy metrics
        """
        period_start = datetime.utcnow() - timedelta(days=period_days)
        period_end = datetime.utcnow()

        outcomes = self.db.query(ApplicationOutcome).filter(
            ApplicationOutcome.outcome_date >= period_start,
            ApplicationOutcome.outcome_date <= period_end,
            ApplicationOutcome.predicted_match_score.isnot(None)
        ).all()

        if not outcomes:
            logger.warning("No outcomes found for accuracy calculation")
            return None

        # Calculate metrics
        total = len(outcomes)
        correct = 0
        false_positives = 0
        false_negatives = 0

        success_scores = []
        failure_scores = []

        for outcome in outcomes:
            predicted_success = outcome.predicted_match_score >= 70
            actual_success = outcome.actual_success

            if predicted_success == actual_success:
                correct += 1

            if predicted_success and not actual_success:
                false_positives += 1

            if not predicted_success and actual_success:
                false_negatives += 1

            if actual_success:
                success_scores.append(outcome.predicted_match_score)
            else:
                failure_scores.append(outcome.predicted_match_score)

        # Calculate percentages
        accuracy_pct = (correct / total) * 100 if total > 0 else None

        true_positives = correct - (total - false_positives - false_negatives)
        precision = (true_positives / (true_positives + false_positives)) * 100 if (true_positives + false_positives) > 0 else None
        recall = (true_positives / (true_positives + false_negatives)) * 100 if (true_positives + false_negatives) > 0 else None

        # Calculate averages
        avg_success_score = statistics.mean(success_scores) if success_scores else None
        avg_failure_score = statistics.mean(failure_scores) if failure_scores else None

        # Simple correlation (positive if success scores > failure scores)
        score_correlation = None
        if avg_success_score and avg_failure_score:
            score_correlation = (avg_success_score - avg_failure_score) / 100

        # Create or update accuracy record
        accuracy = PredictionAccuracy(
            period_start=period_start,
            period_end=period_end,
            total_predictions=total,
            correct_predictions=correct,
            false_positives=false_positives,
            false_negatives=false_negatives,
            accuracy_percentage=accuracy_pct,
            precision=precision,
            recall=recall,
            avg_predicted_score_success=avg_success_score,
            avg_predicted_score_failure=avg_failure_score,
            score_correlation=score_correlation
        )

        self.db.add(accuracy)
        self.db.commit()
        self.db.refresh(accuracy)

        logger.info(f"📈 Prediction accuracy: {accuracy_pct:.1f}% (n={total})")

        return accuracy

    # ==================== Weight Adjustment ====================

    def adjust_scoring_weights(self) -> Dict[str, Any]:
        """
        Adjust scoring weights based on outcome data

        Returns:
            Summary of adjustments made
        """
        outcomes = self.db.query(ApplicationOutcome).all()

        if len(outcomes) < self.MIN_SAMPLE_SIZE * 2:
            logger.warning("Insufficient data for weight adjustment")
            return {"adjusted": False, "reason": "insufficient_data"}

        weights = self.db.query(ScoringWeight).filter(
            ScoringWeight.is_active == True
        ).all()

        adjustments_made = []

        for weight in weights:
            # Analyze correlation between this weight and success
            # (Simplified - in production, you'd extract actual feature correlations)

            # For now, adjust based on overall accuracy
            accuracy = self.calculate_prediction_accuracy(period_days=90)

            if accuracy and accuracy.accuracy_percentage:
                if accuracy.accuracy_percentage < 60:
                    # Poor accuracy - make small adjustments
                    adjustment = 0.02 if weight.current_weight < 0.5 else -0.02
                    new_weight = max(weight.min_weight, min(weight.max_weight, weight.current_weight + adjustment))

                    if new_weight != weight.current_weight:
                        old_weight = weight.current_weight
                        weight.current_weight = new_weight
                        weight.adjustment_count += 1
                        weight.last_adjusted = datetime.utcnow()

                        # Update history
                        if weight.adjustment_history is None:
                            weight.adjustment_history = []
                        weight.adjustment_history.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "old_weight": old_weight,
                            "new_weight": new_weight,
                            "reason": f"Accuracy below 60%: {accuracy.accuracy_percentage:.1f}%"
                        })

                        adjustments_made.append({
                            "weight_name": weight.weight_name,
                            "old_value": old_weight,
                            "new_value": new_weight
                        })

                        # Log learning event
                        event = LearningEvent(
                            event_type="weight_adjustment",
                            description=f"Adjusted {weight.weight_name} from {old_weight:.2f} to {new_weight:.2f}",
                            changes={"weight": weight.weight_name, "old": old_weight, "new": new_weight},
                            reason=f"Low prediction accuracy: {accuracy.accuracy_percentage:.1f}%"
                        )
                        self.db.add(event)

        self.db.commit()

        if adjustments_made:
            logger.info(f"⚙️ Adjusted {len(adjustments_made)} scoring weights")

        return {
            "adjusted": len(adjustments_made) > 0,
            "adjustments": adjustments_made,
            "reason": "accuracy_based_optimization"
        }

    # ==================== Insights Generation ====================

    def generate_insights(self) -> List[AnalyticsInsight]:
        """
        Generate actionable insights from analytics data

        Returns:
            List of generated insights
        """
        insights = []

        # 1. Success rate insights
        outcomes = self.db.query(ApplicationOutcome).all()
        if len(outcomes) >= self.MIN_SAMPLE_SIZE:
            success_count = sum(1 for o in outcomes if o.actual_success)
            success_rate = (success_count / len(outcomes)) * 100

            if success_rate < 20:
                insight = AnalyticsInsightCreate(
                    insight_type="success_pattern",
                    title="Low Overall Success Rate",
                    description=f"Your application success rate is {success_rate:.1f}%. Consider being more selective or adjusting your approach.",
                    priority="high",
                    confidence_level=self._calculate_confidence(len(outcomes), success_rate),
                    actionable=True,
                    recommended_action="Review rejection patterns and focus on higher-match opportunities",
                    supporting_data={"success_rate": success_rate, "total_applications": len(outcomes)}
                )
                insights.append(self._create_insight(insight))

        # 2. Pattern-based insights
        patterns = self.db.query(SuccessPattern).filter(
            SuccessPattern.sample_size_sufficient == True,
            SuccessPattern.success_rate >= 70
        ).order_by(SuccessPattern.success_rate.desc()).limit(3).all()

        for pattern in patterns:
            insight = AnalyticsInsightCreate(
                insight_type="success_pattern",
                title=f"High Success with {pattern.pattern_type}: {pattern.pattern_value}",
                description=pattern.insight_description,
                priority="medium",
                confidence_level=pattern.confidence_score,
                actionable=True,
                recommended_action=pattern.recommendation,
                supporting_data={
                    "success_rate": pattern.success_rate,
                    "sample_size": pattern.applications_count
                }
            )
            insights.append(self._create_insight(insight))

        # 3. Prediction accuracy insights
        accuracy = self.calculate_prediction_accuracy(period_days=30)
        if accuracy and accuracy.accuracy_percentage:
            if accuracy.accuracy_percentage < 60:
                insight = AnalyticsInsightCreate(
                    insight_type="improvement_area",
                    title="Prediction Accuracy Needs Improvement",
                    description=f"Current prediction accuracy is {accuracy.accuracy_percentage:.1f}%. The system is still learning.",
                    priority="medium",
                    confidence_level=0.9,
                    actionable=False,
                    supporting_data={"accuracy": accuracy.accuracy_percentage}
                )
                insights.append(self._create_insight(insight))

        self.db.commit()
        logger.info(f"💡 Generated {len(insights)} new insights")

        return insights

    def _create_insight(self, insight_data: AnalyticsInsightCreate) -> AnalyticsInsight:
        """Create insight record"""
        insight = AnalyticsInsight(**insight_data.model_dump())
        self.db.add(insight)
        return insight

    # ==================== Learning Trigger ====================

    def _trigger_learning_if_ready(self):
        """Trigger learning process if enough new data is available"""
        outcomes_count = self.db.query(ApplicationOutcome).count()

        # Run learning every 10 outcomes
        if outcomes_count % 10 == 0 and outcomes_count >= self.MIN_SAMPLE_SIZE:
            logger.info("🧠 Triggering learning process...")
            self.analyze_success_patterns()
            self.calculate_prediction_accuracy()
            self.adjust_scoring_weights()
            self.generate_insights()

    # ==================== Statistics ====================

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        outcomes_count = self.db.query(ApplicationOutcome).count()
        adjustments_count = self.db.query(LearningEvent).filter(
            LearningEvent.event_type == "weight_adjustment"
        ).count()

        accuracy = self.db.query(PredictionAccuracy).order_by(
            PredictionAccuracy.created_at.desc()
        ).first()

        patterns_count = self.db.query(SuccessPattern).filter(
            SuccessPattern.sample_size_sufficient == True
        ).count()

        insights_count = self.db.query(AnalyticsInsight).filter(
            AnalyticsInsight.is_active == True
        ).count()

        last_event = self.db.query(LearningEvent).order_by(
            LearningEvent.created_at.desc()
        ).first()

        return {
            "total_outcomes_learned_from": outcomes_count,
            "total_adjustments_made": adjustments_count,
            "current_accuracy": accuracy.accuracy_percentage if accuracy else None,
            "accuracy_improvement": None,  # TODO: Calculate from history
            "patterns_discovered": patterns_count,
            "insights_generated": insights_count,
            "last_learning_run": last_event.created_at if last_event else None,
            "learning_status": "active" if outcomes_count >= self.MIN_SAMPLE_SIZE else "insufficient_data"
        }


def get_analytics_service(db: Session) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(db)
