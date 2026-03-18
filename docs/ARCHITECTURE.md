# Architecture Overview

See the complete architecture document for detailed specifications of every component.

## Pipeline Flow

1. **Source Collect** — Load 8 pre-curated trend records, validate, filter
2. **Evidence Check** — Sufficiency gate (sufficient/weak/poor)
3. **Narrative Synth** — Distill 3 trend narratives from sourced data
4. **Generate Assets** — 4 creative agents (ads, video, image, blog)
5. **Score Deterministic** — Tier 1: rule-based format checks (instant, free)
6. **Score LLM Judge** — Tier 2: brand + trend alignment (Claude Sonnet 4)
7. **Route Decision** — Pass / retry with feedback / diagnose upstream / escalate
8. **Package** — Bundle deliverables + campaign metadata + audit trail

## Scoring Formula

```
composite = (deterministic × 0.25) + (brand_alignment × 0.40) + (trend_alignment × 0.35)
pass = composite >= 85
```

## Self-Correction Loop

Failed assets get targeted feedback injected into their retry prompt.
The feedback accumulates across iterations — by v3, the prompt includes
all corrections from v1 and v2 failures.

## Config-Driven Design

Change `config/product_truth.yaml` → changes what the system can claim.
Change `config/brand_voice.yaml` → changes how the system writes.
Change `config/scoring_rubric.yaml` → changes how quality is measured.
No code changes needed to swap products or brands.
