#!/usr/bin/env python3
"""SessionStart hook (Claude Code): put the notes hub in the session's context.

Claude Code adds a SessionStart hook's plain stdout to the model's context
before the first prompt, on `startup`, `resume`, `clear` and again after
`compact`, so the hub `.ai/notes.md` is there without a tool call and is not
lost to a compaction. The text is built by `tasks.py notes --session`, which
owns the size cap, the header and the freshness flags (CONCEPT.md sections
82 and 83); this script only runs it.

Skipped when `agent_type` is `worker`: a worker started with
`claude --agent worker` (the Herdr tab) reads the hub itself, as its contract
says, and must not get it twice. A sub-agent spawned by the Agent tool never
runs SessionStart, which is a per-session event.

Fails open: any error, a missing tool or a slow one prints nothing and exits
0, so a broken hub can never keep a session from starting.
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if not isinstance(data, dict) or data.get("agent_type") == "worker":
        sys.exit(0)
    # .claude/hooks/notes_session.py: the project root is two levels up.
    root = Path(__file__).resolve().parents[2]
    tool = root / ".ai" / "agent" / "tools" / "tasks.py"
    if not tool.is_file():
        sys.exit(0)
    r = subprocess.run([sys.executable, str(tool), "notes", "--session"],
                       capture_output=True, text=True, timeout=10,
                       cwd=str(root))
    if r.returncode == 0 and r.stdout.strip():
        sys.stdout.write(r.stdout)
except SystemExit:
    raise
except BaseException:
    pass
sys.exit(0)
