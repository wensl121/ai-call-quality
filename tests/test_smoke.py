"""冒烟测试：不打 LLM，验证图能 compile 且节点可导入。"""
from __future__ import annotations


def test_graph_compiles():
    from call_quality import build_graph

    graph = build_graph()
    assert graph is not None


def test_aggregator_fatal_zeroes_score():
    from call_quality.nodes.aggregator import aggregator
    import call_quality.nodes.aggregator as agg_mod

    agg_mod._extract_hot_words = lambda _conv: ([], [])

    state = {
        "call_id": "X",
        "call_type": "voice",
        "conversation": "",
        "fatal_triggers": [
            {"rule_id": "1", "scenario_id": 1, "timestamp": "00:00:01", "text": "..."}
        ],
        "deductions": [],
    }
    out = aggregator(state)["result"]
    assert out["totals"]["final_score"] == 0
    assert out["totals"]["fatal_applied"] is True


def test_aggregator_caps_group_deduction():
    from call_quality.nodes import aggregator as agg_mod

    agg_mod._extract_hot_words = lambda _conv: ([], [])
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
    }
    out = agg_mod.aggregator(state)["result"]
    t3 = next(g for g in out["group_deduction_summary"] if g["group_id"] == "T3")
    assert t3["deducted"] == 60
