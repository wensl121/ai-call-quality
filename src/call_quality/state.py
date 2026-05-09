"""LangGraph state 定义。

state 在节点之间累积；用 TypedDict 让 LangGraph 能正确做浅合并。
"""
from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    # === 输入 ===
    call_id: str
    call_type: str
    conversation: str
    rules_json: list[dict[str, Any]]
    template_used: str

    # === 中间产物 ===
    questions: list[dict[str, Any]]
    qa_pairs: list[dict[str, Any]]

    # === 评分 ===
    deductions: list[dict[str, Any]]
    fatal_triggers: list[dict[str, Any]]

    # === 审核 ===
    audit_passed: bool
    audit_reason: str
    audit_attempts: int

    # === 最终输出 ===
    result: dict[str, Any]
    requires_human_review: bool
    review_reason: str
