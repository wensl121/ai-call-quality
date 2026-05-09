"""LLM 客户端：返回 LangChain ChatModel，调用方用 with_structured_output 拿强类型结果。

支持 deepseek / openai / anthropic（通过 LLM_PROVIDER 切换）。所有节点共享同一个
模型实例 —— LangChain 自带的 LangSmith 追踪在设了 LANGCHAIN_API_KEY 后会自动生效，
不需要再手动 @traceable。
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

load_dotenv()


# DeepSeek pricing (2024-Q4 公开价位，仅作粗略估算用)：
# - 输入 ¥1 / 1M tokens  ≈ $0.14 / 1M
# - 输出 ¥2 / 1M tokens  ≈ $0.28 / 1M
# 其他 provider 在 _PRICING 里追加即可。
_PRICING: dict[str, dict[str, float]] = {
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
}


class LLMConfigError(RuntimeError):
    pass


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "deepseek").lower()


@lru_cache(maxsize=4)
def get_chat_model(temperature: float = 0.0) -> BaseChatModel:
    """根据 LLM_PROVIDER 返回 LangChain ChatModel。

    DeepSeek 走 OpenAI-兼容协议，所以复用 ChatOpenAI；OpenAI 同上；
    Claude 走 ChatAnthropic（需要单独装 langchain-anthropic）。
    """
    provider = _provider()

    if provider in {"deepseek", "openai"}:
        from langchain_openai import ChatOpenAI

        if provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            if not api_key:
                raise LLMConfigError("DEEPSEEK_API_KEY not set")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = None
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            if not api_key:
                raise LLMConfigError("OPENAI_API_KEY not set")

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            timeout=60,
        )

    if provider == "claude":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise LLMConfigError(
                "claude provider requires `pip install langchain-anthropic`"
            ) from exc
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        if not api_key:
            raise LLMConfigError("ANTHROPIC_API_KEY not set")
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=temperature,
            timeout=60,
            max_tokens=4096,
        )

    raise LLMConfigError(f"Unknown LLM_PROVIDER: {provider}")


def _model_name() -> str:
    provider = _provider()
    if provider == "deepseek":
        return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if provider == "claude":
        return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    return "unknown"


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """按 _PRICING 表估算美元成本。未知模型返回 0。"""
    rates = _PRICING.get(model)
    if not rates:
        return 0.0
    return (
        input_tokens * rates["input"] / 1_000_000
        + output_tokens * rates["output"] / 1_000_000
    )


def invoke_structured(
    schema: type,
    messages: list[BaseMessage],
    *,
    node_name: str,
) -> tuple[Any, dict[str, Any]]:
    """以结构化输出调 LLM，同时返回 token / 成本统计。

    返回 (parsed_object, usage_record)。usage_record 形如：
        {"node": "rule_scorer", "model": "deepseek-chat",
         "input_tokens": 1234, "output_tokens": 56, "total_tokens": 1290,
         "estimated_cost_usd": 0.000351}
    """
    model = get_chat_model()
    bound = model.with_structured_output(
        schema, method="function_calling", include_raw=True
    )
    result = bound.invoke(messages)
    parsed = result["parsed"]
    raw = result["raw"]

    usage = getattr(raw, "usage_metadata", None) or {}
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    model_name = _model_name()
    record = {
        "node": node_name,
        "model": model_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": round(
            _estimate_cost(model_name, input_tokens, output_tokens), 6
        ),
    }
    return parsed, record
