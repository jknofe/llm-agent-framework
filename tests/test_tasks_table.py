#!/usr/bin/env python3
"""Regression test for tasks.py, the script behind /task.

`tasks.py list` is the whole answer of `/task list` and `tasks.py resolve`
decides whether `/task <id>` creates or works a task (CONCEPT.md, Pillar 2),
so everything both promise is checked here without an agent. Table: live
tasks only, archive counted, sort order, emoji columns and legend, the flags,
the resume pointer, a typo kept visible, no ANSI codes through a pipe, the two
empty states. Resolver: every verdict, case-insensitive ids, near-duplicate
ids, the resume pointer. Bookkeeping: start and finish set status, the
blocked reason and the resume pointer, and finish done refuses an unmet
gate. Builds fixture task files in a temp dir; stdlib
only.

Usage: python3 tests/test_tasks_table.py
"""
import datetime
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentgen import content  # noqa: E402

TODAY = datetime.date.today()
OLD = (TODAY - datetime.timedelta(days=30)).isoformat()
NEW = TODAY.isoformat()
FAILS = []
CHECKED = [0]


def check(cond, msg):
    CHECKED[0] += 1
    if not cond:
        FAILS.append(msg)


def task(root, rel, tid, title, typ, status, updated, extra="",
         done_when="- [ ] c", steps="- [x] a\n- [ ] b", findings=""):
    d = root / ".ai" / "tasks" / rel
    d.mkdir(parents=True, exist_ok=True)
    (d / "task.md").write_text(
        f"---\nid: {tid}\ntitle: {title}\ntype: {typ}\nstatus: {status}\n"
        f"created: {OLD}\nupdated: {updated}\n{extra}---\n## Goal\nx\n"
        f"## Done when\n{done_when}\n## Steps\n{steps}\n## Findings\n"
        f"{findings}## Outcome\n## Notes\n", encoding="utf-8")


def run(root, *args, env_extra=None):
    env = dict(os.environ)
    env.pop("NO_COLOR", None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(root / ".ai/agent/tools/tasks.py"), *args],
        capture_output=True, text=True, env=env, check=True).stdout


def attempt(root, *args):
    """Run tasks.py without failing on a non-zero exit."""
    return subprocess.run(
        [sys.executable, str(root / ".ai/agent/tools/tasks.py"), *args],
        capture_output=True, text=True)


FLAG_CHAR = "\u2757"


def verdict(root, *args):
    """First line of `tasks.py resolve ...`, skipping a `#` comment."""
    lines = [ln for ln in run(root, "resolve", *args).splitlines()
             if not ln.startswith("#")]
    return lines[0] if lines else ""


