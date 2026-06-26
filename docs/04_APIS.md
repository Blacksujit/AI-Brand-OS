# API Contract Specification: BrandOS

## Document Info

| Field | Value |
|-------|-------|
| **Author** | Architecture Team |
| **Status** | Draft |
| **Created** | 2026-06-26 |
| **Last Updated** | 2026-06-26 |
| **Base URL** | `https://api.brandos.app/v1` |
| **Protocol** | REST over HTTPS |
| **Auth** | JWT Bearer Token |

---

## Table of Contents

- [Common Patterns](#1-common-patterns)
- [Authentication API](#2-authentication-api)
- [Profile API](#3-profile-api)
- [Connections API](#4-connections-api)
- [Knowledge Base API](#5-knowledge-base-api)
- [Content API](#6-content-api)
- [Publishing API](#7-publishing-api)
- [Analytics API](#8-analytics-api)
- [Admin API](#9-admin-api)
- [Webhooks](#10-webhooks)
- [Appendix: Error Codes](#11-appendix-error-codes)

---

## 1. Common Patterns

### 1.1 Authentication

All endpoints except `/auth/*` and `/health` require a JWT Bearer token:

```
Authorization: Bearer <access_token>
```

Token lifecycle:
- **Access token**: 15-minute TTL. Sent in `Authorization` header.
- **Refresh token**: 7-day TTL (rotating). Sent in `POST /auth/refresh`.
- **Token refresh**: When server returns `401 TOKEN_EXPIRED`, client calls `POST /auth/refresh` with the refresh token.

### 1.2 Response Envelope

All responses follow this structure:

```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-06-26T12:00:00Z",
    "version": "0.1.0"
  }
}
```

### 1.3 Error Envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "fields": [
        {"field": "email", "message": "Invalid email format", "code": "INVALID_FORMAT"}
      ]
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-06-26T12:00:00Z"
  }
}
```

### 1.4 Pagination

Paginated endpoints accept:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `page_size` | integer | 20 | Items per page (max 100) |

Response includes:

```json
{
  "data": [ ... ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 142,
    "has_more": true,
    "request_id": "req_abc123"
  }
}
```

### 1.5 Idempotency

All mutation endpoints support idempotency via the `Idempotency-Key` header:

```
Idempotency-Key: <uuid>
```

- Same key + same request body → returns cached response (24-hour window)
- Same key + different body → `409 CONFLICT`
- Responses cached for 24 hours in Redis

### 1.6 Rate Limiting

| Scope | Limit | Headers Returned |
|-------|-------|------------------|
| Per-user (authenticated) | 100 req/min | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| Per-IP (unauthenticated) | 30 req/min | Same |
| LLM endpoints | 5 req/min/user | Same |
| Publish endpoints | 10 req/min/user | Same |

Rate limit exceeded: `429 TOO_MANY_REQUESTS` with `Retry-After` header.

### 1.7 Common Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | On protected routes | `Bearer <jwt>` |
| `Content-Type` | On POST/PUT/PATCH | `application/json` |
| `Idempotency-Key` | On mutations | UUID v4 |
| `Accept-Language` | Optional | Locale preference |

---

## 2. Authentication API

### `POST /auth/register`

Create a new email/password account.

**Request:**
```json
{
  "email": "alex@example.com",
  "password": "securePassword123",
  "display_name": "Alex Chen"
}
```

**Validation:**
- `email`: Valid email format, max 255 chars, unique
- `password`: Min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit
- `display_name`: 1-100 chars

**Response `201 Created`:**
```json
{
  "data": {
    "user_id": "uuid",
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "rt_abc123...",
    "expires_at": "2026-06-26T12:15:00Z",
    "is_new_user": true
  }
}
```

**Errors:** `409 CONFLICT` (email exists), `422 UNPROCESSABLE ENTITY` (validation)

---

### `POST /auth/login`

Authenticate with email and password.

**Request:**
```json
{
  "email": "alex@example.com",
  "password": "securePassword123"
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "user_id": "uuid",
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "rt_abc123...",
    "expires_at": "2026-06-26T12:15:00Z",
    "is_new_user": false
  }
}
```

**Errors:** `401 UNAUTHORIZED` (invalid credentials)

---

### `POST /auth/oauth/{provider}`

Authenticate with OAuth provider.

**Parameters:** `provider` = `google` | `github` | `linkedin`

**Request:**
```json
{
  "auth_code": "abc123...",
  "redirect_uri": "https://app.brandos.app/auth/callback"
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "user_id": "uuid",
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "rt_abc123...",
    "expires_at": "2026-06-26T12:15:00Z",
    "is_new_user": false
  }
}
```

---

### `POST /auth/oauth/{provider}/initiate`

Get OAuth authorization URL (for OAuth flow initiation).

**Parameters:** `provider` = `google` | `github` | `linkedin`

**Request:**
```json
{
  "redirect_uri": "https://app.brandos.app/auth/callback"
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "authorization_url": "https://github.com/login/oauth/authorize?...",
    "state": "state_abc123",
    "code_verifier": "verifier_abc123"
  }
}
```

---

### `POST /auth/refresh`

Refresh access token.

**Request:**
```json
{
  "refresh_token": "rt_abc123..."
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "rt_def456...",
    "expires_at": "2026-06-26T12:15:00Z"
  }
}
```

**Note:** The old refresh token is invalidated (rotating refresh tokens).

---

### `POST /auth/logout`

Revoke current session.

**Headers:** `Authorization: Bearer <access_token>`

**Response `204 No Content`**

---

### `GET /auth/me`

Get current user info.

**Headers:** `Authorization: Bearer <access_token>`

**Response `200 OK`:**
```json
{
  "data": {
    "user_id": "uuid",
    "email": "alex@example.com",
    "display_name": "Alex Chen",
    "avatar_url": "https://...",
    "created_at": "2026-06-01T00:00:00Z",
    "email_verified": true,
    "auth_providers": ["google", "github"]
  }
}
```

---

## 3. Profile API

### `GET /profiles/me`

Get the authenticated user's profile.

**Response `200 OK`:**
```json
{
  "data": {
    "user_id": "uuid",
    "display_name": "Alex Chen",
    "bio": "ML Engineer building production AI systems",
    "avatar_url": "https://...",
    "linkedin_url": "https://linkedin.com/in/alexchen",
    "github_username": "alexchen",
    "expertise_areas": [
      {"id": "uuid", "name": "Machine Learning", "category": "ai", "priority": 1, "keywords": ["transformers", "nlp", "computer vision"]},
      {"id": "uuid", "name": "Python", "category": "programming", "priority": 2, "keywords": ["fastapi", "pytorch", "asyncio"]}
    ],
    "created_at": "2026-06-01T00:00:00Z"
  }
}
```

---

### `PATCH /profiles/me`

Update profile.

**Request:**
```json
{
  "display_name": "Alex Chen",
  "bio": "Updated bio...",
  "avatar_url": "https://new-avatar.url"
}
```

All fields optional. Only provided fields are updated.

**Response `200 OK`:** Full profile object.

---

### `GET /profiles/me/preferences`

Get user preferences.

**Response `200 OK`:**
```json
{
  "data": {
    "posting_cadence": "daily",
    "timezone": "America/New_York",
    "brief_hour": 8,
    "default_tone": "conversational",
    "default_length": "medium",
    "digest_enabled": true
  }
}
```

---

### `PATCH /profiles/me/preferences`

Update preferences.

**Request:**
```json
{
  "posting_cadence": "daily",
  "timezone": "America/New_York",
  "brief_hour": 8,
  "default_tone": "conversational",
  "default_length": "medium",
  "digest_enabled": true
}
```

All fields optional.

---

### `GET /profiles/me/expertise`

List expertise areas.

**Response `200 OK`:**
```json
{
  "data": [
    {"id": "uuid", "name": "Machine Learning", "category": "ai", "priority": 1, "keywords": ["transformers", "nlp"]}
  ]
}
```

---

### `POST /profiles/me/expertise`

Add expertise area.

**Request:**
```json
{
  "name": "Rust",
  "category": "programming",
  "priority": 3,
  "keywords": ["systems programming", "cargo", "tokio"]
}
```

**Response `201 Created`:** Expertise area object.

---

### `DELETE /profiles/me/expertise/{id}`

Remove expertise area.

**Response `204 No Content`**

---

## 4. Connections API

### `POST /connections/github`

Connect GitHub account.

**Request:**
```json
{
  "access_token": "gho_abc123..."
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "success": true,
    "platform": "github",
    "external_user_id": "12345",
    "username": "alexchen",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
    "connected_at": "2026-06-26T12:00:00Z"
  }
}
```

---

### `DELETE /connections/github`

Disconnect GitHub account.

**Response `204 No Content`**

---

### `POST /connections/linkedin`

Connect LinkedIn account.

**Request:**
```json
{
  "access_token": "AQV...",
  "refresh_token": "AQX..."
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "success": true,
    "platform": "linkedin",
    "external_user_id": "urn:li:person:abc123",
    "vanity_name": "alexchen",
    "connected_at": "2026-06-26T12:00:00Z"
  }
}
```

---

### `DELETE /connections/linkedin`

Disconnect LinkedIn account.

**Response `204 No Content`**

---

### `GET /connections/status`

Get all platform connection statuses.

**Response `200 OK`:**
```json
{
  "data": {
    "github": {
      "is_connected": true,
      "external_user_id": "12345",
      "username": "alexchen",
      "connected_at": "2026-06-01T00:00:00Z",
      "last_sync_at": "2026-06-26T06:00:00Z",
      "token_expires_at": null,
      "is_token_valid": true
    },
    "linkedin": {
      "is_connected": true,
      "external_user_id": "urn:li:person:abc123",
      "connected_at": "2026-06-01T00:00:00Z",
      "last_sync_at": "2026-06-26T06:00:00Z",
      "token_expires_at": "2026-07-01T00:00:00Z",
      "is_token_valid": true
    }
  }
}
```

---

## 5. Knowledge Base API

### `GET /kb/items`

List knowledge base items.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `page_size` | integer | Items per page |
| `tags` | string (comma-separated) | Filter by tags |
| `content_type` | string | Filter by type: article, paper, tutorial, idea, reference |
| `source_type` | string | Filter by source: url, note, pdf, import |
| `sort` | string | `created_desc` (default), `created_asc`, `title_asc` |
| `search` | string | Full-text search query |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "uuid",
      "url": "https://arxiv.org/abs/2301.12345",
      "title": "Attention Is All You Need: A Modern Retrospective",
      "summary": "This paper revisits the transformer architecture...",
      "tags": ["transformers", "attention", "nlp", "paper"],
      "source_type": "url",
      "content_type": "paper",
      "reading_time_minutes": 12,
      "created_at": "2026-06-25T12:00:00Z",
      "updated_at": "2026-06-25T12:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 47,
    "has_more": true,
    "request_id": "req_abc123"
  }
}
```

---

### `POST /kb/items`

Add a knowledge base item.

**Request:**
```json
{
  "url": "https://arxiv.org/abs/2301.12345",
  "title": "Attention Is All You Need: A Modern Retrospective",
  "notes": "Key insight: the architecture scales better than I thought",
  "tags": ["transformers", "attention"],
  "source_type": "url",
  "content_type": "paper"
}
```

**Validation:**
- At least one of `url` or `notes` must be provided
- `title`: 1-500 chars
- `tags`: Max 20 tags, each 1-50 chars
- `url`: Valid URL format if provided

**Response `201 Created`:**
```json
{
  "data": {
    "id": "uuid",
    "url": "https://arxiv.org/abs/2301.12345",
    "title": "Attention Is All You Need: A Modern Retrospective",
    "summary": "This paper revisits the transformer architecture...",
    "tags": ["transformers", "attention", "nlp", "paper"],
    "source_type": "url",
    "content_type": "paper",
    "reading_time_minutes": 12,
    "created_at": "2026-06-26T12:00:00Z",
    "updated_at": "2026-06-26T12:00:00Z"
  }
}
```

**Processing:** The server will asynchronously extract content, generate summary, suggest tags, and create embeddings. The item is returned immediately; processing status is available via `GET /kb/items/{id}`.

---

### `GET /kb/items/{id}`

Get knowledge item details.

**Response `200 OK`:** Full knowledge item object.

---

### `PUT /kb/items/{id}`

Update knowledge item.

**Request:**
```json
{
  "title": "Updated title",
  "notes": "Updated notes",
  "tags": ["updated", "tags"]
}
```

**Response `200 OK`:** Updated knowledge item.

---

### `DELETE /kb/items/{id}`

Delete knowledge item.

**Response `204 No Content`**

---

### `GET /kb/items/{id}/related`

Get related knowledge items.

**Query Parameters:** `limit` (default: 5, max: 20)

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Related Paper Title",
      "summary": "...",
      "similarity_score": 0.87
    }
  ]
}
```

---

### `POST /kb/search`

Search knowledge base.

**Request:**
```json
{
  "text": "transformer architecture improvements",
  "tags": ["nlp"],
  "content_types": ["paper", "article"],
  "limit": 10,
  "offset": 0,
  "search_mode": "hybrid"
}
```

**Response `200 OK`:**
```json
{
  "data": [
    {
      "item": { ... },
      "score": 0.92,
      "match_type": "semantic"
    }
  ],
  "meta": {
    "total": 15,
    "request_id": "req_abc123"
  }
}
```

---

### `GET /kb/tags`

Get all tags with counts.

**Response `200 OK`:**
```json
{
  "data": [
    {"tag": "transformers", "count": 12, "is_auto_generated": false},
    {"tag": "nlp", "count": 8, "is_auto_generated": false},
    {"tag": "paper", "count": 5, "is_auto_generated": true}
  ]
}
```

---

## 6. Content API

### `GET /content/briefs/today`

Get today's content brief.

**Response `200 OK`:**
```json
{
  "data": {
    "id": "uuid",
    "brief_date": "2026-06-26",
    "ideas": [
      {
        "id": "uuid",
        "title": "Why KV-Cache Optimization Matters More Than New Architectures",
        "description": "Deep dive into how KV-cache techniques like...",
        "category": "opinion",
        "relevance_score": 0.92,
        "novelty_score": 0.85,
        "source_type": "github",
        "source_detail": "Recent PR #42 in transformer-inference repo"
      }
    ],
    "context_summary": "This week you've been working on inference optimization...",
    "signal_quality": {
      "has_github": true,
      "has_kb": true,
      "has_trends": true,
      "idea_count": 5,
      "quality_label": "excellent",
      "message": "Great signal this week!"
    },
    "generated_at": "2026-06-26T12:00:00Z",
    "viewed_at": null
  }
}
```

**Response `204 No Content`** if brief hasn't been generated yet for today (should not happen if cron is running).

---

### `POST /content/ideas/generate`

Generate new ideas on demand.

**Request:**
```json
{
  "count": 5
}
```

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Title",
      "description": "Description",
      "category": "opinion",
      "relevance_score": 0.88,
      "novelty_score": 0.75,
      "source_type": "mixed",
      "source_detail": null,
      "suggested_tone": "educational",
      "suggested_length": "medium"
    }
  ]
}
```

