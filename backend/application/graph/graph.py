from __future__ import annotations

import os
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from application.graph.nodes.analytics_node import analytics_node
from application.graph.nodes.hook_generation_node import make_hook_generation_node
from application.graph.nodes.knowledge_node import make_knowledge_node
from application.graph.nodes.memory_node import memory_node
from application.graph.nodes.research_node import make_research_node
from application.graph.nodes.review_node import make_review_node
from application.graph.nodes.strategy_node import make_strategy_node
from application.graph.nodes.topic_selection_node import make_topic_selection_node
from application.graph.nodes.writing_node import make_writing_node
from application.graph.state import ContentState
from core.llm import LLMClient
from services.prompt.service import PromptService


def build_content_graph(
    llm: LLMClient | None = None,
    prompt_service: PromptService | None = None,
    research_service: Any | None = None,
    kb_service: Any | None = None,
    langsmith_api_key: str | None = None,
    langsmith_project: str = "brandos-content-pipeline",
) -> StateGraph:
    if langsmith_api_key:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", langsmith_api_key)
        os.environ.setdefault("LANGCHAIN_PROJECT", langsmith_project)

    builder = StateGraph(ContentState)

    builder.add_node("research", make_research_node(research_service))
    builder.add_node("knowledge", make_knowledge_node(kb_service))
    builder.add_node("memory", memory_node)
    builder.add_node("topic_selection", make_topic_selection_node())
    builder.add_node("strategy", make_strategy_node(llm, prompt_service))
    builder.add_node("hook_generation", make_hook_generation_node(llm, prompt_service))
    builder.add_node("writing", make_writing_node(llm, prompt_service))
    builder.add_node("review", make_review_node(llm, prompt_service))
    builder.add_node("analytics", analytics_node)

    builder.add_edge(START, "research")
    builder.add_edge("research", "knowledge")
    builder.add_edge("knowledge", "memory")
    builder.add_edge("memory", "topic_selection")
    builder.add_edge("topic_selection", "strategy")
    builder.add_edge("strategy", "hook_generation")
    builder.add_edge("hook_generation", "writing")
    builder.add_edge("writing", "review")

    builder.add_conditional_edges(
        "review",
        _route_from_review,
        {
            "approve": "analytics",
            "human_review": END,
            "reject": END,
        },
    )

    builder.add_edge("analytics", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


def _route_from_review(state: ContentState) -> str:
    review = state.get("review_output") or {}
    action = review.get("recommended_action", "approve")
    if action == "reject":
        return "reject"
    if action in ("revise", "major_revision"):
        return "human_review"
    return "approve"
