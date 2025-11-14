from fastapi import APIRouter, Depends
from typing import Dict, Any

from ..services.ai_service import get_ai_service

router = APIRouter()


@router.get("/ai")
async def get_ai_stats() -> Dict[str, Any]:
    """
    Get AI service usage statistics

    Returns statistics about:
    - Current provider (Claude, OpenRouter, etc.)
    - Configuration (ensemble, prescreening, etc.)
    - API calls made
    - Costs (if tracking enabled)
    - Model performance
    """
    ai_service = get_ai_service()
    stats = ai_service.get_stats()

    return {
        "success": True,
        "stats": stats
    }


@router.get("/")
async def get_all_stats() -> Dict[str, Any]:
    """
    Get comprehensive system statistics

    Includes AI, database, and processing statistics
    """
    ai_service = get_ai_service()

    return {
        "success": True,
        "ai": ai_service.get_stats(),
        # Could add more stats here:
        # "database": {...},
        # "jobs_processed": {...},
        # "success_rate": {...}
    }
