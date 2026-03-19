"""
Audit Log Utility
=================
Creates structured AuditEntry objects for pipeline observability.
Every node and agent calls this to record what happened.

The entries are appended to PipelineState.audit_log,
which the frontend renders as an expandable timeline.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.pipeline.state import AuditEntry


def create_audit_entry(
    node: str,
    action: str,
    input_snapshot: Dict[str, Any] = None,
    output_snapshot: Dict[str, Any] = None,
    model_used: Optional[str] = None,
    prompt_hash: Optional[str] = None,
    latency_ms: Optional[int] = None,
    metadata: Dict[str, Any] = None,
) -> AuditEntry:
    """
    Create a structured audit log entry.
    
    Args:
        node: Which pipeline node (e.g., "generate_assets.ads")
        action: What happened (e.g., "llm_call", "deterministic_check")
        input_snapshot: What went INTO this step
        output_snapshot: What came OUT of this step
        model_used: Which LLM model (if applicable)
        prompt_hash: Hash of the prompt used (for version tracking)
        latency_ms: How long this step took
        metadata: Any extra context (retry count, trigger, etc.)
    
    Returns:
        AuditEntry ready to append to pipeline state
    """
    return AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        node=node,
        action=action,
        input_snapshot=input_snapshot or {},
        output_snapshot=output_snapshot or {},
        model_used=model_used,
        prompt_hash=prompt_hash,
        latency_ms=latency_ms,
        metadata=metadata or {},
    )


def hash_prompt(prompt: str) -> str:
    """
    Create a short hash of a prompt string.
    Same prompt = same hash. Used to detect prompt changes between retries.
    
    Returns first 12 chars of SHA-256 hash.
    """
    return hashlib.sha256(prompt.encode()).hexdigest()[:12]


def hash_payload(payload: Any) -> str:
    """
    Create a short stable hash for any JSON-serializable payload.
    Useful for evidence fingerprints, narrative fingerprints, and retry payloads.
    """
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:12]


def truncate_for_snapshot(text: str, max_length: int = 500) -> str:
    """
    Truncate long text for audit snapshots.
    Full content is stored in the asset — snapshots are for quick inspection.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"... [truncated, {len(text)} chars total]"