# Task commands: regression runbook

How to check that `/task` (`create`, `do`, `list`, and the create-or-do
resolver) still
behave as CONCEPT.md Part I (Pillar 2) says. Run it after any change to
`templates/skills/task.md`, `templates/task/*.md`,
`templates/tools/tasks.py`, the task file
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

On OpenCode (`--harness opencode`) the same cases apply, typed as the same
slash commands: `reviewer` and the worker show as sub-agents in the TUI,
`opencode session export <id>` is the transcript (the sub-agent's own
session records the model it ran on as `info.model`), and `Delegation:`
names the model from the worker's agent file. CONCEPT.md section 55 records
the first run.

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
- **Sessions:** `/task do` needs no fresh session since 12.5: the session
  that ran `/task create` supervises and the worker starts fresh. `/clear`
  between test cases only to keep one case's conversation out of the next;
  a case that tests the create-then-do flow says so and does not clear.
- **Answering Q&A:** pick the option the agent marks as recommended, unless
  the case says otherwise. Note every question it asked.
- **Copilot:** the same cases apply. Its `reviewer` and `worker` are custom
  agents in `.github/agents/`; with no model set `/task do` refuses there as
  everywhere (TC-M1).

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


**TC-C1: type is asked, never inferred** (8.3, 9.1, amended 10.6)

Prompt: `/task create config-errors-no-abort Config errors should not abort
startup: warn and fall back to defaults`

Pass when all hold:
- The first message asks for the type and offers `change`, `bug`,
  `investigation`, `test`, together with the tracker question (10.6)
  and the done-when questions in the same message. No type is picked
  before the answer.
- After answering `change`, the file has `type: change`.

Fail: the file has a type the user never gave, the type question comes
after other questions, or the type is asked alone and the tracker or
done-when questions follow in a second round trip.

**TC-C1b: Create and Do are read from their part files** (9.1)

Any create or do run, on each harness. From the transcript:
- After `tasks.py resolve`, the agent reads `.ai/agent/task/create.md`
  (CREATE) or `.ai/agent/task/do.md` (DO) before acting.
- `/task list` reads neither part file.

Fail: the agent acts on a verdict without reading its part file, or
improvises the steps.

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
  its result. Any task that would change code has the covering tests and lint
  criterion, and no full-suite criterion or step (12.13).
- Steps for `bug` and `investigation` are hypotheses with a check each.
- One `.ai` commit `task: create <id>` per task. No host repo change, no
  `.ai/.current`, work not started. Exception: `investigation` continues into Do
  after its `task: create` commit (9.0); judge its create half from that
  commit, its Do half by TC-D1.

**TC-C3: an existing issue feeds the plan** (10.6)

Prompt: `/task create text-undo-redo Undo/redo for text does not work as
expected (issue #674). Type: bug` (satty has real open issue #674 and,
with `gh` available, `tasks.py trackers` detects it; without `gh`, paste
the issue URL when asked and let the agent fetch it).

Pass when all hold:
- No tracker question is asked: the prompt names the issue.
- The transcript shows the issue fetched (`gh issue view 674` or the
  pasted URL), not just the number copied.
- The Goal, Done-when or Steps carry something only the issue says
  (its symptom or reproduction), alongside the user's own words.
- The task id is `674-text-undo-redo`: the key prefixes the id the
  user gave; the title carries the prefix too; the commit message
  names the new id.
- `## Tracker` names `issue: #674` with the URL, the state, and a
  digest of the body.

Fail: the issue is never fetched, its content feeds nothing, the key
prefix is missing, or the tracker question is asked anyway in a second
message.

**TC-C4: no issue, offered once** (10.6)

Prompt: `/task create readme-typos-scan Sweep README.md for spelling
mistakes and fix them. Type: change`, then answer the tracker question
with `no issue`, and decline the offer to file one.

Pass when all hold:
- The tracker question came in the first message, with the type given
  and no second round trip for it.
- The offer to file an issue is made exactly once; after the decline
  it is not repeated.
- `## Tracker` says `none` and why.
- The task id stays `readme-typos-scan`, no prefix.

Fail: the offer comes twice, an issue is filed anyway, or the section
is missing.

