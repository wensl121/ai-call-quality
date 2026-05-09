"""审核节点：检查打分合理性。

不通过 → audit_passed=False，audit_attempts+1，回到 scoring_loop。
通过 / 达到上限 → audit_passed=True，进入 aggregator（达到上限时 aggregator 会标记人工复核）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from ..llm import chat_json
from ..state import GraphState

_PROMPT = (Path(__file__).parent.parent / "prompts" / "audit.txt").read_text(encoding="utf-8")


def _max_loops() -> int:
    return int(os.getenv("MAX_SCORING_LOOPS", "3"))


def auditor(state: GraphState) -> GraphState:
    attempts = state.get("audit_attempts", 0) + 1

    payload = {
        "conversation": state["conversation"],
        "rules_json": state["rules_json"],
        "deductions": state.get("deductions", []),
        "fatal_triggers": state.get("fatal_triggers", []),
    }
    verdict = chat_json(
        [
            {"role": "system", "content": _PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
    )
    passed = bool(verdict.get("passed", False))
    reason = verdict.get("reason", "")

    if not passed and attempts >= _max_loops():
        return {
            "audit_passed": True,
            "audit_attempts": attempts,
            "audit_reason": reason,
            "requires_human_review": True,
            "review_reason": f"审核连续 {attempts} 次未通过：{reason}",
        }

    return {
        "audit_passed": passed,
        "audit_attempts": attempts,
        "audit_reason": reason,
    }
