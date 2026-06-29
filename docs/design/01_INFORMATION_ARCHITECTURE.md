# BrandOS — Information Architecture & Design Plan

> Based on: PRD, System Architecture, Low Level Design, UI Architecture  
> Created: 2026-06-29  
> Status: Design Draft

---

## 1. Site Map (Content Organization)

```
PUBLIC (no auth)
/                        → Marketing Landing Page
/login                   → Login (email + OAuth)
/register                → Registration

AUTHENTICATED (App Shell)
/(app)/dashboard         → Daily Workspace (content brief + quick actions)
/(app)/content           → Content Library (all generated posts)
  /content/new           → Create post (idea → draft)
  /content/[id]          → Post detail view
  /content/[id]/edit     → Draft editor (full-width, split pane)
/(app)/history/[id]      → Generated content detail (legacy)
/(app)/briefs            → Content briefs archive
  /briefs/[id]           → Brief detail
/(app)/knowledge         → Knowledge Library
  /knowledge/new         → Add knowledge item
  /knowledge/[id]        → Knowledge item detail
  /knowledge/tags        → Tag management
/(app)/analytics         → Analytics overview
  /analytics/content     → Content performance
  /analytics/audience    → Audience insights
/(app)/trends            → Trending topics discovery
/(app)/style             → Voice fingerprint & writing style
/(app)/connections       → Connected services
  /connections/github    → GitHub integration
  /connections/linkedin  → LinkedIn integration
/(app)/settings          → Settings hub
  /settings/profile      → Profile & expertise areas
  /settings/preferences  → Content preferences & cadence
  /settings/api-keys     → API key management

ONBOARDING (no App Shell, wizard layout)
/onboarding/welcome      → Welcome & value prop
/onboarding/profile      → Name, bio, expertise areas
/onboarding/github       → Connect GitHub
/onboarding/knowledge    → First knowledge items (optional)
/onboarding/style        → Voice preferences
/onboarding/complete     → Done + redirect to dashboard
```

---

## 2. Navigation Architecture

### 2.1 Primary Navigation (Sidebar)

| Section | Icon | Route | Badge |
|---------|------|-------|-------|
| Dashboard | LayoutDashboard | /dashboard | — |
| Content Briefs | Sparkles | /briefs | Unread count |
| Content | FileText | /content | Draft count |
| Knowledge | BookOpen | /knowledge | — |
| Analytics | BarChart3 | /analytics | — |
| Trends | TrendingUp | /trends | — |
| Style | Palette | /style | Convergence % |

### 2.2 Secondary Navigation (Sidebar bottom)

| Section | Icon | Route |
|---------|------|-------|
| Connections | Link | /connections |
| Settings | Settings | /settings |

### 2.3 Contextual Navigation

- **Content detail page**: Breadcrumb `Content > [title]`
- **Knowledge detail**: Breadcrumb `Knowledge > [title]`
- **Editor**: Full-width layout, no sidebar (separate `/(editor)` route group)
- **Settings**: Sidebar switches to settings-specific sub-nav

---

## 3. Key User Journeys

### 3.1 First-Time Onboarding (M4)

```
Landing → /register → /onboarding/welcome
  → /onboarding/profile (name, bio, expertise tags)
  → /onboarding/github (OAuth connect, repo selection)
  → /onboarding/knowledge (save first 3 items or skip)
  → /onboarding/style (tone: formal/casual, depth: tutorial/opinion/insight)
  → /onboarding/complete (redirect to /dashboard)
```

### 3.2 Daily Workspace (M2.5 — Dashboard)

```
User opens /dashboard
├── Top: Content Brief card (today's ideas from brief service)
│   └── Click idea → POST /content/draft → opens editor
├── Middle: Quick stats (posts this week, engagement rate, style convergence %)
├── Bottom-left: Recent content list (last 5 items with status)
└── Bottom-right: Trending topics panel (top 3 trending in user's domain)
```

### 3.3 Idea → Draft → Publish (Core Loop)

