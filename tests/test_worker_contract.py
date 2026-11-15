#!/usr/bin/env python3
"""The worker's contract as its agent body (CONCEPT.md section 85).

Run: python3 tests/test_worker_contract.py

Stdlib only. Scaffolds each harness with the real init_agent.py and checks:
on Claude Code and OpenCode the worker file's body holds the whole of
`.ai/agent/task/work.md` (one template, so the two cannot differ), with the
model-check guard first; Copilot's body is the pointer; the supervisor's
spawn prompt in `do.md` tells a claude or opencode worker nothing to read and
a Copilot worker to read work.md; the first step reads notes, task file and
steps.md in one turn; a `model:` line set in the file survives a forced
re-init exactly once with the longer body; frontmatter limits are intact; no
leftover slot.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from agentgen import models  # noqa: E402

FAILS = []
N = [0]
FILES = {"claude": ".claude/agents/worker.md",
         "opencode": ".opencode/agents/worker.md",
         "copilot": ".github/agents/worker.agent.md"}


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def init(root, harness):
    return subprocess.run(
        [sys.executable, str(REPO / "init_agent.py"), "--name", "p",
         "--description", "d", "--harness", harness, "-y"], cwd=root,
        capture_output=True, text=True, input="n\n")


def split(text):
    end = text.index("\n---", 3)
    return text[4:end], text[end + 5:]


def main():
    for harness, rel in FILES.items():
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        init(root, harness)
        agent = (root / rel).read_text(encoding="utf-8")
        work = (root / ".ai/agent/task/work.md").read_text(encoding="utf-8")
        do = (root / ".ai/agent/task/do.md").read_text(encoding="utf-8")
        head, body = split(agent)
        check("${" not in agent, f"{harness}: no unfilled slot")
        if harness == "copilot":
            check(work.strip() not in body and ".ai/agent/task/work.md"
                  in body, "copilot: the body only points at work.md")
            check("`You are the worker for task <id>. Read "
                  ".ai/agent/task/work.md and follow it.`" in do,
                  "copilot: the spawn prompt reads work.md")
        else:
            check(work.strip() in body, f"{harness}: body holds work.md whole")
            check(body.index("init-agent") < body.index(work.strip()[:40]),
                  f"{harness}: the model-check guard comes first")
            check("`You are the worker for task <id>.` " in do
                  and "work.md and follow it" not in do,
                  f"{harness}: the spawn prompt does not send it to work.md")
            check(len(body.split()) > 900, f"{harness}: the longer body")
        m = re.search(r"(?s)1\. Read (.*?)\n2\. ", work)
        step1 = " ".join(m.group(1).split())
        check(".ai/notes.md`, `.ai/tasks/<id>/task.md` whole and "
              "`.ai/agent/task/steps.md` together" in step1
              and "in one turn" in step1,
              f"{harness}: step 1 reads the three files in one turn")
        check("read `.ai/agent/task/work.md` and `steps.md` again first"
              in step1, f"{harness}: a continued worker re-reads the file")
        if harness != "copilot":  # no turn limit there (section 78)
            check("maxTurns: 200" in head or "steps: 200" in head,
                  f"{harness}: turn limit kept")
        if harness == "claude":
            check("disallowedTools: Agent" in head, "claude: Agent denied")

        # A model line survives a forced re-init, once, with the long body.
        (root / rel).write_text(models.with_model(agent, "some-model"),
                                encoding="utf-8")
        init(root, harness)
        again = (root / rel).read_text(encoding="utf-8")
        head2, body2 = split(again)
        check(re.findall(r"(?m)^model:.*$", head2) == ["model: some-model"],
              f"{harness}: one model line after re-init: {head2!r}")
        check(body2 == body, f"{harness}: the body is regenerated unchanged")
        check(models.current(root / rel) == "some-model",
              f"{harness}: models.current reads it")
        check(models.with_model(again, "other").count("model:") == 1,
              f"{harness}: replacing the model keeps one line")
    if FAILS:
        for f in FAILS:
            print(f"FAIL {f}")
        return 1
    print(f"ok: worker contract, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
