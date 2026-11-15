#!/usr/bin/env python3
"""The command a skill runs before the model sees it (CONCEPT.md section 84).

Run: python3 tests/test_inject.py

Stdlib only. /framework-models on Claude Code and OpenCode carries one
`!`...`` injection of `tasks.py models --list --exit-zero`; Copilot keeps the
old body. Checks the rendered bodies (the command is argument-free, stands
alone at a line start, names the script by its relative path, the Claude
skill pre-approves it, Copilot has none, the arguments line stays outside),
runs the injected command in a real scaffold the way the harness would
(through a shell, from the project root) with the roles unset and set, and
that the stricter check in check_templates rejects a stray or
argument-carrying injection.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))
from agentgen import content  # noqa: E402
import check_templates  # noqa: E402

FAILS = []
N = [0]
CMD = "python3 .ai/agent/tools/tasks.py models --list --exit-zero"


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def body(harness):
    specs = content.command_specs(harness, "$ARGUMENTS", "$ARGUMENTS")
    return [b for n, _d, b in specs if n == "framework-models"][0]


def main():
    for harness in ("claude", "opencode"):
        b = body(harness)
        found = re.findall(r"(?m)^!`([^`]*)`$", b)
        check(found == [CMD], f"{harness}: one injection on its own line: "
                              f"{found}")
        check(b.count("!`") == 1, f"{harness}: no other !` in the body")
        check("$" not in CMD, f"{harness}: no variable in the command")
        check(b.index("$ARGUMENTS") < b.index("!`"),
              f"{harness}: the arguments line is outside the command")
    check("!`" not in body("copilot") and "--exit-zero" not in body("copilot"),
          "copilot: the old body, no injection")
    skill = content.render_skills(
        content.command_specs("claude", "$ARGUMENTS", "$ARGUMENTS"))
    check("allowed-tools: Bash(python3 .ai/agent/tools/tasks.py *)"
          in skill["framework-models/SKILL.md"],
          "claude: the script is pre-approved")
    check(all("allowed-tools" not in v for k, v in skill.items()
              if k != "framework-models/SKILL.md"),
          "claude: no other skill gets it")
    check(all("model:" not in v.split("---")[1] for v in skill.values()),
          "claude: no skill names a model")

    # Run it as the harness does: a shell, the project root.
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run([sys.executable, str(REPO / "init_agent.py"), "--name",
                    "p", "--description", "d", "--harness", "claude", "-y"],
                   cwd=root, capture_output=True, text=True, input="n\n")
    r = subprocess.run(CMD, shell=True, cwd=root, capture_output=True,
                       text=True, timeout=60)
    check(r.returncode == 0, f"roles unset: exit 0, got {r.returncode}")
    check(r.stdout.startswith("MODELS MISSING"),
          f"roles unset: the verdict is still the first line: "
          f"{r.stdout[:40]!r}")
    plain = subprocess.run(CMD.replace(" --exit-zero", ""), shell=True,
                           cwd=root, capture_output=True, text=True,
                           timeout=60)
    check(plain.returncode == 1, "without the flag the gate still exits 1")
    for role in ("worker", "reviewer"):
        f = root / ".claude/agents" / f"{role}.md"
        t = f.read_text(encoding="utf-8")
        f.write_text(t.replace("\nmaxTurns:", "\nmodel: some-model\nmaxTurns:",
                               1), encoding="utf-8")
    r = subprocess.run(CMD, shell=True, cwd=root, capture_output=True,
                       text=True, timeout=60)
    check(r.returncode == 0 and r.stdout.startswith("MODELS OK"),
          f"roles set: MODELS OK, exit 0: {r.stdout[:40]!r}")
    check("--models --worker" in r.stdout, "the command to set them is there")

    # The gate check rejects what it must.
    for bad, why in (("!`rm -rf x`", "an unknown command"),
                     ("!`python3 .ai/agent/tools/tasks.py resolve $ARGUMENTS`",
                      "arguments in the command"),
                     ("see !`x", "a stray marker")):
        orig = content.command_specs

        def patched(h, f, t, bad=bad, orig=orig):
            return [(n, d, b + "\n" + bad + "\n") for n, d, b in orig(h, f, t)]
        content.command_specs = patched
        check_templates.failures.clear()
        try:
            check_templates.check_injection_syntax()
        finally:
            content.command_specs = orig
        check(any("[injection]" in x for x in check_templates.failures),
              f"check_templates rejects {why}")
    check_templates.failures.clear()
    check_templates.check_injection_syntax()
    check(not check_templates.failures, "the real set passes the check")

    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: skill injection, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
