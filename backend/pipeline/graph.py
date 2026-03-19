"""
Pipeline Graph
==============
Wires all pipeline nodes into a LangGraph state machine.

This is the ORCHESTRATION BRAIN. It defines:
  - Which nodes exist
  - What order they execute in
  - When to loop back (retry on failure)
  - When to stop (all pass, pattern failure, max retries)

The graph has one conditional edge — after route_decision,
the pipeline either loops back to generate_assets with feedback
injected, or proceeds to package (with one of four outcomes).

Flow:
  source_collect → evidence_check → [STOP if poor evidence]
       ↓
  narrative_synth → generate_assets → score_deterministic
       ↓                    ↑                ↓
  ┌──────────────────── route_decision ← score_campaign ← score_llm_judge
  │                          │
  │         ┌────────────────┼──────────────────────────┐
  │         ↓                ↓                          ↓
  │       RETRY           PACKAGE                    PACKAGE
  │    (individual       (all_passed /            (pattern_failure /
  │     failures)       coherence_failure)        max_retries_exhausted)
  │       + feedback
  └───────────┘
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from backend.pipeline.nodes.source_collect import source_collect
from backend.pipeline.nodes.evidence_check import evidence_check
from backend.pipeline.nodes.narrative_synth import narrative_synth
from backend.pipeline.nodes.generate_assets import generate_assets
from backend.pipeline.nodes.score_deterministic import score_deterministic
from backend.pipeline.nodes.score_llm_judge import score_llm_judge
from backend.pipeline.nodes.score_campaign import score_campaign   # NEW
from backend.pipeline.nodes.route_decision import route_decision
from backend.pipeline.nodes.package import package



# ─────────────────────────────────────────────
# State Schema for LangGraph
# ─────────────────────────────────────────────
# LangGraph uses a dict-based state. We define the schema
# as a TypedDict so the graph knows what keys exist.
# Pydantic validation happens INSIDE each node, not at the graph level.

from typing import TypedDict, List, Optional


class GraphState(TypedDict, total=False):
    """
    LangGraph state schema.

    total=False means all keys are optional — nodes return
    partial updates, not the full state every time.
    LangGraph merges each node's return into the accumulated state.
    """
    # Run metadata
    run_id: str
    trigger: str
    product: str          # Selected anchor product key
    generation_model: str
    judge_model: str
    image_generator: str
    video_generator: str
    started_at: str
    completed_at: str
    status: str

    # Phase 1: Sourcing
    sourced_records: list
    filtered_records: list
    evidence_decision: str
    synthetic_records: list
    trend_narratives: list

    # Phase 2: Generation
    assets: dict

    # Phase 3: Scoring
    scores: dict
    campaign_coherence: dict
    failure_diagnosis: str

    # Iteration control
    iteration_counts: dict
    human_review_queue: list

    # Routing
    next_node: str

    # Observability
    audit_log: list

    # Phase 4: Output
    final_bundle: dict
    campaign_metadata: dict


# ─────────────────────────────────────────────
# Conditional Edge: Evidence Gate
# ─────────────────────────────────────────────

def should_continue_after_evidence(state: Dict[str, Any]) -> str:
    """
    After evidence_check, decide whether to proceed or stop.
    
    SUFFICIENT or WEAK → continue to narrative_synth
    POOR → stop the pipeline (go directly to package with empty assets)
    """
    decision = state.get("evidence_decision", "sufficient")
    
    if decision == "poor":
        return "package_early"
    return "narrative_synth"


# ─────────────────────────────────────────────
# Conditional Edge: Route Decision
# ─────────────────────────────────────────────

def should_retry_or_package(state: Dict[str, Any]) -> str:
    """
    After route_decision, decide whether to retry or package.

    This is THE key conditional edge — the self-correction loop.

    route_decision sets state["next_node"] based on five outcomes:
      - "generate_assets" (decision=retry) — individual assets failed,
        retries remain; feedback injected into assets for next attempt
      - "package" (decision=all_passed) — all 4 assets passed individual
        scoring AND campaign coherence check; happy path
      - "package" (decision=coherence_failure) — all assets passed
        individually but cross-asset coherence check failed; diagnosed
        and sent to package with coherence issues flagged
      - "package" (decision=pattern_failure) — 3+ assets failed on the
        same scoring dimension; upstream fault diagnosed, retry skipped
      - "package" (decision=max_retries_exhausted) — failing assets
        exhausted max retries; sent to human review queue
    """
    next_node = state.get("next_node", "package")
    return next_node


# ─────────────────────────────────────────────
# Graph Construction
# ─────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Construct the complete pipeline graph.
    
    Returns a compiled LangGraph that can be invoked with an initial state.
    
    Node execution order (happy path):
      1. source_collect
      2. evidence_check
      3. narrative_synth
      4. generate_assets
      5. score_deterministic
      6. score_llm_judge
      7. score_campaign      (cross-asset coherence gate)
      8. route_decision
      9. package
    
    With retry loop:
      ... → route_decision → generate_assets → score_deterministic →
      score_llm_judge → route_decision → ... (up to 3 cycles)
    """
    # Create the graph with our state schema
    graph = StateGraph(GraphState)

    # ─── ADD NODES ───
    # Each node is a function that takes state dict and returns partial update
    graph.add_node("source_collect", source_collect)
    graph.add_node("evidence_check", evidence_check)
    graph.add_node("narrative_synth", narrative_synth)
    graph.add_node("generate_assets", generate_assets)
    graph.add_node("score_deterministic", score_deterministic)
    graph.add_node("score_llm_judge", score_llm_judge)
    graph.add_node("score_campaign", score_campaign)
    graph.add_node("route_decision", route_decision)
    graph.add_node("package", package)

    # ─── SET ENTRY POINT ───
    graph.set_entry_point("source_collect")

    # ─── ADD EDGES (linear flow) ───
    # source_collect → evidence_check (always)
    graph.add_edge("source_collect", "evidence_check")

    # evidence_check → conditional: narrative_synth OR package_early
    graph.add_conditional_edges(
        "evidence_check",
        should_continue_after_evidence,
        {
            "narrative_synth": "narrative_synth",
            "package_early": "package",
        },
    )

    # narrative_synth → generate_assets (always)
    graph.add_edge("narrative_synth", "generate_assets")

    # generate_assets → score_deterministic (always)
    graph.add_edge("generate_assets", "score_deterministic")

    # score_deterministic → score_llm_judge (always)
    graph.add_edge("score_deterministic", "score_llm_judge")

    # score_llm_judge → score_campaign (always) — Tier 3: cross-asset coherence
    graph.add_edge("score_llm_judge", "score_campaign")

    # score_campaign → route_decision (always)
    graph.add_edge("score_campaign", "route_decision")

    # route_decision → conditional: generate_assets (retry) OR package (done)
    graph.add_conditional_edges(
        "route_decision",
        should_retry_or_package,
        {
            "generate_assets": "generate_assets",
            "package": "package",
        },
    )

    # package → END (always)
    graph.add_edge("package", END)

    # ─── COMPILE ───
    compiled = graph.compile()

    return compiled


