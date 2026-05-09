"""LangSmith 评估器：把图的输出和 expected 做对比。

每个 evaluator 接收 dict(run, example)，返回 dict(key, score, comment)。
score 在 [0,1]：1=完全一致，0=完全错误。
"""
from __future__ import annotations

from typing import Any


def _pick_rule_ids(deductions: list[dict]) -> set[str]:
    return {str(d.get("rule_id")) for d in deductions or []}


def _pick_fatal_ids(triggers: list[dict]) -> set[str]:
    return {str(t.get("rule_id")) for t in triggers or []}


def _result(outputs: dict[str, Any]) -> dict[str, Any]:
    """图的最终输出在 'result' 字段下。"""
    if not outputs:
        return {}
    if "result" in outputs and isinstance(outputs["result"], dict):
        return outputs["result"]
    return outputs


def rule_match(outputs: dict, reference_outputs: dict) -> dict:
    """非致命扣分 rule_ids 的 Jaccard 相似度。"""
    actual = _pick_rule_ids(_result(outputs).get("deductions", []))
    expected = set(reference_outputs.get("deduction_rule_ids", []))
    if not actual and not expected:
        score = 1.0
    elif not actual or not expected:
        score = 0.0
    else:
        score = len(actual & expected) / len(actual | expected)
    return {
        "key": "rule_match",
        "score": score,
        "comment": f"actual={sorted(actual)} expected={sorted(expected)}",
    }


def fatal_correctness(outputs: dict, reference_outputs: dict) -> dict:
    """致命触发的精确匹配。误判致命会让客户得 0 分，必须严格对齐。"""
    actual = _pick_fatal_ids(_result(outputs).get("fatal_triggers", []))
    expected = set(reference_outputs.get("fatal_rule_ids", []))
    score = 1.0 if actual == expected else 0.0
    return {
        "key": "fatal_correctness",
        "score": score,
        "comment": f"actual={sorted(actual)} expected={sorted(expected)}",
    }


def score_in_range(outputs: dict, reference_outputs: dict) -> dict:
    """final_score 是否落在期望区间内。"""
    actual = int(_result(outputs).get("totals", {}).get("final_score", -1))
    lo = int(reference_outputs.get("final_score_min", 0))
    hi = int(reference_outputs.get("final_score_max", 100))
    score = 1.0 if lo <= actual <= hi else 0.0
    return {
        "key": "score_in_range",
        "score": score,
        "comment": f"actual={actual} expected=[{lo}, {hi}]",
    }


def review_match(outputs: dict, reference_outputs: dict) -> dict:
    """是否需要人工复核要与期望一致。"""
    actual = bool(_result(outputs).get("requires_human_review", False))
    expected = bool(reference_outputs.get("requires_human_review", False))
    score = 1.0 if actual == expected else 0.0
    return {
        "key": "review_match",
        "score": score,
        "comment": f"actual={actual} expected={expected}",
    }


ALL_EVALUATORS = [rule_match, fatal_correctness, score_in_range, review_match]
