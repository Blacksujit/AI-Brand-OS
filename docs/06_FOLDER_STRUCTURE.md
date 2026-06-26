# Folder Structure

> **Phase**: Architecture — Project Layout  
> **Status**: Draft  
> **Last Updated**: 2026-06-26

## Overview

This document defines the BrandOS monorepo directory layout. Every directory and module boundary is derived from the architecture, service boundaries, and data ownership rules established in `02_SYSTEM_ARCHITECTURE.md` and `03_LOW_LEVEL_DESIGN.md`.

### Design Rules

1. **One service = one subpackage**. Services communicate via dependency injection, never direct imports across service boundaries.
2. **Infrastructure is shared, domain is isolated**. Cross-cutting concerns (cache, db, llm, queue) live in `core/`; business logic stays in `services/`.
3. **Prompts are assets, not code**. Every LLM prompt lives under `prompts/` as a standalone file, never hardcoded in a Python string.
4. **Adapters isolate externals**. LinkedIn, Twitter, GitHub, LLM providers all have adapter interfaces with concrete implementations injected by config.
5. **Tests mirror source**. `tests/` mirrors `app/` structure exactly — one test module per service, per pipeline, per adapter.
6. **Frontend is a consumer, not a controller**. BFF routes in `app/api/` handle auth and proxying; business logic never lives in the frontend.

---

## Top-Level Layout

```
brand-os/
├── .github/
├── backend/
├── frontend/
├── infrastructure/
├── docs/
├── prompts/
├── scripts/
├── .env.example
├── .gitignore
├── AGENTS.md
└── README.md
```

---

## `.github/` — CI/CD & Contribution

```
.github/
├── workflows/
│   ├── ci.yml                  # Lint, typecheck, test backend + frontend
│   ├── cd.yml                  # Deploy to staging/production
│   ├── pr-checks.yml           # PR gate: lint, test, build
│   └── nightly-tests.yml       # Integration + E2E tests (daily)
├── CODEOWNERS                  # Automatic reviewer assignment per path
├── renovate.json               # Dependency auto-update config
└── PULL_REQUEST_TEMPLATE.md
```

**Boundary**: CI only. No service or app code. Renovate bot handles dependency PRs.

---

## `backend/` — Python FastAPI Monolith (Schema-Separated)

