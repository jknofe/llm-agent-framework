#!/usr/bin/env python3
"""Task table for /task-list-all.

Reads the frontmatter of every `.ai/tasks/<id>/task.md` (archived ones under
`.ai/tasks/_archive/` included) and prints one markdown table: id, type,
status, title, how many steps and done-when criteria are checked, and when the
task was last touched. The task the resume pointer `.ai/.current` names is
marked. Parsing is deterministic so the table never depends on how carefully
an agent read thirty files.

Read-only; stdlib only.

Usage: python3 .ai/agent/tools/tasks.py   (from anywhere)
"""
import re
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[2]  # the .ai/ directory
TASKS = AI / "tasks"

# Open work first, finished work last, archive after everything live.
STATUS_ORDER = {"in-progress": 0, "blocked": 1, "planned": 2, "done": 3}


def frontmatter(text):
    """The `key: value` pairs of a leading `---` block, as a dict."""
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep:
            out[key.strip()] = value.strip()
    return out


def checked(text, heading):
    """(checked, total) checkboxes under a `## <heading>` section."""
    m = re.search(rf"^## {re.escape(heading)}\b.*?$(.*?)(?=^## |\Z)", text,
                  re.M | re.S)
    if not m:
        return 0, 0
    boxes = re.findall(r"^\s*[-*] \[([ xX~-])\]", m.group(1), re.M)
    return sum(b != " " for b in boxes), len(boxes)


def current_id():
    """The task id `.ai/.current` points at, or None."""
    cur = AI / ".current"
    if not cur.is_file():
        return None
    text = cur.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*(?:task|id)\s*:\s*(\S+)", text, re.M)
    return m.group(1) if m else None


def load(path, archived):
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = frontmatter(text)
    steps = checked(text, "Steps")
    done_when = checked(text, "Done when")
    return {
        "id": fm.get("id") or path.parent.name,
        "type": fm.get("type") or "?",
        "status": fm.get("status") or "?",
        "title": fm.get("title") or "",
        "steps": steps,
        "done_when": done_when,
        "updated": fm.get("updated") or fm.get("created") or "",
        "archived": archived,
    }


def cell(value):
    return str(value).replace("|", "\\|")


def ratio(pair):
    return f"{pair[0]}/{pair[1]}" if pair[1] else "-"


def main():
    if any((AI / "changes").glob("**/spec.md")):
        print("Found specs under `.ai/changes/` from framework 7.x; "
              "/framework-update moves them to `.ai/tasks/`.\n")
    if not TASKS.is_dir():
        print("No tasks yet: `.ai/tasks/` does not exist. "
              "Create one with /task-create <id> <title>.")
        return 0

    rows = []
    for path in sorted(TASKS.glob("*/task.md")):
        if path.parent.name != "_archive":
            rows.append(load(path, archived=False))
    for path in sorted(TASKS.glob("_archive/*/task.md")):
        rows.append(load(path, archived=True))

    if not rows:
        print("No tasks in `.ai/tasks/`. Create one with "
              "/task-create <id> <title>.")
        return 0

    rows.sort(key=lambda r: (r["archived"],
                             STATUS_ORDER.get(r["status"], 9),
                             r["updated"], r["id"]))
    cur = current_id()

    print("| | ID | Type | Status | Title | Steps | Done when | Updated |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        mark = ">" if r["id"] == cur else ""
        status = r["status"] + (" (archived)" if r["archived"] else "")
        print(f"| {mark} | {cell(r['id'])} | {cell(r['type'])} | "
              f"{cell(status)} | {cell(r['title'])} | {ratio(r['steps'])} | "
              f"{ratio(r['done_when'])} | {cell(r['updated'])} |")

    counts = {}
    for r in rows:
        if not r["archived"]:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = ", ".join(f"{n} {s}" for s, n in
                        sorted(counts.items(),
                               key=lambda kv: STATUS_ORDER.get(kv[0], 9)))
    archived = sum(r["archived"] for r in rows)
    print()
    print(f"{summary or 'no live tasks'}; {archived} archived.")
    if cur:
        print(f"`>` marks the resume pointer in `.ai/.current` ({cur}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
