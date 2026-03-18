"""
API Request/Response Models
===========================
Pydantic models for FastAPI endpoints.
Auto-generates OpenAPI docs.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class RunRequest(BaseModel):
    trigger: str = "seasonal_spring"


class RunResponse(BaseModel):
    run_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    run_id: str
    status: str
    assets_generated: int
    assets_passed: int
    current_node: Optional[str] = None


class ScoreSummary(BaseModel):
    asset_type: str
    composite: float
    passed: bool
    version: int
    deterministic_score: Optional[float] = None
    brand_alignment: Optional[int] = None
    trend_alignment: Optional[int] = None
    feedback: List[str] = []


class BundleResponse(BaseModel):
    campaign_metadata: Dict[str, Any]
    final_bundle: Dict[str, Any]
    scores: Dict[str, Any]
    trend_narratives: List[str]
    audit_log_count: int


class AuditLogResponse(BaseModel):
    run_id: str
    entries: List[Dict[str, Any]]
    total_entries: int
