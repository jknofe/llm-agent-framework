#!/usr/bin/env python3
"""Regression tests for the git_guard PreToolUse hook.

Run: python3 tests/test_git_guard.py

Stdlib only. Runs templates/hooks/git_guard.py as the harness does, with a
JSON tool call on stdin, inside a throwaway repository checked out on main.
Exit 2 is a block, exit 0 a pass.

What it pins down:

  plain      the two guardrails on bare commands: merging into or pushing
             to the default branch, `gh pr merge`, a co-author line.
  proxied    the same commands behind a proxy (`rtk gh`, `rtk proxy`,
             `rtk run "<line>"`). RTK's hook rewrites commands to this form
             and its docs teach agents to type it; before 9.1 the hook let
             `rtk gh pr merge` and `rtk run "git merge ..."` through.
  harmless   read-only and feature-branch commands pass, proxied or not.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "templates/hooks/git_guard.py"

BLOCKED = {
    "plain": [
        "gh pr merge 4",
        "git merge feature",
        "git push origin main",
        "git push",
        'git commit -m "x\n\nCo-Authored-By: a <b@c>"',
    ],
    "proxied": [
        "rtk gh pr merge 4",
        "rtk proxy gh pr merge 4",
        "rtk --ultra-compact gh pr merge 4",
        "rtk git merge feature",
        "rtk proxy git merge feature",
        'rtk run "git merge feature"',
        'rtk run -c "cd . && gh pr merge 4"',
        "rtk git push origin main",
        'rtk proxy git commit -m "x Co-Authored-By: a <b@c>"',
    ],
}

PASSED = [
    "git log --oneline",
    "git push origin feature",
    "gh pr view 4",
    "rtk git log --oneline",
    "rtk git push origin feature",
    "rtk grep -n git src",
    "rtk read gh.md",
    'rtk run "git log; git status"',
    'rtk git commit -m "docs: explain rtk run"',
    "rtk",
]

failures = []


def fail(test, msg):
    failures.append(f"{test}: {msg}")


def guard(command, cwd):
    payload = json.dumps({"tool_name": "Bash",
                          "tool_input": {"command": command},
                          "cwd": str(cwd)})
    r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True)
    return r.returncode


def main():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        git = ["git", "-C", td, "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git[:3] + ["init", "-q", "-b", "main"], check=True)
        subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "i"],
                       check=True)
        for test, commands in BLOCKED.items():
            for c in commands:
                if guard(c, repo) != 2:
                    fail(test, f"not blocked: {c!r}")
        for c in PASSED:
            if guard(c, repo) != 0:
                fail("harmless", f"blocked: {c!r}")
    n = sum(map(len, BLOCKED.values())) + len(PASSED)
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print(f"ok: git guard, {n} commands checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
