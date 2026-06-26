# Database Design: BrandOS

## Document Info

| Field | Value |
|-------|-------|
| **Author** | Architecture Team |
| **Status** | Draft |
| **Created** | 2026-06-26 |
| **Last Updated** | 2026-06-26 |
| **Engine** | PostgreSQL 16 + pgvector |
| **Migration Tool** | Alembic |

---

## Table of Contents

- [Schema Organization](#1-schema-organization)
- [Table Definitions](#2-table-definitions)
- [Migration Scripts](#3-migration-scripts)
- [Indexing Strategy](#4-indexing-strategy)
- [Query Patterns](#5-query-patterns)
- [Partitioning Strategy](#6-partitioning-strategy)
- [Backup & Recovery](#7-backup--recovery)

---

## 1. Schema Organization

```
brandos
├── auth          # Authentication, users, sessions, tokens
├── profile       # User profiles, preferences, expertise areas
├── github         # GitHub repositories, commits, pull requests
├── kb            # Knowledge base items, tags, embeddings
├── trend         # Trending topics, sources
├── content       # Drafts, revisions, briefs, ideas
├── style         # Style profiles, signals
├── platform      # Platform connections, schedules, publish logs
├── analytics     # Aggregated analytics data
└── notification  # Notification logs
```

All services share one database in MVP (schema-level isolation). Migration path:
- When any schema exceeds 50GB → extract to dedicated database
- When any table exceeds 500 writes/sec → partition or shard

---

## 2. Table Definitions

### 2.1 `auth` Schema

```sql
-- auth.users
CREATE TABLE auth.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255),             -- NULL for OAuth-only users
    display_name    VARCHAR(100) NOT NULL,
    avatar_url      TEXT,
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at  TIMESTAMPTZ,
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- auth.user_auth_providers
CREATE TABLE auth.user_auth_providers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider        VARCHAR(50) NOT NULL,      -- 'google', 'github', 'linkedin', 'email'
    external_id     VARCHAR(255) NOT NULL,      -- Provider's user ID
    UNIQUE (provider, external_id)
);

-- auth.sessions
CREATE TABLE auth.sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    refresh_token   VARCHAR(255) NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    is_revoked      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ
);

-- auth.platform_tokens
CREATE TABLE auth.platform_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform        VARCHAR(50) NOT NULL,      -- 'linkedin', 'github', 'twitter'
    encrypted_access_token   TEXT NOT NULL,
    encrypted_refresh_token  TEXT,
    expires_at      TIMESTAMPTZ,
    token_metadata  JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, platform)
);
```

### 2.2 `profile` Schema

```sql
-- profile.user_profiles
CREATE TABLE profile.user_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    bio             TEXT,
    avatar_url      TEXT,
    linkedin_url    TEXT,
    github_username VARCHAR(100),
    onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- profile.expertise_areas
CREATE TABLE profile.expertise_areas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL,      -- 'ai', 'programming', 'infra', 'research'
    priority        INT NOT NULL DEFAULT 1,
    keywords        JSONB NOT NULL DEFAULT '[]',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, name)
);

-- profile.user_preferences
CREATE TABLE profile.user_preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    posting_cadence VARCHAR(20) NOT NULL DEFAULT 'daily',
    timezone        VARCHAR(50) NOT NULL DEFAULT 'UTC',
    brief_hour      INT NOT NULL DEFAULT 8,
    default_tone    VARCHAR(20) NOT NULL DEFAULT 'conversational',
    default_length  VARCHAR(10) NOT NULL DEFAULT 'medium',
    digest_enabled  BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_cadence CHECK (posting_cadence IN ('daily', 'weekdays', 'mon_wed_fri', 'weekly')),
    CONSTRAINT valid_tone CHECK (default_tone IN ('conversational', 'professional', 'technical', 'inspirational')),
    CONSTRAINT valid_length CHECK (default_length IN ('short', 'medium', 'long')),
    CONSTRAINT valid_brief_hour CHECK (brief_hour >= 0 AND brief_hour <= 23)
);
```

### 2.3 `github` Schema

```sql
-- github.repositories
CREATE TABLE github.repositories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    external_id     BIGINT NOT NULL,
    name            VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    description     TEXT,
    url             TEXT NOT NULL,
    language        VARCHAR(50),
    languages       JSONB NOT NULL DEFAULT '{}',
    topics          JSONB NOT NULL DEFAULT '[]',
    stars           INT NOT NULL DEFAULT 0,
    forks           INT NOT NULL DEFAULT 0,
    is_archived     BOOLEAN NOT NULL DEFAULT FALSE,
    last_push_at    TIMESTAMPTZ,
    is_analyzed     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, external_id)
);

-- github.commits
CREATE TABLE github.commits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    repo_id         UUID NOT NULL REFERENCES github.repositories(id) ON DELETE CASCADE,
    sha             VARCHAR(40) NOT NULL,
    message         TEXT NOT NULL,
    author_name     VARCHAR(255) NOT NULL,
    author_avatar   TEXT,
    committed_at    TIMESTAMPTZ NOT NULL,
    url             TEXT NOT NULL,
    files_changed   JSONB NOT NULL DEFAULT '[]',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, sha)
);

-- github.pull_requests
CREATE TABLE github.pull_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    repo_id         UUID NOT NULL REFERENCES github.repositories(id) ON DELETE CASCADE,
    external_id     INT NOT NULL,
    title           VARCHAR(255) NOT NULL,
    body            TEXT,
    state           VARCHAR(10) NOT NULL,       -- 'open', 'merged', 'closed'
    created_at      TIMESTAMPTZ NOT NULL,
    merged_at       TIMESTAMPTZ,
    url             TEXT NOT NULL,
    labels          JSONB NOT NULL DEFAULT '[]',
    UNIQUE (user_id, repo_id, external_id)
);
```

### 2.4 `kb` Schema

```sql
-- kb.knowledge_items
CREATE TABLE kb.knowledge_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    url                 TEXT,
    title               VARCHAR(500) NOT NULL,
    summary             TEXT,
    extracted_text      TEXT,
    notes               TEXT,
    source_type         VARCHAR(20) NOT NULL,    -- 'url', 'note', 'pdf', 'import'
    content_type        VARCHAR(20) NOT NULL,    -- 'article', 'paper', 'tutorial', 'idea', 'reference', 'other'
    metadata            JSONB NOT NULL DEFAULT '{}',
    reading_time_minutes INT,
    processing_status   VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    saved_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_source_type CHECK (source_type IN ('url', 'note', 'pdf', 'import')),
    CONSTRAINT valid_content_type CHECK (content_type IN ('article', 'paper', 'tutorial', 'idea', 'reference', 'other'))
);

-- kb.knowledge_tags
CREATE TABLE kb.knowledge_tags (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_item_id UUID NOT NULL REFERENCES kb.knowledge_items(id) ON DELETE CASCADE,
    tag             VARCHAR(50) NOT NULL,
    is_auto_generated BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (knowledge_item_id, tag)
);

-- kb.knowledge_embeddings
CREATE TABLE kb.knowledge_embeddings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_item_id   UUID NOT NULL UNIQUE REFERENCES kb.knowledge_items(id) ON DELETE CASCADE,
    embedding           vector(768) NOT NULL,         -- pgvector
    model_version       VARCHAR(50) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2.5 `trend` Schema

```sql
-- trend.trending_topics
CREATE TABLE trend.trending_topics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    source              VARCHAR(50) NOT NULL,         -- 'rss', 'arxiv', 'hackernews', 'reddit'
    source_url          TEXT,
    relevance_score     FLOAT NOT NULL DEFAULT 0.0,
    freshness_score     FLOAT NOT NULL DEFAULT 0.0,
    engagement_count    INT NOT NULL DEFAULT 0,
    related_keywords    JSONB NOT NULL DEFAULT '[]',
    first_seen_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- trend.trend_sources
CREATE TABLE trend.trend_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL UNIQUE,
    url             TEXT NOT NULL,
    source_type     VARCHAR(20) NOT NULL,             -- 'rss', 'api', 'scrape'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    poll_interval_minutes INT NOT NULL DEFAULT 60,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2.6 `content` Schema

```sql
-- content.content_drafts
CREATE TABLE content.content_drafts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title               VARCHAR(500) NOT NULL,
    body                TEXT NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',  -- 'draft', 'approved', 'scheduled', 'published', 'archived'
    tone                VARCHAR(20),
    length              VARCHAR(10),
    content_type        VARCHAR(30),                           -- ContentCategory enum value
    generation_metadata JSONB NOT NULL DEFAULT '{}',
    quality_scores      JSONB NOT NULL DEFAULT '{}',
    source_idea_id      UUID,                                  -- References brief_ideas.id
    revision            INT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'approved', 'scheduled', 'published', 'archived'))
);

-- content.draft_revisions
CREATE TABLE content.draft_revisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id        UUID NOT NULL REFERENCES content.content_drafts(id) ON DELETE CASCADE,
    body            TEXT NOT NULL,
    diff            TEXT,                                -- Unified diff from previous revision
    change_source   VARCHAR(50) NOT NULL,                -- 'generation', 'user_edit', 'regeneration', 'style_refine'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- content.content_briefs
CREATE TABLE content.content_briefs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    brief_date          DATE NOT NULL,
    context_summary     TEXT,
    signal_quality      JSONB NOT NULL DEFAULT '{}',
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    viewed_at           TIMESTAMPTZ,
    UNIQUE (user_id, brief_date)
);

-- content.brief_ideas
CREATE TABLE content.brief_ideas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id            UUID NOT NULL REFERENCES content.content_briefs(id) ON DELETE CASCADE,
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    category            VARCHAR(30) NOT NULL,
    relevance_score     FLOAT NOT NULL,
    novelty_score       FLOAT NOT NULL,
    source_type         VARCHAR(20) NOT NULL,            -- 'github', 'knowledge', 'trend', 'mixed'
    source_detail       TEXT,
    source_knowledge_item_id UUID,                       -- References kb.knowledge_items(id)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2.7 `style` Schema

```sql
-- style.style_profiles
CREATE TABLE style.style_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    voice_embedding     vector(768),                     -- pgvector, NULL until first signal
    style_params        JSONB NOT NULL DEFAULT '{}',
    learning_rate       FLOAT NOT NULL DEFAULT 0.1,
    confidence          FLOAT NOT NULL DEFAULT 0.0,
    total_ratings       INT NOT NULL DEFAULT 0,
    total_edits         INT NOT NULL DEFAULT 0,
    total_approved      INT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- style.style_signals
CREATE TABLE style.style_signals (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id          UUID NOT NULL REFERENCES style.style_profiles(id) ON DELETE CASCADE,
    source_draft_id     UUID,                            -- References content.content_drafts(id)
    signal_type         VARCHAR(30) NOT NULL,             -- 'rating', 'edit', 'approval', 'rejection', 'import'
    signal_data         JSONB NOT NULL,
    weight              FLOAT NOT NULL DEFAULT 1.0,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- style.ratings
CREATE TABLE style.ratings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    draft_id        UUID NOT NULL REFERENCES content.content_drafts(id) ON DELETE CASCADE,
    score           INT NOT NULL CHECK (score >= 1 AND score <= 5),
    comment         TEXT,
    dimension_scores JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, draft_id)
);
```

### 2.8 `platform` Schema

```sql
-- platform.platform_connections
CREATE TABLE platform.platform_connections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform        VARCHAR(20) NOT NULL,                  -- 'linkedin', 'twitter'
    external_user_id VARCHAR(255),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    connected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_sync_at    TIMESTAMPTZ,
    UNIQUE (user_id, platform)
);

-- platform.scheduled_posts
CREATE TABLE platform.scheduled_posts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id            UUID NOT NULL REFERENCES content.content_drafts(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform            VARCHAR(20) NOT NULL,
    scheduled_for       TIMESTAMPTZ NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'published', 'failed', 'cancelled'
    external_post_id    VARCHAR(255),
    format_params       JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_schedule_status CHECK (status IN ('pending', 'published', 'failed', 'cancelled'))
);

-- platform.publish_logs
CREATE TABLE platform.publish_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheduled_post_id   UUID REFERENCES platform.scheduled_posts(id) ON DELETE SET NULL,
    draft_id            UUID REFERENCES content.content_drafts(id) ON DELETE SET NULL,
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform            VARCHAR(20) NOT NULL,
    status              VARCHAR(20) NOT NULL,              -- 'success', 'failed'
    response            JSONB,
    error_message       TEXT,
    attempt_number      INT NOT NULL DEFAULT 1,
    attempted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- platform.analytics_cache
CREATE TABLE platform.analytics_cache (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform            VARCHAR(20) NOT NULL,
    external_post_id    VARCHAR(255) NOT NULL,
    data                JSONB NOT NULL,
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, platform, external_post_id)
);
```

### 2.9 `notification` Schema

```sql
-- notification.notification_logs
CREATE TABLE notification.notification_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    notification_type   VARCHAR(50) NOT NULL,
    channel             VARCHAR(20) NOT NULL,             -- 'in_app', 'email', 'push'
    title               VARCHAR(255) NOT NULL,
    body                TEXT NOT NULL,
    payload             JSONB,
    is_read             BOOLEAN NOT NULL DEFAULT FALSE,
    delivered           BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at             TIMESTAMPTZ
);

-- notification.notification_preferences
CREATE TABLE notification.notification_preferences (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    email_digest_frequency  VARCHAR(10) NOT NULL DEFAULT 'daily',
    brief_notifications     BOOLEAN NOT NULL DEFAULT TRUE,
    publish_notifications   BOOLEAN NOT NULL DEFAULT TRUE,
    engagement_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    marketing_emails        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 3. Migration Scripts

### 3.1 Initial Migration (MVP)

```python
# migrations/versions/0001_initial_schema.py
"""initial schema

Revision ID: 0001
Create Date: 2026-06-26 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = '0001'
down_revision = None

def upgrade():
    # Create schemas
    for schema in ['auth', 'profile', 'github', 'kb', 'trend', 'content', 'style', 'platform', 'notification']:
        op.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')

    # Enable pgvector
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # --- Auth Schema ---
    op.create_table(
        'users', sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_active_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='auth'
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True, schema='auth')

    # Additional tables follow same pattern for all schemas...
    # Full migration script generated from table definitions in Section 2.

def downgrade():
    for schema in ['notification', 'platform', 'style', 'content', 'trend', 'kb', 'github', 'profile', 'auth']:
        op.execute(f'DROP SCHEMA IF EXISTS {schema} CASCADE')
```

### 3.2 Migration: Add Vector Index (Phase 2)

```python
# migrations/versions/0002_add_vector_indexes.py
"""add vector indexes

Revision ID: 0002
Revises: 0001
"""

def upgrade():
    # HNSW index for knowledge base embeddings
    # IVF index is simpler for MVP but HNSW provides better recall-speed trade-off
    op.execute("""
        CREATE INDEX idx_kb_embeddings_hnsw
        ON kb.knowledge_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200);
    """)

    # HNSW index for style profile voice embeddings
    op.execute("""
        CREATE INDEX idx_style_voice_hnsw
        ON style.style_profiles
        USING hnsw (voice_embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200);
    """)

def downgrade():
    op.execute('DROP INDEX IF EXISTS idx_kb_embeddings_hnsw')
    op.execute('DROP INDEX IF EXISTS idx_style_voice_hnsw')
```

### 3.3 Migration: Partition Content Tables (Phase 3)

```python
# migrations/versions/0003_partition_content.py
"""partition content tables by user_id hash

Revision ID: 0003
Revises: 0002
"""

def upgrade():
    # Convert content_drafts to partitioned table
    op.execute("""
        CREATE TABLE content.content_drafts_partitioned (
            LIKE content.content_drafts INCLUDING DEFAULTS INCLUDING CONSTRAINTS
        ) PARTITION BY HASH (user_id);
    """)

    # Create 8 partitions
    for i in range(8):
        op.execute(f"""
            CREATE TABLE content.content_drafts_p{i}
            PARTITION OF content.content_drafts_partitioned
            FOR VALUES WITH (MODULUS 8, REMAINDER {i});
        """)

    # Migrate data (in maintenance window)
    op.execute("""
        INSERT INTO content.content_drafts_partitioned
        SELECT * FROM content.content_drafts;
    """)

    op.execute('DROP TABLE content.content_drafts CASCADE')
    op.execute('ALTER TABLE content.content_drafts_partitioned RENAME TO content_drafts')

def downgrade():
    op.execute('DROP TABLE IF EXISTS content.content_drafts CASCADE')
    op.execute('ALTER TABLE content.content_drafts RENAME TO content_drafts_unpartitioned')
```

---

## 4. Indexing Strategy

### 4.1 B-Tree Indexes

```sql
-- Auth: Fast user lookup by email
CREATE UNIQUE INDEX idx_users_email ON auth.users (email);

-- Auth: Fast session lookup by refresh token
CREATE INDEX idx_sessions_refresh_token ON auth.sessions (refresh_token);
CREATE INDEX idx_sessions_user_id ON auth.sessions (user_id) WHERE is_revoked = FALSE;

-- Auth: Active platform tokens per user
CREATE INDEX idx_platform_tokens_user ON auth.platform_tokens (user_id, platform);

-- Profile: Expertise areas for brief context gathering
CREATE INDEX idx_expertise_user_id ON profile.expertise_areas (user_id);

-- GitHub: Recent commits per user (for brief generation)
CREATE INDEX idx_commits_user_date ON github.commits (user_id, committed_at DESC);
CREATE INDEX idx_commits_repo_date ON github.commits (repo_id, committed_at DESC);
CREATE INDEX idx_prs_user_state ON github.pull_requests (user_id, state);

-- KB: Recent items per user
CREATE INDEX idx_kb_items_user_date ON kb.knowledge_items (user_id, saved_at DESC);
CREATE INDEX idx_kb_items_user_type ON kb.knowledge_items (user_id, content_type);

-- KB: Tag-based queries
CREATE INDEX idx_kb_tags_tag ON kb.knowledge_tags (tag);
CREATE INDEX idx_kb_tags_item ON kb.knowledge_tags (knowledge_item_id);

-- Content: Drafts by user and status
CREATE INDEX idx_drafts_user_status ON content.content_drafts (user_id, status);
CREATE INDEX idx_drafts_user_date ON content.content_drafts (user_id, created_at DESC);

-- Content: Briefs by user and date
CREATE UNIQUE INDEX idx_briefs_user_date ON content.content_briefs (user_id, brief_date);
CREATE INDEX idx_briefs_generated_at ON content.content_briefs (generated_at);

-- Content: Ideas by brief
CREATE INDEX idx_brief_ideas_brief ON content.brief_ideas (brief_id);

-- Platform: Scheduled posts
CREATE INDEX idx_scheduled_status_date ON platform.scheduled_posts (status, scheduled_for)
    WHERE status = 'pending';
CREATE INDEX idx_scheduled_user_date ON platform.scheduled_posts (user_id, scheduled_for);

-- Platform: Publish logs
CREATE INDEX idx_publish_logs_user ON platform.publish_logs (user_id, attempted_at DESC);

-- Notification: Unread notifications
CREATE INDEX idx_notif_user_unread ON notification.notification_logs (user_id, is_read)
    WHERE is_read = FALSE;
```

### 4.2 Full-Text Search Indexes

```sql
-- KB items: Full-text search on title and extracted text
CREATE INDEX idx_kb_items_fts ON kb.knowledge_items
    USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(extracted_text, '')));

-- Drafts: Full-text search on title and body
CREATE INDEX idx_drafts_fts ON content.content_drafts
    USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(body, '')));
```

### 4.3 GiST/SP-GiST Indexes

```sql
-- JSONB queries on generation metadata
CREATE INDEX idx_drafts_gen_metadata ON content.content_drafts
    USING gin (generation_metadata);

-- JSONB style params
CREATE INDEX idx_style_params ON style.style_profiles
    USING gin (style_params);
```

### 4.4 Composite Indexes for Common Queries

```sql
-- Brief generation: get all signals for a user
CREATE INDEX idx_signals_profile_type ON style.style_signals (profile_id, signal_type, recorded_at DESC);

-- Dashboard: recent activity for a user
CREATE INDEX idx_drafts_user_status_date ON content.content_drafts (user_id, status, updated_at DESC);

-- Analytics: user posts within date range
CREATE INDEX idx_scheduled_user_published ON platform.scheduled_posts (user_id, status, published_at DESC)
    WHERE status = 'published';
```

### 4.5 Unique Constraints

```sql
-- All single-user unique names
auth.users (email)                                  -- Unique email
auth.platform_tokens (user_id, platform)             -- One token per platform per user
profile.user_profiles (user_id)                      -- One profile per user
profile.expertise_areas (user_id, name)              -- Unique expertise name per user
profile.user_preferences (user_id)                   -- One preferences row per user
github.repositories (user_id, external_id)           -- No duplicate repo tracking
github.commits (user_id, sha)                        -- No duplicate commits
github.pull_requests (user_id, repo_id, external_id) -- No duplicate PRs
kb.knowledge_tags (knowledge_item_id, tag)           -- No duplicate tags on an item
content.content_briefs (user_id, brief_date)          -- One brief per day per user
style.style_profiles (user_id)                       -- One style profile per user
style.ratings (user_id, draft_id)                    -- One rating per draft per user
notification.notification_preferences (user_id)      -- One preferences row per user
```

---

## 5. Query Patterns

### 5.1 Brief Generation Query

```sql
-- Get all context for a user's daily brief generation
WITH user_data AS (
    SELECT u.id, u.display_name
    FROM auth.users u
    WHERE u.id = :user_id AND u.is_active = TRUE
),
recent_commits AS (
    SELECT c.message, c.committed_at, c.files_changed, r.full_name as repo_name
    FROM github.commits c
    JOIN github.repositories r ON r.id = c.repo_id
    WHERE c.user_id = :user_id
      AND c.committed_at >= NOW() - INTERVAL '7 days'
    ORDER BY c.committed_at DESC
    LIMIT 20
),
recent_prs AS (
    SELECT pr.title, pr.body, pr.state, r.full_name as repo_name
    FROM github.pull_requests pr
    JOIN github.repositories r ON r.id = pr.repo_id
    WHERE pr.user_id = :user_id
      AND pr.created_at >= NOW() - INTERVAL '7 days'
    ORDER BY pr.created_at DESC
    LIMIT 10
),
recent_kb AS (
    SELECT ki.title, ki.summary, ki.content_type, ki.saved_at,
           array_agg(kt.tag) as tags
    FROM kb.knowledge_items ki
    LEFT JOIN kb.knowledge_tags kt ON kt.knowledge_item_id = ki.id
    WHERE ki.user_id = :user_id
      AND ki.saved_at >= NOW() - INTERVAL '14 days'
    GROUP BY ki.id
    ORDER BY ki.saved_at DESC
    LIMIT 20
),
expertise AS (
    SELECT name, category, keywords
    FROM profile.expertise_areas
    WHERE user_id = :user_id
    ORDER BY priority ASC
)
SELECT * FROM user_data, recent_commits, recent_prs, recent_kb, expertise;
```

### 5.2 Style Profile Update Query

```sql
-- Update style profile after receiving a rating
WITH profile_update AS (
    UPDATE style.style_profiles
    SET
        total_ratings = total_ratings + 1,
        confidence = LEAST(
            1.0,
            (total_ratings + 1)::FLOAT / 50.0  -- 50 ratings = 100% confidence
        ),
        learning_rate = GREATEST(
            0.01,
            0.1 * (1.0 - (total_ratings + 1)::FLOAT / 100.0)
        ),
        style_params = jsonb_set(
            style_params,
            '{formality}',
            to_jsonb(
                style_params->>'formality'::FLOAT * (1.0 - learning_rate)
                + :formality_score * learning_rate
            )
        ),
        updated_at = NOW()
    WHERE user_id = :user_id
    RETURNING id, confidence, total_ratings
)
INSERT INTO style.style_signals (profile_id, source_draft_id, signal_type, signal_data, weight)
VALUES (
    (SELECT id FROM profile_update),
    :draft_id,
    'rating',
    jsonb_build_object('score', :score, 'dimensions', :dimensions::jsonb),
    :weight
);
```

### 5.3 Hybrid Search Query

```sql
-- Hybrid search: keyword + semantic with configurable weights
WITH keyword_results AS (
    SELECT
        ki.id,
        ki.title,
        ki.summary,
        ts_rank(
            to_tsvector('english', coalesce(ki.title, '') || ' ' || coalesce(ki.extracted_text, '')),
            plainto_tsquery('english', :search_text)
        ) * 0.3 AS keyword_score
    FROM kb.knowledge_items ki
    WHERE ki.user_id = :user_id
      AND to_tsvector('english', coalesce(ki.title, '') || ' ' || coalesce(ki.extracted_text, ''))
          @@ plainto_tsquery('english', :search_text)
),
semantic_results AS (
    SELECT
        ki.id,
        ke.embedding <=> :query_embedding::vector AS cosine_distance,
        1.0 - (ke.embedding <=> :query_embedding::vector) AS semantic_score
    FROM kb.knowledge_embeddings ke
    JOIN kb.knowledge_items ki ON ki.id = ke.knowledge_item_id
    WHERE ki.user_id = :user_id
    ORDER BY ke.embedding <=> :query_embedding::vector
    LIMIT :limit
),
combined AS (
    SELECT
        COALESCE(kr.id, sr.id) AS id,
        COALESCE(kr.keyword_score, 0.0) AS keyword_score,
        COALESCE(sr.semantic_score, 0.0) AS semantic_score,
        COALESCE(kr.keyword_score, 0.0) * 0.3 + COALESCE(sr.semantic_score, 0.0) * 0.7 AS hybrid_score
    FROM keyword_results kr
    FULL OUTER JOIN semantic_results sr ON sr.id = kr.id
)
SELECT
    ki.*,
    c.hybrid_score,
    CASE
        WHEN c.keyword_score > c.semantic_score THEN 'keyword'
        WHEN c.semantic_score > c.keyword_score THEN 'semantic'
        ELSE 'hybrid'
    END AS match_type
FROM combined c
JOIN kb.knowledge_items ki ON ki.id = c.id
ORDER BY c.hybrid_score DESC
LIMIT :limit OFFSET :offset;
```

### 5.4 Pending Scheduled Posts Query

```sql
-- Worker query: find scheduled posts due for publishing
SELECT
    sp.id AS schedule_id,
    sp.draft_id,
    sp.user_id,
    sp.platform,
    sp.format_params,
    cd.body AS draft_body,
    cd.title AS draft_title,
    cd.content_type,
    pt.encrypted_access_token,
    pt.encrypted_refresh_token,
    pt.expires_at AS token_expires_at
FROM platform.scheduled_posts sp
JOIN content.content_drafts cd ON cd.id = sp.draft_id
JOIN auth.platform_tokens pt ON pt.user_id = sp.user_id AND pt.platform = sp.platform
WHERE sp.status = 'pending'
  AND sp.scheduled_for <= NOW()
  AND sp.scheduled_for >= NOW() - INTERVAL '1 hour'
FOR UPDATE OF sp SKIP LOCKED
LIMIT 10;
```

### 5.5 Analytics Overview Query

```sql
-- Aggregate post performance for dashboard
WITH post_stats AS (
    SELECT
        sp.user_id,
        COUNT(*) AS total_posts,
        COUNT(*) FILTER (WHERE sp.status = 'published') AS total_published,
        COUNT(*) FILTER (WHERE sp.status = 'failed') AS total_failed,
        MAX(sp.published_at) AS last_publish_at
    FROM platform.scheduled_posts sp
    WHERE sp.user_id = :user_id
      AND sp.created_at >= :start_date
      AND sp.created_at <= :end_date
    GROUP BY sp.user_id
),
engagement_stats AS (
    SELECT
        ac.user_id,
        SUM((ac.data->>'impressions')::INT) AS total_impressions,
        SUM((ac.data->>'engagement_count')::INT) AS total_engagement,
        AVG((ac.data->>'engagement_rate')::FLOAT) AS avg_engagement_rate
    FROM platform.analytics_cache ac
    WHERE ac.user_id = :user_id
      AND ac.fetched_at >= :start_date
    GROUP BY ac.user_id
),
follower_stats AS (
    SELECT
        user_id,
        (data->>'follower_count')::INT AS current_followers
    FROM platform.analytics_cache ac
    WHERE ac.user_id = :user_id
      AND ac.platform = 'linkedin'
      AND ac.external_post_id = '__profile__'
    ORDER BY ac.fetched_at DESC
    LIMIT 1
)
SELECT
    COALESCE(ps.total_published, 0) AS total_published,
    COALESCE(es.total_impressions, 0) AS total_impressions,
    COALESCE(es.total_engagement, 0) AS total_engagement,
    COALESCE(es.avg_engagement_rate, 0.0) AS avg_engagement_rate,
    COALESCE(fs.current_followers, 0) AS current_followers
FROM post_stats ps
LEFT JOIN engagement_stats es ON es.user_id = ps.user_id
LEFT JOIN follower_stats fs ON fs.user_id = ps.user_id;
```

---

## 6. Partitioning Strategy

### 6.1 When to Partition

| Table | Partition Key | Trigger | Partition Count |
|-------|---------------|---------|-----------------|
| `content.content_drafts` | HASH (user_id) | > 5M rows | 8 |
| `content.draft_revisions` | HASH (draft_id) | > 10M rows | 8 |
| `platform.scheduled_posts` | HASH (user_id) | > 1M rows | 4 |
| `platform.publish_logs` | RANGE (attempted_at) | > 5M rows | Monthly |
| `notification.notification_logs` | RANGE (sent_at) | > 10M rows | Monthly |
| `kb.knowledge_items` | HASH (user_id) | > 20M rows | 12 |

### 6.2 Time-Based Partitioning (Publish Logs)

```sql
-- Monthly partitioning for publish logs
CREATE TABLE platform.publish_logs (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    platform VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, attempted_at)
) PARTITION BY RANGE (attempted_at);

-- Create partitions
CREATE TABLE platform.publish_logs_2026_06
    PARTITION OF platform.publish_logs
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE platform.publish_logs_2026_07
    PARTITION OF platform.publish_logs
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
```

### 6.3 Partition Management

```sql
-- Create new partition (run monthly via cron)
SELECT create_publish_log_partition('2026-08');

-- Detach old partition for archival (retention: 12 months)
ALTER TABLE platform.publish_logs DETACH PARTITION platform.publish_logs_2025_06;

-- Archive to S3 before dropping
-- ... (data export job) ...
DROP TABLE platform.publish_logs_2025_06;
```

---

## 7. Backup & Recovery

### 7.1 Backup Schedule

| Type | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| **Full database** | Daily | 30 days | `pg_dump -Fc` |
| **WAL archive** | Continuous | 7 days | WAL archiving to S3 |
| **Point-in-time recovery** | On-demand | 7 days | WAL replay |

### 7.2 Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
BACKUP_FILE="brandos_full_${TIMESTAMP}.dump"
S3_PATH="s3://brandos-backups/database/"

# Full backup
pg_dump -Fc \
    -h $PGHOST \
    -U $PGUSER \
    -d $PGDATABASE \
    --no-owner \
    --compress=9 \
    -f $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE $S3_PATH

# Cleanup old backups (local)
find . -name "brandos_full_*.dump" -mtime +7 -delete

# Cleanup old backups (S3)
aws s3 ls $S3_PATH | while read -r line; do
    createDate=$(echo $line | awk '{print $1" "$2}')
    createDate=$(date -d "$createDate" +%s)
    olderThan=$(date -d "-30 days" +%s)
    if [[ $createDate -lt $olderThan ]]; then
        fileName=$(echo $line | awk '{print $4}')
        aws s3 rm "${S3_PATH}${fileName}"
    fi
done
```

### 7.3 Recovery Procedures

```sql
-- Point-in-time recovery
-- 1. Stop application
-- 2. Restore base backup
pg_restore -Fc -d brandos -h $PGHOST -U $PGUSER brandos_full_20260626_120000.dump

-- 3. Replay WAL to target time
-- (using pg_rewind or full WAL restore)

-- 4. Verify data integrity
SELECT COUNT(*) FROM auth.users;
SELECT COUNT(*) FROM content.content_drafts;

-- 5. Resume application
```

---

## 8. Connection Pooling

```python
# Module: shared/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Engine configuration
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,         # Default: 20
    max_overflow=settings.database_max_overflow,    # Default: 10
    pool_pre_ping=True,                             # Verify connections before use
    pool_recycle=3600,                              # Recycle connections after 1 hour
    echo=settings.database_echo,
    json_serializer=orjson.dumps,
    json_deserializer=orjson.loads,
)

# For read replicas (Phase 2+)
reader_engine = create_async_engine(
    settings.database_reader_url,
    pool_size=40,                                   # More connections for analytics
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
reader_session = sessionmaker(reader_engine, class_=AsyncSession, expire_on_commit=False)
```

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-06-26 | Architecture Team | Initial draft |

---

*This document defines the complete database design for BrandOS. Every table, index, migration, and query pattern is specified. The design follows MVP constraints: single PostgreSQL instance with schema isolation, scaling to partitioned tables as data volume grows.*
