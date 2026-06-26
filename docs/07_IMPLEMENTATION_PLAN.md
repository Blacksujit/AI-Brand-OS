# Implementation Plan

> **Phase**: Planning — Build Order & Milestones  
> **Status**: Draft  
> **Last Updated**: 2026-06-26

## Overview

This document defines the build order, week-by-week milestones, and release criteria for BrandOS. It translates the architecture and design into an execution plan organized by service dependencies.

### Build Order (Bottom-Up)

From the service dependency DAG defined in `03_LOW_LEVEL_DESIGN.md`:

```
Layer 0 (Foundation)     Profile
                          Core Infrastructure (db, cache, llm, queue, security)

Layer 1 (Auth + Data)    Auth
                          GitHub
                          Knowledge Base
                          Style

Layer 2 (Intelligence)   Trend
                          Notification

Layer 3 (Core Product)   Content Engine
                          Platform (LinkedIn)

Layer 4 (Value Add)      Analytics
                          Brief
```

Each layer builds on all layers below. Work within a layer can be parallelized.

---

## MVP: Weeks 1–16

### Phase 1: Foundation (Weeks 1–4)

**Goal**: Running auth, profile management, GitHub connection, and core infrastructure. User can sign up, connect GitHub, and see their repos.

| Week | Deliverables | Dependencies |
|------|-------------|--------------|
| W1 | Project scaffolding — monorepo setup, Docker Compose (sqlite, chromadb, redis, minio), pyproject.toml, CI pipeline, cookiecutter service template | None |
| W1 | Core infrastructure — `core/db.py` (async SQLAlchemy engine + session factory), `core/cache.py` (Redis abstraction), `core/logging.py` (structured JSON), `core/security.py` (password hashing, JWT encode/decode, AES-256-GCM) | W1 scaffold |
| W2 | `models/auth.py` + `models/profile.py` (users, sessions, profiles, preferences) | W1 db |
| W2 | Alembic migration 001 — initial schema (auth + profile tables) | W2 models |
| W2 | `ProfileService` + `/api/v1/profile.py` — CRUD, expertise areas, preferences | W2 models |
| W2 | Frontend scaffold — Next.js, Tailwind, shadcn/ui, auth pages (login/register), dashboard layout with sidebar | W1 scaffold |
| W3 | `AuthService` + `/api/v1/auth.py` — register, login, OAuth initiate/callback, refresh, logout, me | W2 ProfileService |
| W3 | OAuth provider implementations — Google OAuth, GitHub OAuth (in `services/auth/oauth.py`) | W3 AuthService |
| W3 | Frontend auth integration — NextAuth.js, login/register pages, auth guard, OAuth callback handler, token refresh | W3 AuthService |
| W4 | `models/github.py` (repositories, commits, pull_requests) + Alembic migration | W2 models |
| W4 | `GitHubService` + `services/github/client.py` (async GitHub API v4 GraphQL client), `parser.py` (commit/PR parsing), `sync.py` (incremental sync logic) | W3 OAuth |
| W4 | `GET /api/v1/connections/github` + `POST /api/v1/connections/github/connect` + webhook endpoint for push events | W4 GitHubService |
| W4 | Frontend connections page — GitHub connect/disconnect, repo list, sync status indicator | W4 API |

**Phase 1 Gate**: User signs up → connects GitHub → sees their repos and commits synced in dashboard. All auth flows work (email/password, GitHub OAuth, Google OAuth). CI green.

---

### Phase 2: Intelligence (Weeks 5–8)

**Goal**: Knowledge base ingestion, style fingerprint convergence, trend scanning. System can analyze user's content and find relevant topics.

