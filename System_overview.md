

# Dr. Jart+ AI Content Pipeline — Complete System Architecture
 
## For: Pencil Prompt Engineer Assessment
## Author: J Dhana Santhosh Reddy
## Date: March 2026
 
---
 
# 1. SYSTEM OVERVIEW
 
## What This System Does
 
An inspectable, self-correcting creative workflow engine that controls LLM behavior through grounding, structured generation, measurable evaluation, and targeted regeneration. Every final output is anchored to one product, linked to source-backed evidence, validated against a product truth registry, and auditable end-to-end.
 
## What This System Is NOT
 
Not a chatbot wrapper. Not a "call GPT and hope for the best" tool. It is an engineered machine where LLM behavior is constrained, measured, and corrected.
 
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

## Tech Stack
 
| Layer | Technology | Why |
|-------|-----------|-----|
| Orchestration | LangGraph | Graph-based state machine with conditional edges for retry loops |
| LLM | Claude Sonnet 4 (Anthropic) | Strongest instruction adherence on multi-constraint prompts |
| Backend API | FastAPI | Async, auto-documented (Pydantic + OpenAPI), Python-native |
| Data Validation | Pydantic v2 | Type-safe state, LLM output parsing, config validation |
| Frontend | React (Vite) | Interactive dashboard for pipeline inspection |
| Config | YAML files | Human-readable, version-controlled pipeline configuration |
 