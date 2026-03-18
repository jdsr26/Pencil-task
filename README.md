# Dr. Jart+ AI Content Pipeline

An inspectable, self-correcting creative workflow engine for generating brand-safe marketing assets.

Built as a Prompt Engineer assessment for [Pencil](https://trypencil.com) (The Brandtech Group).

## What This System Does

Generates a complete campaign bundle (Google Ads, video prompt, image prompt, blog post) for Dr. Jart+ Ceramidin™ Cream, grounded in real trend data, validated against brand truth, and scored through a hybrid evaluation system.

**Anchor Product:** Ceramidin™ Skin Barrier Moisturizing Cream  
**Trend Narrative:** Barrier Repair + Skin Longevity (2026)  
**Core Model:** Claude Sonnet 4 (Anthropic)

## Architecture

```
source_collect → evidence_check → narrative_synth → generate_assets
                                                          ↓
                                                  score_deterministic
                                                          ↓
                                                   score_llm_judge
                                                          ↓
package ← route_decision ← score_campaign (cross-asset coherence)
               ↑
               └──── RETRY (with targeted feedback) ─┘
```

**9 pipeline nodes** orchestrated by LangGraph with conditional routing for self-correction.

## Key Design Decisions

1. **Hybrid Scoring**: Rule-based checks (format, char counts, keywords) + LLM judge (brand alignment, trend connection). Knowing when NOT to use an LLM is as important as knowing when to use one.

2. **Product Truth Registry**: Anti-hallucination layer. The system can only make claims that exist in `config/product_truth.yaml` or the source registry.

3. **Upstream Fault Diagnosis**: If 3+ assets fail on the same dimension, the system diagnoses the root cause (weak narratives, drifting brand voice, bad templates) instead of blindly retrying.

4. **Complete Audit Trail**: Every LLM call, every scoring decision, every routing choice is logged with full input/output snapshots.

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd Pencil-task

# Install dependencies
pip install -r requirements.txt
# OR with uv:
uv sync

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the pipeline (CLI)
python -m backend.pipeline.graph

# Run the API server
python -m backend.main
# Then open http://localhost:8000/docs for API docs

# Run the frontend (separate terminal)
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## Project Structure

```
config/          — YAML configs (product truth, brand voice, scoring rubric)
data/sourced/    — Pre-curated trend data (8 real research records)
backend/
  pipeline/
    state.py     — Pydantic state schema (the foundation)
    graph.py     — LangGraph wiring (8 nodes + 2 conditional edges)
    nodes/       — Pipeline nodes (source, generate, score, route, package)
    tools/       — Deterministic utilities (char counter, format validator, claim linker)
  agents/        — LLM agents (base + 4 creative + 1 judge)
  registries/    — Ground truth stores (product truth + source registry)
  observability/ — Audit trail + pipeline metrics
  api/           — FastAPI routes
frontend/        — React dashboard for pipeline inspection
```

## Pencil Platform Alignment

This system maps to Pencil\'s agent architecture:
- Each agent has **Instructions** (system prompt), **Knowledge** (context injection), **Tools** (validators, search)
- Agent chaining mirrors Pencil\'s conversation-based agent workflows
- Model aggregation: designed for Claude Sonnet 4 with fallback support
- Predictive scoring: maps to Pencil\'s creative scoring feature
- Brand controls: centralized in YAML configs, not hardcoded

## Author

J Dhana Santhosh Reddy — Prompt Engineer Candidate, March 2026
