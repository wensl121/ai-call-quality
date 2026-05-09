"""知识库接口。

骨架阶段用本地 JSON 做检索：每条记录形如
    {"title": "...", "keywords": ["...", "..."], "answer": "..."}
检索时按 keyword 命中数排序；后续可换向量检索。
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def _load_kb() -> list[dict[str, Any]]:
    path = Path(os.getenv("KB_PATH", "examples/kb.json"))
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def search(question: str, *, top_k: int = 1) -> list[dict[str, Any]]:
    """返回最相关的 KB 条目。命中分数 = 关键词出现次数。"""
    kb = _load_kb()
    if not kb:
        return []

    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in kb:
        score = sum(1 for kw in entry.get("keywords", []) if kw and kw in question)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored[:top_k]]
