from __future__ import annotations

import uuid
from typing import Any

import pytest

from application.graph.graph import _route_from_review, build_content_graph
from application.graph.nodes.analytics_node import make_analytics_node
from application.graph.nodes.memory_node import make_memory_node
from application.graph.nodes.research_node import make_research_node
from application.graph.nodes.topic_selection_node import make_topic_selection_node
from application.graph.state import ContentState


def _make_state(overrides: dict[str, Any] | None = None) -> ContentState:
    base = ContentState(
        user_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        pipeline_id=str(uuid.uuid4()),
        topic=None,
        platform="linkedin",
        tone="professional",
        max_length=280,
    )
    if overrides:
        for k, v in overrides.items():
            setattr(base, k, v)
    return base


class TestGraphConstruction:
    def test_build_content_graph(self) -> None:
        graph = build_content_graph()
        assert graph is not None
        assert graph.name is not None

    def test_graph_has_all_nodes(self) -> None:
        graph = build_content_graph()
        expected_nodes = {
            "research",
            "knowledge",
            "memory",
            "topic_selection",
            "strategy",
            "hook_generation",
            "writing",
            "review",
            "analytics",
        }
        # CompiledStateGraph exposes .nodes as a dict of node_name -> node
        node_names = set(graph.nodes.keys())
        assert expected_nodes.issubset(node_names), f"Missing nodes: {expected_nodes - node_names}"

    def test_graph_compiles_with_checkpointer(self) -> None:
        graph = build_content_graph()
        assert hasattr(graph, "checkpointer")
        assert graph.checkpointer is not None


class TestRouteFromReview:
    def test_approve_routes_to_analytics(self) -> None:
        state = _make_state({"review_output": {"recommended_action": "approve"}})
        assert _route_from_review(state) == "approve"

    def test_reject_routes_to_reject(self) -> None:
        state = _make_state({"review_output": {"recommended_action": "reject"}})
        assert _route_from_review(state) == "reject"

    def test_revise_routes_to_revise(self) -> None:
        state = _make_state({"review_output": {"recommended_action": "revise"}})
        assert _route_from_review(state) == "revise"

    def test_major_revision_routes_to_revise(self) -> None:
        state = _make_state({"review_output": {"recommended_action": "major_revision"}})
        assert _route_from_review(state) == "revise"

    def test_default_approve_when_no_review(self) -> None:
        state = _make_state()
        assert _route_from_review(state) == "approve"

    def test_default_approve_when_unknown_action(self) -> None:
        state = _make_state({"review_output": {"recommended_action": "unknown"}})
        assert _route_from_review(state) == "approve"


class TestResearchNode:
    @pytest.mark.asyncio
    async def test_research_without_service(self) -> None:
        node = make_research_node(research_service=None)
        state = _make_state()
        result = await node(state)
        assert "research_output" in result
        assert result["current_step"] == "research"
        ro = result["research_output"]
        assert ro["findings"] == []
        assert ro["total_findings"] == 0
        assert ro["dominant_theme"] is None

    @pytest.mark.asyncio
    async def test_research_sets_latency(self) -> None:
        node = make_research_node()
        state = _make_state()
        result = await node(state)
        assert result["research_output"]["latency_ms"] >= 0


class TestTopicSelectionNode:
    @pytest.mark.asyncio
    async def test_selects_first_candidate(self) -> None:
        node = make_topic_selection_node()
        state = _make_state(
            {
                "research_output": {
                    "findings": [
                        {"title": "AI Trends", "description": "Latest AI", "relevance_score": 0.9}
                    ],
                    "dominant_theme": "AI",
                }
            }
        )
        result = await node(state)
        to = result["topic_output"]
        assert to["topic"] == "AI Trends"
        assert len(to["candidates"]) == 1

    @pytest.mark.asyncio
    async def test_falls_back_to_input_topic(self) -> None:
        node = make_topic_selection_node()
        state = _make_state({"topic": "Custom Topic"})
        result = await node(state)
        assert result["topic_output"]["topic"] == "Custom Topic"


class TestMemoryNode:
    @pytest.mark.asyncio
    async def test_memory_returns_defaults(self) -> None:
        node = make_memory_node()
        state = _make_state()
        result = await node(state)
        assert "memory_output" in result
        mo = result["memory_output"]
        assert mo["session_count"] == 1
        assert mo["previous_topics"] == []


