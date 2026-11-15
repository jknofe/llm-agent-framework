#!/usr/bin/env python3
"""The generated `.claude/settings.json` and the one key of it that is the
user's (CONCEPT.md section 80).

Run: python3 tests/test_settings.py

Stdlib only. Scaffolds a claude project into a temp dir with the real
init_agent.py and checks: auto memory is off by default, a user's own value
survives a forced re-init (`-y`) in both directions, an unforced re-init
leaves the file alone, the other generated keys are regenerated, an unreadable
file is replaced, and the key is claude only.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INIT = REPO / "init_agent.py"
FAILS = []
N = [0]


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def init(root, harness="claude", yes=True):
    cmd = [sys.executable, str(INIT), "--name", "p", "--description", "d",
           "--harness", harness]
    if yes:
        cmd.append("-y")
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                          input="n\n")


def main():
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    init(root)
    f = root / ".claude/settings.json"
    s = json.loads(f.read_text(encoding="utf-8"))
    check(s.get("autoMemoryEnabled") is False,
          f"fresh scaffold: auto memory off, got {s.get('autoMemoryEnabled')!r}")
    check("allow" in s["permissions"] and "PreToolUse" in s["hooks"],
          "fresh scaffold: permissions and hooks still there")

    # The user turns it back on; a forced re-init keeps their value, and
    # still regenerates everything else.
    s["autoMemoryEnabled"] = True
    s["permissions"]["allow"].append("Bash(make lint:*)")
    f.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
    init(root)
    s = json.loads(f.read_text(encoding="utf-8"))
    check(s["autoMemoryEnabled"] is True, "re-init -y keeps the user's true")
    check("Bash(make lint:*)" not in s["permissions"]["allow"],
          "re-init -y regenerates the rest, as it always did")

    # An unforced re-init does not touch the file at all.
    s["autoMemoryEnabled"] = True
    f.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
    before = f.read_text(encoding="utf-8")
    init(root, yes=False)
    check(f.read_text(encoding="utf-8") == before,
          "re-init without -y leaves the file alone")

    # A file from before 12.18 has no key: the re-init adds the default.
    s.pop("autoMemoryEnabled")
    f.write_text(json.dumps(s), encoding="utf-8")
    init(root)
    check(json.loads(f.read_text(encoding="utf-8"))["autoMemoryEnabled"]
          is False, "no key in the old file: the default false")

    # A value that is not a boolean, or a broken file, is not carried.
    f.write_text('{"autoMemoryEnabled": "yes"}', encoding="utf-8")
    init(root)
    check(json.loads(f.read_text(encoding="utf-8"))["autoMemoryEnabled"]
          is False, "a non-boolean value is replaced by the default")
    f.write_text("{not json", encoding="utf-8")
    init(root)
    check(json.loads(f.read_text(encoding="utf-8"))["autoMemoryEnabled"]
          is False, "an unreadable file is regenerated")

    # The update body tells the updater the same rule.
    skill = (root / ".claude/skills/framework-update/SKILL.md").read_text(
        encoding="utf-8")
    check("`autoMemoryEnabled`" in skill and "stays" in skill,
          "the update body keeps a user's autoMemoryEnabled")

    # Claude only: OpenCode and Copilot have no second memory to turn off.
    for harness in ("opencode", "copilot"):
        other = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=other, check=True)
        init(other, harness)
        text = "".join(p.read_text(encoding="utf-8", errors="ignore")
                       for p in other.rglob("*.json")
                       if ".ai" not in p.parts)
        check("autoMemoryEnabled" not in text,
              f"{harness}: no autoMemoryEnabled")

    if FAILS:
        for m in FAILS:
            print(f"FAIL {m}")
        return 1
    print(f"ok: settings, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
