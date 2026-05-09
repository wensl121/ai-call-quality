"""端到端跑一遍：

    python examples/run_example.py

需要先 `pip install -e .` 并把 .env 配好（DEEPSEEK_API_KEY 等）。
"""
from __future__ import annotations

import json
from pathlib import Path

from call_quality import build_graph


def main() -> None:
    sample = json.loads(Path("examples/sample_input.json").read_text(encoding="utf-8"))

    graph = build_graph()
    final_state = graph.invoke(sample)

    result = final_state.get("result", {})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
