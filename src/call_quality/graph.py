"""LangGraph 主图编排。

5 个顶层节点：
    input → question_extractor → knowledge_retriever → scoring_with_audit → aggregator

`scoring_with_audit` 是一个子图，内部包含 scoring_loop ⇄ auditor 的迭代逻辑。
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from call_quality.nodes import aggregator, input_node, knowledge_retriever, question_extractor
from call_quality.scoring_subgraph import build_scoring_subgraph
from call_quality.state import GraphState


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("input", input_node)
    g.add_node("question_extractor", question_extractor)
    g.add_node("knowledge_retriever", knowledge_retriever)
    g.add_node("scoring_with_audit", build_scoring_subgraph())
    g.add_node("aggregator", aggregator)

    g.add_edge(START, "input")
    g.add_edge("input", "question_extractor")
    g.add_edge("question_extractor", "knowledge_retriever")
    g.add_edge("knowledge_retriever", "scoring_with_audit")
    g.add_edge("scoring_with_audit", "aggregator")
    g.add_edge("aggregator", END)

    return g.compile()


graph = build_graph()
