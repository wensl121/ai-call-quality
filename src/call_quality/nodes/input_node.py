"""输入节点：透传输入并初始化循环计数。

同时对 conversation 做 PII 脱敏（手机号 / 身份证 / 银行卡 / 邮箱 / 详细地址 → 占位符），
所有下游节点（含 LLM 调用与最终 evidence）只看到脱敏版。
"""
from __future__ import annotations

from ..middleware import redact_pii
from ..state import GraphState


def input_node(state: GraphState) -> GraphState:
    return {
        "call_id": state["call_id"],
        "call_type": state["call_type"],
        "conversation": redact_pii(state["conversation"]),
        "rules_json": state["rules_json"],
        "template_used": state.get("template_used", "voice_template"),
        "audit_attempts": 0,
    }
