# Dr. Jart+ AI Content Pipeline

An inspectable, self-correcting creative workflow engine for generating brand-safe marketing assets.

Built as a Prompt Engineer assessment for [Pencil](https://trypencil.com) (The Brandtech Group).

## What This System Does

Generates a complete campaign bundle (Google Ads, video prompt, image prompt, blog post) for a selected Dr. Jart+ anchor product, grounded in trend data, validated against product truth, and scored through a hybrid evaluation system.

**Supported Anchor Products:** Ceramidin™ Cream, Cicapair™ Treatment, Dermask™ Micro Jet  
**Supported Triggers:** scheduled, seasonal spring, seasonal winter, viral trend, competitor launch, manual  
**Default Prompt Generation Model:** Claude Sonnet 4  
**Default Generators:** Midjourney v6 (image), Runway Gen-4 (video)

## What Is New In This Version

This repository now supports:

- Multi-product campaign runs driven by YAML product truth
- Multi-trigger sourcing behavior driven by YAML trigger config
- Canonical prompt specification plus model-specific prompt adapters
- Provider abstraction for Anthropic, OpenAI-family, and Gemini-family models
- Generator adapters for image and video targets
- UI dropdowns for prompt-generation model, judge model, image generator, and video generator
- YAML-backed source packs that make non-default products and triggers functional in the demo

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

## System Model

The architecture has three control layers:

1. Canonical workflow layer
- Trigger selection
- Anchor product selection
- Sourcing, evidence gating, narrative synthesis, asset generation, scoring, routing, packaging

2. Adapter layer
- Prompt adapters: Claude, GPT-family, Gemini-family
- Provider adapters: Anthropic, OpenAI-style, Gemini-style runtime calls
- Generator adapters: Midjourney / GPT Image / Flux and Runway / Veo / Sora instruction shaping

3. Guardrail layer
- Product truth registry
- Brand voice config
- Deterministic scoring
- LLM judge
- Campaign coherence checks
- Retry routing and upstream failure diagnosis

This means model choice is flexible without allowing users to bypass grounding, brand constraints, evaluation, or output contracts.

## Key Design Decisions

1. **Hybrid Scoring**: Rule-based checks (format, char counts, keywords) + LLM judge (brand alignment, trend connection). Knowing when NOT to use an LLM is as important as knowing when to use one.

2. **Product Truth Registry**: Anti-hallucination layer. The system can only make claims that exist in `config/product_truth.yaml` or the source registry.

3. **Prompt Spec + Adapter Separation**: The workflow produces canonical prompt intent; model adapters format that intent for the selected LLM family. This keeps portability without losing control.

4. **Upstream Fault Diagnosis**: If 3+ assets fail on the same dimension, the system diagnoses the root cause (weak narratives, drifting brand voice, bad templates) instead of blindly retrying.

5. **Complete Audit Trail**: Every LLM call, every scoring decision, every routing choice is logged with full input/output snapshots.

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
# Edit .env and add the API key(s) for the models you want to use
# ANTHROPIC_API_KEY is required for Claude models
# OPENAI_API_KEY is required for GPT-family models
# GEMINI_API_KEY is required for Gemini-family models

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
config/          — YAML configs (product truth, brand voice, scoring rubric, triggers, sources)
data/sourced/    — Pre-curated trend data used as base evidence
backend/
  prompting/     — Canonical prompt spec + model/generator adapters
  llm/           — Provider abstraction layer
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

## UI Controls

The left sidebar now supports:

- Anchor product selection
- Campaign trigger selection
- A collapsible `Model Settings` menu containing:
  - Prompt Generation Model
  - Judge Model
  - Image Generator
  - Video Generator

These options are loaded from the backend via `/api/models`, so the UI reflects the current backend allowlist.

## Pencil Platform Alignment

This system maps to Pencil\'s agent architecture:
- Each agent has **Instructions** (system prompt), **Knowledge** (context injection), **Tools** (validators, search)
- Agent chaining mirrors Pencil\'s conversation-based agent workflows
- Model aggregation: supports model selection through provider and prompt adapters
- Predictive scoring: maps to Pencil\'s creative scoring feature
- Brand controls: centralized in YAML configs, not hardcoded

## Verification

Targeted regression and smoke tests cover:

- prompt adapter selection and rendering
- provider-family resolution
- model and generator validation
- trigger/product-aware source coverage
- graph-level smoke runs for non-default trigger/product combinations

Run them with:

```bash
uv run --python .venv/bin/python -m pytest -q tests/test_pipeline_smoke.py tests/test_source_collect_coverage.py tests/test_model_selection.py tests/test_provider_resolution.py tests/test_prompt_adapters.py tests/test_state_validation.py tests/test_deterministic_scoring.py
```

## Author

J Dhana Santhosh Reddy — Prompt Engineer Candidate, March 2026
