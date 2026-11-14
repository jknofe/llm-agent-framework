#!/usr/bin/env python3
"""Path-scoped notes leaves on Claude Code (CONCEPT.md section 89): the link
step `tasks.py notes --link` and the freshness flags that go with it.

Run: python3 tests/test_notes_link.py

Stdlib only. Scaffolds real claude and opencode projects with init_agent.py
(a git repository, so the gitignore line has a place) and checks, with no
agent: a link per leaf with `paths:` (relative, into `.ai/notes/`), retarget,
removal when the leaf is deleted or loses `paths:`, idempotence, a leaf
without frontmatter or with a frontmatter that cannot be trusted left
unlinked, a user's own file, own link and own prefixed file under
`.claude/rules/` never touched, the one gitignore line, init and re-init
doing the step, the other harness doing nothing, a filesystem that cannot
make the link not failing, the frontmatter not read as note text, and the
flags: a glob that matches nothing (every glob form), a link missing or
stale, a frontmatter that cannot be linked. `--session` is unchanged.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FAILS = []
N = [0]
PREFIX = "ai-notes-"
LINE = ".claude/rules/ai-notes-*.md"


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def init(root):
    return subprocess.run(
        [sys.executable, str(REPO / "init_agent.py"), "--name", "p",
         "--description", "d", "--harness", HARNESS[0], "-y"], cwd=root,
        capture_output=True, text=True, input="n\n")


HARNESS = ["claude"]


def project(harness="claude"):
    HARNESS[0] = harness
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    init(root)
    return root


def tasks(root, *args):
    return subprocess.run([sys.executable,
                           str(root / ".ai/agent/tools/tasks.py"), *args],
                          capture_output=True, text=True, cwd=root)


def put(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def leaf(*globs):
    return "---\npaths:\n" + "".join(f'  - "{g}"\n' for g in globs) + \
        "---\n# Topic\n- a gotcha\n"


def rules(root):
    d = root / ".claude/rules"
    return sorted(p.name for p in d.iterdir()) if d.is_dir() else []


def gitignore_count(root):
    gi = root / ".gitignore"
    return gi.read_text().splitlines().count(LINE) if gi.exists() else 0


def main():
    root = project()
    put(root, "src/a.py", "x = 1\n")
    put(root, ".ai/notes/api.md", leaf("src/**"))
    put(root, ".ai/notes/plain.md", "# Plain\n- no frontmatter\n")
    r = tasks(root, "notes", "--link")
    check(r.returncode == 0, f"exit 0: {r.returncode}")
    check(rules(root) == [PREFIX + "api.md"], f"one link: {rules(root)}")
    link = root / ".claude/rules" / (PREFIX + "api.md")
    check(link.is_symlink() and os.readlink(link) == "../../.ai/notes/api.md",
          "relative link into .ai/notes")
    check(link.read_text().startswith("---\npaths:"), "the link resolves")
    check("linked .claude/rules/ai-notes-api.md" in r.stdout, r.stdout)
    check(gitignore_count(root) == 1, "gitignore line added once")
    ig = subprocess.run(["git", "check-ignore", "-q", str(link)], cwd=root)
    check(ig.returncode == 0, "git ignores the link")
    st = subprocess.run(["git", "status", "--short"], cwd=root,
                        capture_output=True, text=True).stdout
    check("rules" not in st.replace(".gitignore", ""), f"link untracked: {st}")

    # idempotent
    r = tasks(root, "notes", "--link")
    check("up to date (1 link)" in r.stdout and rules(root) == [PREFIX + "api.md"],
          f"second run: {r.stdout!r}")
    check(gitignore_count(root) == 1, "gitignore line still once")
    r = tasks(root, "notes", "--link", "--quiet")
    check(r.stdout == "", f"--quiet is silent when nothing to do: {r.stdout!r}")

    # the user's own things under .claude/rules
    put(root, ".claude/rules/mine.md", "my rule\n")
    os.symlink("../../src/a.py", root / ".claude/rules/mine-link.md")
    os.symlink("/etc/hosts", root / ".claude/rules/ai-notes-ext.md")
    put(root, ".claude/rules/ai-notes-top.md", "user file with our prefix\n")
    put(root, ".ai/notes/top.md", leaf("src/**"))
    before = {n: (root / ".claude/rules" / n).is_symlink() for n in rules(root)}
    r = tasks(root, "notes", "--link")
    check("ai-notes-top.md exists and is not a link of this tool" in r.stdout,
          f"blocked name said: {r.stdout!r}")
    check((root / ".claude/rules/ai-notes-top.md").read_text()
          == "user file with our prefix\n", "user file with prefix untouched")
    check((root / ".claude/rules/mine.md").read_text() == "my rule\n",
          "user file untouched")
    check(os.readlink(root / ".claude/rules/mine-link.md")
          == "../../src/a.py", "user link untouched")
    check(os.readlink(root / ".claude/rules/ai-notes-ext.md") == "/etc/hosts",
          "a prefixed link outside .ai/notes is not ours")
    (root / ".ai/notes/top.md").unlink()

    # retarget
    (root / ".ai/notes/other.md").write_text("x\n")
    link.unlink()
    os.symlink("../../.ai/notes/other.md", link)
    r = tasks(root, "notes", "--link")
    check(os.readlink(link) == "../../.ai/notes/api.md"
          and "relinked" in r.stdout, f"retargeted: {r.stdout!r}")

    # leaf edited to drop paths, and deleted
    put(root, ".ai/notes/api.md", "# Topic\n- no more paths\n")
    r = tasks(root, "notes", "--link")
    check(PREFIX + "api.md" not in rules(root)
          and "unlinked .claude/rules/ai-notes-api.md" in r.stdout,
          f"removed on lost paths: {rules(root)}")
    put(root, ".ai/notes/api.md", leaf("src/**"))
    tasks(root, "notes", "--link")
    check(PREFIX + "api.md" in rules(root), "back")
    (root / ".ai/notes/api.md").unlink()
    r = tasks(root, "notes", "--link")
    check(PREFIX + "api.md" not in rules(root), "removed on deleted leaf")
    check(sorted(rules(root)) == ["ai-notes-ext.md", "ai-notes-top.md",
                                  "mine-link.md", "mine.md"],
          f"only ours went: {rules(root)}")

    # frontmatter that cannot be trusted is not linked, and is flagged
    for body in ('---\npaths:\n  - **/*.py\n---\n# x\n',   # YAML alias
                 '---\npaths: src/**\n---\n# x\n',
                 '---\ndescription: x\n---\n# x\n',
                 '---\npaths:\n---\n# x\n'):
        put(root, ".ai/notes/bad.md", body)
        r = tasks(root, "notes", "--link")
        check(PREFIX + "bad.md" not in rules(root), f"not linked: {body!r}")
        f = tasks(root, "notes").stdout
        check("notes/bad.md" in f and "not linked" in f, f"flagged: {f!r}")
    (root / ".ai/notes/bad.md").unlink()

    # nested leaf
    put(root, ".ai/notes/db/mig.md", leaf("src/**"))
    tasks(root, "notes", "--link")
    check(PREFIX + "db--mig.md" in rules(root), f"nested: {rules(root)}")
    (root / ".ai/notes/db/mig.md").unlink()
    tasks(root, "notes", "--link")

    # init and re-init do the step
    put(root, ".ai/notes/api.md", leaf("src/**"))
    init(root)
    check(PREFIX + "api.md" in rules(root), "re-init links")
    check(gitignore_count(root) == 1, "gitignore once after re-init")

    # a filesystem that cannot link: .claude/rules is a file
    bare = project()
    put(bare, "src/a.py", "x\n")
    put(bare, ".ai/notes/api.md", leaf("src/**"))
    (bare / ".claude/rules").write_text("not a dir\n")
    r = tasks(bare, "notes", "--link")
    check(r.returncode == 0 and "could not create symlinks" in r.stdout
          and len(r.stdout.strip().splitlines()) == 1, f"no symlinks: {r.stdout!r}")

    # freshness flags
    fl = project()
    for rel in ("src/a.ts", "lib/b.py", "README.md"):
        put(fl, rel, "x\n")
    put(fl, ".ai/notes.md", "# Notes\n- [api](notes/api.md) - gotchas\n")
    put(fl, ".ai/notes/api.md", leaf(
        "src/**", "**/*.py", "*.md", "/*.md", "src/**/*.{ts,tsx}", "src/*.ts",
        "/*.py", "src/*.py", "docs/**"))
    out = tasks(fl, "notes").stdout
    check('`/*.py`' in out and '`src/*.py`' in out and '`docs/**`' in out
          and "matches no file" in out, f"dead globs named: {out!r}")
    check(out.count("matches no file") == 1 and "`src/**`" not in out
          and "`*.md`" not in out and "`**/*.ts`" not in out,
          f"live globs not flagged: {out!r}")
    check("link(s) missing or stale" in out, f"link missing flagged: {out!r}")
    put(fl, ".ai/notes/api.md", leaf("src/**", "*.md") + "- cites `src/a.ts`\n")
    out = tasks(fl, "notes").stdout
    check("matches no file" not in out and "cites" not in out
          and "link(s) missing" in out, f"clean but unlinked: {out!r}")
    tasks(fl, "notes", "--link")
    out = tasks(fl, "notes")
    check(out.stdout == "" and out.returncode == 0,
          f"no flag once linked: {out.stdout!r}")
    check("paths:" not in tasks(fl, "notes", "--session").stdout
          and "src/**" not in tasks(fl, "notes", "--session").stdout,
          "--session prints the hub only")
    # frontmatter is not note text: a cited-looking path inside it is no cite
    put(fl, ".ai/notes/api.md", '---\npaths:\n  - "src/**"\n---\n- `src/gone.ts`\n')
    out = tasks(fl, "notes").stdout
    check("src/gone.ts" in out, "body still checked for cites")
    # a stale link is flagged
    (fl / ".ai/notes/api.md").unlink()
    out = tasks(fl, "notes").stdout
    check("link(s) missing or stale" in out, f"stale link flagged: {out!r}")

    # the other harness
    oc = project("opencode")
    put(oc, "src/a.py", "x\n")
    put(oc, ".ai/notes/api.md", leaf("src/**"))
    r = tasks(oc, "notes", "--link")
    check(r.returncode == 0 and "nothing to do" in r.stdout
          and "Claude Code only" in r.stdout
          and len(r.stdout.strip().splitlines()) == 1, f"opencode: {r.stdout!r}")
    check(not (oc / ".claude").exists(), "opencode: no .claude")
    check(tasks(oc, "notes", "--link", "--quiet").stdout == "", "quiet")
    put(oc, ".ai/notes/dead.md", leaf("nowhere/**"))
    check("matches no file" in tasks(oc, "notes").stdout
          and "link(s)" not in tasks(oc, "notes").stdout,
          "opencode: glob flag yes, link flag no")

    if FAILS:
        for x in FAILS:
            print(f"FAIL {x}")
        return 1
    print(f"ok: notes links, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
