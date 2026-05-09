"""问题提取节点：从对话文本中抽取客户问题。"""
from __future__ import annotations

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import invoke_structured
from ..schemas import ExtractedQuestions
from ..state import GraphState

_PROMPT = (Path(__file__).parent.parent / "prompts" / "extract_questions.txt").read_text(
    encoding="utf-8"
)


def question_extractor(state: GraphState) -> GraphState:
    parsed, usage = invoke_structured(
        ExtractedQuestions,
        [SystemMessage(_PROMPT), HumanMessage(state["conversation"])],
        node_name="question_extractor",
    )
    return {
        "questions": [q.model_dump() for q in parsed.questions],
        "llm_usage": [usage],
    }
