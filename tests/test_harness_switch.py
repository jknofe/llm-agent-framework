#!/usr/bin/env python3
"""Regression tests for switching an existing scaffold's harness.

Run: python3 tests/test_harness_switch.py

Stdlib only. Scaffolds into throwaway directories and runs the real CLI, so
what is under test is the command a user actually types.

What it pins down, in order of how badly it would hurt to get wrong:

  no_two_live_sets   the old harness's command files must not survive the
                     switch. Two live sets answer the same slash commands out
                     of an AGENTS.md that now describes only one of them, and
                     the user cannot tell which one ran.
  user_files_kept    a skill the user added next to the framework's is theirs.
                     The generator only retires what its own stamp recorded,
                     because guessing wrong here deletes someone's work.
  recoverable        retired files are moved into the backup, never deleted.
  content_preserved  notes and the project-context section survive, as in any
                     other re-init.
  stamp_follows      the stamp records the new harness and only live files.
  not_a_switch       re-running with the same harness retires nothing.
  refusable          a switch is never silent: without -y it needs a yes, and
                     a non-TTY run (no yes available) writes nothing at all.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FW = REPO / "init_agent.py"
BACKUP = ".ai/agent/.harness-backup"

failures = []


def fail(test, msg):
    failures.append(f"[{test}] {msg}")


def run(root: Path, *args, stdin: str = None):
    return subprocess.run([sys.executable, str(FW), "--name", "t",
                           "--description", "d", *args],
                          cwd=str(root), capture_output=True, text=True,
                          input=stdin)


def make_scaffold(tmp: Path, harness: str, seq: int) -> Path:
    root = tmp / f"proj{seq}-{harness}"
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "."], cwd=str(root), check=True)
    r = run(root, "--harness", harness, "-y")
    if r.returncode != 0:
        raise RuntimeError(f"scaffold failed: {r.stderr}")
    return root


def stamp(root: Path) -> dict:
    return json.loads((root / ".ai/agent/framework.json").read_text())


def test_switch(tmp: Path):
    root = make_scaffold(tmp, "claude", 1)

    # A skill of the user's own, sitting next to the framework's.
    mine = root / ".claude/skills/my-own/SKILL.md"
    mine.parent.mkdir(parents=True, exist_ok=True)
    mine.write_text("mine\n")
    notes = root / ".ai/notes.md"
    notes.write_text(notes.read_text() + "\nHAND EDIT\n")
    agents = root / "AGENTS.md"
    agents.write_text(agents.read_text().replace(
        "<!-- Populated by /explore. Do not edit by hand. -->",
        "MODULE MAP: hand filled."))

    r = run(root, "--harness", "hermes", "-y")
    if r.returncode != 0:
        fail("switch", f"exit {r.returncode}: {r.stderr}")
        return

    if not (root / ".agents/skills/explore/SKILL.md").exists():
        fail("switch", "new harness skills not written")

    for gone in (".claude/skills/explore/SKILL.md", ".claude/settings.json",
                 "CLAUDE.md"):
        if (root / gone).exists():
            fail("no_two_live_sets", f"{gone} survived the switch")

    if not mine.exists():
        fail("user_files_kept", "a user-added skill was retired")
    if "my-own" not in r.stdout:
        fail("user_files_kept", "user-added skill not reported as left behind")

    for kept in (".claude/skills/explore/SKILL.md", "CLAUDE.md"):
        if not (root / BACKUP / "claude" / kept).exists():
            fail("recoverable", f"{kept} not in the backup")

    if "HAND EDIT" not in notes.read_text():
        fail("content_preserved", "notes.md was reverted")
    if "MODULE MAP" not in agents.read_text():
        fail("content_preserved", "project-context section was lost")
    if "Running the workflows in Hermes" not in agents.read_text():
        fail("content_preserved", "AGENTS.md still describes the old harness")

    recorded = stamp(root)
    if recorded["harness"] != "hermes":
        fail("stamp_follows", f"harness is {recorded['harness']}")
    stale = [f for f in recorded["framework_files"]
             if f.startswith(".claude") or f == "CLAUDE.md"]
    if stale:
        fail("stamp_follows", f"stamp still lists old-harness files: {stale}")
    missing = [f for f in recorded["framework_files"]
               if not (root / f).exists()]
    if missing:
        fail("stamp_follows", f"stamp lists files that do not exist: {missing}")


def test_not_a_switch(tmp: Path):
    root = make_scaffold(tmp, "hermes", 2)
    r = run(root, "--harness", "hermes", "-y")
    if "retired" in r.stdout or "Switched harness" in r.stdout:
        fail("not_a_switch", "same harness triggered a switch")
    if not (root / ".agents/skills/explore/SKILL.md").exists():
        fail("not_a_switch", "re-init lost the skills")


def test_refusable(tmp: Path):
    root = make_scaffold(tmp, "claude", 3)
    before = sorted(p.name for p in root.iterdir())
    r = run(root, "--harness", "copilot", stdin="n\n")
    if r.returncode == 0:
        fail("refusable", "declining the switch still returned success")
    if (root / ".github").exists():
        fail("refusable", "declining the switch still wrote the new harness")
    if sorted(p.name for p in root.iterdir()) != before:
        fail("refusable", "declining the switch changed the tree")


def main():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_switch(tmp)
        test_not_a_switch(tmp)
        test_refusable(tmp)
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("ok: 3 harness-switch tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