---

### `POST /content/drafts`

Generate a draft from an idea.

**Request:**
```json
{
  "idea_id": "uuid",
  "tone": "conversational",
  "length": "medium",
  "include_code": false
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "draft_id": "uuid",
    "title": "Why KV-Cache Optimization Matters More Than New Architectures",
    "body": "Over the past week, I've been deep in the trenches of inference optimization...",
    "word_count": 423,
    "reading_time_seconds": 127,
    "status": "draft",
    "tone": "conversational",
    "length": "medium",
    "content_type": "opinion",
    "quality_scores": {
      "overall": 0.87,
      "factual_accuracy": 0.95,
      "readability": 0.82,
      "authenticity": 0.79,
      "technical_depth": 0.91
    },
    "created_at": "2026-06-26T12:00:00Z"
  }
}
```

**Expected latency:** `POST /content/drafts` may take up to 15 seconds. The client should show a loading state.

---

### `GET /content/drafts`

List drafts.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `page_size` | integer | Items per page |
| `status` | string | `draft`, `approved`, `scheduled`, `published`, `archived` |
| `content_type` | string | Filter by content category |
| `sort` | string | `created_desc` (default), `updated_desc`, `title_asc` |

**Response `200 OK`:** Paginated list of draft summaries.

---

### `GET /content/drafts/{id}`