```
backend/
├── alembic/
│   ├── versions/                # Migration scripts (one per change)
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_chromadb_collections.py
│   │   └── 003_partition_content_tables.py
│   ├── env.py                   # Alembic environment config
│   └── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory, middleware stack, router registration
│   ├── config.py                # Pydantic Settings (60+ env vars)
│   ├── dependencies.py          # FastAPI dependency injection (get_db, get_current_user, etc.)
│   ├── exceptions.py            # BrandOSError exception hierarchy (28+ types)
│   ├── middleware/              # Request-scoped middleware
│   │   ├── __init__.py
│   │   ├── correlation_id.py    # Request ID injection
│   │   ├── rate_limit.py        # Token-bucket rate limiter (Redis-backed)
│   │   ├── request_log.py       # Structured request/response logging
│   │   └── security_headers.py  # CSP, HSTS, X-Frame-Options
│   ├── models/                  # SQLAlchemy ORM models (one file per schema)
│   │   ├── __init__.py          # Re-exports all models for Alembic
│   │   ├── auth.py              # users, user_auth_providers, sessions
│   │   ├── profile.py           # user_profiles, expertise_areas, user_preferences
│   │   ├── github.py            # repositories, commits, pull_requests
│   │   ├── kb.py                # knowledge_items, knowledge_tags, knowledge_embeddings
│   │   ├── trend.py             # trending_topics, trend_sources
│   │   ├── content.py           # content_drafts, draft_revisions, content_briefs, brief_ideas
│   │   ├── style.py             # style_profiles, style_signals, ratings
│   │   ├── platform.py          # platform_connections, scheduled_posts, publish_logs, analytics_cache
│   │   └── notification.py      # notification_logs, notification_preferences
│   ├── schemas/                 # Pydantic request/response schemas (one file per domain)
│   │   ├── __init__.py
│   │   ├── common.py            # PaginatedResult, ErrorResponse, SuccessResponse
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── connections.py
│   │   ├── knowledge_base.py
│   │   ├── content.py
│   │   ├── publishing.py
│   │   ├── analytics.py
│   │   └── admin.py
│   ├── services/               # 11 domain services (business logic)
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract BaseService with common patterns
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # AuthService implementation
│   │   │   ├── interface.py     # Abstract IAuthService
│   │   │   └── oauth.py         # OAuth provider implementations (Google, GitHub, LinkedIn)
│   │   ├── profile/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # ProfileService
│   │   │   └── interface.py     # Abstract IProfileService
│   │   ├── github/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # GitHubService
│   │   │   ├── interface.py     # Abstract IGitHubService
│   │   │   ├── client.py        # GitHub API client (async HTTP)
│   │   │   ├── parser.py        # Commit/PR message parsing
│   │   │   └── sync.py          # Incremental sync logic
│   │   ├── knowledge_base/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # KnowledgeBaseService
│   │   │   ├── interface.py     # Abstract IKnowledgeBaseService
│   │   │   ├── ingestion.py     # Text extraction, summarization, embedding pipeline
│   │   │   └── search.py        # Hybrid search (FTS + vector) query builder
│   │   ├── trend/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # TrendService
│   │   │   ├── interface.py     # Abstract ITrendService
│   │   │   ├── scrapers/        # Trend source scrapers
│   │   │   │   ├── hacker_news.py
│   │   │   │   ├── devto.py
│   │   │   │   └── github_trending.py
│   │   │   └── scorer.py        # Relevance scoring per user profile
│   │   ├── content_engine/      # The most architecturally significant service
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # ContentEngineService (orchestrates pipeline)
│   │   │   ├── interface.py     # Abstract IContentEngineService
│   │   │   ├── pipeline.py      # Pipeline orchestrator (run stages sequentially with fallback)
│   │   │   └── stages/          # 5 pipeline stages (each is a class with __call__)
│   │   │       ├── __init__.py
│   │   │       ├── base.py      # Abstract BaseStage with retry/metrics
│   │   │       ├── context_aggregator.py
│   │   │       ├── idea_generator.py
│   │   │       ├── draft_composer.py
│   │   │       ├── style_refiner.py
│   │   │       └── quality_gate.py
│   │   ├── style/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # StyleService
│   │   │   ├── interface.py     # Abstract IStyleService
│   │   │   ├── fingerprint.py   # Voice fingerprint (lexical, syntactic, tonal, structural)
│   │   │   ├── analyzers/       # 4 analyzers
│   │   │   │   ├── lexical.py
│   │   │   │   ├── syntactic.py
│   │   │   │   ├── tonal.py
│   │   │   │   └── structural.py
│   │   │   └── ema.py           # Exponential moving average convergence logic
│   │   ├── platform/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # PlatformService
│   │   │   ├── interface.py     # Abstract IPlatformService
│   │   │   ├── scheduler.py     # Post scheduling engine (cron-aware)
│   │   │   └── adapters/        # Platform adapters (one per platform)
│   │   │       ├── __init__.py
│   │   │       ├── base.py      # Abstract BasePlatformAdapter
│   │   │       ├── linkedin.py  # LinkedInAdapter
│   │   │       └── twitter.py   # TwitterAdapter (Phase 2)
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # AnalyticsService
│   │   │   ├── interface.py     # Abstract IAnalyticsService
│   │   │   ├── metrics.py       # Engagement metrics calculations
│   │   │   └── scoring.py       # Content Authority Score computation
│   │   ├── brief/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # BriefService
│   │   │   └── interface.py     # Abstract IBriefService
│   │   └── notification/
│   │       ├── __init__.py
│   │       ├── service.py       # NotificationService
│   │       ├── interface.py     # Abstract INotificationService
│   │       ├── channels/        # Delivery channels
│   │       │   ├── email.py
│   │       │   ├── in_app.py
│   │       │   └── push.py
│   │       └── templates/       # Notification templates
│   │           ├── daily_brief.html
│   │           ├── publish_success.html
│   │           └── weekly_summary.html
│   ├── api/v1/                  # Route handlers (thin — call service, return response)
│   │   ├── __init__.py
│   │   ├── router.py            # Root API router aggregating all sub-routers
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── connections.py
│   │   ├── knowledge_base.py
│   │   ├── content.py
│   │   ├── publishing.py
│   │   ├── analytics.py
│   │   ├── admin.py
│   │   ├── webhooks.py
│   │   └── deps.py              # Route-level dependencies (pagination, filters)
│   ├── core/                    # Cross-cutting infrastructure (shared, not service-owned)
│   │   ├── __init__.py
│   │   ├── cache.py             # Redis cache abstraction (ICacheService)
│   │   ├── db.py                # SQLAlchemy async engine + session factory
│   │   ├── llm.py               # LLM client abstraction (ILLMClient)
│   │   ├── llm_providers/       # LLM provider implementations
│   │   │   ├── anthropic.py
│   │   │   ├── openai.py
│   │   │   └── fallback.py      # Provider A → Provider B → Cache → Error
│   │   ├── embedding.py         # Embedding service (IEmbeddingService)
│   │   ├── storage.py           # S3-compatible storage (IStorageService)
│   │   ├── queue.py             # Arq job queue (IJobQueue)
│   │   ├── security.py          # JWT encode/decode, encryption (AES-256-GCM), password hashing
│   │   ├── logging.py           # Structured JSON logger setup
│   │   └── telemetry.py         # OpenTelemetry tracing + metrics setup
│   ├── workers/                 # Arq background worker functions
│   │   ├── __init__.py
│   │   ├── worker.py            # Arq worker process entry point
│   │   ├── daily_brief.py       # Generate and deliver daily briefs
│   │   ├── github_sync.py       # Periodic GitHub data sync
│   │   ├── kb_ingestion.py      # Async knowledge item processing pipeline
│   │   ├── content_pipeline.py  # Full content lifecycle (idea→draft→schedule→publish)
│   │   ├── publishing.py        # Scheduled post publication
│   │   ├── analytics.py         # Periodic analytics refresh + cache warming
│   │   └── trend_scan.py        # Trend source polling
│   ├── pipelines/               # Non-content-engine pipelines (for extraction, etc.)
│   │   ├── __init__.py
│   │   └── kb_ingestion.py      # Text extraction → summarization → embedding → classification
│   ├── templates/               # Jinja2 templates (brief HTML, report HTML)
│   │   ├── brief.html
│   │   └── report.html
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Shared fixtures: test DB, Redis, mock LLM, auth headers
│   │   ├── services/            # Tests mirror services/ structure
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_profile_service.py
│   │   │   ├── test_github_service.py
│   │   │   ├── test_knowledge_base_service.py
│   │   │   ├── test_trend_service.py
│   │   │   ├── test_content_engine_service.py
│   │   │   ├── test_style_service.py
│   │   │   ├── test_platform_service.py
│   │   │   ├── test_analytics_service.py
│   │   │   ├── test_brief_service.py
│   │   │   └── test_notification_service.py
│   │   ├── api/                 # Tests for route handlers
│   │   │   ├── test_auth_api.py
│   │   │   ├── test_profile_api.py
│   │   │   ├── test_content_api.py
│   │   │   └── ...
│   │   ├── pipelines/           # Tests for pipeline stages
│   │   │   ├── test_context_aggregator.py
│   │   │   ├── test_idea_generator.py
│   │   │   ├── test_draft_composer.py
│   │   │   ├── test_style_refiner.py
│   │   │   └── test_quality_gate.py
│   │   ├── adapters/            # Tests for platform adapters
│   │   │   ├── test_linkedin_adapter.py
│   │   │   └── test_twitter_adapter.py
│   │   ├── workers/
│   │   │   ├── test_daily_brief.py
│   │   │   └── test_github_sync.py
│   │   └── fixtures/            # Test data (JSON snapshots, mock responses)
│   │       ├── github_responses/
│   │       ├── linkedin_responses/
│   │       └── sample_profiles/
│   ├── utils/                   # Shared utilities (no business logic)
│   │   ├── __init__.py
│   │   ├── text.py              # Text cleaning, truncation, token counting
│   │   ├── time.py              # Timezone helpers, cron expression parsing
│   │   ├── validators.py        # Custom Pydantic validators
│   │   └── markdown.py          # Markdown-to-plaintext conversion
│   └── __main__.py              # `python -m app` entry point (uvicorn)
├── requirements/
│   ├── base.txt                 # Production dependencies
│   ├── dev.txt                  # Dev dependencies (pytest, ruff, mypy, etc.)
│   └── prod.txt                 # Pinned production deps (pip freeze)
├── Dockerfile                   # Multi-stage build (dev → prod)
├── Dockerfile.worker            # Worker-specific image (no API server)
├── pyproject.toml               # Project metadata, ruff config, mypy config
└── .coveragerc                  # Coverage configuration
```