### /task do

Run each case apart from the one before (`/clear`, then `/task do <id>`),
for test isolation, not because the skill asks for it (TC-D10 runs create
and do in one session).

In every do case (10.1): the transcript shows `tasks.py start <id>` at the
start and `tasks.py finish <id> done|blocked` at the end, every ticked box
ticked by `tasks.py tick <id> done|steps <n>...` naming its numbers (11.0;
a script or `replace("- [ ] ", "- [x] ")` that ticks every box at once is a
fail), no shell write to
`.ai/.current` or to a task's frontmatter (`printf >`, `sed -i`, `rm`, a
heredoc), and every `.ai` commit as `git -C .ai`, never an absolute path. A
headless run with the scaffold allowlist ends with `.ai` committed.

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
- With a worker (11.1, 11.3): its report says `question` (a missing
  toolchain is outside its reach, not `stuck`). Between that report and the user's
  answer the supervisor runs no host-code edit (no `Edit`/`Write` outside
  `.ai`, no `sed -i` or script on `src/`).

Note: the review gate runs before code ships and before `done`, so a task
that blocks at the test step may have no review line. That is correct.

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

**TC-D5: mechanical diff over ~30 lines, inline review** (9.1)

`/task create readme-bullet-style Reformat README.md: change every list
bullet from "- " to "* " outside the generated --help and config.toml
blocks, nothing else. Pure reformat, no wording change. Docs only, no Rust
toolchain here; I waive all cargo-based criteria. Type: change`

Pass when the diff is over 30 lines and changes only bullet markers, the
Findings line reads `Review: inline (mechanical: ...)` naming why, no
sub-agent runs, no suite runs, and the task ends `done` with every
criterion ticked. Fail: a fresh-context review of a purely mechanical
diff, or an inline review whose line does not say it is mechanical.

**TC-D6: the worker ships, the supervisor reviews** (11.0, 11.3, 12.1)

On a session model above the cheapest tier (claude: Opus or Fable). A
`change` with three or more code steps, then a step "commit on branch
`<branch>`, push, open the pull request" (a scratch repo with a bare
local `origin` stands in for the pull request with a pushed branch).
`/task do <id>`.

Pass when all hold:
- One fresh `worker` sub-agent (not a fork) runs on a cheaper model than
  the session's: the model its agent file pins, with no model passed at
  spawn, or else one picked at spawn (claude: `"model":"haiku"` or
  `"sonnet"`), its whole prompt naming the task and
  `.ai/agent/task/work.md`. No `delegate.py` and no `herdr` call.
- The worker reports `review` before any host commit: the `.ai` log has
  `worker round 1` before the host branch has a commit. The supervisor's
  review leaves a `Review:` line and a `Supervisor check: round 1
  accepted` line; a finding instead leaves a `Supervisor round 1`
  correction that the worker fixes.
- The worker then commits, pushes and records the evidence. Where the
  harness can resume a sub-agent, the transcript shows the supervisor
  continuing the same worker (claude: `SendMessage` to its id), not a
  second spawn.
- The supervisor made no host edit, commit or push (no `Edit`/`Write`
  outside `.ai`, no `git commit` or `git push` in the host repo) and
  changed no file while the worker ran.
- The supervisor ran no test, lint or build (12.1): it read the worker's
  recorded commands and results, and a missing or doubtful one went back
  to the worker as a `Supervisor round` correction.
- No full-suite run (12.13): every round records the tests covering the
  change and lint on the changed files, the last on the final code, and
  the transcript holds no run of the project's whole test command,
  unless every test it runs covers the change (a one-file suite).
- The `reviewer` ran no test, lint or build (12.1): its transcript holds
  only reads (`git diff`, `git show`, `grep`, file reads), and a missing
  result shows up as a finding, not as a run.
- The worker ticked steps only: no done-when box, no Outcome, no
  `notes.md` change in its round commits (`git -C .ai show <commit>`).
- Findings end with a `Delegation: <model> ...` line; the supervisor
  ticked each criterion with `tasks.py tick`, wrote the Outcome, and
  `finish done` passed. Nothing merged into the default branch, and the
  host's default branch got no commit (12.0): the worker committed on a
  feature branch (`git log <default>` unchanged).

