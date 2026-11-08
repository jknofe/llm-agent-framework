#!/usr/bin/env python3
"""Drive one benchmark run through herdr. Usage:
drive.py <agent-name> <harness> <run-dir> <log>

Every step is a fresh session. Question forms get the highlighted
(recommended) option; a question asked in plain text gets one fixed reply;
Claude's "Teach auto mode" prompt gets Esc and the step prompt again; a
folder-trust prompt for the run directory is accepted; any other blocking
dialog stops the run so a human can look.
"""
import json, os, re, subprocess, sys, time
from pathlib import Path

AGENT, HARNESS, RUN, LOG = sys.argv[1:5]
RUN = Path(RUN)
NEW = {"claude": "/clear", "opencode": "/new"}[HARNESS]
FORM = {"claude": ["Enter to select", "Submit answers", "Review your answers"],
        "opencode": ["enter confirm", "enter submit"]}[HARNESS]
STOP = ["Do you want", "proceed?", "Allow once", "Allow always"]
REPLY = ("No tracker issue, and do not file one. No dependencies. The cargo "
         "criteria are waived. Take your recommended defaults and go on.")

DO = ["input-scale-window", "nextrelease-typo", "readme-troubleshooting",
      "keybinds-consistency", "readme-shortcut-tables",
      "readme-config-reference"]
STEPS = [(f"do:{t}", f"/task do {t}", ("done", t)) for t in DO] + [
    ("create:bug", "/task create plan-pixelate-placeholder The pixelate entry "
     "in the README keeps a NEXTRELEASE placeholder after a release. Docs only; "
     "no Rust toolchain here, I waive all cargo-based criteria. Type: bug",
     ("file", "plan-pixelate-placeholder")),
    ("create:change", "/task create plan-cli-reference Add a command-line "
     "reference table for every satty flag to the README. Docs only; no Rust "
     "toolchain here, I waive all cargo-based criteria. Type: change",
     ("file", "plan-cli-reference")),
    ("list", "/task list", None),
]

log = open(LOG, "a", buffering=1)


def note(*a):
    log.write(time.strftime("%H:%M:%S ") + " ".join(map(str, a)) + "\n")


def herdr(*args, timeout=None):
    r = subprocess.run(["herdr", *args], capture_output=True, text=True,
                       timeout=timeout)
    try:
        return json.loads(r.stdout or r.stderr)
    except ValueError:
        return {}


def status():
    return herdr("agent", "get", AGENT).get("result", {}).get(
        "agent", {}).get("agent_status", "?")


def screen():
    return subprocess.run(["herdr", "agent", "read", AGENT, "--source",
                           "visible"], capture_output=True, text=True).stdout


def wait():
    while True:
        herdr("agent", "wait", AGENT, "--timeout", "900000", timeout=960)
        s = status()
        if s in ("idle", "done", "blocked"):
            return s


def submit(text):
    d = herdr("agent", "prompt", AGENT, text, "--wait", "--timeout",
              "1800000", timeout=1900)
    if d.get("error", {}).get("code") == "agent_prompt_stalled":
        time.sleep(2)
        if text[:25] in screen():
            note("  prompt sat unsent; pressing enter")
            herdr("agent", "send-keys", AGENT, "enter")
            time.sleep(5)


def limited():
    """A usage limit answers every prompt with a notice; replies only feed it."""
    scr = screen()
    return bool(re.search(r"hit your .{0,20}limit|Usage limit reached", scr))


def reached(goal):
    if goal is None:
        return True
    kind, tid = goal
    f = RUN / ".ai" / "tasks" / tid / "task.md"
    if kind == "file":
        return f.is_file()
    if not f.is_file():
        return False
    m = re.search(r"^status:\s*(\S+)", f.read_text(), re.M)
    return bool(m) and m.group(1) in ("done", "blocked")


def settle(text):
    """Wait out one turn, answering forms; returns False on a hard stop."""
    forms = 0
    while True:
        s = wait()
        if s != "blocked":
            return True
        time.sleep(2)
        if status() != "blocked":
            continue
        scr = screen()
        tail = "\n".join(l for l in scr.splitlines() if l.strip())[-1500:]
        if "Teach auto mode" in scr:
            note("  auto-mode teaching prompt: esc, prompt again")
            herdr("agent", "send-keys", AGENT, "esc")
            time.sleep(2)
            submit(text)
            continue
        if any(m in scr for m in FORM) and not any(m in scr for m in STOP):
            forms += 1
            note(f"  form #{forms}: highlighted option\n" + tail)
            if forms > 15:
                note("  STOP: too many forms")
                return False
            herdr("agent", "send-keys", AGENT, "enter")
            time.sleep(3)
            continue
        note("  STOP: blocking dialog that is not a question form\n" + tail)
        return False


EFFORT = os.environ.get("EFFORT", "medium")


def opencode_medium():
    """Cycle the TUI's variant to EFFORT; its saved choice outranks config."""
    for _ in range(7):
        m = re.search(r"Claude Agent · (\w+)", screen())
        if m and m.group(1) == EFFORT:
            return True
        herdr("agent", "send-keys", AGENT, "ctrl+t")
        time.sleep(1.2)
    return False


def main():
    note(f"### start {AGENT} {HARNESS} {RUN}")
    if HARNESS == "opencode" and not opencode_medium():
        note(f"### halted: could not set the {EFFORT} variant")
        return 1
    for i, (name, text, goal) in enumerate(STEPS):
        if i:
            herdr("agent", "prompt", AGENT, NEW, "--wait", "--timeout",
                  "8000", timeout=30)
            time.sleep(4)
        t0 = time.time()
        note(f"== {name}")
        submit(text)
        if not settle(text):
            note(f"### halted at {name}")
            return 1
        if limited():
            note(f"### halted at {name}: usage limit")
            return 1
        nudges = 0
        while not reached(goal) and nudges < 2:
            nudges += 1
            note(f"  goal not reached; plain-text reply #{nudges}")
            submit(REPLY)
            if not settle(text):
                note(f"### halted at {name}")
                return 1
        note(f"  {name} {'ok' if reached(goal) else 'NOT REACHED'} "
             f"{time.time() - t0:.0f}s nudges={nudges}")
    note("### finished")
    return 0


sys.exit(main())
