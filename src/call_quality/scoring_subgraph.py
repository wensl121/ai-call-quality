"""打分-审核子图（带 Send 并行 fan-out）。

流程：
    START → scoring_dispatcher  (清空上一轮 deductions / fatal_triggers)
              ↓ Send 派发
            ┌──────────────────────────┬──────────────────┐
        rule_scorer × N (并行 per rule)   extraction_node (并行)
            └──────────────┬───────────┴──────────────────┘
                           ↓ 自动 fan-in
                        auditor → END | back to scoring_dispatcher
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from call_quality.nodes.auditor import auditor
from call_quality.nodes.extraction import extraction_node
from call_quality.nodes.rule_scorer import rule_scorer
from call_quality.nodes.scoring_dispatcher import fan_out, scoring_dispatcher
from call_quality.state import GraphState


def _route_after_audit(state: GraphState) -> str:
    return END if state.get("audit_passed") else "scoring_dispatcher"


def build_scoring_subgraph():
    g = StateGraph(GraphState)
    g.add_node("scoring_dispatcher", scoring_dispatcher)
    g.add_node("rule_scorer", rule_scorer)
    g.add_node("extraction_node", extraction_node)
    g.add_node("auditor", auditor)

    g.add_edge(START, "scoring_dispatcher")
    g.add_conditional_edges(
        "scoring_dispatcher",
        fan_out,
        ["rule_scorer", "extraction_node"],
    )
    # 所有并行 Send 完成后自动汇合到 auditor
    g.add_edge("rule_scorer", "auditor")
    g.add_edge("extraction_node", "auditor")

    g.add_conditional_edges(
        "auditor",
        _route_after_audit,
        {"scoring_dispatcher": "scoring_dispatcher", END: END},
    )
    return g.compile()
