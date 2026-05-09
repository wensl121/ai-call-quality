"""聚合节点：合成最终质检 JSON。

直接消费 state 中由 scoring_loop 产出的 hot_words / business_words / should_say / should_not_say，
不再单独调 LLM。
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from call_quality.state import GraphState

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


def _summarize_cost(usage_records: list[dict[str, Any]]) -> dict[str, Any]:
    if not usage_records:
        return {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "by_node": {},
        }
    by_node: dict[str, dict[str, Any]] = {}
    total_in = total_out = 0
    total_cost = 0.0
    for r in usage_records:
        node = r.get("node", "unknown")
        slot = by_node.setdefault(
            node,
            {"calls": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
        )
        slot["calls"] += 1
        slot["input_tokens"] += int(r.get("input_tokens", 0))
        slot["output_tokens"] += int(r.get("output_tokens", 0))
        slot["estimated_cost_usd"] += float(r.get("estimated_cost_usd", 0.0))
        total_in += int(r.get("input_tokens", 0))
        total_out += int(r.get("output_tokens", 0))
        total_cost += float(r.get("estimated_cost_usd", 0.0))
    for slot in by_node.values():
        slot["estimated_cost_usd"] = round(slot["estimated_cost_usd"], 6)
    return {
        "total_calls": len(usage_records),
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_tokens": total_in + total_out,
        "estimated_cost_usd": round(total_cost, 6),
        "by_node": by_node,
    }


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
        "cost_summary": _summarize_cost(state.get("llm_usage", [])),
    }
    return {"result": result}