| Week | Deliverables | Dependencies |
|------|-------------|--------------|
| W5 | Core LLM — `core/llm.py` (ILLMClient interface), `core/llm_providers/anthropic.py`, `core/llm_providers/openai.py`, `core/llm_providers/fallback.py` (Provider A → B → Cache → error) | Core infra |
| W5 | Core embedding — `core/embedding.py` (IEmbeddingService), text embedding via LLM provider or dedicated embedding model | W5 LLM |
| W5 | Core storage — `core/storage.py` (S3-compatible file storage via boto3 + Minio for dev) | Core infra |
| W5 | Core queue — `core/queue.py` (Arq job queue wrapper, IJobQueue interface) | Core infra |
| W6 | `models/kb.py` (knowledge_items, knowledge_tags, embedding_refs) + Alembic migration + ChromaDB `kb_embeddings` collection setup | W5 embedding |
| W6 | `KnowledgeBaseService` — CRUD, hybrid search (SQLite FTS5 + ChromaDB vector, 0.3/0.7 weight), tag management, `ingestion.py` (text extraction → LLM summarization → embedding → classification), `search.py` (hybrid query builder with SQLite FTS5 + ChromaDB) | W6 models, W5 LLM |
| W6 | `GET /api/v1/kb/items` (search, filter, paginate) + `POST /api/v1/kb/items` (add item) + `DELETE /api/v1/kb/items/{id}` | W6 KBService |
| W6 | Frontend Knowledge Base page — item list, search bar, add item form, tag filter | W6 API |
| W7 | `models/style.py` (style_profiles, style_signals, ratings) + Alembic migration | W2 models |
| W7 | `StyleService` — voice fingerprint (4 analyzers: lexical/syntactic/tonal/structural), EMA signal processing, `fingerprint.py` (convergence logic, 5–10 rated drafts to stable fingerprint), `ema.py` (exponential moving average) | W7 models, W5 LLM |
| W7 | `POST /api/v1/content/rate` — user rates a draft, triggers style signal processing | W7 StyleService |
| W7 | Frontend style meter component — visual gauge showing fingerprint convergence progress | W7 API |
| W8 | `models/trend.py` (trending_topics, trend_sources) + Alembic migration | W2 models |
| W8 | `TrendService` — `scrapers/hacker_news.py`, `scrapers/devto.py`, `scrapers/github_trending.py`, `scorer.py` (relevance scoring per user profile × KB topics) | W8 models, W6 KBService |
| W8 | Worker `trend_scan.py` — periodic polling of trend sources, relevance filtering, caching | W8 TrendService, W5 queue |
| W8 | Frontend trend panel — trending topics card on dashboard | W8 API |

**Phase 2 Gate**: KB accepts text/URL/markdown items, returns hybrid search results. User can rate drafts and see style profile converging. Trending topics appear relevant to user's profile. Workers schedule and execute.

---

### Phase 3: Content Engine + LinkedIn (Weeks 9–12)

**Goal**: Full content pipeline — ideas → drafts → publish to LinkedIn. End-to-end content lifecycle working.

| Week | Deliverables | Dependencies |
|------|-------------|--------------|
| W9 | `prompts/` directory — all 8 prompt files (context_aggregator, idea_generator, draft_composer, style_refiner, quality_gate, fingerprint_extraction, signal_classification, daily_brief, weekly_summary) with `{placeholder}` contracts | Phase 2 |
| W9 | Content Engine pipeline scaffold — `pipeline.py` (orchestrator with stage registry, retry per stage, circuit breaker, metrics collection), `stages/base.py` (abstract BaseStage with timeout, retry policy, typed input/output) | Phase 2 |
| W9 | Stage 1: `ContextAggregator` — collects 7-day GitHub activity + 14-day KB items + recent trends + draft history into structured context object | W9 pipeline scaffold |
| W10 | Stage 2: `IdeaGenerator` — calls LLM with idea_generator prompt + context, parses structured idea objects (title + angle + hook + supporting_points + target_audience), validates schema | W9 Stage 1 |
| W10 | Stage 3: `DraftComposer` — calls LLM with draft_composer prompt + idea + context, returns full draft with post body, suggested hashtags, best posting time | W10 Stage 2 |
| W10 | `models/content.py` (content_drafts, draft_revisions, content_briefs, brief_ideas) + Alembic migration (partitioned HASH) | W9 models |
| W10 | `ContentEngineService` — orchestrates full pipeline, manages draft lifecycle (draft → edit → regenerate → rate), `GET/POST/PUT /api/v1/content/*` | W10 models |
| W11 | Stage 4: `StyleRefiner` — takes draft + current style fingerprint, rewrites to match voice, returns diff (original → refined) | W10 Stage 3 |
| W11 | Stage 5: `QualityGate` — scores draft on relevance (0–10), authenticity (0–10), engagement_potential (0–10), passes if all ≥ 6 OR returns specific failure reasons | W11 Stage 4 |
| W11 | Frontend content page — idea selector → draft editor with style meter → rate/edit/regenerate → schedule → publish flow | W11 API |
| W11 | Draft editor — rich text editor with inline style score, revision history panel, schedule picker, publish button | W11 API |
| W12 | `models/platform.py` (platform_connections, scheduled_posts, publish_logs, analytics_cache) + Alembic migration | W10 models |
| W12 | `PlatformService` — `adapters/base.py` (abstract adapter), `adapters/linkedin.py` (UGC Post API, OAuth v2, image upload, rate limit handling), `scheduler.py` (cron-aware scheduling engine) | W12 models |
| W12 | `POST /api/v1/publishing/publish` + `POST /api/v1/publishing/schedule` + `GET /api/v1/publishing/scheduled` + `DELETE /api/v1/publishing/scheduled/{id}` | W12 PlatformService |
| W12 | Worker `publishing.py` — polls scheduled_posts every 5 min (FOR UPDATE SKIP LOCKED), publishes via adapter, writes to publish_logs | W12 PlatformService, W5 queue |

