"""规则打分节点。

输入：conversation + rules_json + qa_pairs（含 KB 答案）
输出：deductions, fatal_triggers

实现策略：
1. 把规则 + 对话 + QA 对一起塞给 LLM，让它返回结构化扣分结果。
2. 若任意 fatal 规则命中，写入 fatal_triggers。
3. 客服回答与 KB 答案语义不符 → 计入 rule_id=17（业务差错）。
"""
from __future__ import annotations

import json
from pathlib import Path

from ..llm import chat_json
from ..state import GraphState

_PROMPT = (Path(__file__).parent.parent / "prompts" / "score.txt").read_text(encoding="utf-8")


def scoring_loop(state: GraphState) -> GraphState:
    payload = {
        "conversation": state["conversation"],
        "rules_json": state["rules_json"],
        "qa_pairs": state.get("qa_pairs", []),
        "previous_audit_reason": state.get("audit_reason"),
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
    }
