#!/usr/bin/env python3
"""Pre-tool hook: enforce the two git guardrails deterministically.

AGENTS.md states them as protocol; instructions are advisory, hooks are not.
Blocked, with the reason fed back to the agent:

- merging into the default branch: `git merge` while on it, `git push` that
  targets it, `gh pr merge`
- a commit whose message carries a co-author line (`Co-Authored-By:`, or a
  `--trailer` adding one)

One script for every harness. They share the Claude Code wire shape, so
only names differ: the tool is `Bash` (Claude Code), `bash` (Copilot CLI),
`runTerminalCommand` (VS Code) or `terminal` (Hermes), and its arguments
arrive as `tool_input` or `toolArgs`. Any tool call carrying a string
`command` is inspected. A block is exit 2 with the reason on stderr, which
every harness honours, plus the same decision as stdout JSON in the shapes
Copilot CLI and VS Code read. Everything else passes; the hook never blocks
a command it cannot parse as one of the cases above.
"""
import json
import os
import re
import shlex
import subprocess
import sys

CO_AUTHOR = re.compile(r"co-authored-by", re.IGNORECASE)


def run(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def default_branches():
    """The default branch under every name it answers to. Remote HEAD
    first; without a remote, main/master when they exist locally."""
    names = set()
    ref = run("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if ref:
        names.add(ref.split("/", 1)[-1])
        names.add(ref)
    for cand in ("main", "master"):
        if run("rev-parse", "--verify", "--quiet", f"refs/heads/{cand}"):
            names.add(cand)
    return names


def current_branch():
    return run("rev-parse", "--abbrev-ref", "HEAD")


def segments(command):
    """Split a shell line into simple commands on && || ; | so each git
    call is judged on its own arguments."""
    try:
        words = shlex.split(command)
    except ValueError:
        return []
    out, cur = [], []
    for w in words:
        if w in ("&&", "||", ";", "|"):
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(w)
    if cur:
        out.append(cur)
    return out


def block(reason):
    print(json.dumps({
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }))
    print(reason, file=sys.stderr)
    sys.exit(2)


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input") or data.get("toolArgs") or {}
command = tool_input.get("command") if isinstance(tool_input, dict) else None
if not isinstance(command, str):
    sys.exit(0)
if "git" not in command and "gh" not in command:
    sys.exit(0)

cwd = data.get("cwd")
if cwd and os.path.isdir(cwd):
    os.chdir(cwd)

defaults = default_branches()
head = current_branch()
switching_to_default = False

for seg in segments(command):
    if not seg:
        continue
    # git may be preceded by env assignments or flags such as -C <dir>
    try:
        gi = seg.index("git")
    except ValueError:
        gi = -1
    if seg[0] == "gh" and seg[1:3] == ["pr", "merge"]:
        block("Blocked: `gh pr merge` merges into the default branch. "
              "The user merges; stop at the pull request.")
    if gi == -1:
        continue
    args = [a for a in seg[gi + 1:] if not a.startswith("-")]
    if not args:
        continue
    sub = args[0]

    if sub in ("checkout", "switch") and any(a in defaults for a in args[1:]):
        switching_to_default = True

    if sub == "merge" and (head in defaults or switching_to_default):
        block(f"Blocked: merging into the default branch ({head or 'default'}). "
              "Never merge into it unasked; leave the branch or pull request "
              "for the user to merge.")

    if sub == "push":
        targets = args[1:]
        refspecs = targets[1:] if targets else []
        if not refspecs and head in defaults:
            block(f"Blocked: pushing the default branch ({head}) directly. "
                  "Push a feature branch and open a pull request instead.")
        for spec in refspecs:
            dest = spec.split(":", 1)[-1].lstrip("+")
            if dest.startswith("refs/heads/"):
                dest = dest[len("refs/heads/"):]
            if dest in defaults:
                block(f"Blocked: pushing to the default branch ({dest}). "
                      "Push a feature branch and open a pull request instead.")

    if sub == "commit":
        rest = seg[gi + 1:]
        tail = " ".join(rest)
        # a message given as a file: read it, since the text is not inline
        for i, a in enumerate(rest):
            path = None
            if a in ("-F", "--file") and i + 1 < len(rest):
                path = rest[i + 1]
            elif a.startswith("--file="):
                path = a[len("--file="):]
            if path and os.path.isfile(path):
                try:
                    tail += "\n" + open(path, encoding="utf-8",
                                         errors="replace").read()
                except OSError:
                    pass
        if CO_AUTHOR.search(tail):
            block("Blocked: the commit message carries a co-author line. "
                  "Never add Co-Authored-By or any co-author trailer; commit "
                  "again without it.")

sys.exit(0)
