"""Pydantic 输入输出模型。"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


CallType = Literal["voice", "online"]


class QuestionItem(BaseModel):
    timestamp: str
    question_text: str


class QAItem(BaseModel):
    timestamp: str
    question_text: str
    kb_answer: str | None = None
    kb_title: str | None = None
    agent_answer: str | None = Field(
        default=None, description="客服在对话中给出的回答（用于和 kb_answer 比对）"
    )


class Evidence(BaseModel):
    scenario_id: int
    text: str
    timestamp: str
    deduct: int


class Deduction(BaseModel):
    rule_id: str
    group_id: str
    severity: Literal["fatal", "nonfatal"]
    per_deduct: int
    max_cap_in_rule: int
    max_cap_in_group: int
    count: int
    subtotal: int
    evidence: list[Evidence]


class FatalTrigger(BaseModel):
    rule_id: str
    scenario_id: int
    timestamp: str
    text: str


class GroupCap(BaseModel):
    group_id: str
    name: str
    cap: int
    type: Literal["fatal", "nonfatal"]


class Caps(BaseModel):
    overall_cap: int = 100
    groups: list[GroupCap]


class GroupDeductionSummary(BaseModel):
    group_id: str
    deducted: int
    cap_applied: int


class Totals(BaseModel):
    overall_cap: int
    total_deducted: int
    final_score: int
    fatal_applied: bool


class HotWord(BaseModel):
    word: str
    count: int


class QualityResult(BaseModel):
    call_id: str
    call_type: CallType
    template_used: str
    caps: Caps
    fatal_triggers: list[FatalTrigger] = []
    deductions: list[Deduction] = []
    group_deduction_summary: list[GroupDeductionSummary] = []
    totals: Totals
    hot_words: list[HotWord] = []
    business_words: list[HotWord] = []
    requires_human_review: bool = False
    review_reason: str | None = None


class QualityInput(BaseModel):
    call_id: str
    call_type: CallType
    conversation: str
    rules_json: list[dict[str, Any]]
    template_used: str = "voice_template"


# === LLM 调用的结构化输出契约 ===
# 每个节点的 LLM 调用通过 with_structured_output(Schema) 强制返回这些类型，
# 跳过手写 json.loads 与 schema 校验。


class ExtractedQuestion(BaseModel):
    timestamp: str = Field(description="客户提问的时间戳，从对话原文取，没有可留空字符串")
    question_text: str = Field(description="客户提的问题原文或简化")
    agent_answer: str | None = Field(
        default=None,
        description="客服紧接给出的回答原文，用于和知识库比对；没有则为空字符串",
    )


class ExtractedQuestions(BaseModel):
    """问题提取节点的输出。"""

    questions: list[ExtractedQuestion] = Field(default_factory=list)


class RuleScoringOutput(BaseModel):
    """单条规则打分输出（rule_scorer 节点用）。"""

    deductions: list[Deduction] = Field(default_factory=list)
    fatal_triggers: list[FatalTrigger] = Field(default_factory=list)


class ExtractionOutput(BaseModel):
    """提取节点输出：hot_words / business_words / should_say / should_not_say。"""

    hot_words: list[HotWord] = Field(default_factory=list)
    business_words: list[HotWord] = Field(default_factory=list)
    should_say: list[str] = Field(default_factory=list)
    should_not_say: list[str] = Field(default_factory=list)


class AuditIssue(BaseModel):
    type: Literal["规则映射错误", "证据真实性错误", "计算矛盾"]
    location: str = Field(description="如 fatal_triggers[0] / deductions[1].evidence[0] / totals.final_score")
    detail: str


class AuditOutput(BaseModel):
    """审核节点的输出。"""

    passed: bool
    reasons: list[str] = Field(default_factory=list)
    issues: list[AuditIssue] = Field(default_factory=list)
