"""Draw the fixed 400-item samples from the downloaded datasets.

Run in isolated mode (python -I); takes the decisions folder as its only argument.
Writes data/samples/{choice,predicate,score}.jsonl and data/samples/meta.json.
"""
import json
import random
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

SEED = 20261114
N = 400


def banking_labels(readme: Path) -> list[str]:
    text = readme.read_text(encoding="utf-8")
    names = {}
    # Two upstream names are irregular ("Refund_not_showing_up", "reverted_card_payment?"); keep them
    # verbatim as the gold label strings, and normalise only when building option keys.
    for m in re.finditer(r"^\s+'(\d+)':\s*([A-Za-z_?]+)\s*$", text, re.M):
        names[int(m.group(1))] = m.group(2)
    assert len(names) == 77, len(names)
    return [names[i] for i in range(77)]


def main(root: Path) -> None:
    data = root / "data"
    out = data / "samples"
    out.mkdir(exist_ok=True)
    meta = {"seed": SEED, "n": N, "sets": {}}

    labels = banking_labels(data / "banking77" / "README.md")
    t = pq.read_table(data / "banking77" / "test-00000-of-00001.parquet").to_pylist()
    idx = random.Random(SEED).sample(range(len(t)), N)
    with (out / "choice.jsonl").open("w") as f:
        for i in idx:
            f.write(json.dumps({"id": f"b77-{i}", "text": t[i]["text"], "gold": labels[t[i]["label"]]}) + "\n")
    meta["sets"]["choice"] = {"source": "PolyAI/banking77", "split": "test", "rows": len(t), "labels": labels}

    t = pq.read_table(data / "boolq" / "validation-00000-of-00001.parquet").to_pylist()
    idx = random.Random(SEED).sample(range(len(t)), N)
    with (out / "predicate.jsonl").open("w") as f:
        for i in idx:
            r = t[i]
            f.write(json.dumps({"id": f"boolq-{i}", "question": r["question"], "passage": r["passage"],
                                "gold": bool(r["answer"])}) + "\n")
    meta["sets"]["predicate"] = {"source": "google/boolq", "split": "validation", "rows": len(t)}

    rows = [json.loads(line) for line in (data / "sst5" / "test.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    idx = random.Random(SEED).sample(range(len(rows)), N)
    with (out / "score.jsonl").open("w") as f:
        for i in idx:
            r = rows[i]
            f.write(json.dumps({"id": f"sst5-{i}", "text": r["text"], "gold": int(r["label"]),
                                "gold_text": r.get("label_text")}) + "\n")
    meta["sets"]["score"] = {"source": "SetFit/sst5", "split": "test", "rows": len(rows),
                             "label_texts": sorted({(int(r["label"]), r.get("label_text")) for r in rows})}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    for k, v in meta["sets"].items():
        print(k, v["source"], v["split"], v["rows"])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
