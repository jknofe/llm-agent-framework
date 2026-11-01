#!/usr/bin/env python3
"""Deterministic test of `delegate.py plan`, the /task do worker dispatch.

Scaffolds both harnesses into a temp dir, writes task files, and checks every
MODE branch (inline asked, worker recursion guard, small plan, herdr,
subagent, and subagent for a folder the harness has not trusted), the model
choice per type and size and harness, the env override, and the round count
from `Worker round` lines. Trust records live in a fake HOME. Herdr and the harness CLIs are
faked with stub executables on PATH; `launch` and `close` talk to a live
Herdr and are covered by tests/task-commands.md, not here.

Usage: python3 tests/test_delegate.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FAILS = []

TASK = """---
id: {id}
type: {type}
status: planned
title: t
---
## Goal
g
## Done when
- [ ] c
## Steps
{steps}
## Findings
{findings}
## Outcome
"""


def scaffold(root, harness):
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run([sys.executable, str(REPO / "init_agent.py"), "--name",
                    "t", "--description", "d", "--harness", harness, "-y"],
                   cwd=root, check=True, capture_output=True)


def task(root, tid, type_, steps, findings=""):
    d = root / ".ai" / "tasks" / tid
    d.mkdir(parents=True, exist_ok=True)
    (d / "task.md").write_text(TASK.format(
        id=tid, type=type_, findings=findings,
        steps="\n".join(f"- [{'x' if s else ' '}] s{i}"
                        for i, s in enumerate(steps))))


HOME = {}


def plan(root, tid, *extra, env=None, path=""):
    e = {k: v for k, v in os.environ.items()
         if k not in ("HERDR_ENV", "LLM_AGENT_ROLE", "CLAUDE_CONFIG_DIR",
                      "COPILOT_HOME", "LLM_AGENT_WORKER_MODEL")}
    e["PATH"] = path or "/usr/bin:/bin"
    e["HOME"] = HOME["dir"]
    e.update(env or {})
    out = subprocess.run(
        [sys.executable, str(root / ".ai/agent/tools/delegate.py"), "plan",
         tid, *extra], capture_output=True, text=True, env=e)
    return dict(line.split(" ", 1) for line in out.stdout.splitlines()
                if " " in line)


def expect(label, got, **want):
    for k, v in want.items():
        if got.get(k) != v:
            FAILS.append(f"{label}: {k}={got.get(k)!r}, want {v!r}")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        bindir = tmp / "bin"
        bindir.mkdir()
        for name in ("herdr", "claude", "copilot"):
            (bindir / name).write_text("#!/bin/sh\nexit 0\n")
            (bindir / name).chmod(0o755)
        fake = f"{bindir}:/usr/bin:/bin"
        herdr_env = {"HERDR_ENV": "1"}
        home = tmp / "home"
        (home / ".copilot").mkdir(parents=True)
        HOME["dir"] = str(home)

        c = tmp / "claude"
        scaffold(c, "claude")
        u = tmp / "claude-untrusted"
        scaffold(u, "claude")
        task(u, "big-bug", "bug", [0, 0, 0, 0])
        claude_cfg = home / ".claude.json"
        claude_cfg.write_text(json.dumps({"projects": {
            str(c): {"hasTrustDialogAccepted": True},
            str(tmp): {"hasTrustDialogAccepted": True}}}))
        task(c, "big-bug", "bug", [0, 0, 0, 0])
        task(c, "small-change", "change", [0, 0, 0])
        task(c, "tiny", "change", [1, 0, 0])
        task(c, "Round-3", "investigation", [0, 0, 0, 0],
             "- d Worker round 1: stuck: x\n- d Supervisor round 1: y\n"
             "- d Worker round 2: stuck: x\n")

        expect("subagent", plan(c, "big-bug"), MODE="subagent",
               KIND="claude", MODEL="sonnet", ROUND="1")
        expect("herdr", plan(c, "big-bug", env=herdr_env, path=fake),
               MODE="herdr")
        # A trusted parent does not cover a claude project folder.
        untrusted = plan(u, "big-bug", env=herdr_env, path=fake)
        expect("herdr untrusted", untrusted, MODE="subagent")
        if "trust" not in untrusted.get("REASON", ""):
            FAILS.append(f"untrusted reason: {untrusted.get('REASON')!r}")
        expect("herdr untrusted, no herdr env", plan(u, "big-bug"),
               MODE="subagent")
        claude_cfg.write_text("not json")
        expect("trust record unreadable", plan(u, "big-bug", env=herdr_env,
                                               path=fake), MODE="herdr")
        claude_cfg.unlink()
        expect("trust record missing", plan(u, "big-bug", env=herdr_env,
                                            path=fake), MODE="herdr")
        expect("herdr without CLI", plan(c, "big-bug", env=herdr_env),
               MODE="subagent")
        expect("herdr env unset", plan(c, "big-bug", path=fake),
               MODE="subagent")
        expect("inline asked", plan(c, "big-bug", "inline", env=herdr_env,
                                    path=fake), MODE="inline")
        expect("worker guard", plan(c, "big-bug", env={
            **herdr_env, "LLM_AGENT_ROLE": "worker"}, path=fake),
            MODE="inline")
        expect("small change", plan(c, "small-change"), MODE="subagent",
               MODEL="haiku")
        expect("tiny inline", plan(c, "tiny"), MODE="inline")
        expect("override", plan(c, "big-bug", env={
            "LLM_AGENT_WORKER_MODEL": "opus"}), MODEL="opus")
        r3 = plan(c, "round-3")
        expect("round count, id case", r3, ROUND="3", MODEL="sonnet",
               MODE="subagent")
        if "task Round-3, round 3" not in r3.get("PROMPT", ""):
            FAILS.append(f"prompt: {r3.get('PROMPT')!r}")
        if "NONE" not in subprocess.run(
                [sys.executable, str(c / ".ai/agent/tools/delegate.py"),
                 "plan", "nope"], capture_output=True, text=True).stdout:
            FAILS.append("unknown id: no NONE verdict")

        p = tmp / "copilot"
        scaffold(p, "copilot")
        task(p, "small-change", "change", [0, 0, 0])
        copilot_cfg = home / ".copilot" / "config.json"
        copilot_cfg.write_text('// comment line\n{"trustedFolders": []}')
        expect("copilot untrusted", plan(p, "small-change", env=herdr_env,
                                         path=fake), MODE="subagent")
        # Copilot trust covers subfolders of a trusted folder.
        copilot_cfg.write_text(json.dumps({"trustedFolders": [str(tmp)]}))
        expect("copilot", plan(p, "small-change", env=herdr_env, path=fake),
               MODE="herdr", KIND="copilot", MODEL="auto")

    for f in FAILS:
        print("FAIL", f)
    print("ok" if not FAILS else f"{len(FAILS)} failure(s)")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
