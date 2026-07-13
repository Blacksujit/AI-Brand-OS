# System Architecture: BrandOS

## Document Info

| Field | Value |
|-------|-------|
| **Author** | Architecture Team |
| **Status** | Draft |
| **Created** | 2026-07-14 |
| **Last Updated** | 2026-07-14 |
| **Stack** | Firebase + Vercel + Open-Source AI |
| **Target Release** | Q4 2026 |

---

## Table of Contents

- [Architectural Principles](#1-architectural-principles)
- [Technology Decisions](#2-technology-decisions)
- [High Level Architecture](#3-high-level-architecture)
- [Component Architecture](#4-component-architecture)
- [Content Generation Pipeline](#5-content-generation-pipeline)
- [Sequence Diagrams](#6-sequence-diagrams)
- [Memory Architecture](#7-memory-architecture)
- [Knowledge Flow](#8-knowledge-flow)
- [Security Architecture](#9-security-architecture)
- [Caching Strategy](#10-caching-strategy)
- [Deployment Architecture](#11-deployment-architecture)
- [Scalability Path](#12-scalability-path)
- [Cost Analysis](#13-cost-analysis)
- [Decision Log](#14-decision-log)

---

## 1. Architectural Principles

### 1.1 Core Principles

| Principle | Rationale |
|-----------|-----------|
| **Clean Architecture** | Domain logic is independent of Firebase, Vercel, and AI providers. Content engine, style learner, and knowledge base are pure TypeScript with injected adapters. |
| **Event-Driven Core** | Content generation, brief creation, and analytics are async workflows triggered by Firestore events or Cloud Tasks. Synchronous only for user-facing CRUD (profiles, drafts, settings). |
| **Human-in-the-Loop** | AI never publishes without explicit human approval. Content pipeline produces drafts; humans approve. This is enforced at the application layer, not the UI layer. |
| **Provider Abstraction** | LLM providers (Groq, Mistral, future) are behind a common interface. Selection is configurable per user and per task. No coupling to any single provider. |
| **Data as Moat** | User style profiles, voice fingerprints, and knowledge graphs are the defensible asset. Stored in Firestore under the user's document. Never used for model training. |
| **Platform-Agnostic Core** | Content engine produces canonical content objects. Platform adapters (LinkedIn, X, blog) convert to platform-specific formats. Adding a platform means one adapter file. |
| **Serverless by Default** | Every function scales independently. No long-running servers. Firestore triggers replace polling. Cloud Tasks replace cron workers. |
| **Minimal Dependencies** | Each Cloud Function has a specific purpose. No shared state between function invocations. Stateless design enables independent scaling. |

### 1.2 Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Backend Runtime** | Firebase Cloud Functions (TypeScript) | Serverless, scales to zero, integrated with Firestore and Auth. No server management. Free tier: 2M invocations/month on Blaze. TypeScript gives type safety for LLM data contracts. |
| **Frontend** | Next.js 14+ (App Router) → Vercel | SSR for content-rich pages. Firebase Client SDK for auth/firestore. Vercel AI SDK for streaming LLM responses. Existing frontend stack is already Next.js. |
| **Primary Database** | Firestore (NoSQL) | Serverless, real-time capable, integrates with Cloud Functions triggers. Subcollections match our data hierarchy (user → knowledge → drafts → schedule). No managed DB server. |
| **Vector Store** | Supabase pgvector | Already has Supabase client installed. pgvector provides HNSW indexing for sub-100ms similarity search. Free tier: 500MB database, 5K rows. Separate from Firestore for independent scaling. |
| **Auth** | Firebase Auth | Built-in support for email/password, Google, GitHub OAuth. Handles token lifecycle, refresh, session management. Free tier: 50K MAU. |
| **Object Storage** | Firebase Cloud Storage | Serverless file storage with Firestore integration. Blaze plan: 5GB free, then $0.026/GB. Used for draft history exports, user uploads. |
| **LLM Inference** | Groq API (free tier) | Llama 3.3 70B, Qwen3 32B, Llama 4 Scout 17B, DeepSeek R1 Distill 70B. All open-source. Free tier: 30 RPM, 14.4K RPD, no credit card required. OpenAI-compatible API — drop-in with Vercel AI SDK. |
| **Embeddings API** | Mistral AI (free tier) | `mistral-embed` model. 1B tokens/month free. OpenAI-compatible. No credit card required. Cheaper and simpler than running local ONNX models in Cloud Functions. |
| **Async Jobs** | Firebase Cloud Tasks + `onSchedule` Functions | Cloud Tasks handle retries, backoff, and scheduling for content generation jobs. `firebase-functions` v2 `onSchedule` replaces cron for daily briefs. |
| **Secrets Management** | Firebase Cloud Secret Manager (via `defineSecret`) | Managed secrets for Groq API key, Mistral API key, LinkedIn OAuth client secret. Auto-injected into function environment. |

### 1.3 Why Not...

| Option | Why Not |
|--------|---------|
| **Python FastAPI backend** | Requires managing a server (Render, Fly, K8s). Cloud Functions eliminate server management. TypeScript lets frontend+backend share types. |
| **PostgreSQL directly** | Serverless PostgreSQL (Neon, Supabase) would work, but Firestore's real-time triggers, Auth integration, and security rules reduce backend code by ~40%. |
| **SQLite** | Single-file database doesn't scale beyond single-server. Cloud Functions are stateless — no local file persistence between invocations. |
| **ChromaDB** | Requires running a separate process. Supabase pgvector has a free tier and integrates with PostgreSQL queries for hybrid search. |
| **Anthropic/OpenAI** | Paid per-token. Groq's LPU hardware provides faster inference than cloud GPUs for most open-source models — at zero API cost on the free tier. |
| **Redis for cache** | Firestore's built-in caching via `getCountFromServer`, `getAggregateFromServer`, and client-side caching with `{source: 'cache'}` eliminates the need for a separate cache layer at MVP scale. Add Redis-only if latency becomes an issue for brief retrieval. |
| **Server-side session** | Firebase Auth handles sessions client-side with ID tokens. No server-side session store needed. |
| **Monolith service layer** | Cloud Functions are naturally function-grained. Encapsulating logic into a few well-structured functions avoids function sprawl while staying deployable. |

---

## 2. Technology Decisions

### 2.1 Firebase vs. Alternative Backend

| Requirement | Firebase | Alternative (FastAPI + Render) |
|-------------|----------|-------------------------------|
| **Auth** | Built-in (50K MAU free) | Auth0 or Clerk ($200-500/mo at scale) |
| **Database** | Firestore (NoSQL, triggers) | Managed Postgres ($15-50/mo) |
| **Compute** | Cloud Functions (2M invocations free) | Render web service ($7-25/mo) |
| **Storage** | Cloud Storage (5GB free, Blaze) | S3-compatible ($0.023/GB) |
| **Async Jobs** | Cloud Tasks + onSchedule | Celery/Arq + Redis ($15-30/mo) |
| **Operational Cost (MVP)** | ~$0/mo (Blaze with free usage) | ~$30-100/mo |
| **Scaling** | Automatic, serverless | Manual scaling or auto-scaling groups |
| **Cold Start** | ~500ms-2s for Node.js functions | N/A (always-on server) |
| **Migration Path** | Firestore → Firestore (same) | SQLite → Postgres (schema migration) |

Firebase wins for MVP because **operational cost is near-zero** while delivering auth, database, compute, and storage in one platform. The trade-off is Firestore's NoSQL query limitations and cold start latency — both addressed through careful schema design and function warmup.

### 2.2 Groq vs. Other Free AI Providers

| Provider | Free Tier | Models | Limits | Credit Card |
|----------|-----------|--------|--------|-------------|
| **Groq** | Yes | Llama 3.3 70B, Qwen3 32B, Llama 4 Scout 17B, DeepSeek R1 Distill 70B, Mixtral 8x7B | 30 RPM, 6K TPM, ~14.4K RPD | No |
| **Mistral AI** | Yes | Mistral Small/Large, `mistral-embed` (1B tok/mo) | 1B tokens/month (all models) | No |
| **Together AI** | No | Llama 3.3, Mixtral, DeepSeek | $5 minimum deposit | Yes |
| **OpenRouter** | Yes | 30+ free models (limited RPM) | Varies per model | No |
| **Cloudflare Workers AI** | Yes | Llama 3.1 8B, Qwen 1.5, embeddings | 10K neurons/day | No |
| **GitHub Models** | Yes | Llama 3, Phi-3, Mistral | 50-150 requests/day | No |
| **Google Gemini API** | Yes | Gemini 1.5 Flash/Pro | 60 RPM (Flash), 1M context | No |

**Decision:** Groq for generation (best latency with LPU hardware, generous rate limits) + Mistral AI for embeddings (1B tokens/month free, dedicated embedding model). Both are OpenAI-compatible, so Vercel AI SDK works with zero adapter code.

### 2.3 Firestore vs. Postgres for Content Data

Firestore is chosen over Postgres for the primary data layer because:

1. **Serverless triggers** — Cloud Functions fire on Firestore document writes. This eliminates the need for a message queue for many workflows: "when user saves knowledge item → generate embedding" is a Firestore trigger, not a separate job.
2. **Real-time by default** — `onSnapshot` listeners on the client mean the dashboard, brief queue, and content calendar update in real-time without WebSocket infrastructure.
3. **Security Rules** — Access control is declarative at the document level. "User can only read their own drafts" is a 5-line rules file, not middleware code.
4. **No schema migrations** — NoSQL schemas evolve with the application. New fields are added on write, not via ALTER TABLE.

The cost: complex queries (JOINs, GROUP BY, aggregate reporting) require Cloud Functions or a separate analytics pipeline. This is acceptable for MVP — simple queries go to Firestore directly; complex analytics use a nightly aggregation function.

### 2.4 Supabase pgvector for Embeddings

Firestore lacks native vector similarity search. Supabase pgvector fills this gap:

- **Integration** — Supabase client is already installed in the frontend (`@supabase/supabase-js`). Cloud Functions use it server-side with service role key.
- **Free tier** — 500MB database, row-level security, API auto-generated from schema.
- **Cross-reference** — pgvector stores a `user_id` column alongside each embedding vector. This enables user-scoped vector search without per-user indexes.
- **Hybrid search** — Supabase integrates pgvector with Postgres full-text search for keyword + semantic hybrid retrieval (RRF).

Data flow: Firestore triggers a Cloud Function → Mistral Embeddings API → pgvector upsert.

---

## 3. High Level Architecture

### 3.1 System Context

```mermaid
C4Context
  title System Context Diagram — BrandOS (Firebase Stack)

  Person(user, "Technical Professional", "AI engineer, researcher, founder, or creator")

  System(brandos, "BrandOS", "AI-powered Personal Brand Operating System")

  System_Ext(firebase, "Firebase Platform", "Auth, Firestore, Cloud Functions, Storage")
  System_Ext(vercel, "Vercel", "Frontend hosting, serverless edge")
  System_Ext(groq, "Groq API", "Free open-source LLM inference (Llama 3.3, Qwen3)")
  System_Ext(mistral, "Mistral AI", "Free embedding API (mistral-embed)")
  System_Ext(supabase, "Supabase pgvector", "Vector similarity search")
  System_Ext(linkedin, "LinkedIn API", "Social platform for professional content")
  System_Ext(github, "GitHub API", "Code hosting platform")

  Rel(user, brandos, "Creates and manages content")
  Rel(brandos, firebase, "Auth, DB, Compute, Storage")
  Rel(brandos, vercel, "Serves frontend")
  Rel(brandos, groq, "Generates drafts, ideas, summaries")
  Rel(brandos, mistral, "Generates text embeddings")
  Rel(brandos, supabase, "Stores and queries vectors")
  Rel(brandos, linkedin, "Posts content, reads analytics")
  Rel(brandos, github, "Reads repos, commits, PRs")
```

### 3.2 Container Architecture

```mermaid
C4Container
  title Container Diagram — BrandOS (Firebase Stack)

  Person(user, "Technical Professional")

  System_Boundary(brandos, "BrandOS Platform") {
    Container(web, "Next.js App", "TypeScript, React, Tailwind", "SSR web app hosted on Vercel. Firebase client SDK for auth + Firestore reads. Vercel AI SDK for streaming LLM calls.")
    Container(auth, "Firebase Auth", "Managed Service", "Email/password, Google OAuth, GitHub OAuth. Handles token lifecycle, refresh, session.")
    Container(firestore, "Firestore", "NoSQL Database", "Primary data store. Users, profiles, knowledge base, drafts, schedule, briefs. Realtime via onSnapshot.")
    Container(functions, "Cloud Functions", "TypeScript, Node.js 20", "HTTP callable functions, Firestore triggers, scheduled functions. 7 function groups.")

    System_Boundary(agents, "AI Agent Layer") {
      Container(content_agent, "Content Agent", "TypeScript", "Orchestrates context gathering → idea generation → draft composition → style refinement → quality gate. 5-stage pipeline.")
      Container(brief_agent, "Brief Agent", "TypeScript", "Aggregates GitHub activity + KB + trends → ranks ideas → builds daily brief. Scheduled via onSchedule.")
      Container(style_agent, "Style Agent", "TypeScript", "Maintains EMA style profile per user. Learns from ratings, edits, approvals. No LLM calls — purely algorithmic.")
      Container(trend_agent, "Trend Agent", "TypeScript", "RSS feed scraping. Hacker News, Reddit, ArXiv, curated tech newsletters. Relevance scoring per user expertise.")
    }

    ContainerDb(storage, "Cloud Storage", "Object Storage", "Draft revision history, user uploads, exported content. 5GB free on Blaze plan.")
    ContainerDb(vectors, "Supabase pgvector", "Vector Database", "Knowledge embeddings, style vectors, content similarity search. HNSW indexes for sub-100ms queries.")
    ContainerDb(tasks, "Cloud Tasks", "Async Job Queue", "Content generation jobs, scheduled posts. Retry with exponential backoff.")
  }

  System_Ext(groq_api, "Groq API", "Llama 3.3 70B, Qwen3 32B, Llama 4 Scout 17B, Mixtral 8x7B")
  System_Ext(mistral_api, "Mistral AI", "mistral-embed model")
  System_Ext(linkedin_api, "LinkedIn API")
  System_Ext(github_api, "GitHub API")

  Rel(user, web, "HTTPS", "Browser")
  Rel(web, auth, "Firebase Auth SDK", "Client-side auth")
  Rel(web, firestore, "Firebase SDK", "Read/write documents")
  Rel(web, functions, "callable()", "Invoke backend logic")
  Rel(web, groq_api, "Vercel AI SDK", "Streaming draft generation (user-initiated)")

  Rel(functions, firestore, "Admin SDK", "Read/write triggers")
  Rel(functions, groq_api, "Vercel AI SDK", "Token-efficient batch generation")
  Rel(functions, mistral_api, "Fetch API", "Generate embeddings on KB write")
  Rel(functions, vectors, "@supabase/supabase-js", "Upsert/query vectors")
  Rel(functions, github_api, "Octokit", "Repo analysis")
  Rel(functions, linkedin_api, "Fetch API", "Publish + analytics poll")
  Rel(functions, tasks, "Cloud Tasks client", "Enqueue async work")
  Rel(functions, storage, "Admin SDK", "Store/retrieve blobs")
```

### 3.3 Cloud Function Groups

```mermaid
flowchart TB
  subgraph HTTP["HTTP-Callable Functions (onCall)"]
    PROFILE["profile\n· get/set profile\n· preferences\n· expertise areas"]
    KB["knowledgeBase\n· CRUD items\n· hybrid search\n· tags"]
    CONTENT["content\n· generate ideas\n· generate draft\n· schedule post\n· rate/approve"]
    PUBLISH["publish\n· post to LinkedIn\n· schedule\n· history"]
    ANALYTICS["analytics\n· overview\n· engagement\n· audience growth"]
    BRIEF["brief\n· get today's brief\n· list history"]
  end

  subgraph TRIGGER["Firestore Triggers (onDocumentWritten)"]
    KB_EMBED["onKbItemWrite\n· generate embedding\n· upsert to pgvector"]
    SCHEDULE_PUB["onScheduleWrite\n· enqueue publish job\n· validate tokens"]
    STYLE_UPDATE["onDraftRating\n· update style profile\n· EMA recalculation"]
  end

  subgraph SCHEDULED["Scheduled Functions (onSchedule)"]
    DAILY_BRIEF["generateDailyBriefs\n· every 6 hours\n· batch all active users"]
    GITHUB_SYNC["syncGitHubActivity\n· every 6 hours\n· poll repos for active users"]
    TREND_SYNC["syncTrendingTopics\n· every 3 hours\n· RSS + HN + Reddit"]
    LI_ANALYTICS["syncLinkedInAnalytics\n· every 12 hours\n· poll engagement data"]
    CLEANUP["cleanupExpiredTokens\n· every 24 hours\n· revoke stale tokens"]
  end

  subgraph TASKS["Cloud Tasks (Async Jobs)"]
    GEN_DRAFT["generateDraftTask\n· 30s timeout\n· 3 retries"]
    PUBLISH_POST["publishPostTask\n· 15s timeout\n· 5 retries, exponential backoff"]
    ANALYZE_STYLE["analyzeStyleTask\n· 10s timeout\n· 1 retry"]
  end

  PROFILE --> firestore[(Firestore)]
  KB --> firestore
  KB -->|hybrid search| vectors[(Supabase pgvector)]
  CONTENT --> firestore
  CONTENT -->|enqueue| GEN_DRAFT
  CONTENT -->|style profile| STYLE_UPDATE
  PUBLISH -->|enqueue| PUBLISH_POST
  PUBLISH --> firestore
  ANALYTICS --> firestore
  BRIEF -->|read cached| firestore

  KB_EMBED --> mistral_api[Mistral Embeddings API]
  KB_EMBED --> vectors

  GEN_DRAFT --> groq_api[Groq API]
  PUBLISH_POST --> linkedin_api[LinkedIn API]

  DAILY_BRIEF --> GEN_DRAFT
  DAILY_BRIEF --> firestore
  GITHUB_SYNC --> github_api[GitHub API]
  GITHUB_SYNC --> firestore
  TREND_SYNC -->|RSS feeds| firestore
  LI_ANALYTICS --> linkedin_api
  LI_ANALYTICS --> firestore
```

### 3.4 Layer Architecture

```mermaid
flowchart TB
  subgraph Client["Client Layer — Vercel (Next.js)"]
    NEXT["Next.js App Router
         · SSR pages
         · Client components
         · Server actions
         · Route handlers"]
    FIREBASE_CLI["Firebase Client SDK
                  · Auth (onAuthStateChanged)
                  · Firestore (onSnapshot)
                  · Functions (callable)"]
    AI_SDK["Vercel AI SDK
            · Streaming LLM calls
            · Provider abstraction
            · useChat hook"]
  end

  subgraph Auth["Auth Layer — Firebase"]
    FIREBASE_AUTH["Firebase Auth
                   · Email/password
                   · Google OAuth
                   · GitHub OAuth
                   · Custom claims (roles)
                   · ID token lifecycle"]
  end

  subgraph Compute["Compute Layer — Cloud Functions"]
    HTTP_FNS["HTTP-Callable Functions
              · Validated input (zod)
              · Auth context
              · Service orchestration"]
    TRIGGER_FNS["Event-Driven Functions
                 · Firestore triggers
                 · Auth triggers (onCreate/onDelete)"]
    SCHED_FNS["Scheduled Functions
               · Cron via onSchedule
               · Batch processing"]
    TASK_FNS["Cloud Task Handlers
              · Async job execution
              · Retry + backoff
              · Dead letter on failure"]
  end

  subgraph AI["AI Agent Layer (in Cloud Functions)"]
    CONTENT_PIPELINE["Content Pipeline
                      · Context aggregator
                      · Idea generator
                      · Draft composer
                      · Style refiner
                      · Quality gate"]
    BRIEF_PIPELINE["Brief Pipeline
                    · Multi-source context
                    · Idea ranking
                    · Brief assembly"]
    STYLE_PIPELINE["Style Pipeline
                    · Edit tracking
                    · EMA update
                    · Signal weighting"]
  end

  subgraph Data["Data Layer"]
    FIRESTORE[("Firestore
                · User documents
                · Subcollections
                · Composite indexes")]
    PGVECTOR[("Supabase pgvector
               · Knowledge embeddings
               · Style vectors
               · HNSW index")]
    STORAGE[("Cloud Storage
              · Draft exports
              · User uploads
              · Generated assets")]
  end

  subgraph External["External Services"]
    GROQ["Groq API
          · Llama 3.3 70B
          · Qwen3 32B
          · DeepSeek R1 70B"]
    MISTRAL["Mistral AI
             · mistral-embed"]
    GITHUB["GitHub API
            · Octokit
            · Repo analysis"]
    LINKEDIN["LinkedIn API
              · UGC Posts
              · Analytics"]
  end

  NEXT --> FIREBASE_CLI
  NEXT --> AI_SDK
  FIREBASE_CLI --> FIREBASE_AUTH
  FIREBASE_CLI -->|SDK reads| FIRESTORE
  FIREBASE_CLI -->|invoke| HTTP_FNS

  HTTP_FNS -->|zod validation| TRIGGER_FNS
  HTTP_FNS --> CONTENT_PIPELINE
  HTTP_FNS --> BRIEF_PIPELINE
  HTTP_FNS --> FIRESTORE
  HTTP_FNS --> PGVECTOR

  TRIGGER_FNS --> FIRESTORE
  TRIGGER_FNS -->|embedding jobs| PGVECTOR
  TRIGGER_FNS -->|enqueue| TASK_FNS

  SCHED_FNS --> BRIEF_PIPELINE
  SCHED_FNS --> CONTENT_PIPELINE
  SCHED_FNS --> FIRESTORE

  TASK_FNS --> CONTENT_PIPELINE
  TASK_FNS -->|publish| LINKEDIN
  TASK_FNS --> FIRESTORE

  AI_SDK --> GROQ
  CONTENT_PIPELINE --> GROQ
  CONTENT_PIPELINE --> FIRESTORE
  CONTENT_PIPELINE --> STYLE_PIPELINE

  BRIEF_PIPELINE --> FIRESTORE
  BRIEF_PIPELINE --> PGVECTOR

  STYLE_PIPELINE --> FIRESTORE
  STYLE_PIPELINE --> PGVECTOR

  GITHUB -->|Octokit| FIRESTORE
  LINKEDIN --> FIRESTORE
  MISTRAL --> PGVECTOR
```

---

## 4. Component Architecture

### 4.1 Cloud Function Package Structure

```
functions/
  src/
    profile/       # User profile CRUD
    knowledge/     # Knowledge base CRUD + embedding trigger
    content/       # Content generation pipeline
    publish/       # Platform publishing (LinkedIn)
    analytics/     # Analytics aggregation
    briefs/        # Daily brief generation
    github/        # GitHub sync
    trend/         # Trending topic discovery
    style/         # Style profile learning
    common/        # Shared utilities, types, middleware
```

### 4.2 Content Engine — Pipeline Architecture

The Content Engine is a 5-stage pipeline. Each stage is a pure function with typed inputs and outputs. The orchestrator runs them sequentially with timeouts and retry policies.

```mermaid
flowchart LR
  subgraph CONTEXT["Stage 1: Context Aggregator"]
    GA["GitHub Activity
        · Recent commits
        · Open PRs
        · Repo languages"]
    KBR["KB Reader
         · Recent saves
         · Top tags
         · Semantic search
         · Summaries"]
    TA["Trend Signals
        · Relevance scored
        · Freshness weighted
        · Source ranked"]
    SP["Style Profile
        · Voice params
        · Vocab map
        · Tone settings"]
  end

  subgraph IDEATE["Stage 2: Idea Generator (LLM)"]
    IG["Groq API call
        · Prompt: context + constraints
        · Output: 3-5 ranked ideas
        · Model: Llama 3.3 70B"]
  end

  subgraph COMPOSE["Stage 3: Draft Composer (LLM)"]
    DC["Groq API call
        · Prompt: idea + style + format
        · Output: full draft
        · Model: Qwen3 32B (faster)"]
  end

  subgraph REFINE["Stage 4: Style Refiner"]
    SR["Algorithmic
        · Vocab swap
        · Sentence length adjust
        · Tone calibration
        · Hook pattern match"]
  end

  subgraph QUALITY["Stage 5: Quality Gate (LLM)"]
    QG["Groq API call
        · Hallucination scan
        · Readability score
        · Fact-check
        · Verdict: PASS / FAIL / WARN
        · Model: Llama 4 Scout 17B"]
  end

  subgraph OUTPUT["Output"]
    DRAFT[(Draft saved to Firestore)]
  end

  GA --> IDEATE
  KBR --> IDEATE
  TA --> IDEATE
  SP --> IDEATE
  IDEATE -->|3-5 ideas| COMPOSE
  COMPOSE -->|draft text| REFINE
  REFINE -->|adjusted draft| QUALITY
  QUALITY -->|verdict| OUTPUT

  QUALITY -.->|FAIL| COMPOSE
```

**Stage Model Selection Rationale:**

| Stage | Model | Why |
|-------|-------|-----|
| Idea Generator | Llama 3.3 70B | Best reasoning for novel idea synthesis from diverse context |
| Draft Composer | Qwen3 32B | Faster inference (LPU), good technical writing quality |
| Quality Gate | Llama 4 Scout 17B | Strong instruction following for structured evaluation, cheapest |

### 4.3 Style Service — Voice Fingerprint

Style learning is **algorithmic**, not LLM-based. No API calls needed per style update.

```mermaid
flowchart TB
  subgraph INPUTS["Style Signal Sources"]
    RATINGS["· User ratings (1-5)"
             "· Per-dimension scores"
             "· Comment/text feedback"]
    EDITS["· User edits on drafts"
             "· Diff tracking"
             "· Acceptance rate per suggestion"]
    APPROVALS["· Approved vs rejected"
                "· Regenerate triggers"
                "· Manual rewrites count"]
    IMPORTS["· Imported LinkedIn posts"
              "· Historical content"
              "· User-provided examples"]
  end

  subgraph ANALYSIS["Style Analysis (Algorithmic)"]
    LEXICAL["Lexical Analyzer"
             "· Term frequency"
             "· Technical ratios"
             "· Filler word density"]
    SYNTACTIC["Syntactic Analyzer"
               "· Avg sentence length"
               "· Paragraph structure"
               "· Hook type detection"]
    TONAL["Tonal Analyzer"
           "· Formality score"
           "· Confidence markers"
           "· Opinion strength"]
  end

  subgraph PROFILE["Style Profile (per-user)"]
    PARAMS["Parameter Map"
            "· tone: formal|conversational|balanced"
            "· depth: tutorial|opinion|insight|news"
            "· avg_length: short|medium|long"
            "· hook_style: question|stat|quote|story|none"
            "· vocab: {preferred_terms, avoided_terms}"
            "· formality: 0.0–1.0"]
  end

  RATINGS --> LEXICAL
  EDITS --> LEXICAL
  APPROVALS --> LEXICAL
  IMPORTS --> LEXICAL
  RATINGS --> SYNTACTIC
  EDITS --> SYNTACTIC
  APPROVALS --> SYNTACTIC
  IMPORTS --> SYNTACTIC
  RATINGS --> TONAL
  EDITS --> TONAL
  APPROVALS --> TONAL
  IMPORTS --> TONAL

  LEXICAL --> PARAMS
  SYNTACTIC --> PARAMS
  TONAL --> PARAMS
```

**Exponential Moving Average Update:**

```
new_profile = learning_rate * latest_signal + (1 - learning_rate) * current_profile
```

- `learning_rate` starts at 0.3 (converges fast in first 10 interactions)
- After 50 interactions, decays to 0.1 (gradual drift)
- Stored in Firestore as a map under `users/{userId}/styleProfile`
- Style vectors stored in pgvector for similarity-based style matching (future: recommend style templates)

---

## 5. Content Generation Pipeline

### 5.1 Pipeline Stages Detail

| Stage | Type | Timeout | Retries | Cacheable |
|-------|------|---------|---------|-----------|
| Context Aggregator | Algorithmic | 5s | 0 | Per-user/per-day |
| Idea Generator | LLM (Llama 3.3 70B) | 20s | 1 | No |
| Draft Composer | LLM (Qwen3 32B) | 30s | 2 | No |
| Style Refiner | Algorithmic | 3s | 0 | No |
| Quality Gate | LLM (Llama 4 Scout 17B) | 15s | 1 | No |

### 5.2 Model Mapping

| Task | Recommended Model | Fallback Model | Groq Free Tier Limit |
|------|------------------|----------------|--------------------- |
| Content idea generation | Llama 3.3 70B | DeepSeek R1 Distill 70B | 30 RPM / 6K TPM |
| Draft writing | Qwen3 32B | Llama 4 Scout 17B | 30 RPM / 6K TPM |
| Style refinement | (Algorithmic) | — | — |
| Quality gate | Llama 4 Scout 17B | Mixtral 8x7B | 30 RPM / 6K TPM |
| Embeddings | Mistral Embed (via Mistral AI) | — | 1B tokens/month |

### 5.3 Groq Rate Limit Management

With 30 RPM and ~14.4K requests/day on Groq's free tier, we allocate:

| Use Case | Requests/User/Day | Users | Total/Day |
|----------|-------------------|-------|-----------|
| Daily brief generation | 2 (ideas + draft) | 500 | 1,000 |
| User-initiated drafts | 3 | 500 | 1,500 |
| Quality gate | 1 per draft | — | 2,500 |
| Style analysis import | 1 (initial) | — | 500 |
| **Total** | | | **5,500** |

At 5,500 requests/day, we stay well within Groq's ~14,400 daily limit at 500 users.

**Queue Strategy:** Content generation requests are enqueued via Cloud Tasks with a rate limiter that respects Groq's 30 RPM limit. If the queue backs up, users see a "generation in progress" state with real-time status via Firestore.

---

## 6. Sequence Diagrams

### 6.1 Daily Content Brief Generation

```mermaid
sequenceDiagram
  participant User
  participant Web as Next.js App
  participant BriefFn as brief.generateDailyBriefs
  participant ContentFn as content.generateIdeas
  participant Groq as Groq API
  participant StyleFn as style.getProfile
  participant Github as github.getRecentActivity
  participant Trend as trend.getTrending
  participant FS as Firestore
  participant Vectors as Supabase pgvector

  Note over User,Vectors: Scheduled every 6 hours via onSchedule

  BriefFn->>FS: Query users where nextBriefAt < now
  FS-->>BriefFn: [active_users]

  loop per user
    BriefFn->>FS: Get user profile + expertise + preferences
    FS-->>BriefFn: {profile, expertise, cadence}

    par GitHub Context
      BriefFn->>Github: getRecentActivity(userId)
      Github->>FS: Check last sync, return cached or miss
      alt cache miss
        Github->>Github: analyzeRepos(userId)
        Github->>FS: Store fresh results
      end
      Github-->>BriefFn: {commits, prs, languages}
    and KB Context
      BriefFn->>Vectors: semanticSearch(userId, limit=10, query=latest)
      Vectors-->>BriefFn: [{saved_items, tags, summaries}]
    and Trending Topics
      BriefFn->>Trend: getRelevant(userId, expertise)
      Trend->>FS: get expertise areas
      Trend-->>BriefFn: [{topic, score, sources}]
    end

    BriefFn->>StyleFn: getStyleProfile(userId)
    StyleFn->>FS: get style params
    FS-->>StyleFn: {tone, depth, length, hook}
    StyleFn-->>BriefFn: {style}

    BriefFn->>BriefFn: Build aggregated context
    BriefFn->>ContentFn: generateIdeas(context, style)
    ContentFn->>Groq: Generate 5 ranked ideas (Llama 3.3 70B)
    Groq-->>ContentFn: [{idea, angle, relevance, novelty}]
    ContentFn-->>BriefFn: [ranked_ideas]

    BriefFn->>FS: Save brief document
    BriefFn->>FS: Update user.nextBriefAt
  end

  User->>Web: Opens BrandOS dashboard
  Web->>FS: getDoc(user/briefs/latest)
  FS-->>Web: {ideas, context_summary}
  Web-->>User: Display content brief
```

### 6.2 User Draft Generation (Interactive)

```mermaid
sequenceDiagram
  participant User
  participant Web as Next.js App
  participant VercelAI as Vercel AI SDK
  participant ContentFn as content.generateDraft (callable)
  participant Groq as Groq API
  participant StyleFn as style.getProfile
  participant FS as Firestore
  participant Tasks as Cloud Tasks

  User->>Web: Selects idea: "Generate draft"
  Web->>ContentFn: invoke({ideaId, tone, length})
  ContentFn->>StyleFn: getStyleProfile(userId)
  StyleFn->>FS: get styleProfile subcollection
  FS-->>StyleFn: {styleParams, voiceVector}
  StyleFn-->>ContentFn: style profile

  ContentFn->>FS: get idea + context from brief
  FS-->>ContentFn: {title, description, context}

  ContentFn->>ContentFn: Build draft prompt
  ContentFn->>Groq: POST /chat/completions (Qwen3 32B)
  Groq-->>ContentFn: {draftText}

  ContentFn->>ContentFn: Apply style refinement (algorithmic)
  ContentFn->>Groq: POST /chat/completions (Llama 4 Scout 17B, quality gate)
  Groq-->>ContentFn: {verdict: PASS, score: 0.85}

  ContentFn->>FS: create draft document
  ContentFn-->>Web: {draftId, preview, qualityScore}

  Web->>Web: AI SDK useChat (streaming fallback for interactive generation)
  Web-->>User: Display draft in editor

  User->>Web: Edits draft
  Web->>ContentFn: updateDraft({draftId, revisedText})
  ContentFn->>FS: Save revision
  alt First edit
    ContentFn->>Tasks: enqueue analyzeStyleTask({userId, original, revised})
  end
  ContentFn-->>Web: {saved}

  User->>Web: Rates draft 4/5
  Web->>ContentFn: rateDraft({draftId, score: 4, dimensions})
  ContentFn->>FS: Save rating
  ContentFn->>FS: Update style profile EMA
  ContentFn-->>Web: {ratingRecorded}
```

### 6.3 LinkedIn Publish (Async via Cloud Tasks)

```mermaid
sequenceDiagram
  participant User
  participant Web as Next.js App
  participant ContentFn as content.schedulePost (callable)
  participant FS as Firestore
  participant Tasks as Cloud Tasks
  participant PublishFn as publish.linkedinPost (task handler)
  participant LinkedIn as LinkedIn API

  User->>Web: Approves draft, clicks "Schedule"
  Web->>ContentFn: invoke({draftId, scheduledFor, platform: "linkedin"})
  ContentFn->>FS: Update draft status → "scheduled"
  ContentFn->>FS: Create scheduledPost document
  ContentFn->>Tasks: enqueue publishPostTask({userId, draftId, scheduledFor})
  ContentFn-->>Web: {scheduled: true, postId}

  Note over User,LinkedIn: Scheduled time arrives

  Tasks->>PublishFn: Execute task
  PublishFn->>FS: Get draft + user LinkedIn tokens
  FS-->>PublishFn: {draftBody}, {encryptedTokens}
  PublishFn->>PublishFn: Decrypt tokens, format for LinkedIn
  PublishFn->>LinkedIn: POST /rest/posts (OAuth 2.0)
  
  alt Success (201)
    LinkedIn-->>PublishFn: {id, urn, url}
    PublishFn->>FS: Update post status → "published"
    PublishFn->>FS: Save external post ID
    PublishFn-->>Tasks: Acknowledge success
  else Rate Limited (429)
    LinkedIn-->>PublishFn: {error, retryAfter}
    PublishFn-->>Tasks: Retry with backoff (retryAfter + jitter)
  else Token Expired (401)
    LinkedIn-->>PublishFn: {error, "token_expired"}
    PublishFn->>PublishFn: Attempt token refresh
    alt Refresh succeeds
      PublishFn->>FS: Update stored tokens
      PublishFn->>LinkedIn: Retry with new token
    else Refresh fails
      PublishFn->>FS: Update connection status → "needs_reconnect"
      PublishFn-->>Tasks: Fail task, notify user
    end
  end
```

---

## 7. Memory Architecture

BrandOS uses Firestore as the primary memory store. Different memory types map to different access patterns.

### 7.1 Memory Types

| Type | Duration | Store | Access Pattern |
|------|----------|-------|----------------|
| **User Profile** | Permanent | Firestore doc | Frequent reads, rare writes |
| **Style Profile** | Permanent | Firestore doc (EMA) | Written per interaction, read per generation |
| **Knowledge Base** | Permanent | Firestore subcollection + pgvector | Written by user, read by agents |
| **Content Drafts** | 90 days | Firestore subcollection + Storage (exports) | Written by pipeline, read by user |
| **Schedule** | Until published | Firestore subcollection | Written by user, read by scheduler |
| **Briefs** | 7 days | Firestore subcollection | Written by agent, read by user |
| **Session** | Browser session | Client memory + Firestore cache | No server-side session |

### 7.2 Firestore Document Size Budget

Firestore limits: 1 MiB per document, 20 levels of subcollections, 1 write/second per document (burst up to 500).

| Document | Estimated Size | Growth Pattern | Concern? |
|----------|---------------|----------------|----------|
| `users/{id}` | 5-10 KB | Grows with style profile + preferences | No |
| `users/{id}/knowledge/{item}` | 50-200 KB | 1 per saved link/note. Summary + extracted text drive size | Extract text > 100KB → store in Cloud Storage, reference by path |
| `users/{id}/drafts/{draft}` | 10-50 KB | 1 per generated draft. Body + revisions > 50KB | Revisions over 10 → archive to Storage, keep latest 3 in Firestore |
| `users/{id}/briefs/{brief}` | 5-15 KB | 1 per daily brief. 3-5 ideas with context | No |
| `trendingTopics/{id}` | 2-5 KB | ~50 topics total | No |

**Mitigation Strategy:** Any field exceeding 50KB (extracted text, full draft history) is stored in Cloud Storage with a reference path in Firestore.

---

## 8. Knowledge Flow

### 8.1 Knowledge Ingestion Pipeline

```mermaid
flowchart TB
  subgraph INPUT["Knowledge Inputs"]
    MANUAL["Manual Save
             · Paste URL → scrape + summarize
             · Write note → store as-is
             · Upload file → extract text"]
    AUTO["Auto-Capture
           · GitHub linked issues
           · LinkedIn saved posts
           · Browser bookmark (P2)"]
    IMPORT["Bulk Import
             · Twitter bookmarks
             · Pocket export
             · Obsidian notes"]
  end

  subgraph PROCESS["Cloud Functions Processing"]
    EXTRACT["Content Extraction
              · URL → readability (cheerio)
              · PDF → text (pdf-parse)
              · Metadata extraction"]
    SUMMARIZE["Summarization
               · Via Groq (Llama 4 Scout 17B)
               · 2-3 sentence TL;DR
               · Key insight extraction"]
    EMBED["Embedding
            · Via Mistral AI (mistral-embed)
            · 1024-dim vector
            · Stored in pgvector"]
    CLASSIFY["Classification
              · Auto-tagging (via Groq)
              · Category assignment
              · Expertise mapping"]
  end

  subgraph STORE["Storage"]
    FS_STORE[(Firestore
               · Metadata
               · Summary
               · Tags
               · Ref to raw)]
    VEC_STORE[(Supabase pgvector
                · Embeddings
                · HNSW index
                · user_id scoped)]
    FILE_STORE[(Cloud Storage
                 · Raw extracted text
                 · Uploaded files
                 · Screenshots)]
  end

  subgraph RETRIEVAL["Retrieval Patterns"]
    SEARCH["Hybrid Search
             · FTS via pgvector
             · Semantic via pgvector
             · RRF merge (k=60)
             · Filters: user_id, tags, date"]
    CONTEXT["Context Builder
              · Recent items (last 7 days)
              · Top tags (rolling 30 days)
              · Random diversity sample
              · Expertise cross-section"]
    RELATED["Related Discovery
              · Similar items (vector)
              · Same tags (Firestore)
              · Same source type"]
  end

  MANUAL --> EXTRACT
  AUTO --> EXTRACT
  IMPORT --> EXTRACT
  EXTRACT --> SUMMARIZE
  EXTRACT --> CLASSIFY
  SUMMARIZE --> EMBED

  subgraph TRIGGERS["Firestore Triggers"]
    EMBED_TRIGGER["onKnowledgeItemWrite
                    · Detects new/modified item
                    · Calls summarize + embed
                    · Updates status"]
  end

  EMBED_TRIGGER --> EXTRACT
  EMBED_TRIGGER --> SUMMARIZE
  EMBED_TRIGGER --> EMBED

  EMBED --> VEC_STORE
  SUMMARIZE --> FS_STORE
  CLASSIFY --> FS_STORE
  EXTRACT --> FILE_STORE

  SEARCH --> VEC_STORE
  SEARCH --> FS_STORE
  CONTEXT --> FS_STORE
  RELATED --> VEC_STORE
  RELATED --> FS_STORE
```

### 8.2 Hybrid Search Implementation

```typescript
interface SearchResult {
  itemId: string;
  text: string;
  score: number;
  source: 'keyword' | 'semantic';
}

// RRF merge of keyword + semantic results
function hybridSearch(userId: string, query: string, limit: number = 10) {
  // 1. Full-text search via pgvector's built-in TSVector
  const keywordResults = await supabase.rpc('fts_search', {
    user_id: userId,
    query_text: query,
    result_limit: limit * 2
  });

  // 2. Semantic search via pgvector
  const embedding = await generateEmbedding(query);
  const semanticResults = await supabase.rpc('vector_search', {
    user_id: userId,
    query_embedding: embedding,
    match_threshold: 0.7,
    match_count: limit * 2
  });

  // 3. RRF merge with k=60
  return reciprocalRankFusion(keywordResults, semanticResults, limit, 60);
}
```

---

## 9. Security Architecture

### 9.1 Authentication Flow

```mermaid
sequenceDiagram
  participant User
  participant Web as Next.js App
  participant FirebaseAuth as Firebase Auth
  participant LinkedIn as LinkedIn OAuth
  participant GitHub as GitHub OAuth

  Note over User,GitHub: Primary Auth (Firebase Auth handles this)

  User->>Web: Click "Sign in with Google"
  Web->>FirebaseAuth: signInWithPopup(googleProvider)
  FirebaseAuth-->>Web: {user, credential}
  Web->>FirebaseAuth: Get ID token
  FirebaseAuth-->>Web: idToken (JWT, 1 hour)
  Web->>Web: Set auth state → Firestore security rules use this

  Note over User,GitHub: Platform Connection (LinkedIn, GitHub) — separate OAuth

  User->>Web: "Connect LinkedIn account"
  Web->>FirebaseAuth: signInWithPopup(linkedinProvider)
  FirebaseAuth-->>Web: {credential: LinkedInAccessToken}
  Web->>Web: Call Cloud Function: connectLinkedIn(token)
  Note over Web,GitHub: LinkedIn access token stored encrypted in Firestore
```

### 9.2 Security Layers

| Layer | Mechanism |
|-------|-----------|
| **Auth** | Firebase Auth (Google, GitHub, email/password). 50K MAU free. |
| **API Auth** | Cloud Functions `onCall` automatically verifies Firebase ID tokens. `context.auth` is populated for every call. |
| **Data Access** | Firestore Security Rules enforce per-user access. "Read own drafts only" is declarative, not code. |
| **LinkedIn Tokens** | Encrypted at rest in Firestore using Cloud KMS via Cloud Functions. Decrypted only in memory during publish tasks. |
| **API Keys (Groq, Mistral)** | Stored in Firebase Secret Manager. `defineSecret()` injects into function environment. Never logged. |
| **CORS** | Cloud Functions `onCall` enforces CORS implicitly. No manual CORS headers. |
| **Rate Limiting** | Implemented per-user at the function level. Warmup cache in Firestore (last request timestamp + count). |
| **Input Validation** | All function inputs validated with Zod schemas. Malformed input → rejected before processing. |

### 9.3 Firestore Security Rules

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User documents: owner only
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Trending topics: readable by all authenticated users
    match /trendingTopics/{topic} {
      allow read: if request.auth != null;
      allow write: if false; // Admin only via Cloud Functions
    }

    // Briefs: owner only
    match /users/{userId}/briefs/{briefId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if false; // Write-only via Cloud Functions
    }
  }
}
```

---

## 10. Caching Strategy

| Data | Cache Strategy | TTL | Implementation |
|------|---------------|-----|----------------|
| **User Profile** | Firestore SDK client cache | Session | Firebase SDK `{source: 'cache'}` for reads |
| **Style Profile** | Firestore SDK client cache | 5 minutes | Explicit read with `{source: 'server'}` on generation |
| **Content Brief** | Firestore document | 6 hours | Regenerated by scheduled function, stored as document |
| **Trending Topics** | Firestore document | 3 hours | Separate collection, updated by scheduled sync |
| **GitHub Activity** | Firestore document | 6 hours | Stored per-user, timestamp-tracked |
| **Draft Preview** | None | — | Generated on demand, user expects latest |
| **Analytics Dashboard** | Firestore aggregated document | 12 hours | Pre-computed by scheduled function |
| **LLM Responses** | None (MVP) | — | Content is unique per user+context. Cache considered for identical prompts in Phase 2. |

No separate Redis or CDN cache layer is needed for MVP. Firestore's server-side caching and the client SDK's persistence layer provide adequate read performance. If analytics dashboard queries become slow, pre-compute aggregations by a scheduled function into a dedicated cache document.

---

## 11. Deployment Architecture

### 11.1 Deployment Diagram

```mermaid
flowchart TB
  subgraph VERCEL["Vercel Platform"]
    direction LR
    NEXT_APP["Next.js App
              · Automatic SSL
              · Global CDN
              · Preview deployments
              · Environment variables"]
  end

  subgraph FIREBASE["Firebase Project"]
    direction TB
    FA["Firebase Auth"]
    FS_DB["Firestore Database"]
    CF["Cloud Functions
        · Node.js 20
        · 7 function groups
        · Max: 256MB per function
        · Timeout: 60s (HTTP), 540s (background)"]
    CS["Cloud Storage
        · Default bucket
        · Security rules
        · 30-day file retention"]
    CT["Cloud Tasks
        · Pub/sub queues
        · Retry configs
        · Max attempts: 5"]

    FA --- FS_DB
    FA --- CF
    CF --- FS_DB
    CF --- CS
    CF --- CT
  end

  subgraph EXTERNAL["External Services"]
    GROQ["Groq API
          · Llama 3.3 70B
          · Qwen3 32B
          · Llama 4 Scout 17B"]
    MISTRAL["Mistral AI
             · mistral-embed"]
    SUPABASE["Supabase
              · pgvector
              · Free tier database"]
    GITHUB_API["GitHub API"]
    LI_API["LinkedIn API"]
  end

  VERCEL -->|"Firebase SDK"| FIREBASE
  CF -->|"GROQ_API_KEY"| GROQ
  CF -->|"MISTRAL_API_KEY"| MISTRAL
  CF -->|"SUPABASE_SERVICE_KEY"| SUPABASE
  CF -->|"GitHub App"| GITHUB_API
  CF -->|"LinkedIn App"| LI_API
```

### 11.2 CI/CD Pipeline

```mermaid
flowchart LR
  GIT["git push"] --> GHA["GitHub Actions"]
  
  subgraph GHA["GitHub Actions Workflow"]
    direction TB
    LINT["Lint + Type Check
          · eslint
          · tsc --noEmit"]
    TEST["Test
          · vitest (unit)
          · firebase emulators (integration)"]
    BUILD["Build
           · npm run build
           · next build (frontend)
           · tsc (functions)"]
  end

  GHA -->|"Frontend"| VERCELL["Vercel Deploy
                                · Production branch
                                · Preview per PR"]
  GHA -->|"Functions"| FIREBASE_DEPLOY["Firebase Deploy
                                         · firebase deploy --only functions
                                         · firebase deploy --only firestore:rules
                                         · firebase deploy --only firestore:indexes"]

  subgraph ENVIRONMENTS["Deployment Environments"]
    PROD["Production
          · main branch
          · Vercel production
          · Firebase production"]
    PREVIEW["Preview
             · PR branches
             · Vercel preview
             · Firebase staging project"]
  end

  VERCELL --> PROD
  VERCELL --> PREVIEW
  FIREBASE_DEPLOY --> PROD
```

---

## 12. Scalability Path

| Metric | MVP Target (500 users) | Phase 2 (5K users) | Phase 3 (50K users) |
|--------|----------------------|--------------------|---------------------|
| **Auth** | Firebase Auth (50K MAU free) | Same | Same |
| **Firestore** | Native mode, single region | Same | Nam5 → multi-region |
| **Cloud Functions** | 2M invocations/mo (free) | ~10M/mo (~$0.40/M) | ~100M/mo (~$0.40/M) |
| **Cloud Storage** | 5GB (free on Blaze) | ~10GB ($0.026/GB) | ~50GB ($0.026/GB) |
| **Groq API** | Free tier (14.4K RPD) | Paid tier ($0.10-0.30/M tokens) | Reserved capacity |
| **Supabase pgvector** | Free tier (500MB) | Pro tier ($25/mo, 8GB) | Team tier ($599/mo) |
| **LinkedIn API** | Free tier | Same | Same |

### 12.1 Bottleneck Predictions

| Bottleneck | When It Hits | Mitigation |
|------------|-------------|------------|
| **Firestore write limits** | ~500 concurrent users writing simultaneously | Distribute writes across subcollections. Use batched writes. Reduce revision writes to a scheduled compaction. |
| **Groq rate limits** | ~1,500 daily active users | Upgrade to Groq paid tier ($0.15/M tokens for Llama 3.3 70B). Or add Mistral AI Large as secondary generator. |
| **Cloud Function cold starts** | Any scale | Use minimum instances (1-2) for latency-sensitive functions (content generation, brief retrieval). 10 instances free, then $0.000005/instance/s. |
| **pgvector performance** | >100K vectors per user, >100 users | Add IVFFlat index (faster index build, higher recall). Partition by user_id. Upgrade Supabase. |

---

## 13. Cost Analysis

### 13.1 Monthly Operating Cost (MVP, 500 users)

| Service | Component | Estimated Cost |
|---------|-----------|---------------|
| **Firebase** | Auth (50K MAU) | $0 (free tier) |
| **Firebase** | Firestore (1GB storage, 50K reads/day, 20K writes/day) | $0 (free tier) |
| **Firebase** | Cloud Functions (2M invocations/month) | $0 (free on Blaze) |
| **Firebase** | Cloud Storage (5GB) | $0 (free on Blaze) |
| **Firebase** | Cloud Tasks | $0 (free tier) |
| **Vercel** | Next.js hosting (Pro plan) | $20/mo |
| **Groq API** | 165K requests/month average | $0 (free tier) |
| **Mistral AI** | Embeddings (50M tokens/month) | $0 (free tier, 1B/mo cap) |
| **Supabase** | pgvector (500MB) | $0 (free tier) |
| **LinkedIn API** | OAuth + UGC Posts | $0 |
| **GitHub API** | Octokit (5K requests/hour) | $0 |
| **Custom Domain** | Vercel custom domain | $0 (Vercel Pro includes custom domain) |
| **Total** | | **~$20/mo** |

### 13.2 Scale Costs (Phase 2, 5K users)

| Service | Cost |
|---------|------|
| Firebase (beyond free tier) | ~$25/mo |
| Vercel Pro | $20/mo |
| Groq paid tier (~5M tokens/mo) | ~$0.75-2.25/mo |
| Supabase Pro | $25/mo |
| **Total** | **~$75/mo** |

---

## 14. Decision Log

| # | Decision | Date | Rationale |
|---|----------|------|-----------|
| 1 | Firestore over PostgreSQL | 2026-07-14 | Serverless triggers, real-time via onSnapshot, security rules, zero-config. NoSQL document model fits user-centric data hierarchy. Cloud Functions fill the query gap for complex aggregations. |
| 2 | Cloud Functions over FastAPI | 2026-07-14 | Eliminates server management. Scales to zero. Integrated with Firebase Auth + Firestore triggers. TypeScript enables shared types with frontend. Free tier covers MVP. |
| 3 | Groq over Anthropic/OpenAI | 2026-07-14 | Open-source models only per requirement. Groq's LPU hardware provides faster inference than cloud GPUs. Free tier (14.4K RPD) covers MVP with no credit card required. |
| 4 | Mistral over @xenova/transformers for embeddings | 2026-07-14 | 1B tokens/month free tier. No cold start impact (running ONNX in a Cloud Function adds ~2s cold start). Simpler code, no model bundling. |
| 5 | Supabase pgvector over Cloudflare Vectorize | 2026-07-14 | Supabase client already installed in project. pgvector enables hybrid search (keyword + vector) in one database. 500MB free tier sufficient for MVP. |
| 6 | Firestore triggers over message queue | 2026-07-14 | For MVP, Firestore document writes trigger embedding generation and other side effects. This eliminates a separate queue infrastructure. Cloud Tasks used only for scheduled posts and long-running content generation. |
| 7 | No Redis/Separate cache layer | 2026-07-14 | Firestore's client SDK caching and server-side read-after-write consistency are sufficient for MVP. If brief retrieval latency exceeds 500ms, add a Cloud Storage cache document. |
| 8 | Style learning is algorithmic, not LLM-driven | 2026-07-14 | Style profile is updated via exponential moving average of edit signals, ratings, and approvals. No LLM calls needed per update. This saves ~100K LLM calls/month at 500 users. |
| 9 | Single Firebase project, not multiple | 2026-07-14 | One project for all Firebase services. Separate staging project for preview deploys. No multi-region or project-per-service complexity at MVP scale. |
| 10 | Same-model pipeline (all Groq) instead of model-per-stage | 2026-07-14 | All pipeline stages use Groq (different models within Groq: Llama 3.3 70B for ideas, Qwen3 32B for drafts, Llama 4 Scout 17B for quality). Single API provider simplifies auth, error handling, and retry logic. |

---

*This document describes the target architecture. See 07_IMPLEMENTATION_PLAN.md for the phased migration from the current FastAPI/SQLite/ChromaDB stack to Firebase/Firestore/Groq.*
