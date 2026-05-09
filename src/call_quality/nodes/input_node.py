"""输入节点：透传输入并初始化循环计数。"""
from __future__ import annotations

from ..state import GraphState


def input_node(state: GraphState) -> GraphState:
    return {
        "call_id": state["call_id"],
        "call_type": state["call_type"],
        "conversation": state["conversation"],
        "rules_json": state["rules_json"],
        "template_used": state.get("template_used", "voice_template"),
        "audit_attempts": 0,
    }