```
Dashboard brief card → Click "Generate Draft"
  → POST /content/draft → Loading state (streaming)
  → Draft editor opens (full-width):
    ├── Left pane: Markdown editor (CodeMirror)
    ├── Right pane: Live preview (themed)
    ├── Bottom: Rating bar (1-5 stars) + "Regenerate" + "Edit"
    └── Top right: "Schedule" dropdown + "Publish Now" button
  → Rate draft → PUT /content/draft/[id]/rate
  → Edit → PUT /content/draft/[id] (saves revision, triggers style learning)
  → Approve → POST /content/draft/[id]/schedule (or /publish)
  → Toast: "Scheduled for tomorrow 9:00 AM" / "Published to LinkedIn"
```

### 3.4 Style Learning Feedback Loop

```
User rates a draft (4/5) → POST /rate
  → System updates style profile EMA
  → Style meter in sidebar updates convergence %
  → Next draft reflects learned preferences
User edits a draft → PUT /content/draft/[id]
  → System diffs original vs edited
  → Lexical analyzer extracts vocabulary patterns
  → Style profile adjusts
```

---

## 4. App Shell Layout

```
┌────────────────────────────────────────────────────┐
│  Header (56px)                                     │
│  ┌──────┐ ┌─────────────┐ ┌────────────────────┐   │
│  │ ☰    │ │ BrandOS      │ │ 🔔 👤 🌙           │   │
│  └──────┘ └─────────────┘ └────────────────────┘   │
├────────┬───────────────────────────────────────────┤
│        │                                            │
│ Sidebar│  Main Content Area (padding: 32px)         │
│ 240px  │  ┌──────────────────────────────────────┐  │
│  (64px │  │  PageHeader                           │  │
│  coll.)│  │  Title + Description + Actions        │  │
│        │  └──────────────────────────────────────┘  │
│ 🏠 Dash│  ┌──────────────────────────────────────┐  │
│ ✨ Brief│  │  Content (Suspense boundaries)        │  │
│ 📄 Posts│  │                                       │  │
│ 📚 Know│  │                                       │  │
│ 📊 Analy│  │                                       │  │
│ 🔥 Trends│  └──────────────────────────────────────┘  │
│ 🎨 Style│                                            │
│        │                                            │
│ ───────│                                            │
│ 🔗 Conn│                                            │
│ ⚙️ Settings│                                         │
│        │                                            │
└────────┴───────────────────────────────────────────┘
```

---

## 5. Component Hierarchy

