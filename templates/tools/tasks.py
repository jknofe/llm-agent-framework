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

`tasks.py tree`, the `/task tree` answer: the same live tasks as an ASCII
dependency tree, built from the optional `depends:` frontmatter line
(comma-separated ids of live tasks this task waits on). The tree hangs
under the project name; on the first level stand the tasks that block
others, and what waits on a task nests below it with the branch
characters bash `tree` uses. Every task appears exactly once, at its
shallowest position: a task with two dependencies sits under the one
nearest the first level, the first in sort order on a tie, not twice.
`depends:` ids match without regard to case. A done task stays on the
first level: it is the blocker that cleared. Tasks with no dependency
ties stand on the first level too, as leaves after the tasks that block
others. A
`depends:` id that names a task archived as done is a cleared blocker and
is dropped without a word. One that names an archived task not done, or
no task at all, is flagged below the tree and ignored; a task whose whole
chain is unresolvable stands on the first level. Every dependency cycle is flagged once, in
edge order from its first task in sort order. A cycle that waits on no
task outside itself is shown on the first level from that task, tasks
waiting on it nested below; one that waits on other tasks nests where
its tasks fall. The output stays deterministic. Archived
tasks are not shown, only counted in the footer.
Below the tree stand the same legend, summary and resume-pointer line the
table prints. Tree is read-only.

`tasks.py resolve [<id>]` decides whether `/task` creates or works a task, so
no agent has to search for one: it prints one verdict line, then a sentence.
  CREATE <id>     no task with that id; SIMILAR lines name close existing ids
  DO <id>         a live task that is not done (planned, in-progress, blocked)
  DONE <id>       a live task that is done
  ARCHIVED <id>   only under `_archive/`
  INVALID         not usable as an id (a title without an id, a path)
  NONE            no id given and no resume pointer
Ids match case-insensitively; the verdict carries the id as it is on disk.
Without an id, the task `.ai/.current` points at is resolved. An id whose
issue-key prefix (PROJECT-123 or 12345, from Create's tracker question) is
not followed by a slug is INVALID.

`tasks.py trackers`, the tracker discovery behind Create's issue question:
prints one markdown table of tracker access visible from this checkout:
rows from `.ai/trackers.conf` (`key: value` lines: `name`, `kind` github or
jira, `command` run in the project root), an auto-detected `gh` CLI with
the repo `gh repo view` resolves to, and a `jira` CLI on PATH. Read-only.
The task's issue lives in its `## Tracker` section, not in frontmatter, so
the table needs no parser for it.

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

`tasks.py tick <id> done|steps <n> [<n>...]` ticks the named checkboxes of
Done when (`done`) or Steps (`steps`), counted from 1 in file order, and
sets `updated:`. There is no "all": each item is named on purpose, so a box
is ticked because it was checked, not swept by a blanket replace. It prints
each item it ticked with its text, refuses a number the section does not
have, and leaves every other byte of the file alone. Striking a dead step
(`- [x] ~~H1~~ ruled out: ...`) is an edit, not a tick.

Parallel tasks share one working tree (CONCEPT.md section 51). `.ai/.current`
is the tree's resume pointer; a task started while the task it names is
still `in-progress` gets its own pointer, `.ai/.current-<id>`, instead of
replacing it, and start prints every other running task with the files it
has claimed. `tasks.py claim <id> <path> [<path>...]` adds host files to the
task's `modified:` list and refuses (CLAIMED, exit 1) a file another running
task already listed, so two tasks never edit the same file. finish done
deletes the task's own pointer, whichever it is. Every printed commit is
path-scoped (`git -C .ai add tasks/<id>`), never `add -A`: a parallel
session may be mid-edit.

`tasks.py models` checks that the two sub-agents of /task do, `worker` and
`reviewer`, each have a model chosen for this project (CONCEPT.md section
59). The choice is the `model:` line of the agent file, nowhere else, and
the script reads every harness's agent file that exists. A role counts as
set only when that line holds a concrete name: a missing agent file, a
missing or empty line and `inherit` all count as unset. The name itself is
not checked (a proxy may serve names the framework cannot know). First
line `MODELS OK` or `MODELS MISSING`; a missing role gets a line naming
the file. Then the command that sets both, written for this scaffold's
harness (`init-agent --models`, which also tests each name as a
sub-agent): `models worker=<m> reviewer=<m>` fills in those names, else
the current ones, else placeholders. /framework-models shows this output
(CONCEPT.md section 62). Exit 1 when anything is missing. Read-only.

list, tree, resolve, trackers and models are read-only; start, finish, tick
and claim write only the task file and the pointers. Stdlib only.

Usage: python3 .ai/agent/tools/tasks.py   (from anywhere)
"""
import datetime
import difflib
import json
import os
import re
import shutil
import subprocess
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


def pointer_id(path):
    """The task id a pointer file names, or None."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*(?:task|id)\s*:\s*(\S+)", text, re.M)
    return m.group(1) if m else None


