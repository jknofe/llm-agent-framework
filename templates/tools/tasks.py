#!/usr/bin/env python3
"""Task table and id resolver for /task.

`tasks.py` or `tasks.py list`, the `/task list` answer: reads the
frontmatter of every live `.ai/tasks/<id>/task.md` and prints one markdown
table: id, type, status, title, how many steps and done-when criteria are
checked, and when the task was last touched. Archived tasks under
`.ai/tasks/_archive/` are not listed, only counted: archiving is how a task
leaves the working view. The task the resume pointer `.ai/.current` names is
marked. Below the table it flags what needs a look: an `in-progress` task not
updated for STALE_DAYS, a `blocked` task with the reason from its `blocked:`
frontmatter line, a `done` task with unchecked done-when criteria or with no
review line in Findings. Only the task files are read: frontmatter,
checkboxes, and whether Findings names a review. The output is the whole
answer, so no agent has to open a task file to add to it. Status and
type show as emoji only, explained by a legend line under the table. The id
is colored by status, but only when a person runs the script in a terminal
(not piped, NO_COLOR unset).

`tasks.py resolve [<id>]` decides whether `/task` creates or works a task, so
no agent has to search for one: it prints one verdict line, then a sentence.
  CREATE <id>     no task with that id; SIMILAR lines name close existing ids
  DO <id>         a live task that is not done (planned, in-progress, blocked)
  DONE <id>       a live task that is done
  ARCHIVED <id>   only under `_archive/`
  INVALID         not usable as an id (a title without an id, a path)
  NONE            no id given and no resume pointer
Ids match case-insensitively; the verdict carries the id as it is on disk.
Without an id, the task `.ai/.current` points at is resolved.

`tasks.py start <id>` and `tasks.py finish <id> done|blocked [<reason>]` are
the task's bookkeeping, so no agent improvises it with shell redirects or
in-place edits the permission allowlist cannot match (CONCEPT.md section
44). start sets `status: in-progress` and `updated:`, drops a `blocked:`
line, and writes `.ai/.current` (kept as is when it already names this
task, so a resumed task keeps its modified-files list). finish blocked sets
the status and a one-line `blocked:` reason and keeps `.ai/.current`.
finish done refuses while a done-when criterion is unticked or Findings has
no review line, the two conditions `/task list` would flag; otherwise it
sets the status, drops a `blocked:` line, and deletes `.ai/.current` when it
names this task. Neither commits: the agent commits `.ai` itself.

list and resolve are read-only; start and finish write only the task's
frontmatter and `.ai/.current`. Stdlib only.

Usage: python3 .ai/agent/tools/tasks.py   (from anywhere)
"""
import datetime
import difflib
import os
import re
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[2]  # the .ai/ directory
TASKS = AI / "tasks"

# Open work first, finished work last, archive after everything live.
STATUS_ORDER = {"in-progress": 0, "blocked": 1, "planned": 2, "done": 3}

# Emoji carry status and type in every view, the agent's markdown reply
# included. None needs the U+FE0F selector, which misaligns terminal columns.
STATUS_ICON = {"in-progress": "🔄", "blocked": "⛔", "planned": "📋",
               "done": "✅"}
TYPE_ICON = {"change": "🔧", "bug": "🐞", "investigation": "🔍", "test": "🧪"}
POINTER = "👉"
FLAG = "❗"

# ANSI color, on the id by status, only when a person runs the script in a
# terminal. The agent reads it through a pipe and copies it into markdown,
# where escape codes are noise.
COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
STATUS_COLOR = {"in-progress": "33", "blocked": "31", "planned": "2",
                "done": "32"}


LEGEND = ("Legend: " + ", ".join(f"{i} {t}" for t, i in TYPE_ICON.items())
          + "; " + ", ".join(f"{i} {s}" for s, i in STATUS_ICON.items())
          + f"; {POINTER} resume pointer, {FLAG} needs a look")