**TC-D7: inline when asked** (11.0, 11.2)

`/task do <id> inline` on a task with three or more open steps.

Pass when the supervisor says in one line that it works inline, no
sub-agent runs before the review gate, no `Worker round` or `Delegation:`
line is written, and the task still ends with a `Review:` line.

**TC-D8: a small task is worked inline** (11.5)

`/task do <id>` on a task where at most one step edits a host file,
without `inline`.

Pass when the supervisor says in one line that it works inline and names
the count (`Inline: 1 of 2 steps edits a host file.`), no worker runs, the task ends `done` with a `Review: inline`
line, and no `Worker round` line is written.

**TC-D9: the smallest thing that meets the Goal** (12.4)

A delegated `change` with a pull request step. During the run: (a) let the
reviewer find something outside the criteria (a missing extra test, a
nicer structure); (b) when the worker asks a question with two options,
one larger; (c) after the criteria are met, ask for one more thing that
adds a second pull request; (d) let CI take longer than one blocking
command, or require a merge by the user.

Pass when all hold:
- (a) The finding is a `Not sent back` line, not a `Supervisor round`
  correction, and no `Supervisor check ... accepted` line carries fixes.
- (b) The worker's `question` lists both options with a cost each and
  recommends the smaller; the supervisor takes it or, if it asks you,
  recommends the smaller with both costs.
- (c) The supervisor first offers to ship and open a follow-up task, with
  the cost of each way; folded in only on your word, then a `User round`
  line and the new criterion in the task file.
- (d) The worker reports `waiting` with the command that shows the end;
  the supervisor ends its turn with one line on what the task waits for,
  and runs no CI polling, merge or deploy of its own.
- (e, 12.11) Redirect the design while a review of it runs: no new review
  of the old design starts, its findings are not carried over, a `Dropped:`
  line records it; and after the next report the continued worker re-reads
  `work.md` (visible in its transcript).
- Findings lines are short: `python3 .ai/agent/tools/tasks.py` flags no
  line over 300 characters for the task (12.7), long evidence sits in
  `.ai/tasks/<id>/evidence.md`, and there are no "no merge / no push"
  restatements.

**TC-D10: the session supervises; the worker is a sub-agent, or a Herdr tab when asked** (12.5, 12.6)

Inside Herdr, worker and reviewer models set, on each harness. In the
session that ran `/task create`: first `/task do <id>` on a task over the
small-task threshold, then on another such task `/task do <id> herdr`.

Pass for the plain call when the worker is the harness's sub-agent, no tab
opens, and no fresh-session advice appears. Pass for `herdr` when all hold:

Pass when all hold:
- No advice to start a fresh session, before or after.
- A new tab `worker-<id>` opens; its status line shows the worker's model
  from `worker.md`, it receives the fixed prompt, and no existing tab gets
  input. The supervisor spawns no worker sub-agent (no `Agent` call with
  `subagent_type: worker`).
- Each report is a `Worker round` line in the task file; the supervisor
  continues the same tab (`herdr agent prompt worker-<id>`), never a second
  tab or session for the same task. The reviewer is still a sub-agent.
- The tab is open after `finish`.
- The tab starts the harness's CLI on the worker's model: `claude --agent
  worker`, or `copilot --agent worker --model <m>`, `<m>` the `model:`
  line of the worker file. On OpenCode the tab starts plain `opencode`
  (its TUI has no model flag) and is told to spawn the `worker` sub-agent;
  that sub-agent's exported session shows the worker file's model (12.8).
- What the user said after `/task create` reaches the worker: before
  `/task do`, tell the session one thing the work depends on that the task
  file does not hold. It is in the task's Notes before the worker starts
  (12.8).
- `herdr` outside Herdr (no `HERDR_ENV`): one line saying so, then the
  sub-agent, everything else the same.

**TC-D11: tests are for logic** (12.10)

A delegated `change` that edits a declarative file and a small piece of
logic together (for example: add a service to a snap manifest or a job to
a CI workflow, plus a helper function that computes one of its values).

Pass when all hold:
- No new test loads the declarative file and compares its values to
  literals; the file's check is its linter or validator on that file,
  recorded as such in Findings, and no build, CI run or start on the
  target ran for it (12.13).
