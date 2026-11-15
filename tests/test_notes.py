#!/usr/bin/env python3
"""The freshness check of the notes (CONCEPT.md section 82) and the text the
SessionStart hook hands the model (section 83), both from `tasks.py`.

Run: python3 tests/test_notes.py

Stdlib only. Renders tasks.py into temp projects (a git repository, so the
path check has a file list) and checks, with no agent: no flag on clean
notes, each flag (size by lines and by bytes, a cited path that is gone, a
dead leaf link, an unlinked leaf) and each non-flag the check promises to
keep quiet about (bare file names, globs, placeholders, URLs, parent and
home paths, fenced blocks, comments, ignored paths, tails of existing
paths, `read/write`), exit codes, the `/task list` line, a missing hub,
binary and unreadable files, and the `--session` text: the stub is silent,
the hub is printed under its header, an over-cap hub is cut with one line,
the flags are bounded, exit is always 0.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from agentgen import content  # noqa: E402

FAILS = []
N = [0]
FLAG = "❗"


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def project():
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    tool = root / ".ai/agent/tools/tasks.py"
    tool.parent.mkdir(parents=True)
    tool.write_text(content.render_tool_tasks(), encoding="utf-8")
    (root / ".gitignore").write_text("build/\n.ai/\n", encoding="utf-8")
    return root


def run(root, *args):
    return subprocess.run([sys.executable,
                           str(root / ".ai/agent/tools/tasks.py"), *args],
                          capture_output=True, text=True)


def put(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    root = project()
    put(root, "src/app/main.py", "x\n")
    put(root, "docs/guide.md", "x\n")
    put(root, ".ai/notes.md",
        "# Project Notes\n"
        "- deploy order: db first, see `docs/guide.md`\n"
        "- entry is `src/app/main.py:12`, tail `app/main.py` and `main.py`\n"
        "- [infra](notes/infra.md) - hosts\n")
    put(root, ".ai/notes/infra.md", "hosts in `docs/guide.md`\n")
    r = run(root, "notes")
    check(r.returncode == 0 and r.stdout == "",
          f"clean notes: exit 0, no output: {r.returncode} {r.stdout!r}")

    # What must stay quiet.
    quiet = (
        "- bare `setup.py` and `config.yaml`, method `os.path`, `self.run`\n"
        "- glob `src/*.py`, `src/{a,b}.py`, `a/[x].md`\n"
        "- placeholder `notes/<topic>.md`, var `$HOME/x.md`, `${V}/y.md`\n"
        "- url `https://example.com/a/b.html`, `example.com/page.html`\n"
        "- dots `.../x.md`, sibling `../other/x.md`, home `~/git/x.md`, abs `/etc/x.conf`\n"
        "- planned: `src/later/new.py` is not there yet\n"
        "- the retired `src/old/x.py` was removed in 2.0\n"
        "- dir `iot/` and `src/app/` are not files\n"
        "- words `read/write`, `text/html`, `I/O`, `and/or`\n"
        "- command `python3 -m x/y.py run` and `git -C .ai log`\n"
        "- built `build/out/app.bin`, tail `app/main.py`\n"
        "```\ncat `gone/in/fence.md`\n```\n"
        "<!-- `gone/in/comment.md` -->\n")
    put(root, ".ai/notes.md", "# Project Notes\n[infra](notes/infra.md)\n"
        + quiet)
    r = run(root, "notes")
    check(r.stdout == "" and r.returncode == 0,
          f"quiet cases give no flag: {r.stdout!r}")

    # What must flag.
    put(root, ".ai/notes.md",
        "# Project Notes\n- see `src/gone/old.py` and `docs/gone.md`, "
        "`lib/` and `docs/guide.md`\n- [x](notes/dead.md) - gone\n"
        "- [infra](notes/infra.md)\n")
    put(root, ".ai/notes/loose.md", "no link\n")
    put(root, ".ai/notes/infra.md", "see `ops/runbook.md`\n")
    r = run(root, "notes")
    out = r.stdout
    check(r.returncode == 1, f"flags give exit 1: {r.returncode} {out!r}")
    check(all(ln.startswith(f"- {FLAG} ") for ln in out.splitlines()),
          f"every line is a flag line: {out!r}")
    check("notes.md: cites `src/gone/old.py`, `docs/gone.md`, "
          "which does not exist" in out, f"missing paths named: {out!r}")
    check("cites" in out and "`docs/guide.md`" not in out.split("cites")[1].split("\n")[0],
          "an existing path is not named")
    check("notes.md: links `notes/dead.md`" in out, f"dead link: {out!r}")
    check("notes/loose.md: no line of notes.md links it" in out,
          f"unlinked leaf: {out!r}")
    check("notes/infra.md: cites `ops/runbook.md`" in out,
          f"leaves are checked for paths: {out!r}")
    check(all(len(ln) < 200 for ln in out.splitlines()), "lines are short")

    # Size, by lines and by bytes.
    for leaf in (root / ".ai/notes").glob("*.md"):
        leaf.unlink()
    put(root, ".ai/notes.md", "\n".join(["- a"] * 100) + "\n")
    check(run(root, "notes").stdout == "", "exactly 100 lines is fine")
    put(root, ".ai/notes.md", "\n".join(["- a"] * 101) + "\n")
    out = run(root, "notes").stdout
    check("notes.md: 101 lines (cap 100)" in out, f"line cap: {out!r}")
    put(root, ".ai/notes.md", "- " + "w" * 8100 + "\n")
    out = run(root, "notes").stdout
    check("bytes (cap 8000)" in out and "lines (cap" not in out,
          f"byte cap: {out!r}")

    # Odd input never raises.
    (root / ".ai/notes.md").write_bytes(b"\x00\x01\xff binary \x00")
    r = run(root, "notes")
    check("Traceback" not in r.stderr and "not text" in r.stdout,
          f"binary hub: one line: {r.stdout!r} {r.stderr!r}")
    (root / ".ai/notes.md").write_bytes(b"caf\xe9 `docs/guide.md`\n")
    r = run(root, "notes")
    check(r.returncode == 0 and r.stderr == "", "invalid utf-8 is fine")
    (root / ".ai/notes.md").unlink()
    r = run(root, "notes")
    check(r.returncode == 0 and r.stdout == "" and r.stderr == "",
          "missing hub: nothing, exit 0")
    put(root, ".ai/notes.md", "# Project Notes\n- ok\n")
    os.chmod(root / ".ai/notes.md", 0)
    r = run(root, "notes")
    check("Traceback" not in r.stderr, f"unreadable hub: {r.stderr!r}")
    if os.geteuid() != 0:
        check("unreadable" in r.stdout, f"unreadable named: {r.stdout!r}")
    os.chmod(root / ".ai/notes.md", 0o644)
    put(root, ".ai/notes.md", "# Project Notes\n- see `gone/x.md`\n")
    os.symlink("/nonexistent", root / ".ai/notes/broken.md")
    r = run(root, "notes")
    check("Traceback" not in r.stderr, f"dangling leaf: {r.stderr!r}")
    os.unlink(root / ".ai/notes/broken.md")

    # Without a repository the path check stays silent.
    plain = Path(tempfile.mkdtemp())
    tool = plain / ".ai/agent/tools/tasks.py"
    tool.parent.mkdir(parents=True)
    tool.write_text(content.render_tool_tasks(), encoding="utf-8")
    put(plain, ".ai/notes.md", "# Project Notes\n- see `gone/x.md`\n")
    r = run(plain, "notes")
    check(r.stdout == "" and r.returncode == 0,
          f"no git: paths not flagged: {r.stdout!r}")

    # /task list: the flags close the output only when there are any.
    r = run(root, "list")
    check("gone/x.md" in r.stdout and r.returncode == 0,
          f"no tasks: list shows notes flags: {r.stdout!r}")
    put(root, ".ai/notes.md", "# Project Notes\n- ok\n")
    r = run(root, "list")
    check("notes" not in r.stdout.replace("No tasks yet", ""),
          f"clean notes: list says nothing: {r.stdout!r}")
    put(root, ".ai/tasks/t1/task.md",
        "---\nid: t1\ntitle: T\ntype: change\nstatus: planned\n"
        "updated: 2026-01-01\n---\n## Done when\n- [ ] c\n## Steps\n"
        "- [ ] a\n## Findings\n")
    put(root, ".ai/notes.md", "# Project Notes\n- see `gone/x.md`\n")
    r = run(root, "list")
    lines = r.stdout.rstrip("\n").splitlines()
    check(lines[-1].startswith(f"- {FLAG} notes.md: cites `gone/x.md`"),
          f"table path: the notes flag is the last line: {lines[-1]!r}")
    put(root, ".ai/notes.md", "# Project Notes\n- ok\n")
    check("- " + FLAG not in run(root, "list").stdout,
          "table path: clean notes add no flag")

    # --session
    stub = content.render_notes_stub()
    put(root, ".ai/notes.md", stub)
    r = run(root, "notes", "--session")
    check(r.returncode == 0 and r.stdout == "",
          f"the scaffold's stub prints nothing: {r.stdout!r}")
    (root / ".ai/notes.md").unlink()
    r = run(root, "notes", "--session")
    check(r.returncode == 0 and r.stdout == "", "missing hub prints nothing")
    put(root, ".ai/notes.md", stub + "- db first, then app\n")
    r = run(root, "notes", "--session")
    head = r.stdout.splitlines()[0]
    check(".ai/notes.md" in head and r.returncode == 0,
          f"header names the file: {head!r}")
    check("- db first, then app" in r.stdout and "<!--" not in r.stdout
          and "Running memory" not in r.stdout,
          f"hub printed, authoring comment stripped: {r.stdout!r}")
    check("cut" not in r.stdout and "Notes check" not in r.stdout,
          "short clean hub: no cut line, no flags")
    big = "# Project Notes\n" + "".join(f"- line {i}\n" for i in range(150))
    put(root, ".ai/notes.md", big)
    r = run(root, "notes", "--session")
    out = r.stdout.splitlines()
    check("- line 98" in out and "- line 99" not in out,
          "capped head: 100 lines with the title")
    check(sum("cut after 100 of 151 lines" in ln for ln in out) == 1
          and "rest is in `.ai/notes.md`" in out[-1],
          f"one cut line, last: {out[-2:]!r}")
    check("notes.md: 151 lines" not in r.stdout,
          "the size flag is not repeated after the cut line")
    wide = "# Project Notes\n" + "".join("- " + "w" * 98 + "\n"
                                        for _ in range(95))
    put(root, ".ai/notes.md", wide)
    r = run(root, "notes", "--session")
    check(len(r.stdout.encode()) < 9500 and "cut after" in r.stdout,
          f"the byte cap cuts too: {len(r.stdout)}")
    many = "# Project Notes\n- " + " ".join(
        f"`a{i}/x.md`" for i in range(4)) + "\n" + "".join(
        f"- [l{i}](notes/l{i}.md)\n" for i in range(5))
    put(root, ".ai/notes.md", many)
    put(root, ".ai/notes/o1.md", "x\n")
    put(root, ".ai/notes/o2.md", "x\n")
    r = run(root, "notes", "--session")
    flags = [ln for ln in r.stdout.splitlines() if ln.startswith("- ")
             and FLAG in ln]
    check(len(flags) == 3 and "... and" in r.stdout and r.returncode == 0,
          f"at most three flag lines, then a count: {r.stdout!r}")
    (root / ".ai/notes.md").write_bytes(b"\x00bin")
    r = run(root, "notes", "--session")
    check(r.returncode == 0 and r.stdout == "" and "Traceback" not in r.stderr,
          "binary hub: silent in a session")

    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: notes check, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