Get full draft with body content.

**Response `200 OK`:**
```json
{
  "data": {
    "id": "uuid",
    "title": "...",
    "body": "Full draft content...",
    "status": "draft",
    "tone": "conversational",
    "length": "medium",
    "content_type": "opinion",
    "generation_metadata": {
      "source_idea_id": "uuid",
      "llm_model": "claude-sonnet-4-20250514",
      "tokens_used": 1250,
      "generation_duration_ms": 8430,
      "pipeline_stages": [
        {"stage": "context_aggregator", "duration_ms": 1200},
        {"stage": "idea_generator", "duration_ms": 800},
        {"stage": "draft_composer", "duration_ms": 5400},
        {"stage": "style_refiner", "duration_ms": 430},
        {"stage": "quality_gate", "duration_ms": 600}
      ]
    },
    "quality_scores": { ... },
    "created_at": "...",
    "updated_at": "..."
  }
}
```

---

### `PUT /content/drafts/{id}`

Update draft body.

**Request:**
```json
{
  "body": "Revised draft content..."
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "id": "uuid",
    "body": "Revised draft content...",
    "status": "draft",
    "revision": 2,
    "updated_at": "..."
  }
}
```

**Note:** Every update creates a new revision. The server stores the diff for style learning.

---

### `POST /content/drafts/{id}/regenerate`