### Service Dependency Rule

```
services/
├── brief ────────────→ trend, content_engine, notification
├── content_engine ───→ github, knowledge_base, trend, style, profile
├── analytics ────────→ platform, content_engine
├── notification ─────→ (standalone)
├── platform ─────────→ content_engine
├── style ────────────→ profile
├── github ───────────→ profile
├── knowledge_base ───→ profile
├── trend ────────────→ profile, knowledge_base
├── auth ─────────────→ profile
└── profile ──────────→ (standalone)
```

**Enforcement**: `services/` subpackages import only from `core/`, `models/`, `schemas/`, and downstream services via interface. Direct import of another service's internal module (e.g., `services/style/ema.py`) is forbidden — always go through the interface.

---

## `frontend/` — Next.js 14+ App Router

```
frontend/
├── public/                       # Static assets (favicon, og-image, logo)
│   ├── favicon.ico
│   ├── og-image.png
│   └── logo.svg
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── layout.tsx            # Root layout (fonts, metadata, providers)
│   │   ├── page.tsx              # Landing page (unauthenticated)
│   │   ├── (auth)/               # Auth route group (no sidebar)
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── register/
│   │   │   │   └── page.tsx
│   │   │   ├── oauth-callback/
│   │   │   │   └── page.tsx      # OAuth redirect handler
│   │   │   └── layout.tsx        # Auth layout (centered card, no nav)
│   │   ├── (dashboard)/          # Dashboard route group (authenticated, sidebar)
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx      # Main dashboard (brief overview + quick actions)
│   │   │   ├── content/
│   │   │   │   ├── page.tsx      # Content feed (drafts, scheduled, published)
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx  # Draft editor
│   │   │   │   └── new/
│   │   │   │       └── page.tsx  # Idea selection → draft generation
│   │   │   ├── analytics/
│   │   │   │   └── page.tsx      # Analytics dashboard
│   │   │   ├── knowledge-base/
│   │   │   │   ├── page.tsx      # KB items list + search
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx  # KB item detail/edit
│   │   │   ├── settings/
│   │   │   │   ├── page.tsx      # Profile + preferences
│   │   │   │   ├── connections/
│   │   │   │   │   └── page.tsx  # GitHub / LinkedIn connections
│   │   │   │   └── notifications/
│   │   │   │       └── page.tsx  # Notification preferences
│   │   │   ├── brief/
│   │   │   │   └── page.tsx      # Daily brief view
│   │   │   └── layout.tsx        # Dashboard layout (sidebar, topnav)
│   │   ├── api/                  # BFF route handlers (auth proxy, session management)
│   │   │   ├── auth/
│   │   │   │   ├── [...nextauth]/
│   │   │   │   │   └── route.ts  # NextAuth.js catch-all
│   │   │   │   └── refresh/
│   │   │   │       └── route.ts  # Token refresh proxy to backend
│   │   │   └── proxy/
│   │   │       └── [...path]/
│   │   │           └── route.ts  # Generic API proxy (adds auth headers)
│   │   └── error.tsx             # Global error boundary
│   ├── components/               # React components
│   │   ├── ui/                   # Design system primitives (Button, Input, Card, Modal, etc.)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── select.tsx
│   │   │   ├── modal.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── spinner.tsx
│   │   │   └── index.ts          # Barrel export
│   │   ├── layout/               # Layout components
│   │   │   ├── sidebar.tsx
│   │   │   ├── topnav.tsx
│   │   │   ├── auth-guard.tsx    # Redirect unauthenticated users
│   │   │   └── onboarding-flow.tsx
│   │   ├── forms/                # Form components (react-hook-form + zod)
│   │   │   ├── login-form.tsx
│   │   │   ├── register-form.tsx
│   │   │   ├── profile-form.tsx
│   │   │   ├── preferences-form.tsx
│   │   │   └── kb-item-form.tsx
│   │   ├── content/              # Content-specific components
│   │   │   ├── draft-editor.tsx  # Rich text editor (with style score indicator)
│   │   │   ├── draft-card.tsx    # Feed card (status, engagement preview, actions)
│   │   │   ├── idea-list.tsx     # Generated ideas with selection
│   │   │   ├── schedule-picker.tsx
│   │   │   └── style-meter.tsx   # Visual style fingerprint gauge
│   │   ├── analytics/            # Analytics components
│   │   │   ├── engagement-chart.tsx
│   │   │   ├── audience-chart.tsx
│   │   │   ├── content-score.tsx
│   │   │   └── metric-card.tsx
│   │   └── common/               # Shared components
│   │       ├── empty-state.tsx
│   │       ├── error-boundary.tsx
│   │       ├── confirm-dialog.tsx
│   │       └── loading-skeleton.tsx
│   ├── lib/                      # Client-side utilities
│   │   ├── api-client.ts         # Typed fetch wrapper with auto-refresh
│   │   ├── auth.ts               # Auth context provider + hooks
│   │   ├── utils.ts              # cn(), formatters, date helpers
│   │   └── constants.ts          # Route paths, feature flags
│   ├── hooks/                    # Custom React hooks
│   │   ├── use-auth.ts
│   │   ├── use-content.ts
│   │   ├── use-analytics.ts
│   │   ├── use-debounce.ts
│   │   └── use-intersection-observer.ts
│   ├── stores/                   # Zustand stores
│   │   ├── auth-store.ts
│   │   ├── content-store.ts
│   │   └── ui-store.ts           # Sidebar state, theme, toasts
│   ├── styles/                   # Global styles
│   │   ├── globals.css           # Tailwind directives + CSS custom properties
│   │   └── prose.css             # Tailwind typography prose overrides
│   └── types/                    # TypeScript type definitions
│       ├── api.ts                # API response/request types (mirrors backend schemas)
│       ├── content.ts
│       ├── analytics.ts
│       └── next-auth.d.ts        # NextAuth type augmentation
├── __tests__/                    # Frontend tests
│   ├── components/
│   ├── hooks/
│   └── e2e/                      # Playwright E2E tests
│       ├── auth.spec.ts
│       ├── content.spec.ts
│       └── dashboard.spec.ts
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── jest.config.ts
├── playwright.config.ts
├── .eslintrc.json
├── postcss.config.js
└── package.json
```

