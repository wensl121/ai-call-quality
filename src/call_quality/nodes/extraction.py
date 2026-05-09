"""提取节点：一次性抽 hot_words / business_words / should_say / should_not_say。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm import invoke_structured
from ..schemas import ExtractionOutput

_PROMPT = (Path(__file__).parent.parent / "prompts" / "extract_words.txt").read_text(
    encoding="utf-8"
)


def extraction_node(payload: dict[str, Any]) -> dict[str, Any]:
    parsed, usage = invoke_structured(
        ExtractionOutput,
        [SystemMessage(_PROMPT), HumanMessage(payload["conversation"])],
        node_name="extraction_node",
    )
    return {
        "hot_words": [w.model_dump() for w in parsed.hot_words],
        "business_words": [w.model_dump() for w in parsed.business_words],
        "should_say": parsed.should_say,
        "should_not_say": parsed.should_not_say,
        "llm_usage": [usage],
    }