Regenerate draft with optional feedback.

**Request:**
```json
{
  "feedback": "Make this more technical and include code examples",
  "tone": "technical",
  "length": "long"
}
```

All fields optional. If `feedback` is provided, the regeneration considers the user's critique.

**Response `200 OK`:** Full draft object.

---

### `POST /content/drafts/{id}/rate`

Rate a draft.

**Request:**
```json
{
  "score": 4,
  "comment": "Good but could use more technical depth",
  "dimension_scores": {
    "authenticity": 4,
    "technical_depth": 3,
    "readability": 5,
    "relevance": 4,
    "tone": 4
  }
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "rating_id": "uuid",
    "recorded": true,
    "style_profile_updated": true
  }
}
```

---

### `POST /content/drafts/{id}/schedule`

Schedule a draft for publishing.

**Request:**
```json
{
  "platform": "linkedin",
  "scheduled_for": "2026-06-27T09:00:00Z",
  "format_params": {
    "add_hashtags": true,
    "add_call_to_action": true,
    "max_hashtags": 3,
    "include_link": false
  }
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "schedule_id": "uuid",
    "draft_id": "uuid",
    "platform": "linkedin",
    "scheduled_for": "2026-06-27T09:00:00Z",
    "status": "pending",
    "created_at": "2026-06-26T12:00:00Z"
  }
}
```

