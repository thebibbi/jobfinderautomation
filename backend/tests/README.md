# Testing Guide - Quick Start

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Verify pytest is installed
pytest --version
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_services/test_ai_service.py

# Run specific test class
pytest tests/test_services/test_ai_service.py::TestAIServiceProviderSelection

# Run specific test function
pytest tests/test_services/test_ai_service.py::TestAIServiceProviderSelection::test_anthropic_provider_initialization
```

### Coverage

```bash
# Run with coverage report
pytest --cov=app

# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Test Categories

```bash
# Service layer tests
pytest tests/test_services/

# API tests
pytest tests/test_api/

# Integration tests
pytest tests/test_integration/
```

### Filtering Tests

```bash
# Run only fast tests (skip integration)
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run only unit tests
pytest -m unit
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── test_services/                 # Service layer tests
│   ├── test_ai_service.py        # AI service tests
│   └── test_job_analyzer.py      # Job analyzer tests
├── test_api/                      # API endpoint tests
│   ├── test_jobs_api.py          # Jobs endpoints
│   └── test_stats_api.py         # Stats endpoints
└── test_integration/              # Integration tests
    └── test_full_workflow.py     # End-to-end workflows
```

## Writing Tests

### Example Unit Test

```python
def test_analyze_job_success(db_session, create_test_job, sample_analysis_result):
    """Test successful job analysis"""
    job = create_test_job(company="TestCorp", job_title="Data Analyst")

    with patch('app.services.job_analyzer.get_ai_service') as mock_ai:
        mock_ai.return_value.analyze_job_fit.return_value = sample_analysis_result

        analyzer = JobAnalyzer()
        result = await analyzer.analyze_job(job.id)

        assert result["match_score"] == 85
        assert result["should_apply"] is True
```

### Example API Test

```python
def test_create_job_from_extension(client, sample_job_data):
    """Test POST /api/v1/jobs/process endpoint"""
    response = client.post("/api/v1/jobs/process", json=sample_job_data)

    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Example Integration Test

```python
@pytest.mark.asyncio
async def test_full_workflow(client, db_session, sample_job_data):
    """Test complete job processing workflow"""
    # 1. Submit job
    response = client.post("/api/v1/jobs/process", json=sample_job_data)
    job_id = response.json()["jobId"]

    # 2. Analyze job
    # 3. Generate documents
    # 4. Verify results
```

## Available Fixtures

See `conftest.py` for all available fixtures:

- **Database**: `db_session`, `client`, `test_db_engine`
- **Sample Data**: `sample_job_data`, `sample_analysis_result`
- **Mocks**: `mock_claude_response`, `mock_openrouter_response`
- **Factories**: `create_test_job`, `create_test_document`

## Continuous Testing

### Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
ptw
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Debugging Tests

```bash
# Run with Python debugger
pytest --pdb

# Stop on first failure
pytest -x

# Show local variables on failure
pytest --showlocals

# Increase verbosity
pytest -vv
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **One Assertion**: Focus on one logical assertion per test
4. **Fast Tests**: Keep unit tests under 100ms
5. **Mock External Services**: Don't hit real APIs in tests

## Troubleshooting

**Tests fail with database errors**
- Ensure test database is initialized in conftest.py

**Async tests not running**
- Add `@pytest.mark.asyncio` decorator
- Check pytest-asyncio is installed

**Mock not working**
- Verify patch path matches import path

**Tests pass individually but fail together**
- Check for shared state or missing cleanup

## Documentation

For comprehensive testing protocols, see:
📖 [docs/TEST_PROTOCOLS.md](../../docs/TEST_PROTOCOLS.md)
