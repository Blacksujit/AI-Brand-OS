# Implementation Plan: BrandOS (Firebase Stack)

## Document Info

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Created** | 2026-07-14 |
| **Stack** | Firebase Cloud Functions + Next.js + pgvector |
| **Duration** | 12 weeks (3 phases) |

---

## Table of Contents

- [Overview](#1-overview)
- [Build Order](#2-build-order)
- [Phase 1: Foundation (Weeks 1-4)](#3-phase-1-foundation-weeks-1-4)
- [Phase 2: Core Product (Weeks 5-8)](#4-phase-2-core-product-weeks-5-8)
- [Phase 3: Publishing & Analytics (Weeks 9-12)](#5-phase-3-publishing--analytics-weeks-9-12)
- [What Changed from the Python Plan](#6-what-changed-from-the-python-plan)

---

## 1. Overview

This plan builds BrandOS bottom-up, with each phase gated by a working user-facing feature. The total timeline is **12 weeks** — reduced from 16 weeks in the original Python plan because Firebase eliminates:

- Custom auth infrastructure (JWT, sessions, password hashing)
- Custom database setup (SQLite, Alembic migrations, ChromaDB)
- Custom middleware stack (CORS, correlation IDs, security headers)
- Custom queue system (Arq + Redis)
- Docker Compose for local development
- CI/CD pipeline for multiple deploy targets

What remains manual: the domain logic (content pipeline, style analysis, publishing), AI integration (Groq + Mistral), and frontend.

### Build Order

```
Layer 2 (Intelligence)
  Content Pipeline ← Knowledge, Style, Groq
  Publishing       ← LinkedIn API, Scheduler

Layer 1 (Data)
  Knowledge Base   ← Firestore + pgvector
  Style            ← pgvector EMA
  Connections      ← LinkedIn OAuth

Layer 0 (Foundation)
  Auth + Profile   ← Firebase Auth + Firestore
  Common           ← Firebase Admin, Zod, errors, logger
  Infra            ← Firebase project, Firestore indexes, pgvector
```

---

## 2. Build Order

By dependency:

| Layer | Component | Depends On |
|-------|-----------|------------|
| **0** | Firebase project + config | Nothing |
| **0** | `common/` (firebase, supabase, errors, logger) | Firebase project |
| **0** | Firestore indexes + Security Rules | Firebase project |
| **0** | pgvector schema (Supabase) | Supabase project |
| **1** | Auth (Firebase Auth triggers) | common/firebase |
| **1** | Profile functions | common/firebase, Auth |
| **1** | Knowledge Base functions | common/firebase, common/supabase |
| **1** | Style service | common/supabase |
| **1** | Connections (LinkedIn OAuth) | common/firebase |
| **2** | Content Pipeline (Groq) | Knowledge, Style, common/groq |
| **2** | Content functions | Content Pipeline |
| **2** | Briefs functions | Content Pipeline |
| **2** | Publishing functions | Connections (LinkedIn) |
| **2** | Analytics functions | Publishing |

---

## 3. Phase 1: Foundation (Weeks 1-4)

**Goal**: Authenticated user can manage their profile, save knowledge items, and search them. The dashboard shows a profile overview and knowledge base.

### Week 1: Firebase Project + Common Infrastructure

| Task | Files | Notes |
|------|-------|-------|
| Create Firebase project (Blaze plan) | — | Enable Auth, Firestore, Functions, Cloud Scheduler |
| Initialize `functions/` with `firebase init` | `functions/package.json`, `functions/tsconfig.json`, `firebase.json`, `.firebaserc` | |
| Install dependencies | `functions/package.json` | `firebase-functions`, `firebase-admin`, `zod`, `@supabase/supabase-js`, `groq-sdk`, `@mistralai/mistralai` |
| Set up environment variables | `functions/.env` (local) + Firebase secrets | `GROQ_API_KEY`, `MISTRAL_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` |
| Write `common/firebase.ts` | Common | Initialize Admin SDK, export Firestore `db` reference |
| Write `common/supabase.ts` | Common | Initialize `createClient` with `service_role` key |
| Write `common/errors.ts` | Common | `AppError`, `ValidationError`, `NotFoundError`, `RateLimitError`, `AiProviderError` |
| Write `common/logger.ts` | Common | Structured console logger with severity levels |
| Write `common/ratelimit.ts` | Common | In-memory token bucket (per-user, per-function) |
| Write `common/types.ts` | Common | `ContentType`, `ContentTone`, `ContentLength`, `PostStatus` enums + shared interfaces |
| Write Zod schemas | `schemas/profile.ts`, `schemas/knowledge.ts`, `schemas/content.ts`, `schemas/publish.ts`, `schemas/analytics.ts`, `schemas/briefs.ts`, `schemas/connections.ts`, `schemas/common.ts` | Validate all function inputs |
| Write Firestore Security Rules | `firestore.rules` | Per-user subcollection access; admin-only access for analytics and worker collections |
| Write composite index config | `firestore.indexes.json` | All composite indexes from 05_DATABASE.md |
| Apply pgvector migrations | `supabase/migrations/001-004` | Run on Supabase project |
| Set up frontend Firebase SDK | `frontend/lib/firebase.ts` | `initializeApp`, `getFunctions`, `getAuth` |
| Write typed API client | `frontend/lib/api.ts` | `createCallable<TInput, TOutput>` wrappers |

### Week 2: Auth + Profile

| Task | Files | Notes |
|------|-------|-------|
| Write `onUserCreate` auth trigger | `functions/src/triggers.ts` | Creates user Firestore document + pgvector style_vector row on sign-up |
| Write `profile-getMyProfile` | `functions/src/profile/getMyProfile.ts` | Reads user document |
| Write `profile-updateMyProfile` | `functions/src/profile/updateMyProfile.ts` | Updates user document fields |
| Write `profile-updateMyPreferences` | `functions/src/profile/updateMyPreferences.ts` | Updates user preferences subfields |
| Register functions in `index.ts` | `functions/src/index.ts` | Export all `onCall` handlers |
| Write Firebase Auth context | `frontend/lib/auth.ts` | `useAuth` hook, sign-in/sign-up/sign-out |
| Write auth guard component | `frontend/components/layout/auth-guard.tsx` | Redirect to /login if not authenticated |
| Update login/register pages | `frontend/app/(auth)/login/page.tsx`, `register/page.tsx` | Use Firebase Auth instead of NextAuth |
| Write profile form | `frontend/components/forms/profile-form.tsx` | Display name, bio, preferences |
| Write dashboard page | `frontend/app/(dashboard)/dashboard/page.tsx` | Profile card, quick stats, recent activity |

**Phase 1 Gate**: User signs up → sees dashboard with profile → can edit profile and preferences. Auth trigger creates Firestore document. CI green.

### Week 3: Knowledge Base (CRUD + Search)

| Task | Files | Notes |
|------|-------|-------|
| Write `knowledge-createItem` | `functions/src/knowledge/createItem.ts` | Validates input, writes to Firestore |
| Write `knowledge-getItem` | `functions/src/knowledge/getItem.ts` | Reads single item |
| Write `knowledge-updateItem` | `functions/src/knowledge/updateItem.ts` | Updates editable fields |
| Write `knowledge-deleteItem` | `functions/src/knowledge/deleteItem.ts` | Deletes document + pgvector row via trigger |
| Write `knowledge-search` | `functions/src/knowledge/search.ts` | Queries pgvector `match_knowledge` RPC |
| Write `onKnowledgeWritten` trigger | `functions/src/triggers.ts` | On write: generate Mistral embedding → upsert pgvector. On delete: remove from pgvector |
| Write `common/mistral.ts` | `functions/src/common/mistral.ts` | MistralService: `generateEmbedding(text)` → 768-d vector |
| Write `match_knowledge` RPC | Supabase migration `004` | PostgreSQL function for filtered cosine similarity |
| Write knowledge list/search page | `frontend/app/(dashboard)/knowledge-base/page.tsx` | Search bar, tag filter, item list |
| Write knowledge item detail page | `frontend/app/(dashboard)/knowledge-base/[id]/page.tsx` | Read/edit form |
| Write knowledge add form | `frontend/components/forms/kb-item-form.tsx` | URL, title, note, tags, source type |

### Week 4: Connections + Style Foundation

| Task | Files | Notes |
|------|-------|-------|
| Write `connections-connectLinkedIn` | `functions/src/connections/connectLinkedIn.ts` | OAuth callback → store encrypted tokens in Firestore |
| Write `connections-connectGitHub` | `functions/src/connections/connectGitHub.ts` | OAuth callback → store encrypted tokens |
| Write `connections-getConnectionStatus` | `functions/src/connections/getConnectionStatus.ts` | Returns status of all platform connections |
| Write `connections-disconnect` | `functions/src/connections/disconnect.ts` | Removes connection document |
| Write `common/linkedin.ts` | `functions/src/common/linkedin.ts` | LinkedIn API v2 client (OAuth, user info, post creation) |
| Write `common/github.ts` | `functions/src/common/github.ts` | GitHub API client (commits, repos) |
| Set up Firestore trigger for `onDraftRated` | `functions/src/triggers.ts` | Triggers style EMA update on pgvector |
| Write `common/style-service.ts` | `functions/src/common/style-service.ts` | `StyleService` with EMA vector update logic |
| Write connections page | `frontend/app/(dashboard)/settings/connections/page.tsx` | Connect/disconnect LinkedIn, GitHub |

**Phase 2 Gate**: User can save knowledge items, search them semantically. LinkedIn and GitHub accounts connected. Style profile initializes.

---

## 4. Phase 2: Core Product (Weeks 5-8)

**Goal**: Fully functional content generation pipeline. User sees ideas → generates draft → rates draft → system learns their style.

### Week 5: Groq Service + Prompts

| Task | Files | Notes |
|------|-------|-------|
| Write `common/groq.ts` | `functions/src/common/groq.ts` | GroqService: 3 model strategies (Llama 3.3 70B for ideas, Qwen3 32B for drafts, Llama 4 Scout 17B for quality gate). Rate-limit aware. |
| Write prompt template: context aggregator | `functions/src/common/prompts/context-aggregator.ts` | Template string + type-safe `{placeholders}` |
| Write prompt template: idea generator | `functions/src/common/prompts/idea-generator.ts` | |
| Write prompt template: draft composer | `functions/src/common/prompts/draft-composer.ts` | |
| Write prompt template: style refiner | `functions/src/common/prompts/style-refiner.ts` | |
| Write prompt template: quality gate | `functions/src/common/prompts/quality-gate.ts` | |
| Write prompt template: daily brief | `functions/src/common/prompts/daily-brief.ts` | |

### Week 6: Content Pipeline

| Task | Files | Notes |
|------|-------|-------|
| Write `ContentPipeline` class | `functions/src/common/content-pipeline.ts` | Orchestrates 5 stages: context aggregation → idea generation → draft composition → style refinement → quality gate |
| Implement stage 1: context aggregation | `pipeline.ts` | Gather user profile, recent knowledge, recent drafts, trending topics |
| Implement stage 2: idea generation | `pipeline.ts` | Call Groq (Llama 3.3 70B) → parse structured ideas |
| Implement stage 3: draft composition | `pipeline.ts` | Call Groq (Qwen3 32B) → compose full draft |
| Implement stage 4: style refinement | `pipeline.ts` | If style vector exists, call Groq with style context → rewrite to match voice |
| Implement stage 5: quality gate | `pipeline.ts` | Call Groq (Llama 4 Scout 17B) → score draft → pass/warn/fail verdict |
| Handle rate limits | `pipeline.ts` | Rate-limit aware retry with exponential backoff |

### Week 7: Content Functions

| Task | Files | Notes |
|------|-------|-------|
| Write `content-generateIdeas` | `functions/src/content/generateIdeas.ts` | Calls pipeline stages 1+2 |
| Write `content-generateDraft` | `functions/src/content/generateDraft.ts` | Calls pipeline stages 3+4+5 |
| Write `content-updateDraft` | `functions/src/content/updateDraft.ts` | Persists user edits |
| Write `content-regenerateDraft` | `functions/src/content/regenerateDraft.ts` | Pipeline rerun with user feedback |
| Write `content-rateDraft` | `functions/src/content/rateDraft.ts` | Saves rating in Firestore → triggers style update |
| Write `content-schedulePost` | `functions/src/content/schedulePost.ts` | Creates schedule document |
| Write `content-getDraftHistory` | `functions/src/content/getDraftHistory.ts` | Paginated draft list |
| Write draft editor page | `frontend/app/(dashboard)/content/[id]/page.tsx` | Rich text editor, regenerate button, rating UI |
| Write draft feed page | `frontend/app/(dashboard)/content/page.tsx` | Filter by status, sort by date |
| Write draft creation page | `frontend/app/(dashboard)/content/new/page.tsx` | Idea list → select → generate |
| Write idea list component | `frontend/components/content/idea-list.tsx` | Score badges, hover previews |
| Write rating UI | `frontend/components/content/draft-card.tsx` | Star rating per dimension |

**Phase 2 Gate**: User navigates to "New Content" → sees generated ideas → selects one → gets full draft → can edit, regenerate, rate. System learns style from ratings.

---

## 5. Phase 3: Publishing & Analytics (Weeks 9-12)

**Goal**: User can publish to LinkedIn, view post history, see analytics. Daily briefs auto-generate. Backend migrations are clean.

### Week 9: Publishing

| Task | Files | Notes |
|------|-------|-------|
| Write `publish-publishNow` | `functions/src/publish/publishNow.ts` | Reads draft → posts via LinkedIn API → writes result |
| Write `publish-getSchedule` | `functions/src/publish/getSchedule.ts` | Paginated schedule list |
| Write `publish-deleteSchedule` | `functions/src/publish/deleteSchedule.ts` | Cancels scheduled post |
| Write `publish-getPublishHistory` | `functions/src/publish/getPublishHistory.ts` | Published post history |
| Write `processScheduledPosts` worker | `functions/src/worker.ts` | Cloud Scheduler: every 5 min → check `scheduled_worker` → publish if ready |
| Write schedule picker component | `frontend/components/content/schedule-picker.tsx` | Date/time + confirm dialog |
| Write schedule page | `frontend/app/(dashboard)/publish/page.tsx` | Schedule list with status badges |

### Week 10: Analytics + Briefs

| Task | Files | Notes |
|------|-------|-------|
| Write `analytics-getOverview` | `functions/src/analytics/getOverview.ts` | Aggregates recent post metrics |
| Write `analytics-getPostMetrics` | `functions/src/analytics/getPostMetrics.ts` | Single post performance |
| Write `analytics-getAudienceInsights` | `functions/src/analytics/getAudienceInsights.ts` | Follower growth, demographics |
| Write `aggregateDailyAnalytics` worker | `functions/src/worker.ts` | Cloud Scheduler: daily at 2am → roll up metrics |
| Write `briefs-getTodayBrief` | `functions/src/briefs/getTodayBrief.ts` | Generates daily brief (or returns cached) |
| Write `briefs-listBriefs` | `functions/src/briefs/listBriefs.ts` | Recent brief history |
| Write `generateDailyBriefs` worker | `functions/src/worker.ts` | Cloud Scheduler: hourly → check matching `briefHour` → generate |
| Write analytics dashboard page | `frontend/app/(dashboard)/analytics/page.tsx` | Charts, metric cards, post list |
| Write brief page | `frontend/app/(dashboard)/brief/page.tsx` | Today's ideas, context summary |

### Week 11: Admin + Polish

| Task | Files | Notes |
|------|-------|-------|
| Write `admin-getSystemStats` | `functions/src/admin/getSystemStats.ts` | User count, invocations, Groq usage (admin custom claim) |
| Write `admin-forceSync` | `functions/src/admin/forceSync.ts` | Force re-sync user's GitHub/LinkedIn data |
| Error handling audit | All functions | Verify all Zod validation errors surface properly; rate limit responses are helpful; AI errors don't bubble raw provider messages |
| Rate limit tuning | `common/ratelimit.ts` | Adjust per-function rate limits based on actual usage patterns |
| Firestore composite indexes audit | `firestore.indexes.json` | Verify all query patterns are covered; remove unused indexes |
| Security Rules audit | `firestore.rules` | Verify no collection is accessible without auth; verify admin-only collections |
| Frontend error boundaries | `frontend/components/common/error-boundary.tsx` | Wrap each page section with error boundary |
| Loading states | All pages | Skeleton loaders for async data |
| Empty states | All list pages | Informative empty state when no data |

### Week 12: Testing + Launch

| Task | Files | Notes |
|------|-------|-------|
| Write function unit tests | `functions/__tests__/` | Vitest + `firebase-functions-test` emulator |
| Write pipeline tests | `functions/__tests__/common/` | Mock Groq responses, test each stage independently |
| Write integration tests | `functions/__tests__/` | Test function → Firestore → pgvector data flow |
| Write frontend tests | `frontend/__tests__/` | Component tests, page tests |
| Test emulator suite | `scripts/test-emulator.sh` | `firebase emulators:exec` with full test suite |
| Verify Groq + Mistral API keys | Firebase Secrets | Production secrets stored via `firebase functions:secrets:set` |
| Deploy to Firebase | `firebase deploy --only functions` | First production deployment |
| Deploy frontend to Vercel | `vercel --prod` | Connect git repo for auto-deploy |
| Smoke test all features | — | Core paths: signup → profile → knowledge → ideas → draft → rate → schedule → publish → analytics |

**Launch Gate**: All 30 callable functions deployed and tested. User can complete full workflow. All rate limits documented. Monitoring configured.

---

## 6. What Changed from the Python Plan

| Dimension | Python Plan (16 weeks) | Firebase Plan (12 weeks) | Delta |
|-----------|-----------------------|-------------------------|-------|
| **Infrastructure** | W1-2: docker-compose, SQLite, Alembic, Redis, ChromaDB, Minio, custom CI | W1: Firebase CLI init, common modules | -2 weeks |
| **Auth** | W3-4: NextAuth.js, JWT, sessions, password hashing, OAuth providers | W2: Firebase Auth (built-in) | -1 week |
| **Middleware** | Custom CORS, correlation IDs, security headers, rate limiting | W1: Firebase handles CORS/auth; rate limit in one file | -1 week |
| **Workers** | Arq + Redis queue setup, worker Dockerfile | W1: Cloud Scheduler (built-in pubsub) | -1 week |
| **Total** | 16 weeks | 12 weeks | -4 weeks |

### Reused Code

The following are **new code** (no Python equivalent to port):

- `common/groq.ts` — Groq API client (was Anthropic/OpenAI)
- `common/mistral.ts` — Mistral embedding API (was ChromaDB auto-embed)
- `common/content-pipeline.ts` — Pipeline orchestrator (conceptually similar to Python `services/content_engine/pipeline.py`)
- `common/style-service.ts` — EMA vector logic (same concept as Python `services/style/ema.py`)
- All prompt templates (were `.txt` files, now `.ts` template strings)
- All Zod schemas (were Pydantic models — equivalent, different library)
- All function handlers (were FastAPI route handlers — fully different interface)

The prompt templates and pipeline logic are the only true ports. Everything else is a rewrite for the Firebase paradigm.

### Migration Checklist

```
[ ] Week 1: Firebase project created, functions initialized, common modules written
[ ] Week 2: Auth working, profile page renders
[ ] Week 3: Knowledge CRUD + search working
[ ] Week 4: LinkedIn/GitHub connections working, style service initialized
[ ] Week 5: Groq service tested, all prompts written
[ ] Week 6: Content pipeline passing end-to-end tests
[ ] Week 7: Content generation UI fully functional
[ ] Week 8: Rate limiting verified, pipeline handles edge cases
[ ] Week 9: Posting to LinkedIn working, schedule worker tested
[ ] Week 10: Analytics dashboard rendering, daily briefs generating
[ ] Week 11: Admin functions working, polish pass complete
[ ] Week 12: All tests green, deployed to production, smoke test passed
```

---

*This implementation plan replaces the original 16-week Python-based plan. The Firebase stack reduces build time by 4 weeks through managed infrastructure (auth, database, queues) while leaving the core content pipeline — BrandOS's differentiator — as the main development effort.*
