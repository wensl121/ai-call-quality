"""聚合节点：合成最终质检 JSON。

直接消费 state 中由 scoring_loop 产出的 hot_words / business_words / should_say / should_not_say，
不再单独调 LLM。
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from ..state import GraphState

_DEFAULT_GROUPS = [
    {"group_id": "T1", "name": "合规风险事项", "cap": 100, "type": "fatal"},
    {"group_id": "T2", "name": "服务态度", "cap": 100, "type": "fatal"},
    {"group_id": "T3", "name": "服务标准性及服务技巧", "cap": 60, "type": "nonfatal"},
    {"group_id": "T4", "name": "业务水平", "cap": 40, "type": "nonfatal"},
]


def _summarize_groups(deductions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sums: Counter[str] = Counter()
    for d in deductions:
        gid = d.get("group_id")
        if not gid:
            continue
        sums[gid] += int(d.get("subtotal", 0))

    summary = []
    for g in _DEFAULT_GROUPS:
        if g["type"] == "fatal":
            continue
        gid = g["group_id"]
        summary.append(
            {
                "group_id": gid,
                "deducted": min(sums.get(gid, 0), g["cap"]),
                "cap_applied": g["cap"],
            }
        )
    return summary


def _sorted_words(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(words, key=lambda w: int(w.get("count", 0)), reverse=True)


def aggregator(state: GraphState) -> GraphState:
    deductions = state.get("deductions", [])
    fatal_triggers = state.get("fatal_triggers", [])

    fatal_applied = bool(fatal_triggers)
    total_deducted = sum(int(d.get("subtotal", 0)) for d in deductions)
    final_score = 0 if fatal_applied else max(0, 100 - total_deducted)

    result = {
        "call_id": state["call_id"],
        "call_type": state["call_type"],
        "template_used": state.get("template_used", "voice_template"),
        "caps": {"overall_cap": 100, "groups": _DEFAULT_GROUPS},
        "fatal_triggers": fatal_triggers,
        "deductions": deductions,
        "group_deduction_summary": _summarize_groups(deductions),
        "totals": {
            "overall_cap": 100,
            "total_deducted": 0 if fatal_applied else total_deducted,
            "final_score": final_score,
            "fatal_applied": fatal_applied,
        },
        "hot_words": _sorted_words(state.get("hot_words", [])),
        "business_words": _sorted_words(state.get("business_words", [])),
        "should_say": state.get("should_say", []),
        "should_not_say": state.get("should_not_say", []),
        "requires_human_review": state.get("requires_human_review", False),
        "review_reason": state.get("review_reason"),
    }
    return {"result": result}
