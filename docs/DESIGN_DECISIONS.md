# Design Decisions

## Why Ceramidin™?
Dr. Jart+ #1 bestseller + ceramide barrier repair is the dominant 2026 skincare trend.
Trend-product alignment creates rich sourcing data and makes every downstream asset stronger.

## Why Claude Sonnet 4?
Strongest instruction adherence on multi-constraint prompts (500+ word brand voice guide + format specs + trend context).

## Why Hybrid Scoring?
Character counting doesn\'t need an LLM. Brand alignment does. Using an LLM to count characters would be slower, more expensive, and less reliable. Knowing when NOT to use an LLM is engineering judgment.

## Why 40% Brand Alignment Weight?
Off-brand content is the highest-risk failure mode for enterprise clients. A format error is fixable — a tone-deaf ad damages brand trust.

## Why Upstream Fault Diagnosis?
If 3+ assets fail on the same dimension, retrying individual assets won\'t help. The problem is upstream (weak data, drifting voice, bad templates). The system tells you WHERE to look.

## Why LangGraph?
Graph-based orchestration with conditional edges supports the retry loop natively. route_decision can send control back to generate_assets without writing explicit loop logic.

## Why Pydantic?
Type-safe state at every boundary. If the LLM returns malformed JSON, Pydantic catches it immediately — not 5 nodes later when something silently breaks.

## Why Pre-Curated Data?
Live scraping is impressive but fragile during demos. Pre-curated data with scraper code available shows engineering judgment — reliable demo + the capability exists.
