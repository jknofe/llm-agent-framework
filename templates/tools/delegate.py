#!/usr/bin/env python3
"""Worker dispatch for /task do: who works a task's steps, on what model.

`/task do` splits the work in two (CONCEPT.md section 49, after Google's
Elephant-Goldfish Model). The session that ran `/task do` is the supervisor,
the elephant: it holds the conversation with the user, verifies every
round from the files and owns the review gate, the Outcome and `finish`.
The steps themselves go to a worker, the goldfish: a fresh context on a
lower-tier model that knows only the task file, `.ai/notes.md` and
`.ai/agent/task/work.md`. This script makes the choice deterministically, so
no agent improvises it.

`delegate.py plan <id> [inline]` prints the decision, one `KEY value` per line:
  MODE    herdr | subagent | inline
  KIND    the agent CLI the worker runs (the scaffold's harness, so the
          worker runs under the same hooks and permissions)
  MODEL   the worker's model
  ROUND   the next worker round for this task
  REASON  why, in one sentence
  PROMPT  the whole instruction to hand the worker
MODE is chosen in this order:
  inline    `inline` was asked for; this process is itself a worker
            (LLM_AGENT_ROLE=worker); or at most SMALL_STEPS unticked steps
            remain, where a hand-off costs more than the work
  herdr     the session runs inside Herdr (HERDR_ENV=1, `herdr` on PATH),
            the harness CLI is installed, and the harness trusts the
            project folder: the worker gets its own tab the user can watch
            and step into
  subagent  anything else: a fresh sub-agent of the harness. An untrusted
            folder lands here because a worker started there stops at the
            harness's folder-trust dialog, which only the user may answer
Trust is read from the harness's own record: claude's `.claude.json`
(`projects.<path>.hasTrustDialogAccepted`, the exact folder only; a
trusted parent does not cover it), copilot's `~/.copilot/config.json`
(`trustedFolders`, the folder or a parent). When the record cannot be
read, the folder counts as trusted and `launch` catches a dialog.
MODEL: LLM_AGENT_WORKER_MODEL when set. Otherwise, on claude, `haiku` for a
`change` or `test` task with at most SMALL_PLAN steps in all, `sonnet` for
everything else (bugs and investigations reason more than they type); on
copilot `auto`, Copilot's own pick, since its model names change too often to
pin here.

`delegate.py launch <id>` (herdr only) opens a tab labelled `task:<id>` in
the project root without taking focus, starts the worker agent there with
MODEL, and submits PROMPT. Every round gets a fresh worker: a worker still
alive from the previous round is closed with its tab first, so no round
carries the last one's context and corrections reach it only through the
task file, as with a sub-agent. Prints the agent name and the command that
waits for it. `delegate.py close <id>` closes the worker's tab.

The round count is read from the `Worker round <n>` lines in Findings.
`plan` reads only the task file and the environment; `launch` and `close`
talk only to Herdr. Neither writes a file. Stdlib only.

Usage: python3 .ai/agent/tools/delegate.py plan|launch|close <id> [inline]
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[2]  # the .ai/ directory
ROOT = AI.parent
TASKS = AI / "tasks"
WORK = ".ai/agent/task/work.md"

SMALL_STEPS = 2   # unticked steps at or below which the supervisor works inline
SMALL_PLAN = 3    # total steps at or below which a change/test gets haiku
CLI = {"claude": "claude", "copilot": "copilot"}
# Worker CLI arguments per harness. Claude's `auto` permission mode lets the
# worker run its tests without a prompt per command while a classifier still
# stops destructive actions; a prompt it does raise shows as `blocked`.
ARGS = {
    "claude": lambda m: ["--model", m, "--permission-mode",
                         os.environ.get("LLM_AGENT_WORKER_PERMISSION",
                                        "auto")],
    "copilot": lambda m: ["--model", m],
}
USAGE = "Usage: delegate.py plan|launch|close <id> [inline]"


def harness():
    try:
        stamp = json.loads((AI / "agent" / "framework.json").read_text())
        return stamp.get("harness") or "claude"
    except (OSError, ValueError):
        return "claude"


def task_file(tid):
    for path in TASKS.glob("*/task.md"):
        if path.parent.name.lower() == tid.lower():
            return path
    return None


def trusted(h):
    """Whether the harness has trusted the project folder: True, False, or
    None when its record cannot be read."""
    root = os.path.realpath(ROOT)
    try:
        if h == "claude":
            base = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home())
            cfg = json.loads(Path(base, ".claude.json").read_text())
            return any(os.path.realpath(k) == root
                       and v.get("hasTrustDialogAccepted")
                       for k, v in (cfg.get("projects") or {}).items())
        if h == "copilot":
            base = os.environ.get("COPILOT_HOME") or str(Path.home() /
                                                         ".copilot")
            raw = Path(base, "config.json").read_text()
            cfg = json.loads(re.sub(r"(?m)^\s*//.*$", "", raw))
            folders = [os.path.realpath(f)
                       for f in cfg.get("trustedFolders") or []]
            return any(root == f or root.startswith(f.rstrip("/") + "/")
                       for f in folders)
    except (OSError, ValueError, AttributeError):
        return None
    return None


def section(text, heading):
    m = re.search(rf"^## {heading}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def frontmatter_value(text, key):
    m = re.search(rf"^{key}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def plan(tid, want_inline=False):
    path = task_file(tid)
    if path is None:
        print(f"NONE {tid}\nNo live task `{tid}`: run tasks.py resolve.")
        return 1
    tid = path.parent.name
    text = path.read_text(encoding="utf-8")
    steps = section(text, "Steps")
    total = len(re.findall(r"^\s*- \[[ xX]\]", steps, re.M))
    open_ = len(re.findall(r"^\s*- \[ \]", steps, re.M))
    kind = frontmatter_value(text, "type")
    rnd = len(re.findall(r"Worker round \d+", section(text, "Findings"))) + 1
    h = harness()
    cli = CLI.get(h, h)

    model = os.environ.get("LLM_AGENT_WORKER_MODEL", "")
    if not model:
        if h == "copilot":
            model = "auto"
        elif kind in ("change", "test") and total <= SMALL_PLAN:
            model = "haiku"
        else:
            model = "sonnet"

    if want_inline:
        mode, why = "inline", "inline was asked for"
    elif os.environ.get("LLM_AGENT_ROLE") == "worker":
        mode, why = "inline", "this session is itself a worker: never delegate"
    elif open_ <= SMALL_STEPS and rnd == 1:
        mode, why = "inline", (f"{open_} unticked step(s) left: a hand-off "
                               "costs more than the work")
    elif (os.environ.get("HERDR_ENV") == "1" and shutil.which("herdr")
          and shutil.which(cli)):
        if trusted(h) is False:
            mode, why = "subagent", (f"inside Herdr, but {cli} has not "
                                     "trusted this folder: a worker tab "
                                     "would stop at the trust dialog")
        else:
            mode, why = "herdr", "inside Herdr: the worker gets its own tab"
    else:
        mode, why = "subagent", "no Herdr: a fresh sub-agent of the harness"

    prompt = (f"You are the worker for task {tid}, round {rnd}. Read "
              f"{WORK} and follow it.")
    print(f"MODE {mode}\nKIND {cli}\nMODEL {model}\nROUND {rnd}\n"
          f"REASON {why}\nPROMPT {prompt}")
    return 0


def herdr(*args):
    out = subprocess.run(["herdr", *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"herdr {' '.join(args)}: "
                           f"{(out.stderr or out.stdout).strip()}")
    try:
        return json.loads(out.stdout or "{}")
    except ValueError:
        return {}


def agent_name(tid):
    name = "w-" + re.sub(r"[^a-z0-9_-]", "-", tid.lower())
    return name[:32]


def decision(tid):
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = plan(tid)
    if code:
        print(buf.getvalue(), end="")
        return None
    return dict(line.split(" ", 1) for line in buf.getvalue().splitlines())


def launch(tid):
    d = decision(tid)
    if d is None:
        return 1
    if d["MODE"] != "herdr":
        print(f"MODE is {d['MODE']}, not herdr: {d['REASON']}. Nothing "
              "launched; follow the plan output instead.")
        return 2
    name = agent_name(tid)
    tab_id = None
    try:
        # A fresh worker per round: retire the previous round's worker so the
        # name is free and nothing it remembers leaks into this round.
        old = close_worker(name)
        if old:
            print(f"CLOSED previous worker {name} ({old})")
        where = (["--workspace", os.environ["HERDR_WORKSPACE_ID"]]
                 if os.environ.get("HERDR_WORKSPACE_ID") else [])
        tab = herdr("tab", "create", *where, "--cwd", str(ROOT),
                    "--label", f"task:{tid}", "--no-focus",
                    "--env", "LLM_AGENT_ROLE=worker")["result"]
        tab_id = find_key(tab, "tab_id")
        pane = find_key(tab.get("root_pane"), "pane_id")
        herdr("agent", "start", name, "--kind", d["KIND"], "--pane",
              pane, "--timeout", "60000", "--",
              *ARGS.get(d["KIND"], lambda m: [])(d["MODEL"]))
        submit(name, d["PROMPT"])
        print(f"LAUNCHED {name} in tab {tab_id} "
              f"({d['KIND']}, {d['MODEL']}, round {d['ROUND']})")
    except (RuntimeError, KeyError, TypeError) as e:
        # A worker that never got its prompt is useless and its tab would be
        # left behind: show what it was stuck on (a folder-trust or login
        # dialog is the usual cause, and only the user may answer it), then
        # close the tab so the fallback starts clean.
        screen = ""
        if tab_id:
            try:
                out = subprocess.run(
                    ["herdr", "agent", "read", name, "--source", "visible"],
                    capture_output=True, text=True).stdout
                screen = "\n".join(l for l in out.splitlines()
                                   if l.strip())[-1200:]
            except OSError:
                pass
            subprocess.run(["herdr", "tab", "close", tab_id],
                           capture_output=True)
        print(f"FAILED {e}")
        if screen:
            print(f"The worker's screen before its tab was closed:\n{screen}")
        print("Fall back to MODE subagent, and tell the user why Herdr "
              "failed: a dialog above is theirs to answer.")
        return 3
    print(f"Wait: herdr agent wait {name} --timeout 540000")
    return 0


def submit(name, prompt):
    """Submit and confirm the worker started a turn. Herdr only counts a
    prompt as delivered once activity follows, so wait briefly: a timeout
    while it works is success, a stall or a dialog is not."""
    out = subprocess.run(["herdr", "agent", "prompt", name, prompt, "--wait",
                          "--timeout", "20000"], capture_output=True,
                         text=True)
    text = out.stdout + out.stderr
    for bad in ("agent_prompt_stalled", "agent_blocked", "not_found"):
        if bad in text:
            raise RuntimeError(f"herdr agent prompt {name}: {text.strip()}")


def find_key(obj, key):
    """First value under `key` anywhere in a Herdr JSON response."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        obj = list(obj.values())
    if isinstance(obj, list):
        for item in obj:
            found = find_key(item, key)
            if found:
                return found
    return None


def close_worker(name):
    """Close the live worker's tab; return its tab id, or None if no worker
    by that name is alive."""
    try:
        tab = find_key(herdr("agent", "get", name), "tab_id")
    except RuntimeError:
        return None
    if tab:
        herdr("tab", "close", tab)
    return tab


def close(tid):
    name = agent_name(tid)
    tab = close_worker(name)
    if not tab:
        print(f"No live worker {name}: nothing to close.")
        return 0
    print(f"CLOSED {name} ({tab})")
    return 0


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ("plan", "launch", "close"):
        print(USAGE)
        return 2
    if args[0] == "plan":
        return plan(args[1], "inline" in args[2:])
    if args[0] == "launch":
        return launch(args[1])
    return close(args[1])


if __name__ == "__main__":
    sys.exit(main())
