"""单规则评分节点：每个 rule_scorer 实例评估一条规则。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import invoke_structured
from ..schemas import RuleScoringOutput

_PROMPT = (Path(__file__).parent.parent / "prompts" / "score_rule.txt").read_text(encoding="utf-8")


def rule_scorer(payload: dict[str, Any]) -> dict[str, Any]:
    user_payload = {
        "conversation": payload["conversation"],
        "rule": payload["rule"],
        "qa_pairs": payload.get("qa_pairs", []),
        "previous_audit_issues": payload.get("previous_audit_issues", []),
    }
    parsed, usage = invoke_structured(
        RuleScoringOutput,
        [SystemMessage(_PROMPT), HumanMessage(json.dumps(user_payload, ensure_ascii=False))],
        node_name="rule_scorer",
    )
    return {
        "deductions": [d.model_dump() for d in parsed.deductions],
        "fatal_triggers": [t.model_dump() for t in parsed.fatal_triggers],
        "llm_usage": [usage],
    }
