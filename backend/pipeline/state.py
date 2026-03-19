"""
Pipeline State Schema
=====================
Defines the complete state that flows through the LangGraph pipeline.
Every node reads from and writes to this state.
Pydantic enforces type safety at every boundary.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class AssetType(str, Enum):
    """The four asset types this pipeline generates."""
    ADS = "ads"
    VIDEO = "video"
    IMAGE = "image"
    BLOG = "blog"


class TriggerType(str, Enum):
    """What initiated this pipeline run."""
    SCHEDULED = "scheduled"
    COMPETITOR_LAUNCH = "event_competitor_launch"
    VIRAL_TREND = "event_viral_trend"
    SEASONAL_WINTER = "seasonal_winter"
    SEASONAL_SPRING = "seasonal_spring"
    MANUAL = "manual"


class EvidenceDecision(str, Enum):
    """Outcome of the evidence sufficiency check."""
    SUFFICIENT = "sufficient"
    WEAK = "weak"
    POOR = "poor"


# ─────────────────────────────────────────────
# Phase 1: Sourcing Models
# ─────────────────────────────────────────────

class SourceRecord(BaseModel):
    """One sourced trend data record from Phase 1."""
    id: str
    title: str
    source_url: str
    source_name: str
    category: str
    publish_date: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    key_claims: List[str]
    competitor_mentions: List[str] = []
    trend_tags: List[str]
    product_link_rationale: str
    synthetic: bool = False


# ─────────────────────────────────────────────
# Phase 2: Generation Models
# ─────────────────────────────────────────────

class AssetOutput(BaseModel):
    """One generated creative asset from Phase 2."""
    content: str = ""
    version: int = Field(default=1, ge=1)
    feedback_history: List[str] = []
    generated_at: Optional[str] = None
    model_used: str = "claude-sonnet-4-20250514"
    prompt_hash: Optional[str] = None


# ─────────────────────────────────────────────
# Phase 3: Scoring Models
# ─────────────────────────────────────────────

class DeterministicCheckDetail(BaseModel):
    """One individual rule-based check result."""
    check_name: str
    passed: bool
    expected: str
    actual: str
    message: str = ""


class DeterministicResult(BaseModel):
    """Aggregated results from all rule-based checks for one asset."""
    asset_type: AssetType
    checks: List[DeterministicCheckDetail] = []
    checks_passed: int = 0
    checks_total: int = 0
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    failures: List[str] = []


class LLMJudgeResult(BaseModel):
    """Subjective scoring from the LLM judge for one asset."""
    asset_type: AssetType
    brand_alignment: int = Field(default=0, ge=0, le=100)
    trend_alignment: int = Field(default=0, ge=0, le=100)
    feedback: List[str] = []
    raw_response: Optional[str] = None
    model_used: str = "claude-sonnet-4-20250514"


class AssetScore(BaseModel):
    """Combined scoring for one asset — deterministic + LLM + composite."""
    asset_type: AssetType
    deterministic: Optional[DeterministicResult] = None
    llm_judge: Optional[LLMJudgeResult] = None
    composite: float = Field(default=0.0, ge=0.0, le=100.0)
    passed: bool = False
    all_feedback: List[str] = []


class CampaignCoherence(BaseModel):
    """Cross-asset consistency check result."""
    coherent: bool = False
    issues: List[str] = []
    narrative_consistent: bool = False
    tone_consistent: bool = False
    product_consistent: bool = False
    cta_aligned: bool = False


# ─────────────────────────────────────────────
# Observability
# ─────────────────────────────────────────────

class AuditEntry(BaseModel):
    """One entry in the pipeline audit trail."""
    timestamp: str
    node: str
    action: str
    input_snapshot: Dict[str, Any] = {}
    output_snapshot: Dict[str, Any] = {}
    model_used: Optional[str] = None
    prompt_hash: Optional[str] = None
    latency_ms: Optional[int] = None
    metadata: Dict[str, Any] = {}


# ─────────────────────────────────────────────
# Complete Pipeline State
# ─────────────────────────────────────────────

class PipelineState(BaseModel):
    """
    Complete pipeline state.
    This is THE single source of truth that flows through every LangGraph node.
    Each node reads what it needs and writes its outputs back.
    """

    # ─── Run Metadata ───
    run_id: str = ""
    trigger: TriggerType = TriggerType.MANUAL
    generation_model: str = "claude-sonnet-4-20250514"
    judge_model: str = "claude-sonnet-4-20250514"
    image_generator: str = "midjourney-v6"
    video_generator: str = "runway-gen4"
    run_mode: str = "creative"
    retry_policy: str = "production_selective"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "initialized"

    # ─── Phase 1: Sourcing ───
    sourced_records: List[SourceRecord] = []
    filtered_records: List[SourceRecord] = []
    evidence_decision: EvidenceDecision = EvidenceDecision.SUFFICIENT
    synthetic_records: List[SourceRecord] = []
    trend_narratives: List[str] = []
    evidence_hash: Optional[str] = None
    narrative_hash: Optional[str] = None

    # ─── Phase 2: Generation ───
    assets: Dict[str, AssetOutput] = {}

    # ─── Phase 3: Scoring ───
    scores: Dict[str, AssetScore] = {}
    campaign_coherence: Optional[CampaignCoherence] = None
    failure_diagnosis: Optional[str] = None

    # ─── Iteration Control ───
    iteration_counts: Dict[str, int] = {
        "ads": 0, "video": 0, "image": 0, "blog": 0
    }
    human_review_queue: List[str] = []

    # ─── Observability ───
    audit_log: List[AuditEntry] = []

    # ─── Phase 4: Output ───
    final_bundle: Dict[str, Any] = {}
    campaign_metadata: Dict[str, Any] = {}