def pointers():
    """{task id: pointer file} for every running task: `.ai/.current` first,
    then one `.ai/.current-<id>` per task started in parallel."""
    out = {}
    for path in [AI / ".current"] + sorted(AI.glob(".current-*")):
        tid = pointer_id(path)
        if tid and tid not in out:
            out[tid] = path
    return out


def claims(path):
    """The files a pointer's `modified:` list names."""
    text = path.read_text(encoding="utf-8", errors="replace")
    block = text.split("modified:", 1)[1] if "modified:" in text else ""
    return [ln.strip().lstrip("-").strip() for ln in block.splitlines()
            if ln.strip().lstrip("-").strip()]


def current_id():
    """The task `/task do` without an id resumes: the one `.ai/.current`
    names, else the only parallel pointer, else None."""
    cur = pointer_id(AI / ".current")
    if cur:
        return cur
    running = pointers()
    return next(iter(running)) if len(running) == 1 else None


def pointer_line():
    """The footer line naming the running tasks' pointers, or ""."""
    running = pointers()
    if len(running) == 1 and (AI / ".current") in running.values():
        return (f"{POINTER} marks the resume pointer in `.ai/.current` "
                f"({next(iter(running))}).")
    if running:
        return (f"{POINTER} marks running tasks: " + ", ".join(
            f"{tid} (`.ai/{p.name}`)" for tid, p in running.items()) + ".")
    return ""


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
        # Optional: comma-separated ids of tasks this one waits on.
        "depends": [d.strip() for d in (fm.get("depends") or "").split(",")
                    if d.strip()],
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


def summary(rows, archived):
    """The footer line both views end with: counts by status, then how
    many tasks sit in the archive."""
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    tallies = ", ".join(f"{STATUS_ICON.get(s, '')} {n} {s}".strip()
                        for s, n in sorted(counts.items(),
                        key=lambda kv: STATUS_ORDER.get(kv[0], 9)))
    return f"{tallies}; {archived} archived (not listed)."


def cell(value):
    return str(value).replace("|", "\\|")


def ratio(pair):
    return f"{pair[0]}/{pair[1]}" if pair[1] else "-"


ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
# A task that comes from a tracker issue carries its key as the id prefix
# (CONCEPT.md section 49): PROJECT-123-<slug> for Jira-style keys,
# 12345-<slug> for a bare number. The prefix alone is not an id.
ISSUE_PREFIX_RE = re.compile(r"(?:[A-Za-z][A-Za-z0-9]*-\d+|\d+)-$")
ISSUE_SLUG_RE = re.compile(r"(?:[A-Za-z][A-Za-z0-9]*-\d+|\d+)-\S")


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
    if ISSUE_PREFIX_RE.match(arg) and not ISSUE_SLUG_RE.match(arg):
        print(f"INVALID {arg}")
        print("A task id that starts with an issue key (PROJECT-123 or "
              "12345) names the slug after it too, e.g. 12345-fix-ci-crash.")
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
    # An id from an issue key says Create's tracker question is answered.
    print(f"No task `{arg}` yet." + (" Close ids exist; ask whether one of "
                                     "them is meant." if near else ""))
    if ISSUE_SLUG_RE.match(arg):
        print("The id names a tracker issue; Create records it and skips "
              "asking for one.")
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


