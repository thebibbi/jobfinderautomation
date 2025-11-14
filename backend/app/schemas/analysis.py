from pydantic import BaseModel
from typing import Dict, Any, Optional


class AnalysisRequest(BaseModel):
    force_reanalyze: bool = False


class AnalysisResponse(BaseModel):
    job_id: int
    match_score: float
    analysis: Dict[str, Any]
    message: str
