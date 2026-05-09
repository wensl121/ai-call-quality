"""黄金数据集：手工构造的质检例子，每个例子有期望输出，用于回归测试。

数据集设计原则：
- 每条 example 测试一个明确的行为类别
- inputs 与 GraphState 输入字段对齐（直接喂 graph.invoke 即可）
- expected 用宽松断言：rule_ids 集合、score 区间、是否人工复核
"""
from __future__ import annotations

# ---- 标准规则集（跨例子复用）----------------------------------------------------

STANDARD_RULES = [
    {
        "rule_id": 1,
        "deduction_mode": {
            "description": "出现则本任务得分为0",
            "max_deduction": 1000,
            "deduct_points": 1000,
        },
        "scenarios": [
            {
                "check_scope": "客服说的话",
                "type": "关键词检测",
                "scenario_id": 1,
                "required_checks": {
                    "type": "不应该说",
                    "content": "保证收益；保本；稳赚；包赚；肯定包赚；零风险高收益",
                },
            }
        ],
    },
    {
        "rule_id": 4,
        "deduction_mode": {
            "description": "出现则本任务得分为0",
            "max_deduction": 1000,
            "deduct_points": 1000,
        },
        "scenarios": [
            {
                "check_scope": "客服说的话",
                "type": "语义匹配检测",
                "scenario_id": 5,
                "required_checks": {
                    "type": "不应该说",
                    "content": "发表个人对市场或行业未来走势的预测",
                },
            }
        ],
    },
    {
        "rule_id": 7,
        "deduction_mode": {
            "description": "每出现一处扣2分，最多10分",
            "max_deduction": 10,
            "deduct_points": 2,
        },
        "scenarios": [
            {
                "check_scope": "客服说的话",
                "type": "语义匹配检测",
                "scenario_id": 11,
                "required_checks": {
                    "type": "应该说",
                    "content": "标准开场语：您好，招商基金，请问有什么可以帮您？",
                },
            },
            {
                "check_scope": "客服说的话",
                "type": "语义匹配检测",
                "scenario_id": 12,
                "required_checks": {
                    "type": "应该说",
                    "content": "结束前应询问：请问还有什么可以帮到您？",
                },
            },
        ],
    },
    {
        "rule_id": 17,
        "deduction_mode": {
            "description": "答非所问/与知识库不符",
            "max_deduction": 10,
            "deduct_points": 2,
        },
        "scenarios": [
            {
                "check_scope": "客服说的话",
                "type": "语义匹配检测",
                "scenario_id": 0,
                "required_checks": {
                    "type": "应该说",
                    "content": "客服回答应与知识库 kb_answer 一致",
                },
            }
        ],
    },
]


# ---- 黄金例子 ---------------------------------------------------------------

GOLDEN_EXAMPLES = [
    {
        "name": "clean_compliant",
        "description": "客服话术合规、问候/结束完整、回答与 KB 一致",
        "inputs": {
            "call_id": "GOLD-001",
            "call_type": "voice",
            "template_used": "voice_template",
            "conversation": (
                "00:00:00 客服：您好，招商基金，请问有什么可以帮您？\n"
                "00:00:08 客户：你好，我想咨询一下中证白酒指数基金 A 类怎么赎回？\n"
                "00:00:18 客服：好的，中证白酒指数 A 类应在原购买渠道发起赎回，T+1 确认份额，"
                "通常 T+2 至 T+4 到账。\n"
                "00:00:35 客户：好的明白了。\n"
                "00:00:38 客服：请问还有什么可以帮到您？\n"
                "00:00:42 客户：没有了。\n"
                "00:00:44 客服：感谢您的来电，祝您生活愉快，再见。"
            ),
            "rules_json": STANDARD_RULES,
        },
        "expected": {
            "deduction_rule_ids": [],
            "fatal_rule_ids": [],
            "final_score_min": 96,
            "final_score_max": 100,
            "requires_human_review": False,
        },
    },
    {
        "name": "missing_greeting_and_close",
        "description": "未使用标准开场语 + 未询问还有问题；不应触发任何 fatal",
        "inputs": {
            "call_id": "GOLD-002",
            "call_type": "voice",
            "template_used": "voice_template",
            "conversation": (
                "00:00:00 客服：8199 号为您服务。\n"
                "00:00:05 客户：你好，我有一个基金想赎回。\n"
                "00:00:10 客服：好的，请告诉我基金代码。\n"
                "00:00:15 客户：招商中证白酒 A。\n"
                "00:00:18 客服：好的，您可以通过原购买渠道赎回。\n"
                "00:00:30 客户：明白了。\n"
                "00:00:32 客服：好的，那就不打扰您了，再见。"
            ),
            "rules_json": STANDARD_RULES,
        },
        "expected": {
            "deduction_rule_ids": ["7"],
            "fatal_rule_ids": [],
            "final_score_min": 92,
            "final_score_max": 98,
            "requires_human_review": False,
        },
    },
    {
        "name": "fatal_guarantee_returns",
        "description": "客服说『保证收益』触发 rule 1 致命",
        "inputs": {
            "call_id": "GOLD-003",
            "call_type": "voice",
            "template_used": "voice_template",
            "conversation": (
                "00:00:00 客服：您好，招商基金，请问有什么可以帮您？\n"
                "00:00:08 客户：你们这个产品收益怎么样？\n"
                "00:00:12 客服：您放心，我们这个产品保证收益，零风险高收益，"
                "肯定包赚的。\n"
                "00:00:25 客户：那行，我买。\n"
                "00:00:28 客服：好的，请问还有什么可以帮到您？\n"
                "00:00:32 客户：没有了。\n"
                "00:00:34 客服：感谢您的来电，祝您生活愉快，再见。"
            ),
            "rules_json": STANDARD_RULES,
        },
        "expected": {
            "deduction_rule_ids": [],
            "fatal_rule_ids": ["1"],
            "final_score_min": 0,
            "final_score_max": 0,
            "requires_human_review": False,
        },
    },
    {
        "name": "kb_mismatch_answer",
        "description": "客户问基金赎回，客服答非所问 → rule 17 命中",
        "inputs": {
            "call_id": "GOLD-004",
            "call_type": "voice",
            "template_used": "voice_template",
            "conversation": (
                "00:00:00 客服：您好，招商基金，请问有什么可以帮您？\n"
                "00:00:08 客户：我之前买的中证白酒基金怎么赎回？\n"
                "00:00:15 客服：这个您可以打电话给客服热线咨询。\n"
                "00:00:25 客户：好的。\n"
                "00:00:27 客服：请问还有什么可以帮到您？\n"
                "00:00:30 客户：没有了。\n"
                "00:00:32 客服：感谢您的来电，祝您生活愉快，再见。"
            ),
            "rules_json": STANDARD_RULES,
        },
        "expected": {
            "deduction_rule_ids": ["17"],
            "fatal_rule_ids": [],
            "final_score_min": 96,
            "final_score_max": 100,
            "requires_human_review": False,
        },
    },
]
