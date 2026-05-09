"""并行 vs 串行延迟对比。

跑同一个 graph、同一份 sample_input.json，
一次默认（Send 真并行），一次 max_concurrency=1（强制串行）。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from call_quality import build_graph  # noqa: E402


def run_once(label: str, *, max_concurrency: int | None) -> tuple[float, dict]:
    sample = json.loads(Path("examples/sample_input.json").read_text(encoding="utf-8"))
    graph = build_graph()

    config = {}
    if max_concurrency is not None:
        config["max_concurrency"] = max_concurrency

    print(f"\n[{label}]  starting (max_concurrency={max_concurrency})...")
    t0 = time.perf_counter()
    final = graph.invoke(sample, config=config)
    elapsed = time.perf_counter() - t0
    result = final.get("result", {})
    print(f"[{label}]  elapsed: {elapsed:.2f}s")
    print(f"[{label}]  final_score: {result['totals']['final_score']}")
    print(f"[{label}]  llm calls: {result['cost_summary']['total_calls']}")
    print(f"[{label}]  tokens: {result['cost_summary']['total_tokens']}")
    return elapsed, result


def main() -> None:
    parallel_t, parallel_r = run_once("PARALLEL (default)", max_concurrency=None)
    serial_t, serial_r = run_once("SERIAL (max_concurrency=1)", max_concurrency=1)

    saved_pct = (1 - parallel_t / serial_t) * 100 if serial_t else 0
    print("\n" + "=" * 50)
    print(f"  parallel: {parallel_t:.2f}s")
    print(f"  serial:   {serial_t:.2f}s")
    print(f"  saved:    {serial_t - parallel_t:.2f}s  ({saved_pct:.1f}%)")
    print("=" * 50)


if __name__ == "__main__":
    main()