---

### `GET /content/drafts/{id}/revisions`

Get draft revision history.

**Query Parameters:** `limit`, `offset`

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "uuid",
      "draft_id": "uuid",
      "body": "Revision text...",
      "diff": "@@ -1,5 +1,7 @@...",
      "change_source": "user_edit",
      "created_at": "2026-06-26T12:05:00Z"
    }
  ]
}
```

---

### `GET /content/history`

Get all content activity (drafts created, approved, published).

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | ISO datetime | Start of time range |
| `until` | ISO datetime | End of time range |
| `page` | integer | Page number |
| `page_size` | integer | Items per page |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "draft_id": "uuid",
      "title": "...",
      "event": "published",
      "platform": "linkedin",
      "timestamp": "..."
    }
  ]
}
```

---

## 7. Publishing API

### `POST /publish/now`

Publish a draft immediately.

**Request:**
```json
{
  "draft_id": "uuid",
  "platform": "linkedin",
  "format_params": {
    "add_hashtags": true,
    "max_hashtags": 3
  }
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "success": true,
    "platform": "linkedin",
    "external_post_id": "urn:li:share:abc123",
    "post_url": "https://linkedin.com/feed/update/abc123",
    "published_at": "2026-06-26T12:00:00Z",
    "attempt_count": 1,
    "error_message": null
  }
}
```

**Errors:** `502 PUBLISH_FAILED` (platform error), `400 PLATFORM_DISCONNECTED`

---

### `POST /publish/schedule`

Schedule a post (alternative to `POST /content/drafts/{id}/schedule` from publishing API).

**Request:**
```json
{
  "draft_id": "uuid",
  "platform": "linkedin",
  "scheduled_for": "2026-06-27T09:00:00Z"
}
```

**Response `201 Created`:** Schedule object.

---

### `GET /publish/schedule`

