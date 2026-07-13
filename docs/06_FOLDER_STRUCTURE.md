# Folder Structure: BrandOS (Firebase Monorepo)

## Document Info

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Created** | 2026-07-14 |
| **Platform** | Firebase Cloud Functions (TypeScript) + Next.js (Vercel) |
| **Stack** | Monorepo with functions/ + frontend/ |

---

## Table of Contents

- [Overview](#1-overview)
- [Top-Level Layout](#2-top-level-layout)
- [Root Files](#3-root-files)
- [`functions/` — Firebase Cloud Functions](#4-functions--firebase-cloud-functions)
- [`frontend/` — Next.js Frontend](#5-frontend--nextjs-frontend)
- [`supabase/` — pgvector Migrations](#6-supabase--pgvector-migrations)
- [`docs/` — Architecture & Design](#7-docs--architecture--design)
- [Service Boundary Rules](#8-service-boundary-rules)
- [What Changed from the Python Stack](#9-what-changed-from-the-python-stack)

---

## 1. Overview

BrandOS uses a **monorepo** with two deployable units:

| Unit | Platform | Language | Deploy Target |
|------|----------|----------|---------------|
| **Cloud Functions** | Firebase | TypeScript | Firebase Cloud Functions (us-central1) |
| **Frontend** | Next.js | TypeScript | Vercel |

The old Python FastAPI backend (`backend/`) is deprecated. All server logic now lives in Firebase Cloud Functions.

### Design Rules

1. **One domain = one function file.** Each service group (profile, knowledge, content, etc.) is a single named export file, not a subpackage.
2. **Shared infrastructure lives in `common/`.** AI clients, Firestore helpers, error classes, Zod schemas — all in `functions/src/common/`.
3. **Prompts are TypeScript template strings in `.ts` files.** Each prompt system gets a file in `common/prompts/`.
4. **Function calls replace HTTP routes.** The frontend invokes functions via `httpsCallable`, not `fetch`.
5. **Firestore calls are direct SDK; pgvector calls go through `supabase-js`.** No ORM, no query builder abstraction.
6. **Tests mirror source structure.** `__tests__/` mirrors `src/` exactly.
7. **Frontend uses Firebase SDK directly.** No BFF proxy layer — Firebase handles auth and CORS.

---

## 2. Top-Level Layout

```
brand-os/
├── .github/
├── functions/          ← Firebase Cloud Functions (all server logic)
│   ├── src/
│   └── ...
├── frontend/           ← Next.js 14+ App Router
│   ├── app/
│   ├── lib/
│   └── ...
├── supabase/           ← pgvector SQL migrations
│   └── migrations/
├── docs/               ← Architecture, design, planning docs
├── scripts/            ← Dev utility scripts
├── firebase.json       ← Firebase project config
├── .firebaserc         ← Firebase project alias
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Root Files

| File | Purpose |
|------|---------|
| `firebase.json` | Firebase hosting, functions, Firestore indexes configuration |
| `.firebaserc` | Firebase project alias (default: `brand-os-prod`) |
| `.env.example` | All environment variables with dummy values |
| `.gitignore` | `node_modules/`, `.next/`, `.env`, `lib/` (compiled functions), `*.tsbuildinfo` |
| `README.md` | Project overview, quick start, links to docs |

### firebase.json

```json
{
  "functions": {
    "source": "functions",
    "codebase": "default",
    "ignore": [
      "node_modules",
      ".git",
      "*.test.ts",
      "__tests__"
    ]
  },
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "emulators": {
    "functions": {
      "port": 5001
    },
    "firestore": {
      "port": 8080
    },
    "auth": {
      "port": 9099
    },
    "ui": {
      "enabled": true,
      "port": 4000
    }
  }
}
```

---

## 4. `functions/` — Firebase Cloud Functions

### 4.1 Top-Level Layout

```
functions/
├── src/
│   ├── index.ts               ← Function registry: exports all callable functions
│   ├── triggers.ts             ← Firestore/auth triggers (onCreate, onUpdate)
│   ├── worker.ts               ← Scheduled functions (Cloud Scheduler)
│   ├── profile/
│   │   ├── getMyProfile.ts
│   │   ├── updateMyProfile.ts
│   │   └── updateMyPreferences.ts
│   ├── knowledge/
│   │   ├── createItem.ts
│   │   ├── getItem.ts
│   │   ├── updateItem.ts
│   │   ├── deleteItem.ts
│   │   └── search.ts
│   ├── content/
│   │   ├── generateIdeas.ts
│   │   ├── generateDraft.ts
│   │   ├── updateDraft.ts
│   │   ├── regenerateDraft.ts
│   │   ├── rateDraft.ts
│   │   ├── schedulePost.ts
│   │   └── getDraftHistory.ts
│   ├── publish/
│   │   ├── publishNow.ts
│   │   ├── getSchedule.ts
│   │   ├── deleteSchedule.ts
│   │   └── getPublishHistory.ts
│   ├── analytics/
│   │   ├── getOverview.ts
│   │   ├── getPostMetrics.ts
│   │   └── getAudienceInsights.ts
│   ├── briefs/
│   │   ├── getTodayBrief.ts
│   │   └── listBriefs.ts
│   ├── connections/
│   │   ├── connectLinkedIn.ts
│   │   ├── connectGitHub.ts
│   │   ├── getConnectionStatus.ts
│   │   └── disconnect.ts
│   ├── admin/
│   │   ├── getSystemStats.ts
│   │   └── forceSync.ts
│   ├── common/
│   │   ├── firebase.ts          ← Admin SDK initialization
│   │   ├── supabase.ts          ← Supabase client (service_role)
│   │   ├── errors.ts            ← AppError hierarchy
│   │   ├── logger.ts            ← Structured logging
│   │   ├── ratelimit.ts         ← In-memory + Firestore rate limiter
│   │   ├── validation.ts        ← Zod schema re-exports and helpers
│   │   ├── types.ts             ← Shared TypeScript types (ContentType, ContentTone, etc.)
│   │   ├── groq.ts              ← GroqService (3 model endpoints)
│   │   ├── mistral.ts           ← MistralService (embeddings)
│   │   ├── supabase.ts          ← Supabase service_role client
│   │   ├── linkedin.ts          ← LinkedIn API client (OAuth + posting)
│   │   ├── github.ts            ← GitHub API client (commits/repos)
│   │   ├── content-pipeline.ts  ← ContentPipeline orchestrator class
│   │   ├── style-service.ts     ← StyleService (EMA vector logic)
│   │   └── prompts/             ← Prompt templates (one file per prompt system)
│   │       ├── idea-generator.ts
│   │       ├── draft-composer.ts
│   │       ├── style-refiner.ts
│   │       ├── quality-gate.ts
│   │       ├── context-aggregator.ts
│   │       └── daily-brief.ts
│   └── schemas/                 ← Zod schemas (one file per domain)
│       ├── profile.ts
│       ├── knowledge.ts
│       ├── content.ts
│       ├── publish.ts
│       ├── analytics.ts
│       ├── briefs.ts
│       ├── connections.ts
│       └── common.ts            ← Pagination, error response shapes
├── __tests__/
│   ├── profile/
│   ├── knowledge/
│   ├── content/
│   ├── publish/
│   ├── analytics/
│   ├── briefs/
│   ├── connections/
│   └── common/                  ← Tests for pipeline, style service, AI clients
├── package.json
├── tsconfig.json
└── .eslintrc.js
```

### 4.2 Function Registry (`src/index.ts`)

```
index.ts
├── onCall("profile-getMyProfile")          → profile/getMyProfile
├── onCall("profile-updateMyProfile")       → profile/updateMyProfile
├── onCall("profile-updateMyPreferences")   → profile/updateMyPreferences
├── onCall("knowledge-createItem")          → knowledge/createItem
├── onCall("knowledge-getItem")             → knowledge/getItem
├── onCall("knowledge-updateItem")          → knowledge/updateItem
├── onCall("knowledge-deleteItem")          → knowledge/deleteItem
├── onCall("knowledge-search")              → knowledge/search
├── onCall("content-generateIdeas")         → content/generateIdeas
├── onCall("content-generateDraft")         → content/generateDraft
├── onCall("content-updateDraft")           → content/updateDraft
├── onCall("content-regenerateDraft")       → content/regenerateDraft
├── onCall("content-rateDraft")             → content/rateDraft
├── onCall("content-schedulePost")          → content/schedulePost
├── onCall("content-getDraftHistory")       → content/getDraftHistory
├── onCall("publish-publishNow")            → publish/publishNow
├── onCall("publish-getSchedule")           → publish/getSchedule
├── onCall("publish-deleteSchedule")        → publish/deleteSchedule
├── onCall("publish-getPublishHistory")     → publish/getPublishHistory
├── onCall("analytics-getOverview")         → analytics/getOverview
├── onCall("analytics-getPostMetrics")      → analytics/getPostMetrics
├── onCall("analytics-getAudienceInsights") → analytics/getAudienceInsights
├── onCall("briefs-getTodayBrief")          → briefs/getTodayBrief
├── onCall("briefs-listBriefs")             → briefs/listBriefs
├── onCall("connections-connectLinkedIn")   → connections/connectLinkedIn
├── onCall("connections-connectGitHub")     → connections/connectGitHub
├── onCall("connections-getConnectionStatus") → connections/getConnectionStatus
├── onCall("connections-disconnect")        → connections/disconnect
├── onCall("admin-getSystemStats")          → admin/getSystemStats
├── onCall("admin-forceSync")               → admin/forceSync
```

### 4.3 Function Structure (per file)

```
functions/src/content/generateDraft.ts

export const generateDraft = onCall<GenerateDraftInput, DraftResponse>(
  { cors: false },                       // CORS handled by Firebase
  async (request) => {
    const uid = request.auth!.uid;       // Auto-authenticated
    const input = generateDraftSchema.parse(request.data);

    // Orchestrate pipeline
    const pipeline = new ContentPipeline(uid);
    const result = await pipeline.run(input);

    return { success: true, data: result };
  }
);
```

### 4.4 Triggers (`src/triggers.ts`)

```
functions/src/triggers.ts

exports.onUserCreate = functions.auth.user().onCreate(async (user) => {
  // Create Firestore user document
  // Initialize pgvector style_vector row
});

exports.onKnowledgeWritten = functions.firestore
  .document('users/{uid}/knowledge/{itemId}')
  .onWrite(async (change, context) => {
    // On create/update: generate embedding via Mistral → upsert pgvector
    // On delete: remove from pgvector
  });

exports.onDraftRated = functions.firestore
  .document('users/{uid}/drafts/{draftId}')
  .onUpdate(async (change, context) => {
    // If userRating was added: update style EMA vector in pgvector
  });
```

### 4.5 Workers (`src/worker.ts`)

```
functions/src/worker.ts

// Daily brief generation — runs at each user's configured briefHour
exports.generateDailyBriefs = functions.pubsub
  .schedule('every 1 hours')
  .onRun(async () => {
    // Query users whose briefHour matches current hour
    // For each user: generate brief → write to Firestore
  });

// Scheduled post publishing — runs every 5 minutes
exports.processScheduledPosts = functions.pubsub
  .schedule('every 5 minutes')
  .onRun(async () => {
    // Query scheduled_worker for pending/ready jobs
    // Execute publish via LinkedIn API
    // Update schedule document status
  });

// Analytics daily aggregation
exports.aggregateDailyAnalytics = functions.pubsub
  .schedule('0 2 * * *')  // 2am daily
  .onRun(async () => {
    // Aggregate daily metrics → write analytics_daily
  });
```

---

## 5. `frontend/` — Next.js Frontend

### 5.1 Layout

The frontend structure stays mostly unchanged from the existing codebase, with two key changes:
- No `app/api/` BFF routes — all API calls go via `firebase/functions` SDK
- Firebase Auth replaces NextAuth.js

```
frontend/
├── public/                       # Static assets
├── app/                          # Next.js App Router pages
│   ├── layout.tsx                # Root layout with Firebase Provider
│   ├── page.tsx                  # Landing page
│   ├── (auth)/                   # Auth route group
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── oauth-callback/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/              # Dashboard route group
│   │   ├── dashboard/page.tsx
│   │   ├── content/
│   │   │   ├── page.tsx
│   │   │   ├── [id]/page.tsx     # Draft editor
│   │   │   └── new/page.tsx      # Idea → Draft generation
│   │   ├── analytics/page.tsx
│   │   ├── knowledge-base/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   ├── settings/
│   │   │   ├── page.tsx
│   │   │   └── connections/page.tsx
│   │   ├── brief/page.tsx
│   │   └── layout.tsx
│   └── error.tsx
├── components/
│   ├── ui/                       # Design system (Button, Input, Card, etc.)
│   ├── layout/                   # Sidebar, topnav, auth-guard
│   ├── forms/
│   ├── content/                  # Draft editor, draft card, idea list, schedule picker
│   ├── analytics/                # Charts, metric cards
│   └── common/                   # Empty state, error boundary, loading skeleton
├── lib/
│   ├── firebase.ts               ← Firebase app initialization
│   ├── api.ts                    ← Typed httpsCallable wrappers (function invocations)
│   ├── auth.ts                   ← Firebase Auth context + hooks (useAuth)
│   ├── utils.ts                  ← cn(), formatters, date helpers
│   └── constants.ts
├── hooks/
│   ├── use-auth.ts
│   ├── use-content.ts
│   ├── use-analytics.ts
│   └── use-knowledge.ts
├── stores/                       ← Zustand (if needed)
│   ├── auth-store.ts
│   └── ui-store.ts
├── styles/
│   └── globals.css
├── types/
│   ├── api.ts                    ← Mirrors functions/src/common/types
│   ├── content.ts
│   └── analytics.ts
├── __tests__/
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── ...
```

### 5.2 Key Frontend Files

| File | Purpose |
|------|---------|
| `lib/firebase.ts` | `initializeApp`, `getFunctions`, `getAuth` — connects to Firebase project |
| `lib/api.ts` | Typed `createCallable<TInput, TOutput>` wrappers for every Cloud Function |
| `lib/auth.ts` | `useAuth()` hook wrapping `onAuthStateChanged`, sign-in/sign-up/sign-out helpers |
| `components/layout/auth-guard.tsx` | Redirects unauthenticated users to `/login` |

### 5.3 API Client Pattern (`lib/api.ts`)

```typescript
import { getFunctions, httpsCallable } from 'firebase/functions';
import { functions } from './firebase';

function createCallable<TInput, TOutput>(name: string) {
  const fn = httpsCallable<TInput, { success: boolean; data: TOutput }>(functions, name);
  return async (input: TInput): Promise<TOutput> => {
    const result = await fn(input);
    if (!result.data.success) throw new Error(`API error: ${name}`);
    return result.data.data;
  };
}

export const api = {
  getMyProfile: createCallable<{}, ProfileResponse>('profile-getMyProfile'),
  searchKnowledge: createCallable<SearchInput, SearchOutput>('knowledge-search'),
  generateDraft: createCallable<GenerateDraftInput, DraftResponse>('content-generateDraft'),
  // ... every function gets a typed wrapper
};
```

---

## 6. `supabase/` — pgvector Migrations

```
supabase/
└── migrations/
    ├── 001_enable_pgvector.sql
    ├── 002_create_knowledge_embeddings.sql
    ├── 003_create_style_vectors.sql
    ├── 004_create_match_knowledge_rpc.sql
    └── README.md                 ← Apply instructions
```

Migrations are applied via `supabase db push` or manually in the Supabase SQL editor.

---

## 7. `docs/` — Architecture & Design

```
docs/
├── 01_REQUIREMENTS.md
├── 02_SYSTEM_ARCHITECTURE.md     ← Firebase stack architecture, C4 diagrams, costs
├── 03_LOW_LEVEL_DESIGN.md        ← Zod schemas, function interfaces, pipeline design
├── 04_API_SPEC.md                ← Callable function specifications
├── 05_DATABASE.md                ← Firestore collections + pgvector schema
├── 06_FOLDER_STRUCTURE.md        ← This file
├── 07_IMPLEMENTATION_PLAN.md     ← Phased migration plan
└── AGENTS.md                     ← AI assistant instructions
```

---

## 8. Service Boundary Rules

### Function-to-Function Calls

Functions should not call each other directly. Shared logic is extracted to `common/`:

```
functions/src/
├── index.ts
├── content/
│   ├── generateDraft.ts         ← Calls common/content-pipeline.ts (shared orchestration)
│   └── regenerateDraft.ts       ← Also calls common/content-pipeline.ts
├── common/
│   ├── content-pipeline.ts      ← Shared pipeline logic used by multiple functions
│   ├── style-service.ts         ← Shared style EMA logic
│   └── groq.ts                  ← LLM client (used by content + analytics + briefs)
```

### Import Rules

```
functions/src/
├── profile/getMyProfile.ts      → imports from common/{firebase, errors}
├── knowledge/search.ts          → imports from common/{firebase, supabase, mistral, errors}
├── content/generateDraft.ts     → imports from common/{content-pipeline, errors, schemas}
├── content/pipeline.ts          → imports from common/{groq, style-service, prompts/*}
└── common/*                     → imports only npm packages, not src/*
```

### Trigger → Function Boundary

```
Firestore Document Write → triggers.ts (onKnowledgeWritten)
                                → common/supabase.ts (embedding upsert)

Firebase Auth User Create → triggers.ts (onUserCreate)
                                → creates Firestore document
                                → creates pgvector style_vector row
```

---

## 9. What Changed from the Python Stack

| Area | Old (Python) | New (TypeScript) | Reason |
|------|-------------|-------------------|--------|
| **Server framework** | FastAPI + uvicorn | Firebase Cloud Functions (`onCall`) | Serverless removes ops burden; native Firebase Auth integration |
| **Function units** | Router files in `api/v1/` | Individual function files in `src/{domain}/` | Each function is independent; no shared middleware stack |
| **Shared infrastructure** | `core/` (cache, db, llm, queue) | `common/` (firebase, supabase, groq, mistral, errors) | Firebase eliminates need for custom cache/db/queue abstractions |
| **Prompts** | `/prompts/*.txt` (flat files, loaded at runtime) | `common/prompts/*.ts` (TypeScript template strings) | One language; no file I/O overhead; type-safe placeholders |
| **Models** | `models/` SQLAlchemy ORM | Zod schemas in `schemas/` | Validation-only; Firestore is schemaless |
| **Workers** | Arq (Redis-backed) | `functions.pubsub.schedule()` | Native Firebase Cloud Scheduler; no Redis dependency |
| **Database** | SQLite + Alembic + ChromaDB | Firestore + pgvector (Supabase) | Fully managed; no file-based storage; pgvector on existing Supabase |
| **Auth** | NextAuth.js + JWT + FastAPI session | Firebase Auth + ID tokens | Single auth provider; auto-verified by Cloud Functions |
| **API client** | `fetch` → BFF proxy → FastAPI | `httpsCallable` → function name | Type-safe; auto-auth; no CORS concerns |
| **CI/CD** | GitHub Actions + Render deploy | `firebase deploy --only functions` + Vercel | Simpler deployment; managed hosting handles rollback |
| **Tests** | `pytest` + httpx (async) | Vitest + `firebase-functions-test` | Language-native testing; emulator support |
| **Middleware** | Custom (CORS, correlation ID, rate limit, security headers) | Firebase SDK handles auth, CORS; rate limit in `common/ratelimit.ts` | Zero boilerplate for auth/CORS; only rate limiting is custom |
| **Docker** | Multi-stage Dockerfiles + docker-compose | None | Firebase is serverless; no containers to manage |

---

*This document defines the folder structure for the BrandOS Firebase monorepo. Two deployable units (Cloud Functions + Next.js frontend) with clean separation of concerns. The old `backend/` Python directory is deprecated and will be removed once all functions are migrated.*
