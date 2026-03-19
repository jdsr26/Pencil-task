"""
API Request/Response Models
===========================
Pydantic models for FastAPI endpoints.
Auto-generates OpenAPI docs.
"""

from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Optional


ALLOWED_MODELS = [
    "claude-haiku-3-5-20241022",
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

ALLOWED_IMAGE_GENERATORS = [
    "midjourney-v6",
    "flux-1.1-pro",
    "gpt-image-1",
]

ALLOWED_VIDEO_GENERATORS = [
    "runway-gen4",
    "veo-3",
    "sora",
]


class RunRequest(BaseModel):
    trigger: str = "seasonal_spring"
    product: str = "ceramidin_cream"
    generation_model: str = "claude-sonnet-4-20250514"
    judge_model: Optional[str] = None
    image_generator: str = "midjourney-v6"
    video_generator: str = "runway-gen4"

    @field_validator("generation_model")
    @classmethod
    def validate_generation_model(cls, value: str) -> str:
        if value not in ALLOWED_MODELS:
            raise ValueError(
                f"Unsupported generation_model '{value}'. "
                f"Allowed: {', '.join(ALLOWED_MODELS)}"
            )
        return value

    @field_validator("judge_model")
    @classmethod
    def validate_judge_model(cls, value: Optional[str]) -> Optional[str]:
        if value and value not in ALLOWED_MODELS:
            raise ValueError(
                f"Unsupported judge_model '{value}'. "
                f"Allowed: {', '.join(ALLOWED_MODELS)}"
            )
        return value

    @field_validator("image_generator")
    @classmethod
    def validate_image_generator(cls, value: str) -> str:
        if value not in ALLOWED_IMAGE_GENERATORS:
            raise ValueError(
                f"Unsupported image_generator '{value}'. "
                f"Allowed: {', '.join(ALLOWED_IMAGE_GENERATORS)}"
            )
        return value

    @field_validator("video_generator")
    @classmethod
    def validate_video_generator(cls, value: str) -> str:
        if value not in ALLOWED_VIDEO_GENERATORS:
            raise ValueError(
                f"Unsupported video_generator '{value}'. "
                f"Allowed: {', '.join(ALLOWED_VIDEO_GENERATORS)}"
            )
        return value


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
