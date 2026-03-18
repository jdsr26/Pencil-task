"""
Pipeline Tracer
===============
Higher-level observability. Calculates pipeline-level metrics
from the audit log.
"""

from typing import Dict, Any, List


def calculate_pipeline_metrics(audit_log: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary metrics from the audit log."""
    total_llm_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_latency_ms = 0
    nodes_executed = set()

    for entry in audit_log:
        nodes_executed.add(entry.get("node", ""))
        if entry.get("action") == "llm_call":
            total_llm_calls += 1
            meta = entry.get("metadata", {})
            total_input_tokens += meta.get("input_tokens", 0)
            total_output_tokens += meta.get("output_tokens", 0)
        latency = entry.get("latency_ms")
        if latency:
            total_latency_ms += latency

    # Cost estimate (Claude Sonnet 4 pricing)
    input_cost = (total_input_tokens / 1_000_000) * 3.0
    output_cost = (total_output_tokens / 1_000_000) * 15.0
    total_cost = input_cost + output_cost

    return {
        "total_llm_calls": total_llm_calls,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "estimated_cost_usd": round(total_cost, 4),
        "total_latency_ms": total_latency_ms,
        "nodes_executed": list(nodes_executed),
        "audit_entries": len(audit_log),
    }
