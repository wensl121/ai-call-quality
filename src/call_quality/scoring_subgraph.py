"""打分-审核子图。

把 scoring_loop ⇄ auditor 这一闭环抽成独立子图：
- 主图只见到一个节点 `scoring_with_audit`
- 子图自身负责"打分 → 审核 → 不通过则回打分"，并由 auditor 在达到上限时
  强制 passed=True 并标记 requires_human_review

子图复用同一个 GraphState（TypedDict 键自动对齐），父子状态透明合并。
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes.auditor import auditor
from .nodes.scoring_loop import scoring_loop
from .state import GraphState


def _route_after_audit(state: GraphState) -> str:
    return END if state.get("audit_passed") else "scoring_loop"


def build_scoring_subgraph():
    g = StateGraph(GraphState)
    g.add_node("scoring_loop", scoring_loop)
    g.add_node("auditor", auditor)

    g.add_edge(START, "scoring_loop")
    g.add_edge("scoring_loop", "auditor")
    g.add_conditional_edges(
        "auditor",
        _route_after_audit,
        {"scoring_loop": "scoring_loop", END: END},
    )
    return g.compile()
