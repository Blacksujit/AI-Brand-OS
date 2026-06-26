# Agent Design — BrandOS

> **Phase**: Architecture — Agent Specification  
> **Status**: Complete  
> **Last Updated**: 2026-06-26

---

## Table of Contents

1. [Agent Architecture Overview](#1-agent-architecture-overview)
2. [Research Agent](#2-research-agent)
3. [Knowledge Agent](#3-knowledge-agent)
4. [Memory Agent](#4-memory-agent)
5. [Topic Selector](#5-topic-selector)
6. [Strategy Agent](#6-strategy-agent)
7. [Hook Generator](#7-hook-generator)
8. [Writing Agent](#8-writing-agent)
9. [Review Agent](#9-review-agent)
10. [Analytics Agent](#10-analytics-agent)
11. [Agent Orchestration](#11-agent-orchestration)
12. [Prompt Contract Registry](#12-prompt-contract-registry)

---

## 1. Agent Architecture Overview

### 1.1 Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Deterministic orchestration, stochastic execution** | The pipeline order is fixed; individual agents use LLMs for generation but with structured schemas |
| **Single responsibility per agent** | Each agent owns one cognitive task. No agent spans multiple responsibilities |
| **Typed contracts between agents** | All agent inputs/outputs are Pydantic models. No raw text passing between agents |
| **Prompt isolation** | Every prompt lives in `backend/prompts/{agent_name}.md`. Agents reference prompts by name, never embed them |
| **Human-in-the-loop** | Review Agent can surface warnings; Writing Agent never publishes without approval |
| **Observable by default** | Every agent emits metrics: latency, token count, success/failure, retry count |

### 1.2 Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Daily Pipeline (cron)                          │
│                                                                     │
│  Research ──► Knowledge ──► Memory ──► Topic ──► Strategy ──►      │
│  Agent        Agent         Agent       Selector    Agent           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │            Generation Pipeline (on-demand)                │       │
│  │                                                          │       │
│  │  Topic ──► Strategy ──► Hook ──► Writing ──► Review     │       │
│  │  Selector  Agent        Generator  Agent      Agent      │       │
│  │                                                          │       │
│  │  ▲────────────────── regenerate ──────────────────────▲ │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │            Analytics Pipeline (periodic)                   │       │
│  │                                                          │       │
│  │  Platform ──► Analytics Agent ──► Memory Agent           │       │
│  │  (published   (performance        (store insights)       │       │
│  │   posts)      analysis)                                  │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Agent Communication Pattern

All agents communicate through a shared `AgentContext` object that flows through the pipeline:

```python
class AgentContext(BaseModel):
    user_id: uuid.UUID
    session_id: uuid.UUID
    pipeline_id: str                    # Unique run identifier
    pipeline_type: Literal["daily_brief", "draft_generation", "analytics"]
    created_at: datetime
    previous_outputs: dict[str, Any]    # Keyed by agent name
    accumulated_metrics: dict[str, AgentMetrics]
    abort_requested: bool               # Circuit breaker flag
```

Each agent reads from `context.previous_outputs` and writes to `context.previous_outputs[agent_name]`.

### 1.4 Agent Base Interface

```python
class BaseAgent(ABC):
    agent_name: str                     # Unique identifier
    prompt_path: str                    # Path to prompt file

    @abstractmethod
    async def execute(
        self, context: AgentContext
    ) -> AgentResult: ...

    @abstractmethod
    async def validate_input(
        self, context: AgentContext
    ) -> bool: ...

    @abstractmethod
    async def validate_output(
        self, result: AgentResult
    ) -> bool: ...

class AgentResult(BaseModel):
    success: bool
    agent_name: str
    output: dict[str, Any]
    metrics: AgentMetrics
    error: str | None

class AgentMetrics(BaseModel):
    latency_ms: int
    tokens_used: int
    retry_count: int
    llm_calls: int
```

---

## 2. Research Agent

The Research Agent discovers trending topics, relevant discussions, and emerging signals from external sources. It feeds raw material into the Knowledge and Memory agents.

### 2.1 Responsibilities

- Poll external sources (Hacker News, Dev.to, GitHub Trending, RSS feeds, arXiv)
- Deduplicate topics across sources
- Score each topic for freshness, relevance, and authority
- Surface topics that intersect with user expertise areas
- Cache results to avoid redundant scraping

### 2.2 Inputs

```python
class ResearchAgentInput(BaseModel):
    user_id: uuid.UUID
    expertise_areas: list[ExpertiseArea]
    kb_topics: list[str]               # Top tags from knowledge base
    recent_github_activity: GitHubActivity | None
    sources: list[str]                 # Enabled trend sources
    max_topics: int = 15
    lookback_hours: int = 24
    minimum_relevance_score: float = 0.3
```

### 2.3 Outputs

```python
class ResearchAgentOutput(BaseModel):
    topics: list[DiscoveredTopic]
    source_summary: SourceSummary
    dominant_theme: str | None         # Emerging theme across multiple topics

class DiscoveredTopic(BaseModel):
    id: str
    title: str
    description: str
    source: str
    url: str | None
    relevance_score: float             # 0.0 - 1.0
    freshness_score: float             # 0.0 - 1.0
    engagement_count: int
    related_keywords: list[str]
    matched_expertise: list[str]       # Which expertise areas this maps to
    matched_kb_tags: list[str]         # Which KB tags overlap
    suggested_category: ContentCategory

class SourceSummary(BaseModel):
    sources_queried: int
    topics_collected: int
    topics_after_dedup: int
    topics_after_scoring: int
    top_source: str                    # Source with highest avg relevance
```

### 2.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| TrendService | Internal service | Source clients, cached results, deduplication |
| ProfileService | Internal service | Expertise areas for relevance scoring |
| CacheService | Internal service | Trend cache (5min TTL for hot topics, 1hr for scored) |
| LLMClient | LLM | Relevance scoring and topic summarization |

### 2.5 Memory

| Memory Type | Read | Write | TTL |
|------------|------|-------|-----|
| Long-term | User expertise areas | — | Permanent |
| Working | Recent KB tags | Discovered topics (scored) | 6 hours |
| Short-term | — | Raw scrape results | 5 minutes |

### 2.6 Prompt

**Prompt file**: `backend/prompts/research_agent.md`

**System prompt responsibilities**:
- Classify discovered topics into content categories
- Generate concise topic descriptions
- Score relevance against given expertise areas
- Identify emerging themes across multiple topics

**Prompt structure**:
```
SYSTEM:
You are the Research Agent for BrandOS. Your task is to analyze trending topics
and score them for relevance to the user's expertise areas.

USER:
{scraped_topics_json}
{expertise_areas_json}
{kb_topics_json}
TASK: For each topic, determine:
1. Relevance score (0.0-1.0) based on expertise overlap
2. Suggested content category
3. Brief rationale for relevance
```

### 2.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| Source API rate limit | Empty topic list | None (returns cached) | 429 status code |
| Source unavailable | Partial results | Degraded diversity | Timeout > 10s |
| Irrelevant scoring | Low relevance scores | Fewer topic suggestions | Score variance < 0.2 |
| Dedup failure | Duplicate topics | Wasteful downstream | Topic title similarity > 0.9 |

### 2.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | Any source fails | Skip source, continue with remaining |
| 2 | >50% sources fail | Retry all failed sources after 5s |
| 3 | Still >50% fail | Return cached results, log alert |

### 2.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| Source coverage | ≥ 3 sources per run | Count sources queried |
| Dedup accuracy | 0 false positives per 100 topics | Manual audit of deduped pairs |
| Relevance precision | ≥ 80% of topics relevant to user | User feedback on brief ideas |
| Pipeline latency | < 30s total (scrape + score) | Timer from input to output |
| Cache hit rate | > 70% for trend data | Cache stats |

---

## 3. Knowledge Agent

The Knowledge Agent manages the user's curated knowledge repository — ingesting, processing, and retrieving information from saved links, notes, PDFs, and imported content.

### 3.1 Responsibilities

- Process incoming URLs, PDFs, and notes through extraction → summarization → embedding → classification
- Maintain hybrid search index (SQLite FTS5 + ChromaDB vector)
- Build context bundles for the content pipeline
- Suggest tags for new items based on content analysis
- Deduplicate incoming items against existing entries

### 3.2 Inputs

```python
class KnowledgeAgentInput(BaseModel):
    user_id: uuid.UUID
    action: Literal["ingest", "search", "build_context", "suggest_tags"]
    # For ingest
    items: list[AddKnowledgeItemRequest] | None = None
    # For search
    query: SearchQuery | None = None
    # For context building
    context_purpose: Literal["daily_brief", "draft_generation", "trend_scoring"]
    context_limit: int = 20
    topic: str | None = None           # Focus topic for context
```

### 3.3 Outputs

```python
class KnowledgeAgentOutput(BaseModel):
    action: str
    # For ingest
    processed_items: list[ProcessingResult]
    dedup_skipped: int
    # For search
    search_results: list[SearchResult] | None = None
    # For context building
    context: KnowledgeContext | None = None
    suggested_tags: list[str] | None = None

class ProcessingResult(BaseModel):
    item_id: uuid.UUID
    title: str
    summary: str
    tags: list[str]
    reading_time_minutes: int
    vector_dimension: int
    processing_duration_ms: int
    dedup_was_skipped: bool
```

### 3.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| KnowledgeBaseService | Internal service | CRUD, embedding, search |
| LLMClient | LLM | Summarization, tag suggestion, classification |
| EmbeddingService | Embedding | Vector generation for ChromaDB |
| StorageService | Object storage | PDF/attachment processing |

### 3.5 Memory

| Memory Type | Read | Write | TTL |
|------------|------|-------|-----|
| Long-term | Knowledge items, tags, embeddings | New items, tags, embeddings | Permanent |
| Working | Recent context bundles | Current context summary | Session |
| Episodic | — | Processing logs | 90 days |

### 3.6 Prompt

**Prompt file**: `backend/prompts/knowledge_agent.md`

**System prompt responsibilities**:
- Generate concise, accurate summaries from extracted text
- Classify content into categories (article, paper, tutorial, idea, reference)
- Suggest 3-5 relevant tags based on content analysis
- Determine technical level (beginner/intermediate/advanced)
- Extract key insights (3-5 bullet points)

**Prompt structure**:
```
SYSTEM:
You are the Knowledge Agent for BrandOS. Your task is to process incoming
content and extract structured knowledge from it.

USER:
{extracted_text}
{url}
TASK: Generate:
1. A 2-3 sentence summary
2. Content category: article | paper | tutorial | idea | reference | other
3. 3-5 relevant tags
4. 3-5 key insight bullet points
5. Technical level: beginner | intermediate | advanced
6. Estimated reading time in minutes
```

### 3.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| URL unreachable | Extraction returns empty | Item not ingested | HTTP status != 200 |
| Text too long | Token limit exceeded | Truncated summary | Input length > model context |
| Embedding failure | Vector write fails | Item ingested without embedding | ChromaDB write error |
| Low quality summary | Summary contains hallucination | Misleading context | Factual accuracy < 0.7 |

### 3.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | Extraction fails | Retry with different extractor |
| 2 | LLM summarization fails | Retry with shorter input (truncate to 4K tokens) |
| 3 | Both fail | Return item with minimal metadata, flag for reprocessing |

### 3.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| Summary accuracy | ≥ 90% factual precision | Manual audit of 50 summaries |
| Tag relevance | ≥ 85% of tags are appropriate | User tag edit rate |
| Ingest latency (URL) | < 15s p95 | Timer from submit to index |
| Ingest latency (note) | < 5s p95 | Timer from submit to index |
| Search recall@10 | ≥ 0.8 | Judged relevance of top 10 results |
| Dedup accuracy | 0 false positives | Manual check of skip reason |

---

## 4. Memory Agent

The Memory Agent manages the lifecycle of all memory stores — deciding what to keep, what to evict, what to promote between memory tiers, and how to organize episodic data for future retrieval.

### 4.1 Responsibilities

- **Short-term memory**: Manage Redis TTLs, evict stale entries under LRU
- **Working memory**: Promote important context from short-term to working tier, demote stale working data
- **Long-term memory**: Commit style signals, knowledge items, content history
- **Episodic memory**: Archive draft revisions and generation artifacts to S3 after 90 days
- **Strategic memory**: Maintain user preferences, content categories, posting cadence
- **Memory consolidation**: Periodically compress and summarize episodic data into strategic insights
- **Cache warming**: Pre-load common queries into Redis before expected usage

### 4.2 Inputs

```python
class MemoryAgentInput(BaseModel):
    user_id: uuid.UUID
    action: Literal[
        "store", "retrieve", "consolidate",
        "evict", "promote", "warm_cache"
    ]
    # For store
    memory_type: MemoryType | None = None
    key: str | None = None
    value: bytes | None = None
    ttl: int | None = None
    importance: float | None = None    # 0.0 - 1.0 for promotion decisions
    # For retrieve
    query: str | None = None
    memory_types: list[MemoryType] | None = None
    # For consolidation
    consolidation_target: Literal["episodic", "working"] | None = None

class MemoryType(str, Enum):
    SHORT_TERM = "short_term"          # Redis, TTL hours
    WORKING = "working"                # Redis + SQLite, TTL days
    LONG_TERM = "long_term"            # SQLite + ChromaDB, permanent
    EPISODIC = "episodic"              # SQLite + S3, 90 days
    STRATEGIC = "strategic"            # SQLite, permanent
```

### 4.3 Outputs

```python
class MemoryAgentOutput(BaseModel):
    action: str
    success: bool
    # For store
    stored_key: str | None = None
    ttl_set: int | None = None
    promoted_to: MemoryType | None = None
    # For retrieve
    value: bytes | None = None
    source_memory: MemoryType | None = None
    # For consolidate
    items_archived: int = 0
    items_evicted: int = 0
    items_promoted: int = 0
    summary: str | None = None
    # For cache warm
    cache_keys_warmed: int = 0

class MemoryConsolidationReport(BaseModel):
    short_term_count: int
    working_count: int
    long_term_count: int
    episodic_count: int
    strategic_count: int
    stale_promoted: int
    stale_evicted: int
    archived_to_s3: int
    compression_ratio: float
```

### 4.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| CacheService | Redis | Short-term and working memory storage |
| Database (SQLite) | Database | Long-term, strategic, episodic metadata |
| ChromaDB | Vector store | Long-term embedding vectors |
| StorageService | Object storage | Episodic blob archival |
| LLMClient | LLM | Memory consolidation summaries |

### 4.5 Memory

The Memory Agent **is** the memory system. It manages all five stores but does not have its own separate memory — its configuration (TTL policies, eviction rules, promotion thresholds) lives in code configuration, not in a store.

| Policy | Short-Term | Working | Long-Term | Episodic | Strategic |
|--------|-----------|---------|-----------|----------|-----------|
| Eviction | LRU when full | TTL expiry | Never (explicit delete) | TTL 90 days | Never |
| Max size | 100 items/user | 1000 items/user | Unlimited | Unlimited | 100 items/user |
| TTL | 1 hour | 24 hours | Permanent | 90 days | Permanent |
| Promotion | → Working if accessed 3+ times | → Long-term if importance > 0.8 | N/A | → Strategic if patterns detected | N/A |
| Storage | Redis | Redis + SQLite | SQLite + ChromaDB | SQLite + S3 | SQLite |

### 4.6 Prompt

**Prompt file**: `backend/prompts/memory_agent.md`

Used only for the consolidation task — extracting patterns from episodic memory:

```
SYSTEM:
You are the Memory Agent for BrandOS. Your task is to analyze episodic memory
records and extract patterns that should be promoted to strategic memory.

USER:
{episodic_records_json}
{current_strategic_memory_json}
TASK: Analyze the episodic records and identify:
1. Recurring patterns (content categories, posting times, engagement)
2. Anomalies that deviate from established patterns
3. Insights that should be persisted in strategic memory
```

### 4.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| Redis unavailable | Short/working memory lost | Degraded until cache repopulates | Connection error |
| ChromaDB write fails | Vector not persisted | Search quality degraded | Write error log |
| S3 archival fails | Episodic data stays in SQLite | SQLite table grows | Upload error |
| Consolidation LLM fails | Patterns not extracted | No strategic insight update | LLM error |

### 4.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | Redis SET fails | Try alternate Redis endpoint |
| 2 | ChromaDB write fails | Queue for async retry, continue |
| 3 | S3 upload fails | Store locally, retry on next consolidation cycle |

### 4.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| Short-term hit rate | ≥ 90% | Redis cache hit/miss stats |
| Working memory hit rate | ≥ 85% | Cache hit/miss stats |
| Episodic archival rate | 100% of items > 90 days | Count archived vs total |
| Consolidation latency | < 10s per run | Pipeline timing |
| Promotion accuracy | ≥ 80% of promoted items are used | Track promoted item access rate |

---

## 5. Topic Selector

The Topic Selector decides what to write about. It takes all available signals (trending topics, knowledge base highlights, recent GitHub activity, user expertise) and produces ranked content ideas.

### 5.1 Responsibilities

- Fuse signals from Research Agent, Knowledge Agent, and GitHub activity into weighted suggestions
- Generate novel content ideas that span the user's expertise areas
- Score ideas for relevance, novelty, and engagement potential
- Ensure category diversity (not all tutorials, no two similar ideas)
- Check against recent posts to avoid repetition
- Return 3-5 ranked ideas per brief

### 5.2 Inputs

```python
class TopicSelectorInput(BaseModel):
    user_id: uuid.UUID
    research_topics: list[DiscoveredTopic]
    knowledge_context: KnowledgeContext
    github_activity: GitHubActivity | None
    user_expertise: list[ExpertiseArea]
    style_profile: StyleProfile
    recent_ideas: list[ContentIdea]         # Past N days ideas
    recent_posts: list[ContentDraft]        # Published in past 14 days
    count: int = 5                          # Number of ideas to return
    diversity_min: float = 0.3              # Minimum category diversity
```

### 5.3 Outputs

```python
class TopicSelectorOutput(BaseModel):
    ideas: list[ContentIdea]
    selection_rationale: str                # Why these ideas were chosen
    coverage_analysis: CoverageAnalysis

class CoverageAnalysis(BaseModel):
    categories_covered: list[ContentCategory]
    categories_missed: list[ContentCategory]
    dominant_signal: Literal["github", "knowledge", "trends", "mixed"]
    diversity_score: float                  # 0.0 - 1.0
```

### 5.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| ContentEngine (IdeaGenerator) | Internal service | Idea generation and ranking |
| StyleService | Internal service | Style profile for tone/length suggestions |
| CacheService | Internal service | Idea cache (1hr TTL) |

### 5.5 Memory

| Memory Type | Read | Write | TTL |
|------------|------|-------|-----|
| Long-term | Style profile, expertise | — | Permanent |
| Working | Recent ideas, recent posts | Generated ideas | 24 hours |
| Episodic | Past selection patterns | Idea generation logs | 90 days |

### 5.6 Prompt

**Prompt file**: `backend/prompts/topic_selector.md`

```
SYSTEM:
You are the Topic Selector Agent for BrandOS. Your task is to generate
content ideas by fusing multiple signal sources.

USER:
{research_topics_json}
{knowledge_context_json}
{github_activity_json}
{expertise_areas_json}
{style_profile_json}
{recent_posts_json}
TASK: Generate {count} content ideas that:
1. Are relevant to the user's expertise areas
2. Are novel (not duplicates of recent posts)
3. Have a clear angle and hook
4. Span diverse categories
5. Match the user's writing style
```

### 5.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| Low signal quality | Few ideas generated | Brief feels sparse | Signal quality < 0.3 |
| LLM hallucination | Ideas not based on actual signals | Misleading content | Idea sourced to nonexistent signal |
| Category clustering | All ideas same category | Reduced diversity | Diversity < 0.2 |
| Novelty failure | Repeated idea from last week | User ignores brief | Title similarity > 0.8 |

### 5.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | LLM returns < count ideas | Reduce temperature, retry with stricter schema |
| 2 | Still low count | Fall back to template-based ideas from KB tags |
| 3 | Complete failure | Return signal_quality="low" message to user |

### 5.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| Idea acceptance rate | ≥ 40% of ideas lead to drafts | Track idea → draft conversion |
| Category diversity | ≥ 3 categories per brief | Count distinct categories |
| Novelty rate | < 10% duplicates with past 14 days | Title similarity check |
| User satisfaction | ≥ 3.5/5 avg rating on generated drafts | User ratings on drafts |
| Signal relevance | ≥ 80% ideas traceable to input signals | Cross-reference idea sources |

---

## 6. Strategy Agent

The Strategy Agent creates the content strategy — deciding which ideas to pursue, in what order, on which platforms, and at what cadence. It ensures the user's content output is coherent, timely, and aligned with their personal brand goals.

### 6.1 Responsibilities

- Select top ideas from the Topic Selector for immediate execution
- Assign ideas to platforms (LinkedIn, X, blog) based on content fit
- Determine optimal posting schedule considering timezone, platform best times, and user cadence
- Balance content categories across the week/month (e.g., not two tutorials in a row)
- Consider ongoing narrative arcs (multi-part series, follow-ups to hot topics)
- Track content authority score and adjust strategy to improve weak areas

### 6.2 Inputs

```python
class StrategyAgentInput(BaseModel):
    user_id: uuid.UUID
    selected_ideas: list[ContentIdea]
    user_preferences: UserPreferences
    posting_cadence: PostingCadence
    platform_status: dict[str, PlatformConnectionStatus]
    published_recently: list[ContentDraft]     # Past 7 days
    content_scores: list[ContentScore] | None  # Past performance by category
    upcoming_schedule: list[ScheduledPost]      # Already scheduled posts
    days_to_plan: int = 7

class PostingCadence(BaseModel):
    posts_per_week: int
    preferred_days: list[int]           # 0=Mon, 6=Sun
    preferred_times: list[str]          # "HH:MM"
    platforms: list[str]
```

### 6.3 Outputs

```python
class StrategyAgentOutput(BaseModel):
    plan: list[PlannedPost]
    narrative_arc: NarrativeArc | None
    strategy_rationale: str

class PlannedPost(BaseModel):
    idea_id: uuid.UUID
    title: str
    platform: str
    scheduled_date: date
    scheduled_time: str                 # "HH:MM"
    tone: Literal["conversational", "professional", "technical", "inspirational"]
    length: Literal["short", "medium", "long"]
    category: ContentCategory
    suggested_angle: str                # Platform-specific angle
    series_position: int | None         # If part of a series
    priority: Literal["high", "medium", "low"]

class NarrativeArc(BaseModel):
    active: bool
    theme: str                          # e.g., "Building AI Agents"
    posts_in_series: int
    current_position: int
    expected_completion: date
```

### 6.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| ProfileService | Internal service | User preferences, posting cadence |
| PlatformService | Internal service | Platform status, schedule |
| AnalyticsService | Internal service | Past content scores |
| LLMClient | LLM | Strategic reasoning |

### 6.5 Memory

| Memory Type | Read | Write | TTL |
|------------|------|-------|-----|
| Strategic | Posting cadence, platform preferences | Updated cadence | Permanent |
| Long-term | Content scores, category performance | — | Permanent |
| Working | Current plan | Generated plan | 7 days |

### 6.6 Prompt

**Prompt file**: `backend/prompts/strategy_agent.md`

```
SYSTEM:
You are the Strategy Agent for BrandOS. Your task is to create a content
strategy that schedules posts optimally across the user's platforms.

USER:
{ideas_json}
{preferences_json}
{platform_status_json}
{published_recently_json}
{content_scores_json}
{upcoming_schedule_json}
TASK: Create a {days_to_plan}-day content plan that:
1. Assigns each idea to the best platform and time
2. Ensures no two consecutive posts share the same category
3. Prioritizes high-engagement categories based on past performance
4. Creates narrative arcs for related ideas
5. Respects platform posting limits and user cadence
```

### 6.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| Over-scheduling | More posts than cadence allows | User overwhelmed | Count exceeds preference |
| Platform mismatch | Idea assigned to wrong platform | Poor performance | Category-platform fit score < 0.3 |
| No narrative arc | Isolated posts, no series | Missed engagement opportunity | All series_position = None |
| Timezone error | Wrong posting time | Suboptimal engagement | Time outside user's active hours |

### 6.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | Plan validation fails | Remove invalid assignments, regenerate |
| 2 | Still invalid | Return conservative plan (fewer posts, verified slots) |
| 3 | Complete failure | Return empty plan with error explanation |

### 6.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| Plan adoption rate | ≥ 70% of planned posts executed | Count planned → published |
| Category balance | ≤ 40% single category per week | Category distribution |
| Platform fit | ≥ 90% platform assignments used | Published on assigned platform |
| Narrative completion | ≥ 50% series completed | Track series_position progression |

---

## 7. Hook Generator

The Hook Generator creates the opening lines for drafts — the most critical part of any post. It generates multiple hook variations for a single idea, optimized for different platforms and audience segments.

### 7.1 Responsibilities

- Generate 3-5 hook variants per idea
- Optimize hooks for platform-specific engagement patterns (LinkedIn: story-based, X: concise/contrarian)
- Match hook style to user's voice profile (question, statistic, story, quote, contrarian take)
- Score hooks for engagement potential and authenticity
- Provide hook rationale explaining why each variant works

### 7.2 Inputs

```python
class HookGeneratorInput(BaseModel):
    user_id: uuid.UUID
    idea: ContentIdea
    context: AggregatedContext
    style_profile: StyleProfile
    platform: str
    audience: Literal["peers", "managers", "general_tech", "founders"]
    count: int = 3                      # Hook variants to generate
    included_styles: list[HookStyle] | None = None  # Filter by style

class HookStyle(str, Enum):
    QUESTION = "question"               # "What if you could 10x your output?"
    STATISTIC = "statistic"             # "80% of engineers are doing this wrong."
    STORY = "story"                     # "Last week, I accidentally..."
    CONTRARIAN = "contrarian"            # "Everyone is talking about X. Here's why they're wrong."
    QUOTE = "quote"                     # "As [person] once said..."
    PREDICTION = "prediction"           # "In 2027, this will be obsolete."
    PERSONAL = "personal"               # "I spent 3 years building..."
```

### 7.3 Outputs

```python
class HookGeneratorOutput(BaseModel):
    hooks: list[GeneratedHook]
    platform_insight: str               # What works on this platform

class GeneratedHook(BaseModel):
    text: str
    style: HookStyle
    platform_fit_score: float           # 0.0 - 1.0
    engagement_prediction: float        # 0.0 - 1.0
    authenticity_score: float           # 0.0 - 1.0 (matches user voice)
    rationale: str                      # Why this hook works
    suggested_follow_up: str            # How to transition to body
```

### 7.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| LLMClient | LLM | Hook generation |
| StyleService | Internal service | Voice profile for authenticity check |

### 7.5 Memory

| Memory Type | Read | Write | TTL |
|------------|------|-------|-----|
| Long-term | Style profile | — | Permanent |
| Working | — | Generated hooks (discarded after selection) | Session |

### 7.6 Prompt

**Prompt file**: `backend/prompts/hook_generator.md`

```
SYSTEM:
You are the Hook Generator Agent for BrandOS. Your task is to create
compelling opening lines for technical content posts.

USER:
{idea_json}
{style_profile_json}
{platform}
{audience}
TASK: Generate {count} hook variants, each with a different style:
1. The hook text (max 150 chars for LinkedIn, 100 for X)
2. The hook style
3. Why this hook would engage {audience} on {platform}
4. How well it matches the user's authentic voice
5. Predicted engagement potential (0.0-1.0)
6. Suggested transition sentence to the post body
```

### 7.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| Generic hooks | Low authenticity scores | User ignores suggestions | Authenticity < 0.4 |
| Same-style clustering | All hooks same style | Reduced choice | Style variance = 0 |
| Length violation | Hook exceeds platform limit | Truncated in UI | Character count > max |
| Off-tone hook | Hook doesn't match idea | Confusing transition | Manual review |

### 7.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | All hooks same style | Force include at least one of each preferred style |
| 2 | Authenticity < 0.4 | Lower temperature, emphasize voice profile in prompt |
| 3 | Still failing | Return simpler hooks based on user's most-used style |

### 7.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| Hook adoption rate | ≥ 50% of variants used | Track hook → final draft |
| Style diversity | ≥ 3 styles per idea generation | Count distinct styles in output |
| Platform fit | ≥ 80% hooks respect platform limits | Character count check |
| Authenticity score | ≥ 0.6 average | StyleService similarity check |

---

## 8. Writing Agent

The Writing Agent composes full draft content from an idea, context, and style profile. It is the most LLM-intensive agent in the pipeline.

### 8.1 Responsibilities

- Compose complete draft body from idea + aggregated context
- Apply structural templates based on content category (tutorial, opinion, analysis, story)
- Include supporting points, evidence, and examples from knowledge base
- Write in the user's voice using style profile parameters
- Format for target platform constraints (character limits, formatting)
- Include suggested hashtags, mentions, and call-to-action

### 8.2 Inputs

```python
class WritingAgentInput(BaseModel):
    user_id: uuid.UUID
    idea: ContentIdea
    context: AggregatedContext
    style_profile: StyleProfile
    platform: str
    params: CompositionParams
    hook: str | None = None               # Selected hook (optional)
    previous_version: str | None = None   # For regeneration
    feedback: str | None = None           # User feedback for regeneration
```

### 8.3 Outputs

```python
class WritingAgentOutput(BaseModel):
    draft: DraftResult
    composition_log: CompositionLog

class DraftResult(BaseModel):
    title: str
    body: str
    word_count: int
    reading_time_seconds: int
    sections: list[str]
    hashtags: list[str]
    mentions: list[str]
    call_to_action: str | None
    suggested_post_time: str | None

class CompositionLog(BaseModel):
    llm_model: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    temperature: float
    duration_ms: int
    retry_count: int
```

### 8.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| LLMClient | LLM | Draft composition (primary consumer) |
| StyleService | Internal service | Style profile retrieval |
| PromptBuilder | Internal module | Prompt construction |

### 8.5 Memory

| Memory Type | Read | Write | TTL |
|------------|------|-------|-----|
| Long-term | Style profile | — | Permanent |
| Working | Current context, idea | — | Session |
| Episodic | Past drafts (for regeneration) | New draft | 90 days |

### 8.6 Prompt

**Prompt file**: `backend/prompts/writing_agent.md`

```
SYSTEM:
You are the Writing Agent for BrandOS. You write technical content in the
user's authentic voice. You never use generic AI phrasing.

USER:
{idea_json}
{context_json}
{style_profile_json}
{platform}
{params_json}
{hook}
TASK: Write a complete draft with:
1. A compelling title
2. Body paragraphs that flow naturally (not list-like)
3. Technical depth appropriate for {audience}
4. Natural use of the user's vocabulary and sentence patterns
5. A strong closing with a call-to-action
6. 2-3 relevant hashtags

CONSTRAINTS:
- Max {max_chars} characters for {platform}
- Use {tone} tone
- Target {length} length
- Natural code formatting if applicable
- Avoid: "In today's digital landscape", "Let's dive in", "I'm excited to share"
```

### 8.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| Token limit | Output truncated at max_tokens | Incomplete draft | finish_reason == "length" |
| Hallucination | Facts not in context | Misleading content | Quality gate flags |
| Generic writing | Low authenticity score | Not useful to user | Style similarity < 0.3 |
| Platform violation | Content exceeds limit | Publish failure | Character count > max |
| Structure collapse | No clear paragraphs/sections | Hard to read | Section count < 3 |

### 8.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | Truncated output | Increase max_tokens by 50%, retry |
| 2 | Authenticity < 0.4 | Lower temperature to 0.5, add more style examples |
| 3 | Still failing | User gets warning: "AI generation quality low, consider manual draft" |

### 8.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| User rating | ≥ 3.5/5 average | User ratings on generated drafts |
| Edit distance | ≤ 30% user edits post-generation | Diff original vs final |
| Hallucination rate | ≤ 1 per 500 words | Quality gate detection |
| Authenticity score | ≥ 0.6 average | StyleService similarity |
| Platform compliance | 100% within length limits | Automated check before save |
| Generation latency | < 30s p95 | Timer from input to output |

---

## 9. Review Agent

The Review Agent validates generated content before it reaches the user. It checks quality, authenticity, factual accuracy, platform compliance, and safety. It can pass, fail, or warn on specific sections.

### 9.1 Responsibilities

- Score draft across 7 quality dimensions (factual accuracy, hallucination risk, readability, authenticity, technical depth, engagement potential, platform appropriateness)
- Detect hallucinations by cross-referencing claims against context
- Identify sections that deviate from style profile
- Flag platform policy violations (length limits, prohibited content, formatting)
- Provide specific, actionable revision suggestions
- Make pass/fail/warn verdict with clear rationale

### 9.2 Inputs

```python
class ReviewAgentInput(BaseModel):
    user_id: uuid.UUID
    draft: DraftResult
    idea: ContentIdea
    context: AggregatedContext
    style_profile: StyleProfile
    platform: str
    thresholds: QualityThresholds | None = None

class QualityThresholds(BaseModel):
    min_overall: float = 0.6
    min_factual_accuracy: float = 0.7
    max_hallucination_risk: float = 0.3
    min_authenticity: float = 0.5
    min_readability: float = 0.6
```

### 9.3 Outputs

```python
class ReviewAgentOutput(BaseModel):
    verdict: Literal["pass", "warn", "fail"]
    scores: QualityDimensions
    warnings: list[QualityWarning]
    recommendations: list[str]
    can_auto_publish: bool              # True if all thresholds met

class QualityWarning(BaseModel):
    severity: Literal["critical", "major", "minor"]
    category: str                       # e.g., "hallucination", "authenticity", "platform"
    message: str                        # Human-readable
    affected_text: str | None           # The problematic passage
    suggestion: str | None              # How to fix
```

### 9.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| LLMClient | LLM | Quality evaluation (can use smaller/cheaper model) |
| StyleService | Internal service | Authenticity comparison |
| KnowledgeBaseService | Internal service | Factual grounding check |

### 9.5 Memory

| Memory Type | Read | Write | TTL |
|------------|------|-------|-----|
| Long-term | Knowledge base (for fact-check) | — | Permanent |
| Working | Current draft, context | Review results | Session |

### 9.6 Prompt

**Prompt file**: `backend/prompts/review_agent.md`

```
SYSTEM:
You are the Review Agent for BrandOS. You evaluate AI-generated content
for quality, authenticity, and safety before it reaches the user.

USER:
{draft_body}
{idea_json}
{context_json}
{style_profile_json}
{platform}
TASK: Score the draft on these dimensions (0.0-1.0):
1. factual_accuracy — Are claims supported by context?
2. hallucination_risk — Does it state things not in context?
3. readability — Is it clear and well-structured?
4. authenticity — Does it sound like the writer?
5. technical_depth — Is the depth appropriate for the topic?
6. engagement_potential — Would a reader stop scrolling?
7. platform_appropriateness — Does it fit {platform}?

For each dimension < 0.6, provide a specific warning with suggested fix.
```

### 9.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| Over-critical | False positives on quality | User ignores review | > 30% warnings dismissed |
| Too lenient | High scores on poor drafts | Low-quality content published | User edits high or rating low |
| Hallucination miss | Undetected hallucination published | Reputation risk | User reports inaccuracy |
| Performance slow | > 10s review time | Pipeline bottleneck | Timer exceeds threshold |

### 9.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | LLM fails to parse structured output | Re-prompt with stricter schema |
| 2 | Partial scores missing | Fill missing dimensions with conservative estimates |
| 3 | Complete failure | Default to "warn" with "review failed" message |

### 9.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| Warning acceptance | ≥ 60% warnings lead to edits | Track warning → revision |
| False positive rate | ≤ 20% of warnings dismissed as wrong | User dismissal tracking |
| Hallucination catch rate | ≥ 90% of actual hallucinations flagged | Manual audit of 100 drafts |
| Review latency | < 5s p95 | Pipeline timing |
| Correlation with user rating | Review scores correlate with user rating (r > 0.5) | Pearson correlation |

---

## 10. Analytics Agent

The Analytics Agent analyzes published content performance and derives actionable insights. It is not a dashboard — it is an analysis engine that tells the user what's working, what's not, and what to do next.

### 10.1 Responsibilities

- Compute engagement metrics (impressions, likes, comments, shares, CTR, engagement rate)
- Identify top-performing content patterns (by category, length, tone, hook style, posting time)
- Detect growth trends (follower growth, share of voice, category performance over time)
- Generate content score predictions for planned posts
- Produce weekly/monthly performance reports with improvement recommendations
- Feed insights back to Strategy Agent for plan optimization

### 10.2 Inputs

```python
class AnalyticsAgentInput(BaseModel):
    user_id: uuid.UUID
    action: Literal["analyze_period", "predict_performance", "generate_report"]
    period: AnalyticsPeriod | None = None
    # For prediction
    planned_posts: list[PlannedPost] | None = None
    # For report
    report_type: Literal["weekly", "monthly"] | None = None
    include_comparison: bool = True
```

### 10.3 Outputs

```python
class AnalyticsAgentOutput(BaseModel):
    action: str
    # For period analysis
    overview: AnalyticsOverview | None = None
    top_posts: list[PostPerformance] | None = None
    engagement_trends: EngagementTrends | None = None
    audience_growth: AudienceGrowth | None = None
    best_performing_formats: list[FormatPerformance] | None = None
    # For prediction
    performance_predictions: list[PerformancePrediction] | None = None
    # For report
    report: PerformanceReport | None = None

class PerformancePrediction(BaseModel):
    planned_post_id: str
    predicted_engagement_rate: float
    confidence: float
    factors: list[str]                  # Why this prediction

class PerformanceReport(BaseModel):
    period_label: str
    summary: str                        # Executive summary
    key_insights: list[Insight]
    recommendations: list[str]
    comparison_to_previous: PeriodComparison | None

class Insight(BaseModel):
    category: Literal["content", "engagement", "growth", "timing", "audience"]
    finding: str                        # e.g., "Tutorials get 2x more engagement than opinions"
    evidence: str                       # e.g., "15 tutorials avg 5.2% engagement vs 8 opinions avg 2.1%"
    suggested_action: str
    confidence: float
```

### 10.4 Dependencies

| Dependency | Type | Reason |
|-----------|------|--------|
| AnalyticsService | Internal service | Metrics computation, historical data |
| PlatformService | Internal service | Raw analytics from platforms |
| LLMClient | LLM | Insight generation, report narrative |

### 10.5 Memory

| Memory Type | Read | Write | TTL |
|------------|------|-------|-----|
| Long-term | All published post metrics | Updated content scores | Permanent |
| Strategic | Historical performance patterns | Updated best formats | Permanent |
| Working | Current period analytics | Current analysis | Period end |

### 10.6 Prompt

**Prompt file**: `backend/prompts/analytics_agent.md`

```
SYSTEM:
You are the Analytics Agent for BrandOS. You analyze content performance
data and generate actionable insights to improve the user's content strategy.

USER:
{overview_json}
{top_posts_json}
{engagement_trends_json}
{audience_growth_json}
{format_performance_json}
{period}
TASK: Generate a {period} performance analysis:
1. Executive summary (2-3 sentences)
2. Top 3-5 key insights with supporting evidence
3. Specific, actionable recommendations
4. Comparison to previous period
```

### 10.7 Failure Modes

| Failure | Symptom | Impact | Detection |
|---------|---------|--------|-----------|
| Insufficient data | No historical posts | Empty report | post_count == 0 |
| Platform API down | No recent metrics | Stale analysis | API error |
| Statistical noise | High variance, no clear patterns | Misleading recommendations | Confidence < 0.3 |
| Comparison unavailable | First period, no baseline | No trend data | previous_period is None |

### 10.8 Retry Strategy

| Attempt | Condition | Action |
|---------|-----------|--------|
| 1 | Platform API fails | Use cached analytics data |
| 2 | Cache also empty | Return "insufficient data" message with setup guidance |
| 3 | Partial data | Run analysis on available data, note gaps in report |

### 10.9 Evaluation

| Metric | Target | Method |
|--------|--------|--------|
| Insight accuracy | ≥ 80% insights correlate with actual engagement | Verify with next period data |
| Report engagement | ≥ 50% users open weekly report | Report open rate |
| Recommendation adoption | ≥ 30% recommendations reflected in strategy | Cross-reference with strategy |
| Prediction accuracy | ≤ 30% error in engagement predictions | Actual vs predicted |

---

## 11. Agent Orchestration

### 11.1 Pipeline Orchestrator

The `PipelineOrchestrator` manages agent execution order, timeouts, retries, and circuit breaking.

```python
class PipelineOrchestrator:
    """
    Executes agent pipelines with timeout, retry, and circuit breaker.
    """

    def __init__(
        self,
        stages: list[PipelineStage],
        metrics: MetricsCollector,
        logger: Logger,
    ): ...

    async def execute(
        self, context: AgentContext
    ) -> PipelineResult:
        for stage in self.stages:
            stage_result = await self._execute_with_retry(
                stage, context
            )
            context.previous_outputs[stage.agent_name] = stage_result.output

            if stage_result.metrics.abort_requested:
                return PipelineResult(
                    success=False,
                    failed_stage=stage.agent_name,
                    partial_results=context.previous_outputs,
                )
        return PipelineResult(
            success=True,
            full_results=context.previous_outputs,
        )

class PipelineStage(BaseModel):
    agent: BaseAgent
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int = 2
    critical: bool = True               # If False, skip on failure instead of abort
```

### 11.2 Pipeline Configurations

#### Daily Brief Pipeline

```
┌──────────┬──────────────┬──────────┬─────────┐
│ Agent    │ Timeout      │ Retries  │ Critical│
├──────────┼──────────────┼──────────┼─────────┤
│ Research │ 30s          │ 2        │ No      │
│ Knowledge│ 15s          │ 2        │ Yes     │
│ Memory   │ 5s           │ 1        │ Yes     │
│ Topic    │ 20s          │ 2        │ Yes     │
│ Strategy │ 15s          │ 1        │ No      │
└──────────┴──────────────┴──────────┴─────────┘
Total budget: 85s. Runs 1hr before user's brief time.
```

#### Draft Generation Pipeline

```
┌──────────┬──────────────┬──────────┬─────────┐
│ Agent    │ Timeout      │ Retries  │ Critical│
├──────────┼──────────────┼──────────┼─────────┤
│ Knowledge│ 10s          │ 1        │ Yes     │
│ Memory   │ 3s           │ 1        │ Yes     │
│ Hook     │ 10s          │ 2        │ No      │
│ Writing  │ 60s          │ 2        │ Yes     │
│ Review   │ 10s          │ 1        │ Yes     │
└──────────┴──────────────┴──────────┴─────────┘
Total budget: 93s. Runs on-demand when user clicks "Generate draft".
```

#### Analytics Pipeline

```
┌──────────┬──────────────┬──────────┬─────────┐
│ Agent    │ Timeout      │ Retries  │ Critical│
├──────────┼──────────────┼──────────┼─────────┤
│ Analytics│ 30s          │ 2        │ Yes     │
│ Memory   │ 5s           │ 1        │ No      │
│ Strategy │ 10s          │ 1        │ No      │
└──────────┴──────────────┴──────────┴─────────┘
Total budget: 45s. Runs after each publish + weekly summary cron.
```

### 11.3 Circuit Breaker Rules

| Condition | Action | Recovery |
|-----------|--------|----------|
| 3 consecutive pipeline failures | Disable pipeline for 30 minutes | Manual re-enable or timeout |
| Agent retries exhausted (non-critical) | Skip agent, continue pipeline | Next run |
| Agent retries exhausted (critical) | Abort pipeline, notify user | Next run |
| LLM provider returns 429 (rate limit) | Backoff 60s, retry once | Normal operation resumes |

---

## 12. Prompt Contract Registry

Every agent prompt is stored as a separate markdown file in `backend/prompts/`. Each prompt file follows a strict contract format.

### 12.1 Prompt File Contract

```markdown
# {agent_name}.md

## System Prompt
[The system-level instructions that define the agent's role]

## User Prompt Template
[Template with {placeholder} variables for runtime substitution]

## Output Schema
[Structured JSON schema the LLM must return]

## Examples
[2-3 few-shot examples showing ideal input/output pairs]

## Constraints
[Length limits, tone rules, prohibited phrases, etc.]
```

### 12.2 Prompt File Registry

| File | Agent | Variables | Max Tokens | Model |
|------|-------|-----------|------------|-------|
| `research_agent.md` | Research | `scraped_topics`, `expertise_areas`, `kb_topics` | 500 | Claude Haiku |
| `knowledge_agent.md` | Knowledge | `extracted_text`, `url` | 300 | Claude Haiku |
| `memory_agent.md` | Memory | `episodic_records`, `strategic_memory` | 400 | Claude Haiku |
| `topic_selector.md` | Topic Selector | `research_topics`, `kb_context`, `github_activity`, `expertise`, `style`, `recent_posts` | 800 | Claude Sonnet |
| `strategy_agent.md` | Strategy | `ideas`, `preferences`, `platforms`, `recent_posts`, `scores` | 600 | Claude Sonnet |
| `hook_generator.md` | Hook Generator | `idea`, `style_profile`, `platform`, `audience` | 400 | Claude Sonnet |
| `writing_agent.md` | Writing | `idea`, `context`, `style_profile`, `platform`, `params`, `hook` | 2048 | Claude Opus |
| `review_agent.md` | Review | `draft_text`, `idea`, `context`, `style_profile`, `platform` | 600 | Claude Haiku |
| `analytics_agent.md` | Analytics | `overview`, `top_posts`, `trends`, `growth`, `formats` | 800 | Claude Haiku |

### 12.3 Variable Naming Convention

All prompt variables follow `{snake_case}` format. The `PromptBuilder` class resolves them at runtime:

```python
class PromptBuilder:
    def __init__(self, prompt_dir: Path):
        self.prompt_dir = prompt_dir
        self.cache: dict[str, str] = {}

    async def load_prompt(self, agent_name: str) -> str:
        if agent_name not in self.cache:
            path = self.prompt_dir / f"{agent_name}.md"
            self.cache[agent_name] = path.read_text()
        return self.cache[agent_name]

    def build(
        self,
        agent_name: str,
        variables: dict[str, Any],
    ) -> tuple[str, str]:            # (system_prompt, user_prompt)
        prompt = self.load_prompt(agent_name)
        # Parse template, substitute {variables}
        # Return (system_section, user_section)
```

---

## Appendix A: Agent Dependency Graph

```
                    ┌──────────────┐
                    │  Research    │
                    │  Agent       │
                    └──────┬───────┘
                           │ topics
                           ▼
                    ┌──────────────┐
              ┌─────│  Knowledge   │─────┐
              │     │  Agent       │     │
              │     └──────┬───────┘     │
              │            │             │
              │            ▼             │
              │     ┌──────────────┐     │
              │     │  Memory      │     │
              │     │  Agent       │     │
              │     └──────┬───────┘     │
              │            │             │
              ▼            ▼             ▼
        ┌──────────────────────────────────────┐
        │           Topic Selector              │
        └────────────────┬─────────────────────┘
                         │ ideas
                         ▼
        ┌──────────────────────────────────────┐
        │           Strategy Agent              │
        └────────────────┬─────────────────────┘
                         │ plan
                         ▼
        ┌──────────────────────────────────────┐
        │           Hook Generator             │
        └────────────────┬─────────────────────┘
                         │ hook
                         ▼
        ┌──────────────────────────────────────┐
        │           Writing Agent               │
        └────────────────┬─────────────────────┘
                         │ draft
                         ▼
        ┌──────────────────────────────────────┐
        │           Review Agent                │
        │  ┌─────┐  ┌────┐  ┌──────────────┐   │
        │  │Pass │  │Warn│  │    Fail      │   │
        │  └──┬──┘  └──┬─┘  └──────┬───────┘   │
        └─────┼────────┼───────────┼───────────┘
              │        │           │
              ▼        ▼           ▼
         User's   User sees  → Writing Agent
         Drafts   warnings    (regenerate)

        ┌──────────────────────────────────────┐
        │           Analytics Agent             │
        │  Reads: Published posts               │
        │  Writes: Insights → Memory Agent      │
        │          Recommendations → Strategy   │
        └──────────────────────────────────────┘
```

## Appendix B: Agent Cost Budget (per run)

| Agent | Model | Input Tokens | Output Tokens | Cost (est.) |
|-------|-------|-------------|--------------|-------------|
| Research | Claude Haiku | 2,000 | 500 | $0.001 |
| Knowledge | Claude Haiku | 4,000 | 300 | $0.002 |
| Memory | Claude Haiku | 1,000 | 400 | $0.001 |
| Topic Selector | Claude Sonnet | 3,000 | 800 | $0.006 |
| Strategy | Claude Sonnet | 2,000 | 600 | $0.004 |
| Hook Generator | Claude Sonnet | 1,500 | 400 | $0.003 |
| Writing | Claude Opus | 6,000 | 2,048 | $0.12 |
| Review | Claude Haiku | 3,000 | 600 | $0.001 |
| Analytics | Claude Haiku | 2,500 | 800 | $0.001 |
| **Total (brief)** | — | — | — | **$0.018** |
| **Total (draft)** | — | — | — | **$0.131** |
