#!/usr/bin/env python3
"""Stop hook: block ending the turn while .ai has uncommitted changes.

Enforces the AGENTS.md protocol rule "commit .ai after changing it"
deterministically. Exit 2 feeds the message back to the agent, which
commits and ends the turn cleanly. stop_hook_active guards against loops.
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

if data.get("stop_hook_active"):
    sys.exit(0)  # second pass; let the turn end even if still dirty

if not Path(".ai/.git").is_dir():
    sys.exit(0)

r = subprocess.run(
    ["git", "-C", ".ai", "status", "--porcelain"],
    capture_output=True, text=True,
)
if r.returncode == 0 and r.stdout.strip():
    print(
        "Uncommitted .ai changes. Commit them now: "
        'git -C .ai add -A && git -C .ai commit -m "<short summary>"',
        file=sys.stderr,
    )
    sys.exit(2)
sys.exit(0)