def project():
    """The project name for the tree's top line: the `project` key of
    `.ai/agent/framework.json`, falling back to the directory name."""
    stamp = AI / "agent" / "framework.json"
    try:
        name = json.loads(stamp.read_text(encoding="utf-8")).get("project")
        if name:
            return str(name)
    except (OSError, ValueError):
        pass
    return AI.parent.name or "."


def tree():
    """Print live tasks as a dependency tree; see the module docstring."""
    if not TASKS.is_dir():
        print("No tasks yet: `.ai/tasks/` does not exist. "
              "Create one with /task create <id> <title>.")
        return 0
    rows = {tid: load(path) for tid, path in task_dirs().items()}
    archived = len(list(TASKS.glob("_archive/*/task.md")))
    if not rows:
        print(f"No live tasks in `.ai/tasks/` ({archived} archived). "
              "Create one with /task create <id> <title>.")
        return 0

    # Nesting uses only edges between live tasks. A dep archived as done
    # cleared and is dropped silently; one archived in another status, or
    # naming no task, is flagged and ignored. Ids match without regard to
    # case, as `resolve` matches them.
    byname = {t.lower(): t for t in rows}
    gone = {t.lower(): load(p)["status"]
            for t, p in task_dirs(archived=True).items()}
    warns, deps = [], {}
    for tid, r in sorted(rows.items()):
        deps[tid] = []
        for d in r["depends"]:
            live = byname.get(d.lower())
            if live:
                if live not in deps[tid]:
                    deps[tid].append(live)
            elif gone.get(d.lower()) == "done":
                continue
            elif d.lower() in gone:
                warns.append(f"- {FLAG} {tid}: depends on {d}, archived as "
                             f"{gone[d.lower()]}, not done.")
            else:
                warns.append(f"- {FLAG} {tid}: depends on {d}, which names "
                             "no task.")
    children = {tid: [] for tid in rows}
    for tid, ds in deps.items():
        for d in ds:
            children[d].append(tid)

    def rank(tid):
        r = rows[tid]
        return (STATUS_ORDER.get(r["status"], 9), r["updated"], tid)

    # Strongly connected components (iterative Tarjan over deps edges).
    # A component of two or more tasks, or one task that names itself,
    # is a cycle.
    comp, index, low, stack, on, n = {}, {}, {}, [], set(), [0]
    for start in sorted(rows):
        if start in index:
            continue
        work = [(start, 0)]
        while work:
            v, i = work.pop()
            if i == 0:
                index[v] = low[v] = n[0]
                n[0] += 1
                stack.append(v)
                on.add(v)
            if i < len(deps[v]):
                work.append((v, i + 1))
                w = deps[v][i]
                if w not in index:
                    work.append((w, 0))
                elif w in on:
                    low[v] = min(low[v], index[w])
                continue
            if low[v] == index[v]:
                members = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp[w] = v
                    members.append(w)
                    if w == v:
                        break
            if work:
                u = work[-1][0]
                low[u] = min(low[u], low[v])
    groups = {}
    for tid, c in comp.items():
        groups.setdefault(c, []).append(tid)

    def cyclic(members):
        return len(members) > 1 or members[0] in deps[members[0]]

    def ring_from(head, members):
        """The shortest dependency path from `head` back to itself inside
        its cycle, in edge order (`head -> ... -> head`)."""
        inside, back, queue = set(members), {head: None}, [head]
        for v in queue:
            for w in deps[v]:
                if w == head:
                    path = [v]
                    while back[path[-1]] is not None:
                        path.append(back[path[-1]])
                    return path[::-1] + [head]
                if w in inside and w not in back:
                    back[w] = v
                    queue.append(w)
        return [head, head]

    # Every cycle is flagged once, in edge order from its first member in
    # sort order. A cycle that waits on nothing outside itself stands on
    # the first level from that member; one that waits on other tasks
    # nests where its tasks fall.
    sources, cycles = [], []
    for members in groups.values():
        head = min(members, key=rank)
        outside = any(comp[d] != comp[head] for m in members for d in deps[m])
        if cyclic(members):
            cycles.append((head, ring_from(head, members), not outside))
        if not outside:
            sources.append((head, members))
    for head, ring, top in sorted(cycles, key=lambda c: rank(c[0])):
        warns.append(f"- {FLAG} dependency cycle: {' -> '.join(ring)}"
                     + (f"; shown from {head}." if top else "."))

    # The tree hangs under the project name. First level, in three
    # passes: tasks that block others and wait on nothing, then the
    # cycles that wait on nothing outside themselves (from their first
    # task in sort order) and tasks whose every dep is unresolvable,
    # then the tasks with no ties at all, as leaves. Independent means
    # nothing it waits on (after pruning) and nothing waiting on it; a
    # task whose every dep is unresolvable is not independent, its
    # warning says why. Every other task is reachable from one of these.
    lone, blockers, rest = [], [], []
    for head, members in sources:
        if cyclic(members):
            rest.append(head)
        elif children[head]:
            blockers.append(head)
        elif rows[head]["depends"]:
            rest.append(head)
        else:
            lone.append(head)
    tops = (sorted(blockers, key=rank) + sorted(rest, key=rank)
            + sorted(lone, key=rank))

    # Shallowest position: a breadth-first pass from the first level
    # gives each task its least depth; it nests under the first, in sort
    # order, of its deps one level up. Child lists are complete before
    # anything is drawn, so `└── ` always marks the last sibling.
    depth = {t: 0 for t in tops}
    queue = list(tops)
    for v in queue:
        for k in sorted(children[v], key=rank):
            if k not in depth:
                depth[k] = depth[v] + 1
                queue.append(k)
    kids = {tid: [] for tid in rows}
    for tid in rows:
        if depth[tid]:
            up = min((d for d in deps[tid] if depth[d] == depth[tid] - 1),
                     key=rank)
            kids[up].append(tid)

    cur, lines = set(pointers()), []

    def emit(tid, prefix, branch):
        r = rows[tid]
        mark = f"{POINTER} " if tid in cur else ""
        note = (f"   blocked: {r['blocked'] or 'no reason recorded'}"
                if r["status"] == "blocked" else "")
        ident = paint(tid, STATUS_COLOR.get(r["status"]))
        lines.append(f"{prefix}{branch}{mark}"
                     f"{STATUS_ICON.get(r['status'], r['status'])} "
                     f"{ident}{note}")
        wider = prefix + ("    " if branch == "└── " else "│   ")
        below = sorted(kids[tid], key=rank)
        for i, k in enumerate(below):
            emit(k, wider, "└── " if i == len(below) - 1 else "├── ")

    for i, tid in enumerate(tops):
        emit(tid, "", "└── " if i == len(tops) - 1 else "├── ")

    print(project())
    print("\n".join(lines))
    print(f"\n{LEGEND}")
    if warns:
        print("\n" + "\n".join(warns))
    print(f"\n{summary(list(rows.values()), archived)}")
    if pointer_line():
        print(pointer_line())
    return 0


