# LangGraph Migration Architecture

## Target Folder Structure

```
backend/
├── application/
│   ├── __init__.py
│   └── graph/
│       ├── __init__.py
│       ├── state.py              ← ContentState TypedDict (LangGraph state)
│       ├── graph.py              ← build_graph() → compiled ComposeStateGraph
│       └── nodes/
│           ├── __init__.py
│           ├── research_node.py
│           ├── knowledge_node.py
│           ├── memory_node.py
│           ├── topic_selection_node.py
│           ├── strategy_node.py
│           ├── hook_generation_node.py
│           ├── writing_node.py
│           ├── review_node.py
│           └── analytics_node.py
├── services/
│   ├── content_engine/           ← Kept, nodes wrap it
│   ├── evaluation.py
│   ├── history.py
│   ├── prompt/
│   ├── research.py
│   ├── knowledge.py
│   ├── ingestion.py
│   └── trend/
├── agents/                       ← TO DELETE after migration
├── workflows/                    ← TO DELETE after migration
├── models/                       ← Kept
├── schemas/                      ← Kept
├── prompts/                      ← Kept (versioned Markdown)
├── core/
│   ├── config.py                 ← + LANGCHAIN_API_KEY, LANGCHAIN_PROJECT
│   ├── llm.py                    ← Kept, nodes use LLMClient
│   ├── chroma.py                 ← Kept
│   └── embedding.py              ← Kept
├── tools/                        ← NEW: LangChain tools
│   ├── __init__.py
│   └── search_tools.py
└── api/v1/content.py             ← Updated to call compiled graph
```

## State Model

```python
class ContentState(TypedDict):
    # Inputs
    user_id: str
    session_id: str
    pipeline_id: str
    topic: Optional[str]
    platform: str
    tone: str
    max_length: int

    # Progress
    current_step: str
    errors: list[str]
    requires_human_approval: bool

    # Per-node outputs (written once, read by downstream)
    research_output: Optional[dict]
    knowledge_output: Optional[dict]
    memory_output: Optional[dict]
    topic_output: Optional[dict]
    strategy_output: Optional[dict]
    hooks_output: Optional[dict]
    draft_output: Optional[dict]
    review_output: Optional[dict]
    analytics_output: Optional[dict]

    # Final artifact
    final_output: Optional[dict]

    # Timing
    step_timing: dict[str, float]
```

## Graph Topology

```
START → research → knowledge → memory → topic_selection → strategy → hook_generation → writing → review
                                                                                                       │
                                                                                          ┌────────────┤
                                                                                          ▼            ▼
                                                                                     approve       reject
                                                                                          │            │
                                                                                          ▼            ▼
                                                                                     analytics    END (human)
                                                                                          │
                                                                                          ▼
                                                                                        END
```

## Node Contracts

Every node function:
- Signature: `(state: ContentState) → dict` (partial state update)
- Is `@staticmethod` or module-level function
- Has single responsibility
- Delegates to services for business logic
- Uses `LLMClient` for LLM calls (via service layer)

## LangSmith Integration

```python
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = "brandos-content-pipeline"
```

## API Integration

```
POST /content/generate
  → deserialize request
  → compiled_graph.ainvoke(state)
  → record in HistoryService
  → return response
```