def paint(text, code):
    return f"\033[{code}m{text}\033[0m" if COLOR and code else text


# An in-progress task untouched this long is flagged as stale.
STALE_DAYS = 14


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
            value = value.strip()
            # A quoted YAML scalar ("..." or '...') is as valid as a bare one.
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            out[key.strip()] = value
    return out


def section(text, heading):
    """The body of a `## <heading>` section, or ""."""
    m = re.search(rf"^## {re.escape(heading)}\b.*?$(.*?)(?=^## |\Z)", text,
                  re.M | re.S)
    return m.group(1) if m else ""


def checked(text, heading):
    """(checked, total) checkboxes under a `## <heading>` section."""
    boxes = re.findall(r"^\s*[-*] \[([ xX~-])\]", section(text, heading),
                       re.M)
    return sum(b != " " for b in boxes), len(boxes)


def current_id():
    """The task id `.ai/.current` points at, or None."""
    cur = AI / ".current"
    if not cur.is_file():
        return None
    text = cur.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*(?:task|id)\s*:\s*(\S+)", text, re.M)
    return m.group(1) if m else None


def load(path):
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
        "blocked": fm.get("blocked") or "",
        # /task do ends its review gate with a Findings line naming the
        # review; a done task without one skipped the gate.
        "reviewed": bool(re.search(r"^\s*[-*].*\breview",
                                   section(text, "Findings"), re.M | re.I)),
    }


def age_days(value):
    """Days since an ISO date, or None if it does not parse."""
    try:
        day = datetime.date.fromisoformat(value[:10])
    except ValueError:
        return None
    return (datetime.date.today() - day).days


def flags(rows):
    """One line per task that needs a look, in table order."""
    out = []
    for r in rows:
        if r["status"] == "in-progress":
            age = age_days(r["updated"])
            if age is not None and age > STALE_DAYS:
                out.append(f"- {FLAG} {r['id']}: in-progress, not updated for "
                           f"{age} days.")
        elif r["status"] == "blocked":
            out.append(f"- {FLAG} {r['id']}: blocked: "
                       f"{r['blocked'] or 'no reason recorded'}.")
        elif r["status"] == "done":
            if r["done_when"][0] < r["done_when"][1]:
                got, total = r["done_when"]
                out.append(f"- {FLAG} {r['id']}: done with {total - got} of "
                           f"{total} done-when criteria unchecked.")
            if not r["reviewed"]:
                out.append(f"- {FLAG} {r['id']}: done without a review line "
                           "in Findings.")
    return out


def cell(value):
    return str(value).replace("|", "\\|")


def ratio(pair):
    return f"{pair[0]}/{pair[1]}" if pair[1] else "-"


ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def task_dirs(archived=False):
    """{id: task.md path} of live (or archived) tasks."""
    base = TASKS / "_archive" if archived else TASKS
    return {p.parent.name: p for p in base.glob("*/task.md")
            if p.parent.name != "_archive"}


def similar(tid, ids):
    """Existing ids close enough to `tid` to be a possible duplicate."""
    low = {i.lower(): i for i in ids}
    close = difflib.get_close_matches(tid.lower(), list(low), n=3,
                                      cutoff=0.6)
    words = {w for w in re.split(r"[-_.]", tid.lower()) if len(w) >= 3}
    for key, orig in low.items():
        shared = words & {w for w in re.split(r"[-_.]", key) if len(w) >= 3}
        if key not in close and (len(shared) >= 2 or tid.lower() in key
                                 or key in tid.lower()):
            close.append(key)
    return [low[k] for k in close]