def trackers():
    """The tracker access visible from this checkout, as one markdown
    table; see the module docstring."""
    rows = []
    conf = AI / "trackers.conf"
    if conf.is_file():
        entry = {}
        for line in conf.read_text(encoding="utf-8",
                                   errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.partition(":")
            if not sep:
                continue
            key, value = key.strip().lower(), value.strip()
            if key == "name" and entry:
                rows.append(entry)
                entry = {}
            entry[key] = value
        if entry:
            rows.append(entry)
    if shutil.which("gh"):
        repo = ""
        try:
            r = subprocess.run(["gh", "repo", "view", "--json",
                                "nameWithOwner", "-q", ".nameWithOwner"],
                               cwd=AI.parent, capture_output=True, text=True,
                               timeout=10)
            if r.returncode == 0:
                repo = r.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
        rows.append({"name": repo or "this repository", "kind": "github",
                     "command": "gh issue view <number>", "source":
                     "detected: gh on PATH"})
    if shutil.which("jira"):
        rows.append({"name": "jira", "kind": "jira",
                     "command": "jira issue view <KEY>",
                     "source": "detected: jira on PATH"})
    if not rows:
        print("No tracker configured and none detected.")
        print("Add one to `.ai/trackers.conf`, one block per tracker:")
        print("  name: <label>")
        print("  kind: github|jira")
        print("  command: <fetch command, run in the project root>")
        return 0
    print("| Name | Kind | Fetch with | From |")
    print("|---|---|---|---|")
    for r in rows:
        print(f"| {cell(r.get('name', '?'))} | {cell(r.get('kind', '?'))} "
              f"| {cell(r.get('command', '?'))} | "
              f"{cell(r.get('source', '.ai/trackers.conf'))} |")
    return 0


USAGE = ("Usage: tasks.py [list] | tasks.py tree | tasks.py resolve [<id>] "
         "| tasks.py trackers | tasks.py models [worker=<m>] [reviewer=<m>] | "
         "tasks.py start <id> | "
         "tasks.py finish <id> done|blocked [<reason>] | "
         "tasks.py tick <id> done|steps <n> [<n>...] | "
         "tasks.py claim <id> <path> [<path>...]")
TICK_SECTIONS = {"done": "Done when", "steps": "Steps"}
# Where each harness keeps the agent file of a role. A project has the files
# of the harness it was scaffolded for; every one that exists is checked.
AGENT_FILES = {
    "worker": (".claude/agents/worker.md",
               ".github/agents/worker.agent.md",
               ".opencode/agents/worker.md"),
    "reviewer": (".claude/agents/reviewer.md",
                 ".github/agents/reviewer.agent.md",
                 ".opencode/agents/reviewer.md"),
}


# How a user runs the setup command on each harness, and what follows
# (CONCEPT.md section 62). Claude Code and OpenCode run a `!` line from
# their prompt; Copilot's `!` is not verified, so it gets a terminal.
TESTED = "It tests each model as a sub-agent and saves only those that pass."
RUN_FROM = {
    "claude": ("In this session, type:", "! ",
               TESTED + " Then restart the session: it read the agent "
               "files when it started."),
    "opencode": ("In this session, type:", "!",
                 TESTED + " It reloads OpenCode's server itself; the next "
                 "/task do uses the new models."),
    "copilot": ("In a terminal in this project, run:", "",
                "It saves the names without a test (none exists for "
                "Copilot yet). Then restart the session and check them "
                "with a small /task do."),
}


def models_args(args):
    """{role: name} from `worker=<m>` / `reviewer=<m>`, or bare names in
    that order; None for an argument it cannot place."""
    out, bare = {}, []
    for a in args:
        key, sep, value = a.partition("=")
        if sep and key in AGENT_FILES and value:
            out[key] = value
        elif not sep:
            bare.append(a)
        else:
            return None
    for role in AGENT_FILES:
        if role not in out and bare:
            out[role] = bare.pop(0)
    return None if bare else out


def models(args=()):
    root = AI.parent
    wanted = models_args(args)
    if wanted is None:
        print(f"Unknown argument in {' '.join(args)!r}. {USAGE}")
        return 2
    problems, found, current = [], [], {}
    for role, candidates in AGENT_FILES.items():
        files = [c for c in candidates if (root / c).is_file()]
        if not files:
            problems.append(f"{role}: no agent file (looked for "
                            f"{', '.join(candidates)}); run "
                            "/framework-update to restore it")
        for rel in files:
            text = (root / rel).read_text(encoding="utf-8")
            value = frontmatter(text).get("model", "").strip()
            if not value or value.lower() == "inherit":
                problems.append(
                    f"{role}: {rel} has no model (`inherit` does not "
                    "count); set it with the command below, or add a line "
                    "`model: <name>` after the file's `description:` line")
            else:
                found.append(f"{role}: {rel} {value}")
                current.setdefault(role, value)
    if problems:
        print("MODELS MISSING")
        print("\n".join(problems))
        print("Do not start the task and do not pick a model yourself: "
              "tell the user which file needs which line.")
    else:
        print("MODELS OK")
        print("\n".join(found))
    print()
    print("\n".join(run_lines({**current, **wanted})))
    return 1 if problems else 0


def run_lines(names):
    """The setup command for this scaffold's harness. The framework's
    checkout from `$LLM_AGENT_HOME` when it holds init_agent.py, else the
    `init-agent` shell function that install.sh defines."""
    try:
        stamp = json.loads((AI / "agent" / "framework.json")
                           .read_text(encoding="utf-8"))
        harness = stamp.get("harness")
    except (OSError, ValueError):
        harness = None
    where, prefix, after = RUN_FROM.get(harness, RUN_FROM["copilot"])
    home = os.environ.get("LLM_AGENT_HOME", "")
    tool = (f'python3 "{home}/init_agent.py"'
            if home and (Path(home) / "init_agent.py").is_file()
            else "init-agent")
    worker = names.get("worker") or "<worker>"
    reviewer = names.get("reviewer") or "<reviewer>"
    lines = [where,
             f"{prefix}{tool} --models --worker {worker} "
             f"--reviewer {reviewer}",
             after]
    if "<" in worker + reviewer:
        lines.append("Replace <worker> and <reviewer> with model names as "
                     "your harness or provider writes them.")
    return lines


def commit_line(tid, message):
    """The path-scoped `.ai` commit to run: never `add -A`, which would
    sweep a parallel session's half-written files into this commit."""
    return (f"Commit `.ai` now (add notes.md or a notes/ leaf too if you "
            f"changed one): git -C .ai add tasks/{tid} && git -C .ai commit "
            f'-m "{message}"')


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
    running = pointers()
    if tid in running:
        mine, note = running[tid], "kept (it already names this task)"
    else:
        # `.ai/.current` is taken only while the task it names is running;
        # a blocked or finished task's pointer is replaced, as before.
        other = pointer_id(AI / ".current")
        busy = other and other in task_dirs() and \
            load(task_dirs()[other])["status"] == "in-progress"
        mine = AI / (f".current-{tid}" if busy else ".current")
        mine.write_text(f"task: {tid}\npath: .ai/tasks/{tid}/task.md\n"
                        f"started: {today}\nmodified:\n", encoding="utf-8")
        note = ("written (parallel: `.ai/.current` names running task "
                f"{other})" if busy else
                f"written (replaced the pointer to {other})" if other
                else "written")
    print(f"STARTED {tid}: status in-progress, updated {today}; "
          f"`.ai/{mine.name}` {note}.")
    print(f"Claim each host file before you edit it: python3 "
          f".ai/agent/tools/tasks.py claim {tid} <path>...")
    for other, ptr in pointers().items():
        if other != tid:
            owned = ", ".join(claims(ptr)) or "none yet"
            print(f"PARALLEL {other} is running (`.ai/{ptr.name}`), claims: "
                  f"{owned}. Do not edit its files; commit only your paths.")
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
        print(f"BLOCKED {tid}: {reason}. Its pointer is kept for the "
              "resume; `tasks.py start` clears the block.")
        print(commit_line(tid, f"task: blocked {tid}"))
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
    mine = pointers().get(tid)
    if mine:
        mine.unlink()
    print(f"DONE {tid}: status done, updated {today}"
          + (f"; `.ai/{mine.name}` deleted." if mine else "."))
    print(commit_line(tid, f"task: done {tid}"))
    return 0


def tick(arg, which, nums):
    """Tick numbered checkboxes in Done when or Steps, each named."""
    found = live_task(arg) if arg else None
    if not found:
        print(f"No live task {arg!r}.")
        return 1
    try:
        wanted = sorted({int(n) for n in nums})
    except ValueError:
        wanted = []
    if which not in TICK_SECTIONS or not wanted:
        print(USAGE)
        return 2
    tid, path = found
    heading = TICK_SECTIONS[which]
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(heading)}\b.*?$(.*?)(?=^## |\Z)", text,
                  re.M | re.S)
    boxes = (list(re.finditer(r"^\s*[-*] \[([ xX~-])\]\s*(.*)$",
                              m.group(1), re.M)) if m else [])
    bad = [n for n in wanted if not 1 <= n <= len(boxes)]
    if bad:
        print(f"{tid}: `## {heading}` has {len(boxes)} item(s); no item "
              + ", ".join(map(str, bad)) + ". Nothing ticked.")
        return 1
    body = m.group(1)
    for n in reversed(wanted):
        b = boxes[n - 1]
        if b.group(1) == " ":
            body = body[:b.start(1)] + "x" + body[b.end(1):]
    path.write_text(text[:m.start(1)] + body + text[m.end(1):],
                    encoding="utf-8")
    set_fields(path, {"updated": datetime.date.today().isoformat()})
    for n in wanted:
        b = boxes[n - 1]
        state = "TICKED" if b.group(1) == " " else "already ticked"
        print(f"{state} {heading} {n}: {b.group(2)[:90]}")
    got, total = checked(path.read_text(encoding="utf-8"), heading)
    print(f"{tid}: {heading} {got}/{total} ticked.")
    return 0