- The helper function has a test whose expected value comes from the
  requirement, not from the function.
- The reviewer, shown a planted change-detector test in a second run,
  reports it as a finding with the check that fits instead, and the
  supervisor sends it back as a `Supervisor round` correction, not a `Not
  sent back` line.
- A policy test across files (a rule, not a value), if present, is kept.

### Sub-agent models (11.9)

Every `/task do` case above needs both models set first (`init-agent
--models --worker <m> --reviewer <m>` in the scratch repo).

**TC-M1: no model, no work**

On a fresh scaffold with no `model:` line, `/task do <id>` on any task.

Pass when the agent runs `tasks.py models`, prints which file needs which
line, and stops: `tasks.py resolve`'s task is still `planned`, no `.ai/.current`
exists, no file changed, and it picked no model itself. Repeat with `model:
inherit` in the worker file: the same refusal.

**TC-M2: set, test, work**

`init-agent --models --worker <cheap> --reviewer <strong>` (claude: run it
with `!` from the session), then restart the session and `/task do` on a task
over ~30 lines.

Pass when the setup tool reports each role OK, a model that does not exist
is reported FAILED and leaves its file unchanged, and `/task do` spawns
`worker` and `reviewer` with no model passed at spawn (the `Agent` call has no
`model`); the `Delegation:` line names the model from the worker's file.

On OpenCode (section 60) the same, with names as `opencode models` prints
them (`init-agent --models --worker claude-agent/haiku --reviewer
claude-agent/sonnet#medium`), each reported `OK` with "sub-agent ran on" the
same name. The model check: `opencode session export <child>` of the worker
and the reviewer show that provider, id and variant.

### /framework-update hand-off (12.2)

