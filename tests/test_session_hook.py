#!/usr/bin/env python3
"""The SessionStart hook that puts the notes hub in context (CONCEPT.md
section 83).

Run: python3 tests/test_session_hook.py

Stdlib only. Runs templates/hooks/notes_session.py as Claude Code does, with
a JSON payload on stdin, in a temp project with the rendered tasks.py:
the hub is printed under its header, the scaffold's untouched stub is
silent, no hub is silent, a worker started by `--agent worker` gets
nothing, a broken or missing tool fails open (exit 0, no output), the
largest possible output stays under the harness's 10,000-character cap.
Then scaffolds each harness with the real init_agent.py: the claude
settings.json wires `SessionStart` with the four matchers and a timeout to
a script that exists and is a recorded framework file; the other harnesses
get neither.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from agentgen import content  # noqa: E402

FAILS = []
N = [0]


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def project():
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".claude/hooks").mkdir(parents=True)
    (root / ".claude/hooks/notes_session.py").write_text(
        content.render_hook_notes_session(), encoding="utf-8")
    tool = root / ".ai/agent/tools/tasks.py"
    tool.parent.mkdir(parents=True)
    tool.write_text(content.render_tool_tasks(), encoding="utf-8")
    return root


def hook(root, payload, raw=None):
    data = raw if raw is not None else json.dumps(payload)
    return subprocess.run([sys.executable,
                           str(root / ".claude/hooks/notes_session.py")],
                          input=data, capture_output=True, text=True,
                          cwd="/")


def main():
    root = project()
    notes = root / ".ai/notes.md"
    start = {"hook_event_name": "SessionStart", "source": "startup",
             "cwd": str(root)}

    r = hook(root, start)
    check(r.returncode == 0 and r.stdout == "", "no hub: silent, exit 0")
    notes.write_text(content.render_notes_stub(), encoding="utf-8")
    r = hook(root, start)
    check(r.returncode == 0 and r.stdout == "",
          f"the untouched stub: silent: {r.stdout!r}")
    notes.write_text(content.render_notes_stub() + "- db before app\n",
                     encoding="utf-8")
    for source in ("startup", "resume", "clear", "compact"):
        r = hook(root, {**start, "source": source})
        check(r.returncode == 0 and "- db before app" in r.stdout
              and r.stdout.startswith("Project notes, `.ai/notes.md`"),
              f"{source}: hub under its header: {r.stdout!r}")
    check("Running memory" not in r.stdout,
          "the stub's authoring comment is not printed")
    r = hook(root, {**start, "agent_type": "worker"})
    check(r.returncode == 0 and r.stdout == "",
          f"a worker started with --agent gets nothing: {r.stdout!r}")
    r = hook(root, {**start, "agent_type": "other"})
    check("- db before app" in r.stdout, "another agent type still gets it")
    r = hook(root, None, raw="not json")
    check(r.returncode == 0 and "- db before app" in r.stdout,
          "unparsable stdin: treated as an ordinary start")
    r = hook(root, None, raw="[1, 2]")
    check(r.returncode == 0 and r.stdout == "", "a JSON list: silent")
    r = hook(root, None, raw="")
    check(r.returncode == 0 and "- db before app" in r.stdout,
          "empty stdin: ordinary start")

    # The largest possible text stays under the 10,000-character cap.
    notes.write_text("# Project Notes\n" + "".join(
        "- " + "é" * 60 + f" `gone{i}/x.md`\n" for i in range(300)),
        encoding="utf-8")
    r = hook(root, start)
    check(r.returncode == 0 and 0 < len(r.stdout) < 9500,
          f"capped output: {len(r.stdout)} characters")
    check("cut after" in r.stdout and "Notes check" in r.stdout,
          "cut line and flags present")

    # Fail open.
    tool = root / ".ai/agent/tools/tasks.py"
    tool.write_text("def broken(:\n", encoding="utf-8")
    r = hook(root, start)
    check(r.returncode == 0 and r.stdout == "" and "Traceback" not in r.stderr,
          f"a broken tasks.py: silent, exit 0: {r.stdout!r} {r.stderr!r}")
    tool.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    r = subprocess.run([sys.executable,
                        str(root / ".claude/hooks/notes_session.py")],
                       input=json.dumps(start), capture_output=True,
                       text=True, timeout=25)
    check(r.returncode == 0 and r.stdout == "", "a hung tasks.py: silent")
    tool.unlink()
    r = hook(root, start)
    check(r.returncode == 0 and r.stdout == "", "no tasks.py: silent")

    # The wiring, from the real generator.
    for harness in ("claude", "copilot", "opencode"):
        d = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        subprocess.run([sys.executable, str(REPO / "init_agent.py"),
                        "--name", "p", "--description", "d",
                        "--harness", harness, "-y"], cwd=d,
                       capture_output=True, text=True, input="n\n")
        stamp = json.loads((d / ".ai/agent/framework.json").read_text())
        files = stamp["framework_files"]
        if harness == "claude":
            s = json.loads((d / ".claude/settings.json").read_text())
            ss = s["hooks"].get("SessionStart", [])
            check(len(ss) == 1 and ss[0]["matcher"]
                  == "startup|resume|clear|compact",
                  f"claude: SessionStart with the four matchers: {ss}")
            h = ss[0]["hooks"][0] if ss else {}
            check(h.get("type") == "command" and h.get("timeout") == 15
                  and "notes_session.py" in h.get("command", ""),
                  f"claude: a command hook with a timeout: {h}")
            check((d / ".claude/hooks/notes_session.py").is_file()
                  and ".claude/hooks/notes_session.py" in files,
                  "claude: the script exists and is a framework file")
            check("PreToolUse" in s["hooks"] and "Stop" in s["hooks"],
                  "claude: the other hooks stay")
            # End to end in the scaffold: hub text from the real script.
            (d / ".ai/notes.md").write_text(
                "# Project Notes\n- order: a then b\n", encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(d / ".claude/hooks/notes_session.py")],
                input=json.dumps(start), capture_output=True, text=True,
                cwd="/")
            check("- order: a then b" in r.stdout and r.returncode == 0,
                  "claude: the scaffolded hook prints the hub")
        else:
            check(not any("notes_session" in f for f in files)
                  and not (d / ".claude").exists(),
                  f"{harness}: no session hook")
    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: session hook, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
