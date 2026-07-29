#!/usr/bin/env python3
"""Regression tests for --bootstrap-update, against real legacy scaffolds.

Run: python3 tests/test_bootstrap_update.py

Builds fixtures by checking historical generators out of this repo's own git
history and running them, so the "old scaffold" under test is a real one
rather than a hand-written approximation. Needs a git checkout with history;
skips with a clear message when that is missing.

What it pins down, in order of how badly it would hurt to get wrong:

  stamp_is_honest    the bootstrap must not claim the current version. If it
                     did, /update would read "already current", and would also
                     inherit the current file list, so nothing would ever be
                     classified as retired. A silent no-op update.
  touches_nothing    user edits to AGENTS.md and settings.json survive. This
                     is the whole reason bootstrap exists instead of a re-init,
                     which destroys both.
  delivers_update    the /update skill lands, for both harnesses.
  refuses            no scaffold, and already-stamped scaffold, both refused.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FW = REPO / "init_agent.py"

# Historical generators. v5.13 is the last version before /update existed;
# v5.12 additionally emitted worker sub-agents, retired in v5.13.
LEGACY = {"v5.13": "649149b", "v5.12": "4700bb4"}

failures = []


def fail(test, msg):
    failures.append(f"[{test}] {msg}")


def git(*args, cwd=REPO):
    return subprocess.run(["git", *args], cwd=str(cwd),
                          capture_output=True, text=True)


def have_history():
    return all(git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0
               for sha in LEGACY.values())


def legacy_generator(tmp: Path, version: str) -> Path:
    """Extract a historical single-file generator. Both fixture versions
    predate the v5.17 package split, so one file is enough."""
    out = tmp / f"init_{version}.py"
    r = git("show", f"{LEGACY[version]}:init_agent.py")
    if r.returncode != 0:
        return None
    out.write_text(r.stdout)
    return out


_seq = 0


def make_scaffold(tmp: Path, version: str, size: str, harness: str) -> Path:
    global _seq
    _seq += 1
    root = tmp / f"proj{_seq}-{version}-{size}-{harness}"
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "."], cwd=str(root), check=True)
    gen = legacy_generator(tmp, version)
    subprocess.run([sys.executable, str(gen), "--name", "legacyproj",
                    "--description", "d", "--size", size,
                    "--harness", harness, "-y"],
                   cwd=str(root), capture_output=True, check=True)
    return root


def bootstrap(root: Path):
    return subprocess.run([sys.executable, str(FW), "--bootstrap-update"],
                          cwd=str(root), capture_output=True, text=True)


def test_stamp_is_honest(tmp):
    root = make_scaffold(tmp, "v5.13", "small", "claude")
    bootstrap(root)
    stamp = json.loads((root / ".ai/agent/framework.json").read_text())
    if stamp["framework_version"] is not None:
        fail("stamp_is_honest",
             f"claims version {stamp['framework_version']!r}; must be null so "
             "/update does not read the project as already current")
    if stamp["framework_files"]:
        fail("stamp_is_honest",
             "recorded a file list; must be empty so retirement falls to the "
             "orphan test rather than silently finding nothing to retire")
    for key, want in (("profile", "small"), ("harness", "claude"),
                      ("project", "legacyproj")):
        if stamp.get(key) != want:
            fail("stamp_is_honest", f"{key}={stamp.get(key)!r}, want {want!r}")


def test_touches_nothing(tmp):
    root = make_scaffold(tmp, "v5.13", "small", "claude")
    agents = root / "AGENTS.md"
    settings = root / ".claude/settings.json"
    agents.write_text(agents.read_text() + "\n## House rules\n\nNo vendor/.\n")
    cfg = json.loads(settings.read_text())
    cfg["permissions"]["allow"].append("Bash(make:*)")
    settings.write_text(json.dumps(cfg, indent=2))
    before = {p: p.read_bytes() for p in root.rglob("*")
              if p.is_file() and ".git" not in p.parts}

    bootstrap(root)

    for p, content in before.items():
        if not p.exists():
            fail("touches_nothing", f"deleted {p.relative_to(root)}")
        elif p.read_bytes() != content:
            fail("touches_nothing", f"modified {p.relative_to(root)}")
    if "House rules" not in agents.read_text():
        fail("touches_nothing", "lost user rules appended to AGENTS.md")
    if "make:" not in settings.read_text():
        fail("touches_nothing", "lost user permission in settings.json")


def test_delivers_update(tmp):
    for harness, rel in (("claude", ".claude/skills/update/SKILL.md"),
                         ("copilot", ".github/prompts/update.prompt.md")):
        root = make_scaffold(tmp, "v5.13", "small", harness)
        r = bootstrap(root)
        if r.returncode != 0:
            fail("delivers_update", f"{harness}: exit {r.returncode}: {r.stderr}")
        if not (root / rel).is_file():
            fail("delivers_update", f"{harness}: {rel} not written")
        if harness == "claude" and (root / ".github" / "prompts").exists():
            fail("delivers_update", "claude scaffold grew a copilot dir")
        if harness == "copilot" and (root / ".claude").exists():
            fail("delivers_update", "copilot scaffold grew a claude dir")


def test_refuses(tmp):
    empty = tmp / "empty"
    empty.mkdir()
    if bootstrap(empty).returncode == 0:
        fail("refuses", "accepted a directory with no scaffold")

    current = tmp / "current"
    current.mkdir()
    subprocess.run(["git", "init", "-q", "."], cwd=str(current), check=True)
    subprocess.run([sys.executable, str(FW), "--name", "p", "--description",
                    "d", "--size", "small", "--harness", "claude", "-y"],
                   cwd=str(current), capture_output=True, check=True)
    r = bootstrap(current)
    if r.returncode == 0:
        fail("refuses", "accepted an already-stamped current scaffold")


def main():
    if not have_history():
        print("SKIP: this checkout lacks the historical commits the fixtures "
              "need (shallow clone?)")
        return 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for t in (test_stamp_is_honest, test_touches_nothing,
                  test_delivers_update, test_refuses):
            try:
                t(tmp)
            except Exception as e:  # a crash is a failure, not a stack trace
                fail(t.__name__, f"raised {type(e).__name__}: {e}")
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("ok: 4 bootstrap tests passed against real v5.12/v5.13 scaffolds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
