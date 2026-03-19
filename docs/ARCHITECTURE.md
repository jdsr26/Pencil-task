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
