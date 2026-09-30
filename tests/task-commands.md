# Task commands: regression runbook

How to check that `/task` (`create`, `do`, `list`, and the create-or-do
resolver) still
behave as CONCEPT.md Part I (Pillar 2) says. Run it after any change to
`templates/skills/task.md`, `templates/tools/tasks.py`, the task file
format, or the review gate, and before merging a branch that touches them.

Two parts:

- **Part A, deterministic** (every change, 1 s): `python3
  tests/test_tasks_table.py`. Covers everything `tasks.py` promises without an
  agent. It is also in TESTING.md Layer 1.
- **Part B, agent behavior** (behavior changes, about 30 min): the test cases
  below, run live on a real repository. Each case names the prompt, the
  expected behavior, and a command that decides it. Judge from the files,
  the `.ai` git log and the session transcript, never from the agent's own
  summary: on 2026-09-29 an agent reported a task done whose file had 0 of 4
  criteria ticked.

This is a regression check for rules, not a benchmark: it says whether the
agent follows the skill text, not whether the framework makes it faster.

## Part B setup

Pinned target: satty, the GTK4 screenshot annotator, at `f578432`. It has
real open issues for every task type, and a README and `config.toml` that
allow docs-only changes that can finish without a toolchain.

```bash
mkdir -p ~/tmp && cd ~/tmp && rm -rf satty
git clone -q https://github.com/gabm/Satty satty && cd satty
git checkout -q f578432
python3 <framework-checkout>/init_agent.py --harness claude -y --name satty
```

- **Toolchain:** leave Rust and GTK uninstalled. The missing `cargo` is part
  of the test: it drives the `blocked` path (TC-D3). Record in the result
  whether `cargo` was on PATH; with it, TC-D3 does not apply and TC-D1 to
  TC-D4 should end `done` instead.
- **Model:** record it. Reference runs used sonnet-5.5 at medium effort.
- **Fresh session per `/task do`:** `/clear` before each one, as the skill
  requires. The task file is the handoff, not the conversation.
- **Answering Q&A:** pick the option the agent marks as recommended, unless
  the case says otherwise. Note every question it asked.
- **Other harnesses:** the same cases apply to copilot and hermes, with one
  difference: they have no `reviewer` sub-agent, so TC-D2 expects the
  documented fallback (a fresh general-purpose sub-agent, or a clean-context
  self-review that says the `reviewer` was unavailable).

Driving the agent from another agent with herdr is optional; see the appendix.

### Evidence commands

Run these from the satty root after each case.

```bash
T=<task-id>
python3 .ai/agent/tools/tasks.py                     # table, flags, footer
sed -n '1,/^## Goal/p' .ai/tasks/$T/task.md          # frontmatter
grep -n -i review .ai/tasks/$T/task.md               # review line (8.5)
git -C .ai log --oneline | head -5                   # commit sequence
ls .ai/.current 2>/dev/null && cat .ai/.current      # resume pointer
git diff --stat                                      # host repo changes
```

Tool calls and sub-agents of the last session (Claude Code):

```bash
f=$(ls -t ~/.claude/projects/-Users-$USER-tmp-satty/*.jsonl | head -1)
grep -o '"subagent_type":"[^"]*"' "$f" | sort | uniq -c
python3 - "$f" <<'EOF'
import json, sys
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    m = d.get("message", {})
    if d.get("type") != "assistant" or not isinstance(m.get("content"), list):
        continue
    for c in m["content"]:
        if c.get("type") == "tool_use":
            i = c["input"]
            arg = (i.get("subagent_type") or i.get("command")
                   or i.get("file_path") or "")
            print(c["name"], arg[:100].replace("\n", " "))
EOF
```

## Test cases

### /task create

**TC-R1: the script decides create or do** (9.0)

Run `/task <id>` without a subcommand three times: for a new id with a
title, for an existing unfinished task, and for an id close to an existing
one (e.g. `login-timeout-fix` next to `fix-login-timeout`).

Pass when the transcript shows `tasks.py resolve <id>` before anything else,
the new id is created, the existing task is worked (not planned again), and
the close id is asked about instead of created. Fail: the agent searches
with grep or ls to decide, or creates a second task for the same thing.


**TC-C1: type is asked, never inferred** (8.3)

Prompt: `/task create config-errors-no-abort Config errors should not abort
startup (issue #663): warn and fall back to defaults`

Pass when all hold:
- The first question asks for the type and offers `change`, `bug`,
  `investigation`, `test`. No type is picked before the answer.
- After answering `change`, the file has `type: change`.

Fail: the file has a type the user never gave, or the type question comes
after other questions.

