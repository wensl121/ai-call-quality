"""LangGraph 编排：节点 + 条件边。"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import (
    aggregator,
    auditor,
    input_node,
    knowledge_retriever,
    question_extractor,
    scoring_loop,
)
from .state import GraphState


def _route_after_audit(state: GraphState) -> str:
    """审核通过 → aggregator；不通过 → 回 scoring_loop（auditor 自身负责命中上限时切到通过）。"""
    return "aggregator" if state.get("audit_passed") else "scoring_loop"


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("input", input_node)
    g.add_node("question_extractor", question_extractor)
    g.add_node("knowledge_retriever", knowledge_retriever)
    g.add_node("scoring_loop", scoring_loop)
    g.add_node("auditor", auditor)
    g.add_node("aggregator", aggregator)

    g.add_edge(START, "input")
    g.add_edge("input", "question_extractor")
    g.add_edge("question_extractor", "knowledge_retriever")
    g.add_edge("knowledge_retriever", "scoring_loop")
    g.add_edge("scoring_loop", "auditor")

    g.add_conditional_edges(
        "auditor",
        _route_after_audit,
        {"scoring_loop": "scoring_loop", "aggregator": "aggregator"},
    )
    g.add_edge("aggregator", END)

    return g.compile()