# ─────────────────────────────────────────────
# Pipeline Runner
# ─────────────────────────────────────────────

def create_initial_state(
  trigger: str = "manual",
  product: str = "ceramidin_cream",
  generation_model: str = "claude-sonnet-4-20250514",
  judge_model: str = "claude-sonnet-4-20250514",
  image_generator: str = "midjourney-v6",
  video_generator: str = "runway-gen4",
) -> GraphState:
    """
    Create the initial state for a pipeline run.

    This is what gets passed to graph.invoke().
    All fields start empty/default — each node populates its section.
    """
    return {
        "run_id": str(uuid.uuid4())[:8],
        "trigger": trigger,
        "product": product,
        "generation_model": generation_model,
        "judge_model": judge_model,
        "image_generator": image_generator,
        "video_generator": video_generator,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "initialized",
        "sourced_records": [],
        "filtered_records": [],
        "evidence_decision": "sufficient",
        "synthetic_records": [],
        "trend_narratives": [],
        "assets": {},
        "scores": {},
        "failure_diagnosis": None,
        "iteration_counts": {"ads": 0, "video": 0, "image": 0, "blog": 0},
        "human_review_queue": [],
        "next_node": "",
        "audit_log": [],
        "final_bundle": {},
        "campaign_metadata": {},
    }


