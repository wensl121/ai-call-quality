"""审核节点：检查打分合理性。"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import invoke_structured
from ..schemas import AuditOutput
from ..state import GraphState

_PROMPT = (Path(__file__).parent.parent / "prompts" / "audit.txt").read_text(encoding="utf-8")


def _max_loops() -> int:
    return int(os.getenv("MAX_SCORING_LOOPS", "3"))


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
        if gid:
            sums[gid] += int(d.get("subtotal", 0))
    return [
        {
            "group_id": g["group_id"],
            "deducted": min(sums.get(g["group_id"], 0), g["cap"]),
            "cap_applied": g["cap"],
        }
        for g in _DEFAULT_GROUPS
        if g["type"] != "fatal"
    ]


def _build_main_result(state: GraphState) -> dict[str, Any]:
    deductions = state.get("deductions", [])
    fatal_triggers = state.get("fatal_triggers", [])
    fatal_applied = bool(fatal_triggers)
    total_deducted = sum(int(d.get("subtotal", 0)) for d in deductions)
    return {
        "fatal_triggers": fatal_triggers,
        "deductions": deductions,
        "group_deduction_summary": _summarize_groups(deductions),
        "totals": {
            "overall_cap": 100,
            "total_deducted": 0 if fatal_applied else total_deducted,
            "final_score": 0 if fatal_applied else max(0, 100 - total_deducted),
            "fatal_applied": fatal_applied,
        },
    }


def auditor(state: GraphState) -> GraphState:
    attempts = state.get("audit_attempts", 0) + 1

    payload = {
        "conversation": state["conversation"],
        "rules_json": state["rules_json"],
        "main_result": _build_main_result(state),
    }
    verdict, usage = invoke_structured(
        AuditOutput,
        [SystemMessage(_PROMPT), HumanMessage(json.dumps(payload, ensure_ascii=False))],
        node_name="auditor",
    )

    issues = [i.model_dump() for i in verdict.issues]

    if not verdict.passed and attempts >= _max_loops():
        return {
            "audit_passed": True,
            "audit_attempts": attempts,
            "audit_reasons": verdict.reasons,
            "audit_issues": issues,
            "requires_human_review": True,
            "review_reason": (
                f"审核连续 {attempts} 次未通过：{'; '.join(verdict.reasons) or '存在 issues'}"
            ),
            "llm_usage": [usage],
        }

    return {
        "audit_passed": verdict.passed,
        "audit_attempts": attempts,
        "audit_reasons": verdict.reasons,
        "audit_issues": issues,
        "llm_usage": [usage],
    }
