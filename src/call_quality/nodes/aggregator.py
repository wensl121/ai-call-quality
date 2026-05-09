"""聚合节点：合成最终质检 JSON。

- 致命触发 → final_score=0
- 非致命 → 受 max_cap_in_rule 与 group_cap 双重约束累加
- 提取 hot_words / business_words
- 标记 requires_human_review（来自 auditor）
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from ..llm import chat_json
from ..state import GraphState

_HOTWORDS_PROMPT = (
    Path(__file__).parent.parent / "prompts" / "hot_words.txt"
).read_text(encoding="utf-8")


_DEFAULT_GROUPS = [
    {"group_id": "T1", "name": "合规风险事项", "cap": 100, "type": "fatal"},
    {"group_id": "T2", "name": "服务态度", "cap": 100, "type": "fatal"},
    {"group_id": "T3", "name": "服务标准性及服务技巧", "cap": 60, "type": "nonfatal"},
    {"group_id": "T4", "name": "业务水平", "cap": 40, "type": "nonfatal"},
]


def _summarize_groups(deductions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sums: Counter[str] = Counter()
    caps: dict[str, int] = {}
    for d in deductions:
        gid = d.get("group_id")
        if not gid:
            continue
        sums[gid] += int(d.get("subtotal", 0))
        caps[gid] = int(d.get("max_cap_in_group", caps.get(gid, 0)))

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


def _extract_hot_words(conversation: str) -> tuple[list[dict], list[dict]]:
    """LLM 提取 hot_words（高频信息词）和 business_words（业务差错相关词）。"""
    try:
        raw = chat_json(
            [
                {"role": "system", "content": _HOTWORDS_PROMPT},
                {"role": "user", "content": conversation},
            ]
        )
    except Exception:
        return [], []
    hot = raw.get("hot_words", []) if isinstance(raw, dict) else []
    biz = raw.get("business_words", []) if isinstance(raw, dict) else []
    return hot, biz


def aggregator(state: GraphState) -> GraphState:
    deductions = state.get("deductions", [])
    fatal_triggers = state.get("fatal_triggers", [])

    fatal_applied = bool(fatal_triggers)
    total_deducted = sum(int(d.get("subtotal", 0)) for d in deductions)
    final_score = 0 if fatal_applied else max(0, 100 - total_deducted)

    hot_words, business_words = _extract_hot_words(state["conversation"])

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
            "total_deducted": total_deducted if not fatal_applied else 0,
            "final_score": final_score,
            "fatal_applied": fatal_applied,
        },
        "hot_words": hot_words,
        "business_words": business_words,
        "requires_human_review": state.get("requires_human_review", False),
        "review_reason": state.get("review_reason"),
    }
    return {"result": result}
