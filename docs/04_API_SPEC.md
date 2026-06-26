# BrandOS — API Specification v1

> **Version:** 1.0.0
> **Base URL:** `https://api.brandos.app/api/v1`
> **Protocol:** HTTPS only
> **Specification:** OpenAPI 3.1.0 (embedded YAML per section)
> **Last Updated:** 2026-06-26

---

## Table of Contents

1. [Common Patterns](#1-common-patterns)
2. [Authentication](#2-authentication)
3. [Profile](#3-profile)
4. [Connections](#4-connections)
5. [Knowledge Base](#5-knowledge-base)
6. [Style Analysis](#6-style-analysis)
7. [Content Engine](#7-content-engine)
8. [Platform Publishing](#8-platform-publishing)
9. [Trends](#9-trends)
10. [Analytics](#10-analytics)
11. [Briefs](#11-briefs)
12. [Notifications](#12-notifications)
13. [Admin](#13-admin)
14. [Health](#14-health)
15. [Webhooks](#15-webhooks)
16. [OpenAPI Specification](#16-openapi-specification)

---

## 1. Common Patterns

### 1.1 Authentication

All authenticated endpoints require a Bearer JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are short-lived (15 minutes). A rotating refresh token (7-day expiry) is issued alongside the access token. Refresh tokens can be exchanged once for a new pair; the old refresh token is immediately invalidated (rotation prevents replay).

| Token Type   | Lifetime | Storage              | Rotation |
|-------------|----------|----------------------|----------|
| Access       | 15 min   | Memory / short-lived  | No       |
| Refresh      | 7 days   | Secure HttpOnly store | Yes      |

**Scopes** (enforced via JWT `scp` claim):

| Scope              | Description                                  |
|--------------------|----------------------------------------------|
| `profile:read`     | Read own profile and preferences             |
| `profile:write`    | Update own profile and preferences           |
| `kb:read`          | Read knowledge base items, tags, search      |
| `kb:write`         | Create, update, delete knowledge base items  |
| `content:read`     | Read briefs, ideas, drafts, history          |
| `content:write`    | Create, update, publish content              |
| `style:read`       | Read style profile and analysis results      |
| `style:write`      | Update style profile, rate suggestions       |
| `analytics:read`   | Read analytics and content scores            |
| `notifications:read` | Read notification history                |
| `notifications:write` | Mark notifications read                 |
| `connections:read` | Read connected platform accounts             |
| `connections:write` | Connect/disconnect platform accounts       |
| `admin`            | System administration (internal only)        |

Every non-authenticated response MUST carry a `WWW-Authenticate` header describing the auth scheme.

### 1.2 Response Envelope

**Success responses** return the resource directly under a `data` key:

```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_G7a9kL2mQ4"
  }
}
```

**Collection responses** wrap items and include pagination:

```json
{
  "data": [ ... ],
  "meta": {
    "total": 142,
    "cursor": "eyJpZCI6MTQyfQ",
    "has_more": true,
    "request_id": "req_G7a9kL2mQ4"
  }
}
```

**Error responses** use a consistent envelope:

```json
{
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "Access token has expired. Use the refresh token to obtain a new pair.",
    "details": {
      "expired_at": "2026-06-26T14:30:00Z"
    },
    "trace_id": "trace_abc123"
  }
}
```

### 1.3 Error Codes

Codes follow the pattern `DOMAIN_REASON`.

| Code                              | HTTP Status | Description                              |
|-----------------------------------|-------------|------------------------------------------|
| `AUTH_INVALID_CREDENTIALS`        | 401         | Email or password incorrect              |
| `AUTH_TOKEN_EXPIRED`              | 401         | Access token expired                     |
| `AUTH_TOKEN_REVOKED`              | 401         | Token has been revoked                   |
| `AUTH_INVALID_SCOPE`              | 403         | Token lacks required scope               |
| `AUTH_RATE_LIMITED`               | 429         | Too many auth attempts                   |
| `AUTH_REFRESH_ROTATED`            | 401         | Refresh token already used               |
| `PROFILE_NOT_FOUND`               | 404         | Profile does not exist                   |
| `PROFILE_VALIDATION`              | 422         | Profile field validation failed          |
| `CONNECTION_NOT_FOUND`            | 404         | Platform connection not found            |
| `CONNECTION_EXPIRED`              | 401         | OAuth token expired                      |
| `CONNECTION_DUPLICATE`            | 409         | Platform already connected               |
| `GITHUB_SYNC_IN_PROGRESS`         | 409         | Sync already running                     |
| `GITHUB_REPO_NOT_FOUND`           | 404         | Repository not found                     |
| `GITHUB_SYNC_FAILED`              | 500         | GitHub sync encountered error            |
| `KB_ITEM_NOT_FOUND`               | 404         | Knowledge base item not found            |
| `KB_TAG_NOT_FOUND`                | 404         | Tag does not exist                       |
| `KB_TAG_CYCLE`                    | 422         | Tag merge would create circular ref      |
| `KB_EMBEDDING_FAILED`             | 500         | Embedding generation failed              |
| `CONTENT_NOT_FOUND`               | 404         | Content item not found                   |
| `CONTENT_DRAFT_LOCKED`            | 409         | Draft locked by another session          |
| `CONTENT_VERSION_CONFLICT`        | 409         | Optimistic lock version mismatch         |
| `CONTENT_VALIDATION`              | 422         | Content field validation failed          |
| `CONTENT_RATING_INVALID`          | 422         | Rating out of range or invalid           |
| `CONTENT_SCHEDULE_PAST`           | 422         | Scheduled time is in the past            |
| `PLATFORM_POST_FAILED`            | 502         | Platform API rejected the post           |
| `PLATFORM_RATE_LIMITED`           | 429         | Platform API rate limit exceeded         |
| `PLATFORM_ACCOUNT_DISCONNECTED`   | 400         | Platform account not connected           |
| `STYLE_PROFILE_NOT_FOUND`         | 404         | Style profile not found                  |
| `STYLE_ANALYSIS_IN_PROGRESS`      | 409         | Style analysis already running           |
| `TREND_SOURCE_INVALID`            | 422         | Trend source not recognized              |
| `BRIEF_NOT_FOUND`                 | 404         | Brief does not exist                     |
| `BRIEF_ALREADY_ACKNOWLEDGED`      | 409         | Brief already acknowledged               |
| `BRIEF_GENERATION_FAILED`         | 500         | Brief generation failed                  |
| `NOTIFICATION_NOT_FOUND`          | 404         | Notification not found                   |
| `ANALYTICS_NO_DATA`               | 404         | No analytics data for given period       |
| `ADMIN_ONLY`                      | 403         | Endpoint requires admin scope            |
| `RATE_LIMITED`                    | 429         | General rate limit exceeded              |
| `VALIDATION_ERROR`                | 422         | Request body validation failed           |
| `INTERNAL_ERROR`                  | 500         | Unexpected server error                  |

### 1.4 Pagination

Two pagination strategies:

**Cursor-based** (real-time feeds, notifications, content lists):

| Parameter | Type   | Required | Description                                 |
|-----------|--------|----------|---------------------------------------------|
| `cursor`  | string | No       | Opaque base64 cursor from previous response |
| `limit`   | int    | No       | Page size 1–100, default 25                 |

Response includes `cursor` (next page token) and `has_more`.

**Offset-based** (admin tables, analytics export):

| Parameter | Type   | Required | Description                       |
|-----------|--------|----------|-----------------------------------|
| `page`    | int    | No       | Page number 1-based, default 1    |
| `per_page`| int    | No       | Items per page 1–100, default 25  |

Response includes `total`, `page`, `per_page`, `total_pages`.

### 1.5 Rate Limiting

| Header                     | Description                              |
|----------------------------|------------------------------------------|
| `X-RateLimit-Limit`        | Requests allowed per window              |
| `X-RateLimit-Remaining`    | Requests remaining in current window     |
| `X-RateLimit-Reset`        | Unix timestamp when the window resets    |

- Auth endpoints: 20 req/min burst, 200 req/hr sustained
- All other endpoints: 60 req/min burst, 1000 req/hr sustained
- Admin endpoints: 120 req/min, 5000 req/hr
- Webhook receivers: 200 req/min per IP

### 1.6 HATEOAS Links

Responses include `_links` for discoverability:

```json
{
  "data": {
    "id": "item_abc123",
    "title": "My First Brief",
    "_links": {
      "self": { "href": "/api/v1/briefs/item_abc123" },
      "ideas": { "href": "/api/v1/briefs/item_abc123/ideas" },
      "acknowledge": { "href": "/api/v1/briefs/item_abc123/acknowledge", "method": "POST" }
    }
  }
}
```

### 1.7 Common Headers

| Header             | Where      | Description                             |
|--------------------|------------|-----------------------------------------|
| `_idempotency-Key`  | POST/PATCH | _idempotency key (UUID v4)               |
| `X-Request-_id`     | Request    | Client-generated request ID for tracing |
| `If-None-Match`    | GET        | ETag for conditional requests           |
| `If-Match`         | PATCH/DELETE | ETag for optimistic concurrency       |

### 1.8 Field Selection

Use `fields` query parameter: `GET /api/v1/kb/items?fields=id,title,content_type`. Nested fields use dot notation.

### 1.9 _idempotency

POST/PATCH requests support `_idempotency-Key` (UUID v4). Server caches response for 24 hours. Repeat requests with same key return cached response.

### 1.10 Concurrency

Resources carry an `etag` or `version` integer. Read returns `ETag` header. Write with `If-Match` header; server rejects with 412 on conflict.

---

## 2. Authentication

### 2.1 Register

```http
POST /api/v1/auth/register
Content-Type: application/json
```

**Request:**

```json
{
  "email": "user@example.com",
  "password": "SecureP@ss1",
  "name": "Alex Johnson",
  "timezone": "America/New_York"
}
```

| Field      | Type   | Required | Constraints                       |
|-----------|--------|----------|-----------------------------------|
| `email`    | string | Yes      | Valid email, max 255, unique      |
| `password` | string | Yes      | 8–128 chars, upper+lower+digit    |
| `name`     | string | Yes      | 1–100 chars                       |
| `timezone` | string | No       | IANA timezone, default UTC        |

**Response:** `201 Created`

```json
{
  "data": {
    "user": {
      "id": "usr_G7a9kL2mQ4",
      "email": "user@example.com",
      "name": "Alex Johnson",
      "created_at": "2026-06-26T10:00:00Z"
    },
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIs...",
    "expires_in": 900,
    "scope": "profile:read profile:write kb:read ..."
  }
}
```

**Errors:** `409` (email exists), `422` (validation)

### 2.2 Login

```http
POST /api/v1/auth/login
Content-Type: application/json
```

**Request:**
```json
{ "email": "user@example.com", "password": "SecureP@ss1" }
```

**Response:** `200 OK` (same shape as Register)

**Errors:** `401` (`AUTH_INVALID_CREDENTIALS`), `429` (after 5 failed attempts)

### 2.3 OAuth Login

```http
POST /api/v1/auth/oauth
```

**Request:**
```json
{ "provider": "google", "code": "4/0AX4XfWiM..." }
```

| Field      | Type   | Required | Description                      |
|-----------|--------|----------|----------------------------------|
| `provider` | string | Yes      | `google`, `github`, `apple`      |
| `code`     | string | Yes      | Authorization code from OAuth    |

**Response:** `200 OK` (same token response)

### 2.4 Refresh Token

```http
POST /api/v1/auth/refresh
```

**Request:**
```json
{ "refresh_token": "eyJhbGciOiJSUzI1NiIs..." }
```

**Response:** `200 OK`
```json
{
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 900
  }
}
```

**Errors:** `401` (`AUTH_REFRESH_ROTATED`), `401` (expired)

### 2.5 Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

### 2.6 Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "data": {
    "id": "usr_G7a9kL2mQ4",
    "email": "user@example.com",
    "name": "Alex Johnson",
    "timezone": "America/New_York",
    "avatar_url": null,
    "created_at": "2026-06-26T10:00:00Z",
    "onboarding_completed": false,
    "scopes": ["profile:read", "kb:read", ...]
  }
}
```

### 2.7 Change Password

```http
POST /api/v1/auth/change-password
```

**Request:**
```json
{ "current_password": "SecureP@ss1", "new_password": "NewSecureP@ss2" }
```

**Response:** `204 No Content`

**Errors:** `401` (current password wrong), `422` (validation)

### 2.8 OAuth Scopes (OpenAPI 3.1)

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    AuthRegisterRequest:
      type: object
      required: [email, password, name]
      properties:
        email: { type: string, format: email, maxLength: 255 }
        password: { type: string, minLength: 8, maxLength: 128 }
        name: { type: string, minLength: 1, maxLength: 100 }
        timezone: { type: string }
    AuthLoginRequest:
      type: object
      required: [email, password]
      properties:
        email: { type: string, format: email }
        password: { type: string }
    AuthTokenResponse:
      type: object
      properties:
        user: { $ref: '#/components/schemas/UserPublic' }
        access_token: { type: string }
        refresh_token: { type: string }
        expires_in: { type: integer }
        scope: { type: string }
    UserPublic:
      type: object
      properties:
        id: { type: string, pattern: '^usr_[A-Za-z0-9]{12}$' }
        email: { type: string, format: email }
        name: { type: string }
        timezone: { type: string }
        avatar_url: { type: string, nullable: true }
        created_at: { type: string, format: date-time }
```
---

## 3. Profile

### 3.1 Get Profile

```http
GET /api/v1/profile
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "data": {
    "id": "usr_G7a9kL2mQ4",
    "name": "Alex Johnson",
    "bio": "Startup CTO writing about AI and developer tools.",
    "avatar_url": null,
    "timezone": "America/New_York",
    "industry": "Technology",
    "title": "CTO",
    "company": "BrandOS Inc.",
    "location": "New York, NY",
    "website": "https://alexjohnson.dev",
    "preferences": {
      "content_language": "en",
      "default_platform": "linkedin",
      "posting_frequency": "daily",
      "auto_schedule": true,
      "preferred_posting_time": "09:00",
      "notifications_enabled": true
    },
    "expertise_areas": [
      { "id": "exp_abc123", "name": "Software Architecture", "category": "technology", "proficiency": 0.85 },
      { "id": "exp_def456", "name": "AI/ML", "category": "technology", "proficiency": 0.72 }
    ],
    "stats": {
      "total_posts": 42,
      "total_ideas": 128,
      "total_kb_items": 356,
      "connected_platforms": ["github", "linkedin"]
    },
    "_links": { "self": { "href": "/api/v1/profile" } }
  }
}
```

### 3.2 Update Profile

```http
PATCH /api/v1/profile
Content-Type: application/json
```

All fields optional:
```json
{ "name": "Alex J. Johnson", "bio": "Updated bio.", "industry": "AI/ML", "title": "CEO" }
```

**Response:** `200 OK` **Errors:** `412`, `422`

### 3.3 Update Preferences

```http
PATCH /api/v1/profile/preferences
```
```json
{ "posting_frequency": "weekly", "auto_schedule": false }
```
**Response:** `200 OK`

### 3.4 Add Expertise Area

```http
POST /api/v1/profile/expertise
```
```json
{ "name": "DevOps", "category": "technology", "proficiency": 0.65 }
```
**Response:** `201 Created`

### 3.5 Remove Expertise Area

```http
DELETE /api/v1/profile/expertise/{expertise_id}
```
**Response:** `204 No Content`

### 3.6 Onboarding Complete

```http
POST /api/v1/profile/onboarding/complete
```
**Response:** `200 OK`

### 3.7 Schemas

```yaml
components:
  schemas:
    Profile:
      type: object
      properties:
        id: { $ref: '#/components/schemas/User_id' }
        name: { type: string }
        bio: { type: string, nullable: true }
        avatar_url: { type: string, nullable: true }
        timezone: { type: string }
        industry: { type: string, nullable: true }
        title: { type: string, nullable: true }
        company: { type: string, nullable: true }
        location: { type: string, nullable: true }
        website: { type: string, nullable: true }
        preferences: { $ref: '#/components/schemas/UserPreferences' }
        expertise_areas:
          type: array
          items: { $ref: '#/components/schemas/ExpertiseArea' }
    UserPreferences:
      type: object
      properties:
        content_language: { type: string, default: en }
        default_platform: { type: string, enum: [linkedin, twitter, blog] }
        posting_frequency: { type: string, enum: [daily, weekly, monthly] }
        auto_schedule: { type: boolean }
        preferred_posting_time: { type: string, pattern: '^\d{2}:\d{2}$' }
        notifications_enabled: { type: boolean }
    ExpertiseArea:
      type: object
      properties:
        id: { type: string, pattern: '^exp_[A-Za-z0-9]{12}$' }
        name: { type: string }
        category: { type: string }
        proficiency: { type: number, minimum: 0, maximum: 1 }
    User_id:
      type: string
      pattern: '^usr_[A-Za-z0-9]{12}$'
```

---

## 4. Connections

### 4.1 List Connections

```http
GET /api/v1/connections
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "conn_abc123",
      "platform": "github",
      "platform_username": "alexj",
      "connected_at": "2026-06-01T10:00:00Z",
      "status": "active",
      "scopes": ["repo", "user"],
      "metadata": { "avatar_url": "...", "name": "Alex Johnson" }
    },
    {
      "id": "conn_def456",
      "platform": "linkedin",
      "platform_username": "alexjohnson",
      "connected_at": "2026-06-05T14:00:00Z",
      "status": "active",
      "scopes": ["w_member_social", "r_liteprofile"],
      "metadata": { "avatar_url": "...", "headline": "CTO at BrandOS" }
    }
  ]
}
```

### 4.2 Get Connection

```http
GET /api/v1/connections/{connection_id}
```
**Response:** `200 OK` **Errors:** `404`

### 4.3 Initiate OAuth Connection

```http
POST /api/v1/connections/oauth-url
```
```json
{ "platform": "github", "redirect_uri": "https://brandos.app/oauth/callback" }
```
**Response:** `200 OK`
```json
{ "data": { "oauth_url": "https://github.com/login/oauth/authorize?client_id=...", "state": "state_abc123" } }
```

### 4.4 Complete OAuth Connection

```http
POST /api/v1/connections/callback
```
```json
{ "platform": "github", "code": "abc123def456", "state": "state_abc123" }
```
**Response:** `201 Created` **Errors:** `409` (duplicate)

### 4.5 Disconnect Platform

```http
DELETE /api/v1/connections/{connection_id}
```
**Response:** `204 No Content`

### 4.6 Refresh Platform Token

```http
POST /api/v1/connections/{connection_id}/refresh
```
**Response:** `200 OK`

### 4.7 List GitHub Repositories

```http
GET /api/v1/connections/github/repos
```
**Query:** `?page=1&per_page=30`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 12345,
      "name": "brandos",
      "full_name": "alexj/brandos",
      "description": "AI-powered personal brand OS",
      "url": "https://github.com/alexj/brandos",
      "language": "Python",
      "stars": 42,
      "fork": false,
      "private": false,
      "selected": true
    }
  ],
  "meta": { "total": 15, "page": 1, "per_page": 30, "total_pages": 1 }
}
```

### 4.8 Select Repositories for Sync

```http
PUT /api/v1/connections/github/selected-repos
```
```json
{ "repo_ids": [12345, 67890] }
```
**Response:** `200 OK`

### 4.9 Trigger Repository Sync

```http
POST /api/v1/connections/github/sync
```
**Query:** `?repo_id=12345` (optional)

**Response:** `202 Accepted`
```json
{
  "data": {
    "sync_id": "sync_abc123",
    "status": "in_progress",
    "repos_queued": 3,
    "started_at": "2026-06-26T14:00:00Z",
    "_links": { "status": { "href": "/api/v1/connections/github/sync/sync_abc123" } }
  }
}
```
**Errors:** `409` (sync in progress)

### 4.10 Get Sync Status

```http
GET /api/v1/connections/github/sync/{sync_id}
```
**Response:** `200 OK`
```json
{
  "data": {
    "sync_id": "sync_abc123",
    "status": "completed",
    "total_repos": 3,
    "completed_repos": 3,
    "items_discovered": 156,
    "items_imported": 134,
    "items_updated": 22,
    "errors": [],
    "started_at": "2026-06-26T14:00:00Z",
    "completed_at": "2026-06-26T14:02:30Z"
  }
}
```

### 4.11 Schemas

```yaml
components:
  schemas:
    Connection:
      type: object
      properties:
        id: { type: string, pattern: '^conn_[A-Za-z0-9]{12}$' }
        platform: { type: string, enum: [github, linkedin, twitter] }
        platform_username: { type: string }
        connected_at: { type: string, format: date-time }
        status: { type: string, enum: [active, expired, revoked] }
        token_expires_at: { type: string, format: date-time, nullable: true }
        scopes:
          type: array
          items: { type: string }
        metadata: { type: object }
    GitHubRepo:
      type: object
      properties:
        id: { type: integer }
        name: { type: string }
        full_name: { type: string }
        description: { type: string, nullable: true }
        url: { type: string, format: uri }
        language: { type: string, nullable: true }
        stars: { type: integer }
        fork: { type: boolean }
        private: { type: boolean }
        selected: { type: boolean }
    ConnectionOAuthRequest:
      type: object
      required: [platform, redirect_uri]
      properties:
        platform: { type: string, enum: [github, linkedin, twitter] }
        redirect_uri: { type: string, format: uri }
    ConnectionCallbackRequest:
      type: object
      required: [platform, code, state]
      properties:
        platform: { type: string }
        code: { type: string }
        state: { type: string }
    SyncStatus:
      type: object
      properties:
        sync_id: { type: string }
        status: { type: string, enum: [in_progress, completed, failed] }
        total_repos: { type: integer }
        completed_repos: { type: integer }
        items_discovered: { type: integer }
        items_imported: { type: integer }
        items_updated: { type: integer }
        errors: { type: array, items: { type: string } }
        started_at: { type: string, format: date-time }
        completed_at: { type: string, format: date-time, nullable: true }
```

---

## 5. Knowledge Base

### 5.1 List Items

```http
GET /api/v1/kb/items
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `cursor`  | string | No       | Pagination cursor |
| `limit`   | int    | No       | 1–100, default 25 |
| `content_type` | string | No | `documentation`, `code`, `issue`, `discussion`, `note` |
| `status`  | string | No       | `active`, `archived` |
| `tag`     | string | No       | Filter by tag name |
| `source`  | string | No       | `github`, `manual` |
| `q`       | string | No       | Full-text search query |
| `sort`    | string | No       | `created_at`, `updated_at`, `title` |
| `order`   | string | No       | `asc`, `desc` |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "kb_abc123",
      "title": "FastAPI Dependency Injection Patterns",
      "content_type": "documentation",
      "source": "github",
      "source_url": "https://github.com/alexj/brandos/blob/main/docs/di.md",
      "excerpt": "FastAPI uses dependency injection to handle shared state...",
      "language": "markdown",
      "word_count": 1450,
      "tags": [
        { "id": "tag_001", "name": "fastapi", "category": "framework" },
        { "id": "tag_002", "name": "python", "category": "language" }
      ],
      "created_at": "2026-06-10T08:00:00Z",
      "updated_at": "2026-06-20T12:00:00Z",
      "_links": {
        "self": { "href": "/api/v1/kb/items/kb_abc123" },
        "related": { "href": "/api/v1/kb/items/kb_abc123/related" }
      }
    }
  ],
  "meta": { "total": 142, "cursor": "eyJpZCI6MTQyfQ", "has_more": true }
}
```

### 5.2 Get Item

```http
GET /api/v1/kb/items/{item_id}
```
**Response:** `200 OK` (full item with `content` field)
**Errors:** `404`

### 5.3 Create Item

```http
POST /api/v1/kb/items
_idempotency-Key: <uuid>
```
```json
{
  "title": "My New Note",
  "content": "This is a manual knowledge base entry.",
  "content_type": "note",
  "language": "markdown",
  "tags": ["productivity", "notes"]
}
```
| Field         | Type   | Required | Description |
|--------------|--------|----------|-------------|
| `title`       | string | Yes      | 1–500 chars |
| `content`     | string | Yes      | 1–100,000 chars |
| `content_type`| string | Yes      | Enum |
| `language`    | string | No       | Default `markdown` |
| `source`      | string | No       | Default `manual` |
| `tags`        | array  | No       | Array of tag name strings |

**Response:** `201 Created`
**Errors:** `500` (`KB_EMBEDDING_FAILED`)

### 5.4 Update Item

```http
PATCH /api/v1/kb/items/{item_id}
If-Match: "e3b0c44298fc1c149afbf4c8996fb924"
```
```json
{ "title": "Updated title", "tags": ["fastapi", "dependency-injection"] }
```
**Response:** `200 OK` **Errors:** `404`, `412`, `422`

### 5.5 Delete Item

```http
DELETE /api/v1/kb/items/{item_id}
If-Match: "e3b0c44298fc1c149afbf4c8996fb924"
```
**Response:** `204 No Content` **Errors:** `404`, `412`

### 5.6 Hybrid Search

```http
GET /api/v1/kb/search
```
**Query:**
| Parameter   | Type   | Required | Description |
|------------|--------|----------|-------------|
| `q`         | string | Yes      | Search query |
| `limit`     | int    | No       | 1–50, default 10 |
| `content_type` | string | No    | Filter |
| `tags`      | string | No       | Comma-separated tag names |
| `alpha`     | float  | No       | Hybrid weight 0–1, default 0.5 |
| `min_score` | float  | No       | Minimum 0–1, default 0 |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "item": { "id": "kb_abc123", "title": "..." },
      "score": 0.89,
      "match_type": "hybrid",
      "excerpt": "...with **dependency injection** patterns..."
    }
  ],
  "meta": { "total": 12, "query": "dependency injection", "alpha": 0.5 }
}
```

### 5.7 Get Related Items

```http
GET /api/v1/kb/items/{item_id}/related?limit=5
```
**Response:** `200 OK` (array of items with scores)

### 5.8 List Tags

```http
GET /api/v1/kb/tags
```
**Query:** `?q=fast&category=framework`

**Response:** `200 OK`
```json
{
  "data": [
    { "id": "tag_001", "name": "fastapi", "category": "framework", "item_count": 15, "created_at": "..." },
    { "id": "tag_002", "name": "python", "category": "language", "item_count": 42, "created_at": "..." }
  ],
  "meta": { "total": 28 }
}
```

### 5.9 Suggest Tags

```http
POST /api/v1/kb/tags/suggest
```
```json
{ "text": "FastAPI dependency injection with Python type hints." }
```
**Response:** `200 OK`
```json
{
  "data": {
    "suggestions": [
      { "name": "fastapi", "confidence": 0.95, "category": "framework" },
      { "name": "python", "confidence": 0.88, "category": "language" },
      { "name": "dependency-injection", "confidence": 0.76, "category": "pattern" }
    ]
  }
}
```

### 5.10 Merge Tags

```http
POST /api/v1/kb/tags/merge
```
```json
{ "source_tag": "tag_001", "target_tag": "tag_002" }
```
**Response:** `200 OK`
```json
{ "data": { "merged": true, "source_tag": "tag_001", "target_tag": "tag_002", "items_reassigned": 15 } }
```
**Errors:** `404`, `422` (cycle)

### 5.11 Delete Tag

```http
DELETE /api/v1/kb/tags/{tag_id}
```
**Response:** `204 No Content`

### 5.12 Get Embedding Status

```http
GET /api/v1/kb/embedding-status
```
**Response:** `200 OK`
```json
{
  "data": {
    "total_items": 356,
    "embedded_items": 350,
    "pending_items": 6,
    "last_embedding_run": "2026-06-26T13:00:00Z",
    "embedding_model": "text-embedding-3-small"
  }
}
```

### 5.13 Schemas

```yaml
components:
  schemas:
    KBItem:
      type: object
      properties:
        id: { type: string, pattern: '^kb_[A-Za-z0-9]{12}$' }
        title: { type: string, maxLength: 500 }
        content: { type: string }
        content_type:
          type: string
          enum: [documentation, code, issue, discussion, note, snippet]
        source: { type: string, enum: [github, manual] }
        source_url: { type: string, format: uri, nullable: true }
        language: { type: string, default: markdown }
        word_count: { type: integer }
        checksum: { type: string }
        tags:
          type: array
          items: { $ref: '#/components/schemas/Tag' }
        metadata: { type: object }
        created_at: { type: string, format: date-time }
        updated_at: { type: string, format: date-time }
    Tag:
      type: object
      properties:
        id: { type: string, pattern: '^tag_[A-Za-z0-9]{12}$' }
        name: { type: string, maxLength: 100 }
        category: { type: string, maxLength: 50 }
        item_count: { type: integer }
        created_at: { type: string, format: date-time }
    SearchResult:
      type: object
      properties:
        item: { $ref: '#/components/schemas/KBItem' }
        score: { type: number, minimum: 0, maximum: 1 }
        match_type: { type: string, enum: [fulltext, vector, hybrid] }
        excerpt: { type: string }
    CreateKBItemRequest:
      type: object
      required: [title, content, content_type]
      properties:
        title: { type: string, maxLength: 500 }
        content: { type: string }
        content_type: { type: string, enum: [documentation, code, issue, discussion, note, snippet] }
        language: { type: string, default: markdown }
        source: { type: string, default: manual }
        source_url: { type: string, format: uri }
        tags: { type: array, items: { type: string } }
```

---

## 6. Style Analysis

### 6.1 Get Style Profile

```http
GET /api/v1/style/profile
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "data": {
    "id": "stl_abc123",
    "status": "active",
    "overall_tone": { "formal": 0.35, "conversational": 0.65, "analytical": 0.55, "passionate": 0.45, "humorous": 0.25, "authoritative": 0.60 },
    "vocabulary_profile": { "avg_word_length": 4.8, "specialized_ratio": 0.15, "filler_word_ratio": 0.02, "transition_word_ratio": 0.08 },
    "sentence_profile": { "avg_sentence_length": 18.5, "avg_paragraph_length": 3.2, "question_ratio": 0.05, "exclamation_ratio": 0.02 },
    "engagement_signals": { "storytelling_score": 0.72, "hook_effectiveness": 0.68, "call_to_action_frequency": 0.12, "readability_score": 65.0 },
    "content_preferences": { "preferred_topics": ["AI", "software_architecture"], "preferred_content_length": "medium", "preferred_hook_style": "question" },
    "sample_count": 42,
    "last_analyzed": "2026-06-25T18:00:00Z",
    "created_at": "2026-06-01T00:00:00Z",
    "updated_at": "2026-06-25T18:00:00Z",
    "_links": {
      "self": { "href": "/api/v1/style/profile" },
      "progress": { "href": "/api/v1/style/progress" }
    }
  }
}
```
**Errors:** `404` (never analyzed)

### 6.2 Update Style Profile

```http
PATCH /api/v1/style/profile
```
```json
{ "content_preferences": { "preferred_content_length": "long", "preferred_hook_style": "statistic" } }
```
**Response:** `200 OK`

### 6.3 Get Style Progress

```http
GET /api/v1/style/progress
```
**Response:** `200 OK`
```json
{
  "data": {
    "total_samples_analyzed": 42,
    "minimum_required": 10,
    "confidence_level": 0.88,
    "enough_data": true,
    "latest_analysis": "2026-06-25T18:00:00Z"
  }
}
```

### 6.4 Request Style Analysis

```http
POST /api/v1/style/analyze
```
**Response:** `202 Accepted`
```json
{
  "data": {
    "analysis_id": "anl_abc123",
    "status": "in_progress",
    "sample_count": 42,
    "started_at": "2026-06-26T14:00:00Z",
    "_links": {
      "profile": { "href": "/api/v1/style/profile" },
      "progress": { "href": "/api/v1/style/progress" }
    }
  }
}
```
**Errors:** `409` (analysis in progress)

### 6.5 Import Content Samples

```http
POST /api/v1/style/import
```
```json
{
  "samples": [
    { "content": "Full text of the article...", "source": "blog", "title": "My Post", "published_at": "2026-05-15T10:00:00Z" }
  ]
}
```
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `samples` | array | Yes | 1–50 items |
| `content` | string | Yes | 50–50000 chars |
| `source` | string | Yes | `blog`, `linkedin`, `twitter`, `manual` |

**Response:** `201 Created`
```json
{ "data": { "imported": 5, "skipped": 0, "errors": [] } }
```

### 6.6 Get Style Insights

```http
GET /api/v1/style/insights
```
**Response:** `200 OK`
```json
{
  "data": {
    "strengths": [
      { "aspect": "Technical clarity", "score": 0.85, "description": "Clear explanation of complex topics" }
    ],
    "improvements": [
      { "aspect": "Storytelling hooks", "score": 0.45, "description": "Openers could be more engaging", "suggestion": "Try starting with a surprising question" }
    ],
    "signature_patterns": {
      "favorite_transitions": ["however", "moreover", "specifically"],
      "common_openers": ["As a", "When building", "The key insight"],
      "signature_phrases": ["Here's the thing"]
    }
  }
}
```

### 6.7 Schemas

```yaml
components:
  schemas:
    StyleProfile:
      type: object
      properties:
        id: { type: string, pattern: '^stl_[A-Za-z0-9]{12}$' }
        status: { type: string, enum: [analyzing, active] }
        overall_tone:
          type: object
          properties:
            formal: { type: number }
            conversational: { type: number }
            analytical: { type: number }
            passionate: { type: number }
            humorous: { type: number }
            authoritative: { type: number }
        vocabulary_profile:
          type: object
          properties:
            avg_word_length: { type: number }
            specialized_ratio: { type: number }
            filler_word_ratio: { type: number }
            transition_word_ratio: { type: number }
        sentence_profile:
          type: object
          properties:
            avg_sentence_length: { type: number }
            avg_paragraph_length: { type: number }
            question_ratio: { type: number }
            exclamation_ratio: { type: number }
        engagement_signals:
          type: object
          properties:
            storytelling_score: { type: number }
            hook_effectiveness: { type: number }
            call_to_action_frequency: { type: number }
            readability_score: { type: number }
        sample_count: { type: integer }
        last_analyzed: { type: string, format: date-time, nullable: true }
    ContentSample:
      type: object
      required: [content, source]
      properties:
        content: { type: string, minLength: 50, maxLength: 50000 }
        source: { type: string, enum: [blog, linkedin, twitter, manual] }
        title: { type: string, maxLength: 500 }
        published_at: { type: string, format: date-time }
    StyleImportRequest:
      type: object
      required: [samples]
      properties:
        samples:
          type: array
          maxItems: 50
          items: { $ref: '#/components/schemas/ContentSample' }
```
---

## 7. Content Engine

### 7.1 List Briefs

```http
GET /api/v1/briefs
Authorization: Bearer <access_token>
```

**Query:**
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `cursor`  | string | No       | Pagination cursor |
| `limit`   | int    | No       | 1–100, default 25 |
| `status`  | string | No       | `pending`, `acknowledged`, `completed`, `dismissed` |
| `q`       | string | No       | Search query |
| `sort`    | string | No       | `created_at`, `priority` |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "brf_abc123",
      "title": "Write about microservices vs monoliths",
      "context": "Your GitHub repos show expertise in backend architecture...",
      "priority": 0.85,
      "status": "acknowledged",
      "suggested_topics": ["microservices", "monolith", "architecture"],
      "created_at": "2026-06-24T08:00:00Z",
      "_links": {
        "self": { "href": "/api/v1/briefs/brf_abc123" },
        "ideas": { "href": "/api/v1/briefs/brf_abc123/ideas" },
        "acknowledge": { "href": "/api/v1/briefs/brf_abc123/acknowledge", "method": "POST" }
      }
    }
  ],
  "meta": { "total": 8, "cursor": "...", "has_more": false }
}
```

### 7.2 Get Brief

```http
GET /api/v1/briefs/{brief_id}
```
**Response:** `200 OK` (full brief) **Errors:** `404`

### 7.3 Acknowledge Brief

```http
POST /api/v1/briefs/{brief_id}/acknowledge
```
**Response:** `200 OK` **Errors:** `404`, `409`

### 7.4 Dismiss Brief

```http
POST /api/v1/briefs/{brief_id}/dismiss
```
```json
{ "reason": "not_interested" }
```
**Response:** `200 OK`

### 7.5 Request Brief Generation

```http
POST /api/v1/briefs/generate
```
```json
{ "topics": ["serverless", "AI"], "count": 3 }
```
**Response:** `202 Accepted`
```json
{
  "data": {
    "generation_id": "gen_abc123",
    "status": "in_progress",
    "topics": ["serverless", "AI"],
    "count": 3,
    "_links": { "briefs": { "href": "/api/v1/briefs?status=pending" } }
  }
}
```

### 7.6 List _ideas

```http
GET /api/v1/briefs/{brief_id}/ideas
```
**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "idea_abc123",
      "brief_id": "brf_abc123",
      "title": "Microservices Are Not Free",
      "hook": "Before you split your monolith, here's what nobody tells you.",
      "angle": "counter-intuitive",
      "status": "approved",
      "estimated_read_time": 5,
      "created_at": "2026-06-25T10:30:00Z",
      "_links": {
        "self": { "href": "/api/v1/ideas/idea_abc123" },
        "draft": { "href": "/api/v1/ideas/idea_abc123/draft" },
        "approve": { "href": "/api/v1/ideas/idea_abc123/approve", "method": "POST" },
        "reject": { "href": "/api/v1/ideas/idea_abc123/reject", "method": "POST" }
      }
    }
  ]
}
```

### 7.7 Approve _idea

```http
POST /api/v1/ideas/{idea_id}/approve
```
**Response:** `200 OK`

### 7.8 Reject _idea

```http
POST /api/v1/ideas/{idea_id}/reject
```
```json
{ "feedback": "Been covered too many times." }
```
**Response:** `200 OK`

### 7.9 Generate Draft

```http
POST /api/v1/ideas/{idea_id}/draft
```
**Response:** `201 Created`
```json
{
  "data": {
    "id": "dft_abc123",
    "idea_id": "idea_abc123",
    "title": "Microservices Are Not Free",
    "content": "# Microservices Are Not Free\n\nBefore you split your monolith...",
    "word_count": 850,
    "read_time_minutes": 5,
    "status": "draft",
    "style_score": 0.72,
    "platform_suitability": {
      "linkedin": { "score": 0.85, "notes": "Good length for LinkedIn articles" },
      "twitter": { "score": 0.45, "notes": "Too long for thread" },
      "blog": { "score": 0.90, "notes": "Excellent fit" }
    },
    "created_at": "2026-06-25T11:00:00Z",
    "_links": {
      "self": { "href": "/api/v1/drafts/dft_abc123" },
      "revise": { "href": "/api/v1/drafts/dft_abc123/revise", "method": "POST" },
      "approve": { "href": "/api/v1/drafts/dft_abc123/approve", "method": "POST" }
    }
  }
}
```

### 7.10 Get Draft

```http
GET /api/v1/drafts/{draft_id}
```
**Response:** `200 OK` **Errors:** `404`

### 7.11 Update Draft

```http
PATCH /api/v1/drafts/{draft_id}
If-Match: "<etag>"
```
```json
{ "content": "Updated content...", "title": "Updated title" }
```
**Response:** `200 OK` **Errors:** `412`, `404`

### 7.12 Revise Draft

```http
POST /api/v1/drafts/{draft_id}/revise
```
```json
{
  "instructions": "Make it more conversational and add a personal anecdote.",
  "tone_adjustments": { "formal": -0.2, "humorous": 0.3 },
  "target_length": "same"
}
```
**Response:** `202 Accepted`
```json
{ "data": { "revision_id": "rev_abc123", "status": "in_progress", "_links": { "result": { "href": "/api/v1/drafts/dft_abc123/revisions/rev_abc123" } } } }
```

### 7.13 Get Revision

```http
GET /api/v1/drafts/{draft_id}/revisions/{revision_id}
```
**Response:** `200 OK`
```json
{ "data": { "id": "rev_abc123", "draft_id": "dft_abc123", "content": "Revised content...", "changes_summary": "Adjusted tone, added anecdote", "status": "completed", "created_at": "..." } }
```

### 7.14 List Draft Revisions

```http
GET /api/v1/drafts/{draft_id}/revisions
```
**Response:** `200 OK` (array of revision summaries)

### 7.15 Approve Draft

```http
POST /api/v1/drafts/{draft_id}/approve
```
**Response:** `200 OK`

### 7.16 Rate Content

```http
POST /api/v1/content/{content_id}/rate
```
```json
{ "rating": 4, "dimensions": { "clarity": 5, "engagement": 4, "authenticity": 5 }, "feedback": "Great post" }
```
**Response:** `200 OK` **Errors:** `422` (invalid rating)

### 7.17 Get Content History

```http
GET /api/v1/content/history
```
**Query:** `?cursor=...&limit=25&status=published&platform=linkedin&from=...&to=...`

**Response:** `200 OK` (paginated array)

### 7.18 Schedule Content

```http
POST /api/v1/content/{content_id}/schedule
```
```json
{ "scheduled_at": "2026-07-01T09:00:00Z", "platform": "linkedin" }
```
**Response:** `200 OK` **Errors:** `422` (past time)

### 7.19 Cancel Scheduled Content

```http
POST /api/v1/content/{content_id}/cancel-schedule
```
**Response:** `200 OK`

### 7.20 Content Engine Schemas

```yaml
components:
  schemas:
    Brief:
      type: object
      properties:
        id: { type: string, pattern: '^brf_[A-Za-z0-9]{12}$' }
        title: { type: string, maxLength: 500 }
        context: { type: string }
        priority: { type: number, minimum: 0, maximum: 1 }
        status: { type: string, enum: [pending, acknowledged, completed, dismissed] }
        acknowledged_at: { type: string, format: date-time, nullable: true }
        suggested_topics:
          type: array
          items: { type: string }
        knowledge_base_refs:
          type: array
          items: { type: string }
        created_at: { type: string, format: date-time }
    _idea:
      type: object
      properties:
        id: { type: string, pattern: '^idea_[A-Za-z0-9]{12}$' }
        brief_id: { type: string, pattern: '^brf_[A-Za-z0-9]{12}$' }
        title: { type: string }
        hook: { type: string }
        angle: { type: string, enum: [thought_leadership, educational, counter_intuitive, personal_story, industry_analysis, trend_based, how_to, opinion] }
        status: { type: string, enum: [pending, approved, rejected] }
        rejection_reason: { type: string, nullable: true }
        created_at: { type: string, format: date-time }
    Draft:
      type: object
      properties:
        id: { type: string, pattern: '^dft_[A-Za-z0-9]{12}$' }
        idea_id: { type: string, pattern: '^idea_[A-Za-z0-9]{12}$' }
        title: { type: string }
        content: { type: string }
        word_count: { type: integer }
        read_time_minutes: { type: integer }
        status: { type: string, enum: [draft, approved, published, archived] }
        style_score: { type: number, minimum: 0, maximum: 1 }
        version: { type: integer }
        created_at: { type: string, format: date-time }
        updated_at: { type: string, format: date-time }
    RateContentRequest:
      type: object
      required: [rating]
      properties:
        rating: { type: integer, minimum: 1, maximum: 5 }
        dimensions:
          type: object
          properties:
            clarity: { type: integer, minimum: 1, maximum: 5 }
            engagement: { type: integer, minimum: 1, maximum: 5 }
            authenticity: { type: integer, minimum: 1, maximum: 5 }
            value: { type: integer, minimum: 1, maximum: 5 }
        feedback: { type: string }
    ScheduleContentRequest:
      type: object
      required: [scheduled_at, platform]
      properties:
        scheduled_at: { type: string, format: date-time }
        platform: { type: string, enum: [linkedin, twitter, blog] }
    BriefGenerateRequest:
      type: object
      properties:
        topics: { type: array, items: { type: string } }
        count: { type: integer, default: 3, minimum: 1, maximum: 10 }
```

---

## 8. Platform Publishing

### 8.1 Publish Content

```http
POST /api/v1/platform/publish
Authorization: Bearer <access_token>
_idempotency-Key: <uuid>
```
```json
{ "draft_id": "dft_abc123", "platform": "linkedin", "publish_now": true }
```
| Field          | Type    | Required | Description |
|---------------|---------|----------|-------------|
| `draft_id`     | string  | Yes      | Approved draft ID |
| `platform`     | string  | Yes      | `linkedin`, `twitter`, `blog` |
| `publish_now`  | boolean | No       | Default true |
| `scheduled_at` | string  | No       | ISO 8601, required if publish_now=false |

**Response:** `202 Accepted`
```json
{
  "data": {
    "publication_id": "pub_abc123",
    "draft_id": "dft_abc123",
    "platform": "linkedin",
    "status": "publishing",
    "_links": { "status": { "href": "/api/v1/platform/publications/pub_abc123" } }
  }
}
```
**Errors:** `400` (not connected), `502` (platform rejected), `429` (rate limited)

### 8.2 Get Publication Status

```http
GET /api/v1/platform/publications/{publication_id}
```
**Response:** `200 OK`
```json
{
  "data": {
    "id": "pub_abc123",
    "draft_id": "dft_abc123",
    "platform": "linkedin",
    "status": "published",
    "platform_post_id": "li_post_abc123",
    "platform_post_url": "https://linkedin.com/posts/...",
    "published_at": "2026-06-26T15:00:00Z",
    "_links": { "self": { "href": "/api/v1/platform/publications/pub_abc123" }, "analytics": { "href": "/api/v1/analytics/posts/pub_abc123" } }
  }
}
```

### 8.3 List Publications

```http
GET /api/v1/platform/publications
```
**Query:** `?cursor=...&limit=25&status=published&platform=linkedin`

### 8.4 Cancel Scheduled Publication

```http
POST /api/v1/platform/publications/{publication_id}/cancel
```
**Response:** `200 OK` **Errors:** `400` (not scheduled)

### 8.5 Get Platform Post Metrics

```http
GET /api/v1/platform/publications/{publication_id}/metrics
```
**Response:** `200 OK`
```json
{
  "data": {
    "publication_id": "pub_abc123",
    "platform": "linkedin",
    "impressions": 1520,
    "likes": 85,
    "comments": 12,
    "shares": 8,
    "engagement_rate": 0.067,
    "last_synced": "2026-06-27T08:00:00Z"
  }
}
```

### 8.6 Schemas

```yaml
components:
  schemas:
    PublishRequest:
      type: object
      required: [draft_id, platform]
      properties:
        draft_id: { type: string }
        platform: { type: string, enum: [linkedin, twitter, blog] }
        publish_now: { type: boolean, default: true }
        scheduled_at: { type: string, format: date-time }
    Publication:
      type: object
      properties:
        id: { type: string, pattern: '^pub_[A-Za-z0-9]{12}$' }
        draft_id: { type: string }
        platform: { type: string, enum: [linkedin, twitter, blog] }
        status: { type: string, enum: [scheduled, publishing, published, failed] }
        platform_post_id: { type: string, nullable: true }
        platform_post_url: { type: string, format: uri, nullable: true }
        scheduled_at: { type: string, format: date-time, nullable: true }
        published_at: { type: string, format: date-time, nullable: true }
        error_message: { type: string, nullable: true }
        created_at: { type: string, format: date-time }
    PostMetrics:
      type: object
      properties:
        publication_id: { type: string }
        platform: { type: string }
        impressions: { type: integer }
        likes: { type: integer }
        comments: { type: integer }
        shares: { type: integer }
        engagement_rate: { type: number }
        last_synced: { type: string, format: date-time }
```

---

## 9. Trends

### 9.1 Get Trending Topics

```http
GET /api/v1/trends
Authorization: Bearer <access_token>
```
**Query:** `?sources=github,twitter&limit=20&since=2026-06-01`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "trd_abc123",
      "topic": "AI Agents",
      "source": "github",
      "source_name": "GitHub Trending",
      "volume": 1250,
      "growth_percent": 34.5,
      "related_terms": ["agentic ai", "tool use", "autonomous agents"],
      "relevance_score": 0.92,
      "top_content": [{ "title": "openai/gpt-agent", "url": "https://github.com/openai/gpt-agent", "stars": 5200 }],
      "first_seen": "2026-06-20T00:00:00Z"
    }
  ],
  "meta": { "total": 35 }
}
```

### 9.2 Get Trend Detail

```http
GET /api/v1/trends/{trend_id}
```
**Response:** `200 OK` (detailed trend with history)

### 9.3 Get Trend Sources

```http
GET /api/v1/trends/sources
```
**Response:** `200 OK`
```json
{
  "data": [
    { "id": "github", "name": "GitHub Trending", "enabled": true, "last_fetched": "2026-06-26T13:00:00Z" },
    { "id": "twitter", "name": "Twitter/X", "enabled": true, "last_fetched": "2026-06-26T13:30:00Z" },
    { "id": "hackernews", "name": "Hacker News", "enabled": true, "last_fetched": "2026-06-26T14:00:00Z" }
  ]
}
```

### 9.4 Toggle Trend Source

```http
PATCH /api/v1/trends/sources/{source_id}
```
```json
{ "enabled": false }
```
**Response:** `200 OK`

### 9.5 Get Trend Relevance

```http
POST /api/v1/trends/relevance
```
```json
{ "topics": ["AI Agents", "Rust", "Serverless"] }
```
**Response:** `200 OK`
```json
{
  "data": [
    { "topic": "AI Agents", "relevance_score": 0.92, "matching_expertise": ["AI/ML"], "matching_kb_items": 12, "suggested_angle": "Building AI agents with Python" },
    { "topic": "Rust", "relevance_score": 0.15, "matching_expertise": [], "matching_kb_items": 1, "suggested_angle": null }
  ]
}
```

### 9.6 Schemas

```yaml
components:
  schemas:
    Trend:
      type: object
      properties:
        id: { type: string, pattern: '^trd_[A-Za-z0-9]{12}$' }
        topic: { type: string }
        source: { type: string, enum: [github, twitter, news, hackernews] }
        source_name: { type: string }
        volume: { type: integer }
        growth_percent: { type: number }
        related_terms: { type: array, items: { type: string } }
        relevance_score: { type: number, minimum: 0, maximum: 1 }
        top_content:
          type: array
          items:
            type: object
            properties:
              title: { type: string }
              url: { type: string, format: uri }
              stars: { type: integer }
        first_seen: { type: string, format: date-time }
    TrendRelevanceRequest:
      type: object
      required: [topics]
      properties:
        topics:
          type: array
          items: { type: string }
          minItems: 1
          maxItems: 20
    TrendRelevanceResult:
      type: object
      properties:
        topic: { type: string }
        relevance_score: { type: number }
        matching_expertise: { type: array, items: { type: string } }
        matching_kb_items: { type: integer }
        suggested_angle: { type: string, nullable: true }
    TrendSource:
      type: object
      properties:
        id: { type: string }
        name: { type: string }
        enabled: { type: boolean }
        last_fetched: { type: string, format: date-time, nullable: true }
```

---

## 10. Analytics

### 10.1 Get Dashboard Overview

```http
GET /api/v1/analytics/dashboard
Authorization: Bearer <access_token>
```
**Query:** `?period=30d`

**Response:** `200 OK`
```json
{
  "data": {
    "period": { "from": "2026-05-27T00:00:00Z", "to": "2026-06-26T00:00:00Z" },
    "summary": {
      "total_posts": 12,
      "total_impressions": 18500,
      "total_engagement": 1480,
      "avg_engagement_rate": 0.08,
      "content_score_avg": 72.5
    },
    "trends": {
      "impressions": { "current": 18500, "previous": 12200, "change_pct": 51.6 },
      "engagement": { "current": 1480, "previous": 980, "change_pct": 51.0 }
    },
    "top_performers": [
      { "id": "pub_abc123", "title": "Microservices post", "impressions": 3200, "engagement_rate": 0.12 }
    ]
  }
}
```
**Errors:** `404` (no data)

### 10.2 Get Post Analytics

```http
GET /api/v1/analytics/posts/{publication_id}
```
**Response:** `200 OK` (detailed metrics with cumulative timeline and demographics)

### 10.3 Get Engagement Analytics

```http
GET /api/v1/analytics/engagement?period=30d
```
**Response:** `200 OK`
```json
{
  "data": {
    "by_type": {
      "likes": { "total": 580, "avg_per_post": 48.3 },
      "comments": { "total": 92, "avg_per_post": 7.7 },
      "shares": { "total": 45, "avg_per_post": 3.8 }
    },
    "daily": [{"date": "2026-06-20", "likes": 25, "comments": 5, "shares": 3}],
    "best_times": { "day_of_week": "Tuesday", "time_of_day": "09:00 - 11:00" }
  }
}
```

### 10.4 Get Audience Analytics

```http
GET /api/v1/analytics/audience?period=30d
```
**Response:** `200 OK` (follower growth, top industries, locations, active hours)

### 10.5 Get Content Score

```http
GET /api/v1/analytics/content-score?period=30d
```
**Response:** `200 OK`
```json
{
  "data": {
    "overall_score": 72.5,
    "dimensions": { "clarity": 78, "engagement": 68, "authenticity": 85, "value": 75, "consistency": 65 },
    "trend": [
      { "date": "2026-06-01", "score": 68 },
      { "date": "2026-06-22", "score": 75 }
    ],
    "recommendations": [
      "Increase use of storytelling hooks in openings",
      "Post more consistently (target 3-4 posts/week)"
    ]
  }
}
```

### 10.6 Export Analytics

```http
GET /api/v1/analytics/export?format=csv&type=all&from=...&to=...
```
**Response:** `200 OK` with `Content-Type: text/csv` and `Content-Disposition: attachment`

### 10.7 Schemas

```yaml
components:
  schemas:
    AnalyticsOverview:
      type: object
      properties:
        period:
          type: object
          properties:
            from: { type: string, format: date-time }
            to: { type: string, format: date-time }
        summary:
          type: object
          properties:
            total_posts: { type: integer }
            total_impressions: { type: integer }
            total_engagement: { type: integer }
            avg_engagement_rate: { type: number }
            content_score_avg: { type: number }
        trends:
          type: object
          properties:
            impressions:
              type: object
              properties:
                current: { type: integer }
                previous: { type: integer }
                change_pct: { type: number }
    PostAnalytics:
      type: object
      properties:
        publication_id: { type: string }
        title: { type: string }
        platform: { type: string }
        published_at: { type: string, format: date-time }
        metrics:
          type: object
          properties:
            impressions: { type: integer }
            likes: { type: integer }
            comments: { type: integer }
            shares: { type: integer }
            engagement_rate: { type: number }
    ContentScore:
      type: object
      properties:
        overall_score: { type: number }
        dimensions:
          type: object
          properties:
            clarity: { type: number }
            engagement: { type: number }
            authenticity: { type: number }
            value: { type: number }
            consistency: { type: number }
        trend:
          type: array
          items:
            type: object
            properties:
              date: { type: string, format: date-time }
              score: { type: number }
```

---

## 11. Briefs (Schedule)

### 11.1 Schedule Brief Generation

```http
POST /api/v1/briefs/schedule
Authorization: Bearer <access_token>
```
```json
{ "frequency": "daily", "topics": ["AI", "startups"], "max_briefs": 3, "time": "08:00" }
```
**Response:** `201 Created`
```json
{
  "data": {
    "schedule_id": "sch_abc123",
    "frequency": "daily",
    "topics": ["AI", "startups"],
    "max_briefs": 3,
    "time": "08:00",
    "enabled": true,
    "next_generation": "2026-06-27T12:00:00Z"
  }
}
```

### 11.2 Get Schedule

```http
GET /api/v1/briefs/schedule
```
**Response:** `200 OK`

### 11.3 Update Schedule

```http
PATCH /api/v1/briefs/schedule/{schedule_id}
```
**Response:** `200 OK`

### 11.4 Delete Schedule

```http
DELETE /api/v1/briefs/schedule/{schedule_id}
```
**Response:** `204 No Content`
---

## 12. Notifications

### 12.1 List Notifications

```http
GET /api/v1/notifications
Authorization: Bearer <access_token>
```
**Query:** `?cursor=...&limit=25&unread_only=true&type=brief_ready`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "notif_abc123",
      "type": "brief_ready",
      "title": "New content brief available",
      "body": "A brief about AI Agents is ready for review.",
      "read": false,
      "action_url": "/api/v1/briefs/brf_abc123",
      "created_at": "2026-06-26T08:00:00Z",
      "_links": {
        "self": { "href": "/api/v1/notifications/notif_abc123" },
        "mark_read": { "href": "/api/v1/notifications/notif_abc123/read", "method": "POST" }
      }
    }
  ],
  "meta": { "total": 15, "unread_count": 3, "cursor": "...", "has_more": true }
}
```

**Types:** `brief_ready`, `sync_complete`, `publish_success`, `publish_failed`, `style_analysis_done`, `trend_alert`, `platform_disconnected`, `scheduled_post`

### 12.2 Mark Notification Read

```http
POST /api/v1/notifications/{notification_id}/read
```
**Response:** `204 No Content` **Errors:** `404`

### 12.3 Mark All Read

```http
POST /api/v1/notifications/read-all
```
**Response:** `204 No Content`

### 12.4 Get Notification Preferences

```http
GET /api/v1/notifications/preferences
```
**Response:** `200 OK`
```json
{
  "data": {
    "push_enabled": true,
    "email_enabled": false,
    "types": {
      "brief_ready": { "push": true, "email": true },
      "publish_failed": { "push": true, "email": true }
    }
  }
}
```

### 12.5 Update Notification Preferences

```http
PATCH /api/v1/notifications/preferences
```
**Response:** `200 OK`

### 12.6 Schemas

```yaml
components:
  schemas:
    Notification:
      type: object
      properties:
        id: { type: string, pattern: '^notif_[A-Za-z0-9]{12}$' }
        type:
          type: string
          enum: [brief_ready, sync_complete, publish_success, publish_failed, style_analysis_done, trend_alert, platform_disconnected, scheduled_post]
        title: { type: string }
        body: { type: string }
        read: { type: boolean }
        action_url: { type: string }
        created_at: { type: string, format: date-time }
    NotificationPreferences:
      type: object
      properties:
        push_enabled: { type: boolean }
        email_enabled: { type: boolean }
        types:
          type: object
          additionalProperties:
            type: object
            properties:
              push: { type: boolean }
              email: { type: boolean }
```

---

## 13. Admin

### 13.1 Get System Stats

```http
GET /api/v1/admin/stats
Authorization: Bearer <access_token>
```
**Requires:** `admin` scope

**Response:** `200 OK`
```json
{
  "data": {
    "users": { "total": 1, "active_last_30d": 1 },
    "knowledge_base": { "total_items": 356, "total_tags": 28, "total_embeddings": 350 },
    "content": { "total_drafts": 48, "total_briefs": 22, "total_published": 12 },
    "connections": { "total": 2, "expired": 0 },
    "system": {
      "storage_used_mb": 45.2,
      "chroma_collection_size": 45000,
      "last_embedding_run": "2026-06-26T13:00:00Z",
      "api_requests_24h": 1245
    }
  }
}
```
**Errors:** `403` (`ADMIN_ONLY`)

### 13.2 Force Sync

```http
POST /api/v1/admin/force-sync/{user_id}
```
**Response:** `202 Accepted`

### 13.3 List Users

```http
GET /api/v1/admin/users?page=1&per_page=25
```
**Response:** `200 OK` (paginated)

### 13.4 Get User Detail

```http
GET /api/v1/admin/users/{user_id}
```
**Response:** `200 OK` **Errors:** `404`

### 13.5 Regenerate Embeddings

```http
POST /api/v1/admin/regenerate-embeddings
```
**Response:** `202 Accepted`

### 13.6 Schemas

```yaml
components:
  schemas:
    AdminStats:
      type: object
      properties:
        users:
          type: object
          properties:
            total: { type: integer }
            active_last_30d: { type: integer }
        knowledge_base:
          type: object
          properties:
            total_items: { type: integer }
            total_tags: { type: integer }
            total_embeddings: { type: integer }
        content:
          type: object
          properties:
            total_drafts: { type: integer }
            total_briefs: { type: integer }
            total_published: { type: integer }
        connections:
          type: object
          properties:
            total: { type: integer }
            expired: { type: integer }
        system:
          type: object
          properties:
            storage_used_mb: { type: number }
            chroma_collection_size: { type: integer }
            last_embedding_run: { type: string, format: date-time, nullable: true }
            api_requests_24h: { type: integer }
```

---

## 14. Health

### 14.1 Health Check

```http
GET /api/v1/health
```

**Response:** `200 OK`
```json
{
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime_seconds": 86400,
    "checks": {
      "database": { "status": "healthy", "response_time_ms": 2 },
      "chromadb": { "status": "healthy", "response_time_ms": 5 },
      "embedding_service": { "status": "healthy", "response_time_ms": 120 }
    }
  }
}
```

### 14.2 Readiness

```http
GET /api/v1/health/ready
```
**Response:** `200 OK` or `503` if dependencies unavailable

### 14.3 Liveness

```http
GET /api/v1/health/live
```
**Response:** `200 OK`

---

## 15. Webhooks

### 15.1 GitHub Push Webhook

```http
POST /api/v1/webhooks/github
X-GitHub-Event: push
X-Hub-Signature-256: sha256=...
Content-Type: application/json
```

Signed payload verification: HMAC-SHA256 of body using user's webhook secret.

**Response:** `202 Accepted`
```json
{
  "data": {
    "received": true,
    "action": "push",
    "repo": "alexj/brandos",
    "ref": "refs/heads/main"
  }
}
```

### 15.2 LinkedIn Engagement Webhook

```http
POST /api/v1/webhooks/linkedin
```
**Response:** `202 Accepted`

---

## 16. OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: BrandOS API
  version: 1.0.0
  description: AI-powered personal brand operating system
  contact:
    name: BrandOS Team
    url: https://brandos.app
servers:
- url: https://api.brandos.app/api/v1
  description: Production
- url: https://staging-api.brandos.app/api/v1
  description: Staging
security:
- BearerAuth: []
paths:
  /auth/register:
    post:
      tags:
      - Authentication
      summary: Register a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AuthRegisterRequest'
      responses:
        '201':
          description: Account created
        '409':
          description: Email exists
        '422':
          description: Validation error
        '400':
          $ref: '#/components/responses/BadRequest'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Create a new user account with email and password
  /auth/login:
    post:
      tags:
      - Authentication
      summary: Login with email and password
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AuthLoginRequest'
      responses:
        '200':
          description: Authenticated
        '401':
          description: Invalid credentials
        '400':
          $ref: '#/components/responses/BadRequest'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Authenticate with email and password, receive access and refresh tokens
  /auth/oauth:
    post:
      tags:
      - Authentication
      summary: OAuth authentication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
              - provider
              - code
              properties:
                provider:
                  type: string
                  enum:
                  - google
                  - github
                  - apple
                code:
                  type: string
      responses:
        '200':
          description: Authenticated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '409':
          $ref: '#/components/responses/Conflict'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Authenticate via OAuth 2.0 provider (Google, GitHub, or Apple)
  /auth/refresh:
    post:
      tags:
      - Authentication
      summary: Refresh access token
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
              - refresh_token
              properties:
                refresh_token:
                  type: string
      responses:
        '200':
          description: Tokens refreshed
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Exchange a valid refresh token for a new access token pair
  /auth/logout:
    post:
      tags:
      - Authentication
      summary: Revoke tokens
      security:
      - BearerAuth: []
      responses:
        '204':
          description: Logged out
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Revoke all active tokens for the current session
  /auth/me:
    get:
      tags:
      - Authentication
      summary: Get current user
      security:
      - BearerAuth: []
      responses:
        '200':
          description: User profile
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve the currently authenticated user's profile and account information
  /auth/change-password:
    post:
      tags:
      - Authentication
      summary: Change password
      security:
      - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
              - current_password
              - new_password
              properties:
                current_password:
                  type: string
                new_password:
                  type: string
                  minLength: 8
                  maxLength: 128
      responses:
        '204':
          description: Password changed
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Change the current user's password (requires current password verification)
  /profile:
    get:
      tags:
      - Profile
      summary: Get profile
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Profile
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve the authenticated user's full profile including bio, avatar, and links
    patch:
      tags:
      - Profile
      summary: Update profile
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Updated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update the authenticated user's profile fields
  /profile/preferences:
    patch:
      tags:
      - Profile
      summary: Update preferences
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Updated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update user preferences (theme, notification settings, content defaults)
  /profile/expertise:
    post:
      tags:
      - Profile
      summary: Add expertise
      security:
      - BearerAuth: []
      responses:
        '201':
          description: Created
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Add a new expertise area or skill tag to the user's profile
  /profile/expertise/{expertiseId}:
    delete:
      tags:
      - Profile
      summary: Remove expertise
      security:
      - BearerAuth: []
      parameters:
      - name: expertiseId
        in: path
        required: true
        schema:
          type: string
      responses:
        '204':
          description: Removed
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Remove an expertise area from the user's profile
  /profile/onboarding/complete:
    post:
      tags:
      - Profile
      summary: Complete onboarding
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Done
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Mark the onboarding flow as completed and enable all features
  /connections:
    get:
      tags:
      - Connections
      summary: List connections
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Connection list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      - name: platform
        in: query
        required: false
        schema:
          type: string
          enum:
          - github
          - linkedin
          - twitter
          - medium
          description: Filter by platform
      description: List all third-party platform connections with their sync status
  /connections/oauth-url:
    post:
      tags:
      - Connections
      summary: Get OAuth URL
      security:
      - BearerAuth: []
      responses:
        '200':
          description: OAuth URL
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Generate an OAuth 2.0 authorization URL for a specified platform
  /connections/callback:
    post:
      tags:
      - Connections
      summary: Complete OAuth
      security:
      - BearerAuth: []
      responses:
        '201':
          description: Connected
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Complete OAuth 2.0 handshake by exchanging the callback code for tokens
  /connections/{connectionId}:
    get:
      tags:
      - Connections
      summary: Get connection
      security:
      - BearerAuth: []
      parameters:
      - name: connectionId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Connection
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve details and status for a specific platform connection
    delete:
      tags:
      - Connections
      summary: Disconnect
      security:
      - BearerAuth: []
      parameters:
      - name: connectionId
        in: path
        required: true
        schema:
          type: string
      responses:
        '204':
          description: Disconnected
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Disconnect and revoke access for a specific platform connection
  /connections/{connectionId}/refresh:
    post:
      tags:
      - Connections
      summary: Refresh token
      security:
      - BearerAuth: []
      parameters:
      - name: connectionId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Token refreshed
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Manually refresh the OAuth 2.0 access token for a connection
  /connections/github/repos:
    get:
      tags:
      - Connections
      summary: List repos
      security:
      - BearerAuth: []
      parameters:
      - name: page
        in: query
        schema:
          type: integer
          default: 1
      - name: perPage
        in: query
        schema:
          type: integer
          default: 30
      responses:
        '200':
          description: Repo list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: List GitHub repositories accessible through the authenticated connection
  /connections/github/selected-repos:
    put:
      tags:
      - Connections
      summary: Select repos
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Saved
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update the set of GitHub repositories selected for syncing
  /connections/github/sync:
    post:
      tags:
      - Connections
      summary: Trigger sync
      security:
      - BearerAuth: []
      responses:
        '202':
          description: Sync started
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Trigger an immediate GitHub-to-knowledge-base synchronization
  /connections/github/sync/{syncId}:
    get:
      tags:
      - Connections
      summary: Sync status
      security:
      - BearerAuth: []
      parameters:
      - name: syncId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Sync status
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Poll the status of a GitHub synchronization job
  /kb/items:
    get:
      tags:
      - Knowledge Base
      summary: List items
      security:
      - BearerAuth: []
      parameters:
      - name: cursor
        in: query
        schema:
          type: string
      - name: limit
        in: query
        schema:
          type: integer
          default: 25
      - name: contentType
        in: query
        schema:
          type: string
          enum:
          - documentation
          - code
          - issue
          - discussion
          - note
          - snippet
      - name: status
        in: query
        schema:
          type: string
          enum:
          - active
          - archived
      - name: tag
        in: query
        schema:
          type: string
      - name: q
        in: query
        schema:
          type: string
      responses:
        '200':
          description: Item list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: List knowledge base items with optional filtering by type, status, and tags
    post:
      tags:
      - Knowledge Base
      summary: Create item
      security:
      - BearerAuth: []
      responses:
        '201':
          description: Created
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Create a new knowledge base item (documentation, code, note, etc.)
  /kb/items/{itemId}:
    get:
      tags:
      - Knowledge Base
      summary: Get item
      security:
      - BearerAuth: []
      parameters:
      - name: itemId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Item detail
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve a single knowledge base item by ID with full content
    patch:
      tags:
      - Knowledge Base
      summary: Update item
      security:
      - BearerAuth: []
      parameters:
      - name: itemId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Updated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update a knowledge base item's content, title, or metadata
    delete:
      tags:
      - Knowledge Base
      summary: Delete item
      security:
      - BearerAuth: []
      parameters:
      - name: itemId
        in: path
        required: true
        schema:
          type: string
      responses:
        '204':
          description: Deleted
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Delete a knowledge base item permanently
  /kb/items/{itemId}/related:
    get:
      tags:
      - Knowledge Base
      summary: Related items
      security:
      - BearerAuth: []
      parameters:
      - name: itemId
        in: path
        required: true
        schema:
          type: string
      - name: limit
        in: query
        schema:
          type: integer
          default: 5
      responses:
        '200':
          description: Related list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Find semantically related knowledge base items using vector similarity
  /kb/search:
    get:
      tags:
      - Knowledge Base
      summary: Hybrid search
      security:
      - BearerAuth: []
      parameters:
      - name: q
        in: query
        required: true
        schema:
          type: string
      - name: limit
        in: query
        schema:
          type: integer
          default: 10
      - name: alpha
        in: query
        schema:
          type: number
          default: 0.5
      responses:
        '200':
          description: Results
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Full-text and semantic hybrid search across all knowledge base items
  /kb/tags:
    get:
      tags:
      - Knowledge Base
      summary: List tags
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Tag list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      description: List all tags used across the knowledge base with usage counts
  /kb/tags/suggest:
    post:
      tags:
      - Knowledge Base
      summary: Suggest tags
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Suggestions
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Generate AI-powered tag suggestions for a given piece of content
  /kb/tags/merge:
    post:
      tags:
      - Knowledge Base
      summary: Merge tags
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Merged
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Merge two or more tags into a single canonical tag
  /kb/tags/{tagId}:
    delete:
      tags:
      - Knowledge Base
      summary: Delete tag
      security:
      - BearerAuth: []
      parameters:
      - name: tagId
        in: path
        required: true
        schema:
          type: string
      responses:
        '204':
          description: Deleted
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Delete a tag and remove it from all associated items
  /kb/embedding-status:
    get:
      tags:
      - Knowledge Base
      summary: Embedding status
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Status
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Check the status of vector embedding generation for knowledge base items
  /style/profile:
    get:
      tags:
      - Style Analysis
      summary: Get style profile
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Style profile
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve the user's AI-generated writing style profile
    patch:
      tags:
      - Style Analysis
      summary: Update preferences
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Updated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update the writing style profile with manual adjustments
  /style/progress:
    get:
      tags:
      - Style Analysis
      summary: Get progress
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Progress
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Get the style learning progress (number of samples analyzed, confidence score)
  /style/analyze:
    post:
      tags:
      - Style Analysis
      summary: Trigger analysis
      security:
      - BearerAuth: []
      responses:
        '202':
          description: Started
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Submit content samples for AI writing style analysis
  /style/import:
    post:
      tags:
      - Style Analysis
      summary: Import samples
      security:
      - BearerAuth: []
      responses:
        '201':
          description: Imported
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Import existing published content to accelerate style learning
  /style/insights:
    get:
      tags:
      - Style Analysis
      summary: Get insights
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Insights
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Get actionable insights about the user's writing patterns and suggestions
  /briefs:
    get:
      tags:
      - Content Engine
      summary: List briefs
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Brief list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      - name: status
        in: query
        required: false
        schema:
          type: string
          enum:
          - active
          - acknowledged
          - dismissed
          description: Filter by brief status
      description: List content briefs generated from trend analysis and scheduled topics
  /briefs/generate:
    post:
      tags:
      - Content Engine
      summary: Generate briefs
      security:
      - BearerAuth: []
      responses:
        '202':
          description: Generating
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Generate a new content brief from trending topics in the user's expertise areas
  /briefs/{briefId}:
    get:
      tags:
      - Content Engine
      summary: Get brief
      security:
      - BearerAuth: []
      parameters:
      - name: briefId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Brief detail
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve a specific content brief with full detail
  /briefs/{briefId}/acknowledge:
    post:
      tags:
      - Content Engine
      summary: Acknowledge brief
      security:
      - BearerAuth: []
      parameters:
      - name: briefId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Acknowledged
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Mark a content brief as reviewed and acknowledged
  /briefs/{briefId}/dismiss:
    post:
      tags:
      - Content Engine
      summary: Dismiss brief
      security:
      - BearerAuth: []
      parameters:
      - name: briefId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Dismissed
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Dismiss a content brief (removes from active queue)
  /briefs/{briefId}/ideas:
    get:
      tags:
      - Content Engine
      summary: List ideas
      security:
      - BearerAuth: []
      parameters:
      - name: briefId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Idea list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: List AI-generated content ideas derived from a specific brief
  /briefs/schedule:
    get:
      tags:
      - Content Engine
      summary: Get schedule
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Schedule
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      description: List all content brief generation schedules with cadence and status
    post:
      tags:
      - Content Engine
      summary: Create schedule
      security:
      - BearerAuth: []
      responses:
        '201':
          description: Created
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Create a recurring schedule for automated content brief generation
  /briefs/schedule/{scheduleId}:
    patch:
      tags:
      - Content Engine
      summary: Update schedule
      security:
      - BearerAuth: []
      parameters:
      - name: scheduleId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Updated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update a brief generation schedule's cadence or parameters
    delete:
      tags:
      - Content Engine
      summary: Delete schedule
      security:
      - BearerAuth: []
      parameters:
      - name: scheduleId
        in: path
        required: true
        schema:
          type: string
      responses:
        '204':
          description: Deleted
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Delete a brief generation schedule
  /ideas/{ideaId}/approve:
    post:
      tags:
      - Content Engine
      summary: Approve idea
      security:
      - BearerAuth: []
      parameters:
      - name: ideaId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Approved
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Approve a content idea, moving it to the drafting queue
  /ideas/{ideaId}/reject:
    post:
      tags:
      - Content Engine
      summary: Reject idea
      security:
      - BearerAuth: []
      parameters:
      - name: ideaId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Rejected
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Reject a content idea with optional reason
  /ideas/{ideaId}/draft:
    post:
      tags:
      - Content Engine
      summary: Generate draft
      security:
      - BearerAuth: []
      parameters:
      - name: ideaId
        in: path
        required: true
        schema:
          type: string
      responses:
        '201':
          description: Draft created
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Generate an AI draft from an approved content idea
  /drafts/{draftId}:
    get:
      tags:
      - Content Engine
      summary: Get draft
      security:
      - BearerAuth: []
      parameters:
      - name: draftId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Draft
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve a single draft with full content and metadata
    patch:
      tags:
      - Content Engine
      summary: Update draft
      security:
      - BearerAuth: []
      parameters:
      - name: draftId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Updated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update a draft's content, title, or metadata
  /drafts/{draftId}/revise:
    post:
      tags:
      - Content Engine
      summary: Revise draft
      security:
      - BearerAuth: []
      parameters:
      - name: draftId
        in: path
        required: true
        schema:
          type: string
      responses:
        '202':
          description: Revising
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Request an AI revision of a draft with specific instructions
  /drafts/{draftId}/revisions:
    get:
      tags:
      - Content Engine
      summary: List revisions
      security:
      - BearerAuth: []
      parameters:
      - name: draftId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Revision list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: List all revision history entries for a draft
  /drafts/{draftId}/revisions/{revisionId}:
    get:
      tags:
      - Content Engine
      summary: Get revision
      security:
      - BearerAuth: []
      parameters:
      - name: draftId
        in: path
        required: true
        schema:
          type: string
      - name: revisionId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Revision
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve a specific revision entry
  /drafts/{draftId}/approve:
    post:
      tags:
      - Content Engine
      summary: Approve draft
      security:
      - BearerAuth: []
      parameters:
      - name: draftId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Approved
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Mark a draft as approved and ready for scheduling/publication
  /content/history:
    get:
      tags:
      - Content Engine
      summary: Content history
      security:
      - BearerAuth: []
      responses:
        '200':
          description: History
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      - name: status
        in: query
        required: false
        schema:
          type: string
          enum:
          - draft
          - scheduled
          - published
          - failed
          description: Filter by content status
      description: List all published and scheduled content items in chronological order
  /content/{contentId}/rate:
    post:
      tags:
      - Content Engine
      summary: Rate content
      security:
      - BearerAuth: []
      parameters:
      - name: contentId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Rated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Rate a published content item's performance (1-5 stars)
  /content/{contentId}/schedule:
    post:
      tags:
      - Content Engine
      summary: Schedule content
      security:
      - BearerAuth: []
      parameters:
      - name: contentId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Scheduled
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Schedule a content item for publication at a specific time
  /content/{contentId}/cancel-schedule:
    post:
      tags:
      - Content Engine
      summary: Cancel schedule
      security:
      - BearerAuth: []
      parameters:
      - name: contentId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Cancelled
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Cancel a previously scheduled publication
  /platform/publish:
    post:
      tags:
      - Platform Publishing
      summary: Publish content
      security:
      - BearerAuth: []
      responses:
        '202':
          description: Publishing
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Publish content to one or more connected platforms
  /platform/publications:
    get:
      tags:
      - Platform Publishing
      summary: List publications
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Publication list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      - name: status
        in: query
        required: false
        schema:
          type: string
          enum:
          - pending
          - in_progress
          - completed
          - failed
          description: Filter by publication status
      - name: platform
        in: query
        required: false
        schema:
          type: string
          description: Filter by target platform
      description: List all publication records with cross-platform status
  /platform/publications/{publicationId}:
    get:
      tags:
      - Platform Publishing
      summary: Get publication
      security:
      - BearerAuth: []
      parameters:
      - name: publicationId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Publication
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve a specific publication record with per-platform status
  /platform/publications/{publicationId}/cancel:
    post:
      tags:
      - Platform Publishing
      summary: Cancel publication
      security:
      - BearerAuth: []
      parameters:
      - name: publicationId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Cancelled
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Cancel an in-progress or scheduled publication
  /platform/publications/{publicationId}/metrics:
    get:
      tags:
      - Platform Publishing
      summary: Get metrics
      security:
      - BearerAuth: []
      parameters:
      - name: publicationId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Metrics
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve analytics for a specific publication
  /trends:
    get:
      tags:
      - Trends
      summary: Get trending topics
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Trends
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      - name: minRelevance
        in: query
        required: false
        schema:
          type: number
          minimum: 0
          maximum: 1
          description: Minimum relevance score filter
      description: List trending topics with relevance scores for the user's expertise areas
  /trends/{trendId}:
    get:
      tags:
      - Trends
      summary: Get trend detail
      security:
      - BearerAuth: []
      parameters:
      - name: trendId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Trend detail
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve details for a specific trending topic
  /trends/sources:
    get:
      tags:
      - Trends
      summary: List sources
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Sources
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      description: List configured trend monitoring sources and their status
  /trends/sources/{sourceId}:
    patch:
      tags:
      - Trends
      summary: Toggle source
      security:
      - BearerAuth: []
      parameters:
      - name: sourceId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Updated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update a trend source's configuration or enable/disable
  /trends/relevance:
    post:
      tags:
      - Trends
      summary: Score relevance
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Scored
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Recalculate relevance scores for all tracked trends against user expertise
  /analytics/dashboard:
    get:
      tags:
      - Analytics
      summary: Dashboard
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Dashboard
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      description: Get aggregate analytics dashboard data (posts, engagement, growth metrics)
  /analytics/posts/{publicationId}:
    get:
      tags:
      - Analytics
      summary: Post analytics
      security:
      - BearerAuth: []
      parameters:
      - name: publicationId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: Post analytics
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Get per-post analytics for a specific publication
  /analytics/engagement:
    get:
      tags:
      - Analytics
      summary: Engagement
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Engagement data
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      - name: period
        in: query
        required: false
        schema:
          type: string
          enum:
          - 7d
          - 30d
          - 90d
          description: Time period for aggregation
      description: Get engagement analytics (likes, comments, shares over time)
  /analytics/audience:
    get:
      tags:
      - Analytics
      summary: Audience
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Audience data
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      - name: period
        in: query
        required: false
        schema:
          type: string
          enum:
          - 7d
          - 30d
          - 90d
          description: Time period for aggregation
      description: Get audience demographics and growth analytics
  /analytics/content-score:
    get:
      tags:
      - Analytics
      summary: Content score
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Content score
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      description: Get content quality scoring across dimensions (readability, engagement prediction)
  /analytics/export:
    get:
      tags:
      - Analytics
      summary: Export data
      security:
      - BearerAuth: []
      parameters:
      - name: format
        in: query
        required: true
        schema:
          type: string
          enum:
          - csv
          - json
      - name: page
        in: query
        required: false
        schema:
          type: integer
          default: 1
          minimum: 1
          description: Page number
      - name: perPage
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Items per page
      responses:
        '200':
          description: File download
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Export analytics data in CSV or JSON format for external analysis
  /notifications:
    get:
      tags:
      - Notifications
      summary: List notifications
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Notifications
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: cursor
        in: query
        required: false
        schema:
          type: string
          description: Opaque cursor for pagination (returned by previous response)
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Maximum items to return
      - name: unreadOnly
        in: query
        required: false
        schema:
          type: boolean
          default: false
          description: Return only unread notifications
      - name: category
        in: query
        required: false
        schema:
          type: string
          enum:
          - sync
          - publication
          - system
          - trend
          description: Filter by notification category
      description: List all notifications for the authenticated user
  /notifications/{notificationId}/read:
    post:
      tags:
      - Notifications
      summary: Mark read
      security:
      - BearerAuth: []
      parameters:
      - name: notificationId
        in: path
        required: true
        schema:
          type: string
      responses:
        '204':
          description: Marked
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Mark a specific notification as read
  /notifications/read-all:
    post:
      tags:
      - Notifications
      summary: Mark all read
      security:
      - BearerAuth: []
      responses:
        '204':
          description: Done
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Mark all unread notifications as read
  /notifications/preferences:
    get:
      tags:
      - Notifications
      summary: Get preferences
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Preferences
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Get notification channel and category preferences
    patch:
      tags:
      - Notifications
      summary: Update preferences
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Updated
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Update notification preferences per channel and category
  /admin/stats:
    get:
      tags:
      - Admin
      summary: System stats
      security:
      - BearerAuth: []
      responses:
        '200':
          description: Stats
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '403':
          description: Forbidden
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
  /admin/force-sync/{userId}:
    post:
      tags:
      - Admin
      summary: Force sync
      security:
      - BearerAuth: []
      parameters:
      - name: userId
        in: path
        required: true
        schema:
          type: string
      responses:
        '202':
          description: Syncing
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Trigger a forced knowledge base sync for a specified user (admin only)
  /admin/users:
    get:
      tags:
      - Admin
      summary: List users
      security:
      - BearerAuth: []
      responses:
        '200':
          description: User list
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      parameters:
      - name: page
        in: query
        required: false
        schema:
          type: integer
          default: 1
          minimum: 1
          description: Page number
      - name: perPage
        in: query
        required: false
        schema:
          type: integer
          default: 25
          maximum: 100
          description: Items per page
      description: List all registered users with account status (admin only)
  /admin/users/{userId}:
    get:
      tags:
      - Admin
      summary: Get user
      security:
      - BearerAuth: []
      parameters:
      - name: userId
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: User
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Retrieve a specific user's details and system status (admin only)
  /admin/regenerate-embeddings:
    post:
      tags:
      - Admin
      summary: Regenerate embeddings
      security:
      - BearerAuth: []
      responses:
        '202':
          description: Started
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Trigger regeneration of all vector embeddings for the entire knowledge base
  /health:
    get:
      tags:
      - Health
      summary: Health check
      responses:
        '200':
          description: Healthy
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Basic health check returning server status and uptime
  /health/ready:
    get:
      tags:
      - Health
      summary: Readiness
      responses:
        '200':
          description: Ready
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Readiness check verifying all dependencies (DB, Chroma, queue) are reachable
  /health/live:
    get:
      tags:
      - Health
      summary: Liveness
      responses:
        '200':
          description: Alive
          headers:
            Cache-Control:
              schema:
                type: string
                example: public, max-age=60
              description: Caching directive
            ETag:
              schema:
                type: string
                example: '"a1b2c3d4e5"'
              description: Entity tag for conditional requests
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Liveness check for load balancer health probes
  /webhooks/github:
    post:
      tags:
      - Webhooks
      summary: GitHub push webhook
      responses:
        '202':
          description: Received
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Receive GitHub webhook events (push, PR, issue) for live sync
  /webhooks/linkedin:
    post:
      tags:
      - Webhooks
      summary: LinkedIn engagement webhook
      responses:
        '202':
          description: Received
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '500':
          $ref: '#/components/responses/InternalServerError'
      description: Receive LinkedIn webhook events for cross-posting acknowledgments
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  responses:
    BadRequest:
      description: Bad Request — invalid syntax or parameters
      headers:
        X-Request-ID:
          schema:
            type: string
            example: req_a1b2c3d4
          description: Request trace ID
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Unauthorized:
      description: Unauthorized — missing or invalid token
      headers:
        X-Request-ID:
          schema:
            type: string
            example: req_a1b2c3d4
          description: Request trace ID
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Forbidden:
      description: Forbidden — insufficient permissions
      headers:
        X-Request-ID:
          schema:
            type: string
            example: req_a1b2c3d4
          description: Request trace ID
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    NotFound:
      description: Not Found — resource does not exist
      headers:
        X-Request-ID:
          schema:
            type: string
            example: req_a1b2c3d4
          description: Request trace ID
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Conflict:
      description: Conflict — resource already exists or version mismatch
      headers:
        X-Request-ID:
          schema:
            type: string
            example: req_a1b2c3d4
          description: Request trace ID
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    UnprocessableEntity:
      description: Unprocessable Entity — validation failed
      headers:
        X-Request-ID:
          schema:
            type: string
            example: req_a1b2c3d4
          description: Request trace ID
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationError'
    TooManyRequests:
      description: Too Many Requests — rate limit exceeded
      headers:
        X-RateLimit-Reset:
          schema:
            type: integer
          description: Unix timestamp when limit resets
        Retry-After:
          schema:
            type: integer
          description: Seconds to wait before retrying
        X-Request-ID:
          schema:
            type: string
          description: Request trace ID
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    InternalServerError:
      description: Internal Server Error
      headers:
        X-Request-ID:
          schema:
            type: string
            example: req_a1b2c3d4
          description: Request trace ID
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
  schemas:
    ErrorResponse:
      type: object
      required:
      - error
      properties:
        error:
          type: object
          required:
          - code
          - message
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  code:
                    type: string
                  message:
                    type: string
            trace_id:
              type: string
      description: Standard error response envelope for all API errors
      example:
        error:
          code: VALIDATION_ERROR
          message: Invalid request parameters
          details:
          - field: email
            code: INVALID_FORMAT
            message: Email format is invalid
          trace_id: req_a1b2c3d4
    ValidationError:
      type: object
      required:
      - error
      properties:
        error:
          type: object
          required:
          - code
          - message
          properties:
            code:
              type: string
              example: VALIDATION_ERROR
            message:
              type: string
            details:
              type: array
              items:
                type: object
                required:
                - field
                - code
                - message
                properties:
                  field:
                    type: string
                  code:
                    type: string
                  message:
                    type: string
            trace_id:
              type: string
      description: Validation error with per-field error details
      example:
        error:
          code: VALIDATION_ERROR
          message: Validation failed
          details:
          - field: email
            code: REQUIRED
            message: Email is required
          - field: password
            code: MIN_LENGTH
            message: Password must be at least 8 characters
          trace_id: req_x1y2z3

```
