#!/usr/bin/env python3
"""PostToolUse hook: keep generated KB artifacts in sync.

- manifest.yaml written  -> regenerate INDEX.md (gen_index.py) and the
  path-scoped rules (gen_rules.py; covers/tier live in the manifest)
- conventions node written -> regenerate the path-scoped rules only

Regenerating deterministically removes the "remember to run gen_*"
instructions from the phase docs. Non-blocking: the triggering write already
succeeded, so this only keeps the generated views in sync. Always exits 0.
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = str((data.get("tool_input") or {}).get("file_path", "")).replace("\\", "/")
is_manifest = path.endswith(".ai/knowledgebase/manifest.yaml")
is_convention = (".ai/knowledgebase/conventions/" in path
                 and path.endswith(".md"))
if not (is_manifest or is_convention):
    sys.exit(0)

jobs = []
if is_manifest:
    jobs.append(("INDEX.md", Path(".ai/agent/tools/gen_index.py")))
jobs.append((".claude/rules", Path(".ai/agent/tools/gen_rules.py")))

for label, gen in jobs:
    if not gen.exists():
        continue
    r = subprocess.run([sys.executable, str(gen)], capture_output=True, text=True)
    msg = (r.stdout or r.stderr).strip()
    if msg:
        print(f"{label} regenerated: {msg}", file=sys.stderr)
sys.exit(0)
