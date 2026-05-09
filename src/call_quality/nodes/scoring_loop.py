"""规则打分节点。

输入：conversation + rules_json + qa_pairs（含 KB 答案） + 上一轮审核 issues
输出：deductions, fatal_triggers, hot_words, business_words, should_say, should_not_say
"""
from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import get_chat_model
from ..schemas import ScoringOutput
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
    llm = get_chat_model().with_structured_output(ScoringOutput, method="function_calling")
    result: ScoringOutput = llm.invoke(
        [SystemMessage(_PROMPT), HumanMessage(json.dumps(payload, ensure_ascii=False))]
    )
    return {
        "deductions": [d.model_dump() for d in result.deductions],
        "fatal_triggers": [t.model_dump() for t in result.fatal_triggers],
        "hot_words": [w.model_dump() for w in result.hot_words],
        "business_words": [w.model_dump() for w in result.business_words],
        "should_say": result.should_say,
        "should_not_say": result.should_not_say,
    }
