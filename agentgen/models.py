"""`init-agent --models`: set the model of the `worker` and the `reviewer`
sub-agent of this project, and of the optional `updater` (CONCEPT.md
section 64), and prove each one answers as a sub-agent (section 59).

The model of a role is the `model:` line of its agent file, written here and
nowhere else. The framework knows no model names: whatever the user types is
written as given, so a name served through a proxy works. The test is the
real thing, a fresh headless session that spawns the role as a sub-agent and
must get "hello" back; a model that cannot be used that way is not saved.
Claude Code and OpenCode have the test (sections 59 and 60); Copilot gets the
line and a note until its headless sub-agent call is verified."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .const import AGENT_FILES, FRAMEWORK_JSON, ROLES, TASK_ROLES, TOOLS_DIR

TEST_TIMEOUT = 240

# The parent session's whole job. The sub-agent is spawned by the harness
# itself, so this exercises the path /task do uses; the exact reply line is
# the verdict, because a failed spawn still ends the parent's turn cleanly.
# The worker's and updater's descriptions restrict them to their command
# ("Spawned by /task do only"); a parent model may take that literally and
# refuse the test (seen on OpenCode, CONCEPT.md section 71), so the prompt
# names this call as the one sanctioned exception.
TEST_PROMPT = ("This is the framework's model check (`init-agent --models`), "
               "the one sanctioned call of the {role} agent outside its "
               "command. Use the {tool} tool with {param} {role} and the "
               "prompt 'Model check from init-agent, not a task: reply with "
               "the single word hello and do nothing else.' Then print one "
               "line: SUBAGENT_REPLY: followed by its reply, nothing else.")
TOOL_WORDS = {"claude": ("Agent", "subagent_type"),
              "opencode": ("subagent", "agent")}
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


def prompt(harness: str, role: str) -> str:
    tool, param = TOOL_WORDS[harness]
    return TEST_PROMPT.format(tool=tool, param=param, role=role)


def headless_test(root: Path, role: str, harness: str, value: str) -> tuple:
    """(ok, detail) for one role on a harness in TOOL_WORDS."""
    if harness == "opencode":
        return opencode_test(root, role, value)
    return claude_test(root, role)


def claude_test(root: Path, role: str) -> tuple:
    try:
        run = subprocess.run(
            ["claude", "-p", prompt("claude", role),
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


def opencode_bin():
    """`opencode` on PATH, else where its installer puts it."""
    home = Path.home() / ".opencode" / "bin" / "opencode"
    return shutil.which("opencode") or (str(home) if home.is_file() else None)


def ran_on(export: dict) -> str:
    """`provider/model[#variant]` from an exported session: `info.model`, or
    where that is missing the model of its messages (both shapes were
    seen). The variant OpenCode calls `default` is the bare name, which is
    what a file without a variant runs on."""
    m = (export.get("info") or {}).get("model") or next(
        (msg["model"] for msg in export.get("messages") or []
         if isinstance(msg.get("model"), dict)), {})
    name = f"{m.get('providerID', '?')}/{m.get('id', '?')}"
    variant = m.get("variant")
    return f"{name}#{variant}" if variant and variant != "default" else name


def opencode_test(root: Path, role: str, value: str) -> tuple:
    """`opencode run` spawns the role through its `subagent` tool. The verdict
    is the reply line plus the sub-agent's exported session: it records the
    model the sub-agent ran on, which must be the one the file names. Both
    sessions are deleted afterwards (the parent's deletes its children).

    `--standalone`: the background service keeps the agent files it read
    first and ran the sub-agent on the old model; a private server reads
    them now. stdin closed: with it open, `opencode run` waits on it."""
    oc = opencode_bin()
    if not oc:
        return False, "the `opencode` command is not on PATH"
    quiet = dict(cwd=root, capture_output=True, text=True,
                 stdin=subprocess.DEVNULL)
    try:
        run = subprocess.run([oc, "run", "--standalone", "--format", "json",
                              prompt("opencode", role)],
                             timeout=TEST_TIMEOUT, **quiet)
    except subprocess.TimeoutExpired:
        return False, f"no answer within {TEST_TIMEOUT} s"
    texts, child, parent, error = [], None, None, ""
    for line in run.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        parent = parent or event.get("sessionID")
        part = event.get("part") or {}
        if event.get("type") == "text":
            texts.append(part.get("text", ""))
        elif (event.get("type") == "tool_use"
              and part.get("tool") == "subagent"):
            state = part.get("state") or {}
            found = re.search(r'sessionID[=:]\s*"?([\w-]+)',
                              str(state.get("output") or state.get("error")))
            child = child or (state.get("metadata") or {}).get("sessionID") \
                or (found.group(1) if found else None)
            if state.get("status") == "error":
                error = str(state.get("error") or "")
    ran = ""
    if child:
        export = subprocess.run([oc, "session", "export", child], **quiet)
        try:
            ran = ran_on(json.loads(export.stdout))
        except ValueError:
            pass
    if parent:
        subprocess.run([oc, "session", "delete", parent], **quiet)
    reply = "\n".join(texts)
    if not REPLY.search(reply):
        why = error or reply.strip() or run.stderr.strip() or "no reply"
        return False, why[:400]
    if not ran:
        return False, "replied hello, but the sub-agent's model could not " \
                      "be read back from its session"
    if value.strip() != ran:
        return False, f"the sub-agent ran on {ran}, not {value}: the agent " \
                      "file was not honored"
    return True, f"replied hello; sub-agent ran on {ran}"


def reload_opencode(root: Path):
    """OpenCode's background server keeps the agent files it read first and
    does not notice an edit; `opencode reload` makes it read them again
    (CONCEPT.md section 60)."""
    oc = opencode_bin()
    run = subprocess.run([oc, "reload"], cwd=root, capture_output=True,
                         text=True, stdin=subprocess.DEVNULL) if oc else None
    if run and run.returncode == 0:
        print("OpenCode's background server reloaded the agent files "
              "(`opencode reload`); `opencode debug agents` shows them.")
    else:
        print("OpenCode's background server keeps the agent files it read "
              "first: run `opencode reload` before the next /task do.")


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
    wanted = {"worker": args.worker, "reviewer": args.reviewer,
              "updater": getattr(args, "updater", None)}
    # A scaffold older than 12.2 has no updater file yet: it is only an
    # error when that role is asked for.
    missing = [str(files[role].relative_to(root)) for role in ROLES
               if not files[role].is_file()
               and (role in TASK_ROLES or wanted[role])]
    if missing:
        print("Agent file missing: " + ", ".join(missing) + ". Run "
              "/framework-update to restore it.", file=sys.stderr)
        return 1

    if not any(wanted.values()) and sys.stdin.isatty():
        for role in ROLES:
            if not files[role].is_file():
                continue
            have = current(files[role])
            hint = " (optional, a small model)" if role == "updater" else ""
            answer = input(f"{role} model{hint} [{have or 'not set'}]: "
                           ).strip()
            wanted[role] = answer or None
    elif not any(wanted.values()):
        print("Nothing to set: pass --worker, --reviewer and/or --updater "
              "(no terminal to ask in, e.g. under `!` from a session).",
              file=sys.stderr)
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
        if harness not in TOOL_WORDS:
            saved.append(role)
            print(f"{role}: {value} saved. No automatic test on {harness} "
                  "yet: run `/task do` on a small task and check the "
                  "worker's report.")
            continue
        print(f"{role}: testing {value} as a sub-agent ...", flush=True)
        ok, detail = headless_test(root, role, harness, value)
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
        if harness == "opencode":
            reload_opencode(root)
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
