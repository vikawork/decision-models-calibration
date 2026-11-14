#!/usr/bin/env bash
# Run every measured phase for one provider, sequentially. From the repository root:
#   bash .studio/ai-channel/decisions/demo/run-all.sh <google|openai|jev>
set -uo pipefail
P=$1
D=.studio/ai-channel/decisions/demo
py() { uv run --quiet --python 3.12 --with httpx==0.28.1 python -I -B "$D/run.py" "$@"; }
if [ "$P" = jev ]; then
  py jev decisions choice || exit $?
else
  py "$P" pair || exit $?
fi
py "$P" decisions predicate || exit $?
py "$P" decisions score || exit $?
py "$P" fanout || exit $?
echo "run-all $P finished"
