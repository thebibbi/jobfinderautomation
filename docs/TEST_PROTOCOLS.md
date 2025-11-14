# Test Protocols for Job Automation System

This document outlines the testing protocols for the job automation system and all its enhancements.

## Table of Contents

1. [Test Infrastructure Setup](#test-infrastructure-setup)
2. [Running Tests](#running-tests)
3. [Test Categories](#test-categories)
4. [Feature Testing Protocols](#feature-testing-protocols)
5. [Continuous Integration](#continuous-integration)

---

## Test Infrastructure Setup

### Prerequisites

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Or install all dependencies
pip install -r requirements.txt
```

### Test Directory Structure

```
backend/tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_services/             # Service layer tests
│   ├── test_ai_service.py
│   ├── test_job_analyzer.py
│   ├── test_document_generator.py
│   └── test_semantic_matcher.py
├── test_api/                  # API endpoint tests
│   ├── test_jobs_api.py
│   ├── test_analysis_api.py
│   ├── test_documents_api.py
│   └── test_stats_api.py
└── test_integration/          # End-to-end tests
    └── test_full_workflow.py
```

### Fixtures Available

All tests have access to these fixtures (defined in `conftest.py`):

- **Database**: `db_session`, `test_db_engine`, `client`
- **Sample Data**: `sample_job_data`, `sample_job_data_low_match`, `sample_analysis_result`
- **Mock Services**: `mock_claude_response`, `mock_openrouter_response`, `mock_google_drive_service`, `mock_email_service`
- **Factory Fixtures**: `create_test_job`, `create_test_document`

---

## Running Tests

### Run All Tests

```bash
# From backend directory
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=html
```

### Run Specific Test Categories

```bash
# Service tests only
pytest tests/test_services/

# API tests only
pytest tests/test_api/

# Integration tests only
pytest tests/test_integration/

# Specific test file
pytest tests/test_services/test_ai_service.py

# Specific test class
pytest tests/test_services/test_ai_service.py::TestAIServiceProviderSelection

# Specific test function
pytest tests/test_services/test_ai_service.py::TestAIServiceProviderSelection::test_anthropic_provider_initialization
```

### Run Tests by Markers

```bash
# Run only fast tests (unit tests)
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run only async tests
pytest -m asyncio
```

### Continuous Testing During Development

```bash
# Watch mode - re-run tests on file changes
pytest-watch

# Or use pytest with --looponfail
pytest --looponfail tests/
```

---

## Test Categories

### 1. Unit Tests (Service Layer)

**Purpose**: Test individual components in isolation

**Location**: `tests/test_services/`

**Coverage**:
- AI service provider selection
- Job analysis logic
- Document generation
- Semantic matching
- Cost optimization strategies

**Example**:
```python
def test_anthropic_provider_initialization(self, mock_settings):
    """Test initialization with Anthropic provider"""
    mock_settings.AI_PROVIDER = "anthropic"
    service = AIService()
    assert service.provider == "anthropic"
```

### 2. API Tests

**Purpose**: Test HTTP endpoints and request/response handling

**Location**: `tests/test_api/`

**Coverage**:
- Request validation
- Response format
- Error handling
- Status codes
- Authentication (when implemented)

**Example**:
```python
def test_create_job_from_extension(self, client, sample_job_data):
    """Test POST /api/v1/jobs/process endpoint"""
    response = client.post("/api/v1/jobs/process", json=sample_job_data)
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### 3. Integration Tests

**Purpose**: Test complete workflows end-to-end

**Location**: `tests/test_integration/`

**Coverage**:
- Full job processing workflow
- Multi-service interactions
- Data persistence
- Background task execution

**Example**:
```python
@pytest.mark.asyncio
async def test_full_workflow_high_match(client, db_session, ...):
    """Test complete workflow from job submission to document generation"""
    # 1. Submit job
    # 2. Analyze job
    # 3. Generate documents
    # 4. Verify results
```

---

## Feature Testing Protocols

### Protocol Template

For each new feature, follow this testing protocol:

1. **Unit Tests** (Write first - TDD)
   - Test core logic in isolation
   - Mock external dependencies
   - Test edge cases and error conditions
   - Aim for 80%+ code coverage

2. **API Tests** (If feature has endpoints)
   - Test request validation
   - Test success responses
   - Test error responses
   - Test authentication/authorization

3. **Integration Tests**
   - Test feature with real dependencies
   - Test feature in complete workflow
   - Test performance under load

4. **Manual Testing**
   - Test via API with real data
   - Test via UI (when available)
   - Test error scenarios manually

5. **Documentation**
   - Update this TEST_PROTOCOLS.md
   - Add feature-specific test instructions
   - Document test data requirements

---

## Feature-Specific Test Protocols

### ✅ 1. Testing Infrastructure

**Status**: Complete

**What to Test**:
- ✅ All fixtures work correctly
- ✅ Database setup/teardown
- ✅ Mock services function properly
- ✅ Test isolation (no cross-contamination)

**How to Test**:
```bash
# Run all tests to verify infrastructure
pytest -v

# Check coverage
pytest --cov=app --cov-report=term-missing
```

**Success Criteria**:
- All tests pass
- No test isolation issues
- Coverage report generated successfully

---

### 2. Application Tracking System (ATS)

**Status**: Pending Implementation

**What to Test**:
- Job lifecycle state transitions
- Status validation (can't skip states)
- Event tracking and timestamps
- Interview scheduling
- Offer management

**Test Cases**:
```python
# Unit Tests
def test_job_status_transition_valid()
def test_job_status_transition_invalid()
def test_interview_scheduling()
def test_offer_acceptance()
def test_offer_rejection()
def test_application_withdrawal()

# API Tests
def test_update_job_status_api()
def test_get_jobs_by_status()
def test_schedule_interview_api()
def test_record_offer_api()

# Integration Tests
def test_full_application_lifecycle()
def test_interview_reminder_workflow()
def test_offer_negotiation_workflow()
```

**How to Test**:
```bash
# After implementation
pytest tests/test_services/test_ats.py -v
pytest tests/test_api/test_ats_api.py -v
pytest tests/test_integration/test_ats_workflow.py -v
```

**Success Criteria**:
- All state transitions work correctly
- Invalid transitions are prevented
- Events are tracked with timestamps
- Interview and offer data persists correctly

---

### 3. Success Analytics & Learning Loop

**Status**: Pending Implementation

**What to Test**:
- Outcome tracking (interview/offer/rejection)
- Pattern recognition
- Score adjustment based on outcomes
- Feedback loop effectiveness

**Test Cases**:
```python
# Unit Tests
def test_record_application_outcome()
def test_calculate_prediction_accuracy()
def test_adjust_scoring_weights()
def test_identify_successful_patterns()
def test_generate_insights()

# API Tests
def test_record_outcome_api()
def test_get_analytics_api()
def test_get_success_patterns_api()

# Integration Tests
def test_learning_loop_adjusts_scores()
def test_analytics_dashboard_data()
```

**How to Test**:
```bash
pytest tests/test_services/test_analytics.py -v
pytest tests/test_api/test_analytics_api.py -v

# Test with sample outcomes data
python scripts/test_analytics_with_data.py
```

**Success Criteria**:
- Outcomes recorded accurately
- Patterns identified correctly
- Score adjustments improve accuracy over time
- Analytics provide actionable insights

---

### 4. Automated Follow-up System

**Status**: Pending Implementation

**What to Test**:
- Follow-up scheduling
- Email template generation
- Timing optimization
- Multi-stage sequences
- Unsubscribe handling

**Test Cases**:
```python
# Unit Tests
def test_schedule_follow_up()
def test_generate_follow_up_email()
def test_calculate_optimal_timing()
def test_follow_up_sequence()
def test_handle_response()

# API Tests
def test_create_follow_up_api()
def test_get_pending_follow_ups_api()
def test_cancel_follow_up_api()

# Integration Tests
def test_full_follow_up_sequence()
def test_follow_up_after_interview()
```

**How to Test**:
```bash
pytest tests/test_services/test_follow_up.py -v
pytest tests/test_api/test_follow_up_api.py -v

# Test timing logic
python scripts/test_follow_up_timing.py
```

**Success Criteria**:
- Follow-ups scheduled correctly
- Emails generated with appropriate tone
- Timing follows best practices
- Sequences execute properly

---

### 5. Company Research Automation

**Status**: Pending Implementation

**What to Test**:
- Data collection from safe sources
- RapidAPI integration
- Data parsing and storage
- Research report generation
- Rate limiting compliance

**Test Cases**:
```python
# Unit Tests
def test_fetch_company_info_rapidapi()
def test_parse_company_data()
def test_generate_research_report()
def test_handle_api_rate_limits()

# API Tests
def test_research_company_api()
def test_get_research_results_api()

# Integration Tests
def test_research_during_job_analysis()
def test_incorporate_research_in_documents()
```

**How to Test**:
```bash
pytest tests/test_services/test_company_research.py -v

# Test with real API (use test credits)
RAPIDAPI_KEY=test_key pytest tests/test_integration/test_research_api.py -v
```

**Success Criteria**:
- Company data fetched accurately
- API rate limits respected
- Research integrated into analysis
- No scraping violations

---

### 6. Salary Negotiation Assistant

**Status**: Pending Implementation

**What to Test**:
- Salary data retrieval
- Market analysis
- Counter-offer generation
- Negotiation script creation

**Test Cases**:
```python
# Unit Tests
def test_fetch_salary_data()
def test_calculate_market_rate()
def test_generate_counter_offer()
def test_create_negotiation_script()

# API Tests
def test_get_salary_analysis_api()
def test_generate_negotiation_response_api()

# Integration Tests
def test_salary_negotiation_workflow()
```

**How to Test**:
```bash
pytest tests/test_services/test_salary_negotiation.py -v
pytest tests/test_api/test_salary_api.py -v
```

**Success Criteria**:
- Salary data accurate
- Market analysis comprehensive
- Counter-offers reasonable
- Scripts professional and effective

---

### 7. Interview Preparation Assistant

**Status**: Pending Implementation

**What to Test**:
- Question prediction
- STAR story generation
- Practice mode functionality
- Performance tracking

**Test Cases**:
```python
# Unit Tests
def test_predict_interview_questions()
def test_generate_star_stories()
def test_score_practice_response()
def test_suggest_improvements()

# API Tests
def test_get_interview_prep_api()
def test_practice_mode_api()
def test_get_feedback_api()

# Integration Tests
def test_full_interview_prep_workflow()
```

**How to Test**:
```bash
pytest tests/test_services/test_interview_prep.py -v
pytest tests/test_api/test_interview_prep_api.py -v

# Interactive testing
python scripts/interactive_interview_practice.py
```

**Success Criteria**:
- Questions relevant to job
- STAR stories compelling
- Practice feedback helpful
- Improvement suggestions actionable

---

### 8. Smart Job Recommendations

**Status**: Pending Implementation

**What to Test**:
- Recommendation algorithm
- Job similarity calculation
- Preference learning
- Daily digest generation

**Test Cases**:
```python
# Unit Tests
def test_calculate_job_similarity()
def test_rank_recommendations()
def test_learn_from_applications()
def test_filter_recommendations()

# API Tests
def test_get_recommendations_api()
def test_dismiss_recommendation_api()
def test_get_daily_digest_api()

# Integration Tests
def test_recommendation_improves_over_time()
```

**How to Test**:
```bash
pytest tests/test_services/test_recommendations.py -v
pytest tests/test_api/test_recommendations_api.py -v

# Test with historical data
python scripts/test_recommendation_accuracy.py
```

**Success Criteria**:
- Recommendations relevant
- Algorithm learns from feedback
- Daily digests timely and useful
- High acceptance rate

---

### 9. Skills Gap Analysis

**Status**: Pending Implementation

**What to Test**:
- Skill extraction from jobs
- Gap identification
- Learning path generation
- Progress tracking

**Test Cases**:
```python
# Unit Tests
def test_extract_required_skills()
def test_identify_skill_gaps()
def test_generate_learning_path()
def test_track_skill_progress()

# API Tests
def test_get_skill_gaps_api()
def test_get_learning_path_api()
def test_update_skill_progress_api()

# Integration Tests
def test_skills_analysis_workflow()
```

**How to Test**:
```bash
pytest tests/test_services/test_skills_analysis.py -v
pytest tests/test_api/test_skills_api.py -v
```

**Success Criteria**:
- Skills extracted accurately
- Gaps identified correctly
- Learning paths practical
- Progress tracked effectively

---

### 10. Advanced Caching with Redis

**Status**: Pending Implementation

**What to Test**:
- Cache hit/miss rates
- Cache invalidation
- TTL management
- Performance improvement

**Test Cases**:
```python
# Unit Tests
def test_cache_set()
def test_cache_get()
def test_cache_invalidation()
def test_cache_ttl()

# Integration Tests
def test_api_response_cached()
def test_cache_improves_performance()
def test_cache_invalidation_on_update()
```

**How to Test**:
```bash
pytest tests/test_services/test_cache.py -v

# Performance testing
python scripts/benchmark_cache_performance.py
```

**Success Criteria**:
- Cache hit rate > 80%
- Response time improvement > 50%
- Cache invalidation works correctly
- No stale data served

---

### 11. Real-time Updates (WebSockets)

**Status**: Pending Implementation

**What to Test**:
- WebSocket connection establishment
- Real-time event broadcasting
- Connection handling (reconnect)
- Message delivery

**Test Cases**:
```python
# Unit Tests
def test_websocket_connection()
def test_broadcast_event()
def test_handle_disconnection()
def test_reconnection_logic()

# Integration Tests
def test_job_analysis_updates_in_realtime()
def test_multiple_clients_receive_updates()
```

**How to Test**:
```bash
pytest tests/test_websockets.py -v

# Manual testing with test client
python scripts/test_websocket_client.py
```

**Success Criteria**:
- Connections stable
- Events delivered in real-time
- Reconnection automatic
- No message loss

---

### 12. Calendar Integration (Google Calendar)

**Status**: Pending Implementation

**What to Test**:
- Calendar authentication
- Event creation
- Event updates/cancellation
- Reminder configuration

**Test Cases**:
```python
# Unit Tests
def test_create_calendar_event()
def test_update_calendar_event()
def test_delete_calendar_event()
def test_set_event_reminders()

# API Tests
def test_schedule_interview_calendar_api()
def test_get_upcoming_events_api()

# Integration Tests
def test_interview_scheduled_to_calendar()
def test_calendar_event_updates_on_change()
```

**How to Test**:
```bash
pytest tests/test_services/test_calendar.py -v

# Test with real Google Calendar (use test account)
GOOGLE_CALENDAR_ID=test@gmail.com pytest tests/test_integration/test_calendar_api.py -v
```

**Success Criteria**:
- Events created successfully
- Reminders set appropriately
- Updates sync correctly
- No duplicate events

---

### 13. Web Dashboard (React/Next.js)

**Status**: Pending Implementation

**What to Test**:
- Component rendering
- API integration
- State management
- Routing
- User interactions

**Test Cases**:
```javascript
// Component Tests
test('JobList renders correctly')
test('JobCard displays job data')
test('AnalysisResults shows match score')
test('DocumentViewer loads documents')

// Integration Tests
test('Full job submission workflow')
test('Dashboard updates on job analysis')
test('Document generation triggers correctly')

// E2E Tests (Cypress/Playwright)
test('User can submit job from extension')
test('User can view analysis results')
test('User can download generated documents')
```

**How to Test**:
```bash
# Frontend unit tests
cd frontend
npm test

# E2E tests
npm run test:e2e

# Visual regression tests
npm run test:visual
```

**Success Criteria**:
- All components render correctly
- API calls successful
- UI responsive and performant
- E2E workflows complete successfully

---

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
          run: |
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Best Practices

1. **Write Tests First** (TDD)
   - Write failing test
   - Implement feature
   - Make test pass
   - Refactor

2. **Test Isolation**
   - Each test should be independent
   - Use fixtures for setup
   - Clean up after tests

3. **Mock External Services**
   - Don't hit real APIs in tests
   - Use mock responses
   - Test error scenarios

4. **Clear Test Names**
   - `test_feature_scenario_expected_result`
   - Example: `test_job_analysis_high_score_generates_documents`

5. **Comprehensive Coverage**
   - Happy path
   - Error cases
   - Edge cases
   - Performance edge cases

6. **Fast Tests**
   - Unit tests < 100ms each
   - Integration tests < 1s each
   - Use mocks to speed up

7. **Readable Assertions**
   - Use descriptive assertion messages
   - One logical assertion per test
   - Clear failure messages

---

## Troubleshooting Tests

### Common Issues

**Issue**: Tests fail with database errors
**Solution**: Ensure test database is properly initialized in conftest.py

**Issue**: Async tests not running
**Solution**: Add `@pytest.mark.asyncio` decorator and ensure pytest-asyncio is installed

**Issue**: Mock not working
**Solution**: Check patch path matches import path in code

**Issue**: Tests pass individually but fail together
**Solution**: Test isolation issue - check for shared state or missing cleanup

---

## Contributing

When adding new features:

1. Add test protocol to this document
2. Write tests following the protocol
3. Run all tests before committing
4. Update documentation

---

## Test Coverage Goals

- **Overall**: 80%+
- **Core Services**: 90%+
- **API Endpoints**: 85%+
- **Critical Paths**: 95%+

Check coverage:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```