A scratch scaffold staged one version back (render it from the previous
version's commit, or edit its stamp down), with notes, a task, a hand-filled
GENERATED section and the worker and reviewer models set.

**TC-U1: no updater model, inline**

`/framework-update` with no `model:` line in the updater file.

Pass when the session runs `tasks.py models`, says in one line that the
update runs inline because no updater model is set, spawns nothing, opens no
tab, and does the update itself (the stamp moves, one `update:` commit).

**TC-U2: handed to the updater**

`init-agent --models --updater <small>` (claude: `haiku`), restart, then
`/framework-update`, and again with `/framework-update herdr` inside
Herdr.

Pass when the plain call spawns an `updater` sub-agent and opens no tab,
and when, with `herdr`, a new tab `update-<hhmmss>` appears, its
status line shows the updater's model, it receives `/framework-update
inline`, and no existing tab got any input. The sub-agent gets no model
passed. The updater ends with `UPDATE
DONE: <old> -> <new>`; the session then reports one line per check (stamp,
files, retired files, `.ai` commit, `model:` lines, GENERATED section) from
the files, and changed no file itself. The tab is still open. With
`dry-run`: `UPDATE DRY-RUN`, nothing changed, the stamp unchanged.

### Parallel (11.1)

**TC-P1: two tasks planned and worked side by side**

Two supervisor sessions in the same project (two Herdr panes when one
agent drives the run), each on a model above the cheapest tier. Send
both Create prompts at once (TC-D2's
`readme-keybindings` and TC-C1's `config-errors-no-abort`), answer both,
then `/clear` both and send both `/task do` at once.

Pass when all hold:
- Every `.ai` commit holds only its own task's paths (plus `notes.md`
  when that session changed it): `git -C .ai log --name-only`. No
  transcript shows `git -C .ai add -A`.
- The second `start` printed `parallel` and `PARALLEL <other> is running`,
  and wrote `.ai/.current-<id>`; `.ai/.current` still names the first.
- Both worker sub-agents ran at the same time, and every host file a task
  edited is in its pointer's `modified:` list, claimed before the edit.
  If either side tried a file the other claimed, the transcript shows the
  `CLAIMED ... by running task` refusal and the file was left alone.
- Each review judges its own claimed files; Findings name the other
  task's files as the parallel task's, not as scope creep.
- At the end a `done` task's pointer is gone and a `blocked` one's kept;
  `/task list` marks the running one.

Fail: one task's file in the other's commit, a replaced pointer while its
task was in progress, an edit to a file the other task claimed.

### Direct path (9.1)

No `/task`: the plain prompt, as a user would type it.

**TC-E1: a trivial change ends in one turn**

Prompt: `README.md line 139: the pixelate tag says NEXTRELASE, a typo for
NEXTRELEASE, so release.nu never replaces it. Fix it.`

Pass when all hold:
- One user turn: no message that only reports status and waits.
- The diff is the one-word fix; no suite runs (docs only).
- `.ai` is untouched: no note, no commit (`git -C .ai log` unchanged).
- The final message ends with the headings Blocked on me, Changed, Found.

**TC-E2: an answered question stays settled**

Turn 1: `What does the --input-scale option do? Answer in two or three
sentences, no changes.` Turn 2, same session: `Add one sentence about it
to README.md where --input-scale is documented.`

Pass when turn 2 reopens none of the source files turn 1 cited and the
sentence states turn 1's answer; reading the README to place it is
expected. Fail: turn 2 re-investigates the option in the source.

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

**TC-L2: the tree is the reply** (10.2)

Seed the target with three tasks in a chain (`tree-root` blocks
`tree-mid` via `depends: tree-root`, `tree-mid` blocks `tree-leaf`),
one independent task, one task whose `depends:` names no live task, and
`.ai/.current` pointing at `tree-mid`. Run `/task tree` in a fresh
session.

Pass when:
- The reply is the complete tree output, verbatim: the project name on
  the first line, `tree-root` on the first level under it, `├──`/`└──`
  nesting below, the status emoji per line, `👉` before `tree-mid`,
  the independent task on the first level after `tree-root` (no
  trailing `independent:` line), the unknown-id warning, legend and footer,
  with nothing added or summarized.
- Each seeded task appears exactly once.
- The transcript shows exactly one tool call, the `tasks.py tree` run,
  and no file reads.
- `git -C .ai status --short` is empty afterwards (read-only).

Fail: the agent prints the table instead, opens task files, or appends
its own summary.

### Acceptance: one task per type (9.0)

The goal set for 9.0: a Claude and a Copilot session each pass one task of
every type on satty. All four finish without a Rust toolchain; the cargo
criteria of the three that touch files are waived in the prompt.

| Type | Task | Invocation |
|---|---|---|
| investigation | `input-scale-window` (issue #689), as TC-D1 | `/task <id> ... Type: investigation` |
| bug | `nextrelease-typo`: `release.nu:106` replaces `NEXTRELEASE` with the version, but README line 139 says `NEXTRELASE` for pixelate, so a release keeps the placeholder | `/task create`, then `/task <id>` in a fresh session |
| change | `readme-troubleshooting`, as TC-D4 | `/task create`, then `/task do <id>` in the same session |
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
TC-C3 ...
TC-C4 ...
TC-D1 ...
TC-D2 ...
TC-D3 ...
TC-D4 ...
TC-D5 ...
TC-E1 ...
TC-E2 ...
TC-L1 ...
TC-L2 ...
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

Seen in the 9.0 acceptance run (2026-09-30):

- Claude Code may open "Teach auto mode about your environment?", which
  offers to scan shell history and other repositories. It is not a task
  question: answer it with Esc, never with the recommended option, and
  rerun the prompt it swallowed.
- An agent driven from outside must not confirm a folder-trust prompt
  blindly; move the cursor to the option explicitly and read it back first.

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
- To give a free-text answer to a question form, do not press `enter` on its
  "Type something" option: that closes the form with no answer, and text
  sent afterwards lands in the main input box instead. Either select the
  option and type the text before any `enter`, or let the form close and
  submit the answer as an ordinary message (`herdr pane send-text`, then
  `enter`); the agent reads it either way. Record which in the result.
- `herdr agent wait` right after a form was answered can return the stale
  `blocked` state at once; wait again before reading the screen.
- `/model` inside a session also saves the model as the global default in
  `~/.claude/settings.json`; restore it afterwards.
- Wait for completion with `herdr agent wait <name> --until idle` (one state
  per call), then check the files, not the screen.
