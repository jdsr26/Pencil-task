

# Dr. Jart+ AI Content Pipeline — Complete System Architecture
 
## For: Pencil Prompt Engineer Assessment
## Author: J Dhana Santhosh Reddy
## Date: March 2026
 
---
 
# 1. SYSTEM OVERVIEW
 
## What This System Does
 
An inspectable, self-correcting creative workflow engine that controls LLM behavior through grounding, structured generation, measurable evaluation, and targeted regeneration. Every final output is anchored to one product, linked to source-backed evidence, validated against a product truth registry, and auditable end-to-end.

The current implementation supports multiple anchor products, multiple trigger types, selectable prompt-generation and judge models, and selectable image/video target generators.
 
## What This System Is NOT
 
Not a chatbot wrapper. Not a "call GPT and hope for the best" tool. It is an engineered machine where LLM behavior is constrained, measured, and corrected.

It is also not a naive “one prompt works for every model” design. The system now separates canonical prompt intent from model-specific rendering and provider-specific execution.
 
## The Pipeline Flow
 
```
┌──────────────┐
│   TRIGGER    │  What initiates a content cycle
└──────┬───────┘
       ▼
┌──────────────┐
│ INIT & LOAD  │  Load product truth, brand voice, configs
└──────┬───────┘
       ▼
┌──────────────┐
│SOURCE COLLECT│  Load + filter external trend data
└──────┬───────┘
       ▼
┌──────────────┐
│  EVIDENCE    │  Is there enough data to generate?
│  SUFFICIENCY │──── NO (poor) ──→ STOP + escalate
│    CHECK     │──── WEAK ──→ add synthetic supplements
└──────┬───────┘
       │ YES
       ▼
┌──────────────┐
│  NARRATIVE   │  Distill top 3 trend narratives
│  SYNTHESIS   │
└──────┬───────┘
       ▼
┌──────────────┐
│    ASSET     │  4 agents generate: ads, video, image, blog
│  GENERATION  │◄──── RETRY (with targeted feedback)
└──────┬───────┘         ▲
       ▼                 │
┌──────────────┐         │
│DETERMINISTIC │  Rule-based checks (char count, format)
│   CHECKS     │         │
└──────┬───────┘         │
       ▼                 │
┌──────────────┐         │
│  LLM JUDGE   │  Subjective scoring (brand, tone, trend)
└──────┬───────┘         │
       ▼                 │
┌──────────────┐         │
│  CAMPAIGN    │  Cross-asset coherence check
│   JUDGE      │         │
└──────┬───────┘         │
       ▼                 │
┌──────────────┐         │
│    ROUTE     │─ FAIL ──┘
│   DECISION   │─ PATTERN FAIL ──→ upstream diagnosis
│              │─ MAX RETRIES ──→ human review queue
└──────┬───────┘
       │ ALL PASS
       ▼
┌──────────────┐
│   PACKAGE    │  Bundle deliverables + metadata + audit trail
└──────────────┘
```

## Adapter Architecture

The system now has three adapter layers:

1. Prompt adapters
- Convert canonical prompt spec into Claude, GPT-family, or Gemini-family prompt formatting

2. Provider adapters
- Route runtime execution through Anthropic, OpenAI-style, or Gemini-style clients

3. Generator adapters
- Shape image/video instructions for Midjourney, GPT Image, Flux, Runway, Veo, or Sora

This is important because it keeps the core workflow stable while allowing controlled experimentation with rendering and model targets.

## Tech Stack
 
| Layer | Technology | Why |
|-------|-----------|-----|
| Orchestration | LangGraph | Graph-based state machine with conditional edges for retry loops |
| LLM Runtime | Claude Sonnet 4 by default, with provider abstraction | Strong default plus portability path |
| Backend API | FastAPI | Async, auto-documented (Pydantic + OpenAPI), Python-native |
| Data Validation | Pydantic v2 | Type-safe state, LLM output parsing, config validation |
| Frontend | React (Vite) | Interactive dashboard for pipeline inspection |
| Config | YAML files | Human-readable, version-controlled pipeline configuration |

## Config Surface

The implemented config surface now includes:

- `config/product_truth.yaml` for multi-product truth data
- `config/triggers.yaml` for trigger-specific sourcing emphasis
- `config/sources.yaml` for filtering logic, product keyword profiles, and YAML source packs
- `config/brand_voice.yaml` for brand voice and few-shot behavior
- `config/scoring_rubric.yaml` for deterministic and judge scoring rules

## UI Control Surface

The frontend exposes:

- Anchor product selection
- Campaign trigger selection
- A collapsible `Model Settings` menu with:
  - Prompt Generation Model
  - Judge Model
  - Image Generator
  - Video Generator
  - Run Mode (`creative` / `demo`)
  - Retry Policy (`production_selective` / `benchmark_none` / `benchmark_rerun_all`)

The sidebar is scrollable so the full control surface remains usable on smaller screens.

## Reproducibility and Run-To-Run Variance

### Why Two Runs With The Same UI Settings Can Produce Different Bundles

With `run_mode: creative`, all LLM calls use temperature > 0. Temperature > 0 means sampling — the model draws from a probability distribution on every token. Even with identical prompts and identical settings, each run produces a new sample. The pipeline propagates this variance:

1. **Narrative synthesis** — same evidence, different narrative text (traceable via `narrative_hash`)
2. **Asset generation** — different narratives produce different prompts (traceable via per-node `prompt_hash` in the audit log)
3. **Scoring** — different content scores differently, changing pass/fail outcomes
4. **Route decision** — different pass/fail outcomes trigger different retry paths

This is intentional. Zero-temperature outputs are mechanically repetitive and lower quality in production. The hashes make variance observable and debuggable rather than opaque.

### How To Get Deterministic Outputs

Set `run_mode: demo`. This collapses all temperatures to 0.0 across every node (narrative: 0.0, all assets: 0.0, judge: 0.0). Two demo-mode runs with the same inputs will produce identical outputs.

### Tracing Divergence Between Runs

Compare audit files side by side:

| Hash field | Location | What it tells you |
|---|---|---|
| `evidence_hash` | `source_collect` node metadata | Same hash = same filtered source records |
| `narrative_hash` | `narrative_synth` node metadata | Same hash = divergence did not start at narrative |
| `prompt_hash` | Every LLM node entry | Different hash = different prompt content fed to the model |
| `retry_feedback_hash` | `route_decision` node output | Different hash = different failure feedback on retry |
| `resolved_model_versions` | Campaign metadata | Confirms exact model checkpoint used, not just alias |
 