**TC-C2: type given, per-type plan** (8.0, 8.3)

Create one task per remaining type, naming the type in the prompt:

```
/task create text-undo-redo Undo/redo for text does not work as expected (issue #674). Type: bug
/task create blur-scaling Why does the blur result depend on the display scaling (issue #602)? Type: investigation
/task create config-parse-tests Cover config.toml parsing in src/configuration.rs with tests: valid file, unknown keys, bad values. Type: test
```

Pass when, for each:
- No type question is asked.
- Frontmatter has `id`, `title`, `type`, `status: planned`, `created`,
  `updated`; sections Goal, Done when, Steps, Findings, Outcome, Notes.
- Done-when fits the type: `bug` has root cause with evidence and a
  reproduction that fails before and passes after; `investigation` has the
  answer with evidence or "inconclusive"; `test` has each scenario run with
  its result. Any task that would change code has the full test and lint
  criterion.
- Steps for `bug` and `investigation` are hypotheses with a check each.
- One `.ai` commit `task: create <id>` per task. No host repo change, no
  `.ai/.current`, work not started.

### /task do

Run each in a fresh session (`/clear`, then `/task do <id>`).

**TC-D1: investigation runs in one go** (8.5, 8.6, 9.0)

Prompt: `/task input-scale-window Why does --input-scale have the inverse
effect on the window size (issue #689)? Type: investigation`

Pass when all hold:
- No question after the type (here none at all, the type is given); open
  points are numbered assumptions in Notes.
- The same session goes from create straight into do: the `.ai` log shows
  `task: create <id>` and then `task: done <id>` with no user turn between.
- `status: done`, and the table shows Steps and Done when fully ticked
  (n/n), with no flag for it.
- `.ai/.current` was written at the start of do and is gone at the end.
- Findings are dated and each cites evidence. Open each file-and-line
  citation: every one says what the claim says.
- `git diff --stat` shows no host repo change.
- A `Review:` line in Findings names the review; inline only with an
  Outcome under ~30 lines.

**TC-D2: diff over ~30 lines goes to a fresh context** (8.6)

Create with the cargo criteria waived, so the task can reach the review
gate without a toolchain:

`/task create readme-keybindings Add a reference table of every default
keyboard shortcut to README.md, taken from src/keybindings.rs and the tool
code, one row per shortcut. Docs only, hand-written README prose, no Rust
source change. There is no Rust toolchain here; I waive all cargo-based
criteria for this task. Type: change`

Pass when all hold:
- The diff is over 30 lines (`git diff --numstat README.md`).
- The transcript shows `"subagent_type":"reviewer"`.
- The Findings line says the `reviewer` sub-agent ran, and what it found.
- `status: done` with every criterion ticked; the waived criterion is
  marked waived, not silently dropped.

Fail: an inline review on a diff over ~30 lines, or no review line.

**TC-D3: cannot finish, blocks with a reason** (8.4, 8.5)

Task: `config-errors-no-abort`, with no Rust toolchain. If the agent asks
whether to install one, answer neutrally and do not say "blocked":
`Do not install anything on this machine, and I will not run the checks
right now. Continue according to the task rules.`

Pass when all hold:
- `status: blocked` and a frontmatter line `blocked: <reason>`.
- Not `done`, and no done-when box claims the test run.
- The table shows the task with ⛔, the flag `❗ <id>: blocked: <reason>`,
  and the 👉 pointer on it; `.ai/.current` still exists.
- Findings record what was done and what is missing.

Note: the review gate runs only before `done`, so a task that blocks at the
test step may have no review line. That is correct.

**TC-D4: small diff, inline review** (8.6)

`/task create readme-troubleshooting Add a Troubleshooting section to
README.md covering --input-scale and HiDPI window size, blur looking
different at different zoom levels, and what happens on a broken config
file. Docs only, hand-written README prose, no Rust source change. There is
no Rust toolchain here; I waive all cargo-based criteria for this task.
Type: change`

Pass when the diff is under ~30 lines, the Findings line names an inline
review with its size, and the task ends `done` with every criterion ticked.
If the diff comes out over 30 lines, the case turns into TC-D2 and must pass
as that.

### /task list

**TC-L1: the table is the reply** (8.4, 8.7, 8.9)

Run `/task list` in a fresh session, twice.

Pass when, both times:
- The reply contains the complete table, the legend line under it, the
  flags and the footer, copied from `tasks.py` without additions or a
  summary. "The output is above" or a count alone is a fail.
- Type and Status columns show emoji only; the legend explains them.
- The transcript shows exactly one tool call, the `tasks.py` run, and no
  file reads.
- `git -C .ai status --short` is empty afterwards (read-only).

