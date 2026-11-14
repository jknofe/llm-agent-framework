#!/usr/bin/env python3
"""`init-agent --models` (CONCEPT.md section 59), offline: the frontmatter
rewrite, what counts as a usable name, that the paths in agentgen.const and
the copy inside tasks.py agree, and the rollback when the sub-agent test
fails. The real sub-agent call needs a harness and a model; the scaffold
runbook (tests/task-commands.md, TC-M1) covers it."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentgen import const, content, models  # noqa: E402

FAILS = []
N = [0]


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


AGENT = ("---\nname: worker\ndescription: Works.\n---\nBody\n")


def project(harness="claude", model_lines=None):
    root = Path(tempfile.mkdtemp())
    (root / ".ai/agent/tools").mkdir(parents=True)
    (root / ".ai/agent/tools/tasks.py").write_text(
        content.render_tool_tasks(), encoding="utf-8")
    (root / ".ai/agent").joinpath("framework.json").write_text(
        json.dumps({"harness": harness}), encoding="utf-8")
    for role, rel in const.AGENT_FILES[harness].items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(AGENT.replace("worker", role), encoding="utf-8")
    return root


def args(**kw):
    base = dict(worker=None, reviewer=None, updater=None, no_test=False)
    base.update(kw)
    return argparse.Namespace(**base)


def gate(root):
    return subprocess.run(
        [sys.executable, str(root / ".ai/agent/tools/tasks.py"), "models"],
        capture_output=True, text=True)


def main():
    # Never reload the real OpenCode server from a test; record the calls.
    reloads = []
    models.reload_opencode = reloads.append

    # Name rules.
    check(models.usable("gpt-6.1-sol") and models.usable("a/b#medium"),
          "any concrete name is usable")
    check(not models.usable("") and not models.usable("  ") and
          not models.usable("Inherit"), "empty and inherit are not")

    # Frontmatter rewrite: one model line after description, nothing else.
    out = models.with_model(AGENT, "haiku")
    check(out == "---\nname: worker\ndescription: Works.\nmodel: haiku\n---\n"
                 "Body\n", f"insert after description: {out!r}")
    twice = models.with_model(out, "sonnet")
    check(twice.count("model:") == 1 and "model: sonnet" in twice and
          twice.endswith("Body\n"), "a second call replaces, never adds")
    check(models.with_model(AGENT.replace("description: Works.\n", ""), "m")
          == "---\nname: worker\nmodel: m\n---\nBody\n",
          "no description line: model goes last in the frontmatter")

    # tasks.py's own copy of the paths equals const's, for every harness.
    for harness, paths in const.AGENT_FILES.items():
        root = project(harness)
        for rel in paths.values():
            f = root / rel
            f.write_text(models.with_model(f.read_text(encoding="utf-8"),
                                           "m1"), encoding="utf-8")
        r = gate(root)
        check(r.returncode == 0 and r.stdout.startswith("MODELS OK"),
              f"{harness}: paths agree with tasks.py: {r.stdout!r}")

    # cmd_models: a passing test saves, a failing one rolls back.
    root = project()
    with mock.patch.object(models, "headless_test",
                           return_value=(True, "replied hello")):
        rc = models.cmd_models(root, args(worker="w1", reviewer="r1"))
    check(rc == 0 and gate(root).returncode == 0, "both saved when tests pass")
    wfile = root / const.AGENT_FILES["claude"]["worker"]
    before = wfile.read_text(encoding="utf-8")
    with mock.patch.object(models, "headless_test",
                           return_value=(False, "model_not_found")):
        rc = models.cmd_models(root, args(worker="bad"))
    check(rc == 1 and wfile.read_text(encoding="utf-8") == before,
          "a failed test restores the file byte for byte")
    check(models.cmd_models(root, args(worker="inherit")) == 2 and
          wfile.read_text(encoding="utf-8") == before,
          "inherit is refused before anything is written")
    with mock.patch.object(models, "headless_test") as ht:
        models.cmd_models(root, args(worker="w2", no_test=True))
    check(not ht.called and "model: w2" in wfile.read_text(encoding="utf-8"),
          "--no-test saves without calling the test")

    # Other harnesses: saved with a note, never a fake pass.
    root = project("copilot")
    with mock.patch.object(models, "headless_test") as ht:
        rc = models.cmd_models(root, args(worker="gpt-6.1-sol",
                                          reviewer="gpt-6-luna"))
    check(rc == 0 and not ht.called and gate(root).returncode == 0,
          "copilot: lines written, no test claimed")

    # OpenCode is tested, not just written (CONCEPT.md section 60).
    root = project("opencode")
    with mock.patch.object(models, "headless_test",
                           return_value=(True, "ran")) as ht:
        rc = models.cmd_models(root, args(worker="p/w", reviewer="p/r#high"))
    check(rc == 0 and ht.call_count == 2 and
          ht.call_args.args[2:] == ("opencode", "p/r#high"),
          f"opencode: both roles tested with harness and name: {ht.call_args}")
    check(reloads == [root], f"opencode: the server reloaded once: {reloads}")

    def info(**m):
        return {"info": {"model": m}}
    check(models.ran_on(info(providerID="p", id="m", variant="default"))
          == "p/m" and
          models.ran_on(info(providerID="p", id="m", variant="medium"))
          == "p/m#medium" and
          models.ran_on(info(providerID="p", id="m")) == "p/m",
          "ran_on: default variant is the bare name")
    check(models.ran_on({"info": {}, "messages": [
              {"role": "user"}, {"model": {"providerID": "o", "id": "x"}}]})
          == "o/x", "ran_on: falls back to the messages' model")

    # opencode_test against a fake `opencode`: the run's JSON lines, the
    # child session's export, and the delete.
    def fake_opencode(reply, tool_state, ran):
        events = [{"type": "tool_use", "sessionID": "ses_parent",
                   "part": {"tool": "subagent", "state": tool_state}},
                  {"type": "text", "sessionID": "ses_parent",
                   "part": {"text": reply}}]
        calls = []

        def run(cmd, **kw):
            calls.append(cmd[1:3])
            out = ""
            if cmd[1] == "run":
                out = "\n".join(json.dumps(e) for e in events)
            elif cmd[1:3] == ["session", "export"]:
                out = json.dumps({"info": {"model": ran}})
            check(kw.get("stdin") == subprocess.DEVNULL,
                  f"opencode: stdin closed for {cmd[1:3]}")
            if cmd[1] == "run":
                check("--standalone" in cmd, "opencode: run is standalone")
            return subprocess.CompletedProcess(cmd, 0, out, "")
        return run, calls

    done = {"status": "completed",
            "output": '<subagent sessionID="ses_child" state="completed">'
                      "\nhello\n</subagent>"}
    haiku = {"providerID": "claude-agent", "id": "haiku", "variant": "default"}
    with mock.patch.object(models, "opencode_bin", return_value="oc"):
        run, calls = fake_opencode("SUBAGENT_REPLY: hello", done, haiku)
        with mock.patch.object(models.subprocess, "run", run):
            ok, detail = models.opencode_test(root, "worker",
                                              "claude-agent/haiku")
        check(ok and "ran on claude-agent/haiku" in detail,
              f"opencode: hello on the named model passes: {detail}")
        check(["session", "export"] in calls and
              ["session", "delete"] in calls,
              f"opencode: child exported, sessions deleted: {calls}")

        run, _ = fake_opencode("SUBAGENT_REPLY: hello", done, haiku)
        with mock.patch.object(models.subprocess, "run", run):
            ok, detail = models.opencode_test(root, "reviewer",
                                              "claude-agent/sonnet#medium")
        check(not ok and "not honored" in detail,
              f"opencode: another model than the file's fails: {detail}")

        failed = {"status": "error", "error": "Subagent failed (sessionID: "
                  "ses_child): Model unavailable: claude-agent/nope"}
        run, _ = fake_opencode("SUBAGENT_REPLY: none, it failed", failed,
                               haiku)
        with mock.patch.object(models.subprocess, "run", run):
            ok, detail = models.opencode_test(root, "worker",
                                              "claude-agent/nope")
        check(not ok and "Model unavailable" in detail,
              f"opencode: a failed spawn reports the tool error: {detail}")
    with mock.patch.object(models, "opencode_bin", return_value=None):
        ok, detail = models.opencode_test(root, "worker", "p/m")
    check(not ok and "not on PATH" in detail, "opencode: no binary")

    # OpenCode's TUI has no model flag: its Herdr tab starts plain and
    # spawns the role as a sub-agent (CONCEPT.md section 70).
    for text in (content.render_task_part("do", "opencode"),
                 content.render_update_body("opencode", "$ARGUMENTS")):
        start = next(ln for ln in text.splitlines()
                     if "herdr agent start" in ln)
        check(start.rstrip().endswith("--pane <pane>") and
              "opencode --model" not in text and
              "Use the subagent tool with agent" in text,
              f"opencode: the tab starts without a model flag: {start!r}")
    check("-- --agent worker --model <model>" in
          content.render_task_part("do", "copilot") and
          "-- --agent worker --permission-mode" in
          content.render_task_part("do", "claude"),
          "copilot and claude keep their start flags")

    # Nothing to set and no terminal to ask in: says so, exits non-zero.
    root = project()
    with mock.patch.object(sys.stdin, "isatty", return_value=False):
        rc = models.cmd_models(root, args())
    check(rc == 1, f"no flags, no terminal: exit 1, got {rc}")

    # A forced re-init regenerates the agent files but keeps their model
    # line, on every harness; a fresh file still gets none.
    init = Path(__file__).resolve().parents[1] / "init_agent.py"
    for harness in const.HARNESSES:
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        cmd = [sys.executable, str(init), "--harness", harness, "-y",
               "--name", "p"]
        subprocess.run(cmd, cwd=root, capture_output=True, check=True)
        check(gate(root).returncode == 1, f"{harness}: fresh scaffold unset")
        models.cmd_models(root, args(worker="w9", reviewer="r9",
                                     no_test=True))
        subprocess.run(cmd, cwd=root, capture_output=True, check=True)
        r = gate(root)
        check(r.returncode == 0 and "w9" in r.stdout and "r9" in r.stdout,
              f"{harness}: re-init keeps the model lines: {r.stdout!r}")
        wfile = root / const.AGENT_FILES[harness]["worker"]
        check(wfile.read_text(encoding="utf-8").count("model:") == 1,
              f"{harness}: exactly one model line after re-init")
        # The turn limit (section 78) sits in every role file on claude and
        # opencode, once, and survives `--models` and a re-init.
        key = {"claude": "maxTurns", "opencode": "steps"}.get(harness)
        for role, rel in const.AGENT_FILES[harness].items():
            head = (root / rel).read_text(encoding="utf-8").split("\n---")[0]
            lines = [ln for ln in head.split("\n")
                     if ln.startswith(f"{key}:")] if key else []
            check(not key and "maxTurns" not in head and "steps:" not in head
                  or lines == [f"{key}: {const.ROLE_TURNS[role]}"],
                  f"{harness} {role}: one turn limit line, got {lines}")

    # A missing agent file is an error, not a silent create.
    root = project()
    (root / const.AGENT_FILES["claude"]["reviewer"]).unlink()
    check(models.cmd_models(root, args(worker="w")) == 1, "missing file")

    # The updater (CONCEPT.md section 64) is optional: a scaffold older than
    # 12.2 has no file for it and still sets the other two; asking for it
    # there is the error. Set, it is saved and tested like the others.
    root = project()
    (root / const.AGENT_FILES["claude"]["updater"]).unlink()
    with mock.patch.object(models, "headless_test",
                           return_value=(True, "replied hello")):
        rc = models.cmd_models(root, args(worker="w1", reviewer="r1"))
        check(rc == 0, "no updater file: worker and reviewer still set")
        check(models.cmd_models(root, args(updater="u1")) == 1,
              "no updater file: asking for it is an error")
    r = gate(root)
    check(r.returncode == 0 and "updater: not set" in r.stdout and
          "runs the update inline" in r.stdout,
          f"gate: an unset updater is reported, never a failure: {r.stdout!r}")
    root = project()
    with mock.patch.object(models, "headless_test",
                           return_value=(True, "replied hello")) as t:
        rc = models.cmd_models(root, args(worker="w1", reviewer="r1",
                                          updater="haiku"))
    ufile = root / const.AGENT_FILES["claude"]["updater"]
    r = gate(root)
    check(rc == 0 and t.call_count == 3 and
          models.current(ufile) == "haiku" and
          f"updater: {const.AGENT_FILES['claude']['updater']} haiku"
          in r.stdout and "--updater haiku" in r.stdout,
          f"updater saved, tested, shown with its setup flag: {r.stdout!r}")

    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: models, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
