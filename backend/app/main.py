from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from loguru import logger

from .config import settings
from .database import init_db
from .api import jobs, analysis, documents, scraping, stats, ats, analytics, followup, research, recommendations, skills, cache


# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Job Automation System...")
    init_db()
    logger.info("✅ Database initialized")
    yield
    # Shutdown
    logger.info("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Job Application Automation System",
    description="Automated job search, analysis, and application document generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/")
async def root():
    return {
        "message": "Job Automation System API",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include routers
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(scraping.router, prefix="/api/v1/scraping", tags=["scraping"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["statistics"])
app.include_router(ats.router, prefix="/api/v1/ats", tags=["application-tracking"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(followup.router, prefix="/api/v1/followup", tags=["follow-up"])
app.include_router(research.router, prefix="/api/v1/research", tags=["company-research"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills-gap-analysis"])
app.include_router(cache.router, prefix="/api/v1/cache", tags=["cache"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development"
    )