List scheduled posts.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | `pending`, `published`, `failed`, `cancelled` |
| `platform` | string | `linkedin`, `twitter` |
| `from` | ISO datetime | Start date range |
| `to` | ISO datetime | End date range |
| `page`, `page_size` | | Pagination |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "uuid",
      "draft_id": "uuid",
      "draft_title": "...",
      "platform": "linkedin",
      "scheduled_for": "2026-06-27T09:00:00Z",
      "status": "pending",
      "created_at": "2026-06-26T12:00:00Z"
    }
  ]
}
```

---

### `DELETE /publish/schedule/{id}`

Cancel a scheduled post.

**Response `204 No Content`**

---

### `GET /publish/history`

Get publishing history.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page`, `page_size` | | Pagination |
| `status` | string | `published`, `failed` |
| `platform` | string | `linkedin`, `twitter` |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "uuid",
      "draft_id": "uuid",
      "draft_title": "...",
      "platform": "linkedin",
      "status": "published",
      "external_post_id": "urn:li:share:abc123",
      "post_url": "https://linkedin.com/feed/update/abc123",
      "published_at": "2026-06-26T12:00:00Z",
      "attempt_count": 1,
      "error_message": null
    }
  ]
}
```

---

## 8. Analytics API

### `GET /analytics/overview`

Get analytics overview.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | ISO date | 30 days ago | Start of period |
| `end_date` | ISO date | today | End of period |

**Response `200 OK`:**
```json
{
  "data": {
    "total_posts": 24,
    "total_impressions": 45200,
    "total_engagement": 1850,
    "avg_engagement_rate": 4.09,
    "follower_count": 1250,
    "follower_growth": 89,
    "top_post": {
      "post_id": "uuid",
      "title": "...",
      "impressions": 5200,
      "engagement_rate": 6.2
    },
    "period_comparison": {
      "posts_change_percent": 33.3,
      "impressions_change_percent": 45.0,
      "engagement_change_percent": 28.5,
      "followers_change_percent": 7.7,
      "engagement_rate_change": -0.5
    }
  }
}
```

---

### `GET /analytics/posts`

Get individual post performance.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | ISO date | Start of period |
| `end_date` | ISO date | End of period |
| `page`, `page_size` | | Pagination |
| `sort` | string | `date_desc` (default), `date_asc`, `engagement_desc`, `impressions_desc` |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "post_id": "uuid",
      "external_post_id": "urn:li:share:abc123",
      "title": "Post Title",
      "platform": "linkedin",
      "published_at": "2026-06-25T09:00:00Z",
      "impressions": 5200,
      "engagement_count": 322,
      "engagement_rate": 6.2,
      "likes": 245,
      "comments": 42,
      "shares": 35,
      "content_category": "opinion",
      "is_top_performer": true
    }
  ]
}
```

---

### `GET /analytics/engagement`

Get engagement trends.

**Query Parameters:** `start_date`, `end_date`

**Response `200 OK`:**
```json
{
  "data": {
    "daily_avg_engagement": [
      {"date": "2026-06-25T00:00:00Z", "value": 42.5},
      {"date": "2026-06-26T00:00:00Z", "value": 38.2}
    ],
    "weekly_avg_engagement": [
      {"date": "2026-06-22T00:00:00Z", "value": 280.0}
    ],
    "best_day": "Tuesday",
    "best_time": "09:00",
    "trend_direction": "increasing"
  }
}
```

---

### `GET /analytics/audience`

Get audience growth data.

**Query Parameters:** `start_date`, `end_date`

**Response `200 OK`:**
```json
{
  "data": {
    "current_followers": 1250,
    "growth_by_period": [
      {"date": "2026-05-26T00:00:00Z", "value": 1161},
      {"date": "2026-06-26T00:00:00Z", "value": 1250}
    ],
    "growth_rate": 7.7,
    "top_follower_sources": ["linkedin_search", "post_recommendations", "external_referral"]
  }
}
```

---

### `GET /analytics/trends`

Get content performance trends by category.

**Response `200 OK`:**
```json
{
  "data": [
    {
      "content_category": "opinion",
      "avg_engagement_rate": 5.2,
      "total_posts": 8,
      "recommendation": "Continue posting opinion pieces — they consistently outperform your average"
    },
    {
      "content_category": "tutorial",
      "avg_engagement_rate": 3.1,
      "total_posts": 6,
      "recommendation": "Try adding more practical code examples to improve engagement"
    }
  ]
}
```

---

## 9. Admin API

### `GET /admin/stats`

System statistics (admin-only).

**Response `200 OK`:**
```json
{
  "data": {
    "total_users": 142,
    "active_users_last_7d": 87,
    "total_drafts_generated": 3421,
    "total_posts_published": 1250,
    "total_kb_items": 8900,
    "llm_cost_today": 12.45,
    "llm_cost_this_month": 345.20
  }
}
```

---

### `GET /admin/users`

List users (admin-only).

**Query Parameters:** `page`, `page_size`, `status` (`active`, `inactive`)

**Response `200 OK`:** Paginated list of user summaries.

---

### `GET /admin/user/{id}`

