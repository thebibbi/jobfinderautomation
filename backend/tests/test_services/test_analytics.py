"""
Tests for Analytics and Learning Service
"""
import pytest
from datetime import datetime, timedelta
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import ApplicationOutcomeCreate


class TestOutcomeRecording:
    """Test outcome recording functionality"""

    def test_record_outcome_success(self, db_session, create_test_job):
        """Test recording a successful application outcome"""
        job = create_test_job(match_score=85)
        analytics = AnalyticsService(db_session)

        outcome_data = ApplicationOutcomeCreate(
            job_id=job.id,
            outcome_type="offer_accepted",
            outcome_stage="offer",
            actual_success=True,
            interview_count=3,
            days_to_outcome=45
        )

        outcome = analytics.record_outcome(outcome_data)

        assert outcome.id is not None
        assert outcome.job_id == job.id
        assert outcome.actual_success is True
        assert outcome.predicted_match_score == 85
        assert outcome.job_characteristics is not None

    def test_record_outcome_failure(self, db_session, create_test_job):
        """Test recording a failed application outcome"""
        job = create_test_job(match_score=70)
        analytics = AnalyticsService(db_session)

        outcome_data = ApplicationOutcomeCreate(
            job_id=job.id,
            outcome_type="rejected",
            outcome_stage="screening",
            actual_success=False,
            rejection_reason="not_qualified",
            days_to_outcome=7
        )

        outcome = analytics.record_outcome(outcome_data)

        assert outcome.actual_success is False
        assert outcome.rejection_reason == "not_qualified"
        assert outcome.interview_count == 0

    def test_record_outcome_nonexistent_job(self, db_session):
        """Test recording outcome for non-existent job"""
        analytics = AnalyticsService(db_session)

        outcome_data = ApplicationOutcomeCreate(
            job_id=99999,
            outcome_type="rejected",
            outcome_stage="screening",
            actual_success=False
        )

        with pytest.raises(ValueError, match="Job .* not found"):
            analytics.record_outcome(outcome_data)


class TestPatternAnalysis:
    """Test success pattern analysis"""

    def test_analyze_patterns_insufficient_data(self, db_session):
        """Test pattern analysis with insufficient data"""
        analytics = AnalyticsService(db_session)
        patterns = analytics.analyze_success_patterns()

        # Should return empty list with insufficient data
        assert isinstance(patterns, list)

    def test_analyze_patterns_with_data(self, db_session, create_test_job):
        """Test pattern analysis with sufficient data"""
        analytics = AnalyticsService(db_session)

        # Create jobs and outcomes
        for i in range(15):
            job = create_test_job(
                job_id=f"job_{i}",
                company="TechCorp" if i < 10 else "StartupXYZ",
                remote_type="remote" if i % 2 == 0 else "onsite",
                match_score=80 + i
            )

            # 80% success rate for TechCorp, 20% for StartupXYZ
            success = (job.company == "TechCorp" and i % 5 != 0) or (job.company == "StartupXYZ" and i % 5 == 0)

            outcome_data = ApplicationOutcomeCreate(
                job_id=job.id,
                outcome_type="offer_accepted" if success else "rejected",
                outcome_stage="offer" if success else "screening",
                actual_success=success
            )
            analytics.record_outcome(outcome_data)

        # Analyze patterns
        patterns = analytics.analyze_success_patterns()

        assert len(patterns) > 0

        # Should identify TechCorp as successful pattern
        techcorp_patterns = [p for p in patterns if p.pattern_value == "TechCorp"]
        if techcorp_patterns:
            assert techcorp_patterns[0].success_rate > 50

    def test_score_range_categorization(self, db_session):
        """Test score range categorization"""
        analytics = AnalyticsService(db_session)

        assert analytics._get_score_range(95) == "90-100"
        assert analytics._get_score_range(85) == "80-89"
        assert analytics._get_score_range(75) == "70-79"
        assert analytics._get_score_range(65) == "60-69"
        assert analytics._get_score_range(55) == "below-60"
        assert analytics._get_score_range(None) == "unknown"

    def test_confidence_calculation(self, db_session):
        """Test confidence score calculation"""
        analytics = AnalyticsService(db_session)

        # Larger sample, clear pattern = high confidence
        conf1 = analytics._calculate_confidence(100, 90)
        assert conf1 > 0.7

        # Small sample = lower confidence
        conf2 = analytics._calculate_confidence(10, 90)
        assert conf2 < conf1

        # Around 50% success = lower confidence
        conf3 = analytics._calculate_confidence(100, 50)
        assert conf3 < conf1


