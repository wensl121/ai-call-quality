"""调用部署在 LangSmith Platform 上的 graph。

用法：
    set DEPLOYMENT_URL=https://xxx.us.langgraph.app
    python scripts/call_deployment.py [examples/sample_input.json]

需要环境变量：
    DEPLOYMENT_URL    Platform 上 deployment 的 API URL（UI 里复制）
    LANGCHAIN_API_KEY 你的 LangSmith API key（已在 .env 里）
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from langgraph_sdk import get_sync_client  # noqa: E402


def main() -> None:
    url = os.getenv("DEPLOYMENT_URL")
    if not url:
        print("ERROR: set DEPLOYMENT_URL env var (your Platform deployment URL)")
        sys.exit(1)

    api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("ERROR: LANGCHAIN_API_KEY not set")
        sys.exit(1)

    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("examples/sample_input.json")
    payload = json.loads(input_path.read_text(encoding="utf-8"))

    client = get_sync_client(url=url, api_key=api_key)

    print(f"[*] calling {url}")
    print(f"[*] input: {input_path}")

    # /runs/wait — 同步调用，等结果（适合调试）
    result = client.runs.wait(
        thread_id=None,            # None = stateless run
        assistant_id="call_quality",
        input=payload,
    )

    final = result.get("result") if isinstance(result, dict) else result
    print("\n=== result ===")
    print(json.dumps(final, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
