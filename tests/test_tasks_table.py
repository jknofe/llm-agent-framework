#!/usr/bin/env python3
"""Regression test for the task table behind /task-list-all (tasks.py).

The script is the whole answer of /task-list-all (CONCEPT.md, Pillar 2), so
everything it promises is checked here without an agent: live tasks only,
archive counted, sort order, emoji columns and legend, the three flags, the
resume pointer, a typo kept visible, no ANSI codes through a pipe, and the
two empty states. Builds fixture task files in a temp dir; stdlib only.

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


def run(root, env_extra=None):
    env = dict(os.environ)
    env.pop("NO_COLOR", None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(root / ".ai/agent/tools/tasks.py")],
        capture_output=True, text=True, env=env, check=True).stdout


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

        # Empty state 2: tasks directory with only archived tasks.
        for d in (root / ".ai/tasks").iterdir():
            if d.name != "_archive":
                (d / "task.md").unlink()
                d.rmdir()
        out = run(root)
        check("No live tasks in `.ai/tasks/` (1 archived)" in out,
              "only-archived message")

    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: task table, {CHECKED[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
