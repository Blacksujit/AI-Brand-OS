# Database Design: BrandOS (Firestore + pgvector)

## Document Info

| Field | Value |
|-------|-------|
| **Author** | Architecture Team |
| **Status** | Draft |
| **Created** | 2026-07-14 |
| **Operational Engine** | Firestore (NoSQL, schemaless) |
| **Vector Engine** | Supabase pgvector (PostgreSQL extension) |
| **Migration Tool** | Supabase CLI (pgvector) + manual Firestore index setup |

---

## Table of Contents

- [Architecture Overview](#1-architecture-overview)
- [Firestore Collections](#2-firestore-collections)
- [Firestore Indexes](#3-firestore-indexes)
- [pgvector Schema](#4-pgvector-schema)
- [Security Rules](#5-security-rules)
- [Query Patterns](#6-query-patterns)
- [What Changed from SQLite + ChromaDB](#7-what-changed-from-sqlite--chromadb)
- [Future Expansion](#8-future-expansion)

---

## 1. Architecture Overview

BrandOS uses **two database engines** with clear separation of concerns:

### Firestore (Operational Data)

- All user-facing CRUD data: profiles, knowledge items, drafts, schedules, briefs, notifications, analytics
- Subcollections under `users/{userId}` for natural data isolation and security
- NoSQL schemaless design — Zod validation happens in Cloud Functions, not in the database
- Built-in real-time listeners for future live features (e.g., draft auto-save)
- Firestore Security Rules enforce row-level access per user

### Supabase pgvector (Vector Data)

- Embeddings for semantic search: knowledge item vectors, style profile vectors
- Self-hosted PostgreSQL with the `pgvector` extension on Supabase (free tier: 500MB database)
- Separate from Firestore because Firestore has no native vector similarity search
- Access via the existing `supabase-js` client already installed in the frontend

### Data Flow

```
User Action → Cloud Function → Firestore (operational)
                     ↓
             PGVector (if embeddings) via supabase-js
```

### Scale Triggers

| Scale Event | Action |
|-------------|--------|
| Users exceed 1,000 | Evaluate Firestore Native mode (from Datastore mode) |
| pvector row count exceeds 500K per index | Implement IVFFlat → HNSW indexing |
| Embedding count exceeds 1M | Shard by user_id hash prefix in pgvector |

---

## 2. Firestore Collections

### 2.1 Collection: `users/{userId}`

**Root user document.** Created on Firebase Auth sign-up via `functions.auth.user().onCreate` trigger.

```typescript
interface UserDocument {
  // Auth
  uid: string;                   // Firebase Auth UID (doc ID)
  email: string;
  displayName: string;
  photoURL?: string;

  // Profile
  bio?: string;                  // max 1000 chars
  timezone: string;              // e.g., "America/New_York"
  onboardingCompleted: boolean;  // true after first-time setup

  // Preferences
  postingCadence: 'daily' | '3x_week' | 'weekly' | 'custom';
  briefHour: number;             // 0-23, when to generate daily brief
  defaultTone: ContentTone;
  defaultLength: ContentLength;
  digestEnabled: boolean;

  // Stats (denormalized counters)
  stats: {
    totalDrafts: number;
    totalPublished: number;
    totalKnowledgeItems: number;
  };

  // Meta
  createdAt: Timestamp;
  updatedAt: Timestamp;
}
```

### 2.2 Subcollection: `users/{userId}/expertise/{areaId}`

```typescript
interface ExpertiseDocument {
  name: string;          // e.g., "Software Architecture"
  category: string;      // e.g., "Engineering"
  priority: number;      // 1 = highest
  keywords: string[];    // for relevance matching
  createdAt: Timestamp;
}
```

### 2.3 Subcollection: `users/{userId}/knowledge/{itemId}`

Documents the user's saved knowledge base items.

```typescript
interface KnowledgeDocument {
  // Content
  url?: string;            // Source URL
  title: string;           // 1-500 chars
  note?: string;           // User note, max 5000 chars
  summary?: string;        // AI-generated summary

  // Metadata
  sourceType: 'link' | 'note' | 'paper' | 'code' | 'video' | 'podcast';
  tags: string[];          // max 20 tags
  isArchived: boolean;

  // Vector sync
  embeddingStatus: 'pending' | 'synced' | 'failed';
  pgvectorId?: string;     // Row ID in supabase knowledge_embeddings

  // Timestamps
  createdAt: Timestamp;
  updatedAt: Timestamp;
}
```

**Indexes:** `tags` (array), `sourceType`, `createdAt` descending.

### 2.4 Subcollection: `users/{userId}/drafts/{draftId}`

Generated content drafts and user revisions.

```typescript
// Supported content categories
type ContentType = 'tutorial' | 'opinion' | 'tweetstorm' | 'thread'
                 | 'case_study' | 'insight' | 'resources' | 'story'
                 | 'question' | 'milestone' | 'trend_analysis';

// Tone variants
type ContentTone = 'technical' | 'conversational' | 'professional'
                 | 'inspiring' | 'storytelling' | 'analytical';

// Length variants
type ContentLength = 'short' | 'medium' | 'long';

// Post status
type PostStatus = 'idea' | 'drafting' | 'ready' | 'scheduled' | 'published' | 'archived';

interface DraftDocument {
  idea: {
    title: string;           // 1-200 chars
    description: string;     // 1-2000 chars
    category: ContentType;
    contextSources: string[]; // Knowledge item IDs used
  };

  // Content
  title: string;
  body: string;

  // Quality
  qualityScore?: number;     // 0-1, from quality gate
  qualityVerdict?: 'pass' | 'warn' | 'fail';
  readabilityScore?: number;

  // Metadata
  contentType: ContentType;
  tone: ContentTone;
  length: ContentLength;
  wordCount: number;

  // Status
  status: PostStatus;
  version: number;           // Incremented on update

  // User rating (filled after user rates)
  userRating?: {
    score: number;           // 1-5
    dimensions: {
      accuracy: number;      // 1-5
      readability: number;   // 1-5
      authenticity: number;  // 1-5
      engagement: number;    // 1-5
    };
    comment?: string;
    createdAt: Timestamp;
  };

  // Timestamps
  createdAt: Timestamp;
  updatedAt: Timestamp;
  publishedAt?: Timestamp;
}
```

**Indexes:** `status`, `createdAt` descending, composite `(status, createdAt)`.

### 2.5 Subcollection: `users/{userId}/schedule/{scheduleId}`

Scheduled publishing entries.

```typescript
interface ScheduleDocument {
  draftId: string;             // Reference to draft document
  draftTitle: string;          // Denormalized for list views
  platform: 'linkedin';        // Future: 'twitter', 'bluesky', 'threads'
  scheduledFor: Timestamp;
  status: 'pending' | 'published' | 'failed';
  externalPostId?: string;     // LinkedIn post URN
  externalPostUrl?: string;
  errorMessage?: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}
```

**Indexes:** `status`, `scheduledFor` ascending (for worker query), composite `(status, scheduledFor)`.

### 2.6 Subcollection: `users/{userId}/briefs/{briefId}`

Daily content briefs with generated ideas.

```typescript
interface BriefDocument {
  date: string;            // YYYY-MM-DD
  ideas: Array<{
    id: string;
    title: string;
    description: string;
    category: ContentType;
    relevanceScore: number;
    noveltyScore: number;
  }>;
  contextSummary: {
    recentCommits: number;
    recentKnowledge: number;
    trendingTopics: string[];
  };
  status: 'generated' | 'viewed' | 'drafted' | 'exhausted';
  titleCount: number;      // Number of ideas in this brief
  generatedAt: Timestamp;
}
```

**Indexes:** `date` descending.

### 2.7 Subcollection: `users/{userId}/connections/{platform}`

Platform OAuth connections. Document ID is the platform name.

```typescript
interface ConnectionDocument {
  platform: 'linkedin' | 'github';
  accessToken: string;        // Encrypted at rest (Firestore sensitive field)
  refreshToken?: string;
  tokenExpiresAt: Timestamp;
  status: 'connected' | 'expired' | 'needs_reconnect';
  externalUserId?: string;    // LinkedIn profile URN, GitHub user ID
  connectedAt: Timestamp;
  lastSyncAt?: Timestamp;
}
```

### 2.8 Collection: `analytics_daily/{userDateId}`

Rolling analytics snapshots (separate from user subcollections for efficient aggregation).

Document ID: `<userId>_<YYYY-MM-DD>`.

```typescript
interface DailyAnalyticsDocument {
  userId: string;
  date: string;              // YYYY-MM-DD
  impressions: number;
  engagements: number;
  followerCount: number;
  followerDelta: number;
  postsPublished: number;
  createdAt: Timestamp;
}
```

**Indexes:** Composite `(userId, date)`.

### 2.9 Collection: `scheduled_worker/{jobId}`

Worker queue for executing scheduled posts. Written by Cloud Scheduler, read by worker function.

```typescript
interface ScheduledJobDocument {
  userId: string;
  scheduleId: string;
  draftId: string;
  platform: 'linkedin';
  executeAt: Timestamp;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  attempts: number;
  maxAttempts: number;
  lastError?: string;
  lockedUntil?: Timestamp;    // For distributed locking
  createdAt: Timestamp;
  updatedAt: Timestamp;
}
```

**Indexes:** Composite `(status, executeAt, lockedUntil)`.

---

## 3. Firestore Indexes

### 3.1 Composite Index Requirements

The following composite indexes must be created in the Firebase Console or via `firebase.json`:

| Collection/Subcollection | Fields | Query Pattern |
|---|---|---|
| `users/{uid}/knowledge` | `createdAt` DESC | "Show my knowledge items, newest first" |
| `users/{uid}/knowledge` | `tags` ARRAY, `createdAt` DESC | "Filter knowledge by tag" |
| `users/{uid}/knowledge` | `isArchived`, `createdAt` DESC | "Show non-archived items" |
| `users/{uid}/drafts` | `createdAt` DESC | "Show recent drafts" |
| `users/{uid}/drafts` | `status`, `createdAt` DESC | "Filter by status" |
| `users/{uid}/drafts` | `contentType`, `createdAt` DESC | "Filter by content type" |
| `users/{uid}/schedule` | `status`, `scheduledFor` ASC | "Worker picks pending scheduled posts" |
| `users/{uid}/schedule` | `scheduledFor` DESC | "Show recent schedule" |
| `users/{uid}/briefs` | `date` DESC | "Show recent briefs" |
| `analytics_daily` | `userId`, `date` ASC | "Rollup analytics per user" |
| `scheduled_worker` | `status`, `executeAt`, `lockedUntil` | "Worker picks jobs to execute" |

### 3.2 Firestore Limits Awareness

| Limit | Value | Mitigation |
|-------|-------|------------|
| Max document size | 1 MiB | Store only recent body text; archive old versions |
| Max subcollection depth | 100 | All subcollections are 1 level deep |
| Max writes/second per collection | 500 (burst 10K) | Worker uses random stagger |
| Max reads/second per doc | Unlimited (with cache) | Client SDK caches aggressively |
| Max indexes per collection | 200 | Well below limit for MVP (target ~15) |

---

## 4. pgvector Schema

### 4.1 Sandbox (Supabase)

Hosted on the existing Supabase project. The `supabase-js` client is already installed in the frontend (`frontend/lib/supabase.ts`). Cloud Functions also use it via `createClient`.

### 4.2 Extension

Enable the extension via Supabase SQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4.3 Table: `knowledge_embeddings`

Stores vectors for semantic search across knowledge items.

```sql
CREATE TABLE knowledge_embeddings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     TEXT NOT NULL,           -- Firebase UID
  item_id     TEXT NOT NULL UNIQUE,    -- Firestore document ID (knowledge/{itemId})
  title       TEXT NOT NULL,
  note        TEXT,
  source_type TEXT NOT NULL,
  tags        TEXT[],                  -- PostgreSQL array
  embedding   VECTOR(768) NOT NULL,    -- mistral-embed produces 768-d vectors
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for similarity search
CREATE INDEX idx_knowledge_embeddings_vector ON knowledge_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Filter by user
CREATE INDEX idx_knowledge_embeddings_user ON knowledge_embeddings (user_id);

-- Unique constraint ensures one embedding per knowledge item
-- (item_id is already UNIQUE)
```

**Notes:**
- `ivfflat` with `lists = 100` is suitable for up to ~500K rows. Switch to `hnsw` at scale.
- `vector_cosine_ops` for cosine distance (matching Mistral embedding's metric).
- `user_id` column allows per-user filtering before similarity search (or filter in application).

### 4.4 Table: `style_vectors`

Stores per-user style profiles as exponential moving average vectors.

```sql
CREATE TABLE style_vectors (
  user_id     TEXT PRIMARY KEY,        -- Firebase UID
  ema_vector  VECTOR(768) NOT NULL,    -- Current EMA of user style
  alpha       REAL NOT NULL DEFAULT 0.3, -- EMA decay factor
  sample_count INTEGER NOT NULL DEFAULT 0, -- How many samples trained
  last_sample_at TIMESTAMPTZ,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for nearest-neighbor style matching
CREATE INDEX idx_style_vectors_ema ON style_vectors
  USING ivfflat (ema_vector vector_cosine_ops)
  WITH (lists = 10);
```

**Notes:**
- One row per user (upserted on each rating).
- `alpha = 0.3` means newer ratings have ~30% weight, older ratings decay exponentially.
- `sample_count` tracks training volume; style is unreliable below ~5 samples.

### 4.5 Migration SQL

```sql
-- 001_enable_pgvector.sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 002_create_knowledge_embeddings.sql
CREATE TABLE knowledge_embeddings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     TEXT NOT NULL,
  item_id     TEXT NOT NULL UNIQUE,
  title       TEXT NOT NULL,
  note        TEXT,
  source_type TEXT NOT NULL,
  tags        TEXT[],
  embedding   VECTOR(768) NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_knowledge_embeddings_vector ON knowledge_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_knowledge_embeddings_user ON knowledge_embeddings (user_id);

-- 003_create_style_vectors.sql
CREATE TABLE style_vectors (
  user_id      TEXT PRIMARY KEY,
  ema_vector   VECTOR(768) NOT NULL,
  alpha        REAL NOT NULL DEFAULT 0.3,
  sample_count INTEGER NOT NULL DEFAULT 0,
  last_sample_at TIMESTAMPTZ,
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_style_vectors_ema ON style_vectors
  USING ivfflat (ema_vector vector_cosine_ops) WITH (lists = 10);
```

### 4.6 Query Examples

**Semantic search by user:**

```typescript
// Cloud Function or API route
import { createClient } from '@supabase/supabase-js';

async function searchKnowledge(uid: string, queryEmbedding: number[], limit: number = 10) {
  const { data, error } = await supabase.rpc('match_knowledge', {
    query_user_id: uid,
    query_embedding: queryEmbedding,
    match_threshold: 0.7,
    match_count: limit,
  });
  return data;
}
```

**Recommended pgvector RPC:**

```sql
CREATE OR REPLACE FUNCTION match_knowledge(
  query_user_id TEXT,
  query_embedding VECTOR(768),
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE(
  id TEXT,
  user_id TEXT,
  item_id TEXT,
  title TEXT,
  note TEXT,
  source_type TEXT,
  tags TEXT[],
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    ke.id::TEXT,
    ke.user_id,
    ke.item_id,
    ke.title,
    ke.note,
    ke.source_type,
    ke.tags,
    1 - (ke.embedding <=> query_embedding) AS similarity
  FROM knowledge_embeddings ke
  WHERE ke.user_id = query_user_id
    AND 1 - (ke.embedding <=> query_embedding) > match_threshold
  ORDER BY ke.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

---

## 5. Security Rules

### 5.1 Firestore Security Rules

```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Helper: check auth
    function isAuthenticated() {
      return request.auth != null;
    }

    function isOwner(userId) {
      return request.auth.uid == userId;
    }

    // User document — owner only
    match /users/{userId} {
      allow read: if isAuthenticated() && isOwner(userId);
      allow write: if isAuthenticated() && isOwner(userId);
      allow create: if isAuthenticated() && isOwner(userId);
      allow delete: if false; // Disable delete; use soft-delete or admin

      // Subcollections — owner only
      match /expertise/{areaId} {
        allow read, write: if isAuthenticated() && isOwner(userId);
      }

      match /knowledge/{itemId} {
        allow read, write: if isAuthenticated() && isOwner(userId);
      }

      match /drafts/{draftId} {
        allow read, write: if isAuthenticated() && isOwner(userId);
      }

      match /schedule/{scheduleId} {
        allow read, write: if isAuthenticated() && isOwner(userId);
      }

      match /briefs/{briefId} {
        allow read: if isAuthenticated() && isOwner(userId);
        allow create: if isAuthenticated() && isOwner(userId);
        allow delete: if false; // Immutable once created
      }

      match /connections/{platform} {
        allow read: if isAuthenticated() && isOwner(userId);
        allow write: if isAuthenticated() && isOwner(userId);
      }
    }

    // Analytics — admin only or via Cloud Functions
    match /analytics_daily/{docId} {
      allow read: if false;  // Only accessed via Cloud Functions
      allow write: if false; // Only written by worker functions
    }

    // Worker queue — only accessible by internal functions
    match /scheduled_worker/{jobId} {
      allow read, write: if false; // Only accessed via admin SDK in Cloud Functions
    }
  }
}
```

### 5.2 Supabase Row-Level Security

```sql
-- Enable RLS
ALTER TABLE knowledge_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE style_vectors ENABLE ROW LEVEL SECURITY;

-- Users can read their own embeddings
CREATE POLICY user_select_own_embeddings ON knowledge_embeddings
  FOR SELECT USING (auth.uid()::TEXT = user_id);

-- Only server-side functions can write embeddings
CREATE POLICY service_role_manage_embeddings ON knowledge_embeddings
  USING (auth.role() = 'service_role');

-- Style vectors: user can read own, only service_role can write
CREATE POLICY user_select_own_style ON style_vectors
  FOR SELECT USING (auth.uid()::TEXT = user_id);

CREATE POLICY service_role_manage_style ON style_vectors
  USING (auth.role() = 'service_role');
```

**Important:** Cloud Functions should use the Supabase `service_role` key to bypass RLS. Frontend never accesses pgvector directly.

---

## 6. Query Patterns

### 6.1 Daily Brief Generation

```typescript
// Triggered by Cloud Scheduler at each user's briefHour
// 1. Read user document → get expertise, preferences
// 2. Query knowledge subcollection → recent items (last 7 days)
// 3. Query schedule → recent publishes
// 4. Call Groq API → generate ideas
// 5. Write brief document to briefs subcollection
```

### 6.2 Style Profile Update

```typescript
// Triggered when user rates a draft
// 1. Extract user's edit patterns from the draft body (diff)
// 2. Call Mistral API → generate embedding of user's writing from the draft
// 3. Upsert to supabase style_vectors:
//    UPDATE style_vectors SET
//      ema_vector = ema_vector * (1 - alpha) + new_vector * alpha,
//      sample_count = sample_count + 1,
//      ...
//    WHERE user_id = uid
```

### 6.3 Hybrid Knowledge Search

```typescript
// 1. (Client or function) calls Mistral API → query embedding (768-d)
// 2. Queries supabase match_knowledge RPC with user_id filter
// 3. Returns ranked items with similarity scores
// 4. (Optional) Falls back to Firestore tag-based filtering if embedding fails
```

### 6.4 Pending Schedules (Worker)

```typescript
// Cloud Scheduler → Function polls scheduled_worker collection
const thirtyMinAgo = Timestamp.fromMillis(Date.now() - 30 * 60 * 1000);
const snapshot = await db
  .collection('scheduled_worker')
  .where('status', '==', 'pending')
  .where('executeAt', '<=', Timestamp.now())
  .where('lockedUntil', '<', thirtyMinAgo)
  .orderBy('executeAt')
  .limit(5)
  .get();
```

### 6.5 Analytics Rollup

```typescript
// Cloud Scheduler → daily function reads analytics_daily collection
const thirtyDaysAgo = Timestamp.fromMillis(Date.now() - 30 * 24 * 60 * 60 * 1000);
const snapshot = await db
  .collection('analytics_daily')
  .where('userId', '==', uid)
  .where('date', '>=', formatDate(thirtyDaysAgo))
  .orderBy('date')
  .get();
```

---

## 7. What Changed from SQLite + ChromaDB

| Area | SQLite + ChromaDB (Old) | Firestore + pgvector (New) | Rationale |
|------|------------------------|---------------------------|-----------|
| **Operational DB** | SQLite (single file, WAL) | Firestore (managed NoSQL) | Eliminates file-based storage for serverless; built-in real-time sync; native Firebase Auth integration |
| **Vector DB** | ChromaDB (persistent client) | Supabase pgvector | ChromaDB requires a running Python process; pgvector runs on existing Supabase project |
| **FTS5** | SQLite FTS5 on title/body | Firestore array-contains + client-side regex fallback | FTS5 is SQLite-specific; Firestore doesn't support full-text search. MVP uses tags + title match; future can add Algolia/Typesense |
| **Migrations** | Alembic (SQLite) | firebase.json indexes + Supabase CLI SQL | Firestore is schemaless; only index configuration needs explicit management |
| **Foreign keys** | SQLite FK constraints + CASCADE | Application-level enforcement | Firestore has no FK support; all cleanup is done in Cloud Functions |
| **Backup** | VACUUM INTO + gzip | Firestore managed backups + Supabase pg_dump | Firestore has automatic backup via Google Cloud; no manual backup script needed |
| **Connections** | SQLAlchemy async + aiosqlite | `@google-cloud/firestore` SDK + `supabase-js` | Native Firebase and Supabase SDKs; no ORM overhead |
| **Embedding trigger** | ChromaDB auto-embed (Python) | Firestore `onDocumentWritten` → Cloud Function → Mistral API → pgvector | Async pipeline; embeddings are eventually consistent with knowledge items |
| **Security** | Application-level auth | Firestore Security Rules + Supabase RLS | Declarative security at the database layer |
| **ID generation** | UUID v4 in Python | Firestore auto-ID (or custom ID) | Firestore generates unique document IDs automatically |

---

## 8. Future Expansion

### PostgreSQL → Firestore Native Mode

When user count exceeds 1,000 or analytics data volume grows, the project can be transitioned to Firestore Native mode (currently Datastore mode in some projects) for better scaling characteristics.

### Vector Scaling

| Scale | Index Strategy | Notes |
|-------|---------------|-------|
| < 10K rows | No index (brute force) | Acceptable latency for user-level search |
| 10K - 500K | IVFFlat (lists = 100) | Fast approximate search |
| 500K - 10M | HNSW (m=16, ef=64) | Better recall, higher memory |
| > 10M | Partition by user_id hash | Shard across multiple pgvector instances |

### Full-Text Search

If tag-based search becomes insufficient, options include:

1. **Algolia** — Managed, fast, generous free tier (10K records, 10K searches/mo)
2. **Typesense** — Open-source, self-hosted or cloud
3. **Google Cloud Search** — Native GCP integration with Firestore

### Caching

- **Firestore client SDK** provides built-in document caching (no additional cost)
- **Supabase connection pool** — `supabase-js` manages HTTP connection pooling
- **Vercel CDN** — Static responses cached at the edge
- **Redis** — Only if generated briefs become a performance bottleneck (post-MVP)

### Backup

| Engine | Method | Frequency | Retention |
|--------|--------|-----------|-----------|
| Firestore | Google Cloud managed backup (Console → Firestore → Backups) | Daily | 7 days (default) |
| Supabase pgvector | Supabase Database Backup (Console → Database → Backups) | Daily | 7 days (free tier) |

No custom backup scripts needed — both providers handle durability natively.

---

*This document defines the complete database design for BrandOS using Firestore for operational data and Supabase pgvector for vector embeddings. The dual-engine design leverages each system's strengths: Firestore's serverless NoSQL for user-facing CRUD, and pgvector's SQL-powered similarity search for AI features.*