**Phase 3 Gate**: Full content lifecycle end-to-end: daily brief → ideas → draft → style refine → quality gate → schedule → publish to LinkedIn. Draft editor shows style score in real time. Scheduled posts publish on time.

---

### Phase 4: Analytics + Briefs + Beta Polish (Weeks 13–16)

**Goal**: Analytics dashboard, daily briefs, notification system, beta readiness.

| Week | Deliverables | Dependencies |
|------|-------------|--------------|
| W13 | `models/notification.py` (notification_logs, notification_preferences) + Alembic migration | W2 models |
| W13 | `NotificationService` — channels (email via SendGrid/Resend, in-app via SSE/WebSocket), templates (brief, publish_success, weekly_summary), preference filtering | W13 models |
| W13 | `models/analytics.py` → already in `platform` schema (analytics_cache) | W12 models |
| W13 | `AnalyticsService` — `metrics.py` (impressions, engagement rate, CTR, follower growth, content score), `scoring.py` (Content Authority Score = weighted composite), cache warming | W12 PlatformService |
| W13 | `GET /api/v1/analytics/overview` + `GET /api/v1/analytics/posts` + `GET /api/v1/analytics/trends` + `GET /api/v1/analytics/audience` + `GET /api/v1/analytics/content-score` | W13 AnalyticsService |
| W13 | Worker `analytics.py` — periodic LinkedIn analytics fetch, cache warming, content score recalculation | W13 AnalyticsService, W5 queue |
| W14 | Frontend analytics page — engagement chart, audience growth chart, content score metric card, post list with performance indicators | W13 API |
| W14 | `models/content.py` additions — brief tables already exist in Phase 3 | W10 models |
| W14 | `BriefService` — generates daily brief (trends + recent GitHub + suggested content angles + KB highlights), `GET /api/v1/content/brief/today` | Phase 3 |
| W14 | Worker `daily_brief.py` — scheduled generation + notification delivery (email + in-app) | W14 BriefService, W13 NotificationService |
| W15 | Frontend brief page — daily brief view with trend cards, content suggestions, quick action buttons (→ generate idea from trend) | W14 API |
| W15 | `NotificationService` channels — email templates finalized, in-app notification center UI, notification preferences page | W15 NotificationService |
| W15 | Onboarding flow — first-run wizard: connect GitHub → connect LinkedIn → add KB items → generate first draft → schedule first post | All Phase 3 |
| W16 | **Beta release** — full E2E tests pass, load test at 100 concurrent users, error budget 99.9% uptime, all P0 user stories green | All phases |
| W16 | Production hardening — rate limit tuning, cache TTL optimization, error message polishing, cost tracking (LLM token spend per user) | All phases |

**Phase 4 Gate**: All 15 P0/P1 user stories pass. Beta users can onboard in <5 minutes. Analytics reflect real LinkedIn data. Daily briefs delivered on schedule. No P0 bugs open.

---

## GA: Weeks 17–24 (Phase 5)

**Goal**: Production readiness — performance, security, documentation, monitoring, migration scripts.

| Week | Deliverables |
|------|-------------|
| W17 | Performance optimization — query profiling, N+1 elimination, pagination tuning, Redis cache hit ratio >80% |
| W17 | Image optimization — CDN setup, responsive images in content |
| W18 | Security audit — dependency audit, penetration test, secrets scan, rate limit enforcement verification |
| W18 | GDPR compliance — data export endpoint (`GET /api/v1/admin/user/{id}/export`), delete user flow, privacy policy |
| W19 | Monitoring — Datadog/Grafana dashboards, PagerDuty alerting for P0/P1, OpenTelemetry tracing for pipeline stages |
| W19 | Error budget — implement SLO monitoring, burn rate alerts for API + pipeline + worker |
| W20 | Documentation — API reference (OpenAPI/Swagger), deployment guide, runbook for common incidents, user FAQ |
| W20 | Landing page — public marketing site with features, pricing, testimonials |
| W21 | Closed beta with 50 users — bug bash, feedback collection, NPS survey |
| W21 | Performance test at 500 users — response time P99 < 500ms for API, < 30s for content pipeline |
| W22 | Bug fixes from closed beta, UX polish |
| W22 | Database migration 003 — partition content_drafts, draft_revisions, publish_logs by time |
| W23 | GA release — deploy to production, monitoring active, all runbooks verified |
| W24 | Post-GA stabilization — incident response, hotfix process, monitoring tuning |

