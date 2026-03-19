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

## Why Two Run Modes (Creative vs Demo) Instead Of One Fixed Temperature?
Creative mode uses low nonzero temperatures (narrative: 0.2, assets: 0.25–0.3, judge: 0.1). Pure 0.0 across the board makes outputs mechanically repetitive — the same sentence structures, the same phrasing, the same hook every run. That hurts quality in production. Demo mode uses 0.0 everywhere and is designed for controlled comparisons, benchmarking, and debugging — not for production campaigns.

## Why Do Two Creative-Mode Runs Produce Different Bundles?
This is expected and intentional. Temperature > 0 means the model samples from a probability distribution on every token. Even with identical prompts and identical settings, each run is a new sample. The narrative synthesis node produces slightly different narratives, which changes downstream asset prompt hashes, which changes asset content, which changes scores. This is not a bug — it is the creative variance that makes the output non-robotic. The `evidence_hash` and `narrative_hash` in each audit file let you trace exactly where the two runs diverged.

## Why Log evidence_hash and narrative_hash?
Hashes fingerprint the inputs to each stochastic stage. If two runs share the same `evidence_hash` but have different `narrative_hash` values, the divergence happened inside narrative synthesis. If they share the same `narrative_hash` but produce different assets, the divergence happened inside asset generation. This makes run-to-run variance debuggable instead of opaque.

## Why Three Retry Policies?
`production_selective` retries only failing assets, preserving passed ones — correct for production where passed assets are expensive to regenerate. `benchmark_none` disables retries entirely — correct for benchmarking where you want a clean single-pass measurement. `benchmark_rerun_all` regenerates all assets on retry regardless of previous pass state — correct for reproducibility testing where you need to confirm scores are stable across full reruns, not just for individual failing assets.