def row(out, tid):
    for line in out.splitlines():
        if line.startswith("|") and f"| {tid} |" in line:
            return [c.strip() for c in line.strip("|").split(" | ")]
    return None


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tool = root / ".ai/agent/tools/tasks.py"
        tool.parent.mkdir(parents=True)
        tool.write_text(content.render_tool_tasks(), encoding="utf-8")

        # Empty state 1: no tasks directory.
        out = run(root)
        check("`.ai/tasks/` does not exist" in out, "missing-dir message")

        task(root, "stale", "stale", "Old work", "bug", "in-progress", OLD)
        task(root, "fresh", "fresh", "Pipe | title", "change", "in-progress",
             NEW)
        task(root, "why", "why", "Blocked with reason", "test", "blocked",
             NEW, extra="blocked: waiting for rig access\n")
        task(root, "noreason", "noreason", "Blocked, no reason",
             "investigation", "blocked", NEW)
        reviewed = f"- {NEW} Review: inline: criteria met.\n"
        task(root, "half", "half", "Half done", "change", "done", NEW,
             done_when="- [x] c\n- [ ] d", findings=reviewed)
        task(root, "full", "full", "Full done", "change", "done", NEW,
             done_when="- [x] c", findings=reviewed)
        # "review" in the Goal or Notes does not count, only in Findings.
        task(root, "unrev", "unrev", "No review", "change", "done", OLD,
             done_when="- [x] c", findings="- found x, see Notes\n",
             extra="")
        task(root, "plan", "plan", "Planned", "test", "planned", NEW)
        task(root, "typo", "typo", "Typo type", "bugg", "planned", NEW)
        task(root, "quoted", "quoted", '"Quoted: title"', "'bug'", "planned",
             NEW)
        task(root, "_archive/old", "old", "Archived", "change", "done", OLD)
        (root / ".ai/.current").write_text("task: fresh\n", encoding="utf-8")

        out = run(root)
        lines = out.splitlines()

        # Live tasks only; archive counted in the footer.
        check(row(out, "old") is None, "archived task listed")
        check("1 archived (not listed)" in out, "archive count in footer")

        # Sort: in-progress, blocked, planned, done; then updated, then id.
        order = [ln.split(" | ")[1] for ln in lines
                 if ln.startswith("| ") and " | " in ln
                 and not ln.startswith("| | ID")]
        check(order == ["stale", "fresh", "noreason", "why", "plan",
                        "quoted", "typo", "unrev", "full", "half"],
              f"sort order: {order}")

        # Emoji only for known type and status; unknown value stays text.
        r = row(out, "stale")
        check(r and r[2] == "🐞" and r[3] == "🔄", f"stale row: {r}")
        r = row(out, "why")
        check(r and r[2] == "🧪" and r[3] == "⛔", f"blocked row: {r}")
        r = row(out, "full")
        check(r and r[2] == "🔧" and r[3] == "✅", f"done row: {r}")
        r = row(out, "noreason")
        check(r and r[2] == "🔍", f"investigation row: {r}")
        r = row(out, "plan")
        check(r and r[3] == "📋", f"planned row: {r}")
        r = row(out, "typo")
        check(r and r[2] == "bugg", f"typo kept as text: {r}")

        # Quoted YAML scalars are unquoted (8.10).
        r = row(out, "quoted")
        check(r and r[4] == "Quoted: title" and r[2] == "🐞",
              f"quoted title and type: {r}")

        # Progress counts and pipe escaping.
        r = row(out, "half")
        check(r and r[5] == "1/2" and r[6] == "1/2", f"progress: {r}")
        check("Pipe \\| title" in out, "pipe in title escaped")

        # Resume pointer.
        r = row(out, "fresh")
        check(r and r[0] == "👉", f"pointer on fresh: {r}")
        check("👉 marks the resume pointer in `.ai/.current` (fresh)" in out,
              "pointer footer line")

        # Legend directly under the table, before the flags.
        legend = [i for i, ln in enumerate(lines) if ln.startswith("Legend:")]
        last_row = max(i for i, ln in enumerate(lines) if ln.startswith("|"))
        check(legend and legend[0] == last_row + 2, "legend under table")
        for word in ("🔧 change", "🐞 bug", "🔍 investigation", "🧪 test",
                     "🔄 in-progress", "⛔ blocked", "📋 planned", "✅ done",
                     "👉 resume pointer", "❗ needs a look"):
            check(legend and word in lines[legend[0]], f"legend has {word}")

        # The three flags, and nothing flagged that should not be.
        check("❗ stale: in-progress, not updated for 30 days." in out,
              "stale flag")
        check("❗ why: blocked: waiting for rig access." in out,
              "blocked reason flag")
        check("❗ noreason: blocked: no reason recorded." in out,
              "blocked without reason flag")
        check("❗ half: done with 1 of 2 done-when criteria unchecked." in out,
              "half-done flag")
        check("❗ unrev: done without a review line in Findings." in out,
              "unreviewed flag")
        check("❗ half: done without a review line" not in out,
              "reviewed task flagged as unreviewed")
        for quiet in ("fresh", "full", "plan"):
            check(f"❗ {quiet}:" not in out, f"{quiet} flagged")

        # Footer summary in status order.
        check("🔄 2 in-progress, ⛔ 2 blocked, 📋 3 planned, ✅ 3 done; "
              "1 archived (not listed)." in out, "footer summary")

        # No ANSI through a pipe, which is how the agent reads it.
        check("\x1b[" not in out, "ANSI codes in piped output")

        # Retired 7.x check stays gone (8.4).
        check(".ai/changes" not in out, "7.x changes/ check came back")
        check(run(root, "list") == out, "`list` differs from no argument")

        # Resolver (9.0): one verdict per case, id as it is on disk.
        check(verdict(root, "plan") == "DO plan status=planned type=test",
              "resolve planned task")
        check(verdict(root, "why").startswith("DO why status=blocked"),
              "resolve blocked task")
        check(verdict(root, "full") == "DONE full", "resolve done task")
        check(verdict(root, "FRESH").startswith("DO fresh "),
              "resolve is case-insensitive")
        check(verdict(root, "old") == "ARCHIVED old", "resolve archived")
        check(verdict(root, "brand-new") == "CREATE brand-new",
              "resolve unknown id")
        near = run(root, "resolve", "review-no")
        check(near.startswith("CREATE review-no")
              and "SIMILAR" not in near, "no false near-duplicate")
        near = run(root, "resolve", "done-half")
        check("SIMILAR half (done)" in near, f"near-duplicate: {near!r}")
        check(verdict(root, "two words").startswith("INVALID"),
              "resolve rejects a title as id")
        check(verdict(root, "../etc").startswith("INVALID"),
              "resolve rejects a path")
        check(verdict(root) == "DO fresh status=in-progress type=change",
              "resolve without id follows the resume pointer")
        (root / ".ai/.current").unlink()
        check(verdict(root) == "NONE", "resolve without id or pointer")
        (root / ".ai/.current").write_text("task: fresh\n", encoding="utf-8")

        # start / finish: the bookkeeping do.md routes through the script.
        task(root, "keep", "keep", "Keep", "change", "planned", OLD,
             done_when="- [ ] c1", steps="- [ ] s")
        tf = root / ".ai/tasks/keep/task.md"
        body = tf.read_text(encoding="utf-8").split("\n---\n", 1)[1]
        out = run(root, "start", "KEEP")
        fm = tf.read_text(encoding="utf-8")
        check(out.startswith("STARTED keep"), f"start verdict: {out!r}")
        check("status: in-progress" in fm and f"updated: {NEW}" in fm,
              "start sets status and updated")
        check(fm.split("\n---\n", 1)[1] == body,
              "start leaves the body byte for byte")
        cur = (root / ".ai/.current").read_text(encoding="utf-8")
        check(cur.startswith("task: keep\n") and "replaced the pointer to "
              "fresh" in out, "start replaces another task's pointer")
        (root / ".ai/.current").write_text(cur + "modified: a.py\n",
                                           encoding="utf-8")
        run(root, "start", "keep")
        check("a.py" in (root / ".ai/.current").read_text(encoding="utf-8"),
              "start keeps a pointer that already names the task")

        r = attempt(root, "finish", "keep", "done")
        check(r.returncode == 1 and "1 of 1 done-when criteria unticked" in
              r.stdout and "no `Review:` line" in r.stdout,
              f"finish done refuses an unmet gate: {r.stdout!r}")
        check("status: in-progress" in tf.read_text(encoding="utf-8"),
              "a refused finish changes nothing")
        check(attempt(root, "finish", "keep", "blocked").returncode == 1,
              "finish blocked needs a reason")
        run(root, "finish", "keep", "blocked", "no", "toolchain:", "here")
        fm = tf.read_text(encoding="utf-8")
        check("status: blocked\nblocked: no toolchain: here\n" in fm,
              "finish blocked writes status and reason")
        check((root / ".ai/.current").exists(), "blocked keeps the pointer")
        check(f"{FLAG_CHAR} keep: blocked: no toolchain: here." in run(root),
              "the table flags the blocked reason")
        run(root, "start", "keep")
        check("blocked:" not in tf.read_text(encoding="utf-8"),
              "start clears the block")
        tf.write_text(tf.read_text(encoding="utf-8")
                      .replace("- [ ] c1", "- [x] c1")
                      .replace("## Findings\n",
                               "## Findings\n- x Review: inline: ok\n"),
                      encoding="utf-8")
        out = run(root, "finish", "keep", "done")
        check(out.startswith("DONE keep") and "git -C .ai" in out,
              f"finish done: {out!r}")
        check("status: done" in tf.read_text(encoding="utf-8")
              and not (root / ".ai/.current").exists(),
              "finish done sets status and deletes the pointer")
        check(attempt(root, "start", "keep").returncode == 1,
              "start refuses a done task")
        check(attempt(root, "finish", "nope", "done").returncode == 1,
              "finish refuses an unknown task")
        check(attempt(root, "finish", "keep", "maybe").returncode == 2,
              "finish rejects an unknown state")
        (root / ".ai/.current").write_text("task: fresh\n", encoding="utf-8")

        # Empty state 2: tasks directory with only archived tasks.
        for d in (root / ".ai/tasks").iterdir():
            if d.name != "_archive":
                (d / "task.md").unlink()
                d.rmdir()
        out = run(root)
        check("No live tasks in `.ai/tasks/` (1 archived)" in out,
              "only-archived message")
        check(run(root, "tree") == out.replace("No live tasks",
              "No live tasks"), "tree only-archived message")
        (root / ".ai/tasks/_archive/old/task.md").unlink()
        (root / ".ai/tasks/_archive/old").rmdir()
        (root / ".ai/tasks/_archive").rmdir()
        (root / ".ai/tasks").rmdir()
        check(run(root, "tree") == run(root), "tree missing-dir message")

    # Tree view (10.2, independents on the first level since 10.4), in a
    # fresh temp dir: a 3-level chain, a diamond, independents, a cycle, an unknown dep, a blocked task, and the
    # resume pointer on a nested task.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tool = root / ".ai/agent/tools/tasks.py"
        tool.parent.mkdir(parents=True)
        tool.write_text(content.render_tool_tasks(), encoding="utf-8")

        task(root, "root-task", "root-task", "Root", "change",
             "in-progress", NEW)
        task(root, "mid-task", "mid-task", "Mid", "bug", "blocked", NEW,
             extra="depends: root-task\nblocked: waits for root\n")
        task(root, "leaf-task", "leaf-task", "Leaf", "test", "planned",
             OLD, extra="depends: mid-task\n")
        # Diamond: depends on two roots, nests under the first in sort
        # order (both planned, same updated: id decides, root-a first).
        task(root, "root-a", "root-a", "Root A", "change", "planned", NEW)
        task(root, "root-b", "root-b", "Root B", "change", "planned", NEW)
        task(root, "diamond", "diamond", "Diamond", "change", "planned",
             NEW, extra="depends: root-a, root-b\n")
        # Diamond into the same subtree: extra deps on the subtree's own
        # root must not emit the task a second time at the top level.
        task(root, "deep-a", "deep-a", "Deep A", "change", "planned",
             NEW, extra="depends: root-task, mid-task\n")
        task(root, "solo-1", "solo-1", "Solo 1", "test", "planned", NEW)
        task(root, "solo-2", "solo-2", "Solo 2", "investigation",
             "planned", OLD)
        task(root, "cyc-a", "cyc-a", "Cycle A", "change", "planned", NEW,
             extra="depends: cyc-b\n")
        task(root, "cyc-b", "cyc-b", "Cycle B", "change", "planned", OLD,
             extra="depends: cyc-a\n")
        task(root, "cyc-tail", "cyc-tail", "Waits on cycle", "change",
             "planned", NEW, extra="depends: cyc-a\n")
        task(root, "self-dep", "self-dep", "Self dep", "change",
             "planned", NEW, extra="depends: self-dep\n")
        task(root, "ghost", "ghost", "Ghost dep", "change", "planned",
             NEW, extra="depends: no-such-task\n")
        task(root, "done-root", "done-root", "Done root", "change",
             "done", NEW, done_when="- [x] c", findings=reviewed)
        task(root, "waits-done", "waits-done", "Waits on done", "change",
             "planned", NEW, extra="depends: done-root\n")
        task(root, "_archive/old", "old", "Archived", "change", "done",
             OLD)
        (root / ".ai/.current").write_text("task: leaf-task\n",
                                           encoding="utf-8")
        (root / ".ai/agent/framework.json").write_text(
            '{"project": "fixture-proj", "framework_version": "10.2"}\n',
            encoding="utf-8")

        out = run(root, "tree")
        lines = out.splitlines()

        # The tree hangs under the project name from framework.json.
        check(lines[0] == "fixture-proj", f"project root line: {lines[0]!r}")
        # First-level tasks carry `├── ` / `└── `, nested levels
        # accumulate `│   ` / `    `; the project line has no branch.
        check("├── 🔄 root-task" in out, "first-level blocker line")
        check("│   ├── ⛔ mid-task   blocked: waits for root" in out,
              "mid nested under root with blocked annotation")
        check("│   │   ├── 👉 📋 leaf-task" in out,
              "leaf nested three levels, pointer before the name")
        check("│       │   └── 👉" not in out, "pointer stays on its task")
        # Exactly one line per task id (appear-once, both diamonds).
        for tid in ("root-task", "mid-task", "leaf-task", "root-a",
                    "root-b", "diamond", "deep-a", "cyc-a", "cyc-b",
                    "cyc-tail", "self-dep", "ghost", "done-root", "waits-done",
                    "solo-1", "solo-2"):
            n = sum(1 for ln in lines
                    if f" {tid}" in ln and not ln.startswith("- ❗"))
            check(n == 1, f"{tid} appears once ({n})")
        # deep-a names a root and a task inside that root's subtree; it
        # nests once, under the root, never as a first-level line.
        deep = next(ln for ln in lines if " deep-a" in ln)
        check(deep.startswith("│   │   └──"), f"deep-a nested: {deep!r}")
        # Diamond under the first-sorting root only.
        dia = next(ln for ln in lines if " diamond" in ln)
        check(dia.startswith("├── ") or dia.startswith("└── ")
              or dia.startswith(("│   ", "    ")),
              f"diamond is not a project-level line: {dia!r}")
        # Done task still shows as a first-level blocker.
        check(any(ln.startswith(("├── ✅ done-root", "└── ✅ done-root"))
                  for ln in lines), "done task as first-level blocker")
        check("waits-done" in out, "dependent of done task shown")
        # Independents stand on the first level as leaves, after the
        # tasks that block others, in sort order; archived excluded.
        tops = [ln for ln in lines if ln.startswith(("├── ", "└── "))]
        check(tops[-2:] == ["├── 📋 solo-2", "└── 📋 solo-1"],
              f"independents last on the first level: {tops[-2:]!r}")
        check("independent" not in out, "no trailing independent line")
        check("old" not in out.replace("no-such-task", ""),
              "archived task not in tree")
        check("1 archived (not listed)." in out, "tree footer counts archive")
        # Warnings: unknown dep and the cycle, once each.
        check("- ❗ ghost: depends on no-such-task, which is not a live "
              "task (unknown or archived)." in out, "unknown dep flagged")
        cyc = [ln for ln in lines if "dependency cycle" in ln]
        check(len(cyc) == 2
              and "cyc-b -> cyc-a -> cyc-b; shown from cyc-b." in cyc[0]
              and "self-dep -> self-dep; shown from self-dep." in cyc[1],
              f"each cycle flagged once, in edge order: {cyc!r}")
        tail = next(ln for ln in lines if " cyc-tail" in ln)
        check(tail.startswith(("│   ", "    ")),
              f"task downstream of a cycle nests under it: {tail!r}")
        # Legend and summary reused from the table.
        check(any(ln.startswith("Legend:") for ln in lines),
              "legend under tree")
        check("🔄 1 in-progress, ⛔ 1 blocked, 📋 13 planned, ✅ 1 done; "
              "1 archived (not listed)." in out, "tree footer summary")
        check("👉 marks the resume pointer in `.ai/.current` (leaf-task)"
              in out, "tree pointer footer")
        check("\x1b[" not in out, "ANSI codes in piped tree output")
        # The table is unchanged by the tree additions.
        check("depends" not in run(root), "list output mentions no deps")
        # Without framework.json the directory name tops the tree.
        (root / ".ai/agent/framework.json").unlink()
        check(run(root, "tree").splitlines()[0] == Path(tmp).name
              or run(root, "tree").splitlines()[0] == ".",
              "tree falls back to the directory name")

    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: task table, {CHECKED[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
