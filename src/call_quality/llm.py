"""LLM 客户端：返回 LangChain ChatModel，调用方用 with_structured_output 拿强类型结果。

支持 deepseek / openai / anthropic（通过 LLM_PROVIDER 切换）。所有节点共享同一个
模型实例 —— LangChain 自带的 LangSmith 追踪在设了 LANGCHAIN_API_KEY 后会自动生效，
不需要再手动 @traceable。
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()


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
