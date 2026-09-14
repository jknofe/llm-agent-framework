#!/bin/bash
# usage: gate.sh WORK_DIR N   (N = task number 1..3)
W=$1; N=$2; HIDDEN=/home/johannes/git/llm-agent-framework/benchmarks/hidden-tests
case $N in 2) H=test_hidden_t2_rename_column.py;; 3) H=test_hidden_t3_drop_column.py;; *) H="";; esac
[ -n "$H" ] && cp "$HIDDEN/$H" "$W/tests/"
docker run --rm -v "$W":/workspace -w /workspace python:3.12 bash -c '
  pip install -q -e . pytest hypothesis cogapp >/dev/null 2>&1
  python -m pytest -q 2>&1 | tail -6; echo "SUITE-EXIT: ${PIPESTATUS[0]}"
  cog --check README.md docs/*.rst >/dev/null 2>&1; echo "COG-EXIT: $?"'
[ -n "$H" ] && rm "$W/tests/$H"
echo "TESTS-DIFF: $(git -C "$W" diff --stat HEAD -- tests/ | tail -1)"
echo "DIFF-STAT: $(git -C "$W" diff --stat HEAD | tail -1)"
