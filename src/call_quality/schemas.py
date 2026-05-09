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