### Acceptance: one task per type (9.0)

The goal set for 9.0: a Claude and a Copilot session each pass one task of
every type on satty. All four finish without a Rust toolchain; the cargo
criteria of the three that touch files are waived in the prompt.

| Type | Task | Invocation |
|---|---|---|
| investigation | `input-scale-window` (issue #689), as TC-D1 | `/task <id> ... Type: investigation` |
| bug | `nextrelease-typo`: `release.nu:106` replaces `NEXTRELEASE` with the version, but README line 139 says `NEXTRELASE` for pixelate, so a release keeps the placeholder | `/task create`, then `/task <id>` in a fresh session |
| change | `readme-troubleshooting`, as TC-D4 | `/task create`, then `/task do <id>` in a fresh session |
| test | `keybinds-consistency`: every action under `[keybinds]` in `config.toml` exists in `src/keybindings.rs` and in the README | `/task create`, then `/task <id>` in a fresh session |

Prompts (Copilot CLI: wrap each as `Run task ...: read
.github/prompts/task.prompt.md and follow it.`):

```
/task input-scale-window Why does --input-scale have the inverse effect on the window size (issue #689)? Type: investigation
/task create nextrelease-typo The release script leaves a NEXTRELEASE placeholder in the README for pixelate. Docs and release text only, no Rust source change; no Rust toolchain here, I waive all cargo-based criteria. Type: bug
/task create readme-troubleshooting Add a Troubleshooting section to README.md covering --input-scale and HiDPI window size, blur looking different at different zoom levels, and what happens on a broken config file. Docs only, no Rust source change; no Rust toolchain here, I waive all cargo-based criteria. Type: change
/task create keybinds-consistency Check that every action under [keybinds] in config.toml exists in src/keybindings.rs and is documented in README.md; record each mismatch as a finding, fix nothing. No Rust toolchain here, I waive all cargo-based criteria. Type: test
```

A type passes when:
- investigation: TC-D1.
- bug, change, test: create asks its Q&A (answer with the recommended
  option) and stops without working; the fresh session's `/task <id>` or
  `/task do <id>` resolves to `DO` and works it to `done`, all criteria
  ticked or waived as agreed, a `Review:` line, citations that hold. Bug:
  a reproduction that fails before the fix and passes after (for example
  the release `sed` on a copy of README, then a grep for `NEXTRELASE`).
  Test: one result per scenario with evidence, mismatches recorded as
  findings, nothing fixed.
- `/task list` afterwards shows all four done, no flag for any of them.

## Recording a run

Keep one line per case, and the evidence for any FAIL.

```
Framework <version> (<commit>) | harness <h> | model <m> | cargo <yes/no> | <date>
TC-C1 PASS|FAIL <note>
TC-C2 ...
TC-D1 ...
TC-D2 ...
TC-D3 ...
TC-D4 ...
TC-L1 ...
```

A FAIL that comes from the skill text gets a fix in the template, a
CONCEPT.md version entry citing the case, and a rerun of that case before
the commit, as 8.5 to 8.7 were made.

## Known observations (reference run 2026-09-29, 8.4 to 8.9, sonnet-5.5)

Not failures of a rule, but worth watching:

- Findings tend to be written in one go at the end, not as they happen.
  Left unenforced on purpose: for a short task nothing is lost.
- Looking for a missing `cargo`, the agent once ran `find /` over the whole
  filesystem.
- The auto-mode classifier of Claude Code can drop out mid-run and deny
  every write. The correct behavior, seen once: stop, list what is still
  open, finish on retry. A run hit by it is not a test result; rerun it.
- `.ai/.current` is shared: `/task do` on a second task overwrites the
  pointer of a blocked first one. The agent reported it; the table then
  points at the newer task.

## Appendix: driving the agent with herdr

Useful when one agent runs the cases on another. Load the herdr skill
(`herdr --skill`) first. Learned the hard way:

- Always `herdr agent prompt <name> "<text>" --wait`. Without `--wait` the
  prompt was not submitted. `/clear` and `/model` return
  `agent_prompt_stalled`, which is expected: they start no turn.
- Key names are lowercase: `herdr agent send-keys <name> enter`.
- A question UI makes the agent `blocked`. Read it before answering
  (`herdr agent read <name>`). Multi-select questions need `enter` to tick
  and the arrow keys to reach "Next"; `enter` alone toggles.
- Never press `enter` on a folder-trust or permission prompt without reading
  which option is selected.
- `/model` inside a session also saves the model as the global default in
  `~/.claude/settings.json`; restore it afterwards.
- Wait for completion with `herdr agent wait <name> --until idle` (one state
  per call), then check the files, not the screen.