def run_pipeline(
  trigger: str = "manual",
  product: str = "ceramidin_cream",
  generation_model: str = "claude-sonnet-4-20250514",
  judge_model: str = "claude-sonnet-4-20250514",
  image_generator: str = "midjourney-v6",
  video_generator: str = "runway-gen4",
) -> Dict[str, Any]:
    """
    Execute the complete pipeline.
    
    This is the top-level function that:
      1. Builds the graph
      2. Creates initial state
      3. Invokes the graph
      4. Returns the final state
    
    Usage:
        result = run_pipeline(trigger="seasonal_spring")
        print(result["campaign_metadata"])
        print(result["final_bundle"])
        print(result["audit_log"])
    
    Args:
        trigger: What initiated this run (from triggers.yaml)
    
    Returns:
        Complete final pipeline state
    """
    # Build the graph
    graph = build_graph()

    # Create initial state
    initial_state = create_initial_state(
      trigger=trigger,
      product=product,
      generation_model=generation_model,
      judge_model=judge_model,
      image_generator=image_generator,
      video_generator=video_generator,
    )

    # Run the pipeline
    print(f"\n{'='*60}")
    print(f"🚀 Starting pipeline run: {initial_state['run_id']}")
    print(f"   Trigger: {trigger}")
    print(f"   Generation model: {generation_model}")
    print(f"   Judge model: {judge_model}")
    print(f"   Image generator: {image_generator}")
    print(f"   Video generator: {video_generator}")
    print(f"   Started: {initial_state['started_at']}")
    print(f"{'='*60}\n")

    # Invoke the graph — LangGraph handles all the routing
    final_state = graph.invoke(initial_state)

    # Print summary
    metadata = final_state.get("campaign_metadata", {})
    print(f"\n{'='*60}")
    print(f"✅ Pipeline complete: {metadata.get('status', 'unknown')}")
    print(f"   Assets passed: {metadata.get('assets_passed', 0)}/4")
    print(f"   Total iterations: {metadata.get('total_iterations', 0)}")
    print(f"   Human review: {metadata.get('assets_in_human_review', 0)}")
    print(f"   Audit entries: {metadata.get('audit_log_entries', 0)}")
    if metadata.get("failure_diagnosis"):
        print(f"   ⚠️ Diagnosis: {metadata['failure_diagnosis'][:100]}")
    print(f"{'='*60}\n")

    return final_state


# ─────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run the pipeline from command line:
        uv run python -m backend.pipeline.graph
    """
    import json
    import sys

    trigger = sys.argv[1] if len(sys.argv) > 1 else "seasonal_spring"
    
    result = run_pipeline(trigger=trigger)

    # Save results
    output_path = f"data/outputs/run_{result['run_id']}.json"
    
    import os
    os.makedirs("data/outputs", exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump({
            "campaign_metadata": result.get("campaign_metadata", {}),
            "final_bundle": result.get("final_bundle", {}),
            "scores": result.get("scores", {}),
            "trend_narratives": result.get("trend_narratives", []),
            "audit_log": result.get("audit_log", []),
        }, f, indent=2, default=str)

    print(f"📁 Results saved to: {output_path}")