Get user details (admin-only).

**Response `200 OK`:**
```json
{
  "data": {
    "user_id": "uuid",
    "email": "alex@example.com",
    "display_name": "Alex Chen",
    "created_at": "...",
    "last_active_at": "...",
    "total_drafts": 45,
    "total_published": 30,
    "llm_cost_total": 4.50,
    "style_profile_confidence": 0.85,
    "connections": ["github", "linkedin"],
    "account_status": "active"
  }
}
```

---

### `POST /admin/force-sync/{user_id}`

Force trigger a GitHub sync for a user (admin-only).

**Response `202 Accepted`:**
```json
{
  "data": {
    "sync_id": "uuid",
    "status": "queued"
  }
}
```

---

## 10. Webhooks

### 10.1 Outgoing Webhooks (BrandOS → External)

No outgoing webhooks in MVP. Webhook delivery for "post published" events is planned for Phase 2.

### 10.2 Incoming Webhooks (External → BrandOS)

#### GitHub Push Webhook

```
POST /webhooks/github
```

When a user configures a GitHub webhook, push events trigger a delta analysis.

**Request Body (GitHub standard push event):**
```json
{
  "ref": "refs/heads/main",
  "commits": [
    {
      "id": "abc123",
      "message": "Optimize KV-cache implementation",
      "timestamp": "2026-06-26T11:00:00Z",
      "author": {"username": "alexchen"},
      "added": ["inference/kv_cache.py"],
      "modified": ["inference/model.py"]
    }
  ],
  "repository": {
    "full_name": "alexchen/transformer-inference",
    "html_url": "https://github.com/alexchen/transformer-inference"
  }
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "processed": true,
    "commits_added": 1,
    "brief_updated": true
  }
}
```

#### LinkedIn Post Engagement Webhook

```
POST /webhooks/linkedin/engagement
```

LinkedIn engagement events (when LinkedIn API supports webhooks).

**Response `200 OK`:**
```json
{
  "data": {
    "processed": true,
    "engagement_updated": true
  }
}
```

---

## 11. Appendix: Error Codes

### 11.1 HTTP Status Code Usage

| Status Code | Usage |
|-------------|-------|
| `200 OK` | Successful GET, PUT, PATCH |
| `201 Created` | Successful POST (resource created) |
| `202 Accepted` | Async operation accepted (queued) |
| `204 No Content` | Successful DELETE |
| `400 Bad Request` | Validation error, malformed request |
| `401 Unauthorized` | Missing or invalid authentication |
| `403 Forbidden` | Authenticated but not authorized |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Duplicate resource, idempotency mismatch |
| `422 Unprocessable Entity` | Request body validation failed |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server error |
| `502 Bad Gateway` | External service error (LLM, GitHub, LinkedIn) |
| `503 Service Unavailable` | Service temporarily unavailable |
| `504 Gateway Timeout` | External service timeout |

### 11.2 Error Code Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_ERROR` | 401 | Generic auth failure |
| `TOKEN_EXPIRED` | 401 | Access token has expired |
| `TOKEN_REVOKED` | 401 | Session has been revoked |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `CONTENT_GENERATION_ERROR` | 500 | Content engine failure |
| `IDEA_GENERATION_FAILED` | 500 | Idea generation failed |
| `DRAFT_COMPOSITION_FAILED` | 500 | Draft composition failed |
| `QUALITY_GATE_FAILED` | 500 | Draft failed quality check |
| `LLM_TIMEOUT` | 504 | LLM provider timed out |
| `LLM_RATE_LIMITED` | 429 | LLM rate limit exceeded |
| `PUBLISH_FAILED` | 502 | Platform publish failed |
| `PLATFORM_DISCONNECTED` | 400 | Platform not connected |
| `PLATFORM_ERROR` | 502 | Platform API error |
| `GITHUB_API_ERROR` | 502 | GitHub API error |
| `LINKEDIN_API_ERROR` | 502 | LinkedIn API error |
| `OAUTH_ERROR` | 502 | OAuth provider error |
| `INSUFFICIENT_STYLE_SIGNALS` | 400 | Not enough style data |
| `EXTERNAL_SERVICE_ERROR` | 502 | Generic external service error |

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-06-26 | Architecture Team | Initial draft |

---

*This document defines every API endpoint in the BrandOS system. All endpoints follow the common patterns defined in Section 1. These contracts are the interface between frontend and backend — both teams must agree before implementation.*
