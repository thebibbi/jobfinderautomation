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

    # AI Provider Configuration
    AI_PROVIDER: str = "anthropic"  # anthropic, openrouter, openai

    # Anthropic Claude
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS: int = 8000

    # OpenRouter
    OPENROUTER_API_KEY: str = ""
    ANALYSIS_MODEL: str = "anthropic/claude-3.5-sonnet"
    PRESCREENING_MODEL: str = "meta-llama/llama-3.1-8b-instruct"
    COVER_LETTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    RESUME_MODEL: str = "openai/gpt-4-turbo"
    FALLBACK_MODEL: str = "google/gemini-pro-1.5"

    # Ensemble & Cost Optimization
    ENABLE_ENSEMBLE: bool = False
    ENSEMBLE_MODELS: str = ""
    MAX_COST_PER_JOB: float = 0.50
    USE_CHEAP_PRESCREENING: bool = True
    CHEAP_MODEL_THRESHOLD: int = 60
    ENABLE_COST_TRACKING: bool = True

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

    @property
    def ensemble_models_list(self) -> List[str]:
        if not self.ENSEMBLE_MODELS:
            return []
        return [model.strip() for model in self.ENSEMBLE_MODELS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
