#!/usr/bin/env python3
"""Regression test for tasks.py, the script behind /task.

`tasks.py list` is the whole answer of `/task list` and `tasks.py resolve`
decides whether `/task <id>` creates or works a task (CONCEPT.md, Pillar 2),
so everything both promise is checked here without an agent. Table: live
tasks only, archive counted, sort order, emoji columns and legend, the flags,
the resume pointer, a typo kept visible, no ANSI codes through a pipe, the two
empty states. Resolver: every verdict, case-insensitive ids, near-duplicate
ids, the resume pointer, the issue-key prefix rule (10.6). Tracker
discovery: no config, config rows, a detected `gh`. Bookkeeping: start and
finish set status, the
blocked reason and the resume pointer, and finish done refuses an unmet
gate. Builds fixture task files in a temp dir; stdlib
only.

Usage: python3 tests/test_tasks_table.py
"""
import datetime
import json
import os
import shutil
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
        # A worker's `review` report and a supervisor naming the reviewer
        # are not the gate's `Review:` line.
        task(root, "wround", "wround", "Worker said review", "change", "done",
             NEW, done_when="- [x] c",
             findings=(f"- {NEW} Worker round 1: review: ready.\n"
                       f"- {NEW} Supervisor check: round 1 accepted: "
                       "reviewer passed.\n"))
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
                        "quoted", "typo", "unrev", "full", "half", "wround"],
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
        check("❗ wround: done without a review line in Findings." in out,
              "worker review report taken for the review line")
        for quiet in ("fresh", "full", "plan"):
            check(f"❗ {quiet}:" not in out, f"{quiet} flagged")

        # Footer summary in status order.
        check("🔄 2 in-progress, ⛔ 2 blocked, 📋 3 planned, ✅ 4 done; "
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
        # Issue-key prefixes (10.6): bare key rejected, key plus slug
        # accepted with the tracker-answered note.
        bare = run(root, "resolve", "12345-")
        check(bare.startswith("INVALID 12345-")
              and "12345-fix-ci-crash" in bare,
              f"resolve rejects a bare issue number: {bare!r}")
        check(verdict(root, "PROJ-123-").startswith("INVALID"),
              "resolve rejects a bare Jira key")
        out = run(root, "resolve", "12345-fix-ci-crash")
        check(out.startswith("CREATE 12345-fix-ci-crash"),
              f"resolve accepts key plus slug: {out!r}")
        check("tracker issue" in out, "CREATE names the answered question")
        out = run(root, "resolve", "PROJ-123-fix-ci-crash")
        check(out.startswith("CREATE PROJ-123-fix-ci-crash"),
              f"resolve accepts Jira key plus slug: {out!r}")
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
        # `.ai/.current` names `fresh`, which is in progress: keep runs in
        # parallel with its own pointer instead of replacing it (11.1).
        mine = root / ".ai/.current-keep"
        check(mine.read_text(encoding="utf-8").startswith("task: keep\n")
              and "parallel" in out and "PARALLEL fresh is running" in out,
              f"start beside a running task gets its own pointer: {out!r}")
        check((root / ".ai/.current").read_text(encoding="utf-8")
              .startswith("task: fresh"), "the running task's pointer stays")
        mine.write_text(mine.read_text(encoding="utf-8") + "  - a.py\n",
                        encoding="utf-8")
        run(root, "start", "keep")
        check("a.py" in mine.read_text(encoding="utf-8"),
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
              and not mine.exists()
              and (root / ".ai/.current").exists(),
              "finish done deletes only its own pointer")
        check("git -C .ai add tasks/keep &&" in out and "add -A" not in out,
              f"finish prints a path-scoped commit: {out!r}")
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

        # Tracker discovery (10.6): no config, nothing detectable
        # without a config file or a CLI on PATH.
        out = run(root, "trackers", env_extra={"PATH": "/nonexistent"})
        check("No tracker configured and none detected." in out
              and ".ai/trackers.conf" in out, f"trackers empty: {out!r}")
        # A config row survives a PATH with no CLIs.
        (root / ".ai/trackers.conf").write_text(
            "# team trackers\n"
            "name: bosch-jira\nkind: jira\n"
            "command: tr issue view <KEY>\n"
            "\n"
            "name: team-gh\nkind: github\n"
            "command: gh issue view <number> --repo org/repo\n",
            encoding="utf-8")
        out = run(root, "trackers", env_extra={"PATH": "/nonexistent"})
        check("| Name | Kind | Fetch with | From |" in out
              and "| bosch-jira | jira | tr issue view <KEY> | "
                  ".ai/trackers.conf |" in out
              and "| team-gh | github | gh issue view <number> --repo "
                  "org/repo | .ai/trackers.conf |" in out,
              f"trackers config rows: {out!r}")
        # A `gh` on PATH is detected, with the repo it resolves to.
        fakebin = root / "fakebin"
        fakebin.mkdir()
        (fakebin / "gh").write_text(
            '#!/bin/sh\nif [ "$1" = "repo" ]; then echo org/repo; fi\n',
            encoding="utf-8")
        (fakebin / "gh").chmod(0o755)
        out = run(root, "trackers", env_extra={"PATH": str(fakebin)})
        check("gh issue view <number>" in out and "org/repo" in out
              and "detected: gh on PATH" in out,
              f"trackers detects gh: {out!r}")

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
        # Archived as done: a cleared blocker, no warning. Archived while
        # still planned: flagged.
        task(root, "waits-old", "waits-old", "Waits on archived",
             "change", "planned", NEW, extra="depends: OLD\n")
        task(root, "_archive/shelved", "shelved", "Shelved", "change",
             "planned", OLD)
        task(root, "waits-shelved", "waits-shelved", "Waits on shelved",
             "change", "planned", NEW, extra="depends: shelved\n")
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
        check("│   │   └── 👉 📋 leaf-task" in out,
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
        # nests once, at its shallowest position: directly under the root,
        # after mid-task, which therefore keeps `├── `.
        deep = next(ln for ln in lines if " deep-a" in ln)
        check(deep == "│   └── 📋 deep-a", f"deep-a nested: {deep!r}")
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
        check(not any(ln.endswith((" old", " shelved")) for ln in lines),
              "archived tasks not in tree")
        check("2 archived (not listed)." in out, "tree footer counts archive")
        # Warnings: unknown dep and the cycle, once each.
        check("- ❗ ghost: depends on no-such-task, which names no task."
              in out, "unknown dep flagged")
        check("- ❗ waits-shelved: depends on shelved, archived as planned, "
              "not done." in out, "dep archived while not done flagged")
        check("waits-old: depends" not in out,
              "dep archived as done not flagged")
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
        check("🔄 1 in-progress, ⛔ 1 blocked, 📋 15 planned, ✅ 1 done; "
              "2 archived (not listed)." in out, "tree footer summary")
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

    # Tree placement (10.5): shallowest position across first-level
    # tasks, branch characters from complete child lists, a cycle below a
    # first-level task, and case-insensitive `depends:` ids.
    def tree_of(spec):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool = root / ".ai/agent/tools/tasks.py"
            tool.parent.mkdir(parents=True)
            tool.write_text(content.render_tool_tasks(), encoding="utf-8")
            for tid, dep in spec.items():
                task(root, tid, tid, tid, "change", "planned", NEW,
                     extra=f"depends: {dep}\n" if dep else "")
            out = run(root, "tree")
            return out.split("\nLegend")[0].splitlines()[1:], out

    body, _ = tree_of({"t": "", "a": "t", "b": "t, a"})
    check(body == ["└── 📋 t", "    ├── 📋 a", "    └── 📋 b"],
          f"shallowest within one tree, last sibling closes: {body!r}")
    body, _ = tree_of({"t1": "", "t2": "", "a": "t1", "x": "a, t2"})
    check(body == ["├── 📋 t1", "│   └── 📋 a", "└── 📋 t2",
                   "    └── 📋 x"],
          f"shallowest across first-level tasks: {body!r}")
    body, out = tree_of({"t": "", "a": "t, b", "b": "a"})
    check(body == ["└── 📋 t", "    └── 📋 a", "        └── 📋 b"],
          f"cycle below a first-level task nests: {body!r}")
    check("- ❗ dependency cycle: a -> b -> a." in out,
          "cycle below a first-level task flagged")
    body, out = tree_of({"BUG-7": "", "other": "bug-7"})
    check(body == ["└── 📋 BUG-7", "    └── 📋 other"],
          f"depends ids match without case: {body!r}")
    check("not a live task" not in out, "case-only dep not flagged")

    # tick (11.0): named boxes only, refuses unknown numbers, no "all".
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tool = root / ".ai/agent/tools/tasks.py"
        tool.parent.mkdir(parents=True)
        tool.write_text(content.render_tool_tasks(), encoding="utf-8")
        task(root, "tk", "tk", "Tick", "change", "in-progress", OLD,
             done_when="- [ ] first\n      continued\n- [ ] second\n- [ ] third",
             steps="- [x] ~~H1~~ ruled out: x\n- [ ] s2\n- [ ] s3")
        path = root / ".ai/tasks/tk/task.md"
        before = path.read_text(encoding="utf-8")
        out = run(root, "tick", "tk", "done", "1", "3")
        after = path.read_text(encoding="utf-8")
        check("TICKED Done when 1: first" in out and
              "TICKED Done when 3: third" in out, f"tick prints items: {out!r}")
        check("- [x] first\n      continued\n- [ ] second\n- [x] third"
              in after, "tick ticks only the named boxes")
        check("Done when 2/3 ticked" in out, "tick prints progress")
        check(after.replace(f"updated: {TODAY}", f"updated: {OLD}")
              .replace("[x] first", "[ ] first")
              .replace("[x] third", "[ ] third") == before,
              "tick changes nothing else but updated:")
        out = run(root, "tick", "tk", "steps", "1", "2")
        check("already ticked Steps 1" in out and "TICKED Steps 2: s2" in out,
              f"tick reports an already-ticked step: {out!r}")
        r = attempt(root, "tick", "tk", "done", "4")
        check(r.returncode == 1 and "no item 4" in r.stdout,
              f"tick refuses a missing item: {r.stdout!r}")
        check(path.read_text(encoding="utf-8").count("- [ ] second") == 1,
              "a refused tick changes nothing")
        for bad in (["tk", "done", "all"], ["tk", "outcome", "1"],
                    ["tk", "done"]):
            check(attempt(root, "tick", *bad).returncode == 2,
                  f"tick usage error for {bad}")
        check(attempt(root, "tick", "nope", "done", "1").returncode == 1,
              "tick on an unknown task")

    # Parallel tasks (11.1): own pointers, claims, resume and list marks.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tool = root / ".ai/agent/tools/tasks.py"
        tool.parent.mkdir(parents=True)
        tool.write_text(content.render_tool_tasks(), encoding="utf-8")
        for tid in ("pa", "pb", "pc"):
            task(root, tid, tid, tid.upper(), "change", "planned", OLD)
        out = run(root, "start", "pa")
        check("`.ai/.current` written" in out and "PARALLEL" not in out,
              f"first task takes .ai/.current: {out!r}")
        out = run(root, "start", "pb")
        check((root / ".ai/.current-pb").is_file() and
              "PARALLEL pa is running" in out and "claims: none yet" in out,
              f"second task runs in parallel: {out!r}")
        check(run(root, "claim", "pa", "src/a.py", "README.md")
              .startswith("CLAIMED for pa"), "claim adds files")
        r = attempt(root, "claim", "pb", "./README.md")
        check(r.returncode == 1 and "CLAIMED README.md by running task pa"
              in r.stdout.replace("./", ""), f"claim refuses: {r.stdout!r}")
        check("README.md" not in (root / ".ai/.current-pb")
              .read_text(encoding="utf-8"), "a refused claim writes nothing")
        check(run(root, "claim", "pb", "src/b.py").startswith(
              "CLAIMED for pb"), "a free file is claimed")
        check("(already claimed)" in run(root, "claim", "pa", "README.md"),
              "re-claiming your own file is fine")
        check(attempt(root, "claim", "pc", "x").returncode == 1,
              "claim needs a started task")
        out = run(root, "start", "pc")
        check("claims: src/a.py, README.md" in out and
              "PARALLEL pb is running" in out, f"start lists claims: {out!r}")
        out = run(root)
        marked = [r for r in ("pa", "pb", "pc") if (row(out, r) or [""])[0]]
        check(marked == ["pa", "pb", "pc"] and "marks running tasks" in out,
              f"list marks every running task: {out!r}")
        check(verdict(root).startswith("DO pa"),
              "do without an id resumes .ai/.current")
        # finish pa: its pointer goes; pb and pc keep theirs.
        tf = root / ".ai/tasks/pa/task.md"
        tf.write_text(tf.read_text(encoding="utf-8")
                      .replace("- [ ] c", "- [x] c")
                      .replace("## Findings\n",
                               "## Findings\n- x Review: inline: ok\n"),
                      encoding="utf-8")
        run(root, "finish", "pa", "done")
        check(not (root / ".ai/.current").exists() and
              (root / ".ai/.current-pb").exists(), "finish frees only pa")
        check(run(root, "claim", "pb", "README.md").startswith(
              "CLAIMED for pb"), "a finished task's files are free again")
        check(verdict(root).startswith("NONE"),
              "two parallel pointers and no .current: do without id asks")
        run(root, "finish", "pc", "blocked", "x")
        check((root / ".ai/.current-pc").exists(), "blocked keeps pointer")
        # A pointer to a task that is not running is replaced, as before.
        task(root, "qb", "qb", "QB", "change", "blocked", OLD)
        task(root, "qa", "qa", "QA", "change", "planned", OLD)
        (root / ".ai/.current").write_text("task: qb\n", encoding="utf-8")
        out = run(root, "start", "qa")
        check("replaced the pointer to qb" in out and
              (root / ".ai/.current").read_text(encoding="utf-8")
              .startswith("task: qa"), f"non-running pointer replaced: {out!r}")

        # Sub-agent models (CONCEPT.md section 59): each of worker and
        # reviewer needs a concrete `model:` line; nothing else counts.
        def agent(rel, model_line):
            f = mroot / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"---\nname: x\ndescription: d\n{model_line}---\nb\n",
                         encoding="utf-8")
        mroot = root / "mproj"
        mtool = mroot / ".ai/agent/tools/tasks.py"
        mtool.parent.mkdir(parents=True)
        mtool.write_text(content.render_tool_tasks(), encoding="utf-8")
        r = attempt(mroot, "models")
        check(r.returncode == 1 and r.stdout.startswith("MODELS MISSING") and
              "worker: no agent file" in r.stdout, "models: no agent files")
        for role in ("worker", "reviewer"):
            agent(f".claude/agents/{role}.md", "")
        r = attempt(mroot, "models")
        check(r.returncode == 1 and r.stdout.count("has no model") == 2 and
              ".claude/agents/worker.md" in r.stdout, "models: no lines")
        agent(".claude/agents/worker.md", "model: inherit\n")
        agent(".claude/agents/reviewer.md", "model:\n")
        r = attempt(mroot, "models")
        check(r.returncode == 1 and r.stdout.count("has no model") == 2,
              "models: inherit and empty count as unset")
        agent(".claude/agents/worker.md", "model: gpt-6.1-sol\n")
        r = attempt(mroot, "models")
        check(r.returncode == 1 and "reviewer:" in r.stdout and
              "worker: .claude" not in r.stdout.split("MODELS MISSING")[1],
              "models: one role set, the other still refused")
        agent(".claude/agents/reviewer.md", 'model: "claude-agent/sonnet#medium"\n')
        r = attempt(mroot, "models")
        check(r.returncode == 0 and r.stdout.startswith("MODELS OK") and
              "gpt-6.1-sol" in r.stdout and
              "claude-agent/sonnet#medium" in r.stdout,
              f"models: both set, any name accepted: {r.stdout!r}")
        for role in ("worker", "reviewer"):
            agent(f".github/agents/{role}.agent.md", "")
        r = attempt(mroot, "models")
        check(r.returncode == 1 and ".github/agents/worker.agent.md" in r.stdout,
              "models: a second harness's files are checked too")

        # The setup command (/framework-models, CONCEPT.md section 62):
        # written for the stamp's harness, names from the arguments, else
        # the current lines, else placeholders.
        shutil.rmtree(mroot / ".github")
        home = Path(tempfile.mkdtemp())
        (home / "init_agent.py").write_text("", encoding="utf-8")

        def setup(*args, harness=None, env_home=None):
            stamp = mroot / ".ai/agent/framework.json"
            if harness:
                stamp.write_text(json.dumps({"harness": harness}),
                                 encoding="utf-8")
            elif stamp.exists():
                stamp.unlink()
            env = {k: v for k, v in os.environ.items()
                   if k != "LLM_AGENT_HOME"}
            if env_home:
                env["LLM_AGENT_HOME"] = str(env_home)
            return subprocess.run(
                [sys.executable, str(mtool), "models", *args],
                capture_output=True, text=True, env=env)

        r = setup(harness="claude", env_home=home)
        check(r.returncode == 0 and "In this session, type:" in r.stdout and
              f'! python3 "{home}/init_agent.py" --models --worker '
              "gpt-6.1-sol --reviewer claude-agent/sonnet#medium" in r.stdout
              and "restart the session" in r.stdout,
              f"models: claude line with the current names: {r.stdout!r}")
        r = setup("worker=w1", harness="opencode")
        check("\n!init-agent --models --worker w1 --reviewer "
              "claude-agent/sonnet#medium" in r.stdout and
              "reloads OpenCode" in r.stdout,
              f"models: opencode line, no home, one name given: {r.stdout!r}")
        r = setup("a1", "b1", harness="copilot")
        check("In a terminal in this project, run:\ninit-agent --models "
              "--worker a1 --reviewer b1" in r.stdout and
              "without a test" in r.stdout,
              f"models: copilot terminal line, bare names: {r.stdout!r}")
        r = setup("foo=bar", harness="claude")
        check(r.returncode == 2 and r.stdout.startswith("Unknown argument"),
              "models: an unknown argument is refused")
        for role in ("worker", "reviewer"):
            agent(f".claude/agents/{role}.md", "")
        r = setup(harness="claude")
        check(r.returncode == 1 and "--worker <worker> --reviewer <reviewer>"
              in r.stdout and "Replace <worker>" in r.stdout,
              f"models: placeholders when nothing is set: {r.stdout!r}")

        # `--list` (/framework-models, CONCEPT.md section 65): the models the
        # harness or its backend can name, never in the /task do gate.
        import http.server
        import threading
        seen = {}

        class Fake(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen["key"] = self.headers.get("x-api-key")
                if FAKE["status"] != 200:
                    self.send_error(FAKE["status"])
                    return
                body = json.dumps({"data": [
                    {"id": "small-1", "type": "model",
                     "display_name": "Small One", "capabilities":
                     {"type": "chat"}, "billing": {"token_prices": {
                         "default": {"input_price": 10,
                                     "output_price": 50}}}},
                    {"id": "plain-2", "type": "model"},
                    {"id": "embed-3", "type": "model",
                     "capabilities": {"type": "embeddings"}},
                    {"id": "img-4", "type": "image"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        FAKE = {"status": 200}
        srv = http.server.HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        fake_url = f"http://127.0.0.1:{srv.server_port}"

        def listed(harness, **env_extra):
            (mroot / ".ai/agent/framework.json").write_text(
                json.dumps({"harness": harness}), encoding="utf-8")
            env = {k: v for k, v in os.environ.items() if not
                   k.startswith("ANTHROPIC_")}
            env.update(env_extra)
            return subprocess.run(
                [sys.executable, str(mtool), "models", "--list"],
                capture_output=True, text=True, env=env).stdout

        out = listed("claude", ANTHROPIC_BASE_URL=fake_url,
                     ANTHROPIC_API_KEY="k-test")
        check("small-1  (Small One)  in/out 10/50" in out and
              "  plain-2" in out and "embed-3" not in out and
              "img-4" not in out and seen.get("key") == "k-test" and
              "Choose the names yourself" in out,
              f"list: backend models, chat only, key sent: {out!r}")
        FAKE["status"] = 404
        out = listed("claude", ANTHROPIC_BASE_URL=fake_url)
        check("does not list them (HTTP 404)" in out and "`/model`" in out,
              f"list: a backend without /v1/models: {out!r}")
        out = listed("claude")
        check("no API key in the environment" in out,
              f"list: nothing to ask with: {out!r}")
        out = listed("copilot")
        check("Copilot CLI has no command that lists them" in out,
              f"list: copilot points at its picker: {out!r}")
        out = listed("opencode", PATH="/nonexistent",
                     HOME=tempfile.mkdtemp())
        check("`opencode` is not on PATH" in out,
              f"list: opencode missing: {out!r}")
        r = attempt(mroot, "models")
        check("Available models" not in r.stdout,
              "list: the /task do gate never lists or calls out")
        srv.shutdown()

    # Findings lines over LONG_FINDING (300) characters are flagged
    # (CONCEPT.md section 69): a paragraph on one line is still too long.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tool = root / ".ai/agent/tools/tasks.py"
        tool.parent.mkdir(parents=True)
        tool.write_text(content.render_tool_tasks(), encoding="utf-8")
        long_line = "- 2026-11-11 S3 checks: " + "x" * 576 + "\n"
        edge = "- " + "y" * 298 + "\n"
        task(root, "wordy", "wordy", "Wordy", "change", "in-progress", NEW,
             findings=long_line + long_line[:-200] + "\n" + edge)
        task(root, "terse", "terse", "Terse", "change", "in-progress", NEW,
             findings="- 2026-11-11 checks: yamllint, xmllint OK\n" + edge)
        out = run(root)
        check("- ❗ wordy: 2 Findings line(s) over 300 characters (longest "
              "600)" in out and "evidence.md" in out,
              f"long findings flagged with count and longest: {out!r}")
        check("terse:" not in out.split("Legend")[-1],
              f"short findings and a 300-character line not flagged: {out!r}")
        # A correction stays as long as it must, and nobody rewrites the
        # Findings of a done task (CONCEPT.md section 70).
        fix = "- 2026-11-11 Supervisor round 1: " + "z" * 500 + "\n"
        task(root, "fixes", "fixes", "Fixes", "change", "in-progress", NEW,
             findings=fix)
        task(root, "over", "over", "Over", "change", "done", NEW,
             done_when="- [x] c", steps="- [x] a",
             findings=long_line + "- 2026-11-11 Review: inline: ok\n")
        out = run(root)
        check("fixes:" not in out.split("Legend")[-1],
              f"a long Supervisor round line is not flagged: {out!r}")
        check("over: 1 Findings" not in out,
              f"a done task's long findings are not flagged: {out!r}")

    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: task table, {CHECKED[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