**GA Gate**: All P0/P1 user stories pass. Performance at 500 users with P99 API < 500ms, pipeline < 30s. Security audit clean. Error budget >99.9%. All runbooks verified.

---

## Phase 2 (Q1 2027): X/Twitter + Analytics Depth

| Milestone | Target | Dependencies |
|-----------|--------|-------------|
| TwitterAdapter — OAuth v1.1/v2, tweet posting, media upload, rate limit handling | Week +4 post MVP | PlatformService |
| Twitter trend scraper — trending topics from X API | Week +4 | TrendService |
| Multi-platform publishing — schedule same draft to LinkedIn + X with platform-specific formatting | Week +6 | PlatformService |
| Analytics depth — per-platform breakdown, content score trends, audience demographic estimation | Week +8 | AnalyticsService |
| Content Authority Score v2 — incorporate cross-platform engagement velocity, share of voice | Week +8 | AnalyticsService |

---

## Phase 3 (Q2–Q3 2027): Blogs + Newsletters

| Milestone | Target | Dependencies |
|-----------|--------|-------------|
| Platform adapter base → 3 new adapters: Medium, Dev.to, Substack | Week +12 | PlatformService |
| Long-form content pipeline — blog posts 1500–3000 words with structure (H2/H3, pull quotes, CTAs) | Week +14 | ContentEngineService |
| Content repurposing — blog → LinkedIn thread → X thread (automatic) | Week +16 | ContentEngineService |
| Email newsletter generation — digest format from published content | Week +16 | ContentEngineService + NotificationService |

---

## Phase 4 (Q4 2027+): Ecosystem

| Milestone | Target |
|-----------|--------|
| Public API — rate-limited, API-key based, documented with OpenAPI | Q4 2027 |
| Embeddable widget — "Latest posts" widget for personal websites/portfolios | Q4 2027 |
| Team/collaboration — multi-user workspaces, approval workflows | Q1 2028 |
| AI-generated images — DALL-E/Stable Diffusion integration for post visuals | Q1 2028 |

---

## Workstream Dependencies

```
W1 ─── W2 ─── W3 ─── W4 ─── W5 ─── W6 ─── W7 ─── W8 ─── W9 ─── W10 ─── W11 ─── W12 ─── W13 ─── W14 ─── W15 ─── W16
│      │      │      │      │      │      │      │      │       │       │       │       │       │       │       │
│      │      │      │      │      ├── W6 │      │      │       │       │       │       │       │       │       │
│      │      │      │      ├── W5 │      │      │      │       │       │       │       │       │       │       │
│      │      │      │      │      │      ├── W8 │      │       │       │       │       │       │       │       │
│      │      │      │      │      │      │      ├── W9 ─── W10 ── W11 ── W12    │       │       │       │       │
│      │      │      │      │      │      │      │      │       │       │       ├── W13 ── W14 ── W15 ── W16    │
│      │      │      │      │      │      │      │      │       │       │       │       │       │       │       │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┘
 Foundation       Intelligence        Content Engine      Analytics + Beta
```

---

## Release Criteria

### Per-Phase Gate

| Phase | Gate Requirements |
|-------|------------------|
| Phase 1 | User signs up → connects GitHub → sees repos. Auth flows all pass. CI green. |
| Phase 2 | KB hybrid search returns results. Style profile converges after 8 ratings. Trends relevant to user profile. |
| Phase 3 | Full content lifecycle E2E. Draft published to LinkedIn from within app. Scheduled posts fire on time. |
| Phase 4 | All P0 user stories pass. Beta onboarding <5 min. Analytics reflect real data. No P0 bugs. |
| GA | P99 API <500ms at 500 users. Pipeline <30s. Security audit clean. Error budget >99.9%. |

### User Story Coverage (PRD)