### Frontend-Backend Boundary

```
┌──────────────┐     BFF Proxy     ┌───────────────┐
│  Next.js SSR  │ ──────────────→  │  FastAPI API   │
│  pages        │ ←────────────── │  v1 routes     │
│               │   JSON responses │                │
│  api/         │                  │  services/     │
│  ├── auth/    │  Auth delegation │  core/         │
│  └── proxy/   │  API key mgmt   │  models/       │
└──────────────┘                  └───────────────┘
```

- Frontend never calls external APIs directly. All external requests go through the backend.
- Frontend `api/proxy/` only adds auth headers and forwards. No business logic transformation.
- Auth session management uses NextAuth.js with JWT cookies; refresh tokens proxied to `POST /auth/refresh`.

---

## `infrastructure/` — Deployment & Operations

```
infrastructure/
├── docker/
    │   ├── docker-compose.yml         # Dev: api + worker + sqlite + chromadb + redis + minio
│   ├── docker-compose.prod.yml    # Prod overrides (replicas, secrets, logging driver)
│   └── .env.example               # Docker Compose environment variables
├── k8s/                           # Kubernetes manifests (Phase 2+)
│   ├── base/                      # Shared configs
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   └── secrets.yaml           # ExternalSecret references
│   ├── api/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml               # Horizontal Pod Autoscaler
│   │   └── pdb.yaml               # Pod Disruption Budget
│   ├── worker/
│   │   ├── deployment.yaml
│   │   └── hpa.yaml
│   ├── ingress.yaml               # Traefik / nginx-ingress config
│   └── overlays/                  # Environment-specific overlays
│       ├── staging/
│       │   └── kustomization.yaml
│       └── production/
│           └── kustomization.yaml
└── terraform/                     # Infrastructure-as-Code
    ├── main.tf                    # Provider config + backend (S3 + DynamoDB)
    ├── variables.tf
    ├── outputs.tf
    ├── modules/
    │   ├── rds/                   # Future PostgreSQL (post-MVP)
    │   ├── elasticache/           # Redis (cache + queue)
    │   ├── ecs/                   # Fargate (api + worker)
    │   └── s3/                    # User content storage
    └── environments/
        ├── staging/
        │   └── terraform.tfvars
        └── production/
            └── terraform.tfvars
```

