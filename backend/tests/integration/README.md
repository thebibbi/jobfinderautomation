# Integration Tests

Comprehensive integration tests for the Job Automation System.

## Overview

These tests verify that all components work together correctly in a real environment:

- **Docker Stack Tests** (`test_docker_stack.py`): Verify all Docker services are healthy
- **End-to-End Workflow Tests** (`test_e2e_workflows.py`): Test complete user workflows
- **WebSocket Integration Tests** (`test_websocket_integration.py`): Test real-time updates
- **Cross-Feature Integration Tests** (`test_cross_feature_integration.py`): Test feature interactions

## Prerequisites

### Required:
- Docker and Docker Compose installed
- All services running: `docker-compose up -d`
- Database initialized: `docker-compose exec backend alembic upgrade head`

### Optional (for full coverage):
- Google OAuth credentials configured (for calendar tests)
- Redis running (for caching tests)
- Candidate skills added (for skills gap tests)

## Running Tests

### Run All Integration Tests

```bash
# From project root
docker-compose exec backend pytest tests/integration/ -v

# With coverage
docker-compose exec backend pytest tests/integration/ --cov=app --cov-report=html

# Run in parallel (faster)
docker-compose exec backend pytest tests/integration/ -n auto
```

### Run Specific Test Files

```bash
# Docker stack tests
docker-compose exec backend pytest tests/integration/test_docker_stack.py -v

# End-to-end workflows
docker-compose exec backend pytest tests/integration/test_e2e_workflows.py -v

# WebSocket integration
docker-compose exec backend pytest tests/integration/test_websocket_integration.py -v

# Cross-feature integration
docker-compose exec backend pytest tests/integration/test_cross_feature_integration.py -v
```

### Run Specific Test Classes

```bash
# Test Docker services
docker-compose exec backend pytest tests/integration/test_docker_stack.py::TestDockerStack -v

# Test job processing workflow
docker-compose exec backend pytest tests/integration/test_e2e_workflows.py::TestJobProcessingWorkflow -v

# Test WebSocket events
docker-compose exec backend pytest tests/integration/test_websocket_integration.py::TestWebSocketEvents -v
```

### Run Specific Tests

```bash
# Test backend health
docker-compose exec backend pytest tests/integration/test_docker_stack.py::TestDockerStack::test_backend_health -v

# Test job creation workflow
docker-compose exec backend pytest tests/integration/test_e2e_workflows.py::TestJobProcessingWorkflow::test_end_to_end_job_processing -v

# Test WebSocket connection
docker-compose exec backend pytest tests/integration/test_websocket_integration.py::TestWebSocketConnection::test_websocket_connection -v
```

## Test Markers

### Slow Tests

Some tests are marked as slow (e.g., container restart tests):

```bash
# Skip slow tests
docker-compose exec backend pytest tests/integration/ -m "not slow" -v

# Run only slow tests
docker-compose exec backend pytest tests/integration/ -m slow -v
```

### Async Tests

WebSocket tests use async/await:

```bash
# Run only async tests
docker-compose exec backend pytest tests/integration/test_websocket_integration.py -v
```

## Test Coverage

### Current Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_docker_stack.py` | 15 | Docker services, volumes, networking |
| `test_e2e_workflows.py` | 10 | Job processing, application lifecycle, recommendations |
| `test_websocket_integration.py` | 12 | WebSocket events, channels, reconnection |
| `test_cross_feature_integration.py` | 12 | ATS↔Calendar, Jobs↔Skills, Jobs↔Recommendations |

**Total**: 49 integration tests

### Coverage Areas

✅ **Docker Infrastructure**:
- Service health checks
- Database connectivity
- Redis connectivity
- WebSocket endpoint
- Service dependencies
- Volume persistence
- Network isolation
- Resource usage

✅ **Job Processing Workflow**:
- Job creation → analysis
- Company research
- Skills gap analysis
- Document generation (if score >= 70)
- Cache updates
- WebSocket notifications

✅ **Application Lifecycle**:
- Status transitions (saved → applied → interviewing → offer → accepted)
- Interview scheduling
- Offer management
- Notes tracking
- Timeline generation

✅ **Real-time Updates**:
- WebSocket connection/reconnection
- Event broadcasting
- Channel subscriptions
- Multi-client support
- Ping/pong keep-alive

✅ **Feature Integration**:
- ATS → Follow-ups (status changes trigger sequences)
- ATS → Calendar (interview scheduling)
- Jobs → Skills (automatic gap analysis)
- Jobs → Recommendations (learning from actions)
- Jobs → Company Research (automatic research)
- Cache → All features (invalidation)

## Expected Results

### All Tests Passing

