"""单规则评分节点：每个 rule_scorer 实例评估一条规则。

被 Send 派发，输入是 dispatcher 构造的 payload（不是完整 GraphState）。
返回的 deductions / fatal_triggers 通过 list_add_or_reset reducer 累加到 GraphState。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import get_chat_model
from ..schemas import RuleScoringOutput

_PROMPT = (Path(__file__).parent.parent / "prompts" / "score_rule.txt").read_text(encoding="utf-8")


def rule_scorer(payload: dict[str, Any]) -> dict[str, Any]:
    user_payload = {
        "conversation": payload["conversation"],
        "rule": payload["rule"],
        "qa_pairs": payload.get("qa_pairs", []),
        "previous_audit_issues": payload.get("previous_audit_issues", []),
    }
    llm = get_chat_model().with_structured_output(RuleScoringOutput, method="function_calling")
    result: RuleScoringOutput = llm.invoke(
        [SystemMessage(_PROMPT), HumanMessage(json.dumps(user_payload, ensure_ascii=False))]
    )
    return {
        "deductions": [d.model_dump() for d in result.deductions],
        "fatal_triggers": [t.model_dump() for t in result.fatal_triggers],
    }
