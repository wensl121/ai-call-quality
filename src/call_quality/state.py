"""LangGraph state 定义。

支持并行 fan-out：deductions / fatal_triggers 用 reducer 累加多个 rule_scorer 的输出，
重打分循环开头由 dispatcher 写入 RESET 信号清空。
"""
from __future__ import annotations

from typing import Annotated, Any, TypedDict


class _Reset:
    """Sentinel value: signals the reducer to clear the field."""

    _instance: "_Reset | None" = None

    def __new__(cls) -> "_Reset":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<RESET>"


RESET = _Reset()


def list_add_or_reset(left: Any, right: Any) -> list:
    """Reducer: extend list; right==RESET resets to []."""
    if right is RESET:
        return []
    if not isinstance(right, list):
        return list(left or [])
    return list(left or []) + right


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

    # === 评分（并行写入，需要 reducer） ===
    deductions: Annotated[list[dict[str, Any]], list_add_or_reset]
    fatal_triggers: Annotated[list[dict[str, Any]], list_add_or_reset]

    # === 提取（单节点写入，无需 reducer） ===
    hot_words: list[dict[str, Any]]
    business_words: list[dict[str, Any]]
    should_say: list[str]
    should_not_say: list[str]

    # === 审核 ===
    audit_passed: bool
    audit_reasons: list[str]
    audit_issues: list[dict[str, Any]]
    audit_attempts: int

    # === 最终输出 ===
    result: dict[str, Any]
    requires_human_review: bool
    review_reason: str
