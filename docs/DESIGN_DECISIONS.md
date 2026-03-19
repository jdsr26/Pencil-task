# Design Decisions

## Why Ceramidin™?
Dr. Jart+ #1 bestseller + ceramide barrier repair is the dominant 2026 skincare trend.
Trend-product alignment creates rich sourcing data and makes every downstream asset stronger.

## Why Add More Anchor Products?
The assessment started with Ceramidin as the strongest default demo path, but a product system that exposes multiple anchor products should make those options operational. YAML-backed source packs and product profiles now make Cicapair and Dermask usable paths instead of placeholder UI states.

## Why Claude Sonnet 4 As Default?
Strongest instruction adherence on multi-constraint prompts (500+ word brand voice guide + format specs + trend context). It remains the recommended default, but the system now separates canonical prompt intent from model-specific rendering and provider execution.

## Why A Canonical Prompt Spec + Adapter Layer?
One prompt should not be treated as universally optimal across all model families. The canonical spec captures intent; the adapter layer controls formatting. This gives portability, A/B-testability, and vendor flexibility without letting model choice bypass grounding or brand controls.

## Why Separate Prompt Adapters From Provider Adapters?
Prompt shape and transport/runtime are different concerns. A Claude-style sectioned prompt rendered for GPT via an OpenAI transport is still a prompt-formatting decision, not a networking one. Splitting these layers keeps the system easier to reason about and extend.

## Why Hybrid Scoring?
Character counting doesn\'t need an LLM. Brand alignment does. Using an LLM to count characters would be slower, more expensive, and less reliable. Knowing when NOT to use an LLM is engineering judgment.

## Why 40% Brand Alignment Weight?
Off-brand content is the highest-risk failure mode for enterprise clients. A format error is fixable — a tone-deaf ad damages brand trust.

## Why Upstream Fault Diagnosis?
If 3+ assets fail on the same dimension, retrying individual assets won\'t help. The problem is upstream (weak data, drifting voice, bad templates). The system tells you WHERE to look.

## Why YAML Source Packs?
The UI and API allow multiple triggers and anchor products. If the evidence layer only had strong coverage for one path, those options would be misleading. YAML source packs are a pragmatic demo-safe way to make those combinations functional without pretending there is a full live multi-source ingestion layer.

## Why LangGraph?
Graph-based orchestration with conditional edges supports the retry loop natively. route_decision can send control back to generate_assets without writing explicit loop logic.

## Why Pydantic?
Type-safe state at every boundary. If the LLM returns malformed JSON, Pydantic catches it immediately — not 5 nodes later when something silently breaks.

## Why Pre-Curated Data?
Live scraping is impressive but fragile during demos. Pre-curated data with scraper code available shows engineering judgment — reliable demo + the capability exists.

## Why A Collapsible Model Settings Menu In The UI?
There are now four related controls: prompt-generation model, judge model, image generator, and video generator. Grouping them under one expandable menu reduces sidebar clutter while still making the system's configurability visible during demos and interviews.
