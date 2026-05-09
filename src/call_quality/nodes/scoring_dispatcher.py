"""打分派发节点。

职责：
1. 进入新一轮打分时，清空上轮的 deductions / fatal_triggers（用 RESET 信号）。
2. 通过 conditional edge 的 fan_out 函数，按规则数量 + 提取节点派发 Send。
"""
from __future__ import annotations

from typing import Any

from langgraph.types import Send

from call_quality.state import RESET, GraphState


def scoring_dispatcher(state: GraphState) -> dict[str, Any]:
    return {
        "deductions": RESET,
        "fatal_triggers": RESET,
    }


def fan_out(state: GraphState) -> list[Send]:
    """每条规则一个 rule_scorer Send，再额外派一个 extraction Send。

    所有 Send 完成后，LangGraph 自动在 auditor（共同下游）汇合。
    """
    base = {
        "conversation": state["conversation"],
        "qa_pairs": state.get("qa_pairs", []),
        "previous_audit_issues": state.get("audit_issues", []),
    }
    sends: list[Send] = [
        Send("rule_scorer", {**base, "rule": rule}) for rule in state["rules_json"]
    ]
    sends.append(Send("extraction_node", {"conversation": state["conversation"]}))
    return sends
