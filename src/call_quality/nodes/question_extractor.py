"""问题提取节点：从对话文本中抽取客户问题。"""
from __future__ import annotations

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import get_chat_model
from ..schemas import ExtractedQuestions
from ..state import GraphState

_PROMPT = (Path(__file__).parent.parent / "prompts" / "extract_questions.txt").read_text(
    encoding="utf-8"
)


def question_extractor(state: GraphState) -> GraphState:
    llm = get_chat_model().with_structured_output(ExtractedQuestions, method="function_calling")
    result: ExtractedQuestions = llm.invoke(
        [SystemMessage(_PROMPT), HumanMessage(state["conversation"])]
    )
    return {"questions": [q.model_dump() for q in result.questions]}
