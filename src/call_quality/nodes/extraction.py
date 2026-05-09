"""提取节点：一次性抽 hot_words / business_words / should_say / should_not_say。

与 rule_scorer 并行运行（同样由 Send 派发），不需要规则上下文，只看对话本身。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import get_chat_model
from ..schemas import ExtractionOutput

_PROMPT = (Path(__file__).parent.parent / "prompts" / "extract_words.txt").read_text(
    encoding="utf-8"
)


def extraction_node(payload: dict[str, Any]) -> dict[str, Any]:
    llm = get_chat_model().with_structured_output(ExtractionOutput, method="function_calling")
    result: ExtractionOutput = llm.invoke(
        [SystemMessage(_PROMPT), HumanMessage(payload["conversation"])]
    )
    return {
        "hot_words": [w.model_dump() for w in result.hot_words],
        "business_words": [w.model_dump() for w in result.business_words],
        "should_say": result.should_say,
        "should_not_say": result.should_not_say,
    }
