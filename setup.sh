#!/usr/bin/env bash
# Download the three pinned datasets over HTTPS, record SHA-256, and draw the fixed samples.
# Run from the repository root:  bash .studio/ai-channel/decisions/demo/setup.sh
set -euo pipefail
D=.studio/ai-channel/decisions
fetch() {  # repo revision path outdir
  local url="https://huggingface.co/datasets/$1/resolve/$2/$3"
  local out="$D/data/$4/$(basename "$3")"
  [ -s "$out" ] || curl -sSfL --proto '=https' -o "$out" "$url"
  echo "$1 $2 $3 $(sha256sum "$out" | cut -d' ' -f1) $(stat -c %s "$out")"
}
{
  fetch PolyAI/banking77 1846984189f2bc0ac51c6fc3a600fa9e1714e0c6 data/test-00000-of-00001.parquet banking77
  fetch PolyAI/banking77 1846984189f2bc0ac51c6fc3a600fa9e1714e0c6 README.md banking77
  fetch google/boolq 35b264d03638db9f4ce671b711558bf7ff0f80d5 data/validation-00000-of-00001.parquet boolq
  fetch google/boolq 35b264d03638db9f4ce671b711558bf7ff0f80d5 README.md boolq
  fetch SetFit/sst5 e51bdcd8cd3a30da231967c1a249ba59361279a3 test.jsonl sst5
  fetch SetFit/sst5 e51bdcd8cd3a30da231967c1a249ba59361279a3 README.md sst5
} | tee "$D/data/downloads.txt"
# Parse the untrusted files in isolated mode; the script lives outside the data folders.
uv run --quiet --python 3.12 --with pyarrow==18.1.0 python -I "$D/demo/make_samples.py" "$D"
