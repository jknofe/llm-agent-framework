#!/usr/bin/env python3
"""Turn-end hook: keep the agent working while .ai has uncommitted changes.

Enforces the AGENTS.md protocol rule "commit .ai after changing it"
deterministically. One script for every harness; they share the Claude Code
wire shape, so the differences are only in the names below:

- Claude Code `Stop`, Copilot `agentStop` / VS Code `Stop`: `stop_hook_active`
  is true on the pass after a block
- Hermes `pre_verify`: `extra.attempt` counts the nudges already given

The block is the stdout JSON, which all four read; the message is what the
agent sees. A second pass lets the turn end even if still dirty, so a repo
the hook cannot commit never traps the loop.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

cwd = data.get("cwd")
if cwd and os.path.isdir(cwd):
    os.chdir(cwd)

attempt = (data.get("stop_hook_active")
           or data.get("stopHookActive")
           or (data.get("extra") or {}).get("attempt"))
if attempt:
    print("{}")
    sys.exit(0)

if not Path(".ai/.git").is_dir():
    print("{}")
    sys.exit(0)

r = subprocess.run(
    ["git", "-C", ".ai", "status", "--porcelain"],
    capture_output=True, text=True,
)
if r.returncode == 0 and r.stdout.strip():
    reason = ("Uncommitted .ai changes. Commit them now: "
              'git -C .ai add -A && git -C .ai commit -m "<short summary>"')
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)
print("{}")
sys.exit(0)