class TestAnalyticsNode:
    @pytest.mark.asyncio
    async def test_analytics_with_good_score(self) -> None:
        node = make_analytics_node()
        state = _make_state(
            {
                "review_output": {"score": 0.85, "issues": []},
                "draft_output": {"draft": {"body": "Test body content here for the post"}},
            }
        )
        result = await node(state)
        ao = result["analytics_output"]
        assert ao["quality_label"] == "excellent"

    @pytest.mark.asyncio
    async def test_analytics_with_low_score(self) -> None:
        node = make_analytics_node()
        state = _make_state(
            {
                "review_output": {"score": 0.3, "issues": [{"severity": "critical", "aspect": "length", "suggestion": "Too short"}]},
                "draft_output": {"draft": {"body": "Short"}},
            }
        )
        result = await node(state)
        ao = result["analytics_output"]
        assert ao["quality_label"] == "needs_improvement"
        assert len(ao["recommendations"]) > 0


class TestFullGraph:
    @pytest.mark.asyncio
    async def test_graph_executes_without_services(self) -> None:
        graph = build_content_graph()
        start_state = _make_state({"topic": "AI in healthcare"})
        result = await graph.ainvoke(start_state, {"configurable": {"thread_id": "test-1"}})
        assert result is not None
        assert result.get("current_step") in ("analytics", "review")
        assert result.get("research_output") is not None
        assert result.get("topic_output") is not None
        assert result.get("strategy_output") is not None
        assert result.get("draft_output") is not None
        assert result.get("review_output") is not None

    @pytest.mark.asyncio
    async def test_graph_produces_draft(self) -> None:
        graph = build_content_graph()
        start_state = _make_state({"topic": "Machine Learning"})
        result = await graph.ainvoke(start_state, {"configurable": {"thread_id": "test-2"}})
        draft_output = result.get("draft_output") or {}
        draft = draft_output.get("draft", {})
        assert draft.get("body", "") != ""
        assert draft.get("title", "") != ""

    @pytest.mark.asyncio
    async def test_graph_sets_errors_list(self) -> None:
        graph = build_content_graph()
        start_state = _make_state({"topic": "Test Topic"})
        result = await graph.ainvoke(start_state, {"configurable": {"thread_id": "test-3"}})
        assert isinstance(result.get("errors"), list)

    @pytest.mark.asyncio
    async def test_graph_step_timing_populated(self) -> None:
        graph = build_content_graph()
        start_state = _make_state({"topic": "Test Topic"})
        result = await graph.ainvoke(start_state, {"configurable": {"thread_id": "test-4"}})
        assert isinstance(result.get("step_timing"), dict)


class TestGraphStateTransitions:
    @pytest.mark.asyncio
    async def test_pipeline_completes_all_steps(self) -> None:
        graph = build_content_graph()
        start_state = _make_state({"topic": "Test Topic"})
        result = await graph.ainvoke(start_state, {"configurable": {"thread_id": "test-5"}})
        step_keys = [
            "research_output",
            "knowledge_output",
            "memory_output",
            "topic_output",
            "strategy_output",
            "hooks_output",
            "draft_output",
            "review_output",
        ]
        for key in step_keys:
            assert result.get(key) is not None, f"Missing {key}"

    @pytest.mark.asyncio
    async def test_requires_human_approval_on_short_draft(self) -> None:
        graph = build_content_graph()
        start_state = _make_state(
            {
                "topic": "Short",
                "max_length": 30,
                "draft_output": {"draft": {"body": "Too short"}, "topic": "Short"},
            }
        )
        # Run only the review node to test routing
        from langgraph.graph import END, START, StateGraph

        builder = StateGraph(ContentState)
        from application.graph.nodes.review_node import make_review_node
        builder.add_node("review", make_review_node(llm=None, prompt_service=None))
        builder.add_edge(START, "review")
        builder.add_conditional_edges(
            "review",
            _route_from_review,
            {"approve": END, "revise": END, "reject": END},
        )
        mini_graph = builder.compile()
        result = await mini_graph.ainvoke(start_state)
        assert result.get("requires_human_approval") is True

    @pytest.mark.asyncio
    async def test_empty_body_passes_review(self) -> None:
        from application.graph.nodes.review_node import make_review_node

        node = make_review_node(llm=None)
        state = _make_state(
            {"draft_output": {"draft": {"body": "A longer body that should pass review easily with enough words."}, "topic": "Test"}}
        )
        result = await node(state)
        ro = result["review_output"]
        assert ro["score"] >= 0.3
        assert "recommended_action" in ro