| ID | Description | Phase | Priority |
|----|------------|-------|----------|
| US-001 | GitHub activity → daily context | P1 (W5–6) | P0 |
| US-002 | Add article/link → KB item | P2 (W6) | P0 |
| US-003 | Generate content ideas | P3 (W9–10) | P0 |
| US-004 | Compose draft from idea | P3 (W10) | P0 |
| US-005 | Match my writing style | P3 (W11) | P0 |
| US-006 | Edit and refine draft | P3 (W11) | P0 |
| US-007 | Publish to LinkedIn | P3 (W12) | P0 |
| US-008 | Schedule posts | P3 (W12) | P0 |
| US-009 | Rate published content | P4 (W13) | P1 |
| US-010 | Daily content brief | P4 (W14) | P1 |
| US-011 | Track engagement analytics | P4 (W13) | P1 |
| US-012 | Multi-platform posting | Phase 2 | P1 |
| US-013 | One-tap repurpose content | Phase 3 | P2 |
| US-014 | Grant assistant access | Phase 3 | P2 |
| US-015 | Maintain brand voice across posts | Phase 2 | P1 |

---

## Test Strategy

| Layer | Tool | Scope | Frequency |
|-------|------|-------|-----------|
| Unit tests | pytest + pytest-asyncio | Services, pipelines, adapters, utils | Every PR |
| Integration tests | pytest + testcontainers (PG + Redis) | API endpoints, worker jobs, DB queries | Every PR |
| E2E tests | Playwright (frontend) + httpx (backend) | Auth flow, content lifecycle, publishing | Nightly |
| Load tests | k6 or locust | API endpoints, content pipeline | Pre-release |
| Security scan | bandit, safety, trivy | Dependencies, code patterns | Weekly CI |

### Test Targets

| Metric | Target |
|--------|--------|
| Unit test coverage (app/services/) | ≥ 90% |
| Unit test coverage (app/pipelines/) | ≥ 95% |
| Integration test coverage (api/v1/) | 100% of endpoints |
| E2E test coverage (critical paths) | Auth, Content Lifecycle, Publishing |

---

## Risk-Adjusted Timeline

| Risk | Likelihood | Impact | Mitigation | Buffer |
|------|-----------|--------|------------|--------|
| LinkedIn API rate limits block publishing | Medium | High | UGC Post API with quota tracking; queue with exponential backoff; fallback to "save as draft" | +2 days |
| LLM cost exceeds budget | Medium | Medium | Token tracking per user; tiered model selection (Haiku for stages 1/2/4, Sonnet for stage 3); hard monthly cap per user | +3 days |
| Style convergence requires >10 ratings | Low | Medium | Seed fingerprint from writing sample analysis; cold-start with technical-writing defaults | +2 days |
| GitHub API pagination for large repos | Low | Medium | Incremental sync with cursor-based pagination; sync only default branch + recent (≤90 days) | +1 day |
| ChromaDB query performance regression | Low | High | HNSW index tuning (ef_search, M); ChromaDB batch size limits; query timeout 5s; Phase 2 vector store scaling | +3 days |

### Buffer Allocation

Each phase includes a **20% time buffer** distributed across the final 2 weeks for integration issues, unexpected edge cases, and UX polish.

| Phase | Working Days | Buffer Days | Total |
|-------|-------------|-------------|-------|
| Phase 1 (W1–4) | 16 | 4 | 20 |
| Phase 2 (W5–8) | 16 | 4 | 20 |
| Phase 3 (W9–12) | 16 | 4 | 20 |
| Phase 4 (W13–16) | 16 | 4 | 20 |
| GA (W17–24) | 32 | 8 | 40 |

---

## Resource Plan

### MVP Team (Recommended)

| Role | Count | Focus |
|------|-------|-------|
| Backend engineer | 2 | Services, API, workers, DB |
| Frontend engineer | 1 | Next.js, components, BFF |
| ML/AI engineer | 1 | LLM integration, prompt engineering, style fingerprint, embeddings |
| DevOps/Infra | 0.5 | CI/CD, Docker, deployment (shared) |
| PM/Design | 0.5 | Product decisions, UX review, user testing (shared) |

### Parallelization Opportunities

| Workstreams | Can Run Together | Notes |
|-------------|-----------------|-------|
| Frontend auth pages + Backend auth service | No — backend API must exist first | Sequential: W3 |
| KB ingestion pipeline + Trend scraper | Yes — independent but both need core infra | Parallel: W6 + W8 |
| Style analyzers (4) | Yes — independent | Parallel: W7 |
| Content pipeline stages (5) | No — sequential by design | Sequential: W9–11 |
| Analytics service + Frontend analytics | No — backend API must exist first | Sequential: W13–14 |
| Notification service + Brief service | Partial — brief depends on notification | Overlapping: W13–14 |
| Infrastructure + All backend | Yes — infra is prerequisite | W1 infra, then ongoing |
| GA tasks (perf, security, docs) | Yes — independent workstreams | Parallel: W17–20 |