def claim(arg, files):
    """Add host files to a running task's `modified:` list, refusing any a
    parallel task already claimed."""
    running = pointers()
    found = live_task(arg) if arg else None
    if not found or not files:
        print(f"No live task {arg!r}." if not found else USAGE)
        return 1 if not found else 2
    tid = found[0]
    if tid not in running:
        print(f"{tid} is not running: run `tasks.py start {tid}` first.")
        return 1
    def norm(f):
        return os.path.normpath(f)
    taken = {norm(f): other for other, ptr in running.items()
             if other != tid for f in claims(ptr)}
    clash = [(f, taken[norm(f)]) for f in files if norm(f) in taken]
    if clash:
        for f, other in clash:
            print(f"CLAIMED {f} by running task {other}: do not edit it. "
                  "Ask the user, or wait until that task finishes.")
        return 1
    mine = running[tid]
    have = {norm(f) for f in claims(mine)}
    new = [f for f in dict.fromkeys(files) if norm(f) not in have]
    if new:
        text = mine.read_text(encoding="utf-8")
        if "modified:" not in text:
            text = text.rstrip("\n") + "\nmodified:\n"
        text = text.rstrip("\n") + "\n" + "".join(
            f"  - {f}\n" for f in new)
        mine.write_text(text, encoding="utf-8")
    print(f"CLAIMED for {tid}: " + ", ".join(files)
          + (f" ({len(new)} new)" if new else " (already claimed)"))
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
    if args and args[0] == "claim":
        if len(args) < 3:
            print(USAGE)
            return 2
        return claim(args[1], args[2:])
    if args and args[0] == "tick":
        if len(args) < 4:
            print(USAGE)
            return 2
        return tick(args[1], args[2], args[3:])
    if args and args[0] == "tree":
        return tree()
    if args and args[0] == "trackers":
        return trackers()
    if args and args[0] == "models":
        return models(args[1:])
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
    cur = set(pointers())

    print("| | ID | Type | Status | Title | Steps | Done when | Updated |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        mark = POINTER if r["id"] in cur else ""
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

    notes = flags(rows)
    if notes:
        print()
        print("\n".join(notes))
    print()
    print(summary(rows, archived))
    if pointer_line():
        print(pointer_line())
    return 0


if __name__ == "__main__":
    sys.exit(main())
