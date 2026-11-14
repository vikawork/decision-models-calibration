"""Fetch the pinned SST-5 test split and rebuild data/samples/score.jsonl.

The SST-5 copy we used (SetFit/sst5) states no licence, so its sentences are not in this repository.
This script downloads the exact file we used, checks its SHA-256, draws the same 400 items with the
same seed as make_samples.py, and checks the result against data/samples/score-ids.jsonl.

Run from the repository root, standard library only:  python3 -I fetch_sst5.py
"""
import hashlib
import json
import random
import sys
import urllib.request
from pathlib import Path

REPO = "SetFit/sst5"
REVISION = "e51bdcd8cd3a30da231967c1a249ba59361279a3"
FILE = "test.jsonl"
SHA256 = "1384216112a34f3d70b6fa210762f3399bb080410c0456ac6e54a5cb413f04b2"
SEED = 20261114  # same as make_samples.py
N = 400

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
raw = root / "data" / "sst5" / FILE
out = root / "data" / "samples" / "score.jsonl"
ids = root / "data" / "samples" / "score-ids.jsonl"

if not raw.exists():
    raw.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{FILE}"
    with urllib.request.urlopen(url, timeout=120) as r:
        raw.write_bytes(r.read())
digest = hashlib.sha256(raw.read_bytes()).hexdigest()
if digest != SHA256:
    sys.exit(f"{raw}: SHA-256 {digest} does not match the pinned {SHA256}")

rows = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines() if line.strip()]
picked = random.Random(SEED).sample(range(len(rows)), N)
items = [{"id": f"sst5-{i}", "text": rows[i]["text"], "gold": int(rows[i]["label"]),
          "gold_text": rows[i].get("label_text")} for i in picked]

expected = [json.loads(line) for line in ids.read_text(encoding="utf-8").splitlines() if line.strip()]
got = [{"id": r["id"], "gold": r["gold"], "gold_text": r["gold_text"]} for r in items]
if got != expected:
    sys.exit("the drawn sample does not match data/samples/score-ids.jsonl")

with out.open("w", encoding="utf-8") as f:
    for r in items:
        f.write(json.dumps(r) + "\n")
print(f"wrote {out} ({len(items)} items, matches score-ids.jsonl)")
