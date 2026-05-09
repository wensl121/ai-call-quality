"""冒烟测试：不打 LLM，验证图能 compile 且聚合逻辑正确。"""
from __future__ import annotations


def test_graph_compiles():
    from call_quality import build_graph

    graph = build_graph()
    assert graph is not None


def test_scoring_subgraph_compiles():
    from call_quality.scoring_subgraph import build_scoring_subgraph

    sub = build_scoring_subgraph()
    assert sub is not None


def test_pii_redaction_phone_id_email():
    from call_quality.middleware import redact_pii

    text = (
        "客服张三，手机号 13602828838，"
        "身份证 110101199001011234，邮箱 abc@example.com"
    )
    out = redact_pii(text)
    assert "13602828838" not in out
    assert "110101199001011234" not in out
    assert "abc@example.com" not in out
    assert "[PHONE]" in out
    assert "[ID_CARD]" in out
    assert "[EMAIL]" in out


def test_pii_redaction_address():
    from call_quality.middleware import redact_pii

    text = "客户地址在广州市番禺区新联路40号703房"
    out = redact_pii(text)
    assert "新联路" not in out
    assert "[ADDRESS]" in out


def test_pii_redaction_passthrough_safe_text():
    from call_quality.middleware import redact_pii

    text = "您好，请问有什么可以帮您？"
    assert redact_pii(text) == text


def test_aggregator_cost_summary():
    import importlib

    agg_mod = importlib.import_module("call_quality.nodes.aggregator")
    state = {
        "call_id": "X",
        "call_type": "voice",
        "conversation": "",
        "fatal_triggers": [],
        "deductions": [],
        "hot_words": [],
        "business_words": [],
        "llm_usage": [
            {
                "node": "rule_scorer",
                "model": "deepseek-chat",
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
                "estimated_cost_usd": 0.000028,
            },
            {
                "node": "rule_scorer",
                "model": "deepseek-chat",
                "input_tokens": 200,
                "output_tokens": 70,
                "total_tokens": 270,
                "estimated_cost_usd": 0.000048,
            },
            {
                "node": "auditor",
                "model": "deepseek-chat",
                "input_tokens": 500,
                "output_tokens": 100,
                "total_tokens": 600,
                "estimated_cost_usd": 0.000098,
            },
        ],
    }
    out = agg_mod.aggregator(state)["result"]
    cs = out["cost_summary"]
    assert cs["total_calls"] == 3
    assert cs["total_input_tokens"] == 800
    assert cs["total_output_tokens"] == 220
    assert cs["total_tokens"] == 1020
    assert cs["by_node"]["rule_scorer"]["calls"] == 2
    assert cs["by_node"]["auditor"]["calls"] == 1


def test_list_add_or_reset_reducer():
    from call_quality.state import RESET, list_add_or_reset

    assert list_add_or_reset([], [1, 2]) == [1, 2]
    assert list_add_or_reset([1, 2], [3]) == [1, 2, 3]
    assert list_add_or_reset([1, 2, 3], RESET) == []
    assert list_add_or_reset(None, [1]) == [1]
    assert list_add_or_reset([1], "garbage") == [1]


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
        "llm_usage": [],
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
        "llm_usage": [],
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
        "llm_usage": [],
    }
    out = agg_mod.aggregator(state)["result"]
    assert [w["word"] for w in out["hot_words"]] == ["B", "C", "A"]
