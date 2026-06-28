# Sprint 4 Summary — LangGraph Pipeline Finalize

**Status**: Complete  
**Date**: 2026-06-28  
**Scope**: Phase 3 (Content Engine) — Pipeline finalization, API unification, testing

---

## Goal

Finalize the AI content pipeline — replace dual orchestration (manual + LangGraph) with a single LangGraph-driven pipeline, unify the API surface, freeze backend for frontend development.

## What Was Done

### 1. ContentState TypedDict → Pydantic BaseModel

- `backend/application/graph/state.py`: Migrated from `TypedDict` to Pydantic `BaseModel` with typed fields, defaults, and `Field(default_factory=...)` for mutable containers
- Added `revision_count: int = 0` for cycle-limiting in review routing

### 2. Error Propagation (all 9 nodes)

Every node wraps its logic in try/except, appending `{"step": <name>, "message": str(exc)}` to `state.errors`. Errors never crash the pipeline; they accumulate for downstream inspection.

### 3. Step Timing (all 9 nodes)

Each node records `{step_name: latency_ms}` into `state.step_timing`, enabling per-stage performance analysis.

### 4. Review Routing Fix

- `_route_from_review` returns `"approve"` → analytics, `"revise"` → writing (loop-back), `"reject"` → END
- Added `MAX_REVISIONS = 2` cap — prevents infinite loop when heuristic review rejects short drafts
- `"major_revision"` maps to `"revise"` (loop-back), `"approve"` is default

### 5. ContentEngine Orchestration Removed

- `services/content_engine/service.py`: Stripped `run_pipeline()` and `generate_draft()` — only `generate_ideas()` remains as a legacy wrapper
- Stage classes (`ContextAggregator`, `IdeaGenerator`, `DraftComposer`, `StyleRefiner`, `QualityGate`) kept as reusable logic, imported directly by API when needed

### 6. API Unification

- `POST /content/pipeline` (ContentEngine-based) removed
- `POST /content/generate` now uses LangGraph exclusively, returns richer `GenerateResponse`
- `POST /content/regenerate` added (always creates new `pipeline_id`, no state carry-over)
- `GET /content/pipeline/{id}` and `GET /content/pipeline/{id}/output` retained for polling
- `POST /content/ideas` kept (uses ContentEngine stage classes directly)

### 7. Schemas Updated

- `schemas/content.py`: Replaced `PipelineCreateRequest`/`PipelineCreateResponse` with `GenerateResponse` (includes `topic`, `quality_label`, `total_duration_ms`, `steps_completed`, `errors`) and `RegenerateRequest`

### 8. Tests

- 90 content + graph tests all passing
- 421 total tests in suite — all pass
- `test_graph.py` fixed: Pydantic-compatible `_make_state()`, factory function imports, routing expectations, cycle-safe graph execution
- Pre-existing SQLAlchemy connection warnings (not from our changes)

## Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Keep stage classes, remove orchestration layer | Stages contain reusable logic; orchestration was the duplication source |
| Review loop-back to writing | Prevents human-in-loop requiring for minor revisions; capped at 2 cycles |
| `/regenerate` always creates new pipeline_id | Stateless — no state carry-over between generations |
| Pydantic BaseModel over TypedDict | Type-safe defaults, validation, no mutable-default footguns |

## Files Changed

```
backend/application/graph/state.py          — ContentState: add revision_count
backend/application/graph/graph.py          — _route_from_review: add revision cap
backend/application/graph/nodes/*.py        — all 9 nodes: error+timing wiring
backend/application/graph/nodes/review_node.py — increment revision_count
backend/api/v1/content.py                   — removed /pipeline POST, unified generate/regenerate
backend/schemas/content.py                  — new GenerateResponse, RegenerateRequest
backend/services/content_engine/service.py  — stripped to generate_ideas only
backend/services/content_engine/__init__.py — updated exports
backend/tests/test_graph.py                 — factory imports, Pydantic init, routing
```

## Next Steps

1. Frontend implementation (pending approval)
2. Production validation with Docker Compose
3. Monitoring for LangGraph execution latencies
