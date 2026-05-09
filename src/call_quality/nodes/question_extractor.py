"""问题提取节点：从对话文本中抽取客户问题。"""
from __future__ import annotations

from pathlib import Path

from ..llm import chat_json
from ..state import GraphState

_PROMPT = (Path(__file__).parent.parent / "prompts" / "extract_questions.txt").read_text(
    encoding="utf-8"
)


def question_extractor(state: GraphState) -> GraphState:
    conversation = state["conversation"]
    questions = chat_json(
        [
            {"role": "system", "content": _PROMPT},
            {"role": "user", "content": conversation},
        ]
    )
    if isinstance(questions, dict):
        questions = questions.get("questions", [])
    return {"questions": questions or []}
