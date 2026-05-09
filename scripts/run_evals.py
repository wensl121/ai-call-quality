"""跑黄金数据集回归。

先 `python scripts/upload_dataset.py` 把数据上 LangSmith，再用本脚本评估。

用法：
    python scripts/run_evals.py [experiment_prefix] [dataset_name]
默认 experiment_prefix=baseline，dataset_name=ai-call-quality-golden
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from langsmith.evaluation import evaluate  # noqa: E402

from call_quality import build_graph  # noqa: E402
from evals.evaluators import ALL_EVALUATORS  # noqa: E402


def _target(inputs: dict) -> dict:
    """LangSmith 把 example.inputs 喂进来；返回值会作为 run.outputs。"""
    graph = build_graph()
    return graph.invoke(inputs)


def run(
    experiment_prefix: str = "baseline",
    dataset_name: str = "ai-call-quality-golden",
) -> None:
    print(f"[*] experiment_prefix={experiment_prefix}  dataset={dataset_name}")
    results = evaluate(
        _target,
        data=dataset_name,
        evaluators=ALL_EVALUATORS,
        experiment_prefix=experiment_prefix,
        max_concurrency=4,
    )

    # 简要汇总打印（详细看 LangSmith UI）
    rows = list(results)
    print(f"\n[done] {len(rows)} examples")
    by_eval: dict[str, list[float]] = {}
    for row in rows:
        for ev in row.get("evaluation_results", {}).get("results", []):
            by_eval.setdefault(ev.key, []).append(ev.score or 0.0)
    print("\nAverage scores per evaluator:")
    for k, scores in by_eval.items():
        avg = sum(scores) / len(scores) if scores else 0
        print(f"  {k:20s} {avg:.2%}  (n={len(scores)})")


if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    dataset = sys.argv[2] if len(sys.argv) > 2 else "ai-call-quality-golden"
    run(prefix, dataset)