```
RootLayout (app/layout.tsx)
├── ThemeProvider
├── QueryProvider (TanStack)
├── Toaster (Sonner)
└── SessionProvider (NextAuth)

AppShell (app/(app)/layout.tsx) — 'use client'
├── Sidebar
│   ├── SidebarLogo
│   ├── SidebarNav (primary links)
│   ├── SidebarNav (secondary links)
│   └── StyleMeter (mini circular progress)
├── Sheet (mobile sidebar)
└── Header
    ├── SidebarToggle (mobile)
    ├── CommandPaletteTrigger (⌘K)
    ├── NotificationBell
    ├── ThemeToggle
    └── UserMenu (Avatar + Dropdown)

Page Shell (per page)
├── PageHeader (title + description + actions)
│   └── ActionButtons
├── Suspense fallback={<Skeleton />}
└── PageContent (actual data)

Dashboard (/dashboard)
├── PageHeader
├── BriefCard (today's content brief summary)
│   └── BriefIdeaList → BriefIdeaRow (click → generate draft)
├── MetricCardsGrid
│   └── MetricCard × 4 (posts/week, engagement, style %, ideas)
├── RecentContentList
│   └── ContentRow × 5 (title, status, date, platform)
└── TrendPanel
    └── TrendCard × 3

Content Library (/content)
├── PageHeader + "New Post" button
├── ContentToolbar (search, filter by status/platform, sort)
├── ContentTable (paginated)
│   └── ContentRow (title, status badge, platform, date, actions)
└── EmptyState (when no content)

Draft Editor (/(editor)/drafts/[id])
├── EditorSplitPane (resizable)
│   ├── MarkdownEditor (CodeMirror)
│   └── LivePreview (rendered markdown, theme-aware)
├── EditorToolbar (bold, italic, heading, link, code, list)
├── RatingBar (1-5 stars + quick actions)
├── ApprovalPanel (schedule / publish / save as draft)
└── RevisionHistory (drawer/bottom sheet)

Knowledge Library (/knowledge)
├── PageHeader + "Add Item" button
├── SearchInput + TagFilter
├── KbItemList (grid or list)
│   └── KbItemCard (title, excerpt, tags, source icon, date)
├── AddKnowledgeModal (url input / text note / file upload)
└── EmptyState

Analytics (/analytics)
├── PageHeader + DateRangePicker
├── AnalyticsSummaryRow (total posts, impressions, engagement, followers)
├── EngagementChart (Chart.js, dynamic import)
├── PlatformBreakdown (pie/donut chart)
├── GrowthChart (line chart, followers over time)
└── ContentPerformanceTable (top posts ranked by engagement)

Trends (/trends)
├── PageHeader + "Refresh" button
├── TrendCard × N (topic, relevance score, source, articles)
└── TrendDetail (expandable: related posts, angle suggestions)

Style (/style)
├── PageHeader
├── StyleMeter (large circular gauge, convergence %)
├── StyleParameterCards (tone, depth, length, hook type)
└── RecentRatings (history of ratings → style improvements)

Settings (/settings)
├── SettingsSidebar (profile, preferences, api keys)
├── ProfileForm (name, bio, avatar, expertise areas)
├── PreferencesForm (posting cadence, tone default, linkedin default)
├── ApiKeyManager (generate, revoke, list API keys)
└── DangerZone (delete account)

Onboarding Wizard (no AppShell)
├── Stepper (step 1-5 indicator)
├── OnboardingProfile → OnboardingGithub → OnboardingKnowledge → OnboardingStyle
└── Complete screen with confetti + redirect
```

---

## 6. State Management Plan

| Scope | Tool | Key Stores |
|-------|------|------------|
| Server data | TanStack Query | content, knowledge, briefs, analytics, trends, style |
| Server mutations | TanStack Query | create/update/delete content, rate draft, sync connections |
| UI state | Zustand | sidebar open, theme, active modal, command palette |
| Editor state | Zustand (scoped) | content, cursor, isDirty, revision history |
| Form state | React Hook Form | all forms (profile, settings, content, knowledge) |
| URL state | useSearchParams | pagination, filters, sort, active tab |
| Auth state | NextAuth | session, user, loading |

---

## 7. Implementation Order

### Phase 1 (M2.5): Foundation + Dashboard
- App Shell (layout, sidebar, header)
- Dashboard page (brief card, metrics, recent content, trends panel)
- TanStack Query provider setup
- Zustand stores (ui-store)
- Theme toggle (dark/light)
- shadcn/ui: Card, Button, Skeleton, Badge, Avatar, Separator, Sheet

### Phase 2 (M3): Style + Trends + Content Polish
- Style page with StyleMeter and parameter cards
- Trends page with trend cards and detail panel
- Content Library polish (table with real data, search, filter, sort)
- Content detail page refactor

### Phase 3 (M4): Onboarding + Settings + Publish
- Onboarding wizard (5-step with stepper)
- Settings pages (profile, preferences, API keys)
- Publish flow (schedule dialog, platform selection)
- Connections pages (GitHub, LinkedIn)

### Phase 4 (M5): Analytics + Polish
- Analytics dashboard (charts, summary, content table)
- Empty states for every page
- Loading skeletons for every route
- Error boundaries + fallbacks
- Lighthouse audit (LCP < 2.5s, CLS < 0.1)
- Accessibility pass (WCAG 2.2 AA)
