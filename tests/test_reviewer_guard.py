#!/usr/bin/env python3
"""Regression tests for the reviewer's PreToolUse hook (CONCEPT.md section 79).

Run: python3 tests/test_reviewer_guard.py

Stdlib only. Runs templates/hooks/reviewer_guard.py as Claude Code does, with
a JSON tool call on stdin. Exit 2 is a block, exit 0 a pass. Also checks the
rendered reviewer and worker files: the hook is declared in the reviewer's
frontmatter, the OpenCode reviewer's shell rules list the same commands as
the hook, and the worker may not spawn agents.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
HOOK = REPO / "templates/hooks/reviewer_guard.py"

from agentgen import const, content  # noqa: E402

PASSED = [
    "git diff",
    "git diff --stat main..HEAD",
    "git show HEAD:README.md",
    "git log --oneline -5",
    "git status --short",
    "git -C .ai log -3",
    "grep -rn 'a && b' src",
    "rg todo",
    "cat README.md",
    "ls -la tests",
    "gh pr view 4",
    "gh pr diff 4",
    "gh pr checks 4",
    "gh run view 123",
    "git diff 2>&1",
    "git diff 2>/dev/null",
    "git diff | grep foo",
    "git diff && git log -1",
    "rtk git diff",
    "rtk proxy gh pr checks 4",
    "rtk --ultra-compact git log",
    "rtk read README.md",
    'rtk run "git log && git status"',
    "rtk grep -n x src",
]

BLOCKED = [
    "python3 -m unittest",
    "pytest -q",
    "make test",
    "npm test",
    "git commit -m x",
    "git push",
    "git checkout main",
    "git diff && git push",
    "git diff; rm -rf x",
    "git diff\nrm x",
    "git diff | sh",
    "git diff |& sh",
    "git diff --output=out.txt",
    "git -c core.pager=sh log",
    "cat a > b",
    "cat a >> b",
    "cat <<EOF",
    "echo $(rm x)",
    "grep x `rm y`",
    "rg --pre sh x",
    "gh pr merge 4",
    "gh pr create",
    "find . -delete",
    "sleep 1 &",
    "rtk python3 t.py",
    "rtk proxy python3 t.py",
    'rtk run "git log && python3 t.py"',
]

FAILS = []
N = [0]


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def run(payload):
    return subprocess.run([sys.executable, str(HOOK)], input=payload,
                          capture_output=True, text=True)


def call(command):
    return run(json.dumps({"tool_name": "Bash",
                           "tool_input": {"command": command}}))


def main():
    for c in PASSED:
        r = call(c)
        check(r.returncode == 0, f"should pass: {c!r}: {r.stderr!r}")
    for c in BLOCKED:
        r = call(c)
        check(r.returncode == 2 and "report what you could not check"
              in r.stderr and json.loads(r.stdout.splitlines()[0])
              ["permissionDecision"] == "deny",
              f"should block with the reason: {c!r}: {r.returncode}")

    # Fails open, like git_guard.py: no JSON, no command, an unparsable line.
    for payload in ("", "not json", "[]", "{}",
                    json.dumps({"tool_input": {"command": 4}}),
                    json.dumps({"tool_input": "git push"}),
                    json.dumps({"tool_input": {"command": "git diff 'x"}})):
        check(run(payload).returncode == 0, f"should fail open: {payload!r}")

    # The OpenCode rules and the hook name the same commands.
    src = HOOK.read_text(encoding="utf-8")
    ns = {}
    exec(src.split("SEPARATORS")[0].split("import sys")[1], ns)
    check(ns["ALLOWED"] == const.REVIEWER_SHELL,
          "hook list equals const.REVIEWER_SHELL")
    oc = content.render_opencode_reviewer()
    rules = [ln.strip() for ln in oc.splitlines() if "action: shell" in ln]
    check(rules[0].endswith('resource: "*", effect: deny }') and
          rules[1:] == [f'- {{ action: shell, resource: "{c} *", '
                        'effect: allow }' for c in const.REVIEWER_SHELL],
          f"opencode reviewer: deny all shell, then the list: {rules}")
    check('action: edit, resource: "*", effect: deny' in oc,
          "opencode reviewer still denies edit")

    # Claude: the hook sits in the reviewer's frontmatter, not in settings.
    rv = content.render_reviewer_agent()
    head = rv.split("\n---")[0]
    check("PreToolUse" in head and 'matcher: "Bash"' in head and
          '.claude/hooks/reviewer_guard.py' in head,
          "claude reviewer declares the hook")
    check("reviewer_guard" not in content.render_settings_json(),
          "the hook is not a project-wide hook")
    check("disallowedTools: Agent" in
          content.render_worker_agent().split("\n---")[0],
          "claude worker may not spawn agents")
    check("disallowedTools" not in content.render_opencode_worker() and
          "hooks" not in content.render_copilot_agent("reviewer"),
          "claude-only frontmatter does not leak to opencode or copilot")

    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: reviewer guard, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
