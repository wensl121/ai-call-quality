"""PII 脱敏：在喂 LLM 之前，把对话里的敏感信息替换成占位符。

合规要点：身份证、手机号、银行卡号、邮箱、详细地址不应进入第三方 LLM 上下文。
覆盖范围（中国大陆场景）：
- 手机号：11 位数字以 1 开头
- 身份证：18 位数字（最后一位可能是 X）或 15 位
- 银行卡号：13–19 位数字
- 邮箱
- 详细地址：「市/区/路/号」串联出现

注：脱敏是启发式，复杂场景应换 presidio / PrivacyShield。证据 evidence.text 引用对话时
也会带上脱敏后的版本，最终输出对外不会泄露 PII。
"""
from __future__ import annotations

import re

# 顺序很重要：先匹配长串数字，避免身份证被手机号误吃
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # 邮箱
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    # 18 位身份证（含末尾 X）
    (re.compile(r"\b\d{17}[\dXx]\b"), "[ID_CARD]"),
    # 15 位身份证
    (re.compile(r"\b\d{15}\b"), "[ID_CARD]"),
    # 银行卡号 13–19 位
    (re.compile(r"\b\d{13,19}\b"), "[BANK_CARD]"),
    # 大陆手机号
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[PHONE]"),
    # 详细街道地址：xx路/街/巷/弄 + 数字 + 号 (+ 可选 房间/楼栋)
    (
        re.compile(
            r"[一-龥]{2,}(?:路|街|巷|弄|大道|道路)\d+号"
            r"(?:[\d\-]+(?:室|楼|栋|单元))?"
        ),
        "[ADDRESS]",
    ),
    # 省/市/区/县多级组合（至少 2 级，避免误匹配单个 "市" / "号"）
    (
        re.compile(r"(?:[一-龥]{2,}(?:省|市|区|县|镇|村)){2,}[一-龥]*"),
        "[ADDRESS]",
    ),
]


def redact_pii(text: str) -> str:
    """对文本做 PII 脱敏，返回脱敏后字符串。空 / 非字符串原样返回。"""
    if not isinstance(text, str) or not text:
        return text
    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out