def resolve(arg):
    """Print the verdict for `/task <id>`; see the module docstring."""
    if not arg:
        cur = current_id()
        if not cur:
            print("NONE")
            print("No id given and no resume pointer in `.ai/.current`.")
            return 0
        arg = cur
        print(f"# no id given; resuming `.ai/.current` ({cur})")
    if not ID_RE.fullmatch(arg):
        print(f"INVALID {arg}")
        print("Not usable as a task id: use a short kebab-case id "
              "(letters, digits, - _ .), e.g. fix-login-timeout.")
        return 0
    live, archived = task_dirs(), task_dirs(archived=True)
    for ids, where in ((live, "live"), (archived, "archive")):
        match = next((i for i in ids if i.lower() == arg.lower()), None)
        if not match:
            continue
        r = load(ids[match])
        if where == "archive":
            print(f"ARCHIVED {match}")
            print(f"Archived task `.ai/tasks/_archive/{match}/task.md` "
                  f"({r['type']}, {r['status']}). Do not create it again.")
        elif r["status"] == "done":
            print(f"DONE {match}")
            print(f"Task `.ai/tasks/{match}/task.md` ({r['type']}) is done: "
                  f"{r['title']}")
        else:
            print(f"DO {match} status={r['status']} type={r['type']}")
            print(f"Task `.ai/tasks/{match}/task.md` exists: {r['title']}")
        return 0
    print(f"CREATE {arg}")
    near = similar(arg, list(live) + list(archived))
    for i in near:
        src = live.get(i) or archived.get(i)
        r = load(src)
        state = "archived" if i in archived and i not in live else r["status"]
        print(f"SIMILAR {i} ({state}): {r['title']}")
    print(f"No task `{arg}` yet." + (" Close ids exist; ask whether one of "
                                     "them is meant." if near else ""))
    return 0


def set_fields(path, updates, drop=()):
    """Rewrite frontmatter keys in place: replace each key in `updates`
    (adding a missing one after `status:`), remove each key in `drop`.
    Everything outside the leading `---` block is left byte for byte."""
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    if not text.startswith("---\n") or end == -1:
        raise ValueError(f"{path} has no frontmatter block")
    lines, seen = [], set()
    for line in text[4:end].splitlines():
        key = line.partition(":")[0].strip()
        if key in drop:
            continue
        if key in updates:
            line = f"{key}: {updates[key]}"
            seen.add(key)
        lines.append(line)
    for key, value in updates.items():
        if key not in seen:
            at = next((i + 1 for i, ln in enumerate(lines)
                       if ln.startswith("status:")), len(lines))
            lines.insert(at, f"{key}: {value}")
    path.write_text("---\n" + "\n".join(lines) + text[end:],
                    encoding="utf-8")


def live_task(arg):
    """(id as on disk, task.md path) of a live task, or None."""
    live = task_dirs()
    match = next((i for i in live if i.lower() == arg.lower()), None)
    return (match, live[match]) if match else None


USAGE = ("Usage: tasks.py [list] | tasks.py resolve [<id>] | "
         "tasks.py start <id> | tasks.py finish <id> done|blocked [<reason>]")
COMMIT = "Commit `.ai` now: git -C .ai add -A && git -C .ai commit -m"


def start(arg):
    """Mark a task in progress and point `.ai/.current` at it."""
    found = live_task(arg) if arg else None
    if not found:
        print(f"No live task {arg!r}. Run `tasks.py resolve {arg}` first.")
        return 1
    tid, path = found
    if load(path)["status"] == "done":
        print(f"Task {tid} is done; there is nothing to start.")
        return 1
    today = datetime.date.today().isoformat()
    set_fields(path, {"status": "in-progress", "updated": today},
               drop=("blocked",))
    cur, note = AI / ".current", "kept (it already names this task)"
    if current_id() != tid:
        replaced = current_id()
        cur.write_text(f"task: {tid}\npath: .ai/tasks/{tid}/task.md\n"
                       f"started: {today}\nmodified:\n", encoding="utf-8")
        note = (f"written (replaced the pointer to {replaced})" if replaced
                else "written")
    print(f"STARTED {tid}: status in-progress, updated {today}; "
          f"`.ai/.current` {note}.")
    print("Keep its `modified:` list current as you change files.")
    return 0


