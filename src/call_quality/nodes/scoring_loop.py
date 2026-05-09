"""规则打分节点。

输入：conversation + rules_json + qa_pairs（含 KB 答案） + 上一轮审核 issues
输出：deductions, fatal_triggers, hot_words, business_words, should_say, should_not_say
"""
from __future__ import annotations

import json
from pathlib import Path

from ..llm import chat_json
from ..state import GraphState

_PROMPT = (Path(__file__).parent.parent / "prompts" / "score.txt").read_text(encoding="utf-8")


def scoring_loop(state: GraphState) -> GraphState:
    payload = {
        "call_type": state.get("call_type"),
        "conversation": state["conversation"],
        "rules_json": state["rules_json"],
        "qa_pairs": state.get("qa_pairs", []),
        "previous_audit_issues": state.get("audit_issues", []),
    }
    raw = chat_json(
        [
            {"role": "system", "content": _PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
    )
    return {
        "deductions": raw.get("deductions", []),
        "fatal_triggers": raw.get("fatal_triggers", []),
        "hot_words": raw.get("hot_words", []),
        "business_words": raw.get("business_words", []),
        "should_say": raw.get("should_say", []),
        "should_not_say": raw.get("should_not_say", []),
    }