```
tests/integration/test_docker_stack.py ..................... [100%]
tests/integration/test_e2e_workflows.py ................... [100%]
tests/integration/test_websocket_integration.py ........... [100%]
tests/integration/test_cross_feature_integration.py ....... [100%]

============== 49 passed in 45.23s ==============
```

### Partial Failures (Expected in Some Environments)

Some tests may skip or fail gracefully if optional services aren't configured:

**Google Calendar Tests**:
- May skip if OAuth credentials not configured
- Tests will gracefully handle missing calendar integration

**Company Research Tests**:
- May return empty results if research APIs not configured
- Tests verify graceful degradation

**Skills Gap Tests**:
- May skip if candidate skills not in database
- Tests handle missing skills gracefully

## Debugging Failed Tests

### View Test Output

```bash
# Verbose output
docker-compose exec backend pytest tests/integration/ -v -s

# Show local variables on failure
docker-compose exec backend pytest tests/integration/ -l

# Stop on first failure
docker-compose exec backend pytest tests/integration/ -x

# Run last failed tests
docker-compose exec backend pytest tests/integration/ --lf
```

### Check Service Logs

```bash
# Backend logs
docker-compose logs backend

# Database logs
docker-compose logs db

# Redis logs
docker-compose logs redis

# All services
docker-compose logs
```

### Inspect Service Health

```bash
# Check all services are healthy
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test database connection
docker-compose exec db psql -U postgres -d jobautomation -c "SELECT 1;"

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Common Issues

#### 1. Connection Timeout

**Error**: `requests.exceptions.ConnectionError: Connection refused`

**Solution**:
```bash
# Verify services are running
docker-compose ps

# Restart services
docker-compose restart backend

# Check backend is healthy
curl http://localhost:8000/health
```

#### 2. Database Not Ready

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check database is healthy
docker-compose ps db

# Wait for database to be ready
docker-compose exec db pg_isready -U postgres

# Restart backend after database is ready
docker-compose restart backend
```

#### 3. WebSocket Tests Fail

**Error**: `websockets.exceptions.InvalidStatusCode: server rejected WebSocket connection: HTTP 400`

**Solution**:
```bash
# Check WebSocket endpoint
curl http://localhost:8000/api/v1/connections

# Check CORS settings
# Ensure ALLOWED_ORIGINS includes http://localhost in .env

# Restart backend
docker-compose restart backend
```

#### 4. Tests Hang

**Issue**: Tests don't complete

**Solution**:
```bash
# Run with timeout
docker-compose exec backend pytest tests/integration/ --timeout=60

# Kill hung processes
docker-compose restart backend

# Clear test database
docker-compose exec db psql -U postgres -d jobautomation -c "TRUNCATE jobs CASCADE;"
```

## Test Data Cleanup

Tests automatically clean up their data, but you can manually clean:

```bash
# Clear test data from database
docker-compose exec backend python scripts/clear_test_data.py

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart with fresh database
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: |
          sleep 10
          docker-compose exec -T backend curl http://localhost:8000/health

      - name: Run integration tests
        run: docker-compose exec -T backend pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Performance Benchmarks

Expected test execution times (on standard hardware):

| Test Suite | Duration | Tests |
|------------|----------|-------|
| Docker Stack | ~10s | 15 |
| E2E Workflows | ~20s | 10 |
| WebSocket | ~15s | 12 |
| Cross-Feature | ~15s | 12 |
| **Total** | **~60s** | **49** |

## Contributing

### Adding New Integration Tests

1. Create test in appropriate file:
   - Infrastructure → `test_docker_stack.py`
   - User workflows → `test_e2e_workflows.py`
   - Real-time → `test_websocket_integration.py`
   - Feature interaction → `test_cross_feature_integration.py`

2. Follow naming conventions:
   - Test classes: `TestFeatureName`
   - Test methods: `test_specific_behavior`

3. Use fixtures for setup/teardown:
   ```python
   @pytest.fixture
   def test_data(api_base_url):
       # Setup
       data = create_test_data()
       yield data
       # Cleanup
       cleanup_test_data(data)
   ```

4. Add documentation:
   ```python
   def test_feature(self):
       """
       Test that feature works correctly.

       Steps:
       1. Setup test data
       2. Perform action
       3. Verify results
       4. Cleanup
       """
   ```

5. Run tests locally before committing:
   ```bash
   docker-compose exec backend pytest tests/integration/test_new_file.py -v
   ```

## Support

- **Documentation**: [../../docs/](../../docs/)
- **API Reference**: [../../docs/API_REFERENCE.md](../../docs/API_REFERENCE.md)
- **Docker Setup**: [../../DOCKER_SETUP.md](../../DOCKER_SETUP.md)
- **Issues**: GitHub Issues