def finish(arg, state, reason):
    """Close a task as done (only when the gate is met) or blocked."""
    found = live_task(arg) if arg else None
    if not found or state not in ("done", "blocked"):
        print(f"No live task {arg!r}." if not found else USAGE)
        return 1 if not found else 2
    tid, path = found
    today = datetime.date.today().isoformat()
    if state == "blocked":
        reason = " ".join(reason.split())
        if not reason:
            print("A blocked task needs a reason: "
                  f"tasks.py finish {tid} blocked <reason in one line>")
            return 1
        set_fields(path, {"status": "blocked", "blocked": reason,
                          "updated": today})
        print(f"BLOCKED {tid}: {reason}. `.ai/.current` kept for the "
              "resume; `tasks.py start` clears the block.")
        print(f'{COMMIT} "task: blocked {tid}"')
        return 0
    r = load(path)
    missing = []
    got, total = r["done_when"]
    if got < total:
        missing.append(f"{total - got} of {total} done-when criteria "
                       "unticked")
    if not r["reviewed"]:
        missing.append("no `Review:` line in Findings")
    if missing:
        print(f"NOT DONE {tid}: " + "; ".join(missing) + ". Meet them, get "
              "the user's agreement to drop a criterion, or finish it as "
              "blocked.")
        return 1
    set_fields(path, {"status": "done", "updated": today}, drop=("blocked",))
    cleared = current_id() == tid
    if cleared:
        (AI / ".current").unlink()
    print(f"DONE {tid}: status done, updated {today}"
          + ("; `.ai/.current` deleted." if cleared else "."))
    print(f'{COMMIT} "task: done {tid}"')
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == "resolve":
        return resolve(args[1] if len(args) > 1 else "")
    if args and args[0] == "start":
        return start(args[1] if len(args) > 1 else "")
    if args and args[0] == "finish":
        if len(args) < 3:
            print(USAGE)
            return 2
        return finish(args[1], args[2], " ".join(args[3:]))
    if args and args[0] != "list":
        print(f"Unknown argument {args[0]!r}. {USAGE}")
        return 2
    if not TASKS.is_dir():
        print("No tasks yet: `.ai/tasks/` does not exist. "
              "Create one with /task create <id> <title>.")
        return 0

    rows = [load(path) for path in sorted(TASKS.glob("*/task.md"))
            if path.parent.name != "_archive"]
    archived = len(list(TASKS.glob("_archive/*/task.md")))

    if not rows:
        print(f"No live tasks in `.ai/tasks/` ({archived} archived). "
              "Create one with /task create <id> <title>.")
        return 0

    rows.sort(key=lambda r: (STATUS_ORDER.get(r["status"], 9),
                             r["updated"], r["id"]))
    cur = current_id()

    print("| | ID | Type | Status | Title | Steps | Done when | Updated |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        mark = POINTER if r["id"] == cur else ""
        # Known values show as their emoji only (see LEGEND); an unknown one
        # stays text so a typo in a task file is visible, not hidden.
        kind = TYPE_ICON.get(r["type"]) or cell(r["type"])
        state = STATUS_ICON.get(r["status"]) or cell(r["status"])
        ident = paint(cell(r["id"]), STATUS_COLOR.get(r["status"]))
        print(f"| {mark} | {ident} | {kind} | {state} | "
              f"{cell(r['title'])} | {ratio(r['steps'])} | "
              f"{ratio(r['done_when'])} | {cell(r['updated'])} |")

    print()
    print(LEGEND)

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = ", ".join(f"{STATUS_ICON.get(s, '')} {n} {s}".strip()
                        for s, n in
                        sorted(counts.items(),
                               key=lambda kv: STATUS_ORDER.get(kv[0], 9)))
    notes = flags(rows)
    if notes:
        print()
        print("\n".join(notes))
    print()
    print(f"{summary}; {archived} archived (not listed).")
    if cur:
        print(f"{POINTER} marks the resume pointer in `.ai/.current` ({cur}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
