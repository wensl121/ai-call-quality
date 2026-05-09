"""冒烟测试：不打 LLM，验证图能 compile 且聚合逻辑正确。"""
from __future__ import annotations


def test_graph_compiles():
    from call_quality import build_graph

    graph = build_graph()
    assert graph is not None


def test_aggregator_fatal_zeroes_score():
    import importlib

    agg_mod = importlib.import_module("call_quality.nodes.aggregator")

    state = {
        "call_id": "X",
        "call_type": "voice",
        "conversation": "",
        "fatal_triggers": [
            {"rule_id": "1", "scenario_id": 1, "timestamp": "00:00:01", "text": "..."}
        ],
        "deductions": [],
        "hot_words": [],
        "business_words": [],
    }
    out = agg_mod.aggregator(state)["result"]
    assert out["totals"]["final_score"] == 0
    assert out["totals"]["fatal_applied"] is True


def test_aggregator_caps_group_deduction():
    import importlib

    agg_mod = importlib.import_module("call_quality.nodes.aggregator")
    state = {
        "call_id": "X",
        "call_type": "voice",
        "conversation": "",
        "fatal_triggers": [],
        "deductions": [
            {
                "rule_id": "7",
                "group_id": "T3",
                "severity": "nonfatal",
                "per_deduct": 2,
                "max_cap_in_rule": 10,
                "max_cap_in_group": 60,
                "count": 80,
                "subtotal": 80,
                "evidence": [],
            }
        ],
        "hot_words": [],
        "business_words": [],
    }
    out = agg_mod.aggregator(state)["result"]
    t3 = next(g for g in out["group_deduction_summary"] if g["group_id"] == "T3")
    assert t3["deducted"] == 60


def test_hot_words_sorted_desc():
    import importlib

    agg_mod = importlib.import_module("call_quality.nodes.aggregator")
    state = {
        "call_id": "X",
        "call_type": "voice",
        "conversation": "",
        "fatal_triggers": [],
        "deductions": [],
        "hot_words": [
            {"word": "A", "count": 1},
            {"word": "B", "count": 5},
            {"word": "C", "count": 3},
        ],
        "business_words": [],
    }
    out = agg_mod.aggregator(state)["result"]
    assert [w["word"] for w in out["hot_words"]] == ["B", "C", "A"]