### Infrastructure Phasing

| Component | MVP (Vercel + Render) | Phase 2+ (AWS EKS) |
|-----------|----------------------|-------------------|
| Frontend | Vercel | Vercel (unchanged) |
| API | Render (web service) | ECS Fargate + ALB |
| Workers | Render (worker) | ECS Fargate (scheduled tasks) |
| Database | SQLite (file-based) + ChromaDB (local) | RDS PostgreSQL + pgvector (post-MVP) |
| Cache/Queue | Render Redis (managed) | ElastiCache Redis |
| Storage | Render Disk (ephemeral) | S3 + CloudFront |
| IaC | docker-compose.yml | Terraform + K8s |

---

## `prompts/` — LLM Prompt Assets

```
prompts/
├── content-engine/
│   ├── context_aggregator.txt     # Instructions for building user context summary
│   ├── idea_generator.txt         # Generate content ideas from context + trends
│   ├── draft_composer.txt         # Compose LinkedIn post from idea + context
│   ├── style_refiner.txt          # Rewrite draft to match voice fingerprint
│   └── quality_gate.txt          # Score draft quality (relevance, authenticity, engagement)
├── style-analysis/
│   ├── fingerprint_extraction.txt # Analyze writing to extract voice fingerprint
│   └── signal_classification.txt  # Classify user feedback as positive/negative signal
├── brief-generation/
│   ├── daily_brief.txt            # Generate daily briefing from GitHub + KB + trends
│   └── weekly_summary.txt         # Weekly content performance summary
└── kb-ingestion/
    ├── summarization.txt          # Summarize knowledge item
    └── classification.txt         # Classify item into domain/tag taxonomy
```