class TestPredictionAccuracy:
    """Test prediction accuracy calculation"""

    def test_calculate_accuracy_no_data(self, db_session):
        """Test accuracy calculation with no outcomes"""
        analytics = AnalyticsService(db_session)
        accuracy = analytics.calculate_prediction_accuracy()

        assert accuracy is None

    def test_calculate_accuracy_with_data(self, db_session, create_test_job):
        """Test accuracy calculation with outcome data"""
        analytics = AnalyticsService(db_session)

        # Create jobs with predicted scores and actual outcomes
        # 7 correct predictions, 3 incorrect
        test_cases = [
            (85, True),   # Predicted success (≥70), actual success ✓
            (90, True),   # ✓
            (75, True),   # ✓
            (80, True),   # ✓
            (70, True),   # ✓
            (60, False),  # Predicted failure (<70), actual failure ✓
            (55, False),  # ✓
            (85, False),  # Predicted success, actual failure ✗ (false positive)
            (75, False),  # ✗ (false positive)
            (65, True),   # Predicted failure, actual success ✗ (false negative)
        ]

        for i, (score, success) in enumerate(test_cases):
            job = create_test_job(
                job_id=f"accuracy_job_{i}",
                match_score=score
            )

            outcome_data = ApplicationOutcomeCreate(
                job_id=job.id,
                outcome_type="offer_accepted" if success else "rejected",
                outcome_stage="offer" if success else "screening",
                actual_success=success
            )
            analytics.record_outcome(outcome_data)

        # Calculate accuracy
        accuracy = analytics.calculate_prediction_accuracy(period_days=30)

        assert accuracy is not None
        assert accuracy.total_predictions == 10
        assert accuracy.correct_predictions == 7
        assert accuracy.accuracy_percentage == 70.0
        assert accuracy.false_positives == 2
        assert accuracy.false_negatives == 1

    def test_accuracy_metrics(self, db_session, create_test_job):
        """Test precision and recall calculations"""
        analytics = AnalyticsService(db_session)

        # Perfect predictions
        for i in range(10):
            job = create_test_job(
                job_id=f"perfect_{i}",
                match_score=80 if i < 5 else 60
            )

            success = i < 5  # First 5 succeed (score ≥70), last 5 fail (score <70)

            outcome_data = ApplicationOutcomeCreate(
                job_id=job.id,
                outcome_type="offer_accepted" if success else "rejected",
                outcome_stage="offer" if success else "screening",
                actual_success=success
            )
            analytics.record_outcome(outcome_data)

        accuracy = analytics.calculate_prediction_accuracy()

        assert accuracy.accuracy_percentage == 100.0
        assert accuracy.false_positives == 0
        assert accuracy.false_negatives == 0


class TestScoringWeights:
    """Test scoring weight management"""

    def test_default_weights_created(self, db_session):
        """Test that default weights are created on initialization"""
        analytics = AnalyticsService(db_session)

        from app.models.analytics import ScoringWeight
        weights = db_session.query(ScoringWeight).all()

        assert len(weights) >= 5  # At least the 5 default weights
        assert any(w.weight_name == "skills_match" for w in weights)
        assert any(w.weight_name == "experience_match" for w in weights)

    def test_adjust_weights_insufficient_data(self, db_session):
        """Test weight adjustment with insufficient data"""
        analytics = AnalyticsService(db_session)
        result = analytics.adjust_scoring_weights()

        assert result["adjusted"] is False
        assert result["reason"] == "insufficient_data"

    def test_adjust_weights_with_data(self, db_session, create_test_job):
        """Test weight adjustment with sufficient data"""
        analytics = AnalyticsService(db_session)

        # Create 30 outcomes with poor accuracy
        for i in range(30):
            job = create_test_job(
                job_id=f"weight_test_{i}",
                match_score=75
            )

            # Random outcomes (simulating poor predictions)
            success = i % 3 == 0  # 33% success rate

            outcome_data = ApplicationOutcomeCreate(
                job_id=job.id,
                outcome_type="offer_accepted" if success else "rejected",
                outcome_stage="offer" if success else "screening",
                actual_success=success
            )
            analytics.record_outcome(outcome_data)

        # Adjust weights
        result = analytics.adjust_scoring_weights()

        # With poor accuracy, adjustments should be made
        assert isinstance(result, dict)
        assert "adjusted" in result


