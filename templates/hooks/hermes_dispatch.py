#!/usr/bin/env python3
"""Hermes hook dispatcher: run the hook of whichever project a session is in.

Hermes declares shell hooks per profile in ~/.hermes/config.yaml, not per
repository, so one copy of this file lives at
~/.hermes/agent-hooks/llm-agent-hook.py and the config names it once. On
each event it reads the payload, takes the session's `cwd`, and runs
<cwd>/.agents/hooks/<name>.py with the same payload. A directory without a
scaffold gets a no-op, so the entry is safe for every project and can stay
fail-closed.

Usage in config.yaml: ~/.hermes/agent-hooks/llm-agent-hook.py <name>
Hermes expands `~` only at the start of the command and spawns it without
a shell, so the file is run through its shebang and must be executable
(`install -m 755`).
"""
import json
import os
import subprocess
import sys

raw = sys.stdin.read()
name = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    cwd = json.loads(raw).get("cwd") or os.getcwd()
except Exception:
    cwd = os.getcwd()

script = os.path.join(cwd, ".agents", "hooks", f"{name}.py")
if not name or not os.path.isfile(script):
    print("{}")
    sys.exit(0)

r = subprocess.run([sys.executable, script], input=raw, cwd=cwd,
                   capture_output=True, text=True)
sys.stdout.write(r.stdout)
sys.stderr.write(r.stderr)
sys.exit(r.returncode)