**Rule**: Every prompt file is loaded from disk at startup, cached in memory, and referenced by a named constant. Never interpolate user data into prompts at the file level — use `{placeholders}` resolved by the prompt loader.

---

## `scripts/` — Development & Operations Scripts

```
scripts/
├── setup.sh                   # One-command dev env setup (check deps, docker compose up, migrate)
├── seed-data.sh              # Seed demo data (sample user, GitHub repos, KB items)
├── migrate.sh                 # `alembic upgrade head`
├── lint.sh                    # `ruff check . && mypy .`
├── test.sh                    # `pytest --cov=app`
├── reset-db.sh               # Drop + recreate + migrate + seed (dev only)
└── backup-db.sh               # SQLite VACUUM INTO + ChromaDB snapshot to S3
```

---

## Root Files

| File | Purpose |
|------|---------|
| `.env.example` | All environment variables with dummy values and comments. Source of truth for required config. |
| `.gitignore` | Python `__pycache__`, `.venv`, `node_modules`, `.next`, `.env`, `*.pyc`, IDE files |
| `AGENTS.md` | Agent instructions for AI coding assistants (Claude, Copilot, etc.) |
| `README.md` | Project overview, architecture diagram, quick start, links to docs |

---

## Dependency Graph (Folder-Level)

```
prompts/ ←── backend/app/services/content_engine/stages/
              backend/app/workers/
                    │
                    ▼
backend/app/core/ ←── backend/app/services/*/
  ├── cache.py          (all services)
  ├── db.py             (models, services)
  ├── llm.py            (content_engine, style, kb)
  ├── embedding.py      (kb)
  ├── storage.py        (kb, platform)
  ├── queue.py          (workers)
  └── security.py       (auth, middleware)
                    │
                    ▼
backend/app/models/ ←── backend/app/services/*/
                    │
                    ▼
backend/app/schemas/ ←── backend/app/api/v1/
                         backend/app/services/*/
                    │
                    ▼
frontend/src/lib/api-client.ts ←── backend/app/api/v1/*

frontend/src/app/api/ ←── backend/app/api/v1/auth
```

