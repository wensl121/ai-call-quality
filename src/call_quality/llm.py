"""LLM 客户端适配层。

支持 deepseek / claude / openai 三个后端，通过 LLM_PROVIDER 环境变量切换。
返回值统一为字符串；调用方负责 JSON 解析。
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

try:
    from langsmith import traceable
except ImportError:  # langsmith optional
    def traceable(*_args, **_kwargs):  # type: ignore[no-redef]
        def deco(f):
            return f
        return deco if not _args or not callable(_args[0]) else _args[0]


class LLMError(RuntimeError):
    pass


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "deepseek").lower()


@traceable(name="llm.chat", run_type="llm")
def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    response_format: str | None = None,
) -> str:
    """统一聊天接口。

    response_format="json" 时尝试启用对应后端的 JSON 模式（DeepSeek / OpenAI 支持，
    Claude 不支持则忽略，依赖提示词约束输出）。
    """
    provider = _provider()
    if provider == "deepseek":
        return _call_openai_compatible(
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key_env="DEEPSEEK_API_KEY",
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=messages,
            temperature=temperature,
            response_format=response_format,
        )
    if provider == "openai":
        return _call_openai_compatible(
            base_url="https://api.openai.com",
            api_key_env="OPENAI_API_KEY",
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=temperature,
            response_format=response_format,
        )
    if provider == "claude":
        return _call_anthropic(
            messages=messages,
            temperature=temperature,
        )
    raise LLMError(f"Unknown LLM_PROVIDER: {provider}")


def _call_openai_compatible(
    *,
    base_url: str,
    api_key_env: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    response_format: str | None,
) -> str:
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise LLMError(f"{api_key_env} not set")
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format == "json":
        payload["response_format"] = {"type": "json_object"}
    resp = httpx.post(
        f"{base_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_anthropic(
    *,
    messages: list[dict[str, str]],
    temperature: float,
) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("ANTHROPIC_API_KEY not set")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    system_chunks = [m["content"] for m in messages if m["role"] == "system"]
    user_messages = [m for m in messages if m["role"] != "system"]

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 4096,
            "temperature": temperature,
            "system": "\n\n".join(system_chunks) if system_chunks else None,
            "messages": user_messages,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


@traceable(name="llm.chat_json", run_type="llm")
def chat_json(messages: list[dict[str, str]], *, temperature: float = 0.0) -> Any:
    """调用 LLM 并解析 JSON 输出。"""
    raw = chat(messages, temperature=temperature, response_format="json")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM did not return valid JSON: {raw[:200]}") from exc
