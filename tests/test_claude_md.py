#!/usr/bin/env python3
"""The `CLAUDE.md` that imports `@AGENTS.md` on the claude harness
(CONCEPT.md section 81).

Run: python3 tests/test_claude_md.py

Stdlib only. Runs the real init_agent.py in temp projects. Covers: no
CLAUDE.md (one line written), one without the import (the line appended, the
rest byte-identical), one with it (untouched), the cases that count or do
not count as an import, re-init (idempotent, user text kept), the
`--ensure-agents-import` flag `/framework-update` runs, that the file is never
a recorded framework file nor deleted by a harness switch, and that the
other harnesses and the update reference get none.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INIT = REPO / "init_agent.py"
sys.path.insert(0, str(REPO))
from agentgen.scaffold import has_agents_import  # noqa: E402

FAILS = []
N = [0]


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def project():
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


def init(root, *flags, harness="claude"):
    return subprocess.run(
        [sys.executable, str(INIT), "--name", "p", "--description", "d",
         "--harness", harness, "-y", *flags],
        cwd=root, capture_output=True, text=True, input="n\n")


def ensure(root):
    return subprocess.run([sys.executable, str(INIT),
                           "--ensure-agents-import"], cwd=root,
                          capture_output=True, text=True)


def main():
    # absent: one line
    root = project()
    check(init(root).returncode == 0, "init works")
    cm = root / "CLAUDE.md"
    check(cm.read_text(encoding="utf-8") == "@AGENTS.md\n",
          f"absent: the single import line, got {cm.read_text()!r}")

    # present with the import: untouched, also on re-init and via the flag
    kept = "@AGENTS.md\n\n## Claude Code\n\nUse plan mode.\n"
    cm.write_text(kept, encoding="utf-8")
    init(root)
    check(cm.read_text(encoding="utf-8") == kept, "with import: re-init no-op")
    r = ensure(root)
    check(r.stdout.strip() == "CLAUDE.md: unchanged" and
          cm.read_text(encoding="utf-8") == kept, f"flag, with import: {r.stdout!r}")

    # present without the import: appended, the rest untouched
    for before in ("# Rules\n\nBe brief.\n", "# Rules\n\nNo newline at end"):
        cm.write_text(before, encoding="utf-8")
        init(root)
        after = cm.read_text(encoding="utf-8")
        check(after.startswith(before) and
              after[len(before):].lstrip("\n") == "@AGENTS.md\n" and
              has_agents_import(after),
              f"without import: appended after {before!r}, got {after!r}")
        init(root)
        check(cm.read_text(encoding="utf-8") == after,
              "without import: the second re-init changes nothing")
    cm.write_text("# Rules\n", encoding="utf-8")
    r = ensure(root)
    check(r.stdout.strip() == "CLAUDE.md: appended" and
          cm.read_text(encoding="utf-8") == "# Rules\n@AGENTS.md\n",
          f"flag, without import: {r.stdout!r}")
    cm.unlink()
    r = ensure(root)
    check(r.stdout.strip() == "CLAUDE.md: created" and
          cm.read_text(encoding="utf-8") == "@AGENTS.md\n",
          f"flag, absent: {r.stdout!r}")

    # what counts as an import, as Claude Code parses it
    for text, want in (("@AGENTS.md", True), ("see @AGENTS.md here", True),
                       ("  @AGENTS.md  \n", True),
                       ("`@AGENTS.md`", False),
                       ("```\n@AGENTS.md\n```\n", False),
                       ("Read AGENTS.md", False),
                       ("@docs/AGENTS.md", False), ("a@AGENTS.md", False),
                       ("@AGENTS.mdx", False), ("", False)):
        check(has_agents_import(text) == want, f"import({text!r}) is {want}")

    # a symlink to AGENTS.md already is AGENTS.md; a .claude/CLAUDE.md that
    # imports it counts as the project's CLAUDE.md
    root2 = project()
    init(root2)
    (root2 / "CLAUDE.md").unlink()
    (root2 / "CLAUDE.md").symlink_to("AGENTS.md")
    before = (root2 / "AGENTS.md").read_text(encoding="utf-8")
    init(root2)
    check((root2 / "AGENTS.md").read_text(encoding="utf-8") == before and
          (root2 / "CLAUDE.md").is_symlink(),
          "symlink to AGENTS.md: left alone, AGENTS.md not appended to")
    root3 = project()
    (root3 / ".claude").mkdir()
    (root3 / ".claude/CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    init(root3)
    check(not (root3 / "CLAUDE.md").exists(),
          ".claude/CLAUDE.md with the import: no second file")

    # never a framework file: not recorded, survives a harness switch
    stamp = json.loads((root / ".ai/agent/framework.json").read_text())
    check("CLAUDE.md" not in stamp["framework_files"],
          "CLAUDE.md is not in the recorded file list")
    cm.write_text("# mine\n@AGENTS.md\n", encoding="utf-8")
    init(root, harness="opencode")
    check(cm.read_text(encoding="utf-8") == "# mine\n@AGENTS.md\n",
          "a switch away from claude leaves the user's CLAUDE.md in place")

    # other harnesses and the reference get none; the flag says so
    for harness in ("copilot", "opencode"):
        other = project()
        init(other, harness=harness)
        check(not (other / "CLAUDE.md").exists(), f"{harness}: no CLAUDE.md")
        r = ensure(other)
        check(r.returncode == 0 and "not needed" in r.stdout and
              not (other / "CLAUDE.md").exists(),
              f"{harness}: the flag does nothing: {r.stdout!r}")
    ref = Path(tempfile.mkdtemp()) / "ref"
    subprocess.run([sys.executable, str(INIT), "--emit-reference", str(ref),
                    "--harness", "claude"], capture_output=True, check=True)
    check(not (ref / "CLAUDE.md").exists(), "the update reference has none")
    empty = Path(tempfile.mkdtemp())
    r = ensure(empty)
    check(r.returncode == 1 and not (empty / "CLAUDE.md").exists(),
          "no scaffold: the flag refuses and writes nothing")

    # the update body tells the updater to run the flag, not to judge
    skill = (root / ".claude/skills/framework-update/SKILL.md")
    init(root, harness="claude")
    text = skill.read_text(encoding="utf-8")
    check("--ensure-agents-import" in text and "never delete it" in text,
          "the update body runs the flag and never deletes CLAUDE.md")

    if FAILS:
        for m in FAILS:
            print(f"FAIL {m}")
        return 1
    print(f"ok: CLAUDE.md import, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
