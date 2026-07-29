#!/usr/bin/env python3
"""PreToolUse hook: block direct writes to generated files.

INDEX.md is generated from manifest.yaml, and marked rule files under
.claude/rules/ are generated from conventions KB nodes; direct edits would
silently diverge. Hand-written rule files (no marker) stay editable. Exit 2
blocks the tool call and tells the agent the fix.
"""
import json
import sys
from pathlib import Path

MARKER = "${rules_marker}"

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = str((data.get("tool_input") or {}).get("file_path", "")).replace("\\", "/")
if path.endswith(".ai/knowledgebase/INDEX.md"):
    print(
        "INDEX.md is generated. Edit .ai/knowledgebase/manifest.yaml, then "
        "run: python3 ${tools_dir}/gen_index.py",
        file=sys.stderr,
    )
    sys.exit(2)
if "/.claude/rules/" in f"/{path}" and path.endswith(".md"):
    try:
        existing = Path(path).read_text(encoding="utf-8")
    except OSError:
        existing = ""
    if MARKER in existing:
        print(
            "This rule file is generated from a conventions KB node. Edit "
            "the node under .ai/knowledgebase/conventions/, then run: "
            "python3 ${tools_dir}/gen_rules.py (a hook also does this "
            "automatically).",
            file=sys.stderr,
        )
        sys.exit(2)
sys.exit(0)
