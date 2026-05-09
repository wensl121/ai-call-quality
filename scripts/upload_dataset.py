"""把 evals/golden_dataset.GOLDEN_EXAMPLES 同步到 LangSmith。

幂等：如果同名 dataset 已存在，会跳过 examples 中已上传的（按 example name 去重）。

用法：
    python scripts/upload_dataset.py [dataset_name]
默认 dataset_name = ai-call-quality-golden
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from langsmith import Client  # noqa: E402

from evals.golden_dataset import GOLDEN_EXAMPLES  # noqa: E402


def upload(dataset_name: str = "ai-call-quality-golden") -> None:
    client = Client()

    existing = list(client.list_datasets(dataset_name=dataset_name))
    if existing:
        ds = existing[0]
        print(f"[*] reusing dataset: {ds.name} (id={ds.id})")
    else:
        ds = client.create_dataset(
            dataset_name=dataset_name,
            description="AI call quality regression golden set",
        )
        print(f"[+] created dataset: {ds.name} (id={ds.id})")

    existing_names = {
        ex.metadata.get("name") for ex in client.list_examples(dataset_id=ds.id)
    }

    added = 0
    skipped = 0
    for example in GOLDEN_EXAMPLES:
        if example["name"] in existing_names:
            print(f"  - skip (exists): {example['name']}")
            skipped += 1
            continue
        client.create_example(
            inputs=example["inputs"],
            outputs=example["expected"],
            dataset_id=ds.id,
            metadata={"name": example["name"], "description": example.get("description", "")},
        )
        print(f"  + added: {example['name']}")
        added += 1

    print(f"[done] added={added} skipped={skipped}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "ai-call-quality-golden"
    upload(name)
