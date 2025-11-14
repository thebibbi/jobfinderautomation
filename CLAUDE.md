# CLAUDE.md - AI Assistant Guide

> **Last Updated**: 2025-11-14
> **Version**: 1.0.0
> **Purpose**: Comprehensive guide for AI assistants working with this codebase

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Technology Stack](#architecture--technology-stack)
3. [Directory Structure](#directory-structure)
4. [Development Workflows](#development-workflows)
5. [Coding Conventions](#coding-conventions)
6. [API Design Patterns](#api-design-patterns)
7. [Database & ORM Patterns](#database--orm-patterns)
8. [Testing Guidelines](#testing-guidelines)
9. [Configuration Management](#configuration-management)
10. [Key Integration Points](#key-integration-points)
11. [Common Tasks](#common-tasks)
12. [Best Practices for AI Assistants](#best-practices-for-ai-assistants)

---

## Project Overview

### What This Is
This is a **sophisticated end-to-end job automation platform** that combines web scraping, AI-powered analysis, document generation, and application tracking to streamline the entire job search process from discovery to offer negotiation.

### Core Functionality
- **Job Discovery**: Multi-platform scraping (LinkedIn, Indeed, Glassdoor)
- **Semantic Matching**: Pre-filters jobs using sentence transformers (40%+ similarity threshold)
- **Deep Analysis**: Claude AI analyzes job fit with 0-100 match scoring
- **Document Generation**: Tailored resumes (DOCX) and cover letters
- **Application Tracking**: Full lifecycle ATS from discovery to offer
- **Skills Gap Analysis**: Identifies and tracks skill development needs
- **Smart Recommendations**: ML-based job suggestions with feedback loop
- **Follow-up Automation**: Scheduled reminders and email templates

### Key Metrics
- **Total Files**: 84+ Python files, 14,302+ lines of code
- **Test Coverage**: Comprehensive test suite with pytest
- **API Endpoints**: 12 REST API routers with 50+ endpoints
- **Database Models**: 20+ SQLAlchemy models
- **Services**: 17 business logic services

---

## Architecture & Technology Stack

### Backend Stack
```
FastAPI 0.104.1       → REST API framework
Uvicorn 0.24.0        → ASGI server
SQLAlchemy 2.0.23     → ORM (SQLite default, PostgreSQL supported)
Celery 5.3.4          → Async task queue
Redis 5.0.1           → Caching & task broker
Pydantic 2.5.0        → Data validation & schemas
```

### AI/ML Stack
```
Anthropic Claude      → Primary AI (claude-sonnet-4-20250514)
OpenRouter            → Multi-model access (100+ models)
Sentence Transformers → Semantic similarity matching
PyTorch 2.1.1         → ML operations
```

### Integrations
```
Google Drive API      → Document organization
Gmail API             → Email notifications
Google Sheets API     → Data export
Selenium/Playwright   → Web scraping
BeautifulSoup4        → HTML parsing
```

### Document Processing
```
python-docx           → Resume generation (DOCX)
PyPDF2                → PDF processing
ReportLab             → PDF generation
Jinja2                → Template rendering
```

### Development Tools
```
pytest                → Testing framework
black                 → Code formatting
flake8                → Linting
mypy                  → Type checking
loguru                → Structured logging
Docker                → Containerization
```

---

## Directory Structure

```
/home/user/jobfinderautomation/
│
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point [CRITICAL]
│   │   ├── config.py                # Configuration management [CRITICAL]
│   │   ├── database.py              # SQLAlchemy setup [CRITICAL]
│   │   │
│   │   ├── api/                     # REST API endpoints (12 routers)
│   │   │   ├── jobs.py              # Job CRUD operations
│   │   │   ├── analysis.py          # Job analysis endpoints
│   │   │   ├── scraping.py          # Scraping operations
│   │   │   ├── documents.py         # Document management
│   │   │   ├── stats.py             # Statistics & metrics
│   │   │   ├── ats.py               # Application tracking
│   │   │   ├── analytics.py         # Analytics & learning
│   │   │   ├── followup.py          # Follow-up automation
│   │   │   ├── research.py          # Company research
│   │   │   ├── recommendations.py   # Job recommendations
│   │   │   ├── skills.py            # Skills gap analysis
│   │   │   └── cache.py             # Cache management
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM models (11 files)
│   │   │   ├── job.py               # Core job model
│   │   │   ├── document.py          # Document model
│   │   │   ├── candidate.py         # User profile
│   │   │   ├── analysis.py          # Analysis results
│   │   │   ├── application.py       # ATS models
│   │   │   ├── skills.py            # Skills models
│   │   │   ├── analytics.py         # Analytics models
│   │   │   ├── recommendations.py   # Recommendation models
│   │   │   ├── followup.py          # Follow-up models
│   │   │   └── research.py          # Research models
│   │   │
│   │   ├── schemas/                 # Pydantic schemas (11 files)
│   │   │   └── [*.py]               # Request/response models for each domain
│   │   │
│   │   ├── services/                # Business logic layer (17 services)
│   │   │   ├── ai_service.py        # AI provider abstraction [CRITICAL]
│   │   │   ├── claude_service.py    # Direct Claude integration
│   │   │   ├── openrouter_service.py # OpenRouter integration
│   │   │   ├── job_analyzer.py      # Job analysis logic
│   │   │   ├── semantic_matcher.py  # Semantic job matching
│   │   │   ├── document_generator.py # Resume/cover letter generation
│   │   │   ├── scraper_service.py   # Scraping orchestration
│   │   │   ├── email_service.py     # Email notifications
│   │   │   ├── google_drive_service.py # Drive integration
│   │   │   ├── cache_service.py     # Advanced Redis caching
│   │   │   ├── analytics_service.py # Learning & analytics
│   │   │   ├── ats_service.py       # Application tracking
│   │   │   ├── skills_service.py    # Skills gap analysis
│   │   │   ├── recommendation_service.py # ML recommendations
│   │   │   ├── followup_service.py  # Follow-up automation
│   │   │   └── research_service.py  # Company research
│   │   │
│   │   ├── tasks/                   # Celery async tasks
│   │   │   ├── celery_app.py        # Celery configuration
│   │   │   └── job_tasks.py         # Job processing tasks
│   │   │
│   │   ├── scrapers/                # Job board scrapers
│   │   │   ├── base_scraper.py      # Base scraper class
│   │   │   ├── linkedin_scraper.py  # LinkedIn (placeholder)
│   │   │   └── indeed_scraper.py    # Indeed (placeholder)
│   │   │
│   │   ├── prompts/                 # AI prompt templates
│   │   │   ├── job_analysis.py      # Analysis prompts
│   │   │   └── cover_letter.py      # Cover letter prompts
│   │   │
│   │   └── utils/                   # Shared utilities
│   │
│   ├── tests/                       # Comprehensive test suite
│   │   ├── conftest.py              # Shared pytest fixtures
│   │   ├── test_api/                # API endpoint tests (4 files)
│   │   ├── test_services/           # Service layer tests (9 files)
│   │   └── test_integration/        # End-to-end tests
│   │
│   ├── requirements.txt             # 72 Python dependencies
│   ├── pytest.ini                   # Pytest configuration
│   └── Dockerfile                   # Container definition
│
├── extension/                        # Chrome extension (Manifest V3)
│   ├── manifest.json                # Extension configuration
│   ├── content.js                   # Job data extraction
│   ├── background.js                # Service worker
│   ├── styles.css                   # UI styling
│   └── popup/                       # Settings popup UI
│
├── skills/                          # Job matching skill data
│   ├── job-match-analyzer/          # Claude skill for matching
│   │   ├── SKILL.md                 # Skill definition
│   │   ├── experience_inventory.csv # Work history
│   │   ├── skills_taxonomy.csv      # Skill categories
│   │   ├── corporate_translation.csv # Terminology mapping
│   │   └── achievement_library.csv  # Achievements
│   └── voice_profile.md             # Writing style profile
│
├── scripts/                         # Utilities
│   └── setup_google_auth.py         # Google OAuth setup
│
├── docs/                            # Documentation
│   ├── OPENROUTER_INTEGRATION.md    # OpenRouter guide
│   └── TEST_PROTOCOLS.md            # Testing guide
│
├── docker-compose.yml               # Multi-service orchestration
├── .env.example                     # Environment template (90+ vars)
├── README.md                        # Quick start guide
├── README_IMPLEMENTATION.md         # Detailed setup guide
└── JOB_AUTOMATION_BUILD_GUIDE.md    # Architecture guide
```

### Key File Locations

| Purpose | Location | Notes |
|---------|----------|-------|
| API Entry Point | `backend/app/main.py` | FastAPI app initialization |
| Configuration | `backend/app/config.py` | Pydantic settings with env vars |
| Database Setup | `backend/app/database.py` | SQLAlchemy engine & session |
| API Routes | `backend/app/api/*.py` | 12 routers with REST endpoints |
| Business Logic | `backend/app/services/*.py` | All core functionality |
| Data Models | `backend/app/models/*.py` | SQLAlchemy ORM models |
| Schemas | `backend/app/schemas/*.py` | Pydantic request/response models |
| Tests | `backend/tests/**/*.py` | Comprehensive test suite |

---

## Development Workflows

### Local Development Setup

```bash
# 1. Clone and setup environment
cp .env.example .env
# Edit .env with your API keys

# 2. Start services with Docker Compose
docker-compose up

# 3. Services available at:
# - Backend API: http://localhost:8000
# - Redis: localhost:6379
# - API Docs: http://localhost:8000/docs
```

### Development Without Docker

```bash
# 1. Setup Python environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Redis separately
redis-server

# 4. Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Run Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test types
pytest -m unit                  # Unit tests only
pytest -m integration           # Integration tests only
pytest -m "not slow"            # Exclude slow tests
pytest -m requires_redis        # Tests requiring Redis

# Run specific test file
pytest tests/test_services/test_ai_service.py

# Run with verbose output
pytest -v -s

# View coverage report
open htmlcov/index.html
```

### Code Quality Checks

```bash
# Format code with black
black backend/app

# Lint with flake8
flake8 backend/app

# Type checking with mypy
mypy backend/app
```

### Git Workflow

This project uses **feature branches** with the naming convention: `claude/claude-md-<session-id>`

```bash
# Current branch
git status

# Commit changes (when requested by user)
git add .
git commit -m "Brief description of changes"

# Push to remote (ALWAYS use -u flag)
git push -u origin <branch-name>

# CRITICAL: Branch must start with 'claude/' and end with session ID
# Example: claude/claude-md-mhz95r1hvk0kvnae-018VCaKJJBG7MBf2s9o3dLDC
```

### Deployment Workflow

```bash
# 1. Build Docker images
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Check logs
docker-compose logs -f backend

# 4. Stop services
docker-compose down

# 5. Clean restart
docker-compose down -v
docker-compose up --build
```

---

## Coding Conventions

### Python Code Style

#### 1. Import Organization
```python
# Standard library imports
from datetime import datetime
from typing import List, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

# Local imports
from ..database import get_db
from ..models.job import Job
from ..schemas.job import JobCreate, JobResponse
```

#### 2. Type Hints (REQUIRED)
```python
# Function signatures MUST have type hints
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
) -> JobResponse:
    """Create a new job entry"""
    pass

# Class attributes should have type hints
class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"
```

#### 3. Docstrings (Required for Public Functions)
```python
def analyze_job(job_id: int, db: Session) -> AnalysisResult:
    """
    Analyze a job posting using AI.

    Args:
        job_id: Database ID of the job to analyze
        db: Database session

    Returns:
        AnalysisResult with match score and reasoning

    Raises:
        HTTPException: If job not found or AI service fails
    """
    pass
```

#### 4. Error Handling Pattern
```python
# Always use try-except with specific exceptions
try:
    result = await ai_service.analyze(job_description)
except APIError as e:
    logger.error(f"AI API error: {e}")
    raise HTTPException(status_code=500, detail="AI analysis failed")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### 5. Logging Pattern
```python
from loguru import logger

# Use structured logging
logger.info(f"Processing job {job_id}")
logger.debug(f"Job data: {job_data}")
logger.warning(f"Low match score: {score}")
logger.error(f"Failed to process job {job_id}: {error}")
```

#### 6. Async/Await Usage
```python
# Use async for I/O-bound operations
async def create_job(job_data: JobCreate, db: Session):
    # Async endpoints in FastAPI
    pass

# Celery tasks for long-running operations
@celery_app.task
def process_job_analysis(job_id: int):
    # Background task processing
    pass
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `job_analyzer.py` |
| Classes | PascalCase | `JobAnalyzer` |
| Functions | snake_case | `analyze_job()` |
| Variables | snake_case | `match_score` |
| Constants | UPPER_SNAKE_CASE | `MAX_TOKENS` |
| Private methods | _leading_underscore | `_calculate_score()` |
| DB Models | PascalCase | `Job`, `Document` |
| Pydantic Schemas | PascalCase + suffix | `JobCreate`, `JobResponse` |
| API Routes | kebab-case | `/api/v1/job-analysis` |

### Code Organization Principles

#### 1. Service Layer Pattern
```python
# API routes are THIN - just routing and validation
@router.post("/analyze")
async def analyze_job(job_id: int, db: Session = Depends(get_db)):
    # Validation only
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404)

    # Delegate to service
    result = await job_analyzer.analyze(job)
    return result

# Business logic lives in services
class JobAnalyzer:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def analyze(self, job: Job) -> AnalysisResult:
        # All business logic here
        pass
```

#### 2. Dependency Injection
```python
# Use FastAPI's dependency injection
from fastapi import Depends

def get_ai_service() -> AIService:
    return AIService(config=settings)

@router.post("/analyze")
async def analyze_job(
    job_id: int,
    db: Session = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service)
):
    pass
```

#### 3. Configuration Management
```python
# All config from environment variables via Pydantic
from .config import settings

# Never hardcode values
api_key = settings.ANTHROPIC_API_KEY  # Good
api_key = "sk-ant-xxxxx"  # Bad

# Use property methods for computed values
@property
def job_titles_list(self) -> List[str]:
    return [title.strip() for title in self.DEFAULT_JOB_TITLES.split(",")]
```

---

## API Design Patterns

### Router Structure

Every API router follows this pattern:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from loguru import logger

from ..database import get_db
from ..models.job import Job
from ..schemas.job import JobCreate, JobResponse, JobUpdate

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    """Create endpoint"""
    pass


@router.get("/", response_model=List[JobResponse])
async def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List endpoint with pagination"""
    pass


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get by ID endpoint"""
    pass


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    """Update endpoint"""
    pass


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete endpoint"""
    pass
```

### REST API Conventions

| Method | Path | Purpose | Status Code |
|--------|------|---------|-------------|
| POST | `/resource` | Create new | 201 Created |
| GET | `/resource` | List all | 200 OK |
| GET | `/resource/{id}` | Get one | 200 OK |
| PATCH | `/resource/{id}` | Partial update | 200 OK |
| PUT | `/resource/{id}` | Full update | 200 OK |
| DELETE | `/resource/{id}` | Delete | 204 No Content |

### Response Patterns

#### Success Response
```python
{
    "id": 123,
    "status": "completed",
    "data": {...}
}
```

#### Error Response
```python
{
    "detail": "Job not found"
}
```

#### Paginated Response
```python
{
    "total": 150,
    "items": [...],
    "skip": 0,
    "limit": 100
}
```

### Current API Endpoints

```
/api/v1/jobs              - Job CRUD operations
/api/v1/analysis          - Job analysis & AI scoring
/api/v1/documents         - Resume & cover letter management
/api/v1/scraping          - Web scraping operations
/api/v1/stats             - Statistics & metrics
/api/v1/ats               - Application tracking system
/api/v1/analytics         - Learning & analytics
/api/v1/followup          - Follow-up automation
/api/v1/research          - Company research
/api/v1/recommendations   - ML job recommendations
/api/v1/skills            - Skills gap analysis
/api/v1/cache             - Cache management
```

---

## Database & ORM Patterns

### SQLAlchemy Model Pattern

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Job(Base):
    __tablename__ = "jobs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Required fields
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    job_url = Column(String, unique=True, nullable=False)

    # Optional fields
    description = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    status = Column(String, default="pending", index=True)

    # Timestamps (ALWAYS include)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="job", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="job", uselist=False)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    document_type = Column(String, nullable=False)  # resume, cover_letter
    file_path = Column(String, nullable=False)
    drive_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="documents")
```

### Pydantic Schema Pattern

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


# CREATE schema - used for POST requests
class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    job_url: HttpUrl
    description: Optional[str] = None
    location: Optional[str] = None


# UPDATE schema - used for PATCH requests
class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    match_score: Optional[float] = None


# RESPONSE schema - used for API responses
class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    job_url: str
    description: Optional[str]
    match_score: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from ORM models
```

### Database Operations Pattern

```python
# CREATE
job = Job(**job_data.model_dump())
db.add(job)
db.commit()
db.refresh(job)

# READ
job = db.query(Job).filter(Job.id == job_id).first()
jobs = db.query(Job).filter(Job.status == "pending").all()

# UPDATE
job = db.query(Job).filter(Job.id == job_id).first()
for field, value in update_data.model_dump(exclude_unset=True).items():
    setattr(job, field, value)
job.updated_at = datetime.utcnow()
db.commit()
db.refresh(job)

# DELETE
db.delete(job)
db.commit()

# QUERY with filters
jobs = db.query(Job)\
    .filter(Job.status == "pending")\
    .filter(Job.match_score >= 70)\
    .order_by(Job.match_score.desc())\
    .offset(skip)\
    .limit(limit)\
    .all()
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── test_api/                      # API endpoint tests
│   ├── test_jobs_api.py
│   ├── test_analysis_api.py
│   └── test_documents_api.py
├── test_services/                 # Service layer tests
│   ├── test_ai_service.py
│   ├── test_job_analyzer.py
│   └── test_cache.py
└── test_integration/              # End-to-end tests
    └── test_full_workflow.py
```

### Pytest Configuration (pytest.ini)

```ini
[pytest]
minversion = 7.0
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests

addopts =
    -v                          # Verbose
    -ra                         # Show summary
    --showlocals                # Show local vars in errors
    --strict-markers            # Fail on unknown markers

markers =
    slow: marks tests as slow
    integration: integration tests
    unit: unit tests
    api: API tests
    requires_redis: requires Redis
    requires_db: requires database
    requires_api_key: requires API keys
```

### Shared Fixtures (conftest.py)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with test database"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_ai_service(mocker):
    """Mock AI service for testing"""
    mock = mocker.Mock()
    mock.analyze.return_value = {"score": 85, "reasoning": "Great match"}
    return mock
```

### Test Patterns

#### Unit Test Example
```python
import pytest
from app.services.job_analyzer import JobAnalyzer

@pytest.mark.unit
def test_calculate_match_score(mock_ai_service):
    """Test match score calculation"""
    analyzer = JobAnalyzer(ai_service=mock_ai_service)
    score = analyzer.calculate_score(skills_match=0.8, experience_match=0.9)
    assert score >= 0 and score <= 100
```

#### API Test Example
```python
import pytest

@pytest.mark.api
def test_create_job(client):
    """Test job creation endpoint"""
    job_data = {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "job_url": "https://example.com/job/123"
    }
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == 201
    assert response.json()["title"] == job_data["title"]
```

#### Integration Test Example
```python
@pytest.mark.integration
@pytest.mark.slow
def test_full_job_workflow(client, db_session):
    """Test complete job processing workflow"""
    # 1. Create job
    job_response = client.post("/api/v1/jobs/", json=job_data)
    job_id = job_response.json()["id"]

    # 2. Analyze job
    analysis_response = client.post(f"/api/v1/analysis/{job_id}")
    assert analysis_response.status_code == 200

    # 3. Generate documents
    docs_response = client.post(f"/api/v1/documents/{job_id}/generate")
    assert docs_response.status_code == 200
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific markers
pytest -m unit
pytest -m "not slow"
pytest -m requires_redis

# Specific file
pytest tests/test_services/test_ai_service.py

# Stop on first failure
pytest -x

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

---

## Configuration Management

### Environment Variables (.env)

The project uses **90+ environment variables** organized into categories:

#### AI API Keys
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENROUTER_API_KEY=sk-or-xxxxx
OPENAI_API_KEY=sk-xxxxx
```

#### Model Configuration
```bash
AI_PROVIDER=openrouter  # anthropic, openrouter, openai
ANALYSIS_MODEL=anthropic/claude-3.5-sonnet
PRESCREENING_MODEL=meta-llama/llama-3.1-8b-instruct
COVER_LETTER_MODEL=anthropic/claude-3.5-sonnet
RESUME_MODEL=openai/gpt-4-turbo
FALLBACK_MODEL=google/gemini-pro-1.5
```

#### Cost Optimization
```bash
MAX_COST_PER_JOB=0.50
USE_CHEAP_PRESCREENING=true
CHEAP_MODEL_THRESHOLD=60
ENABLE_COST_TRACKING=true
ENABLE_ENSEMBLE=false
```

#### Database
```bash
DATABASE_URL=sqlite:///./job_automation.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/dbname
```

#### Redis
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_KEY_PREFIX=jobfinder
```

#### Google Cloud
```bash
GOOGLE_CREDENTIALS_PATH=./credentials/service-account.json
GOOGLE_OAUTH_CREDENTIALS_PATH=./credentials/oauth-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id
```

#### Application Settings
```bash
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO
MIN_MATCH_SCORE=70
```

### Configuration Access Pattern

```python
# Access via settings object
from app.config import settings

# Simple values
api_key = settings.ANTHROPIC_API_KEY
port = settings.API_PORT

# Computed properties
job_titles = settings.job_titles_list  # Parses comma-separated string
locations = settings.locations_list
ensemble_models = settings.ensemble_models_list

# Environment-specific behavior
if settings.ENVIRONMENT == "development":
    # Development-only code
    pass
```

---

## Key Integration Points

### 1. AI Service Integration

The system uses a **provider abstraction layer** for AI services:

```python
from app.services.ai_service import AIService

# Automatically uses configured provider (Anthropic, OpenRouter, or OpenAI)
ai_service = AIService()

# Analyze job
result = await ai_service.analyze_job(
    job_description="...",
    candidate_profile="..."
)
```

#### Provider Switching
Change via `AI_PROVIDER` environment variable:
- `anthropic` → Direct Claude API
- `openrouter` → Multi-model access (100+ models)
- `openai` → OpenAI API

### 2. Google Cloud Integration

#### Google Drive
```python
from app.services.google_drive_service import GoogleDriveService

drive_service = GoogleDriveService()

# Create folder structure
folder_id = drive_service.create_job_folder(company="Tech Corp", job_title="Engineer")

# Upload document
file_id = drive_service.upload_file(
    file_path="resume.docx",
    folder_id=folder_id,
    file_name="Resume_TechCorp.docx"
)
```

#### Gmail
```python
from app.services.email_service import EmailService

email_service = EmailService()

# Send notification
email_service.send_job_notification(
    to=settings.NOTIFICATION_EMAIL,
    job=job,
    analysis_result=result,
    drive_link=drive_link
)
```

### 3. Redis Caching

```python
from app.services.cache_service import CacheService

cache = CacheService()

# Set cache
await cache.set("job_analysis_123", analysis_result, ttl=3600)

# Get cache
result = await cache.get("job_analysis_123")

# Delete cache
await cache.delete("job_analysis_123")

# Clear all cache
await cache.clear_all()
```

### 4. Celery Background Tasks

```python
from app.tasks.job_tasks import process_job_analysis

# Queue task
task = process_job_analysis.delay(job_id=123)

# Check status
task_result = process_job_analysis.AsyncResult(task.id)
if task_result.ready():
    result = task_result.result
```

---

## Common Tasks

### Adding a New API Endpoint

1. **Create/Update Router** (`backend/app/api/your_router.py`)
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.your_schema import YourCreate, YourResponse

router = APIRouter()

@router.post("/", response_model=YourResponse)
async def create_resource(data: YourCreate, db: Session = Depends(get_db)):
    # Implementation
    pass
```

2. **Register Router** (`backend/app/main.py`)
```python
from .api import your_router

app.include_router(
    your_router.router,
    prefix="/api/v1/your-resource",
    tags=["your-resource"]
)
```

### Adding a New Database Model

1. **Create Model** (`backend/app/models/your_model.py`)
```python
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from ..database import Base

class YourModel(Base):
    __tablename__ = "your_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. **Import in database.py**
```python
def init_db():
    from .models import job, document, your_model  # Add import
    Base.metadata.create_all(bind=engine)
```

3. **Create Pydantic Schemas** (`backend/app/schemas/your_model.py`)
```python
class YourCreate(BaseModel):
    name: str

class YourResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
```

### Adding a New Service

1. **Create Service** (`backend/app/services/your_service.py`)
```python
from loguru import logger

class YourService:
    def __init__(self):
        self.initialized = True

    async def do_something(self, param: str) -> dict:
        """Service method"""
        logger.info(f"Processing: {param}")
        # Implementation
        return {"result": "success"}
```

2. **Use in API Router**
```python
from ..services.your_service import YourService

your_service = YourService()

@router.post("/action")
async def perform_action(param: str):
    result = await your_service.do_something(param)
    return result
```

### Adding Tests

1. **Create Test File** (`backend/tests/test_services/test_your_service.py`)
```python
import pytest
from app.services.your_service import YourService

@pytest.mark.unit
def test_your_service():
    service = YourService()
    result = service.do_something("test")
    assert result["result"] == "success"
```

2. **Run Tests**
```bash
pytest tests/test_services/test_your_service.py -v
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Best Practices for AI Assistants

### 1. Understanding Context

Before making changes:
- **Read related files** to understand current implementation
- **Check existing patterns** in similar code
- **Review tests** to understand expected behavior
- **Consult docs** for integration details

### 2. Making Changes

When modifying code:
- **Follow existing patterns** - Don't introduce new styles
- **Maintain type hints** - All functions need type annotations
- **Add/update tests** - Test coverage is important
- **Update docstrings** - Keep documentation current
- **Use loguru** - Consistent logging across codebase

### 3. API Changes

When adding/modifying endpoints:
- **Follow REST conventions** - Use standard HTTP methods
- **Use Pydantic schemas** - For request/response validation
- **Add to main.py** - Register new routers
- **Document with docstrings** - Explain endpoint purpose
- **Write API tests** - Test happy path and error cases

### 4. Database Changes

When modifying models:
- **Add timestamps** - created_at, updated_at on all models
- **Use indexes** - For frequently queried fields
- **Define relationships** - Use SQLAlchemy relationships
- **Update init_db()** - Import new models
- **Create schemas** - Pydantic models for API

### 5. Service Layer

When adding business logic:
- **Create service classes** - Don't put logic in API routes
- **Use dependency injection** - Via FastAPI Depends()
- **Handle errors gracefully** - Try-except with logging
- **Make it testable** - Mock external dependencies
- **Cache when appropriate** - Use Redis for expensive operations

### 6. Testing

When writing tests:
- **Use appropriate markers** - @pytest.mark.unit, @pytest.mark.integration
- **Mock external services** - Don't call real APIs in tests
- **Use fixtures** - Leverage conftest.py fixtures
- **Test edge cases** - Not just happy paths
- **Aim for high coverage** - 80%+ is target

### 7. Configuration

When adding settings:
- **Add to Settings class** - In backend/app/config.py
- **Add to .env.example** - Document the setting
- **Use type hints** - Specify expected type
- **Provide defaults** - When sensible
- **Add to docs** - Update CLAUDE.md if significant

### 8. Git Workflow

When committing:
- **Write clear messages** - Describe what and why
- **Commit related changes** - Logical groupings
- **Test before committing** - Ensure tests pass
- **Push with -u flag** - `git push -u origin branch-name`
- **Use correct branch** - Must start with `claude/`

### 9. Documentation

When updating docs:
- **Update CLAUDE.md** - For architectural changes
- **Update README** - For user-facing changes
- **Add inline comments** - For complex logic
- **Write docstrings** - For all public functions
- **Keep examples current** - Update when APIs change

### 10. Common Pitfalls to Avoid

❌ **Don't:**
- Hardcode API keys or secrets
- Put business logic in API routes
- Skip type hints
- Ignore existing patterns
- Commit without testing
- Break existing tests
- Remove error handling
- Skip logging

✅ **Do:**
- Use environment variables
- Put logic in services
- Add type hints everywhere
- Follow existing conventions
- Run tests before committing
- Fix broken tests
- Add comprehensive error handling
- Log important operations

---

## Troubleshooting

### Common Issues

#### Redis Connection Failed
```bash
# Check Redis is running
docker ps | grep redis

# Start Redis
docker-compose up redis

# Or locally
redis-server
```

#### Database Locked (SQLite)
```bash
# SQLite doesn't handle concurrent writes well
# Consider switching to PostgreSQL for production
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

#### API Key Not Found
```bash
# Verify .env file exists and has keys
cat .env | grep API_KEY

# Ensure .env is loaded
# Check backend/.env and root .env
```

#### Import Errors
```bash
# Ensure in correct directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
echo $PYTHONPATH
```

#### Tests Failing
```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv -s

# Check for missing fixtures
grep -r "conftest.py" tests/
```

---

## Quick Reference

### File Paths Reference
```bash
# Main application
backend/app/main.py           # FastAPI entry point
backend/app/config.py         # Configuration
backend/app/database.py       # Database setup

# API routes
backend/app/api/*.py          # All API routers

# Business logic
backend/app/services/*.py     # Service layer

# Data models
backend/app/models/*.py       # SQLAlchemy models
backend/app/schemas/*.py      # Pydantic schemas

# Tests
backend/tests/                # Test suite
backend/pytest.ini            # Test configuration

# Configuration
.env                          # Environment variables
docker-compose.yml            # Docker setup
```

### Useful Commands
```bash
# Development
docker-compose up                    # Start all services
uvicorn app.main:app --reload        # Run backend only
celery -A app.tasks.celery_app worker # Run Celery

# Testing
pytest                               # Run all tests
pytest -m unit                       # Unit tests only
pytest --cov=app                     # With coverage

# Code quality
black backend/app                    # Format code
flake8 backend/app                   # Lint code
mypy backend/app                     # Type check

# Database
alembic upgrade head                 # Run migrations
alembic revision --autogenerate      # Create migration

# Git
git status                           # Check status
git add .                            # Stage all
git commit -m "message"              # Commit
git push -u origin branch            # Push
```

### Environment Quick Setup
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your keys
nano .env

# 3. Start services
docker-compose up

# 4. Access API
curl http://localhost:8000/health

# 5. View docs
open http://localhost:8000/docs
```

---

## Additional Resources

### Documentation Files
- `README.md` - Quick start guide
- `README_IMPLEMENTATION.md` - Detailed setup (304 lines)
- `JOB_AUTOMATION_BUILD_GUIDE.md` - Architecture guide (158 lines)
- `docs/OPENROUTER_INTEGRATION.md` - Multi-model guide (347 lines)
- `docs/TEST_PROTOCOLS.md` - Testing guide

### External Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Celery Docs](https://docs.celeryproject.org/)
- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [OpenRouter Docs](https://openrouter.ai/docs)

### Key Concepts
- **Service Layer Pattern** - Business logic separated from API routes
- **Provider Abstraction** - Swappable AI providers
- **Async Processing** - Celery for long-running tasks
- **Semantic Matching** - Pre-filtering before expensive AI calls
- **Two-Tier Analysis** - Cheap prescreening + expensive final analysis
- **Redis Caching** - Multi-tier with fallback support

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-14 | Initial comprehensive CLAUDE.md creation |

---

## Maintenance Notes

This file should be updated when:
- New major features are added
- API structure changes significantly
- Development workflows change
- New conventions are established
- Configuration requirements change
- Testing patterns evolve

**Last reviewed by**: Claude AI Assistant
**Next review**: When significant architectural changes occur

---

## Contact & Support

For questions about this codebase:
1. Review this CLAUDE.md file
2. Check relevant documentation in `docs/`
3. Review code examples in existing implementation
4. Consult external documentation links above

---

*This guide is designed to help AI assistants quickly understand and work effectively with this codebase while maintaining consistency and quality.*
