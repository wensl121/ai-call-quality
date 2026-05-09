"""知识检索节点：为每个问题查 KB，并尝试从对话里抽取客服的对应回答。"""
from __future__ import annotations

from call_quality import kb
from call_quality.state import GraphState


def knowledge_retriever(state: GraphState) -> GraphState:
    qa_pairs: list[dict] = []
    for q in state.get("questions", []):
        hits = kb.search(q.get("question_text", ""))
        top = hits[0] if hits else None
        qa_pairs.append(
            {
                "timestamp": q.get("timestamp"),
                "question_text": q.get("question_text"),
                "kb_answer": top["answer"] if top else None,
                "kb_title": top["title"] if top else None,
                "agent_answer": q.get("agent_answer"),
            }
        )
    return {"qa_pairs": qa_pairs}
