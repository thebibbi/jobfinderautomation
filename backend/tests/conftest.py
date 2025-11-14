"""
Pytest configuration and shared fixtures for job automation testing
"""
import pytest
import asyncio
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import os
import tempfile

from app.database import Base, get_db
from app.main import app
from app.models.job import Job
from app.models.document import Document, DocumentType
from app.config import settings


# ==================== Database Fixtures ====================

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine"""
    # Use in-memory SQLite for fast testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==================== Sample Data Fixtures ====================

@pytest.fixture
def sample_job_data() -> Dict[str, Any]:
    """Sample job posting data"""
    return {
        "company": "TechCorp",
        "job_title": "Data Analyst",
        "job_description": """
        We are seeking a Data Analyst with strong analytical skills.

        Requirements:
        - 3+ years of experience in data analysis
        - Proficiency in SQL, Python, and data visualization
        - Experience with statistical analysis
        - Strong communication skills

        Responsibilities:
        - Analyze large datasets to identify trends
        - Create dashboards and reports
        - Collaborate with cross-functional teams
        - Present insights to stakeholders
        """,
        "job_url": "https://example.com/jobs/12345",
        "source": "indeed",
        "location": "Remote",
        "salary_range": "$80,000 - $110,000"
    }


@pytest.fixture
def sample_job_data_low_match() -> Dict[str, Any]:
    """Sample job posting with low match (for testing prescreening)"""
    return {
        "company": "StartupXYZ",
        "job_title": "Senior C++ Developer",
        "job_description": """
        Looking for an experienced C++ developer for embedded systems.

        Requirements:
        - 10+ years of C++ development
        - Embedded systems experience
        - Real-time operating systems
        - Hardware interfacing
        """,
        "job_url": "https://example.com/jobs/67890",
        "source": "linkedin",
        "location": "On-site",
        "salary_range": "$150,000+"
    }


@pytest.fixture
def sample_analysis_result() -> Dict[str, Any]:
    """Sample job analysis result"""
    return {
        "match_score": 85,
        "should_apply": True,
        "key_strengths": [
            "Strong data analysis background",
            "Proficiency in Python and SQL",
            "Experience creating visualizations"
        ],
        "potential_concerns": [
            "May need to demonstrate advanced statistical knowledge"
        ],
        "recommended_talking_points": [
            "Highlight curriculum data analysis experience",
            "Emphasize process improvement track record",
            "Showcase technical proficiency"
        ],
        "cover_letter_strategy": "Position teaching experience as data-driven decision making"
    }


@pytest.fixture
def sample_low_score_analysis() -> Dict[str, Any]:
    """Sample analysis result with low match score"""
    return {
        "match_score": 45,
        "should_apply": False,
        "key_strengths": [
            "Problem-solving skills",
            "Analytical thinking"
        ],
        "potential_concerns": [
            "Lacks C++ experience",
            "No embedded systems background",
            "Different technical stack"
        ],
        "recommended_talking_points": [],
        "cover_letter_strategy": "Not recommended to apply"
    }


# ==================== Mock AI Service Fixtures ====================

@pytest.fixture
def mock_claude_response():
    """Mock Claude API response"""
    return {
        "id": "msg_test123",
        "type": "message",
        "role": "assistant",
        "content": [{
            "type": "text",
            "text": """
            MATCH SCORE: 85/100

            KEY STRENGTHS:
            - Strong data analysis background
            - Proficiency in Python and SQL

            POTENTIAL CONCERNS:
            - May need to demonstrate advanced statistical knowledge

            RECOMMENDED TALKING POINTS:
            - Highlight curriculum data analysis experience

            COVER LETTER STRATEGY:
            Position teaching experience as data-driven decision making

            SHOULD APPLY: Yes
            """
        }],
        "model": "claude-3-5-sonnet-20241022",
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 200
        }
    }


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response"""
    return {
        "id": "gen-test123",
        "model": "anthropic/claude-3.5-sonnet",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": """
                MATCH SCORE: 85/100

                KEY STRENGTHS:
                - Strong data analysis background

                SHOULD APPLY: Yes
                """
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 200,
            "total_tokens": 1200
        }
    }


@pytest.fixture
def mock_openrouter_low_score_response():
    """Mock OpenRouter response with low score (for prescreening tests)"""
    return {
        "id": "gen-test456",
        "model": "meta-llama/llama-3.1-8b-instruct",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": """
                MATCH SCORE: 45/100

                KEY STRENGTHS:
                - Problem-solving skills

                POTENTIAL CONCERNS:
                - Lacks required technical experience

                SHOULD APPLY: No
                """
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 800,
            "completion_tokens": 150,
            "total_tokens": 950
        }
    }


# ==================== Mock External Services ====================

@pytest.fixture
def mock_google_drive_service(monkeypatch):
    """Mock Google Drive service"""
    class MockDriveService:
        def create_job_folder(self, company: str, job_title: str, job_id: str):
            return {
                "folder_id": f"mock_folder_{job_id}",
                "folder_url": f"https://drive.google.com/drive/folders/mock_{job_id}"
            }

        def upload_document(self, file_bytes, filename: str, folder_id: str, mime_type: str):
            return {
                "file_id": f"mock_file_{filename}",
                "file_url": f"https://drive.google.com/file/d/mock_{filename}"
            }

    return MockDriveService()


@pytest.fixture
def mock_email_service(monkeypatch):
    """Mock email service"""
    class MockEmailService:
        def __init__(self):
            self.sent_emails = []

        def send_job_analysis_notification(self, job_data: Dict[str, Any], analysis_results: Dict[str, Any]):
            self.sent_emails.append({
                "type": "analysis",
                "job": job_data,
                "analysis": analysis_results
            })
            return True

        def send_documents_ready_notification(self, job_data: Dict[str, Any], drive_folder_url: str):
            self.sent_emails.append({
                "type": "documents_ready",
                "job": job_data,
                "folder_url": drive_folder_url
            })
            return True

    return MockEmailService()


# ==================== Environment Setup ====================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["LOG_LEVEL"] = "ERROR"  # Reduce noise during tests
    os.environ["AI_PROVIDER"] = "anthropic"  # Default for tests
    os.environ["MIN_MATCH_SCORE"] = "70"
    yield
    # Cleanup if needed


# ==================== Async Support ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== Helper Functions ====================

@pytest.fixture
def create_test_job(db_session: Session):
    """Factory fixture to create test jobs"""
    def _create_job(**kwargs) -> Job:
        default_data = {
            "job_id": "test_job_123",
            "company": "TestCorp",
            "job_title": "Test Position",
            "job_description": "Test description",
            "job_url": "https://example.com/test",
            "source": "test",
            "status": "discovered"
        }
        default_data.update(kwargs)

        job = Job(**default_data)
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    return _create_job


@pytest.fixture
def create_test_document(db_session: Session):
    """Factory fixture to create test documents"""
    def _create_document(job_id: int, document_type: DocumentType, **kwargs) -> Document:
        default_data = {
            "job_id": job_id,
            "document_type": document_type,
            "drive_file_id": f"test_file_{document_type.value}",
            "drive_file_url": f"https://drive.google.com/file/d/test_{document_type.value}",
            "local_path": f"/tmp/test_{document_type.value}.docx"
        }
        default_data.update(kwargs)

        doc = Document(**default_data)
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)
        return doc

    return _create_document
