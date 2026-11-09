"""`init-agent --models`: set the model of the `worker` and the `reviewer`
sub-agent of this project, and prove each one answers as a sub-agent
(CONCEPT.md section 59).

The model of a role is the `model:` line of its agent file, written here and
nowhere else. The framework knows no model names: whatever the user types is
written as given, so a name served through a proxy works. The test is the
real thing, a fresh headless session that spawns the role as a sub-agent and
must get "hello" back; a model that cannot be used that way is not saved.
Only Claude Code has the test so far: the other harnesses get the line and a
note, until their headless sub-agent call is verified."""
import json
import re
import subprocess
import sys
from pathlib import Path

from .const import AGENT_FILES, FRAMEWORK_JSON, ROLES, TOOLS_DIR

TEST_TIMEOUT = 240

# The parent session's whole job. The sub-agent is spawned by the harness
# itself, so this exercises the path /task do uses; the exact reply line is
# the verdict, because a failed spawn still ends the parent's turn cleanly.
TEST_PROMPT = ("Use the Agent tool with subagent_type {role} and the prompt "
               "'Reply with the single word hello'. Then print one line: "
               "SUBAGENT_REPLY: followed by its reply, nothing else.")
REPLY = re.compile(r"^SUBAGENT_REPLY:\s*\W*hello\W*$", re.I | re.M)


def usable(value: str) -> bool:
    """A concrete name: not empty and not `inherit`, which is the session's
    model and so no choice at all."""
    return bool(value.strip()) and value.strip().lower() != "inherit"


def current(path: Path) -> str:
    """The `model:` value of an agent file, "" when there is none."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 3)
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() == "model":
            return value.strip().strip("\"'")
    return ""


def with_model(text: str, value: str) -> str:
    """The agent file with exactly one `model:` line, right after its
    `description:` line; everything else untouched."""
    if not text.startswith("---\n"):
        raise ValueError("agent file has no frontmatter")
    end = text.find("\n---", 3)
    head = [ln for ln in text[4:end].split("\n")
            if ln.partition(":")[0].strip() != "model"]
    new = f"model: {value}"
    at = next((i + 1 for i, ln in enumerate(head)
               if ln.partition(":")[0].strip() == "description"), len(head))
    head.insert(at, new)
    return "---\n" + "\n".join(head) + text[end:]


def headless_test(root: Path, role: str) -> tuple:
    """(ok, detail) for one role on Claude Code."""
    try:
        run = subprocess.run(
            ["claude", "-p", TEST_PROMPT.format(role=role),
             "--output-format", "json", "--no-session-persistence"],
            cwd=root, capture_output=True, text=True, timeout=TEST_TIMEOUT)
    except FileNotFoundError:
        return False, "the `claude` command is not on PATH"
    except subprocess.TimeoutExpired:
        return False, f"no answer within {TEST_TIMEOUT} s"
    try:
        data = json.loads(run.stdout)
    except ValueError:
        return False, (run.stderr.strip() or run.stdout.strip()
                       or f"exit {run.returncode}")[:400]
    result = str(data.get("result", "")).strip()
    models = ", ".join((data.get("modelUsage") or {}).keys())
    if REPLY.search(result):
        return True, f"replied hello; models seen: {models}"
    why = result or run.stderr.strip() or "no reply"
    return False, why[:400]


def cmd_models(root: Path, args) -> int:
    stamp = root / FRAMEWORK_JSON
    try:
        harness = json.loads(stamp.read_text(encoding="utf-8"))["harness"]
        files = {role: root / rel
                 for role, rel in AGENT_FILES[harness].items()}
    except (OSError, ValueError, KeyError):
        print("No agent scaffold here (or an unknown harness): run "
              "init-agent first.", file=sys.stderr)
        return 1
    missing = [str(f.relative_to(root)) for f in files.values()
               if not f.is_file()]
    if missing:
        print("Agent file missing: " + ", ".join(missing) + ". Run "
              "/framework-update to restore it.", file=sys.stderr)
        return 1

    wanted = {"worker": args.worker, "reviewer": args.reviewer}
    if not any(wanted.values()) and sys.stdin.isatty():
        for role in ROLES:
            have = current(files[role])
            answer = input(f"{role} model [{have or 'not set'}]: ").strip()
            wanted[role] = answer or None
    elif not any(wanted.values()):
        print("Nothing to set: pass --worker and/or --reviewer (no terminal "
              "to ask in, e.g. under `!` from a session).", file=sys.stderr)
    for role, value in wanted.items():
        if value is not None and not usable(value):
            print(f"{role}: {value!r} is not a model name (`inherit` is the "
                  "session's model, not a choice).", file=sys.stderr)
            return 2

    saved, failed = [], False
    for role in ROLES:
        value = wanted[role]
        if value is None:
            continue
        path = files[role]
        before = path.read_text(encoding="utf-8")
        path.write_text(with_model(before, value), encoding="utf-8")
        if args.no_test:
            saved.append(role)
            print(f"{role}: {value} saved, not tested.")
            continue
        if harness != "claude":
            saved.append(role)
            print(f"{role}: {value} saved. No automatic test on {harness} "
                  "yet: run `/task do` on a small task and check the "
                  "worker's report.")
            continue
        print(f"{role}: testing {value} as a sub-agent ...", flush=True)
        ok, detail = headless_test(root, role)
        if ok:
            saved.append(role)
            print(f"{role}: {value} OK ({detail})")
        else:
            path.write_text(before, encoding="utf-8")
            failed = True
            print(f"{role}: {value} FAILED, not saved. {detail}")
    if saved:
        print("A running session read the agent files when it started: "
              "restart it to use the new models.")
    # The exit status is the gate's: a run that leaves a role unset, even
    # one that set nothing at all, did not do its job.
    gate = root / TOOLS_DIR / "tasks.py"
    gate_rc = 0
    if gate.is_file():
        run = subprocess.run([sys.executable, str(gate), "models"],
                             capture_output=True, text=True)
        print(run.stdout.rstrip())
        gate_rc = run.returncode
    return 1 if failed or gate_rc else 0
