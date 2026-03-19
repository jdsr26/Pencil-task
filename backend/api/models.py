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

ALLOWED_RUN_MODES = [
    "creative",
    "demo",
]

ALLOWED_RETRY_POLICIES = [
    "production_selective",
    "benchmark_none",
    "benchmark_rerun_all",
]


class RunRequest(BaseModel):
    trigger: str = "seasonal_spring"
    product: str = "ceramidin_cream"
    generation_model: str = "claude-sonnet-4-20250514"
    judge_model: Optional[str] = None
    image_generator: str = "midjourney-v6"
    video_generator: str = "runway-gen4"
    run_mode: str = "creative"
    retry_policy: str = "production_selective"

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

    @field_validator("run_mode")
    @classmethod
    def validate_run_mode(cls, value: str) -> str:
        if value not in ALLOWED_RUN_MODES:
            raise ValueError(
                f"Unsupported run_mode '{value}'. "
                f"Allowed: {', '.join(ALLOWED_RUN_MODES)}"
            )
        return value

    @field_validator("retry_policy")
    @classmethod
    def validate_retry_policy(cls, value: str) -> str:
        if value not in ALLOWED_RETRY_POLICIES:
            raise ValueError(
                f"Unsupported retry_policy '{value}'. "
                f"Allowed: {', '.join(ALLOWED_RETRY_POLICIES)}"
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