---

## Migration Paths

### Monolith → Microservices (Phase 3)

When a schema exceeds 50 GB or 500 writes/second, extract it as a standalone service:

1. Copy the service subpackage (e.g., `services/knowledge_base/`) to a new repo
2. Add a FastAPI app with its own `main.py`, `core/`, `models/`
3. Add a gRPC or REST client in the original monolith's `core/`
4. Keep the shared `schemas/` as an installable Python package (`brand-os-schemas`)
5. Keep the shared `core/` as another installable package (`brand-os-core`)

The folder structure already supports this: clean interface boundaries, no cross-service internal imports, schema-separated models.

### Shared Package Extraction (Pre-Microservice)

Before full microservice extraction, shared code can be extracted into installable packages:

```
backend/
├── packages/                    # Shared packages (extracted from app/)
│   ├── brand-os-core/           # cache, db, llm, embedding, storage, queue, security, logging
│   │   ├── src/
│   │   └── pyproject.toml
│   ├── brand-os-schemas/        # Pydantic request/response schemas
│   │   ├── src/
│   │   └── pyproject.toml
│   └── brand-os-models/         # SQLAlchemy ORM models
│       ├── src/
│       └── pyproject.toml
├── app/                         # Remaining monolith
└── ...
```

This is pre-optimization. Do not extract until the second independent consumer exists.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Services as subpackages, not separate repos | MVP monolith avoids distributed debugging; clean interface boundaries make extraction trivial |
| `models/` flat, not per-service | Alembic needs a single model import; per-service models create circular migration issues at MVP scale |
| `core/` not `shared/` | "Core" implies infrastructure; "shared" is ambiguous and invites business logic leakage |
| Prompts as standalone `.txt` files in `prompts/` | Version-controllable, reviewable in PRs, loadable at startup, never buried in string literals |
| Tests mirror source structure | `tests/services/` → `services/` — discoverable without cross-reference |
| Separate worker Dockerfile | Worker doesn't need uvicorn, middleware stack, or API routes — smaller image, faster startup |
| `api/v1/` not `api/` | URL-space versioning; `/v2/` can coexist during migration |
| `infrastructure/` not `ops/` or `deploy/` | Includes IaC, not just deploy scripts; "infrastructure" is the standard SRE term |
