# API Specification: BrandOS (Firebase Callable Functions)

## Document Info

| Field | Value |
|-------|-------|
| **Author** | Architecture Team |
| **Status** | Draft |
| **Created** | 2026-07-14 |
| **Protocol** | Firebase Callable Functions (`https.onCall`) |
| **Auth** | Firebase ID Token (auto-verified by `onCall`) |

---

## Table of Contents

- [Protocol Overview](#1-protocol-overview)
- [Client Usage](#2-client-usage)
- [Profile API](#3-profile-api)
- [Knowledge Base API](#4-knowledge-base-api)
- [Content API](#5-content-api)
- [Publishing API](#6-publishing-api)
- [Analytics API](#7-analytics-api)
- [Briefs API](#8-briefs-api)
- [Connections API](#9-connections-api)
- [Admin API](#10-admin-api)
- [Error Codes](#11-error-codes)

---

## 1. Protocol Overview

### 1.1 Firebase Callable Functions

Unlike traditional REST APIs, Firebase Callable Functions use a **function-call** protocol:

- Functions are invoked by name via the Firebase client SDK
- Authentication is automatic — `context.auth` is populated by Firebase
- CORS, CSRF, and request/response serialization are handled by the SDK
- Input validation uses Zod schemas on the server side
- Responses are serialized JSON with automatic deserialization in the client SDK

### 1.2 Invocation Pattern

```typescript
// Client-side invocation
import { getFunctions, httpsCallable } from 'firebase/functions';

const functions = getFunctions();
const generateDraft = httpsCallable(functions, 'content-generateDraft');

const result = await generateDraft({
  idea: { title: '...', description: '...', category: 'tutorial' },
  tone: 'technical',
  length: 'medium',
});
// result.data → { success: true, data: { draftId, title, body, ... } }
```

### 1.3 Response Envelope

All functions return:

```typescript
interface FunctionResponse<T> {
  success: boolean;
  data?: T;          // Present on success
  error?: {
    code: string;    // Machine-readable error code
    message: string; // Human-readable message
    details?: unknown;
  };
}
```

### 1.4 Authentication

All functions (except auth callbacks) require an authenticated Firebase user. Cloud Functions `onCall` automatically verifies the Firebase ID token and populates `request.auth`. If a function is called without authentication, the SDK throws an `unauthenticated` error.

Functions access the authenticated user via:

```typescript
const uid = request.auth!.uid; // Non-null after auth verification
```

---

## 2. Client Usage

### 2.1 SDK Setup

```typescript
// lib/firebase.ts
import { initializeApp } from 'firebase/app';
import { getFunctions, connectFunctionsEmulator } from 'firebase/functions';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

const app = initializeApp(firebaseConfig);
const functions = getFunctions(app, 'us-central1');

if (process.env.NODE_ENV === 'development') {
  connectFunctionsEmulator(functions, 'localhost', 5001);
}

export { app, functions };
```

### 2.2 Typed Client Helpers

```typescript
// lib/api.ts
import { getFunctions, httpsCallable } from 'firebase/functions';
import { functions } from './firebase';

function createCallable<TInput, TOutput>(name: string) {
  const fn = httpsCallable<TInput, { success: boolean; data: TOutput }>(functions, name);
  return async (input: TInput): Promise<TOutput> => {
    const result = await fn(input);
    if (!result.data.success) {
      throw new Error(`API error from ${name}`);
    }
    return result.data.data;
  };
}

// Typed API client
export const api = {
  // Profile
  getMyProfile: createCallable<{}, ProfileResponse>('profile-getMyProfile'),
  updateMyProfile: createCallable<UpdateProfileInput, {}>('profile-updateMyProfile'),

  // Knowledge Base
  createKnowledgeItem: createCallable<CreateKnowledgeInput, { id: string }>('knowledge-createKnowledgeItem'),
  searchKnowledge: createCallable<SearchKnowledgeInput, { items: KnowledgeItem[] }>('knowledge-searchKnowledge'),

  // Content
  generateIdeas: createCallable<GenerateIdeasInput, { ideas: Idea[] }>('content-generateIdeas'),
  generateDraft: createCallable<GenerateDraftInput, DraftResponse>('content-generateDraft'),
  rateDraft: createCallable<RateDraftInput, {}>('content-rateDraft'),
  schedulePost: createCallable<SchedulePostInput, {}>('content-schedulePost'),

  // Briefs
  getTodayBrief: createCallable<{}, BriefResponse>('briefs-getTodayBrief'),

  // Connections
  connectLinkedIn: createCallable<ConnectLinkedInInput, {}>('connections-connectLinkedIn'),
  getConnectionStatus: createCallable<{}, ConnectionStatusResponse>('connections-getConnectionStatus'),

  // Analytics
  getAnalyticsOverview: createCallable<{}, AnalyticsOverview>('analytics-getAnalyticsOverview'),
};
```

---

## 3. Profile API

### 3.1 `profile-getMyProfile`

Returns the authenticated user's profile.

| Field | Type |
|-------|------|
| **Input** | `{}` |
| **Output** | `ProfileResponse` |

```typescript
interface ProfileResponse {
  id: string;
  email: string;
  displayName: string;
  photoURL?: string;
  bio?: string;
  expertiseAreas: ExpertiseArea[];
  preferences: UserPreferences;
  stats: UserStats;
  createdAt: string;   // ISO 8601
}

interface ExpertiseArea {
  name: string;
  category: string;
  priority: number;
  keywords: string[];
}

interface UserPreferences {
  postingCadence: 'daily' | '3x_week' | 'weekly' | 'custom';
  timezone: string;
  briefHour: number;
  defaultTone: ContentTone;
  defaultLength: ContentLength;
  digestEnabled: boolean;
}

interface UserStats {
  totalDrafts: number;
  totalPublished: number;
  totalKnowledgeItems: number;
  memberSince: string;
}
```

### 3.2 `profile-updateMyProfile`

Updates profile fields. Uses Firestore merge, so only provided fields are changed.

| Field | Type | Required |
|-------|------|----------|
| `displayName` | `string (1-100)` | No |
| `bio` | `string (max 1000)` | No |
| `photoURL` | `string (URL)` | No |
| `expertiseAreas` | `ExpertiseArea[] (max 10)` | No |

Output: `{}`

### 3.3 `profile-updateMyPreferences`

Updates user preferences.

| Field | Type | Required |
|-------|------|----------|
| `postingCadence` | `'daily' \| '3x_week' \| 'weekly' \| 'custom'` | No |
| `timezone` | `string` | No |
| `briefHour` | `number (0-23)` | No |
| `defaultTone` | `ContentTone` | No |
| `defaultLength` | `ContentLength` | No |
| `digestEnabled` | `boolean` | No |

Output: `{}`

---

## 4. Knowledge Base API

### 4.1 `knowledge-createKnowledgeItem`

Creates a new knowledge item. Triggers automatic embedding generation via Firestore trigger.

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `url` | `string (URL)` | No | — |
| `title` | `string (1-500)` | Yes | — |
| `note` | `string (max 5000)` | No | — |
| `tags` | `string[] (max 20)` | No | `[]` |
| `sourceType` | `'link' \| 'note' \| 'paper' \| 'code' \| 'video' \| 'podcast'` | No | `'link'` |

```typescript
// Output
interface CreateKnowledgeResponse {
  id: string;  // Firestore document ID
}
```

### 4.2 `knowledge-searchKnowledge`

Hybrid search across the user's knowledge base.

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `query` | `string (1-200)` | Yes | — |
| `limit` | `number (1-50)` | No | 10 |
| `cursor` | `string` | No | — |
| `tags` | `string[] (max 20)` | No | — |
| `sourceTypes` | `SourceType[]` | No | — |

```typescript
interface SearchResponse {
  items: KnowledgeItem[];
  nextCursor?: string;
  hasMore: boolean;
}

interface KnowledgeItem {
  id: string;
  title: string;
  url?: string;
  note?: string;
  summary?: string;
  tags: string[];
  sourceType: string;
  createdAt: string;
}
```

### 4.3 `knowledge-getKnowledgeItem`

Gets a single knowledge item by ID.

| Field | Type |
|-------|------|
| `itemId` | `string` |

Output: `KnowledgeItem`

### 4.4 `knowledge-updateKnowledgeItem`

Updates a knowledge item.

| Field | Type | Required |
|-------|------|----------|
| `itemId` | `string` | Yes |
| `title` | `string` | No |
| `note` | `string` | No |
| `tags` | `string[]` | No |

Output: `{}`

### 4.5 `knowledge-deleteKnowledgeItem`

Deletes a knowledge item and its embedding.

| Field | Type |
|-------|------|
| `itemId` | `string` |

Output: `{}`

---

## 5. Content API

### 5.1 `content-generateIdeas`

Generates ranked content ideas from user context.

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `briefId` | `string` | No | — |
| `count` | `number (1-10)` | No | 5 |
| `tone` | `ContentTone` | No | User default |
| `length` | `ContentLength` | No | User default |
| `categories` | `ContentType[]` | No | All |

```typescript
interface GenerateIdeasOutput {
  ideas: Idea[];
}

interface Idea {
  title: string;
  description: string;
  category: ContentType;
  relevanceScore: number;  // 0-1
  noveltyScore: number;    // 0-1
  contextSources: string[];
}
```

### 5.2 `content-generateDraft`

Generates a full draft from an idea. Runs the 5-stage pipeline.

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `idea.title` | `string (1-200)` | Yes | — |
| `idea.description` | `string (1-2000)` | Yes | — |
| `idea.category` | `ContentType` | Yes | — |
| `idea.contextSources` | `string[]` | No | — |
| `tone` | `ContentTone` | No | User default |
| `length` | `ContentLength` | No | User default |

```typescript
interface DraftResponse {
  draftId: string;
  title: string;
  body: string;
  qualityScore: number;
  qualityVerdict: 'pass' | 'warn' | 'fail';
  readabilityScore: number;
  wordCount: number;
  metadata: {
    modelsUsed: string[];
    stageTimings: Record<string, number>;
  };
}
```

### 5.3 `content-updateDraft`

Updates a draft with user edits. If this is the first edit, triggers style analysis.

| Field | Type |
|-------|------|
| `draftId` | `string` |
| `body` | `string (1-10000)` |

Output: `{}`

### 5.4 `content-regenerateDraft`

Regenerates a draft with additional feedback.

| Field | Type |
|-------|------|
| `draftId` | `string` |
| `feedback` | `string (max 1000)` |
| `tone` | `ContentTone (optional)` |
| `length` | `ContentLength (optional)` |

Output: `DraftResponse`

### 5.5 `content-rateDraft`

Records a user rating and updates the style profile.

| Field | Type | Required |
|-------|------|----------|
| `draftId` | `string` | Yes |
| `score` | `number (1-5)` | Yes |
| `dimensions.accuracy` | `number (1-5)` | No |
| `dimensions.readability` | `number (1-5)` | No |
| `dimensions.authenticity` | `number (1-5)` | No |
| `dimensions.engagement` | `number (1-5)` | No |
| `comment` | `string (max 1000)` | No |

Output: `{}`

### 5.6 `content-schedulePost`

Schedules a draft for publishing on a platform.

| Field | Type |
|-------|------|
| `draftId` | `string` |
| `platform` | `'linkedin'` |
| `scheduledFor` | `string (ISO 8601)` |

Output: `{}`

### 5.7 `content-getDraftHistory`

Returns the user's draft history (paginated).

| Field | Type | Default |
|-------|------|---------|
| `limit` | `number (1-50)` | 10 |
| `cursor` | `string` | — |
| `status` | `PostStatus` | — |

```typescript
interface DraftHistoryResponse {
  drafts: DraftSummary[];
  nextCursor?: string;
  hasMore: boolean;
}

interface DraftSummary {
  id: string;
  title: string;
  status: PostStatus;
  contentType: ContentType;
  qualityScore?: number;
  createdAt: string;
  updatedAt: string;
}
```

---

## 6. Publishing API

### 6.1 `publish-publishNow`

Publishes a draft immediately (bypasses schedule queue).

| Field | Type |
|-------|------|
| `draftId` | `string` |
| `platform` | `'linkedin'` |

Output:

```typescript
interface PublishResponse {
  externalPostId: string;
  postUrl: string;
  publishedAt: string;
}
```

### 6.2 `publish-getSchedule`

Returns the user's publishing schedule.

| Field | Type | Default |
|-------|------|---------|
| `limit` | `number` | 20 |
| `status` | `'pending' \| 'published' \| 'failed'` | — |

```typescript
interface ScheduleResponse {
  items: ScheduledItem[];
}

interface ScheduledItem {
  id: string;
  draftId: string;
  draftTitle: string;
  platform: string;
  scheduledFor: string;
  status: 'pending' | 'published' | 'failed';
  externalPostUrl?: string;
}
```

### 6.3 `publish-deleteSchedule`

Cancels a scheduled post.

| Field | Type |
|-------|------|
| `scheduleId` | `string` |

Output: `{}`

### 6.4 `publish-getPublishHistory`

Returns publishing history.

| Field | Type | Default |
|-------|------|---------|
| `limit` | `number` | 20 |
| `cursor` | `string` | — |

---

## 7. Analytics API

### 7.1 `analytics-getAnalyticsOverview`

Returns aggregated analytics snapshot.

| Field | Type |
|-------|------|
| **Input** | `{}` |

```typescript
interface AnalyticsOverview {
  summary: {
    totalPosts: number;
    totalImpressions: number;
    totalEngagements: number;
    followerCount: number;
    followerGrowth: number;       // % change (30 days)
    avgEngagementRate: number;     // %
  };
  recentPosts: PostMetric[];
  topPosts: PostMetric[];
  engagementByDay: DayMetric[];
}

interface PostMetric {
  id: string;
  title: string;
  impressions: number;
  engagements: number;
  engagementRate: number;
  publishedAt: string;
}

interface DayMetric {
  date: string;
  impressions: number;
  engagements: number;
  followerDelta: number;
}
```

### 7.2 `analytics-getPostMetrics`

Returns metrics for a specific published post.

| Field | Type |
|-------|------|
| `postId` | `string` |

Output: `PostMetric`

### 7.3 `analytics-getAudienceInsights`

Returns audience demographics and growth data.

Output:

```typescript
interface AudienceInsights {
  followerGrowth: Array<{ date: string; count: number }>;
  topLocations: Array<{ region: string; percentage: number }>;
  topIndustries: Array<{ industry: string; percentage: number }>;
  engagementByDayOfWeek: Array<{ day: string; rate: number }>;
}
```

---

## 8. Briefs API

### 8.1 `briefs-getTodayBrief`

Returns today's content brief (or generates one on the fly if none exists).

| Field | Type |
|-------|------|
| **Input** | `{}` |

```typescript
interface BriefResponse {
  id: string;
  date: string;
  ideas: BriefIdea[];
  contextSummary: {
    recentCommits: number;
    recentKnowledge: number;
    trendingTopics: string[];
  };
  generatedAt: string;
}

interface BriefIdea {
  title: string;
  description: string;
  category: ContentType;
  relevanceScore: number;
  noveltyScore: number;
}
```

### 8.2 `briefs-listBriefs`

Returns recent brief history.

| Field | Type | Default |
|-------|------|---------|
| `limit` | `number` | 7 |

---

## 9. Connections API

### 9.1 `connections-connectLinkedIn`

Completes LinkedIn OAuth flow and stores tokens.

| Field | Type |
|-------|------|
| `code` | `string` — OAuth authorization code from LinkedIn |
| `redirectUri` | `string` — Must match the redirect URI registered in LinkedIn app |

Output: `{ status: 'connected' }`

### 9.2 `connections-connectGitHub`

Completes GitHub OAuth flow.

| Field | Type |
|-------|------|
| `code` | `string` — OAuth authorization code from GitHub |

Output: `{ status: 'connected' }`

### 9.3 `connections-getConnectionStatus`

Returns status of all platform connections.

Output:

```typescript
interface ConnectionStatusResponse {
  connections: Array<{
    platform: 'linkedin' | 'github';
    status: 'connected' | 'expired' | 'needs_reconnect';
    connectedAt?: string;
    lastSyncAt?: string;
  }>;
}
```

### 9.4 `connections-disconnect`

Disconnects a platform.

| Field | Type |
|-------|------|
| `platform` | `'linkedin' \| 'github'` |

Output: `{}`

---

## 10. Admin API

### 10.1 `admin-getSystemStats`

Returns system-wide statistics. Requires `admin` custom claim.

| Field | Type |
|-------|------|
| **Input** | `{}` |

```typescript
interface SystemStats {
  totalUsers: number;
  activeUsers30d: number;
  totalDrafts: number;
  totalPublished: number;
  groqRequestsToday: number;
  groqRequestsLimit: number;
  functionInvocations30d: number;
}
```

### 10.2 `admin-forceSync`

Triggers an immediate sync for a user.

| Field | Type |
|-------|------|
| `userId` | `string` |
| `source` | `'github' \| 'linkedin'` |

Output: `{}`

---

## 11. Error Codes

| Code | HTTP Equivalent | Meaning |
|------|----------------|---------|
| `VALIDATION_ERROR` | 400 | Input failed Zod validation. `details` contains field-level errors. |
| `UNAUTHENTICATED` | 401 | No valid Firebase ID token. SDK throws this automatically. |
| `UNAUTHORIZED` | 403 | Authenticated but lacks required permissions. |
| `NOT_FOUND` | 404 | Requested resource does not exist. |
| `CONFLICT` | 409 | Resource already exists or state conflict. |
| `RATE_LIMITED` | 429 | Too many requests. `details.retryAfter` has the wait duration. |
| `AI_PROVIDER_ERROR` | 502 | Groq or Mistral API returned an error. |
| `PLATFORM_ERROR` | 502 | LinkedIn or GitHub API returned an error. |
| `TOKEN_EXPIRED` | 401 | Platform OAuth token expired and refresh failed. User must reconnect. |
| `QUOTA_EXCEEDED` | 429 | Daily generation quota reached (configurable per user). |
| `INTERNAL_ERROR` | 500 | Unexpected error. Details are logged server-side, returned as generic message. |

---

## Appendix: Function Index

| Function Name | Group | Auth | Latency Target | Invocation Pattern |
|--------------|-------|------|---------------|-------------------|
| `profile-getMyProfile` | Profile | Required | < 200ms | User opens dashboard |
| `profile-updateMyProfile` | Profile | Required | < 500ms | User edits profile |
| `profile-updateMyPreferences` | Profile | Required | < 500ms | User changes settings |
| `knowledge-createKnowledgeItem` | Knowledge | Required | < 500ms | User saves link/note |
| `knowledge-searchKnowledge` | Knowledge | Required | < 1s | User searches KB |
| `knowledge-getKnowledgeItem` | Knowledge | Required | < 200ms | User opens item |
| `knowledge-updateKnowledgeItem` | Knowledge | Required | < 500ms | User edits item |
| `knowledge-deleteKnowledgeItem` | Knowledge | Required | < 500ms | User deletes item |
| `content-generateIdeas` | Content | Required | < 5s | User opens brief |
| `content-generateDraft` | Content | Required | < 15s | User clicks "Generate" |
| `content-updateDraft` | Content | Required | < 500ms | User edits draft |
| `content-regenerateDraft` | Content | Required | < 15s | User clicks "Regenerate" |
| `content-rateDraft` | Content | Required | < 500ms | User rates draft |
| `content-schedulePost` | Content | Required | < 500ms | User schedules post |
| `content-getDraftHistory` | Content | Required | < 500ms | User views history |
| `publish-publishNow` | Publish | Required | < 3s | User publishes immediately |
| `publish-getSchedule` | Publish | Required | < 500ms | User views schedule |
| `publish-deleteSchedule` | Publish | Required | < 500ms | User cancels post |
| `publish-getPublishHistory` | Publish | Required | < 500ms | User views history |
| `analytics-getAnalyticsOverview` | Analytics | Required | < 1s | User opens analytics |
| `analytics-getPostMetrics` | Analytics | Required | < 500ms | User clicks post |
| `analytics-getAudienceInsights` | Analytics | Required | < 2s | User views audience |
| `briefs-getTodayBrief` | Briefs | Required | < 3s | User opens dashboard |
| `briefs-listBriefs` | Briefs | Required | < 500ms | User views history |
| `connections-connectLinkedIn` | Connections | Required | < 2s | OAuth callback |
| `connections-connectGitHub` | Connections | Required | < 2s | OAuth callback |
| `connections-getConnectionStatus` | Connections | Required | < 200ms | User views settings |
| `connections-disconnect` | Connections | Required | < 500ms | User disconnects |
| `admin-getSystemStats` | Admin | Admin role | < 500ms | Admin dashboard |
| `admin-forceSync` | Admin | Admin role | < 10s | Admin action |

---

*This specification covers all Cloud Functions for the BrandOS MVP. Each function corresponds to a single Firestore operation or a multi-step pipeline orchestration. See 05_DATABASE.md for the complete Firestore schema.*
