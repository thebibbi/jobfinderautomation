from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Anthropic Claude
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS: int = 8000

    # Google Cloud
    GOOGLE_CREDENTIALS_PATH: str
    GOOGLE_OAUTH_CREDENTIALS_PATH: str
    GOOGLE_DRIVE_FOLDER_ID: str

    # Email
    NOTIFICATION_EMAIL: str
    SENDER_EMAIL: str

    # Job Search
    DEFAULT_LOCATION: str
    DEFAULT_JOB_TITLES: str
    MIN_MATCH_SCORE: int = 70

    # Job Board APIs (Optional)
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    INDEED_API_KEY: str = ""
    GLASSDOOR_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def job_titles_list(self) -> List[str]:
        return [title.strip() for title in self.DEFAULT_JOB_TITLES.split(",")]

    @property
    def locations_list(self) -> List[str]:
        return [loc.strip() for loc in self.DEFAULT_LOCATION.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
