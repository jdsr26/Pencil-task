# Architecture Overview

See the complete architecture document for detailed specifications of every component.

## Implemented Scope

The current implementation is no longer single-product or single-trigger in practice.
It supports:

- Multiple anchor products selected at run time
- Multiple campaign triggers selected at run time
- Multiple prompt-generation model families through adapters
- Multiple image/video generator targets through adapter guidance
- YAML-backed source packs that supplement the base sourced dataset

## Pipeline Flow

1. **Source Collect** — Load base sourced records plus YAML source packs, then validate and filter using selected product + trigger
2. **Evidence Check** — Sufficiency gate (sufficient/weak/poor)
3. **Narrative Synth** — Distill 3 trend narratives from sourced data for the selected anchor product
4. **Generate Assets** — 4 creative agents (ads, video, image, blog)
5. **Score Deterministic** — Tier 1: rule-based format checks (instant, free)
6. **Score LLM Judge** — Tier 2: brand + trend alignment using selected judge model
7. **Route Decision** — Pass / retry with feedback / diagnose upstream / escalate
8. **Package** — Bundle deliverables + campaign metadata + audit trail

## Adapter Layers

### Prompt Adapter Layer

Canonical prompt intent is represented separately from vendor-specific formatting.

- Canonical spec: `backend/prompting/spec.py`
- Prompt adapters: `backend/prompting/adapters.py`

This layer converts the same intent into:

- section-based prompts for Claude-family models
- tag-structured prompts for GPT-family models
- markdown-structured prompts for Gemini-family models

### Provider Adapter Layer

Runtime execution is abstracted behind provider adapters in `backend/llm/providers.py`.

Supported families:

- Anthropic / Claude
- OpenAI-style GPT-family
- Gemini

This is distinct from prompt formatting. Prompt rendering and runtime transport are two separate concerns.

### Generator Adapter Layer

Image and video assets use target-generator guidance adapters in `backend/prompting/generator_adapters.py`.

Image targets:

- Midjourney v6
- Flux 1.1 Pro
- GPT Image 1

Video targets:

- Runway Gen-4
- Google Veo 3
- Sora

The generation agents still return structured outputs that satisfy deterministic validators, while the wording is shaped toward the selected generator.

## Scoring Formula

```
composite = (deterministic × 0.25) + (brand_alignment × 0.40) + (trend_alignment × 0.35)
pass = composite >= 85
```

## Self-Correction Loop

Failed assets get targeted feedback injected into their retry prompt.
The feedback accumulates across iterations — by v3, the prompt includes
all corrections from v1 and v2 failures.

## Trigger and Product Awareness

### Trigger Config

`config/triggers.yaml` controls:

- sourcing window
- priority source categories
- messaging emphasis
- seasonal or event context

### Product Truth

`config/product_truth.yaml` controls:

- approved claims
- blocked claims and blocked language
- key ingredients
- competitor context

### Source Packs

`config/sources.yaml` now contains:

- product keyword profiles
- product-specific YAML source packs
- trigger-specific YAML source packs

This makes non-default products and triggers operational in the demo instead of only existing as UI options.

## Config-Driven Design

Change `config/product_truth.yaml` → changes what the system can claim.
Change `config/brand_voice.yaml` → changes how the system writes.
Change `config/scoring_rubric.yaml` → changes how quality is measured.
Change `config/triggers.yaml` → changes sourcing emphasis and campaign context.
Change `config/sources.yaml` → changes filtering behavior and YAML-backed evidence coverage.
No code changes needed to swap supported products, triggers, or allowed models.

## Reproducibility Controls

### Run Modes

| Mode | Narrative temp | Asset temps | Judge temp | Purpose |
|------|---------------|-------------|------------|---------|
| `creative` | 0.2 | ads/video/blog: 0.25, image: 0.3 | 0.1 | Production — low nonzero for quality variance |
| `demo` | 0.0 | 0.0 all | 0.0 | Controlled comparison, benchmarking, debugging |

### Retry Policies

| Policy | Behaviour |
|--------|-----------|
| `production_selective` | Retry only failing assets; preserve passed ones |
| `benchmark_none` | No retries; max_retries forced to 0 |
| `benchmark_rerun_all` | Retry regenerates all assets, ignoring previous pass state |

### Payload Hashes

Every run records stable SHA-256 fingerprints (12-char hex prefix) for the key stochastic boundaries:

- **`evidence_hash`** — fingerprint of the filtered source records fed into narrative synthesis (id, source_name, category, claims, tags). Same hash = same evidence input.
- **`narrative_hash`** — fingerprint of the 3 trend narratives produced. Same hash = same narrative, regardless of which run produced it.
- **`retry_feedback_hash`** — fingerprint of the feedback payload injected into each retry cycle.

These appear in the audit log entry for each node and in the final campaign metadata bundle.

### Resolved Model Versions

`resolved_model_versions` in campaign metadata is the sorted set of actual model IDs returned by provider API responses (e.g. `claude-sonnet-4-20250514`). This is distinct from the requested model alias — it pins the exact checkpoint used, not the alias that might resolve differently over time.

### Why Two Runs With The Same Settings Produce Different Bundles

With `run_mode: creative`, temperature > 0 means every LLM call samples from a distribution. The same prompt produces different tokens on each run. Narrative synthesis diverges first (same evidence_hash, different narrative_hash), then asset generation diverges (different prompt hashes downstream), then scores diverge. The hashes make this traceable: compare `evidence_hash` → `narrative_hash` → per-asset prompt hashes across two audit files to identify exactly which stage diverged.

To eliminate this: use `run_mode: demo`. All temperatures collapse to 0.0.