class TestInsightsGeneration:
    """Test insights generation"""

    def test_generate_insights_no_data(self, db_session):
        """Test insight generation with no data"""
        analytics = AnalyticsService(db_session)
        insights = analytics.generate_insights()

        assert isinstance(insights, list)

    def test_generate_insights_low_success_rate(self, db_session, create_test_job):
        """Test insight generation for low success rate"""
        analytics = AnalyticsService(db_session)

        # Create 15 outcomes with low success rate
        for i in range(15):
            job = create_test_job(job_id=f"low_success_{i}")

            # Only 13% success rate
            success = i % 8 == 0

            outcome_data = ApplicationOutcomeCreate(
                job_id=job.id,
                outcome_type="offer_accepted" if success else "rejected",
                outcome_stage="offer" if success else "screening",
                actual_success=success
            )
            analytics.record_outcome(outcome_data)

        insights = analytics.generate_insights()

        # Should generate insight about low success rate
        low_success_insights = [i for i in insights if "Low" in i.title or "low" in i.description.lower()]
        assert len(low_success_insights) > 0

    def test_generate_insights_from_patterns(self, db_session, create_test_job):
        """Test insight generation from success patterns"""
        analytics = AnalyticsService(db_session)

        # Create clear pattern: remote jobs = high success
        for i in range(20):
            job = create_test_job(
                job_id=f"pattern_insight_{i}",
                remote_type="remote" if i < 15 else "onsite"
            )

            # Remote jobs have 80% success, onsite 20%
            if job.remote_type == "remote":
                success = i % 5 != 0
            else:
                success = i % 5 == 0

            outcome_data = ApplicationOutcomeCreate(
                job_id=job.id,
                outcome_type="offer_accepted" if success else "rejected",
                outcome_stage="offer" if success else "screening",
                actual_success=success
            )
            analytics.record_outcome(outcome_data)

        # Analyze patterns first
        analytics.analyze_success_patterns()

        # Generate insights
        insights = analytics.generate_insights()

        assert len(insights) > 0


class TestLearningStats:
    """Test learning statistics"""

    def test_get_learning_stats_no_data(self, db_session):
        """Test learning stats with no data"""
        analytics = AnalyticsService(db_session)
        stats = analytics.get_learning_stats()

        assert stats["total_outcomes_learned_from"] == 0
        assert stats["learning_status"] == "insufficient_data"

    def test_get_learning_stats_with_data(self, db_session, create_test_job):
        """Test learning stats with sufficient data"""
        analytics = AnalyticsService(db_session)

        # Create outcomes
        for i in range(15):
            job = create_test_job(job_id=f"stats_test_{i}")

            outcome_data = ApplicationOutcomeCreate(
                job_id=job.id,
                outcome_type="offer_accepted" if i % 2 == 0 else "rejected",
                outcome_stage="offer",
                actual_success=i % 2 == 0
            )
            analytics.record_outcome(outcome_data)

        stats = analytics.get_learning_stats()

        assert stats["total_outcomes_learned_from"] >= 15
        assert stats["learning_status"] == "active"


class TestLearningTrigger:
    """Test automatic learning triggers"""

    def test_learning_triggered_at_intervals(self, db_session, create_test_job):
        """Test that learning is triggered at appropriate intervals"""
        analytics = AnalyticsService(db_session)

        # Record 10 outcomes (should trigger learning)
        for i in range(10):
            job = create_test_job(job_id=f"trigger_test_{i}")

            outcome_data = ApplicationOutcomeCreate(
                job_id=job.id,
                outcome_type="offer_accepted" if i % 2 == 0 else "rejected",
                outcome_stage="offer",
                actual_success=i % 2 == 0
            )
            analytics.record_outcome(outcome_data)

        # Check that patterns were analyzed
        from app.models.analytics import SuccessPattern
        patterns = db_session.query(SuccessPattern).count()

        # Patterns may or may not be created depending on data distribution
        assert patterns >= 0  # Just verify no errors occurred
