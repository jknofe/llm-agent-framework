# Project-Aware LLM Agent Framework: Concept

**State: 2026-11-26, v14.3.** The framework rests on four premises, stated in
Part I. Two are claims about what it does for a project; two are properties of
the artifact. Everything the generator emits serves one of them or is a
candidate for removal.

**How to read this file.**

- **Part I** is the framework as it stands. It is normative: when a template
  and Part I disagree, Part I is right and the template is a bug.
- **Part II** is what has been measured, one line per round, with what each
  round decided. It is why Part I says what it says.
- **Part III** is the revision history, sections 1 to 56, unchanged and
  numbered as they always were, because other documents cite those numbers.
  Many of them describe a framework that no longer exists; the ones that were
  explicitly retired are listed at the top of Part III. History is kept
  because it carries the evidence, not because it is still in force.

---

# Part I: The framework (normative)

## The four premises

**Pillar 1. Durable project knowledge that the repository cannot state
itself.** `.ai/notes.md` as private memory across sessions, plus a short
requirements block in `AGENTS.md` holding the commands the project is checked
with and the tools it requires or forbids.

**Pillar 2. An opt-in plan-and-do path for any task, whose value is the plan
shown in advance.** `/task create` writes down what the agent intends before
any work is done, so a human can redirect it; `/task do` works the plan,
records findings as they happen, and reviews the result against the task's
done-when criteria. A task is a code change, a bug, an investigation or a
test; what counts as done depends on which. The user starts it. By default
the agent just does the task.

**Property 3. One command set on three harnesses.** Three commands, identical
names and bodies on Claude Code, Copilot and OpenCode. No command's name depends
on where it is typed.

**Property 4. Economical about its own text, not about the session.** The
always-loaded footprint is capped and everything else is read on demand. The
framework does not make a session cheaper; every round measured more tokens,
by design.

The two pillars are claims that could be wrong and have been tested. The two
properties are facts about the generator's output and need no test.

## Pillar 1: knowledge the repository cannot state

### The test
Before writing anything into `.ai/`, ask: **can the repository state this
itself?** If yes, it does not belong there. This single test is what keeps the
retired digest (Part III section 6) from returning under a new name.

Qualifies: decisions and the reason behind them, gotchas, unwritten rules,
ownership, release and migration order, domain terms an outsider would read
wrong, runbooks, pointers to sibling repos.

Does not qualify: a summary of code the agent just read, a module map, a
glossary of names that are already identifiers, a restatement of the README.
An overview does not help an agent find anything (Part II, ETH round), and
writing one costs on every session that loads it.

### Where it lives
- `.ai/notes.md`, the hub. Appended, telegraphic. Read at the start of a
  session: by the agent on Copilot; put into the context on Claude Code by a
  SessionStart hook (section 83), so it is also there after a compaction,
  capped at 100 lines and 8,000 bytes, and on OpenCode by the `instructions`
  key of its config (section 86), whole and uncapped.
- `.ai/notes/<topic>.md`, optional leaves, each linked from the hub with a
  one-line pointer. Split only once the hub passes one to two screens. A
  leaf about one directory or file pattern may start with a `paths:`
  frontmatter of quoted globs; Claude Code then loads it when a matching
  file is read or edited, through a gitignored symlink under
  `.claude/rules/` that `tasks.py notes --link` keeps (section 89). The
  hub never carries one; the other harnesses read the leaf on demand.
- The `GENERATED:project-context` block in `AGENTS.md`, cap ~300 tokens: the
  always-loaded slice. Build, test and lint commands verbatim; tools required
  or forbidden; the user's rules; one-line pointers to docs the repo already
  has. No purpose paragraph, no module map, no glossary.

`.ai/` is its own nested git repository, gitignored from the host, committed
after every change. It stays private: no remote, no team sharing.

### How it gets there
`/explore` asks the user what the code cannot tell it and records the answers.
The questions are the mechanism, not the probe: developer-written content is
the only arm that measured positive. `probe.py` runs first and prints detected
build/test/lint commands and the documentation the repo already has, as a
starting point for the questions. The user's answers override detection.

On Claude Code the generated `.claude/settings.json` turns the harness's own
auto memory off for the project, so `.ai/notes.md` is the only memory
(section 80).

Notes go stale and nothing else checks them, so `tasks.py notes` does, by
script and never by the agent (section 82): the hub over a size cap, a
cited repository path that no longer exists, a dead leaf link, an unlinked
leaf. The flags close the `/task list` output; nothing is added to any
always-loaded file.

Between explores, notes grow on correction: when the user corrects the agent,
or a check fails for a reason the code does not explain, the agent records it
before moving on. A correction is the cheapest signal that something was not
derivable from the repository, and a gotcha noted at the moment it bit is the
only kind that is still accurate. Without this rule the notes hold only what
`/explore` asked about.

## Pillar 2: the opt-in plan-and-do path

One command, `/task`, with `create`, `do` and `list`. Whether a task exists
is decided by a script, not by the agent looking around: `tasks.py resolve
<id>` prints one verdict (`CREATE`, `DO`, `DONE`, `ARCHIVED`, `INVALID`,
`NONE`; after `DO` the task file follows whole, between two `-----` lines,
section 91), matches ids case-insensitively, and names close existing ids as
`SIMILAR` so a second task for the same thing is asked about before it is
made. `/task <id> [title]` without a subcommand goes wherever the verdict
says.

`/task create <id> <title>` writes `.ai/tasks/<id>/task.md`: type, goal,
done-when criteria, steps, empty Findings and Outcome sections, and a
Tracker section. Its first question, asked in the same message as the
type, is whether a tracker issue exists for the task (a GitHub issue, a
Jira key); which tracker access the checkout has is again a script's
answer (`tasks.py trackers` reads `.ai/trackers.conf` and detects the
`gh` and `jira` CLIs), not the agent's guess. The fetched issue feeds the
plan on equal footing with the user's input, the issue key becomes the
task id's prefix (`12345-fix-ci-crash`), and the section holds the key,
URL and a digest of what fed the plan, so `do` never queries the tracker
again. With no issue, the user is asked once whether to file one and may
decline; an issueless task is normal. The type
comes from the user: when they did not name it, the first question asks for
it; the agent never infers it. For a `change`, `bug` or `test` it runs a
bounded Q&A and stops, and in the same dialog settles what would otherwise
stop the work later: what proves each criterion and what happens when that
cannot be produced here, where it is proven, the scope, and the outward
actions (push, pull request, comment, CI rerun) the work may take without
asking; it runs each command a criterion names once while planning. The
answers go into the task's `## Autonomy` section (section 98). The point is
the plan a human reads before the work
starts, and `/task do` then works it, in the same session or a later one:
the session supervises and the worker starts fresh (section 67). An
`investigation` asks
nothing after the type and runs straight on into `do` in the same session:
planning an investigation is most of doing it, and the user redirects from
the answer, which cites its evidence, rather than from a plan.

The type decides what done means:

| `type` | Done when |
|---|---|
| `change` | the user's criteria, plus the tests covering the change and lint on the changed files green |
| `bug` | root cause with evidence; a reproduction that fails before the fix and passes after; covering tests green. Or, cause only, a write-up another person can act on |
| `investigation` | the question in Goal answered, every claim citing its evidence, or an explicit "inconclusive" naming what was ruled out. Covers research |
| `test` | every named scenario run and its result recorded with evidence; new tests pass with the tests that cover the same code |

Any task that ends up changing code takes the covering-tests criterion,
whatever its type: every test that exercises the changed code, not only one
the task names, and lint on the changed files, green on the final code. The
full suite is not the framework's: CI on a push or the owner's run on the
target covers it (section 75). For bugs and investigations the steps are hypotheses,
each with how to confirm or rule it out, and the plan is expected to change.

`/task do <id>` works the steps, appends each finding to the task file as it
happens, and re-plans in the file when a result invalidates the plan: a
hypothesis ruled out is struck with its evidence, not silently abandoned. A
change to the Goal or a done-when criterion goes back to the user. It ends
with a review sized to the result (inline only when the diff and the
Outcome are each under ~30 lines, a fresh-context `reviewer` sub-agent
otherwise) that
checks a diff against the criteria and an Outcome against its evidence
(every file-and-line citation opened and confirmed), and
leaves one line in Findings naming the review that ran. It sets `done` only
with every done-when criterion ticked, then distills what the repository
cannot state into `.ai/notes.md`.

Since 11.0 `/task do` splits into two roles, after Google's
Elephant-Goldfish Model (section 50); since 11.3 the worker does the whole
job and the supervisor none of it (section 53). The worker is the
framework's `worker` agent, defined beside `reviewer` on every harness
(section 55), run as the harness's sub-agent, or in a Herdr tab of its
own when the user asks for `herdr`, on every harness (section 68): on the model its agent file names, which the user sets per
project (`init-agent --models`, section 59) and which `/task do` refuses to
work without, never a default and never the session's, and it knows
only `.ai/notes.md`, the task file and its contract (the body of its agent
file on Claude Code and OpenCode, `.ai/agent/task/work.md` on Copilot, section
85), which points it to the working steps in `.ai/agent/task/steps.md`
(section 77). It works
every step the task names: the code, the tests, then the branch, commit,
push, pull request, the wait for CI, a dev run, a tracker comment. Before
code ships it reports `review`; it also stops at `question`, `waiting`,
`stuck` and `done`, each a `Worker round <n>` line in Findings. The session that ran
`/task do` is the supervisor and stands in for the user: it reviews the
uncommitted diff before it ships (the review gate), answers a question as
the user would from the task file, decides a reversible choice the
Autonomy section and Notes leave open (a `Decision:` line, reported as made),
and asks the user only a changed Goal or criterion, an irreversible choice,
or an action the Autonomy section does not list (a merge into the default
branch, production, deleting data and a force-push never are). It asks each
question once (a `Pending:` line) and offers no extra work (section 98). It judges each report from the files and trusts recorded
evidence, a CI result or a command with its output, and runs no check
itself: missing or doubtful evidence goes back to the worker (section 63).
A worker's `done` is a
claim, not a gate result. Corrections and answers go into Findings as
`Supervisor round <n>` lines, an accepted review as a `Supervisor check`
line. A correction is only what keeps a criterion from being met; any
other finding stays a `Not sent back` line. Between options it takes, and
recommends to the user, the smallest that meets the Goal. A wait on CI
or a person (`waiting`) ends its turn instead of watching. A user ask
beyond the written criteria is offered as a follow-up task first, and
logged as a `User round` line when folded in (section 66); then the supervisor continues the same worker where the harness can
resume a sub-agent, or spawns a fresh one that reads the file. The
supervisor never edits host code, commits or pushes, not even to fix a
review finding; it takes over only when the user says so, and works the
steps itself only for `inline`, where no sub-agent can be spawned, or for
a small task: at most one open step changes a host file, or none does
(section 55). The
Outcome, the notes, the Done-when ticks and `finish` are its own. The
worker never ticks a done-when box, never writes Outcome, notes or the
review line, and never commits on or merges into the default branch. The roles are held by the harness where it can: section 79. Each sub-agent file
carries a turn limit against tool-call loops: worker 200, reviewer 50,
updater 100 (section 78).

`/task list` prints every live task with type, status and progress as
one table; archived tasks are counted, not listed, because archiving is how
a task leaves the working view. A script (`tasks.py`) produces the whole
answer from the task files' frontmatter, checkboxes and review line,
including the flags below the table: an `in-progress` task untouched for 14
days, a `blocked` task with the reason from its `blocked:` frontmatter line, a
`done` task with unchecked criteria or without a review line in Findings, and,
last, the notes flags of section 82. The
agent only shows the output; it opens no file. Outside any agent,
`python3 .ai/agent/tools/tasks.py` prints the same table with no model
involved.

The task's bookkeeping is the same script: `tasks.py start <id>` sets
`in-progress` and writes the resume pointer `.ai/.current`, `tasks.py tick
<id> done|steps <n>...` ticks the named criteria or steps, and `tasks.py
finish <id> done|blocked [reason]` closes it. `tick` has no "all": every
box is named on purpose (section 50). `finish done` refuses while a
criterion is unticked or the review line is missing, so the gate the
table flags afterwards is also enforced before. By default neither commits;
the agent commits `.ai` with the relative `git -C .ai` (section 44). One
call does all of it: `finish <id> done --tick-steps <n>... --tick <n>...
--commit [--add <path>...]` ticks the named steps and criteria, closes the
task and commits `.ai` with `tasks/<id>` and the named paths only; it is
all or nothing (section 90).

Rules that came from failures, not from theory:

- A code-changing task always includes a criterion that the tests
  covering the change, every one that exercises the changed code, and lint
  on the changed files pass, never only the test the task names. A
  criterion naming a single test is what produced the one correctness loss
  the framework has ever caused (Part II, sequence round): the fix passed
  the named test and failed the others on the same code. The full suite is
  not run by the framework at all. On one task with a 4-minute suite the
  worker ran it 34 times and the reviewer 10 times (section 63); 12.1 cut
  that to one run, and section 75 drops the last one, because in the
  owner's projects CI on the push or the owner's own run on the target
  already covers it. What that leaves uncaught inside the session, a break
  in code the change does not touch, CI catches before a merge. A review
  reads and runs nothing.
- Tests are for logic. A declarative file (configuration, manifest, build
  file, CI workflow) is checked by its linter or validator on that file,
  never by a test that compares its values to literals: such a
  change-detector test fails only on an intended edit. Agents wrote them in
  two projects (section 72). A build, a CI run, a plan or a start on the
  target is CI's or the owner's, like the full suite (section 75).
- `/task do` records a failing test as pre-existing only after it fails on
  a clean checkout and the test has been read. Later sessions act on notes;
  a wrong note is carried as faithfully as a right one.
- Neither command ever starts on its own. The default path is direct: read,
  do the task as the smallest complete change (reuse what the code, the
  standard library or an installed dependency has; no option, abstraction
  or dependency nobody asked for; every caller the change breaks fixed and
  the tests rule 2 asks for written),
  run the covering tests if code changed, note what is durable, commit
  `.ai` (section 97).

`status:` in the task frontmatter (`planned|in-progress|blocked|done`) is the
index across parallel task directories. `.ai/.current` is the resume
pointer, starting `task: <id>`.

Since 11.1 tasks run in parallel in one working tree (section 51): two
`/task create` or `/task do` sessions side by side, each with its own
worker sub-agent. Isolation is cooperative, not physical:
- `tasks.py start` takes `.ai/.current` only while the task it names is
  not running; otherwise it writes the task's own pointer
  `.ai/.current-<id>` and prints every running task with its files
  (`PARALLEL`).
- A host file is claimed before it is edited, `tasks.py claim <id>
  <path>...`, which refuses (`CLAIMED`) a file another running task
  listed. Two tasks never edit the same file; the one that needs it asks
  the user or waits.
- Every `.ai` commit names its own paths (`git -C .ai add tasks/<id>`,
  plus `notes.md` when changed), never `add -A`, which would sweep a
  parallel session's half-written files; the turn-end hook names the
  dirty paths instead of suggesting `add -A`.
- A review judges the task's diff as `git diff --` its claimed files; a
  file another running task claimed is not scope creep.
What stays shared: one working tree and so one test run, which sees the
other task's unfinished edits (a failure in a file another task claimed is
recorded, not fixed), and `notes.md`. Git worktrees, the physical
alternative, were rejected for now (section 51). A `depends:` line records
that one task waits on another; it schedules nothing.

## Property 3: one command set

Four commands: `/explore`, `/task` (`create`, `do`, `list`, `tree`),
`/framework-models`, `/framework-update`. Same names on every harness, and
the same bodies but for what the harness needs (the update body, and
`/framework-models` where the harness runs a command before the model sees
the skill, section 84); only the entry files differ (Agent Skills
under `.claude/skills/`, prompt files under `.github/prompts/`, commands under
`.opencode/commands/`). `AGENTS.md` is the one instructions file and every
harness reads it natively except Claude Code in some cases: it reads
`AGENTS.md` only when no `CLAUDE.md` or `CLAUDE.local.md` exists in the
project directory or above it, and in a session that can load it (not
Bedrock or telemetry-off before 2.1.281). So the claude scaffold makes sure
the project root has a `CLAUDE.md` importing `@AGENTS.md`, created, appended
to or left alone, by `init-agent` and, through `--ensure-agents-import`, by
`/framework-update` (section 81; 7.1 had retired the pointer, see its version log entry).
That file is the user's, never recorded as framework output and never
retired. A name that collides with a harness built-in is
renamed on **every** harness, which is why the update command is
`/framework-update` everywhere (Hermes reserved `/update`; the name outlived
Hermes support, section 43).

Switching harness is tooling, not an update: `init-agent --harness <name>`
writes the new set and retires the recorded old one into a backup. It is
also the only path a scaffold built for Hermes still has: init and the
update refuse to render Hermes and print the switch instead.

Updating a scaffold is a merge, so the agent does it, not the CLI.
`/framework-update` reads the version stamp, renders a pristine reference,
then adds, merges, migrates and retires file by file. It never re-runs
`/explore`: what the project knows is the expensive artifact and is migrated,
never re-derived. The migrations it applies come from the reference's own
copy of the skill, not the project's: the project's copy is as old as the
project's version and cannot know what the new version changed.

Since 12.2 the session that runs `/framework-update` does not merge
itself: it hands the update to the `updater` sub-agent, on the small model
the project chose for it (`init-agent --models --updater`, the same
mechanism as the worker and reviewer, section 59), and checks the result
from the files: stamp, file list, `.ai` commit, `model:` lines, the
GENERATED section. The updater is the harness's sub-agent; with
`herdr` it gets a tab of its own that stays open for the user, on every
harness. No updater model, or `inline`, means the update runs in the
session as before; the framework never picks a model for it (sections 64
and 68). The worker of `/task do` follows the same rule: a sub-agent by
default, a Herdr tab only when asked.

## Property 4: bounded own footprint

- `AGENTS.md` before the generated section: 612 words on claude, 610 on
  opencode, 728 on copilot, where the balance is that harness's own CLI note.
  `check_templates` fails above 730 (650 until 12.10, raised for the test
  rule of section 72, which saves more tokens than it costs; 700 until 14.2,
  raised for the smallest-change rule of section 97). The number is
  a tripwire against
  drift back toward a digest, not a target: a rule stated clearly beats
  one squeezed to fit.
- The generated block: cap ~300 tokens.
- The notes hub on Claude Code (up to 100 lines and 8,000 bytes, about
  2,000 tokens) and on OpenCode (the whole file, no cap) in the context of
  every session, from the project's own
  `.ai/notes.md`. Argued below.
- `probe.py`: 199 lines, commands and documentation detection only.
  `tasks.py`: about 1,900 lines: the task table, the dependency tree, the
  resolver, the tracker discovery, the models gate, the notes check and its link step, and
  `start`/`tick`/`claim`/`finish`.
- A claude scaffold records 21 framework files, a copilot one 19, an opencode
  one 20 (its plugin is the extra entry point), counting the five `/task` parts under `.ai/agent/task/`.
- Everything else, skill bodies included, is read on demand. `/task` loads
  only its dispatcher (about 3.4 KB); Create and Do are read when the resolver's
  verdict sends the agent there (section 42), and Do sends a session to
  `supervise.md` (about 1,200 words) only when it hands the task to a worker
  (section 92). The worker reads `steps.md` (about 820 words) and has `work.md` as the
  body of its agent file on Claude Code and OpenCode, about 940 words that
  only a spawned worker loads, not `do.md` (sections 77 and 85).

### Why the notes hub may be always-loaded on Claude Code (section 83)

Property 4 caps the always-loaded text; 12.21 adds to it, so the case is made
here, before the template changes.

- **What is added.** The hub `.ai/notes.md`, never the leaves, comments
  stripped, cut at 100 lines or 8,000 bytes (about 2,000 tokens at most),
  plus at most three freshness flags. It sits in the cached prefix of the
  session, as `AGENTS.md` does.
- **What it replaces.** Protocol rule 1 already said "Read `.ai/notes.md`
  first", and a hub read whole is those same tokens. What changes is who
  reads it: no read turn at the start of a session and after each compaction
  (the earlier read survives a compaction only as far as its summary does),
  and no session in which the agent did not read it. Where an agent would
  have skipped the read, the hub now costs tokens it did not cost before;
  that is the price, and the cap bounds it. No run measured how often the
  read was skipped, so this is an argument and not a number.
- **Not a digest.** What Part II measured and rejected is the
  LLM-generated overview of the code (ETH round: success -0.5% and -2%,
  cost +20% to +23%, no faster to the first relevant file). The hub is the
  other kind of content, developer-written and about what the repository
  cannot state (Pillar 1, "The test"), the arm Part II records as the only
  one that measured positive: a rule stated by the user landed verbatim and
  a tool named in the always-loaded block got used. No round in Part II
  loaded such content and came out worse. The risk is real all the same: a
  hub that drifts into a code summary would now be paid for in every
  session. Two things guard it: the cap, and `tasks.py notes` (section 82),
  which flags a hub over the cap and a note citing a path that is gone, and
  whose flags the hook prints with the hub.
- **Claims unchanged.** This is not a saving. "Not cheaper" and "Not
  amortizing" stand; nothing here is argued from speed.
- **Where.** Claude Code only. OpenCode's `instructions` key could load the
  file, but its relative-path base, its behavior on a missing file and
  whether sub-agents get it are not stated in its docs, and the version
  installed here (2.2.5) shows nothing for them without a model call, so
  none of it is shipped. Copilot has no verified equivalent. They keep
  reading the hub themselves.

## What the framework does not claim

- **Not cheaper.** Every round measured more tokens than a bare agent.
- **Not faster to the relevant file.** An always-loaded overview does not
  shorten discovery, at any repo size.
- **Not amortizing.** Later tasks on the same repository are not cheaper or
  more correct because of accumulated context. Three rounds tested this and
  none supported it.
- **Not proven more correct.** The evidence is split and the only measured
  correctness loss was caused by the framework's own spec.
- **Not proven cheaper by delegation.** The cheaper worker tier lowers the
  price of the steps, but the reviews, the decisions and the reading of
  each report stay on the session's model. Section 23 measured a
  same-tier worker at +35% tokens; a harness that cannot pick the
  sub-agent's model pays that. The
  two live runs of section 50 are evidence that the split works, not a
  cost result.
- **Not measured on anything but code changes.** Every benchmark task was a
  change with a gate. The bug, investigation and test types rest on the
  organizational argument of section 39, not on a round.

What can be said: a rule the user states once lands verbatim in the
requirements block and is still being cited three sessions later; a tool named
there gets used; the direct path costs a few percent over a bare agent while
the spec chain costs two to three times.

## The protocol

Every session, regardless of path. `/task` runs only when the user invokes
it; the Right-sizing paragraph of AGENTS.md says so, so the protocol does not
repeat it.

Execution (section 42): keep going while a step needs no input, with status
notes in the same message as the next action; stop only when blocked on the
user, when a workflow says so, or before anything destructive nobody asked
for; a change the user or a task step asked for, even to a production
database, is the job (section 61). An answered
question stays settled unless the user reopens it. Every run ends with the
headings Blocked on me, Changed, Found. Most direct tasks add nothing to
`.ai/notes.md`.


1. Read `.ai/notes.md` unless the harness put it in context (Claude Code,
   section 83). Open only the leaves the task needs.
2. When code changed, the tests that cover the change, not only the one a
   task names, and lint on the changed files must pass on the final code.
   Done = those checks green. The full suite is CI's or the owner's, not
   the agent's (section 75); docs or comments only need no test run. When the task is a question,
   done = an answer citing its evidence, or "inconclusive" with what was
   ruled out.
3. Commit `.ai` in its own repo after changing it. Never commit `.ai` content
   to the host repo.
4. `.ai/.current` is the resume pointer (`.ai/.current-<id>` for a task
   running in parallel); read it at session start.
   Unrelated tasks run in fresh sessions: instruction adherence decays
   as a session grows, and the task file is the handoff that makes a
   fresh session cheap. `/task do` needs none: the session that runs it
   is the supervisor, the long-memory elephant, and its worker is the
   fresh goldfish (section 67).
5. Never commit on or merge into the default branch unasked. Work on a
   feature branch and stop at it or its pull request; merging is the user's
   action.
6. Never add a co-author trailer to a commit message. Harnesses inject one by
   default; the scaffold overrides it.

Enforced mechanically where possible: a turn-end hook blocks ending a turn
while `.ai` is dirty, and a pre-tool hook blocks rules 5 and 6 at the shell
(`git merge` on the default branch, `git push` targeting it, `gh pr merge`, a
commit whose message carries a co-author line). A rule that can be checked
deterministically gets a hook and stays in the protocol text as the backstop,
because instructions are advisory and hooks are not. One exception by the
owner's choice: a commit on the default branch is rule 5 in the text only,
with no hook, because the user may ask for one and a hook cannot tell asked
from unasked (section 61).

The two hook scripts are the same file on every harness. Claude Code and
Copilot (CLI, VS Code, cloud agent) both pipe a JSON payload with `cwd`,
`tool_name` and `tool_input.command` to stdin and accept `{"decision":
"block", "reason": ...}` on stdout, so one script serves all of them; only
the tool's name and the registration differ:

- claude: `.claude/hooks/`, registered in `.claude/settings.json`
  (`PreToolUse` on `Bash`, `Stop`), plus a read-only permission allowlist.
- copilot: `.github/hooks/`, registered in `.github/hooks/llm-agent.json`
  (`preToolUse`, `agentStop`), which VS Code and the cloud agent read too.
  Loaded only from a trusted folder; an untrusted checkout runs with no
  hooks and no warning, which is why the AGENTS.md note names the
  condition.

The `reviewer` has a third hook script on claude, `reviewer_guard.py`,
declared in its own agent file and not in `settings.json`, so it runs only
while the reviewer does (section 79).

Every harness overrides a turn-end block after a few consecutive passes and
runs hooks only when the repository is the session's working directory, so
the protocol text remains the guarantee the hooks merely back.

## Language and register

Two registers. Normative documents (AGENTS.md, skill bodies) in plain
imperative English; notes content telegraphic. Identifiers, paths and commands
verbatim. No em dashes. English rather than the user's own language throughout,
for two reasons that have not changed since section 8: it is the best-trained
model language, and it tokenizes more densely than German. Generated artifacts stay ecosystem-neutral: no benchmark terms, no
repo-specific names.

## The rule for future changes

A change that introduces an always-loaded summary of the codebase, or that
makes a task plan or review the default, contradicts a measurement. It belongs in
this file as an argument first, with the evidence that overturns the old one,
and only then in a template.

A change that removes an artifact needs no such argument. Dropping the
`write()` call is enough; `/framework-update` deletes the file from existing
projects via the recorded file list.

---

# Part II: What was measured

Each round had a `report.md` and raw per-session files under
`benchmarks/<name>/`, everything pinned except MODEL and EFFORT. The
`benchmarks/` tree was removed on 2026-09-29 with the measurement program
halted; this table is the record. The raw files, runbooks and gate tests are
in git history: `git show 3fe749a:benchmarks/<name>/report.md`, or `git checkout
3fe749a -- benchmarks` to restore them. Paths to `benchmarks/` in Part III refer
to that commit.

| Round | What it measured | What it decided |
|---|---|---|
| `haiku-high-2026-07-03` / `-04` | First amortization attempt, n=1 | Framework's marginal session was more expensive, not less. Overhead flat across modeled N. The one round where the framework arm produced the only valid fix. |
| `sonnet5-medium-2026-07-03` | One-shot cells, large profile | Baseline for the profile that v5.22 later removed. |
| `sonnet5-medium-small-2026-07-06` | One-shot overhead, small profile | +84% to +403% on a single task. Cost half of the digest claim confirmed. |
| `w4-sonnet5-medium-2026-07-17` | Worker sub-agents on a mid-tier model | Retired the idea (section 23). |
| `u-update-sonnet5-medium-2026-07-28` | The `/framework-update` skill | Agent-driven update works as a merge. |
| `tidy-up-sonnet5-medium-2026-07-29` | The `/tidy-up` sweep | Worked; cut in v7.0 anyway for serving neither pillar. |
| ETH Zurich context-file evaluation (external; `docs/history/agents-md-paper-response.md`) | LLM-generated context files, 4 agent/model pairs, SWE-bench Lite + AGENTbench | Success -0.5% and -2%, cost +20% to +23%. Agents with a file reach the first relevant file no faster. Tools named in the file get used, 1.6 vs 0.01 per task. Killed the digest (v6.0). |
| `v6-vs-5.26-sonnet5-medium-2026-09-14` | 6.0 against 5.26, cell 2 | Both PASS. Verification, not a saving. |
| `seq-sonnet5-medium-2026-09-14` | Three tasks, two arms, three reps, hidden tests | Marginal cost of tasks 2+3: +74%, +160%, +136%. Amortization failed 0 of 3. One correctness loss from a spec criterion naming a single test. Made spec and build opt-in (v6.1). |
| `v7-vs-6.1-sonnet5-medium-2026-09-14` | 7.0 against 6.1, framework arm and context-only arm | All four PASS, identical packages. 7.0 was 7% cheaper on one arm and 11% dearer on the other: noise. The useful number: the spec chain costs 2.1x to 2.5x the direct path. |
| `constraint-sonnet5-medium-2026-09-14` | Does a stated non-derivable rule survive three sessions? 21 sessions, hidden constraint test | 18 of 18 gates passed. Constraint held F 6/6, B 5/6: no support under the pre-stated rule. The round cannot decide, because task N's output became task N+1's local precedent. `/explore` with a human answering landed the rule verbatim 3 of 3. |
| `egm-live-opus5.5-2026-11-01` | `/task do` with a supervised cheaper worker (section 50), two tasks, n=1 each | Both done. Herdr worker (sonnet) ran in its own tab; a trust dialog forced the sub-agent fallback (haiku) once. Supervisor caught one wrong citation. No cost claim: no inline twin. |
| `parallel-satty-opus5.5-2026-11-01` | Two `/task` sessions side by side in one tree, create then do (section 51) | Both pairs ran at once. Commits path-scoped, a `CLAIMED` refusal stopped a real collision, first live second round. One done, one blocked. |
| `harness-sh-2026-11-08` (`tests/harness-benchmark.md`) | Claude Code vs OpenCode, Sonnet supervisor, Haiku worker, Sonnet reviewer, 3 runs each on satty, framework default effort | 18/18 tasks and decisions on both. OpenCode about $1.30 per run against $2.22 and 475 to 495 s against 564 to 905 s, no overlap. Found the small-task rule being read as "docs are small"; Do now counts editing steps (section 56). |
| `harness-sh-equal-effort-2026-11-08` | The same with every role at `medium`, verified per role | 18/18 tasks, 17/18 decisions on both. OpenCode $1.23 against $2.18, no overlap; time by median only (563 against 586 s, ranges overlap). The difference is input: Claude Code re-reads twice the context. OpenCode's tool calls ran natively behind its Claude Agent provider, so this is Claude Code's CLI against the Claude engine inside OpenCode. Next: the top-tier profile. |
| `versions-opencode-2026-11-15` (section 95; tags `alpha`, `bravo`, `charlie`) | The framework against its own earlier versions on the harness benchmark, OpenCode, equal-effort profile: 11.6 (5 runs), 12.14, 12.26 and 12.30 (2 runs each) | Cache-read tokens per run: 11.6 median 2.76M; 12.14 3.06M and 3.20M; 12.26 3.45M and 3.62M; 12.30 2.60M and 2.57M with 6 of 6 on both runs. The review's first batches cost about 12% more than 12.14; fewer model calls and less loaded text (sections 90 to 93) took 12.30 about 17% below it. Cache-write and output tokens did not move. A cold worker on top of 12.30 showed no saving (section 94). |
| `opencode-2.3-and-claude-2026-11-15` (section 96) | Framework 14.1 on OpenCode 2.3.0 (background sub-agents) and on Claude Code 2.1.325, one run each, same profile | 6 of 6 on both, no nudge. OpenCode: 2.64M cache-read tokens, 322 s (12.30 on 2.2.5: 2.60M, 2.57M). Claude Code: 5.38M, 487 s, the first live run of the 12.27 to 12.30 forms there. Before the fix, the driver left the worker task unfinished on 2.3.0 (5 of 6). |

**Planned and withdrawn:** `amortization-playbook.md` (Experiment B,
navigation2) was withdrawn with the amortization thesis. `constraint-runbook.md`
had its four pre-run controls verified, but a deciding round needs a
constraint that an earlier task cannot seed. Both were removed with the tree.

**Status of the measurement program:** halted 2026-09-14. Four rounds in one
day produced no defensible performance benefit, and each failed round bred a
more elaborate successor. The accumulated nulls are the answer: the value is
organizational, not performance. The one untested arm worth a single cheap run
is weak models, where the only positive result the framework ever produced
came from an n=1 haiku round.

---

# Part III: Revision history

Sections 1 to 40, unchanged, numbered as they have always been because the
README, the templates and the benchmark reports cite those numbers.

**Sections that describe a framework that no longer exists.** Retired by
section 36: **1** (Knowledge Base), **2** (Phases), **4** (Ticket lifecycle),
**5** (Living KB), **6** (AGENTS.md as hot-tier transport), **9** item 5
(token economy), **13** (Small-project profile), **20** (Automatic profile
selection), **21** (Explore-freshness guard). Retired by the v7.0 cut list in
section 38: **15** (`/import-kb`), **22** (`/goal` as a documented mode, moved
to the README), **25** (`/import-agent`), **26** (`/tidy-up`). Already marked
removed in its own heading: **23** (Worker sub-agents), revived under its
own conditions by section 50 for `/task do` only; read 23 for the evidence,
50, 52 and 53 for what is in force. Retired by section
43: **30** (Hermes as a third harness), and the Hermes parts of 32, 34, 35
and 39. Retired by section 52: the Herdr worker, `delegate.py` and its
model table in **50**, and the Herdr worker tabs of **51**.

Everything else still describes current behavior, and sections 36 to 39
are the reasoning that produced Part I. Where 37 and 38 name `/spec`,
`/build` and `.ai/changes/`, read them as the 7.x names of what section 39
generalized; their evidence carries over unchanged.

## Version log

v14.3 (2026-11-26, the work runs on what create settled, section 98.
`/task create` asks, in its one dialog, what would otherwise stop the work
(evidence and fallback per criterion, where it is proven, scope, outward
actions) and runs each criterion's command once; the answers go into
`## Autonomy`. `/task do` decides reversible choices inside it, asks each
question once, and offers no extra work.)

v14.2 (2026-11-25, the smallest complete change on the direct path, section
97. AGENTS.md's Right-sizing paragraph takes the one-line essence of the
ponytail skill, with its tests clause; the AGENTS.md tripwire moves from 700
to 730 words. Live A/B against 14.1 on Haiku 5.5: no loss, no measurable
size gain. The i-have-adhd skill was evaluated and left out.)

v14.1 (2026-11-15, a sub-agent that runs in the background, section 96.
OpenCode 2.3.0 returns from a spawn before the sub-agent has finished. The
supervision, the review gate and the update hand-over say what to do then:
wait for the report. The benchmark driver waits for a run's sub-agents
before it judges a turn. Run live on OpenCode 2.3.0 and on Claude Code.)

v14.0 (2026-11-15, the best-practice review of 12.14 closed, section 95. No
behavior change: the record of what 12.15 to 12.30 changed, the measured
outcome on the tagged versions `alpha`, `bravo` and `charlie`, the sources,
and how to repeat the review. There is no 13.)

v12.30 (2026-11-15, a shorter dispatcher, section 93. The `/task` command
text drops what its own sections and `create.md` already say; no rule
removed.)

v12.29 (2026-11-15, a session that works the task itself does not load the
supervision, section 92. `do.md` keeps the decision and what both paths
need; the part on supervising a worker moves, text unchanged, to
`.ai/agent/task/supervise.md`, read only at the decision for a worker.)

v12.28 (2026-11-15, the start of a task in fewer calls, section 91.
`tasks.py resolve` prints the task file after a `DO` verdict; `/task create`
and `/task do` read their part file in the turn of `resolve`; `do.md` has
a session read the notes, `steps.md` and run the models gate with `start`
in one turn.)

v12.27 (2026-11-15, the end of a task in one call, section 90. `finish <id>
done --tick-steps <n>... --tick <n>... --commit` ticks the named items,
closes the task and commits `.ai` with the task's paths only; `tick` takes
`--commit` too. `do.md`, `steps.md` and `work.md` use the one-call forms and
join consecutive commands that need no look between. Fewer model calls at
the end of a task, where each call carries the most context.)

v12.26 (2026-11-14, path-scoped notes leaves on Claude Code, section 89.
A leaf may start with a `paths:` frontmatter; `tasks.py notes --link` keeps
one gitignored symlink per such leaf under `.claude/rules/`, run by init,
re-init, `/framework-update` and the agent. Nothing always-loaded is added;
other harnesses read the leaf on demand as before. Reverses the "not built"
of section 87 on the evidence of section 89.)

v12.25 (2026-11-14, a forced re-init keeps the keys a user added to
`.opencode/opencode.json`, section 88. `compaction` was dropped before.
The harness's compaction default stays; README says when to change it.)

v12.24 (2026-11-14, the notes hub in context on OpenCode too, section 86.
`.opencode/opencode.json` gets `instructions: [".ai/notes.md"]`; a user's own
entries survive a re-init and an update. Corrects section 83's "not shipped".)

v12.23 (2026-11-14, the worker's contract is in its agent file, section 85.
On Claude Code and OpenCode the body of the `worker` file is rendered from
the same text as `work.md`, so a worker starts without the read turn.
Copilot keeps the pointer. `work.md` stays.)

v12.22 (2026-11-14, script output without a model round trip, section 84.
On Claude Code and OpenCode `/framework-models` carries the output of
`tasks.py models --list --exit-zero` in its body, run by the harness before
the model sees it. `/task` is not changed. Copilot keeps the old body.)

v12.21 (2026-11-14, the notes hub is in context at session start on Claude
Code, section 83. A `SessionStart` hook prints the capped hub and the
freshness flags. OpenCode and Copilot: not shipped, reasons in the section.
Argued in Part I, Property 4.)

v12.20 (2026-11-14, a freshness check for the notes, section 82.
`tasks.py notes` flags a hub over 100 lines or 8,000 bytes, a cited path
that is gone, a dead hub link and an unlinked leaf; the same lines close
`/task list` when there are any.)

v12.19 (2026-11-14, AGENTS.md loads on Claude Code in every case, section
81. The claude scaffold makes sure the project root's `CLAUDE.md` imports
`@AGENTS.md`, from `init-agent` and from `/framework-update`; the file is
the user's and is never retired.)

v12.18 (2026-11-14, one memory on Claude Code, section 80. The generated
`.claude/settings.json` sets `autoMemoryEnabled: false`; a user's own value
survives a re-init and an update.)

v12.17 (2026-11-14, the sub-agent roles are enforced, section 79. The
Claude Code worker may not spawn agents; the reviewer's shell is limited
to read-only commands by a hook in its own frontmatter on Claude Code and
by `shell` rules on OpenCode.)

v12.16 (2026-11-14, a turn limit on every sub-agent, section 78.
`maxTurns` on Claude Code and `steps` on OpenCode: worker 200, reviewer 50,
updater 100. Tripwires against loops, not budgets.)

v12.15 (2026-11-14, the worker reads only its own steps, section 77.
`do.md` splits: the working steps and the escalation rule move to
`steps.md`, which the worker and a session working inline both read; the
worker no longer loads the supervisor protocol.)

v12.14 (2026-11-13, ask with the question tool, section 76. AGENTS.md
names each harness's question tool and asks all open questions together;
Blocked on me never holds a question; a worker asks its supervisor, never
the user.)

v12.13 (2026-11-13, the full suite is CI's, section 75. Every changed
file gets the cheap check that reads only it: the tests covering changed
logic plus lint, a linter or validator for a declarative file. No agent
runs the full suite, a build, CI or a start on the target unless the task
asks for it. `tasks.py` counts only a `Review:` line as the review
record.)

v12.12 (2026-11-12, a workaround is not a pattern, section 74. A
workaround for a denied permission is recorded with its cause and the
normal way is tried again, instead of standing for the rest of the task.)

v12.11 (2026-11-12, follow the existing pattern, section 73. Create names
the sibling a new part copies; a user redirect drops the old design and its
pending review; a correction names a source only after reading it; a
continued worker re-reads `work.md`.)

v12.10 (2026-11-12, tests are for logic, section 72. No change-detector
tests for declarative files; their check is the tool that reads them. The
reviewer asks of every assertion whether it could fail other than by an
intended edit. AGENTS.md tripwire raised from 650 to 700 words.)

v12.9 (2026-11-12, the OpenCode paths run live, section 71. The model
check reaches worker and updater; an update makes one `.ai` commit and
writes no note, and step 0 checks both.)

v12.8 (2026-11-11, review fixes for 12.2 to 12.7, section 70. OpenCode's
Herdr tab starts plain and spawns the role as a sub-agent; the update
check diffs merged files against the backup; the reviewer follows a
finding into `evidence.md`; the long-line flag spares `Supervisor round`
lines and done tasks; `gh run watch` is on the allowlist; the runbook
no longer asks for a fresh session per `/task do`.)

v12.7 (2026-11-11, a finding is a claim and a pointer, section 69. At
most ~200 characters, checks of a kind grouped in one line, long evidence
in `.ai/tasks/<id>/evidence.md`; "verbatim" only for the one full run;
`tasks.py` flags Findings lines over 300 characters. The update deletes
its old backup by literal path.)

v12.6 (2026-11-11, Herdr only when asked, on every harness, section 68.
The `/task do` worker and the `/framework-update` updater are the
harness's sub-agent by default on Claude Code, Copilot and OpenCode; with
`herdr` in the call they get a Herdr tab, started per harness on the
role's model.)

v12.5 (2026-11-11, the session supervises, the worker runs in a sub-agent
or a Herdr tab, section 67. On Claude Code inside Herdr the `/task do`
worker gets a tab of its own (`claude --agent worker`); elsewhere a
sub-agent. `/task do` no longer asks for a fresh session.)

v12.4 (2026-11-11, the smallest thing that meets the Goal, section 66.
Corrections only for unmet criteria, the rest `Not sent back`; the
smallest option recommended, with its cost; asks beyond the criteria
offered as a follow-up task first, logged as `User round`; one-line
Findings without restated rules; a `waiting` report that ends the
supervisor's turn instead of watching CI.)

v12.3 (2026-11-11, `/framework-models` lists what can be named, section
65. `tasks.py models --list`: `opencode models` on OpenCode, the backend's
`/v1/models` on Claude Code where it answers (chat models only, prices
where the backend gives them), a pointer to the picker on Copilot. The
user still chooses; the /task do gate never lists.)

v12.2 (2026-11-11, the update runs on a small model, section 64.
`/framework-update` hands the merge to a new `updater` sub-agent whose model
the project sets with `init-agent --models --updater`, in a Herdr tab of its
own on Claude Code, and checks the result from the files. No updater model,
or `inline`: the update runs in the session as before.)

v12.1 (2026-11-10, the full suite runs once per task, section 63. The
worker iterates, and reports `review`, on the covering tests and lint of
the changed files; the project's full test and lint commands run once on
the final code, and a green CI run on the last push is that run. The
review and the supervisor read the diff and the recorded results and run
nothing; only the worker runs checks.)

v12.0 (2026-11-09, OpenCode model test, default-branch rules and
`/framework-models`, sections 60 to 62. `init-agent --models` tests an OpenCode name the way it tests a
Claude Code one, and also checks that the sub-agent ran on the model the
file names. Rule 5 and the worker's contract name committing on the default
branch, not only merging into it; protocol only, no hook, so the user can
still ask for it. Force-pushing is asked about only for the default branch,
and destructive work only when nobody asked for it. `/framework-models`
shows the worker and reviewer models and prints the command that sets
them, section 62.)

v11.9 (2026-11-09, sub-agent models are explicit, section 59. `/task do`
refuses unless the `worker` and the `reviewer` each have a model in their
agent file; `tasks.py models` is the gate, `init-agent --models` sets and
tests them; no model is ever picked, inherited or passed at spawn.)

v11.8 (2026-11-09, `/agent-models` removed, section 58. The command, its
skill body and its per-harness fragments are gone; the `worker` agent and a
hand-written `model:` line in an agent file stay. The feature is to be
rethought.)

v11.7 (2026-11-09, OpenCode gets the `worker` agent and `/agent-models`,
section 57. The OpenCode harness follows the 11.5 change: a `worker` agent
beside `reviewer`, the `model:` line set by `/agent-models`.)

v11.6 (2026-11-09, OpenCode as a third harness, section 56. `--harness
opencode` writes commands, the reviewer agent, a permission list and the two
hook scripts under `.opencode/`, with a small plugin bridging OpenCode V2's
hooks to the scripts. Tested live on 2.2.5.)

v11.5 (2026-11-09, a `worker` agent and `/agent-models`, section 55. The
`/task do` worker is a `worker` agent defined beside `reviewer` on both
harnesses; `/agent-models` sets the `model:` line of either, the same way
on both. A small task, at most one open step that edits a host
file, is worked inline. Ported from the OpenCode branch without OpenCode.)

v11.4 (2026-11-05, an archived dependency is a cleared blocker, section
54. `/task tree` drops a `depends:` id that names a task archived as done
without a warning, flags one archived in another status as `archived as
<status>, not done`, and one that names no task as `names no task`.)

v11.3 (2026-11-03, the worker does the whole job, section 53. The worker
works every step the task names through to the pull request, CI and dev
runs, asking for a review before code ships; the supervisor reviews,
answers as the user would, asks the user only what it cannot decide, and
does none of the work. Reports: `review`, `question`, `stuck`, `done`
(`needs-user` gone). The supervisor resumes the same worker where the
harness can, trusts CI and recorded evidence, and no longer works steps
of small tasks itself. Runbook: TC-D6 rewritten, TC-D3 adjusted.)

v11.2 (2026-11-03, the worker is the harness's own sub-agent, section 52.
`delegate.py` and every Herdr path of `/task do` are gone: the supervisor
spawns a fresh general-purpose sub-agent on a cheaper model where the
harness lets it pick one, inline when asked, for two or fewer open steps,
or when no sub-agent can be spawned. Supervision is unchanged. Removed:
`delegate.py`, `tests/test_delegate.py`, the `delegate.py` and `herdr
agent` permissions, `LLM_AGENT_WORKER_MODEL`. Runbook: TC-D6, TC-D7
rewritten.)

v11.1 (2026-11-01, parallel tasks in one working tree, section 51.
`/task create` and `/task do` run side by side: a running task keeps
`.ai/.current`, the next gets `.ai/.current-<id>`; `tasks.py claim`
gives each host file one owner; every `.ai` commit is path-scoped, never
`add -A`; the review judges the claimed files. Live test: both satty
tasks planned and worked in parallel. Runbook: TC-P1. Also, from a report
at work and the satty transcripts: a worker that stops is a question for
the user. The supervisor asks first, edits no host code and keeps the
worker tab open until the answer, and takes over only with agreement; a
missing toolchain is `needs-user`, not `stuck`. Runbook: TC-D3.)

v11.0 (2026-11-01, `/task do` on a supervised cheaper-tier worker, section
50, after Google's Elephant-Goldfish Model. The `/task do` session
supervises; a fresh worker on a cheaper model works steps 2 to 5 from
`.ai/agent/task/work.md`, in a Herdr tab when the session runs inside
Herdr, as a harness sub-agent otherwise. `delegate.py plan|launch|close`
decides the mode and model; `inline` keeps the old path. `tasks.py tick`
ticks named criteria and steps, no "all". New framework
files: `delegate.py`, `task/work.md`. Test: `tests/test_delegate.py`;
runbook: TC-D6, TC-D7.)

v10.6 (2026-11-02, /task create asks for the tracker issue, section 49.
Create's first question, in the same message as the type, is whether a
tracker issue exists; the fetched issue feeds the plan, its key prefixes
the task id, and the task file records it in a `## Tracker` section.
`tasks.py trackers` discovers the tracker access (`.ai/trackers.conf`,
detected `gh`/`jira` CLIs) and `resolve` rejects a bare issue-key prefix
without a slug. Runbook: TC-C3, TC-C4.)

v10.5 (2026-11-01, /task tree placement fixes, section 48. Tasks sit at
their shallowest position across the whole tree, branch characters
follow the final child lists, every cycle is flagged, `depends:` ids
match without case.)

v10.4 (2026-10-27, /task tree independents on the first level, section
47. Tasks with no dependency ties stand on the first level as leaves,
after the tasks that block others; the trailing `independent:` line is
gone.)

v10.3 (2026-10-15, /task tree cycle handling, section 46. A cycle is
found from any task no first-level task reaches, flagged once in edge
order, and tasks waiting on it nest below it.)

v10.2 (2026-10-15, /task tree: the dependency view, section 45.
Task frontmatter gains an optional `depends:` line; `tasks.py tree`
prints live tasks as an ASCII dependency tree; Create asks the
dependency question. Runbook: TC-L2.)

v10.1 (2026-10-04, task bookkeeping in the script, section 44. `tasks.py
start` and `finish done|blocked` set status, the `blocked:` line and the
resume pointer; `finish done` refuses an unmet gate. `do.md` routes every
status change through them and every `.ai` commit through the relative
`git -C .ai`. Runbook: TC-D5, TC-E1, TC-E2 and a bookkeeping criterion for
every do case.)

v10.0 (2026-10-04, Hermes support dropped, section 43. Two harnesses,
claude and copilot. init, `--emit-reference` and `--bootstrap-update`
refuse `hermes` and print the switch to a supported harness, which retires
the recorded `.agents/` files into the harness backup; the out-of-repo
`~/.hermes` hook entries are the user's to remove. The `/framework-update`
name stays.)

v9.1 (2026-10-04, execution rules from the Opus 5.5 prompting guide plus
the owner's point-by-point decisions. AGENTS.md: keep going without status
stops, answered questions stay settled, a three-heading run summary, most
direct tasks add no note, covering tests while iterating and the full suite
once before done, no suite for docs or comments; protocol rule 3 folded into
Right-sizing, rules renumber. `/task`: type asked with the done-when Q&A in
one message, mechanical diffs reviewed inline, only load-bearing citations
all opened, Create and Do split into `.ai/agent/task/` and read on demand.
Claude: `effort` frontmatter on skills and `reviewer`. §42.)
v9.0 (2026-09-30, one `/task` command replaces `/task-create`, `/task-do`
and `/task-list-all`, with `create`, `do` and `list`. A script decides
whether a task exists (`tasks.py resolve`), so `/task <id>` alone goes to
create or do without the agent searching. An investigation is planned and
worked in one go, with no Q&A after the type; the other types are planned
as before. The three old skill entries are retired framework files. §41.)
v8.11 (2026-09-29, a skipped review is caught mechanically. The 8.10 re-test
on Copilot (mai-code-1.1-flash) reached `done` with no review and no
Findings line, although the skill requires both and the harness can spawn a
sub-agent. Text alone did not hold, so the check moves into the script, as
8.4 did for unticked boxes: `tasks.py` flags a `done` task whose Findings
names no review, and `/task-do` fixes the line's form (`- <date> Review:
<kind>: <result>`) and sets `done` only once it is there.)
v8.10 (2026-09-29, the review checks citations, and the fallback order is
enforced. First Copilot run on satty (gpt-6-luna): an investigation reached
`done` with 4/4 steps ticked, but its answer was wrong and two citations did
not say what it claimed (it said `input_scale` does not set the zoom;
`src/femtovg_area/imp.rs:188` shows it does). Copilot has no `reviewer`, so it
went straight to a self-review, which agreed with itself. Now every review,
inline or fresh, opens each file-and-line citation; the fresh context is the
`reviewer`, else a general-purpose sub-agent, tried before any self-review,
and a self-review names what was unavailable and why. The `reviewer` brief
gains the same citation check. Also: `tasks.py` unquotes quoted YAML values,
which Copilot writes and the table showed with their quotes. The first
two-digit minor version: `/framework-update` now says to compare version
parts as numbers, so 8.10 is not read as older than 8.9.)
v8.9 (2026-09-29, the Type and Status columns show the emoji alone, with a
legend line under the table; an unknown value stays text so a typo in a task
file shows. The terminal color moves to the id, since a colored emoji does
not change color. Owner's request.)
v8.8 (2026-09-29, the task table gets emoji for status and type, a pointing
hand for the resume pointer and a mark on each flag, so a long table reads
at a glance. Status is also colored, but only when a person runs `tasks.py`
in a terminal: the agent reads it through a pipe and copies it into
markdown, where escape codes would be noise, and `NO_COLOR` turns it off.
Owner's request.)
v8.7 (2026-09-29, `/task-list-all` puts the table in the reply itself. On
satty the agent ran `tasks.py` and answered "the script's output is above":
Claude Code collapses tool output, so the user saw a count and no table. The
8.4 wording "show its output as printed" allowed that reading. The skill now
says to copy the complete output into the reply verbatim, because the user
does not see tool output.)
v8.6 (2026-09-29, the inline review threshold is size only. On satty the
agent reviewed inline twice where 8.5 required a fresh context: an
investigation with six steps, no diff and a ten-line Outcome, and a
five-step docs change with a six-line diff. Both times it judged by size and
ignored the step count, and both times a sub-agent would have added nothing.
The rule now matches that judgment and stays checkable: inline when the
diff and the Outcome are each under ~30 lines, a fresh context when either
is larger. The Findings line from 8.5 keeps the choice visible.)
v8.5 (2026-09-29, two `/task-do` rules made checkable. Observed on a live
repo (satty, sonnet-5.5): an investigation set `done` with 0 of 4 done-when
criteria ticked, because the skill never said to tick them, and neither run
used the `reviewer` sub-agent its size called for; one skipped the review
without a word. Step 8 now ticks each met criterion and refuses `done` while
one is open (meet it, drop it with the user's agreement, or block). The
inline review threshold becomes a count, a single step and under ~30 lines,
and the review that ran is named in one line in Findings. Two runs, no
benchmark: the defects were in the text, not in a rate.)
v8.4 (2026-09-29, `/task-list-all` is the script and nothing else. The three
checks the agent used to add below the table (stale, blocked, done with open
criteria) move into `tasks.py`, so the agent no longer opens task files to
answer; the skill body says to show the output as printed. A blocked task
carries its reason as a `blocked:` frontmatter line that `/task-do` writes
and removes. `tasks.py` stops flagging 7.x specs under `.ai/changes/`;
`/framework-update` owns that migration. The table runs without a model as
`python3 .ai/agent/tools/tasks.py`. Owner's call after first use.)
v8.3 (2026-09-29, `/task-create` asks for the task type when the user did
not name it, instead of classifying it from the title or the code. The type
decides what done means, so it is the user's call, not the agent's guess.
An autonomous run still picks one and records it as an assumption. Owner's
call after first use.)
v8.2 (2026-09-28, `/task-list-all` lists live tasks only. Archived tasks
under `.ai/tasks/_archive/` are counted in the footer, not shown: the table
is the working view, and an archive that grows with every finished task
would bury it. Owner's call after first use.)
v8.1 (2026-09-28, `/framework-update` takes its migration list from the
reference's copy of the skill instead of only its own. Found on the 8.0
migration itself: a 7.1 project runs the 7.1 skill, which does not know the
spec-to-task move and says to leave specs alone. A check renders a reference
per harness and fails if the path the body names is not there. §40.)
v8.0 (2026-09-28, Pillar 2 generalized from spec-and-build to plan-and-do
for any task. `/spec` and `/build` become `/task-create` and `/task-do`; a
new read-only `/task-list-all` prints every task as a table from a script,
`tasks.py`. Tasks carry a `type` (`change`, `bug`, `investigation`, `test`)
that decides what done means, a Findings section written while the work
happens, and an Outcome. `.ai/changes/<id>/spec.md` moves to
`.ai/tasks/<id>/task.md`; `/framework-update` migrates existing specs as
`type: change`. Protocol rule 2 conditions the full-suite rule on code
having changed and adds the evidence rule for questions. No measurement:
the argument is organizational, §39.)
v7.1 (2026-09-19, two git guardrails in the protocol: never merge into the
default branch without being asked, never add a co-author trailer to a commit
message. Both are rules the repository cannot state itself and both were
violated in practice by harness defaults, so they live in every scaffold's
AGENTS.md rather than in per-project notes. No measurement; a prohibition
needs none. Same release drops the `CLAUDE.md` pointer from the claude
scaffold: Claude Code 2.1.277 reads `AGENTS.md` natively when no `CLAUDE.md`
sits in or above the project, so the pointer was a duplicate entry file.
`/framework-update` retires it from existing scaffolds unless the user
added text below the import or the session cannot load `AGENTS.md`. Three
further changes from a survey of 2026 practice (Anthropic and OpenAI
guidance, Willison's patterns, the ETH context-file study and its
follow-ups): notes grow on correction, not only on `/explore`; the two git
guardrails get a pre-tool hook, `git_guard.py`, because a rule that can be
checked deterministically should not rest on prose; both hooks now ship on
all three harnesses from one script each, since Copilot hooks
(`.github/hooks/*.json`) and Hermes shell hooks share the Claude Code wire
shape, Hermes needing a one-time dispatcher in the profile because it has no
per-repository hook registry. Both verified live the same day: Hermes 0.21.3
on a local model and Copilot CLI 1.0.86 each denied the merge and the
co-author commit, and Copilot's `agentStop` held the turn until `.ai` was
committed; and the
protocol says to run `/build` and unrelated tasks in fresh sessions, since
adherence measurably decays within a session.)
v7.0 (the framework is reduced to two pillars: durable
project knowledge that is not derivable from the repo (`.ai/notes.md` plus
the requirements block in AGENTS.md), and an opt-in spec-and-build path whose
value is the plan shown in advance. The amortization thesis is retired rather
than left open: the discovery saving it rests on was measured null across the
repo-size range, so a bigger repo is not where it lives. Eight framework
artifacts are cut (`/tidy-up`, `/import-kb`, `/import-agent`, the module map
as framework output, most of `probe.py`, the archive protocol, the `/goal`
fragment, `/build`'s drift check). §38).
v6.1 (spec and review are opt-in. The sequence benchmark
(three tasks, two arms, three replications, hidden gate tests, Sonnet 5)
found the spec-then-build-then-review chain costing +74% to +160% on later
tasks with no correctness gain and one correctness loss caused by a spec
criterion that named a single test. The default path is now: do the task,
run the whole suite, note, commit `.ai`; `/spec` and `/build` run only when
the user invokes them. The spec skill always requires the full suite green;
`/build` may record a failure as pre-existing only after checking it on a
clean checkout. §37).
v6.0 (AGENTS.md is a requirements file, not a repository
overview. The ETH Zurich evaluation of context files (Gloaguen et al., ICLR
2026 workshop) measured the mechanism §6 and §9 item 5 rest on, an
always-loaded LLM-generated digest, and found it does not help agents find
files or finish tasks while raising cost; the framework's own baseline rounds
agree. The generated section now holds build/test/lint commands, required or
forbidden tools, user-stated rules and pointers to existing docs, capped at
~300 tokens; the module map, stack and glossary move to `.ai/notes/map.md`,
read on demand; `/explore` asks the user first and skips what the repo
already documents; the explore-before-work guard of v5.10 is dropped; the
protocol text shrinks by half; the README stops claiming token economy.
§36).
v5.26 (`/import` becomes `/import-agent` on every harness,
finishing what v5.25 started: no command's name depends on where it is typed,
and the per-harness rename table is gone rather than left carrying one entry.
§35).
v5.25 (the update command is `/framework-update` on every
harness. It was `/update` on two of them and `/framework-update` on hermes,
which reserves the short name; a command whose name depends on where you type
it is worse than a longer name that is always right. §34).
v5.24 (the project name and one-line description are
recorded in the version stamp. They were the only two init answers nothing
kept: /explore overwrites the section the description is seeded into, so every
later re-render invented both and renamed the project to its directory. §33).
v5.23 (switching an existing scaffold's harness is
tooling, not a manual chore: `init-agent --harness <name>` writes the new
entry files and retires the recorded old ones into a backup, so the failure
that mattered, two live command sets disagreeing about the protocol, cannot
happen by accident. §32).
v5.22 (the large profile is removed; the framework is what
used to be the small profile, for every harness. The knowledge base, phase
docs, KB tools, ticket pipeline and second review gate are gone, and with them
the profile axis: one shape, three harnesses. Sections 1, 2, 4, 5, 13 and 20
are now history rather than current design. §31).
v5.21 (hermes as a third harness: the same skill bodies
emitted as project skills under `.agents/skills/`, with hermes frontmatter and
three commands renamed because hermes reserves `/plan`, `/import` and
`/update` for built-ins of its own. The harness axis was two-valued in code
but not in principle, so this is a third value, not a fork. §30).
v5.20 (review gates sized to the change: right-sizing now
reaches the gates, not just the pipeline entrance. A right-sized small-profile
change gets no gate at all, the large trivial path sizes both gates down to an
inline criteria check, and the reviewer brief scales depth to the artifact
with the packaging/toolchain sweep conditioned on the diff touching build
config. Sizing down is allowed, silent skipping is not).
v5.19 (copilot invocation documented correctly: prompt
files are a VS Code feature invoked as `/name` slash commands, and Copilot
CLI does not read `.github/prompts/` at all, so it gets the kickoff
sentences instead. The generated AGENTS.md section said prompt files were
VS Code only without ever saying how to run them there, and
`--bootstrap-update` told copilot users to run `/update` regardless of
surface. Docs only, no mechanism change).
v5.18 (`--bootstrap-update`: deliver the `/update` skill
into a scaffold built before it existed, and nothing else, so pre-5.14
projects can be updated by the agent instead of by a blind re-init. The stamp
it writes records `framework_version: null` on purpose. Also fixes the orphan
test, whose `-- init_agent.py` path filter went stale in 5.17 and would have
made every file added after that version unretirable. §28). v5.17 (generator
restructured: content the generator emits
moved out of string literals into `templates/` as files of their own kind
(emitted Python as `.py`, prose as `.md`, data as data), logic split into an
`agentgen/` package, `init_agent.py` reduced to the CLI. Slots use
`string.Template` because emitted content is full of literal braces. The two
axes keep branching in code, with conditional prose as fragment files, so no
document is duplicated per variant. Verified by byte-identity across all four
variants: the emitted scaffold is unchanged from v5.16. §27). v5.16 (/tidy-up:
a bounded hygiene sweep over the host code
in four passes (dead code removed with evidence, obsolete files proposed but
never deleted, overlong comments compressed to 1-2 lines without losing the
knowledge in them, em dashes rewritten out of prose), gated on a green
test/lint baseline captured up front and forbidden from changing behavior;
both profiles, both harnesses. The generator's own templates were swept for
the em-dash rule they already stated. §26). v5.15 (/import: migrate a whole
existing `.ai/` folder
(older framework version or foreign agent layout) into the current structure,
carrying both the knowledge and the lifecycle state (tickets, tasks, plans,
decisions, notes; small profile: in-flight changes) that /import-kb drops;
both profiles, both harnesses. Distinct from /update, which upgrades a
scaffold this framework already stamped; /import handles unstamped or foreign
folders. §25). v5.14 (agent-driven framework update: `init_agent.py`'s
`-u/--update` is removed and replaced by an `/update` skill in both profiles
and both harnesses. Scaffolds now carry a version stamp
(`.ai/agent/framework.json`: framework version, profile, harness, and the
list of framework files that version emitted); the CLI keeps two flags that
only serve the skill, `--detect` and `--emit-reference DIR`. Updating is a
merge, and merges need judgment a stdlib scaffolder does not have. §24).
v5.13 (worker sub-agents removed: the `code-worker` and
`explore-helper` definitions, their dispatch guidance in the phase docs and
the small-profile skills, and the runbook's W arm are gone. Two reasons: the
dispatch instructions were harness-neutral text while the agent definitions
were claude-only, so copilot scaffolds told the agent to dispatch to
sub-agents that do not exist; and the one W-arm measurement showed the
delegation claim failing (+35% total tokens, +43% cost at an equal gate).
§23 rewritten as the rejected-design record). v5.12 (worker sub-agents on a
mid-tier model: optional scaffolded `code-worker` and `explore-helper` agent
definitions pinning `model: sonnet` in frontmatter; removed in v5.13).
v5.11 (/goal as a documented autonomous-dispatch mode:
AGENTS.md now names /goal explicitly in both profiles, pointed at the same
done-bar /build (small) or /implement (large) already defines rather than a
new one, paired with the existing stall/escalation rule; claude-harness only,
§22). v5.10 (explore-freshness guard: small-profile Protocol item 1
now tells the agent to check whether the Project Context digest is still an
unpopulated stub and run /explore first if so, instead of proceeding on a
stale/wrong one-liner; notes.md stub explicitly sanctions cross-repo/path
pointers as an existing genre, while restating that architecture/module-map
content stays out of notes.md, §21). v5.9 (automatic profile selection:
init-agent counts source
LOC and applies the ~10k boundary to pick small vs large when --size is omitted
or 'auto'; explicit --size still wins,
§20). v5.8 (small-profile notes hub: .ai/notes.md may become a
linked index with .ai/notes/<topic>.md leaves once it grows past ~1-2 screens,
guidance-only, §19). v5.7 (project-context freshness: end-of-change refresh of
the AGENTS.md generated digest via probe.py, LOC-only drift excluded; ecosystem-
neutral correctness-criteria examples; §18). v5.6 (harness-mechanism pass after
a best-practice review: skills locked to manual invocation, path-scoped rules
generated from conventions nodes, parallel-ok task marking, /goal as middle
verification tier, prune test in KB lint, §17). v5.5 (more determinism offloaded from the
model to scripts/
hooks: probe.py repo inventory, auto-regenerate INDEX on manifest write,
check_stale at session start, §16). v5.4 (/import-kb: transform an existing
knowledge base of any structure into .ai, §15). v5.3: durable task cursor +
running-memory notes.md in
both profiles, backported from the legacy agents (§14). v5.2: size profiles, a
stripped-down small profile for codebases ≤10k LOC (§13). v5.1: model choice
fully delegated to user (§3); v5: standards + deterministic enforcement (§12).

---

## 1. Knowledge Base

### Layout

```
.ai/knowledgebase/
├── manifest.yaml            # machine-readable index (source of truth)
├── INDEX.md                 # generated human view, read-only
├── architecture/
│   ├── overview.md          # hot
│   └── module-<name>.md
├── conventions/
│   ├── code-style.md        # hot
│   ├── testing.md
│   └── git-workflow.md
├── domain/
│   ├── glossary.md          # hot
│   └── <context>.md
├── infra/
│   ├── build.md
│   └── ci-cd.md
├── decisions/               # ADRs, append-only
│   └── NNNN-<slug>.md
├── references/              # external references: 1 node per source
│   └── <name>.md            # origin, fetched, pinned, usage notes
└── tasks/
    ├── <ticket-id>/
    │   ├── ticket.md        # original + Q&A answers
    │   ├── plan.md          # task index: order, deps, status, kb-commit
    │   ├── NN-<slug>.md     # one file per task, self-contained
    │   └── kb-delta.yaml    # accumulated KB patches
    └── _archive/            # finished tickets, invisible to agent

.ai/tickets/                 # inbox: <ID>-<slug>.md, via /add-ticket or
                             # dropped in by user; /plan consumes into tasks/

.ai/external/                # raw external material (clones, doc dumps);
└── <name>/                  # search territory, never load territory;
                             # excluded from .ai git (re-fetchable)
```

### External references

Two layers: raw copy in `.ai/external/<name>/` (clone/copy via
`add-reference`), curated node `references/<name>.md` in KB (origin, fetched
date, pinned version, consult-for notes). Agent loads node only; raw copy =
targeted search, sub-agent where available, never bulk-load. Staleness
visible via `fetched`/`pinned` frontmatter.

### Node format

```yaml
---
id: architecture/module-payment
summary: Payment processing, Stripe adapter, idempotency handling
tags: [payment, stripe, api]
covers: ["src/payment/**"]
tier: hot|cold
updated: 2026-06-11
related: [domain/billing]
---
```

Rules: node cap ~1500 tokens, larger → split + cross-link. Single source of
truth, never duplicate. `summary` + `covers` enable load decisions without
content loads.

### manifest.yaml over prose index

Flat node list (id, path, summary, tags, covers, tier, updated) + budgets.
Agent parses, not reads → deterministic matching. INDEX.md = generated human
view.

### Navigation protocol (every turn)

1. Parse manifest.yaml (always)
2. Hot tier: embedded in AGENTS.md generated section (see §6), never loaded
   separately
3. Two-stage retrieval: (a) `covers` globs + tag match, exact; (b) on miss
   only, keyword score over summaries. No embedding index below ~200 nodes
4. Budget (soft): target ≤4 cold nodes / ≤6000 tokens per task; `related`
   ≤1 hop. Overrun allowed: state reason in one line, proceed. Recall before
   precision: never skip needed context to satisfy budget
5. Never load `tasks/_archive/`
6. Exploration + review in sub-agent contexts where harness supports it (§2)
7. INDEX.md = generated by `gen_index.py` from manifest, never edited;
   PreToolUse hook blocks direct writes (claude harness)
8. Compaction: instruct harness to preserve current ticket id, task file
   path, modified-files list, build/test commands. v4 items dropped as not
   model-actionable in any current harness: session node cache, used/unused
   marking, tool-result clearing (§12)

## 2. Phases

### Phase 1: Initialization
- Deterministic inventory first: `probe.py` (host SHA, language mix, detected
  build/test/lint commands, module map + LOC, dep manifests, entry points) →
  seed mechanical project-context fields free, sample by its map (§16)
- Sampling, no full scan: per module entry points, public API, tests
- Exploration in isolated sub-agent contexts where harness supports it; each
  returns condensed summary ≤2000 tokens to main context. Keeps raw file
  dumps out of the synthesizing context
- Bottom-up: module nodes → overview → update manifest; INDEX auto-regenerates
  (PostToolUse hook runs `gen_index.py` on manifest write, §16)
- Q&A for non-derivable knowledge (domain terms, unwritten rules)
- Once build/test/lint commands known: offer project-specific Stop hook
  (lint/tests on turn end) → "done = checks pass" deterministic (claude)
- Store host-repo commit SHA → re-init = diff only
- Coverage report: unread areas (lazy init in Phase 4)

### Phase 2: Planning
- Ticket source: `.ai/tickets/` inbox (via /add-ticket or user-dropped md
  file); agent creates `tasks/<id>/` from it, deletes inbox file
- Interactive Q&A until acceptance criteria unambiguous; answers → ticket.md
- One file per task `NN-<slug>.md`: goal, criteria, affected files, pre-bound
  KB node ids (**warm start**), expected signatures/interfaces, test
  skeletons
- plan.md = thin index (order, deps, status) + `kb-commit` frontmatter: .ai
  commit SHA the plan was built against. Drift baseline; replaces v4
  per-node content hashes (git diff = deterministic, model-computed hashes
  were not)
- Pre-binding = warm start, not contract: implementation starts from bound
  nodes/files; bounded extra discovery allowed (≤5 targeted searches) before
  `missing-context` escalation. Rationale: agentic search is cheap and
  improving; baking the planner's context guess into a hard contract trades
  brittleness for tokens
- Trivial path: ticket fits one sentence / 1-2 files → skip Q&A, single task
  file, sign-off = one line, and both review gates size down to an inline
  criteria check (§29). Ceremony must not exceed the task (SDD field
  reports: planning overhead > savings on small tasks)
- Plan-review gate before Phase 3: adversarial review in fresh context
  (reviewer sub-agent; fallback: user review) vs acceptance criteria, then
  user sign-off on plan.md. v4 self-review dropped: producing context grades
  its own work. Weak plan poisons every downstream task

### Phase 3: Implementation
- Loads only: plan.md + current task file + its nodes/files; bounded extra
  discovery ≤5 targeted searches
- Drift check, diff-aware: `git -C .ai diff <kb-commit> -- <node path>` per
  pre-bound node. Empty → proceed. Delta not touching task's
  interfaces/criteria → proceed on fresh content. Touching them → re-plan
  affected task only. Never silent-proceed on stale context, never full
  re-plan on cosmetic drift
- Done = tests green + lint + `status: done` + patch in kb-delta.yaml
  (op: update/create/split, node, diff)
- Ticket review gate: after last task, review of full diff vs acceptance
  criteria, sized to the ticket (§29). Trivial path → inline check, no
  sub-agent; otherwise fresh-context review (reviewer sub-agent). Fix
  correctness gaps, ignore style-only findings; record `reviewed: <date>` in
  plan.md
- Typed escalation:
  - missing-context → bounded discovery + reload KB (1 hop, sub-agent where
    available), then ask user
  - ambiguity → ask user
  - test-fail ×2 → stop; fresh-context critique of approach or re-plan the
    task; never a third blind attempt
  Never improvise around blockers

### Phase 4: Operational
- No fixed workflow; protocol + budgets still apply
- Post-merge + session start: `check_stale.py` flags nodes whose `covers`
  globs match commits since `updated`

## 3. Model choice (revised v5.1)

Model choice belongs to the user, via harness controls (`/model`,
`opusplan`, sub-agent `model:` frontmatter). The framework is
model-agnostic: no routing machinery, no model instructions in generated
docs.

- v4 per-task complexity routing dropped in v5: harnesses route per
  sub-agent/session, not per task file; routing machinery cost > savings at
  this scale; outcome data to tune it never existed
- v5 "strong main loop" default guidance dropped in v5.1: restates or
  fights a user decision the harness already owns; always-on tokens, zero
  behavior change
- Kept as property, not instruction: self-contained task files +
  fresh-context review gates are what make cheap-execution modes (e.g.
  opusplan: plan on strong model, implement on cheap one) viable. Stated in
  README, not in agent docs. Direction stays asymmetric: never plan on the
  weak model
- v5.12 instantiated that property once with two scaffolded worker
  definitions pinning `model: sonnet`; v5.13 removed them (§23). The rule
  stands as before: routing is the user's, via harness controls, and the
  framework ships no tier pin of its own

## 4. Ticket lifecycle

- Status in frontmatter (`planned|in-progress|done|blocked`), never folder
  names → stable paths for pre-bound refs + kb-commit diffs
- Intake: ticket md lands in `.ai/tickets/` inbox (/add-ticket or by hand);
  /plan converts to `tasks/<id>/`
- Ticket done: kb-delta applied → user prompts agent to archive; agent
  verifies all tasks `done` + kb-delta applied, moves to `tasks/_archive/`,
  commits .ai (no CLI command; rules in instructions file)
- Archive invisible to agent; knowledge lives on in KB/ADRs

## 5. Living KB

- KB delta = mandatory final step of every implementation task, structured
  patch (kb-delta.yaml), not free text
- Declarative auto-apply: metadata/`covers` = auto, structural = review gate
- Staleness: `check_stale.py` compares `covers` globs vs host commits since
  `updated` (exit 1 on findings → CI-wirable); run post-merge + operational
  session start
- Compaction job: enforce node cap, merge fragments, prune dead nodes
- Ownership: automation flags, human decides. Named KB owner + fixed review
  cadence (monthly lint: obsolete rationale, dead nodes, drifted `covers`,
  and the prune test — any rule the agent already follows unprompted gets
  deleted; always-on instruction bloat is why real rules get ignored).
  Neglected KB = confident wrong context, worse than no KB
- Telemetry: cut in v5. v4 specified two layers (token cost + outcomes)
  with no collection mechanism; spec without mechanism = dead weight.
  Re-add together with collection hooks when needed; outcome data stays the
  precondition for any future routing automation (§3)

## 6. AGENTS.md as hot-tier transport (decision, revised v5)

Canonical instructions file = AGENTS.md (vendor-neutral standard, read
natively by Copilot and most current harnesses). Claude harness gets a
one-line CLAUDE.md pointer (`@AGENTS.md` import); copilot-instructions.md
dropped. Hot-tier content written into AGENTS.md as **generated section**,
since it is loaded every session anyway:

```markdown
<!-- BEGIN GENERATED:project-context (source: hot-tier nodes) -->
<!-- END GENERATED:project-context -->
```

- Source stays KB (hot nodes); section = build artifact, regenerated by init,
  kb-delta apply on hot nodes, compaction
- Section budget ~1500 tokens, condensed: one-liner, stack, build/test
  commands, top conventions, module map 1 line/module, core glossary
- Protocol change: never load hot tier separately
- No manual duplication → staleness solved by regeneration, not discipline
- Re-init recovers an existing generated section (also from legacy CLAUDE.md
  scaffolds) instead of reverting it to the stub

Regeneration of the section is an agent duty (Phase 1 + after hot-node
kb-delta), not a CLI feature: the CLI only scaffolds.

## 7. AGENTS.md split: phase docs on demand + skills (decision, revised v5)

AGENTS.md (incl. imports) is loaded eagerly → split only pays if it changes
what gets loaded. Phases are mutually exclusive per session → on-demand.

- AGENTS.md = core, cap 2000 tokens: KB protocol, budgets, ticket layout,
  right-sizing rule, generated project-context section, phase pointer table
- `.ai/agent/phases/{init,planning,implementation}.md`: single source of
  truth, loaded only at phase start. Operational = no doc, core protocol is
  default
- Escalation + KB maintenance rules live in implementation.md
- Entry points = Agent Skills (implemented v5): each workflow packaged as
  `.claude/skills/<name>/SKILL.md` (open SKILL.md standard; frontmatter
  name + description ~30-50 tokens at startup, body loaded on trigger) →
  progressive disclosure enforced by harness, not by model obedience.
  Skill bodies stay thin pointers to the phase docs. Copilot harness: same
  bodies as `.github/prompts/*.prompt.md` (VS Code)
- Mitigation "implementing session skips phase doc": plan.md frontmatter
  carries `read-first: .ai/agent/phases/implementation.md` → instruction
  comes from artifact it must load anyway; also covers skill-less harnesses
  (Copilot CLI kickoff lines)
- Net: ~50-60% of agent instructions out of always-on context; active phase
  doc ~400-600 tokens on demand

## 8. Language + style policy (decision, revised v4)

- All agent docs, KB nodes, tickets, plans: English. Best-trained model
  language, denser tokenization vs German, no mixed-language context
- Two registers:
  - **Normative text** (KB protocol, phase docs, escalation rules,
    acceptance criteria): plain imperative English, complete sentences.
    Compression research validates terse *content*, not terse *instructions*;
    the cost-efficient executor is exactly the model class most likely to
    misread ambiguous fragments. ~500 tokens saved per doc < cost of one
    misread rule
  - **KB content** (nodes, summaries, tickets, glossaries): telegraphic.
    Drop articles/filler, symbols (→ = ≤ ×) over words. ~20-30% token
    reduction, zero information discarded
- Exceptions kept verbatim everywhere: identifiers, paths, commands, code
  blocks, frontmatter keys
- Validation path: A/B same ticket in both styles, compare escalation +
  re-plan rates (a two-register A/B spec was drafted for v5.6 but never run; a
  spec'd-but-never-run validation is the same dead weight telemetry was culled
  for)

## 9. Token efficiency stack (summary)

1. Manifest + frontmatter summaries → load decisions without loads
2. Node caps + dedup → bounded worst case
3. Plan pre-binds nodes/files + `kb-commit` baseline → warm start,
   near-zero discovery, deterministic drift check
4. Single task files → only current task in context
5. Hot tier via AGENTS.md generated section
6. Slim core AGENTS.md + on-demand phase docs (Agent Skills / prompt files)
7. Incremental init via commit SHA, sampling + sub-agent isolation over
   full scan
8. Typed escalation + fresh-context review gates (plan + ticket diff)
9. Two-register language: plain instructions, telegraphic content
10. Soft budgets with declared overruns; right-sizing: no ticket ceremony
    below ticket scale
11. Deterministic tools + hooks over protocol prose (probe inventory,
    gen_index, check_stale; PreToolUse/PostToolUse/SessionStart/Stop hooks)

## 10. v4 revision notes (2026-06-11)

Research-informed pass (Anthropic context engineering + Agent Skills, KB-for-
coding-agents literature, plan-then-execute studies). Changes vs v3:

1. Pre-binding demoted: contract → warm start; bounded discovery (≤5
   searches); diff-aware hash-drift handling instead of re-plan-on-any-drift
2. Budgets hard → soft: declared overruns, recall before precision
3. Sub-agent isolation for exploration, ≤2000-token summaries back
4. Session hygiene: tool-result clearing, node-cache invalidation on
   compaction
5. Language policy split into two registers (plain normative / telegraphic
   content)
6. Agent Skills packaging for phase docs; AGENTS.md portability
7. Plan-review gate before implementation
8. Telemetry extended with outcome layer; KB ownership + review cadence

Unchanged: KB layout, manifest navigation, hot/cold tiers, hot tier via
CLAUDE.md generated section, kb-delta, staleness CI, ticket lifecycle +
archive.

## 11. Tooling update (2026-06-12)

CLI reduced to a single interactive scaffold command (`init-agent`, no
subcommands, no parameters; prompts: name, description, harness
claude/copilot, overwrite-confirm replaces --force). Lifecycle ops moved
from CLI to agent:

- ticket intake: `.ai/tickets/` inbox (`<ID>-<slug>.md`), filled via
  /add-ticket or by hand; /plan consumes inbox → `tasks/<id>/`
- references: /add-reference (clone/copy → `.ai/external/`, node + index
  updates by agent) or material placed by hand, node created on discovery
- archive: user prompts agent; rules in instructions file, no command
- .ai commits: agent duty (protocol rule), CLI commits only at init;
  `git -C .ai` pre-allowed in the permission list

Rationale: every lifecycle op is agent-executable instruction-following;
keeping it in the CLI duplicated logic the agent must know anyway and
forced parameter ceremony on the user. Slash commands /explore, /add-ticket,
/plan, /implement, /add-reference, /import-kb (§15); harness copilot gets the
same as .github/prompts/*.prompt.md.

## 12. v5 revision notes (2026-06-12)

Implementation pass: open standards + deterministic enforcement over
protocol prose. Changes vs v4:

1. AGENTS.md = canonical instructions file; CLAUDE.md = `@AGENTS.md`
   pointer (claude harness); copilot-instructions.md dropped (Copilot reads
   AGENTS.md natively)
2. Slash commands → Agent Skills (`.claude/skills/<name>/SKILL.md`, open
   standard); copilot keeps VS Code prompt files; phase docs remain single
   source of truth in `.ai/agent/phases/`
3. Enforcement via hooks (claude): PreToolUse blocks direct INDEX.md edits;
   Stop blocks turn end on dirty `.ai` repo; Phase 1 offers a
   project-specific lint/test Stop hook once commands are known
4. Review gates adversarial: `reviewer` sub-agent (fresh context, read-only
   tools) replaces v4 self-review at the plan gate; new ticket diff-review
   gate at the end of Phase 3
5. Drift detection: per-node content hashes → plan.md `kb-commit` +
   `git -C .ai diff` (deterministic, pre-allowed command)
6. Deterministic KB tools in `.ai/agent/tools/`: gen_index.py (INDEX.md
   from manifest), check_stale.py (covers globs vs commits since `updated`,
   CI-wirable exit code)
7. Model routing dropped entirely (§3): v5 cut complexity-tag routing,
   v5.1 (same day) cut the remaining "strong main loop" guidance and the
   AGENTS.md Model Use section. Model choice = user's, via harness controls;
   framework model-agnostic
8. Telemetry spec cut (§5): no mechanism existed, spec without mechanism is
   dead weight
9. Right-sizing: trivial path in Phase 2; one-sentence single-file changes
   need no ticket at all
10. Always-on protocol pruned: non-model-actionable v4 items removed
    (session node cache, used/unused marking, tool-result clearing);
    compaction-preserve instruction added
11. init never overwrites hand-filled KB content (nodes, manifest, INDEX);
    existing generated project-context section recovered on re-init, also
    from legacy CLAUDE.md scaffolds
12. Decision (owner, 2026-06-12): `.ai` stays a private nested repo, no
    remote, no host-repo sharing. Team-shared KB rejected

Unchanged: KB layout, manifest navigation, hot/cold tiers, kb-delta,
staleness model, ticket lifecycle + archive, two-register language policy.

## 13. Small-project profile (2026-06-24, v5.2)

`init-agent` now prompts for a size profile. **large** (default) is the full
framework above. **small** targets codebases up to ~10k LOC, where there is no
context scarcity to manage: the whole source is cheap to read on demand. The
profile is a strict subset — same private nested `.ai` repo, same AGENTS.md
transport, same review-gate idea — with the large-codebase machinery removed.

Design rule: keep what pays even when the code is small; drop everything whose
only job is rationing context or tracking drift in a large KB. Rationale:
current best practice favors just-in-time retrieval (keep lightweight
identifiers, read the real source via tools) over a pre-loaded knowledge store,
and "do the simplest thing that works"; at ≤10k LOC the agent re-reads the
source faster than it can maintain a synced index, so the index's upkeep cost
(drift, staleness, commits, regeneration) exceeds its value.

### Kept
- AGENTS.md as canonical, always-on instructions (host repo) + CLAUDE.md
  pointer; build/test/lint commands are the highest-ROI content.
- Generated `project-context` section in AGENTS.md as the only knowledge store
  (arch summary, module map, glossary, commands), filled by `/explore`.
- Private nested `.ai/.git` repo + the `ai_repo_clean` Stop hook (owner
  decision, 2026-06-24: same privacy model as large).
- `reviewer` sub-agent as a single final-diff review gate before done.
- Read-only permission allow list; right-sizing rule + trivial path;
  two-register language; dual skill/prompt rendering from one spec list.

### Simplified
- KB (manifest, INDEX, hot/cold nodes, two-stage retrieval, per-task budgets,
  `related` hops) → the AGENTS.md generated section, plus ad-hoc
  `.ai/<topic>.md` only if a project genuinely needs it.
- Ticket pipeline (inbox → ticket.md → plan.md → NN-task.md → kb-delta.yaml,
  two gates) → a single `.ai/changes/<id>/spec.md` (goal + acceptance criteria
  + task checklist) and one gate.
- Four phases + on-demand phase docs + skills-as-pointers → three
  self-contained skills (`/explore`, `/spec`, `/build`); instructions inlined,
  still loaded on trigger by the harness (progressive disclosure kept,
  indirection dropped).
- Living KB + ADRs (`decisions/`) → one append-only `.ai/notes.md` (structured
  note-taking).
- Five skills → three.

### Dropped (solving a non-problem at this scale)
- manifest.yaml, INDEX.md, hot/cold tiers, two-stage retrieval, per-task
  token/node budgets, `related`-hop limits.
- Drift detection (`kb-commit` + per-node `git diff`), staleness scanning
  (`check_stale.py`), `gen_index.py`, the `protect_generated` hook (no
  generated INDEX to protect).
- `kb-delta.yaml` structured patches; the plan-review gate (keep only the final
  review); the `add-ticket` and `add-reference` skills (external material:
  clone into `.ai/external/` ad hoc and note it in `notes.md`).

### Trade-offs
- Retained ceremony: the `.ai` commit discipline + Stop hook is the one piece of
  large-profile operational tax kept, by owner decision.
- One gate not two: a poor task decomposition can slip past planning; mitigated
  by small task counts and the final diff review. Plan-review is the upgrade
  path.
- Graduation is not automatic: crossing ~10-15k LOC means re-running init as
  large (hand-filled content is preserved) and hand-migrating `notes.md`/specs
  into KB nodes; the artifact shapes differ. No auto-migrator. The crossing is
  at least *flagged* since the §18.1 refresh: probe.py prints a code-only LOC
  total, and small `/build` proposes the re-init once it passes ~10k (proposal
  only, migration stays a deliberate user decision).

### Unchanged across profiles
Private `.ai` repo model, AGENTS.md generated-section transport, the
fresh-context review idea, two-register language, the right-sizing rule, and
the single-interactive-scaffold CLI (now with one extra size prompt).

## 14. Backport from legacy agents (2026-06-26, v5.3)

Comparison against an earlier family of Copilot-style project agents (the
direct conceptual ancestor: same private nested `.ai` repo, same
ticket→task→implement pipeline) surfaced two things they did better, both now
backported. Everything else they had — context rationing, drift/staleness,
review gates, sub-agent isolation, single-source instructions — this framework
already does better or equivalently, so only these two were taken.

### 14.1 Durable task cursor (`.ai/.current`)

Problem: resume across *new sessions*. v4 dropped an explicit session cursor as
"not model-actionable", but that judgment was about an in-memory node cache, not
a file. The legacy agents kept a dead-simple on-disk pointer (`.ai/tasks/.current`
= JIRA id + task id) that survived session boundaries with zero machinery. The
framework's only resume mechanism was a *compaction-preserve instruction* — a
hint to the harness, lost on a cold start.

Decision: a `.ai/.current` cursor file in both profiles, recording the active
ticket/change id, the current task/spec file, the modified-files list, and the
date. Read at session start (offer to resume); updated on task start/finish;
deleted when the work item is done.

- **Gitignored, not tracked.** It is per-checkout working state, not shared
  knowledge: resuming always happens in the same working copy, so on-disk
  persistence is enough, and tracking it would churn KB history and force a
  commit on every cursor update. Added to `.ai/.gitignore` next to `external/`.
- **Does not fight the Stop hook.** `ai_repo_clean` runs `git -C .ai status
  --porcelain`; an ignored file never appears, so the hook stays quiet.
- It is the on-disk backup of exactly what the compaction-preserve item asks
  the harness to keep; the two are complementary, not redundant.

### 14.2 Running memory for runbooks/gotchas (`.ai/notes.md`, large profile)

Problem: the highest-value knowledge the mature legacy agents carried was
*procedural/operational* — validation loops, CI failure modes (e.g. stale
`workflow_dispatch` keys → HTTP 422), merge-order rules. The large profile's
node taxonomy (architecture/conventions/domain/infra/decisions/references) has
no natural home for this volatile, list-shaped knowledge; it would either bloat
a curated node or be lost.

Decision: give the large profile the same `.ai/notes.md` the small profile
already had, rather than invent a new typed node category (the smaller change,
and the graduation path already assumes `notes.md` exists). It is the **volatile
layer**: read at session start, appended telegraphically as gotchas surface;
anything durable and structural is **promoted into a curated node via
kb-delta.yaml**. Curated nodes remain the single source of truth; `notes.md` is
scratch/operational memory beside them. The stub text now names runbooks and CI
quirks explicitly so the genre is obvious in both profiles.

### Unchanged
KB layout and protocol, manifest navigation, hot/cold tiers, kb-delta, drift
and staleness model, ticket lifecycle + archive, review gates, two-register
language, size profiles, single-interactive-scaffold CLI.

## 15. Knowledge-base import (2026-06-26, v5.4)

`/import-kb <source>` ingests an *existing* knowledge base of arbitrary
structure — a docs/wiki folder, a Confluence/Markdown export, a README-heavy
repo, or a legacy `.ai/` (e.g. the ancestor agents' `docs/` chapters) — and
transforms it into the framework's own shape. The transform is the model's job,
not a parser's: the input has no fixed schema to match ("regardless of
structure"), so a deterministic importer cannot exist. The skill encodes a
read → classify → transform protocol; the model supplies the understanding.

### Why a skill, not a tool
The input layout is unknown by definition, which is exactly what an LLM is for:
read heterogeneous material, infer what each piece *is*, map it onto the target
taxonomy. A script could only handle one known layout. The deterministic parts
the skill reuses are the ones the framework already owns: `gen_index.py` for
INDEX, the manifest format, the node frontmatter schema.

### Protocol (both profiles)
1. **Survey, don't bulk-load.** List the source tree, sample entry/index/README
   files, run the survey in a sub-agent where available, return a condensed map.
   The source may be huge; it never enters the synthesizing context wholesale.
2. **Classify** each piece of content into the target shape.
3. **Transform, don't copy.** Synthesize into telegraphic content, dedup against
   existing knowledge (merge, never a second source of truth), record provenance
   (source path/URL) so the import is auditable.
4. **Wire up + commit.** Regenerate the dependent artifacts, commit `.ai`, report
   a source→target mapping and list the unclassifiable remainder for the user.

### Profile differences
- **Large**: targets are KB nodes under the six categories; operational
  gotchas/runbooks route to `notes.md` (§14). Output is full nodes with
  frontmatter and `covers` globs matched to real code paths; `manifest.yaml` +
  `INDEX.md` + the project-context section are regenerated.
- **Small**: no node store; the skill distills stable facts into the AGENTS.md
  project-context section and routes the rest to `notes.md`. Large bodies worth
  only searching are cloned into `.ai/external/` and noted, not inlined. The
  small profile now carries four skills (`/explore`, `/spec`, `/build`,
  `/import-kb`).

### Boundary vs /add-reference
`/import-kb` *absorbs and transforms* curated knowledge into the KB (the source
can then be retired). `/add-reference` *keeps raw external material* under
`.ai/external/` as search territory and registers only a thin pointer node, no
transformation. Code or upstream docs you only want to search later go through
add-reference; a prior team's documentation you want to *become* your KB goes
through import-kb. The skill body states this distinction so the agent chooses
correctly.

## 16. More determinism offloaded to scripts/hooks (2026-07-01, v5.5)

Continues §12.6's "deterministic tools + hooks over protocol prose". Three
mechanical jobs that were LLM-driven (or standing prose instructions the model
had to remember) become scripts/hooks. Motive: save tokens on the most
expensive work and make the outcome reproducible. `ai_repo_clean` stays
unchanged — content commits keep model-written, meaningful messages (owner
decision; auto-templated messages rejected).

1. `probe.py` (`.ai/agent/tools/`, both profiles): read-only, stdlib-only repo
   inventory. Uses `git ls-files` (gitignore-aware, deterministic; `os.walk`
   fallback). Prints compact, stable-sorted Markdown to stdout: host commit
   SHA, language mix, detected build/test/lint commands (package.json scripts,
   Cargo/Go/Python/Ruby manifests, Makefile targets, ROS 2/colcon via
   package.xml, vcstool .repos, Snapcraft, Debian packaging via
   debian/control, Docker/Compose, GitHub Actions workflow list), module map
   with files + LOC, dependency manifests, entry-point candidates. First step of Phase 1
   (large) and `/explore` (small): the mechanical `project-context` fields are
   seeded from it, not re-derived by the model, and its map drives sampling.
   Biggest single lever — the initialization phase is the costliest.
2. Auto-INDEX (PostToolUse hook `regen_index.py`, large only): runs
   `gen_index.py` whenever `manifest.yaml` is written, always exit 0
   (non-blocking; the write already succeeded). Replaces the standing prose
   rule "after a manifest change, run gen_index". `protect_generated` (blocks
   hand-edits of INDEX.md) stays. On non-claude harnesses (no hook) the phase
   docs still tell the agent to run `gen_index.py`.
3. check_stale at session start (SessionStart hook, large only): runs the
   existing `check_stale.py` with `|| true` (neutralizes its CI exit code);
   its stdout enters the session as context. Replaces the prose "run it at the
   start of operational sessions". Manual run kept for after a merge / non-
   claude harnesses.

Not in scope (future iterations, tracked): `apply_delta.py` (declarative
metadata/covers auto-apply), `drift.py` (bundle the per-node drift diffs),
archive + ADR-number helpers. Node content, classification, planning, and the
review gates stay with the model — that is genuine judgment, not mechanism.

## 17. Harness-mechanism pass (2026-07-02, v5.6)

Web-research review of the concept against mid-2026 best practice (Anthropic
context engineering, Claude Code best-practices docs, AGENTS.md/AAIF status,
SDD field reports) confirmed the foundations and surfaced newer harness
features the framework predated. Theme continues §16: replace protocol prose
with harness mechanism as harnesses grow them. Copilot support is unchanged
throughout — every claude-specific mechanism is additive, with the manifest
protocol as the fallback on other harnesses.

1. **Skills locked to manual invocation.** Every scaffolded skill is a
   user-sequenced pipeline step with side effects (KB writes, code changes,
   `.ai` commits); `disable-model-invocation: true` prevents the model from
   auto-triggering them mid-conversation (e.g. starting /plan on sight of a
   ticket). `argument-hint` added for discoverability. Copilot prompt files
   have no such field and are unchanged.
2. **Path-scoped rules as generated artifacts (claude, large).** Cold
   `conventions/*` nodes with non-empty `covers` render to
   `.claude/rules/<id>.md` with `paths:` frontmatter via `gen_rules.py`:
   the harness now injects the convention deterministically when matching
   files are touched, instead of the model remembering the manifest lookup.
   Same pattern as the AGENTS.md generated section: node = source of truth,
   rule = build artifact (marker line, stale-file cleanup). The
   regen hook fires on conventions-node and manifest writes;
   `protect_generated` blocks edits to marked rule files (hand-written
   rules stay editable). Hot nodes excluded (already in the AGENTS.md
   section — no duplication); nodes without `covers` stay manifest-loaded.
3. **Parallel-ok task marking.** `/plan` sets `parallel: ok` on tasks with
   no `depends` and no overlapping affected files; plan.md's table gains a
   Parallel column. implementation.md defines the dispatch constraints:
   one self-contained task file per session, `.ai` single-writer (only the
   coordinating session commits), worktree caveat (gitignored `.ai/` is not
   carried over), review gate stays serial on the combined diff. Zero
   machinery — the self-contained task files already made this safe; the
   protocol now says so. Harness-neutral.
4. **/goal as middle verification tier (claude).** The Phase-1 verification
   offer now names the session-scoped `/goal` condition as the lighter
   alternative to the scaffolded lint/test Stop hook. Both profiles.
5. **Prune test in KB lint.** Monthly lint + implementation.md gain the
   canonical deletion criterion for standing instructions: if the agent
   already behaves correctly without a rule, delete it (§5).
6. **README corrections.** The `ai_repo_clean` "never lost" claim softened
   (Claude Code overrides a Stop hook after repeated consecutive blocks;
   protocol rule = backstop); auto permission mode noted as the
   low-maintenance interactive alternative to the scaffolded allowlist.
7. **Two-register A/B made runnable.** §8's validation path was given a
   benchmark spec instead of a standing intention (later removed unrun when the
   benchmarks were consolidated to a single fixed runbook).

Rejected in this pass: subdirectory-CLAUDE.md pointers for module nodes
(weaker duplicate of item 2), embedding retrieval (still wrong below ~200
nodes), auto-migrating the allowlist to auto mode (allowlist stays default:
deterministic, works headless).

Unchanged: KB layout, manifest navigation, hot/cold tiers, kb-delta, drift
and staleness model, ticket lifecycle + archive, review gates, two-register
language, size profiles, model-agnosticism, single-interactive-scaffold CLI.

## 18. Project-context freshness + ecosystem-neutral criteria (2026-07-02, v5.7)

Two small refinements after v5.6, both surfaced and then validated by benchmark
runs (the multi-eco set and the sonnet5-medium regression cell). No new
machinery; both harden existing behavior.

1. **End-of-change project-context refresh.** The always-loaded AGENTS.md
   `GENERATED:project-context` digest had no regenerator outside `/explore` and
   re-init: INDEX.md and path-scoped rules auto-regenerate via hooks (§16.2,
   §17.2), but the digest could silently drift once implementation changed a
   build command or the module map. Fix: a bounded step at the end of small
   `/build` and large implementation.md — re-run `probe.py`, compare its
   build/test/lint commands and module map against the digest, and refresh the
   section only for a changed command or a new/removed/renamed module. A bare
   LOC delta on an existing module is explicitly **not** actionable (that
   exclusion came from the sonnet5-medium run, where a +26-line file tripped a
   false rewrite). Deliberately a model-run step, not a hook: `probe.py` output
   is the mechanical input, but deciding whether the curated human-readable
   digest needs an edit is judgment. Validated: fired and caught a real
   new-`make deb`-target drift in the sonnet5-medium-small-v2 cell, and fired
   5/5 in the multi-eco round while correctly staying quiet on LOC-only drift.
   One graduation exception rides this step (2026-07-04): probe.py prints a
   code-only `Code LOC` total, and if it exceeds ~10k in a small-profile
   project, `/build` proposes re-initializing as large (§13). Threshold-based,
   no stored snapshot needed; proposal only, never an automatic migration.
2. **Ecosystem-neutral correctness criteria.** The `/spec` skill and large
   task-file format ask for acceptance criteria that name the relevant
   linter/policy check (§12, ecosystem correctness). The example list named
   only `lintian` and `clippy` — the two ecosystems benchmarked at the time
   (Debian packaging, Rust) — biasing agents on other stacks toward
   benchmark-flavored criteria. Diversified to `eslint, mypy/ruff, clippy,
   shellcheck, lintian, schema validators` with "for the ecosystem you touch"
   framing. Found by a static overfitting audit; confirmed by the multi-eco
   run, where agents named their repos' own gates unprompted (pytest, mypy,
   flake8, shellcheck) with no lintian/clippy reflex.

The multi-eco round (Python/Shell/C++-ROS × bugfix/feature/refactor) found no
framework defects; the harness-side fixes it did surface (container image,
brief premise, parallel-orchestration) were benchmark-harness details, not
framework changes.

## 19. Small-profile notes hub (2026-07-03, v5.8)

The small profile stored durable knowledge in a single flat `.ai/notes.md` plus
the curated project-context digest. Flat is right while notes are small (the
whole file is cheap to read whole), but on a long-lived small project the log
grows and every session re-reads all of it. Fix: `notes.md` may become a
hub-and-spoke — a linked index whose detail lives in `.ai/notes/<topic>.md`
leaves, so a session reads the compact hub and opens only the leaves a task
needs. This is the large profile's manifest→node retrieval principle done with
plain markdown links and none of its machinery (no manifest, no generated
INDEX, no hot/cold tiers, no budgets, no kb-delta). Same shape as this repo's
own auto-memory (`MEMORY.md` index + one-file-per-fact leaves).

Design choices:
- **Progressive, threshold-triggered.** Start flat; once `notes.md` passes ~1-2
  screens, move topic clusters (largest first) into leaves until the hub is back
  under ~1 screen. Never split while notes stay short — the index-plus-leaf read
  is strictly more expensive than one small file. (The "largest cluster only,
  once" wording of the first draft under-split a mature project — hub stayed
  over threshold, ~14% read reduction; corrected to split-until-under-threshold
  after the A/B below.)
- **Guidance only, no tooling.** Lives in the AGENTS.md protocol, the notes.md
  stub, `/explore` (read hub first), and `/build` step 5 (split + keep links in
  sync). The link-integrity check (every leaf linked, every pointer resolves)
  rides the existing end-of-build project-context refresh — no new hook.
- **No staleness guard, by design.** Small dropped `check_stale.py`; the hub is
  the volatile notes layer (not curated architecture) and the source is read
  JIT, so a stale leaf is low-cost. A project that needs `covers`-addressable,
  staleness-guarded memory has outgrown small — re-init as large (carries the
  digest over).

Validated by a controlled A/B (sonnet-5 medium, same repo + task, notes size the
only variable): a seeded 84-line notes.md split correctly (hub + leaf, links in
sync); a fresh 43-line notes.md correctly stayed flat. Both code gates green.

## 20. Automatic profile selection (2026-07-03, v5.9)

`init-agent` now picks the size profile from the codebase itself instead of
defaulting to large. When `--size` is omitted (or given as `auto`), it counts
lines of code across the host repo's source files and applies the §13 boundary:
`<=10k LOC` -> small, above -> large.

- **LOC estimate (`estimate_loc`).** Reuses probe.py's file-discovery model:
  `git ls-files` when the target is a git repo (deterministic, gitignore-aware
  so lockfiles/vendored trees don't count), else an `os.walk` fallback that
  skips `.git`, `.ai`, and common vendor/build dirs. Counts only code
  extensions (`CODE_EXTS`) — docs, data, and markup (`.md`, `.json`, `.yaml`,
  `.toml`, `.html`, `.css`) are excluded so the number reflects code the agent
  must reason about, not prose or generated files. Threshold is the single
  constant `SIZE_LOC_THRESHOLD = 10000`, matching §13's ~10k boundary.
- **Interaction.** `--size auto` (explicit) selects silently. `--size
  large|small` still forces that profile — an explicit flag always wins. With
  no flag and a TTY, the auto pick becomes the *default* of the existing size
  prompt, so the estimate is shown and the user can veto it; with no flag and
  no TTY (scripted), the auto pick is used directly. Graduation between
  profiles stays a deliberate re-init, per §13, never a side effect of an
  update; v5.14 moved updating out of the CLI entirely and `/update` reports a
  profile mismatch rather than acting on it (§24).

Validated on real and synthetic repos: ha-core (2.29M LOC) -> large,
network-status (30 LOC) -> small; a synthetic 12.6k-LOC git project scaffolds
large and a 90-LOC one scaffolds small, with explicit-override, non-git
fallback, and the (since removed) `--update --size auto` edge cases all
correct. Scaffold path only
(no explore run).

## 21. Explore-freshness guard + notes.md pointer clarification (2026-07-06, v5.10)

Investigated a proposal: could the small profile's `.ai/notes.md` carry more
steering — pointers to sub-repos/folders, or an architecture overview — so a
fresh session finds the right code faster instead of re-deriving structure by
search. Surveyed four real deployments of this framework
(`ha-value-crossing`, `ha-weatherstage`, `navigation2`, and this repo itself)
rather than reasoning in the abstract.

Findings:
- The mechanism the proposal wants **already exists** and, when used, works
  well: the small profile's `GENERATED:project-context` section in AGENTS.md
  (module map, tech stack, glossary — filled by `/explore`) and the large
  profile's `architecture/*` KB nodes. `ha-value-crossing`'s digest has a
  precise per-file module map; `navigation2`'s KB has a real module-oriented
  architecture split. Adding a second architecture home inside `notes.md`
  would duplicate this and violate the standing single-source-of-truth
  invariant (§13's design rule) — this is the collision the proposal itself
  anticipated. **Rejected.**
- "Pointers to other repos/folders" already happens, unprompted, inside
  `notes.md` — `ha-weatherstage`'s notes point at
  `ha-value-crossing`'s `.venv-ha` for running its HA-aware tests. This fits
  the stub's existing "operational runbooks" genre; it was just never named
  as an explicit example, making it a discoverability gap rather than a
  missing capability.
- The real gap: the project-context digest has **no freshness guard**. This
  repo's own `AGENTS.md` is the live counterexample — its digest still reads
  the scaffold-time placeholder ("CLI tool and Python library for
  manipulating SQLite databases", left over from a §20 test run) while
  `.ai/notes.md` has 60+ lines of real, current decisions. `/explore` was
  simply never invoked here, and nothing short-circuits non-trivial work on
  a repo whose always-loaded digest is still a stub or wrong. A fresh session
  reading this file cold gets actively misled about the project's purpose —
  the opposite of the token efficiency the digest exists to buy.

Decision: two guidance-only edits (no new tooling, matching the §19
precedent), both in the shared stub renderers:
1. Small-profile Protocol item 1 (`render_agents_md_small`) now tells the
   agent to check the Project Context section first and run `/explore` before
   non-trivial work if it is still just the seed one-liner or the raw
   `Populated by /explore` marker with no module map/commands.
2. The `notes.md` stub (`render_notes_stub`, shared by both profiles) now
   names "pointers to related repos/paths this project depends on" as an
   explicit example of what belongs there, and restates in the same breath
   that architecture/module-map content stays in the Project Context section
   — sanctioning the observed-useful pattern without opening the door to
   duplicating the digest.

Rejected alternatives: seeding the digest from `probe.py`'s mechanical output
at scaffold time (would help, but the framework deliberately keeps `probe.py`
output out of the committed scaffold — see `--debug-probe`'s `PROBE.md`,
explicitly "not part of the scaffold" — so this would be a separate, larger
design change, not a minor steering fix); a dedicated `references/`-style
node for small (already covered by `.ai/external/` + a `notes.md` line per
§13's dropped list; small deliberately has no node machinery).

## 22. /goal as a documented autonomous-dispatch mode (2026-07-08, v5.11)

2026's "loop engineering" trend (self-prompting agents that run turn after
turn until a stated condition holds — Claude Code's native `/goal`/`/loop`,
the community Ralph Wiggum technique) was checked against this concept.
Comparison found the two are answering different questions rather than
competing: right-sizing decides *how much ceremony a task needs*; `/goal`
decides *whether a human supervises turn-by-turn or the agent runs
unsupervised toward an already-stated finish line*. Nothing in the concept
previously said anything about the second question beyond one throwaway
line (§17 item 4: "/goal ... the lighter alternative to the scaffolded
lint/test Stop hook").

Key finding driving the design: `/goal`'s own condition text is not
automatically the spec's (or plan's) acceptance criteria — it is exactly
and only the string the user types after `/goal`, checked each turn by a
separate, fast model. `/build` and `/implement` already have a rigorous
definition of done baked into the skill (acceptance criteria checked off,
gate green, reviewer clean); if the `/goal` condition restates that
loosely ("build spec-01") instead of pointing at the artifact directly, the
condition-checker's bar and the skill's own bar can silently drift apart —
the checker might call it done a step early (e.g., before the reviewer
runs) because nothing in the condition said that step was required.

Decision: document `/goal` as a **supervision mode layered on the existing
paths, not a third size tier and not a new definition of done**. Added to
both profiles' `AGENTS.md`, `claude`-harness only (`/goal` has no Copilot
equivalent), right after Right-sizing:
- A decision rule for when it applies: the finish line must be
  machine-checkable (tests, lint, a named gate script), and no mid-flight
  judgment call is expected — a `/goal` loop cannot ask the user a
  question, so it is the wrong tool the moment ambiguity is likely.
- A fixed condition-phrasing convention that points at the artifact
  already defining done instead of restating it: `.ai/changes/<id>/spec.md`
  (small) or `.ai/knowledgebase/tasks/<id>/plan.md` (large), plus the gate
  and the reviewer's sign-off.
- A paired stall clause, reusing the existing typed-escalation wording
  verbatim (test-fail-twice → stop, never a third blind attempt) rather
  than inventing a new guardrail — this was the one gap the loop-engineering
  comparison actually surfaced: the concept had no generic iteration/budget
  ceiling in prose, only that one specific escalation trigger.

Hardened after a doc-check against the official /goal and /loop references
(2026-07-08, same version):
- The goal evaluator reads only the transcript — it never runs commands or
  reads files — so the scaffolded condition examples now require the agent
  to *show* the checked-off criteria and the gate's exit status in output,
  not merely reach them; a condition that only names a file leaves the
  evaluator guessing.
- A turn-cap clause ("or stop after N turns") now rides both condition
  examples — the docs' own bounding mechanism, closing the budget-ceiling
  gap noted above with zero new machinery.
- Because scaffolded skills are `disable-model-invocation: true` (§17.1),
  a /goal loop cannot load `/build`/`/implement` itself: the documented
  ordering is invoke the skill first, then set the goal, so the procedure
  is already in context for every loop turn. For the same reason,
  `/loop <interval> /build <id>` delivers the skill as plain text instead
  of executing it (v2.1.196 scheduled-fire semantics) — the framework does
  not use /loop, recorded here so nobody debugs it as a defect later.

Usage pattern this surfaced: `/goal` is a **second way to drive the
framework, running alongside human-supervised spec-then-build rather than
replacing it**. Turn-by-turn supervision (write a spec, watch `/build`
implement it, review the diff) stays the default for one-off or
judgment-heavy work. `/goal`'s complement is a backlog of several
already-scoped, independently checkable tasks (a ticket queue, a handful of
specs already written) worked through in one continuous session without a
human re-approving between them. Within that session, discovery already
surfaced for the first task (the project-context digest, `notes.md`, files
already read) carries forward in-context for free through later tasks — no
rediscovery — as long as the window doesn't fill. The two risks that erase
that saving are exactly why `notes.md` is worth writing to mid-loop, not
only at `/explore` time: compaction (detail lost to summarization once the
window fills) and context rot (earlier detail degrading before any hard
compaction event). `notes.md` is the loop's insurance against both — cheap
to write, and the reason the framework's persistence layer and `/goal`'s
unsupervised dispatch reinforce each other rather than being unrelated
features.

Rejected: treating `/goal` as a new top-level path alongside trivial and
ticket-driven work (first draft of this idea) — cleaner to model it as
orthogonal to sizing, since the same spec or plan is used either way and
nothing about the artifact format changes. Also rejected: adopting
heartbeats/crons/hooks (the other loop-engineering patterns) as core
mechanisms — they answer "run on a schedule/event with nobody watching,"
a use case this concept is not built for (every unit of work starts from a
human-filed ticket or invocation by design); worth a deliberate look only
if scheduled maintenance-style agents become an actual separately-scoped
goal, not a reason to retrofit the pipeline now.

## 23. Worker sub-agents on a mid-tier model (2026-07-17, v5.12; removed 2026-07-28, v5.13)

v5.12 scaffolded two optional agent definitions (claude harness only, both
profiles), each pinning `model: sonnet` in frontmatter: `code-worker`
implemented one fully specified change item dispatched by the main agent,
`explore-helper` was the read-only collector for the exploration fan-out.
Planning, specs, review gates, and digest/KB curation stayed on the strong
tier, and the dispatcher re-verified every gate.

v5.13 removes both definitions and every dispatch instruction that named
them (phase 1 explore bullet, phase 3 "Worker dispatch" section,
small-profile /explore and /build skills, the runbook's W arm). Two reasons:

1. Harness leakage. The agent definitions were claude-only, but the dispatch
   guidance lived in harness-neutral text (phase docs, `command_specs_small`).
   Copilot scaffolds therefore instructed the agent to dispatch to
   `code-worker` and `explore-helper`, which do not exist there. Any revival
   has to gate the prose on `harness == "claude"`, not only the file writes.
2. The measurement came back negative. The W arm ran once
   (`benchmarks/w4-sonnet5-medium-2026-07-17/`, sonnet-5 x medium, cell-4
   py-feature, worker pinned to the same tier as MODEL). Both twins passed
   the gate; the worker twin cost +35% total tokens, +40% output, +43%
   estimated cost, with only wall-clock active time slightly lower. §13's
   scale threshold applies to delegation as well: brief construction, worker
   cold context, report-back, and re-verification exceeded the discovery
   noise kept out of the orchestrator.

What survives the removal:
- §3 stands unchanged and now has no exception: routing is the user's, via
  harness controls; the framework pins no tier anywhere.
- The generic guidance the workers were attached to stays, phrased without
  named agents: run the exploration fan-out in sub-agent contexts, cap each
  return at ~2000 tokens, and never let a sub-agent write the digest, notes,
  or KB (digest errors compound across every later warm start).
- The asymmetry rule from the 2026-07-04 round is unaffected: low-tier
  self-reported PASS is not a gate result, so gates are re-verified by
  whoever owns them.

Conditions for a revival, if one is ever attempted: harness-gated prose, a
worker tier actually cheaper than MODEL (the measured pair used the same
tier, so a price gap remains untested), and a repo large enough that
discovery noise dominates dispatch ceremony. The recorded W round stays in
`benchmarks/` as the evidence; the runbook arm that produced it is retired.

## 24. Agent-driven framework update (2026-07-28, v5.14)

`init_agent.py -u/--update` regenerated every framework-owned file and froze
every hand-filled one (`write` vs `write_owned`). Measured against a real
scaffold, that binary ownership model loses in three ways:

1. **Retired files survive forever.** `-u` only writes; it never deletes. A
   project scaffolded on v5.12 keeps `.claude/agents/code-worker.md` after an
   update to v5.13, which withdrew it. Confirmed on a test scaffold: the file
   was still there after `-u`, and nothing in the report mentioned it.
2. **User edits to framework files are silently reverted.** A permission entry
   added to `.claude/settings.json` was gone after `-u`, unreported. The same
   holds for rules appended to AGENTS.md outside the generated markers.
3. **The shape of hand-filled content can never change.** `write_owned`
   refuses to touch a file whose content differs from the stub, which is
   correct for content and wrong for structure: a new frontmatter key, a new
   manifest field, or a renamed directory never reaches an existing project.
   The KB is preserved and silently frozen at the schema it was born with.

Two smaller ones: nothing recorded which framework version built a scaffold,
so an update could only overwrite unconditionally; and the pre-update snapshot
covered `.ai` only, while AGENTS.md, CLAUDE.md and the harness directory live
in the host repo and were overwritten with no rescue copy.

What did work and is kept: `extract_generated` carries the
`GENERATED:project-context` section across a regeneration in both profiles
(verified for small and large), and `write_owned` protects KB node bodies.

**Decision.** An update is a three-way merge (project state, previous
framework, current framework) plus a schema migration. Both are judgment
calls, so the agent owns them and the CLI provides only what is deterministic:

- **Version stamp.** `.ai/agent/framework.json` records `framework_version`,
  `profile`, `harness`, `project`, `generated`, and `framework_files` (every
  framework path that version emitted, collected by `write()` itself so the
  list cannot drift from the writes). `recorded framework_files` minus
  `reference framework_files` is exactly the retire set, so defect 1 becomes
  a set difference rather than a guess.
- **`--emit-reference DIR`.** Renders a pristine scaffold of the current
  framework into an empty dir with no git init, no gitignore edits, no commit,
  no host-project side effects. This is the comparison target; a real project
  is never compared against a re-run over itself.
- **`--detect`.** Prints the stamp as JSON, falling back to inspecting the
  tree for scaffolds that predate the stamp (version `null`, empty file list,
  so the skill knows nothing can be retired deterministically).
- **`/update` skill**, both profiles, both harnesses. Preflight (read the
  stamp, commit `.ai`, copy the host-repo framework files to the gitignored
  `.ai/agent/.update-backup/`, refuse to proceed silently over uncommitted
  work) -> render the reference -> classify every path as added / identical /
  framework-changed / user-edited / retired and act per class, merging the
  user-edited ones and deleting the retired ones together with the
  instructions that still named them -> migrate hand-filled content into the
  new shape in place -> verify every referenced tool runs -> rewrite the stamp
  and report one row per file. `dry-run` stops after classification.

The governing rule, stated in the skill itself: the knowledge is the
expensive artifact and the framework files are cheap, so `/update` never
re-runs `/explore` and never regenerates hand-filled content from a stub. If
a new field cannot be derived from what the project already records, it is
left empty and reported, not invented and not researched from the codebase.

Harness gating is explicit per §23's lesson: the merge cases, the backup
paths, and the verification steps name `.claude/settings.json` and hooks only
on claude, and `.github/prompts/` only on copilot. The skill body is built by
one `render_update_body(size, harness, arg)` so both axes stay in one place.

Not in scope: profile switching. Graduating small -> large stays a deliberate
re-init per §20; `/update` detects a codebase that has outgrown its profile
and says so in the report instead of migrating on its own.

**Measured** (`benchmarks/u-update-sonnet5-medium-2026-07-28/`, sonnet-5 x
medium): a v5.12 Satty scaffold with a real `/explore` digest, real notes, and
hand edits, updated to 5.14 by an agent following only the skill. Gate 13/13:
the 4540-byte project-context digest came through byte-identical, notes and the
hand-added AGENTS.md section survived, the two user-added permissions survived,
both retired worker definitions were deleted with no dangling references, and
the agent never read the codebase. Two runs were needed. The first exposed the
design's one real hole: retirement rested on the recorded `framework_files`
list, which is empty on every scaffold that exists today, and the fallback rule
said to treat unmatched files as the user's. Defect 1 was therefore fixed only
for scaffolds not yet created. The fix is an **orphan test** that asks the
generator's own history instead of the stamp:

    git -C "$LLM_AGENT_HOME" log --oneline -S'<basename>' -- init_agent.py

Commits found means the framework emitted the file and a later version dropped
it, so retire it; none means the user wrote it, so leave it; no git checkout
means undecidable, so report it. This makes retirement work on legacy scaffolds
without a stamp, which is the only case that matters in the field. Three smaller
instruction fixes came from the same runs: ensure `.ai/.gitignore` covers the
backup path before writing it (legacy scaffolds lack the entry), separate
untracked from tracked-and-modified in the stop condition (an
uncommitted-scaffold host repo is normal, not a reason to block), and carry
profile/harness explicitly from preflight into the reference render.

## 25. Migrating an existing .ai/ folder (2026-07-29, v5.15)

`/import <source>` migrates a whole prior `.ai/` working directory - an older
version of this framework, or a differently-shaped agent folder - into the
current structure. It runs after scaffolding, against a copy of the old folder
(move the pre-existing `.ai/` aside to `.ai.old/` before init, then
`/import .ai.old`), because init writes a fresh `.ai/` and a foreign layout has
no owned files for `write_owned` to preserve.

### Why it is separate from /import-kb (§15)
`/import-kb` transforms *arbitrary curated knowledge* (a docs/wiki dump, a
README-heavy repo) into KB nodes and deliberately ignores task and ticket state
(§15 last paragraph: "transform docs/ into nodes and ignore its task and ticket
state"). That is the wrong operation for a prior `.ai/` you want to keep working
in: you would lose the inbox, the planned/in-progress tasks, the decisions, and
the running notes. `/import` is the migration counterpart - it carries the
*lifecycle state* across as well, and upgrades already-framework-shaped nodes in
place (re-categorize, rewrite frontmatter to the current schema, re-match
`covers`) rather than re-synthesizing them from scratch. For the knowledge that
is not already node-shaped it reuses the /import-kb read->classify->transform
protocol, so the two skills share machinery without duplicating intent. The
four-way boundary the skill bodies state so the agent chooses correctly:
`/add-reference` keeps raw material for search; `/import-kb` transforms curated
knowledge into nodes; `/import` migrates a whole `.ai/` working directory,
knowledge and state; `/update` (§24) upgrades a scaffold this framework already
wrote.

### Why it is separate from /update (§24)
Both move a prior `.ai/` to the current shape, but they start from different
material. `/update` operates on a scaffold this framework wrote, identified by
its `.ai/agent/framework.json` stamp: the file list is known, so the work is a
file-by-file merge plus retirement of what the framework dropped. `/import`
starts from a folder with no stamp - an older pre-stamp version, or a foreign
agent layout - where nothing about the source can be assumed, so the work is
classification before migration. The decision rule the skill bodies carry:
stamped scaffold -> `/update`, unstamped or foreign -> `/import`. Because
`/import` runs after a fresh init, the current scaffold's stamp is already
correct; `/import` must never overwrite it with the source's copy, or the next
`/update` would diff against the wrong version.

### Why a skill, not a tool
Same reasoning as §15: the source layout is unknown by definition (any prior
version, or a foreign framework), so no deterministic parser can exist. The
model reads heterogeneous input, infers what each piece *is* (a node, a ticket,
a plan, a decision, a note), and maps it onto the current shape. The
deterministic parts it reuses are the ones the framework already owns:
`gen_index.py`, the manifest format, the node frontmatter schema, the ticket and
changes layouts.

### Protocol
Survey (sub-agent, condensed map, detect large|small|foreign layout) ->
migrate knowledge (upgrade node-shaped content in place; classify+transform the
rest) -> migrate lifecycle state (tickets -> inbox; planned/in-progress ->
tasks/<id>/ with status preserved in frontmatter; finished -> _archive/;
decisions -> decisions/ nodes; external -> references/ + `.ai/external/`; notes
-> notes.md) -> regenerate the derived artifacts (manifest, INDEX,
project-context) from the migrated content rather than copying the source's
generated files, leaving `.ai/agent/framework.json` as init stamped it ->
report a source->target mapping, list the unmappable remainder, preserve the
source, commit `.ai` (`import: <source>`).

### Profile differences
- **Large**: full migration into KB nodes plus the ticket/task pipeline;
  `manifest.yaml` + `INDEX.md` + the project-context section are regenerated.
- **Small**: no node store; distill the source's stable facts into the AGENTS.md
  project-context section, route the rest to `notes.md`, and carry in-flight
  work into `.ai/changes/<id>/spec.md` (finished ones to `_archive/`). A
  large-profile source's hot-tier nodes are distilled down, not reproduced.

### Profile mismatch
The source's profile and the current scaffold's profile need not match; `/import`
maps the source's content onto the *current* profile's targets rather than
recreating the source's shape (a small source's project-context becomes nodes in
a large scaffold; a large source's node store is distilled into project-context +
notes in a small scaffold). The small profile now carries seven skills
(`/explore`, `/spec`, `/build`, `/import-kb`, `/import`, `/tidy-up`,
`/update`).

## 26. Hygiene sweeps as a skill (2026-07-29, v5.16)

`/tidy-up [scope]` sweeps the host code for four kinds of rot: dead code,
obsolete files, overlong comments, and em dashes in prose. It is maintenance,
not a phase and not a ticket, so it sits beside `/update` rather than inside
the pipeline.

### The constraint that shapes it
A tidy-up may not change behavior. That single rule is what makes the skill
safe to hand an agent, and it is enforced structurally rather than by asking
nicely: step 0 captures a green build/test/lint baseline and refuses to start
without one, step 5 re-runs the same commands and compares. Without the
up-front baseline the agent cannot distinguish a break it caused from one it
inherited, which is the failure mode that makes automated cleanup dangerous.
Anything that would change behavior is out of scope by definition and becomes
a change spec instead.

### Why the four passes carry different authority
Removing dead code and rewriting prose is reversible and locally verifiable,
so the agent does it. Deleting a file is neither: the evidence that a file is
unused is always circumstantial (nothing references it *that a search found*),
and the cost of being wrong is unbounded. So pass 2 only proposes, with a
table of path, reason, blast radius, and confidence. This asymmetry is the
design, not caution for its own sake: the passes are ordered by how cheaply a
mistake can be detected and undone.

### Dead code needs evidence, and a library has none
The pass states where a plain search goes blind (reflection, plugin
registries, dependency injection, serialized field names, conditional
compilation, generated bindings, packaging entry points) because an agent that
greps for a symbol and finds nothing will otherwise conclude it is dead. The
sharper rule: in a library, an exported symbol is not dead because this repo
does not call it. Removing it is an API break, so the public surface counts as
used. Ecosystem tools that report unused code are treated as a candidate list
to verify, never as authority.

### Comments: a line count that cannot destroy knowledge
Shortening comments to 1-2 lines is trivially satisfiable by deleting them,
which is the wrong outcome. The pass therefore separates narrative that
restates the code (compress or delete) from information the code cannot carry:
why, invariants, workarounds, citations. That content is compressed if it
fits and relocated with a pointer if it does not. Licence headers, SPDX tags,
generated-file banners, and published API documentation are exempt from the
count entirely.

### Em dashes: a register rule the framework owed itself
§8 has required plain punctuation in generated artifacts since v1. The
generator was violating it: nine em dashes in `init_agent.py` templates
reached ten files across the four scaffold variants. Those were rewritten by
clause (parenthetical to commas, break to colon or full stop) rather than
swapped character for character, which is the same instruction the pass gives.
Fixtures, golden files, vendored sources, licence texts, and data files are
excluded, because there the character is the data and editing it is a
behavior change.

### Profile and harness differences
- **Large**: removals can invalidate KB nodes whose `covers` globs matched a
  deleted path; those nodes and their `manifest.yaml` entries are updated and
  `INDEX.md` regenerated.
- **Small**: the module map in the project-context digest is updated only if a
  module disappeared, and durable findings append to `notes.md`.
- **claude**: the survey fan-out runs in sub-agents that return evidence
  rather than file dumps, and the `reviewer` sub-agent takes the diff.
- **copilot**: search-based survey and a clean-context self-review, noted as
  such in the report.

Like every other skill, it commits `.ai` and leaves host-repo changes staged
for the user. The framework does not commit the host project repo.

## 27. Generator structure: content as files (2026-07-29, v5.17)

The generator was one 3093-line Python file in which two thirds of the lines
were not code. Measured by AST: 792 lines of skill body prose, 554 lines of
Python programs written as string literals, 312 lines of AGENTS.md text, 272
of phase docs, 151 of static config. About 600 lines were actual logic. This
section records why that was split and on what principle, because the shape
is easy to undo by accident.

### The principle
Content that the generator emits lives under `templates/` as a file of its
own kind: emitted Python as `.py`, emitted markdown as `.md`, emitted data as
a data file. Code decides *which* content applies and *what* fills its slots.
Prose does not live in string literals, and logic does not live in templates.

### What that buys
The 554 lines of embedded programs were the sharpest case. `probe.py` was 236
lines of Python that no linter, type checker, or test could see, because to
every tool it was one long string. Writing a `{` in it required remembering to
write `{{`. As a file it is just Python. The same move turned
`_MANIFEST_PARSER`, a code fragment that was spliced into three tools by hand,
into one file included in three places.

It also made a test layer possible for the first time. `tests/check_templates.py`
asserts properties that could not previously be asked: no template is orphaned,
every slot a template declares is filled by its caller, no rendered artifact
still contains a `${...}`, every rendered tool parses as Python, the rendered
settings parse as JSON, and no template carries an em dash (section 8, which
the generator had been violating in nine places).

### Slot syntax: why not str.format
Emitted content is full of literal braces: JSON, dict literals, f-strings
inside the generated tools. `str.format` would demand every one of them be
doubled, and a missed escape is a silent corruption rather than an error.
`string.Template.safe_substitute` ignores braces entirely, and it leaves
unknown `$NAME` alone, so the three harness variables that must reach the
output verbatim (`$ARGUMENTS`, `$LLM_AGENT_HOME`, `$CLAUDE_PROJECT_DIR`) need
no escaping either. The cost of `safe_substitute` is that a mistyped slot
fails silently, which is exactly what the slot check in the test layer exists
to catch. Slot names stay lowercase so they cannot collide with the
passthrough variables.

### The two axes stay in code
Profile and harness branch at 28 points, and the branches are sentence-level
rather than document-level: a clause that appears only on the claude harness,
a bullet only in the large profile. The tempting move is four copies of
AGENTS.md, one per variant. That is rejected: duplicated documents are how the
axes drift, which is the failure the "handle both or state why" rule in the
dev guide already exists to prevent. Instead the conditional prose is a
fragment file under `fragments/<harness>/` or `fragments/<profile>/`, and the
`if` that selects it stays in Python. Templates hold prose; they do not hold
conditionals, and no template language was introduced.

### Distribution was never the constraint
"Single stdlib file" read like a distribution requirement. It was not one.
`install.sh` git-clones the whole repo and the shell function runs
`$LLM_AGENT_HOME/init_agent.py` after a pull, so a sibling package and
template tree travel with it automatically. There is no `curl | python`, no
pip, no zipapp path. Python puts the script's own directory on `sys.path`, so
the imports resolve regardless of the working directory the user runs
`init-agent` from. If a single-file artifact is ever wanted, `zipapp` is
stdlib and can bundle the tree without changing the source layout.

### The refactor was verified, not reviewed
Restructuring 2081 lines of content by hand invites silent corruption, so the
move was gated on byte-identity: render all four size and harness variants
before and after, diff the trees, and require an empty diff. That harness
caught two real defects during the work that reading the diff would not have.
The first was an extraction script that neutralized `if __name__ ==
"__main__"` by rewriting the text, which also rewrote the nested guards inside
the templates. The second was `/update`'s description, which differs by
profile and had been collapsed to one string. Both surfaced as a failing diff
within seconds. No behavior changed in this revision: the emitted scaffold is
identical to v5.16 in all four variants, and the version bump records the
source layout, not the output.

## 28. Bootstrapping /update into a pre-5.14 scaffold (2026-07-29, v5.18)

§24 put updating in the agent's hands: an update is a merge, and merges need
judgment a scaffolder does not have. That leaves a gap at the bottom. A
scaffold built before v5.14 has no `/update` skill to run, so the agent has no
way in, and the obvious workaround is wrong.

### Why re-running init is not the workaround
Init overwrites framework files whole, which is all a scaffolder can do. On an
existing scaffold that was measured, not assumed:

- project rules appended below the framework text in AGENTS.md: gone
- a permission the user added to `.claude/settings.json`: gone
- files the framework retired two versions ago: still there, because `write()`
  has no concept of deletion
- re-running without `--harness` on a copilot scaffold: a `.claude/` tree
  appears next to the `.github/prompts/` one, and the stamp then names the
  wrong harness

Only the `GENERATED:project-context` section is rescued, because
`extract_generated` looks for it specifically. Everything else a user put in a
framework-owned file is lost silently.

### What the bootstrap does instead
`init_agent.py --bootstrap-update` writes exactly two things: the `/update`
skill (or its prompt-file equivalent) and a stamp. Nothing else is touched, so
there is nothing for it to destroy. Profile and harness come from
`detect_scaffold`, never from a flag, which removes the drift failure above by
construction. It refuses on a directory with no scaffold, and on one already
stamped with a version, where `/update` is the right tool and already present.

This is safe for a reason specific to skills: skill files are entirely
framework-owned. Unlike AGENTS.md, which carries a generated section plus
whatever the user appended, and unlike `settings.json`, which carries user
permissions, a skill file has no user-edited region at all. Overwriting one
cannot lose anything. That property is what makes the narrow fix possible, and
it is worth preserving: do not add a user-editable region to a skill file.

### The stamp must not claim a version
The stamp records `framework_version: null` and an empty file list. Stamping
the current version instead would be actively harmful, and in the obvious way:
`/update`'s preflight reads the recorded version, sees it match the reference,
and concludes the project is current, while the project still holds the old
AGENTS.md and phase docs. The empty file list matters for the same reason.
Retirement is "in the recorded list, absent from the reference", so a current
list makes that set empty and nothing is ever retired. Null is the honest
value and is the case the preflight already handles: profile, harness, and
project name are recorded so the agent need not re-detect them, and the
version stays unknown so retirement falls to the orphan test, deliberately.

### The orphan test had gone stale
With an empty file list the orphan test is the only thing that can retire
anything, and v5.17 had broken it without anyone noticing. It asks the
generator's history whether a path was ever emitted:

    git -C "$LLM_AGENT_HOME" log --oneline -S'<basename>' -- init_agent.py

That path filter was right while `init_agent.py` was the whole product. After
the restructure the write calls live in `agentgen/` and the content under
`templates/`, so a file introduced after 5.17 leaves no trace in
`init_agent.py`. The test would report "no commits", conclude the user wrote
the file, and leave it forever. The filter now covers all three paths. The
failure was latent rather than live, because every path that exists today was
named in `init_agent.py` back when it was added, and it would have started
biting on the first file retired after 5.17.

### What this deliberately does not do
No three-way merge, no deterministic classification plan, no second update
implementation in Python. The bootstrap is a delivery mechanism and stops
there. Making `/update` itself smarter, by rendering the reference for the
version a project was built at so "did the user edit this file" becomes a hash
comparison rather than a judgment call, is a real improvement and is measured
in the notes for a later revision. It is not needed for the mechanism to work,
and it is better designed after watching `/update` run against real legacy
scaffolds than before.

## 29. Review gates sized to the change (2026-08-26, v5.20)

Owner report from daily use: reviews fire too often and run too deep, and
small changes feel like they pay a gate built for large ones. Reading the
templates confirms it. Right-sizing existed only at the *entrance* to the
pipeline (does this need a ticket / a spec?) and never at the *gate*. Once
inside, review cost was constant.

### Three separate defects

**The small profile reviewed changes it had just exempted from planning.**
Right-sizing says a one-sentence, 1-2 file change needs no spec: make it,
note it, commit. The always-on protocol then said "before declaring a change
done, have the full diff reviewed in a fresh context against the acceptance
criteria" with no scope qualifier. A right-sized change has neither a spec nor
acceptance criteria, so the rule demanded a `reviewer` sub-agent for a diff
whose whole content fits in a sentence. The two rules sat eleven lines apart
in the same always-loaded document. This is the main driver of the "too often"
report: it hits the most common daily change, the small one.

**The large profile's trivial path shrank one gate of two.** Phase 2 shrinks
the plan-review gate to a one-line sign-off for a trivial ticket, and
AGENTS.md advertised the path as "one task file, one review gate". Phase 3's
ticket review gate carried no trivial clause and closed with "Never silently
skip the gate", so a trivial ticket still paid a full sub-agent diff review.
The two phase docs disagreed and the entry document described a third
behavior. Both gates now size down together on the trivial path.

**Review depth did not scale.** The `reviewer` brief ran one fixed checklist
regardless of the artifact, including toolchain-version and
registry-availability reasoning for build config even when the diff touched no
build config, and both gates cross-checked every gotcha in `notes.md`
unconditionally. The packaging reasoning is now conditioned on the diff
actually touching build/CI/packaging (which is what it was written for, per
§18), as is the gotcha sweep, and the brief opens by telling the reviewer to
match depth to the artifact and that report length is not evidence of rigor.

### The rule
Sizing a gate down is a judgment call the agent may make; skipping one
silently is not. Every gate keeps a floor, an inline check against the
acceptance criteria, so "small" buys a cheaper instrument rather than no
instrument. The fresh-context requirement is what gets spent, and it is spent
where a producing context is actually likely to grade its own work wrong: a
multi-task diff, or one with blast radius beyond the files it names.

### What this does not change
The gates themselves stay. §12's finding stands, a producing context grades
its own work generously, and fresh-context review is also what makes
cheap-execution modes safe (§9, §23). The change is proportionality, not
removal, and it does not touch the plan-review gate for non-trivial tickets:
a weak plan still poisons every downstream task, and that is the gate with the
highest leverage per token in the whole framework.

## 30. Hermes as a third harness (2026-09-09, v5.21)

The harness axis (§27) had two values, claude and copilot, and every branch in
the generator was written as `if harness == "claude": ... else: ...`. Hermes,
which discovers SKILL.md skills under `.agents/skills/` in a trusted git
repository and exposes each one as a slash command, is a third value. Adding it
is the first real test of whether the axis was a genuine axis or just two
hard-coded cases.

### What hermes shares and what it does not

It shares the bodies. A hermes scaffold emits exactly the same skill bodies,
AGENTS.md, phase docs and KB tools as the other harnesses; no document is
duplicated per harness, per §27. What differs is mechanism, and only
mechanism:

- **Location and frontmatter.** `.agents/skills/<name>/SKILL.md` rather than
  `.claude/skills/` or `.github/prompts/`. Hermes wants `name`, a `version`
  (the framework version, so a scaffold reports which revision built it),
  an audited `platforms` list, and its own `metadata.hermes` block. It caps
  `description` at 60 characters, which the descriptions carried in the skill
  templates exceed, so hermes gets a second, short description per command in
  `HERMES_DESCRIPTIONS`. `disable-model-invocation` is a claude key and is not
  emitted; hermes has no equivalent.
- **No hooks, settings, or reviewer sub-agent.** Those are claude mechanisms.
  Hermes falls on the non-claude side of the branches that already existed,
  the same way copilot does.
- **Arguments.** Claude substitutes `$ARGUMENTS`, copilot prompts through
  `${input:...}`, hermes substitutes nothing: text after the command name
  reaches the agent as the user instruction. So the skill has to say where its
  argument comes from, in prose, which is what `HERMES_ARG_FOCUS` and
  `HERMES_ARG_TICKET` fill the argument slot with.

### Reserved names

Hermes ships built-in slash commands, and three framework command names
collide with them: `/plan`, `/import` and `/update`. A project skill cannot be
relied on to shadow a built-in, so on that harness those three are emitted as
`/plan-ticket`, `/import-agent` and `/framework-update`. The workflows are
unchanged; only the name is.

The renaming is not free: several documents name a sibling command in prose
("that begins with /plan <ID>", "it is also not /update"). A per-harness name
that only the emitter knows would leave that prose pointing at commands the
user cannot run. So the three renamable names became slots (`${cmd_plan}`,
`${cmd_import}`, `${cmd_update}`) filled from one table. Only those three;
every other command keeps its name on every harness and stays literal in the
templates, because a slot per command name would be ceremony around a constant.

### Trust

Hermes loads project skills only from a repository the user has trusted with
`hermes skills trust`, and re-reads changed skills on `/reload-skills`. That is
a step init cannot take on the user's behalf, so the generated AGENTS.md states
it and the init report prints it.

### What this validates
The claude/copilot branching held: adding a third value changed the generator
in the places the axis already existed and nowhere else, and byte-identity
across the four pre-existing variants is unchanged. The rule from §27 stands
and now has evidence behind it: branch in Python, keep conditional prose in
fragment files, never duplicate a document per variant.

## 31. Removing the large profile (2026-09-09, v5.22)

Two profiles existed because §13 assumed a boundary: above roughly 10k LOC a
codebase is too expensive to re-read, so context has to be rationed through a
curated knowledge base, and below it the source is cheaper to read than an
index is to maintain. v5.22 drops the large side of that boundary. What
remains is what was the small profile, and it is now the only shape the
generator emits.

### What goes

The whole KB apparatus: `manifest.yaml` and `INDEX.md`, hot and cold tiers,
`covers` globs, per-task token budgets, `kb-delta.yaml`, drift detection
against a `kb-commit`, and the deterministic tools that kept those views in
sync (`gen_index.py`, `check_stale.py`, `gen_rules.py`) with their hooks. The
on-demand phase docs go with them, and so does the ticket pipeline they
served: `/add-ticket`, `/plan`, `/implement`, `/add-reference`, and the
plan-review gate. One review gate remains, on the diff, which is the one §29
identified as carrying its cost best on a change of this size.

### What it costs, stated plainly

This is a real capability loss, not a simplification of an equivalent. On a
codebase large enough that the source cannot be sampled per task, the KB was
the mechanism that made the agent's context finite, and nothing replaces it.
A project past that scale is no longer served by this framework. The
justification is not that the KB was wrong; §12 and §16 still stand for what
they measured. It is that maintaining two profiles across three harnesses
meant every change had to be made and verified six ways, and the profile axis
was the one carrying the least benefit per unit of that cost.

### The axis, not just the branch

Removing the large branch removes the axis. `profile` disappears from the
generator: one roster, one AGENTS.md template, one composed body per skill,
templates addressed as `skills/<name>.md` rather than
`skills/<profile>/<name>.md`. The harness axis (§27, §30) is untouched and is
now the only one. `profile` stays in the `framework.json` stamp, always
`"small"`, because that field is what lets `/update` recognize a scaffold
built before this revision.

### Migration

There is no `/update` path across this boundary. A large scaffold's reference
cannot be rendered by a generator that no longer emits it, so `/update` reads
`"profile": "large"` from the stamp and stops, and `--bootstrap-update`
refuses the same case. The supported route is a fresh `init-agent` plus
`/import <old-.ai>`, which already knows how to read a large-profile folder:
it distills the KB into the project-context digest and `notes.md` and carries
in-flight change state across. That skill is deliberately kept pointed at the
old shape, and is the only place in the framework that still describes it.

## 32. Switching harness in place (2026-09-09, v5.23)

With three harnesses (§30) and one profile (§31), the harness is the only
thing left to choose, and there was no supported way to change it. Re-running
init with a different `--harness` wrote the new entry files and left the old
ones exactly where they were.

### The failure that motivates it

Not the stale files themselves, which are harmless clutter. It is that the old
files still answer the same slash commands. A project switched from claude to
hermes would have `.claude/skills/build/SKILL.md` and
`.agents/skills/build/SKILL.md` both live, both claiming `/build`, while
AGENTS.md now documents only the hermes half. Whichever the harness picks up,
the user cannot tell which one ran, and the two drift apart from the first
framework update onward. One command must have one definition.

### Why the generator, not the agent

§24 draws the line: a merge belongs to the agent, a whole-file operation
belongs to the scaffolder. The harness entry files are pure framework output.
They have no GENERATED region, no user-edited part, nothing to reconcile, and
the new set is rendered from the same bodies as the old one. So a switch is an
init, and `init-agent --harness <name>` on an existing scaffold performs it.
`/update` says so and stops if asked.

### Retire by moving, and only what was recorded

Two rules keep it from costing anyone work.

Only files the version stamp actually recorded are retired. A skill the user
wrote next to the framework's is indistinguishable from one the generator
forgot it wrote, so it stays and is reported instead. A scaffold with no
recorded file list retires nothing at all and prints what to remove by hand.

Retired files are moved to `.ai/agent/.harness-backup/<old-harness>/`, not
deleted. The realistic loss is a `.claude/settings.json` carrying permissions
a user added by hand, and a move is recoverable where a delete is not. The
backup is gitignored inside `.ai`, like the `/update` one: a rescue snapshot,
not history.

A switch also forces regeneration of the framework files. AGENTS.md and the
skill bodies name the harness they were built for, so leaving them as "exists"
would produce a scaffold describing the harness it just moved off.

## 33. Recording the project's identity (2026-09-09, v5.24)

Init asks three questions: project name, one-line description, harness. The
harness was recorded in the stamp from the start, because /update needs it to
render a matching reference. The other two were not, and there is no second
copy of either.

### Where they went

The name reaches the AGENTS.md title, the description is seeded into the
project-context section with a note telling Phase 1 to verify it against the
code. Then /explore does exactly that and replaces the section with what it
found. From that point the original one-liner exists nowhere, and the name
exists only as prose in a heading.

So any later re-render had to invent both. A harness switch or a plain re-init
that did not repeat `--name` fell back to the directory name and silently
retitled the project; without `--desc` it seeded an empty description. The
`/update` skill had the same gap: it renders a reference to diff against, and
was told to pass `<project-name>` with nothing authoritative to take it from.

### The rule

The stamp records what the user answered, not what the generator can re-derive.
Framework version, harness, and the file list were already there on that
principle; `project` and `description` belong to the same category and are now
recorded beside them. Everything else in a scaffold is either derived from the
codebase (/explore's output) or written by the user afterwards, and neither
belongs in a machine-readable stamp.

That makes the stamp the single source for re-rendering, so init reads it back
before prompting: on an existing scaffold the recorded name, description and
harness become the prompt defaults, and Enter keeps the project as it is
rather than proposing a rename. A scaffold stamped before this revision has
`"description": null`, which /update is told to treat as "ask the user", not
as an empty description to write in.

## 34. One name per command (2026-09-09, v5.25)

§30 introduced per-harness command names to get around hermes built-ins, and
applied them to `/update`, `/import` and `/plan`. §31 removed `/plan` with the
ticket pipeline. What was left was a framework whose central maintenance
command was `/update` on claude and copilot and `/framework-update` on hermes.

That is a worse property than it looks. The name is what a user types, what
they search the README for, what they tell a colleague, and what the framework
writes in its own instructions. Making it depend on which harness the project
happens to target means no sentence anywhere can name the command without
qualifying it, which is why §30 had to introduce `${cmd_*}` slots in the first
place. The cost is paid on every document that mentions the command, forever.

So the command is `/framework-update` everywhere. Hermes cannot have `/update`,
so that was never the name all three could share; the question was only whether
the other two would keep a shorter name that hermes could not. They do not.
The longer name is also the more accurate one: it updates the framework, not
the project, and `/update` next to a harness's own `/update` was ambiguous even
where it was legal.

`/import` stays renamed on hermes (`/import-agent`), because there the
alternative is renaming it on all three to work around one harness's built-in,
and unlike the update command it is not the framework's own maintenance verb.
The mechanism from §30 stays for exactly that case; it now carries one entry
instead of three.

### Migration

Existing scaffolds rename themselves. The old `/update` skill renders a
reference containing `framework-update`, sees its own file as retired and the
new one as added, and the classification rules in step 3 already cover that;
they gain one clause saying a renamed command is a move, not an addition
beside the old one. So the last act of the old command is to replace itself,
which is the only sequencing that works: there is no version at which both
names should answer.

## 35. No per-harness names left (2026-09-09, v5.26)

§34 unified the update command and left `/import` renamed on hermes alone,
reasoning that renaming it on all three would be routing two harnesses around
a third's built-in. That reasoning was wrong in a way worth recording, because
it weighed the wrong cost.

The cost of a longer name is paid once, when the user reads it. The cost of a
name that varies by harness is paid by every document that mentions the
command, every time it is written or read, forever: the README needs a table,
the skill bodies need a slot, and a user who moves between two projects has to
remember which one they are in. §34 established that; keeping one exception
meant keeping the entire mechanism, and a mechanism with one user is a
mechanism that will grow a second.

So `/import` is `/import-agent` everywhere, and the per-harness name table,
the `command_name` and `command_slots` helpers, and the `${cmd_*}` slots are
deleted rather than left holding a single entry. `/import-agent` also pairs
with `/import-kb`, which it is routinely confused with: both are now
`import-<what>`, and the difference in the name is the difference in what they
read.

### The rule this settles
A command name that collides with a harness built-in is renamed on every
harness. The framework does not carry per-harness names. `check_templates`
asserts it: the three harnesses must emit the same set of command names, so
re-introducing a rename for one of them fails the mechanical checks rather
than quietly shipping.

## 36. AGENTS.md as a requirements file (2026-09-14, v6.0)

Trigger: "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful
for Coding Agents?" (Gloaguen, Muendler, Mueller, Raychev, Vechev; ETH
Zurich and LogicStar; ICLR 2026 Workshop on Memory for LLM-Based Agentic
Systems). Full reading and the mapping onto this framework are in
`docs/history/agents-md-paper-response.md`. The numbers that decide this section:

- LLM-generated context files: success -0.5% (SWE-bench Lite) and -2%
  (AGENTbench), cost +20% to +23%, across four agent/model pairs.
- Developer-written files: +4% success on average; Claude Code + Sonnet 4.5
  loses 2.5% even with them.
- Overviews: every Sonnet-generated file contained one; agents with a file
  reached the first task-relevant file no faster than agents without.
- Instructions are followed: tools named in the file are used, tools not
  named are not (`uv` 1.6 vs 0.01 uses per task).
- With all repo documentation removed, LLM-generated files help (+2.7%).
- Recommendation: keep a human-written file to minimal requirements, such as
  the specific tooling to use.

### What it falsifies here
§6 ("AGENTS.md as hot-tier transport") and §9 item 5 rest on one claim: an
always-loaded digest of the codebase saves discovery later. The paper
measured that claim and it is false; a digest raises steps and cost and does
not shorten the path to the relevant file. The framework's own benchmarks
had already shown the cost half of this (one-shot overhead +84% to +403% in
`benchmarks/sonnet5-medium-small-2026-07-06/`) and had failed the one
amortization test that was run (`haiku-high-2026-07-04/baseline-comparison.md`).
§6 and §9 item 5 are history from this version on, alongside §1, §2, §4,
§5, §13 and §20. §21's freshness guard (run `/explore` before non-trivial
work because a stale digest costs discovery tokens) is retired for the same
reason.

### What it does not touch
The spec, the sized review gate, the private `.ai` memory, the Stop hook and
the harness axis. The paper varies only the file; it has no workflow layer,
no multi-session setting, no non-Python ecosystem. Those parts keep their
own evidence, which is split (haiku round: a reliability gain; Sonnet 5
round: no gap) and stays open. The harness axis is untouched because the
paper found no consistent difference between harness-specific init prompts,
which supports one skill body per command with fragments only for
mechanics (§27, §30).

### Decisions
1. The generated section is a requirements block, cap ~300 tokens:
   build/test/lint commands verbatim, tools required or forbidden, rules the
   user states, one-line pointers to docs the repo already has. No purpose
   paragraph, no module map, no glossary. Marker text updated; the marker
   prefix `extract_generated` matches on is unchanged, so re-init and
   `/framework-update` still recover it.
2. The module map, stack and glossary go to `.ai/notes/map.md`, a leaf of
   the notes hub (§19), linked from `notes.md`, read when a task spans
   unfamiliar areas. `/build`'s drift check (§18) compares probe's map
   against that leaf and probe's commands against AGENTS.md.
3. `/explore` asks the user before sampling code. The developer-written
   arm is the only one that helped; the questions are the mechanism for
   getting developer knowledge into the file. `probe.py` reports which
   documentation the repo already has (README over 200 words, `docs/`,
   CONTRIBUTING and similar) and `/explore` points at it instead of
   restating it (the paper's redundancy finding, Figure 5).
4. The protocol shrinks to what applies to every task: read notes, the
   spec/build entry, checks green, commit `.ai`, the resume pointer. Gate
   sizing, notes-hub splitting and compaction guidance live in `/build`,
   which the harness loads on demand (§7, finally applied to the
   framework's own text). The `/goal` fragment is compressed to its rule
   and its example. Rendered AGENTS.md before the generated section: 1007
   words in v5.26, about 530 in v6.0 (copilot 560, its CLI note is the
   largest fragment). `check_templates` enforces a 600-word ceiling.
5. The README stops claiming token economy and says what every measurement
   shows: more tokens on a one-shot task, by design. It claims what remains
   arguable: one command set on three harnesses, a review discipline sized
   to the change, memory across sessions.
6. Benchmark: `fixed-runbook.md` gains a C arm (scaffold plus `/explore`,
   no `/spec`, `/build` or review) so the context-file effect the paper
   measured can be separated from the workflow effect the framework claims.
   `count_tokens.py`'s API-call count serves as the step count the paper
   reports. The Sonnet 5 amortization run in `amortization-playbook.md`
   stays the open gate for any token-economy claim.

### Bug fixed alongside
`/build` step 5 still told the agent to propose "re-initializing as large"
above ~10k LOC, a profile v5.22 removed. Deleted; `probe.py` no longer
prints the size-profile boundary either. `check_templates` now fails on
the phrases that described the retired digest.

### Migration
`/framework-update` carries a 5.x scaffold across: the migrate rule splits
the old digest, keeping commands and conventions in AGENTS.md and moving
the rest verbatim to `.ai/notes/map.md` with the hub pointer. Nothing is
re-derived and nothing is dropped.

## 37. Spec and review opt-in (2026-09-14, v6.1)

Trigger: `benchmarks/seq-sonnet5-medium-2026-09-14/report.md`, the first run
of `benchmarks/sequence-runbook.md`. Three pinned tasks on sqlite-utils in
one work dir, framework arm (scaffold, `/explore`, then `/spec` and `/build`
per task) against a baseline arm (no scaffold, cold session per task),
three replications each, every session gated by the orchestrator with
hidden tests the agent never saw.

- Marginal cost of tasks 2 plus 3, framework over baseline: +74%, +160%,
  +136%. Amortization failed 0 of 3 under the rule fixed before the run.
- Task 1 (a bugfix): baseline 3 of 3 gates, framework 1 of 3. Both failing
  framework sessions wrote an acceptance criterion naming the one failing
  test, fixed the wrong LIKE slot in `detect_fts`, saw a second test still
  red, recorded it in `notes.md` as pre-existing, and the reviewer, given
  the diff and that criterion, signed off. Every later session in those
  trees repeated the note.
- Hidden tests for tasks 2 and 3: 6 of 6 on both arms. The notes carried
  the cog gotcha across sessions in two of three framework replications and
  were read in every framework task session.
- Per-call context was equal on both arms. The framework's extra cost is
  extra calls: skill reads, spec, reviewer sub-agent, notes and map upkeep,
  probe re-run, `.ai` commits. None of it shrank from task 2 to task 3.

This is the third negative result on the amortization thesis (§13, §36)
and the first with a correctness loss caused by the framework's own
artifacts. With it, the case for running spec and review on every
non-trivial task is gone for the measured setting: a strong model on a
small repo. The case that remains is unmeasured: weak models (the one
haiku round, n=1, where the framework arm produced the only valid fix),
large repos (Experiment B in `amortization-playbook.md`, never run), and
sessions where a human answers `/explore`'s and `/spec`'s questions (never
exercised; every round ran autonomously).

### Decisions
1. The default path is direct: read, change, run the project's full test
   and lint commands, note what is durable, commit `.ai`. The right-sizing
   rule no longer routes anything to a spec by size.
2. `/spec` and `/build` are opt-in. They exist for a change the user wants
   written down and reviewed before it is called done, and only the user
   starts them. The skills, the reviewer sub-agent and the sized gate (§29)
   are unchanged inside that path.
3. The spec skill always includes a criterion that the full suite and lint
   pass. A criterion naming a single test is what produced today's narrow
   fixes; the reviewer cannot catch a gap the criteria do not state.
4. `/build` records a failing test as pre-existing only after it fails on a
   clean checkout and the test has been read. Notes are acted on by later
   sessions; a wrong note is carried as faithfully as a right one.
5. The `/goal` fragment points at the gate command by default and at the
   spec only when there is one.
6. The README says what the benchmarks support: one command set on three
   harnesses, memory across sessions, an opt-in spec path; and what they do
   not: cheaper or more correct later tasks with a strong model on a small
   repo.

### Protocol findings for the next sequence round
Commit the host tree between sessions (uncommitted diffs from earlier tasks
confused reviewers on both arms and one baseline session discarded a prior
session's edit); close the seed leak (two baseline sessions found the
upstream fix in `git log -p`; use a shallow clone or an orphan seed commit);
run agents in an environment where the project's dev dependencies install,
so self-verification matches the gate.

### Not changed
The harness axis, the skill names, `probe.py`, the requirements block and
the map leaf from §36, `/tidy-up`, `/framework-update`, `/import-*`, the
Stop hook and the allowlist.

## 38. Reduction to two pillars (2026-09-14, v7.0)

Trigger: the owner's decision to reduce the framework to its minimum idea,
taken after §36 and §37 removed the evidence for most of what sat on top of
it. §36 and §37 each cut a claim; this section cuts the artifacts that
existed to serve those claims, and settles which of the original intents
the framework still pursues.

### The five original intents, audited
Recorded verbatim in substance, because the framework has been rebuilt
around the survivors and the record of what was dropped is the point.

1. **A knowledge base holding important project knowledge: user input,
   analysis, domain knowledge, whatever the next session needs.** Survives,
   and is now the first pillar. Refined by evidence: what qualifies is what
   is *not derivable from the repo*. User statements, domain terms,
   decisions and their reasons, gotchas, cross-repo pointers. Analysis
   output does not qualify. A summary the agent produced by reading the
   code is the digest of §6, measured null in §36, and it re-enters through
   this door if the criterion is not stated.
2. **Spec-driven development when wanted.** Survives, made opt-in in §37,
   and re-justified here. The claim is no longer that a written spec plus a
   fresh-context review catches more defects; that evidence is split and the
   one measured correctness loss came from a spec. The claim is that a plan
   read before any code exists is the cheapest point at which a human can
   redirect the work. This is a smaller claim and it does not depend on
   amortization.
3. **Task-based work on several parallel tasks, tracked by the spec's
   status.** Alive as an intent, never actually built. `.ai/.current` holds
   one active change id; nothing in the protocol supports two in flight, and
   no round ever exercised it. The mechanism the harnesses now offer is a
   git worktree per task with its own session. Decision below keeps the
   `status:` field (one line, and the only index across parallel change
   directories) and scopes `.current` to the working tree rather than the
   project, so two worktrees do not overwrite each other's resume pointer.
   Parallel work remains unmeasured; the framework does not claim it works.
4. **AGENTS.md as steering, so the agent has a rough idea what is in the
   project instead of re-exploring it every session.** Falsified. This is
   §6 and §9 item 5 stated as the intent that produced them. The ETH round
   measured exactly this mechanism and found agents with a context file
   reached the first task-relevant file no faster than agents without,
   across SWE-bench Lite (django, sympy, scikit-learn among them) and
   AGENTbench's 12 niche repos. Both ends of the size range, same null.
   Search is cheap and roughly flat in repo size; the discovery cost the
   intent assumed is not there to save. AGENTS.md keeps the half that did
   measure: naming a required tool causes it to be used (1.6 vs 0.01 uses
   per task). It steers what the agent *does*, not what it *knows*.
5. **Token efficiency.** Falsified as a net claim and not made anywhere in
   the framework's text. Every round measured more tokens, by design: one
   shot costs +84% to +403% (§36), tasks 2 and 3 cost +74% to +160% (§37).
   What survives is a bounded-footprint claim, which is different and true:
   the framework's own always-loaded text is capped (AGENTS.md under 600
   words, its generated block under ~300 tokens, enforced by
   `check_templates`), and everything else is read on demand. The framework
   is economical about itself; it does not make the session cheaper.

### Consequence for the amortization thesis
§13 staked the thesis on medium and large repos on the grounds that cold
discovery is expensive there. Intent 4 is that thesis's premise, and the
premise is what §36 measured null, at size. A fourth negative round on a
bigger repo would buy little. The thesis is retired rather than left open.
`amortization-playbook.md` is withdrawn with it: it now opens with a
superseded header, Experiment B (navigation2, never run on any model) is
removed from it and survives only in git history, and Experiment A is marked
as answered by the 2026-09-14 sequence round. Its scaffold command had also
stopped working, since it passes the `--size large` flag that 5.22 removed. §37's list of
unmeasured cases is rewritten: weak models (the one haiku round, n=1),
**density of non-derivable context** (replacing "large repos"), and
sessions where a human answers the questions. The successor experiment is
the constraint-carrying round described under "Next measurement" below,
which costs a fraction of Experiment B.

Residual possibility, recorded so it is not lost: on a repo whose *build*
is the hard part (colcon, rosdep, a package graph), what a warm session
carries is build knowledge, not a module map. That is a control claim, it
belongs in `.ai/notes.md`, and this reduction is consistent with it.

### Decisions
1. Two pillars, stated in the README and in AGENTS.md: durable non-derivable
   project knowledge, and an opt-in spec-and-build path. Nothing else is a
   framework claim.
2. Cut list. Each entry is removed from the scaffold; §24's retirement
   mechanism (drop the `write()` call, `/framework-update` deletes the file
   via the recorded `framework_files` list) carries existing projects.
   - `/tidy-up`: a hygiene sweep, orthogonal to both pillars.
   - `/import-kb`: vestigial since v5.22 removed the KB profile.
   - `/import-agent`: a one-time on-ramp. With the target shape at six
     files, converting an existing setup is a plain request to the agent,
     not a skill the scaffold must carry forever.
   - `.ai/notes/map.md` **as framework output**: the last remnant of the
     digest. §36 relocated it instead of deleting it on the theory that
     on-demand it still pays; intent 4's audit removes that theory. Nothing
     generates or maintains it after this version. Existing files are notes
     content and are never deleted by an update (migration rule below).
   - `/build` step 5's drift check: without a map it reduces to "did the
     commands change", which the agent learns when a command fails.
   - `probe.py` shrinks from an inventory tool to command detection plus
     documentation detection. The module map, the LOC table (already ruled
     unactionable in §36) and the entry-point candidates go. It is updated
     in place, not retired, so the path the instructions verify is stable.
   - The archive protocol in AGENTS.md: `status: done` plus moving to
     `changes/_archive/` becomes one sentence. Existing `_archive/`
     directories are untouched.
   - The `/goal` fragment in AGENTS.md: harness usage advice, not a project
     requirement. Moves to the README.
3. Skill roster after the cut: `explore`, `spec`, `build`,
   `framework-update`. `/explore` loses its probe-inventory and map steps
   and becomes the Q&A plus the requirements block, which is the arm that
   measured positive (+4%, developer-written).
4. `.ai/.current` is scoped to the working tree, so parallel change
   directories in separate worktrees do not overwrite one another's resume
   pointer. `status:` stays in the spec frontmatter as the index across
   them.
5. Retained unchanged: `.ai` as its own private repo, the Stop hook that
   enforces committing it, the allowlist, the `reviewer` sub-agent and the
   sized gate inside `/build`, the harness axis, the version stamp, and the
   `GENERATED:project-context` marker prefix (so re-init and update still
   recover a project's own content).
6. Target shape, claude harness: `AGENTS.md`, `CLAUDE.md` pointer,
   `.ai/notes.md`, four skills, `reviewer.md`, the hook plus
   `settings.json`, the stamp, and the reduced `probe.py`. Rendered AGENTS.md
   before the generated section: 394 words on claude (the framework text
   itself, down from about 530 in v6.0), 486 on copilot and 485 on hermes,
   where the balance is the harness's own CLI mechanics note rather than
   protocol. `check_templates` lowers the ceiling from 600 to 500, bans the
   retired command names, and bans the `notes/map.md` path everywhere except
   the update body, which has to name the leaf to say it must not be
   deleted. `probe.py` drops from 267 lines to 190.

### Migration rule
`/framework-update`'s migrate fragment gains the 7.0 entry. The governing
principle is unchanged from §24 and `write_owned`: framework output is
retired, user knowledge is never destroyed.

1. Retire `/tidy-up`, `/import-kb` and `/import-agent` as ordinary retired
   files, including the orphan test in step 3 and the grep that removes
   instructions still pointing at them.
2. `.ai/notes/map.md` is **not** deleted and its hub pointer in
   `.ai/notes.md` is **not** removed. It became ordinary notes content the
   moment the framework stopped generating it, and the user may have edited
   it. Report it as "no longer maintained by the framework; trim or delete
   it yourself". Deleting a notes leaf during an update is forbidden.
3. `probe.py` is updated, not retired. A project that pinned or edited it
   follows the normal merge case.
4. AGENTS.md: the generated block is carried across untouched, as always;
   hand-appended user rules are preserved by the existing merge case. The
   archive paragraph and the `/goal` fragment are dropped from the
   framework's half only.
5. Existing `.ai/changes/<id>/spec.md` files are left as they are. The
   frontmatter shape did not change, and `_archive/` contents are not
   touched.
6. `.ai/.current` is gitignored and per-tree; an existing one is left in
   place.

Sequencing: v7.0 ships with `/framework-update` intact, because the
retirement mechanism is what executes this demolition on projects already
in the field. Whether a slimmer update skill survives a framework this
small is a question for a later version, not this one.

### Next measurement
The reduced framework makes only control claims, so the round that tests it
is a control round, not an amortization round. Reuse the sequence runbook's
seed, gate and replication discipline, and change one thing: the tasks must
require honoring constraints that are **not discoverable from the
repository** (a tool that must be used, a module that must not be touched, a
convention stated once in session 1). A baseline agent cannot know them; the
framework arm has them in the requirements block and the notes. If the
framework does not win there, the control thesis is dead too and the
framework reduces further, to memory plus an opt-in plan preview. This also
exercises the human-answered path that §37 flagged as never run, since
injecting the constraint is what `/explore`'s Q&A is for.

The cheapest open arm remains a rerun of the 6.1 sequence at haiku: the only
positive result the framework has ever produced is n=1.

### Not changed
The harness axis, the skill names that remain, the private `.ai` repo and
its Stop hook, the allowlist, the `reviewer` sub-agent, the sized gate, the
version stamp and the generated-section markers.

## 39. Plan-and-do for any task (2026-09-28, v8.0)

Trigger: the owner's daily work. About half of it is code changes; the other
half is investigating, hunting bugs, researching, and testing. The opt-in
path fit only the first half: a spec's tasks named files, its one fixed
criterion was a green suite, and `/build` reviewed a diff. An investigation
has no diff, and "checks green" says nothing about whether a question was
answered.

### The argument
Pillar 2's stated value was never specific to code: it is the plan a human
reads and redirects before work starts (§37, §38). What was code-specific is
the definition of done and the shape of the review. Generalizing those two
keeps the pillar's claim and widens where it applies. Nothing becomes a
default, so the rule for future changes is not engaged.

Three things matter more for a non-code task than for a change, which is why
the generalization is more than a rename:

1. **Resume state.** A change keeps its state in the diff. An investigation
   keeps it only in the session, and compaction or the next day loses it.
   The Findings section, written as findings happen, is that state.
2. **Hypothesis discipline.** Steps for a bug or an investigation are
   hypotheses with a check each, cheapest first. A ruled-out hypothesis is
   struck with its evidence in the file. This extends the old "a test fails
   twice, rethink" rule to "two hypotheses die without a new lead, rethink",
   and makes drift from the plan visible instead of silent.
3. **Evidence-checked review.** The review of an Outcome checks that every
   claim cites evidence produced in this task, not inferred. Plausible but
   unverified conclusions are the characteristic failure of an agent
   answering a question, and the diff review never looked for them.

It also closes a loop between the pillars. Notes grew from `/explore` and
from correction (7.1). The findings of a bug or an investigation are almost
always what the repository cannot state (a root cause, how a subsystem
behaves at runtime), so `/task-do` ends by distilling them into
`.ai/notes.md`. That makes the task path the richest source of Pillar 1
content.

### What it costs, stated plainly
No round measured a non-code task, and none is planned: the measurement
program halted on 2026-09-14 and this is an organizational argument, which
is where Part II says the framework's value lies. The plan chain costs what
the spec chain cost, 2.1x to 2.5x the direct path; for a short question it
is overhead and the direct path remains the default. AGENTS.md grew by 10
words on claude and 11 on hermes and shrank by 10 on copilot, whose CLI note
now shows one generic "read the prompt file and follow it" line instead of
a paraphrase per command. The scaffold gained one tool, `tasks.py`, and one
skill.

### Decisions
- Names: `/task-create`, `/task-do`, `/task-list-all`, chosen by the owner.
  `/plan` was not an option: Hermes reserves it and the check already bans
  it, and Claude Code's plan mode already uses the word.
- Four types, not five: research folds into `investigation`. The type decides
  done; two types with the same done-when are one type.
- A code-changing task of any type takes the full-suite criterion. The one
  measured correctness loss came from a criterion naming a single test, and
  a bug fix is where that happens most easily.
- `status` gains `blocked`, because investigations and tests wait on
  hardware, access or other people far more often than changes do.
- `/task-list-all` is a script plus a thin skill. The table is deterministic
  work (§16); the agent adds at most three lines the table cannot show
  (stale in-progress, blocked reason, done with unchecked criteria).
- `.ai/.current` starts `task: <id>` so the script can mark it.
- The `reviewer` sub-agent reviews a diff, an Outcome, or both.

### Migration
`/framework-update` retires `/spec` and `/build` as ordinary retired
framework files and migrates the content: `git mv` of `.ai/changes/` to
`.ai/tasks/` and of each `spec.md` to `task.md`, `_archive/` included;
`type: change` and `updated:` added to the frontmatter; `Acceptance
criteria` renamed `Done when` and `Tasks` renamed `Steps`; empty Findings
and Outcome added. Every goal, criterion, task line and checkbox state is
kept as written. `tasks.py` flags a leftover `.ai/changes/` so an
unmigrated project is visible in the table.

### Not changed
Pillar 1, `/explore`, the hooks, the private `.ai` repo, the sized review
gate, the fresh-session rule, the version stamp, and the opt-in principle.

## 40. The update reads the target version's migrations (2026-09-28, v8.1)

Trigger: reviewing whether `/framework-update` moves a 7.1 project's specs
to tasks (§39). It does not. The skill a project runs is the copy scaffolded
with that project, and its migrate list is frozen at that version: the 7.1
copy has no 8.0 entry, and its 7.0 entry says to leave existing specs and
`_archive/` exactly as they are. The 8.0 migration exists only in the 8.0
copy, which the update installs but does not follow. Every earlier shape
change had the same exposure; 7.0 and 7.1 changed no hand-filled content, so
it never showed.

### Decision
Step 4 of the update body now tells the agent that its own list is stale by
construction and that the authoritative list is step 4 of the reference's
copy of the skill, which step 2 has already rendered from the current
generator. The agent applies every entry newer than the recorded version,
and the reference wins where the two disagree. An entry also applies when
the stamp already names the new version but the content it migrates is
still present, so a second run repairs an update that skipped a migration.

The path differs per harness (`.claude/skills/framework-update/SKILL.md`,
`.agents/skills/framework-update/SKILL.md`,
`.github/prompts/framework-update.prompt.md`), so it is a slot, and
`check_templates` renders a reference per harness and fails if the named
file is absent. A wrong path would fail silently in the field: the agent
finds nothing and falls back to the stale list.

### What it does not fix
Projects already on 7.1 or 8.0 run a copy without this instruction. Their
first update to 8.1 or later installs it; the spec-to-task move then needs
a second `/framework-update` run, or the plain request to migrate
`.ai/changes/` as step 4 of the installed skill describes. `tasks.py` flags
a leftover `.ai/changes/`, so the gap is visible rather than silent.

## 41. One /task command, a script decides create or do (2026-09-30, v9.0)

Owner's request after the satty runs of 8.3 to 8.11: three commands for one
object is two too many, and "does this task exist?" should not depend on how
an agent searches. `/task-create`, `/task-do` and `/task-list-all` become
`/task create|do|list`; the bodies keep their rules word for word, so every
fix of 8.3 to 8.11 carries over.

The create-or-do decision moved into `tasks.py resolve`, for the reason 8.4
moved the table there: parsing is deterministic work. An agent asked to find
out whether `fix-login` exists will grep, guess from titles, or miss an
archived task; the script checks the live and archived directories,
case-insensitively, and reports near-duplicates (difflib ratio 0.6, or two
shared id words of three letters or more) as `SIMILAR`, which the skill
turns into a question instead of a second task.

An investigation no longer stops after planning. Its plan is a list of
hypotheses with checks, and writing that list is most of the investigation;
stopping for a human to approve it bought a pause and nothing else. It also
asks nothing after the type: the decision it feeds and when to stop looking
become numbered assumptions in Notes, visible in the result. The other types
keep the stop: a change, a bug fix or a test campaign acts on the code, and
the plan shown before that is the point of Pillar 2.

Name: `/task`, singular. `/tasks` is taken in Copilot CLI and as a Hermes
alias of `/agents`; both are now in `check_templates`' reserved list.

Verified on satty `f578432` (2026-09-30), one task per type on Claude Code
(sonnet-5.5) and Copilot CLI (Auto), without a Rust toolchain, cargo
criteria waived where files changed: all eight reached `done` with every
criterion ticked, a `Review:` line, and citations that hold on inspection.
Every run called `tasks.py resolve` first. Two defects surfaced and were
fixed in the skill before the acceptance runs that count:

- Claude ran an investigation as one write: plan and result together, no
  `task: create` commit, no `in-progress`, no `.ai/.current`. "Continue
  straight into Do" was read as "skip Do's bookkeeping". The skill now keeps
  the phases apart in the record; the re-run committed the plan, set the
  pointer, and closed with `task: done`.
- Copilot answered `list` with a bullet summary after reading `tasks.py`
  itself. In the combined file the List section sits at the end, 200 lines
  after the instruction that sent it there; 8.9's standalone file had
  passed. `list` is now handled completely in Dispatch, at the top, with
  the instruction not to read further; both harnesses then printed the
  table verbatim.

Remaining, not a rule failure: Copilot once named a done commit after the
change rather than `task: done <id>`.

## 42. Execution rules for models that think on their own (2026-10-04, v9.1)

Source: Anthropic, "Getting the most out of Opus 5.5"
(https://claude.dev/blog/getting-the-most-out-of-opus-5-5/). Owner's report
before the change: easy tasks feel slow, the agent overthinks or inflates
them.

The guide's points, checked against 9.0:

- No "think step by step" or "think carefully" lines: none in any template.
  Nothing to do; effort is a harness setting, not prompt text.
- Name the finish line: `/task` has Done-when; the direct path has rule 2.
- A checklist that survives compaction: `.ai/.current` and Findings.
- Check sub-agent evidence: the review gate and the `reviewer` brief.
- Keep going, status in the same message as the next action, stop only when
  blocked or before destructive actions: missing. Added as `## Execution`.
- A fixed run summary (Blocked on me, Changed, Found): missing. Added.
- "Treat an answered question as done": missing for the direct path, where a
  long session is most likely. Added.

One addition of our own: the direct path said to append to `.ai/notes.md`
"if a decision, gotcha, or finding emerged", which together with the turn-end
hook nudges the agent to find something to write on every task. It now says
most direct tasks add nothing.

Decided with the owner, point by point, after the first cut:

- Type question (v8.3): still asked, never inferred, but in one message
  with the done-when Q&A instead of a separate round trip first. TC-C1
  updated.
- Review gate (v8.6): size alone sent a 40-line rename to a sub-agent.
  Inline now also covers a mechanical diff (rename, move, reformat,
  regenerated file, no logic changed); the Review line names why, so the
  choice stays checkable.
- Suite runs (rule 2): iterate on the tests covering the change, the whole
  test and lint suite once before done. Docs or comments only: no suite
  run. The guarantee at done is unchanged; only the runs in between drop.
- Citations (v8.10): every citation the Outcome rests on is opened, as
  before; citations in Findings the Outcome does not use (ruled-out
  hypotheses, side notes) are spot-checked, up to three. The v8.10 failure
  was in the Outcome and stays covered.
- Skill size: `/task` was 13 KB and loaded whole for every call, `list`
  included. Split: the skill keeps Dispatch and List; Create and Do move to
  `.ai/agent/task/create.md` and `do.md`, one harness-neutral copy beside
  the tools, read only after `tasks.py resolve` names the branch. Risk, from
  v9.0: Copilot drifted in a long combined file; whether every harness
  reads the part file before acting needs a Layer 2 run on all three.
- Effort (Claude only, verified against code.claude.com docs, skills and
  sub-agents pages, 2026-10-04): `effort` frontmatter on each skill,
  `medium` for `/task` and `/explore`, `high` for `/framework-update`, and
  `high` on the `reviewer`. No project `effortLevel`: the direct path keeps
  each user's own default. Copilot and Hermes document no equivalent.
- Working on the framework (repo `CLAUDE.md`, `TESTING.md`): Layer 1 only
  for changes under `templates/`, `agentgen/`, `tests/` or to
  `init_agent.py`; docs-only edits run `check_templates` alone. Agents read
  Part I and append to Part III without reading it.

Not measured yet. Layer 2 check: a trivial change on a live repo should end
in one turn, with no status-only message, no note, and the three headings.


Layer 2, 2026-10-04: satty at `f578432`, harness claude, Framework 9.1
(`c7a43a7`), model claude-opus-5-5 at the user's default effort `high`
(`/task` carries `medium`), cargo not on PATH. Driven headless (`claude
-p`, Q&A answered with `--resume`), so questions came as text, not the
question UI. satty was an untrusted workspace, so the scaffold allowlist
was passed with `--allowedTools`. The runner has RTK installed, whose
global hook rewrites commands to `rtk ...`. Every permission denial in the
run held a command off the allowlist (`gh`, `sed`, `cargo`, `mkdir`, a
heredoc), so RTK caused none of them: its hook itself answers `allow` for a
chain made only of allowlisted commands.

- TC-C1 PASS. The first message asked the type (all four offered) as
  question 1, with the done-when questions in the same message; no file
  was written before the answer. The agent said it would guess `change`
  but left the choice open. After `change`: `type: change`, one commit
  `task: create config-errors-no-abort`, no `.ai/.current`, no host change.
- TC-C1b PASS (Claude only). All four create sessions ran `tasks.py
  resolve` and then read `.ai/agent/task/create.md` before acting. The
  investigation read `do.md` only after its `task: create` commit. `/task
  list` ran `tasks.py` and read neither part file. Copilot and Hermes are
  not yet run.
- TC-C2 PASS. bug, investigation and test: no type question; full
  frontmatter and six sections; done-when fits the type (bug: root cause,
  repro failing before and passing after, full suite; investigation:
  answer with evidence or inconclusive; test: one result per scenario,
  full suite). Bug and investigation steps are hypotheses with a check
  each. Bug and test asked their Q&A and stopped at `planned`. The
  investigation committed its plan alone (`status: planned`) and then
  continued into Do in the same session, as `create.md` says since 9.0;
  it ended `done` with 2/2 criteria and no host change. The runbook's "work
  not started" for TC-C2 predated that rule and now exempts investigation.
- Observed: every final message ended with Blocked on me, Changed and
  Found. Two runs still wrote to `.ai/notes.md`, one a rendering gotcha
  (investigation, fits) and one "this Mac has no Rust toolchain" from a
  test create, a machine fact rather than project knowledge.

RTK and the git guard (2026-10-04, same version). The guard matched `gh`
only as the first word and saw a `rtk run "<line>"` string as one word, so
`rtk gh pr merge`, `rtk proxy gh pr merge` and `rtk run "git merge main"`
passed while on the default branch. RTK's hook rewrites commands to that
form and its docs teach agents to type it. The guard now unwraps a leading
`rtk` (with `proxy`, or `run` and its string) before judging each segment.
`tests/test_git_guard.py` pins both the bare and the proxied forms; it
fails five cases on the old hook. Not covered, as before: a line inside
`sh -c`, and `gh` after `env` assignments (`git` after `env` is caught).

## 43. Hermes support dropped (2026-10-04, v10.0)

Owner's decision: drop the Hermes harness completely. A change that removes
an artifact needs no argument against a measurement (Part I); this one
removes a whole harness, so Property 3 now reads two harnesses, not three.

What went:

- The render path: `render_hermes_skills`, the dispatcher and the
  `hermes-hooks.yaml` snippet, the hermes AGENTS.md and skill fragments,
  `HERMES_DESCRIPTIONS` and the hermes argument wording, the `extra.attempt`
  loop guard in `ai_repo_clean.py`, and the `check_templates` hermes check
  (60-character descriptions, built-in collisions). The check that every
  harness emits the same command names stays, as `names`.
- `hermes` as a harness choice for a new scaffold.

What stayed, and why:

- `/framework-update` keeps its name. Hermes reserving `/update` was the
  reason for it, but renaming a command breaks every existing project,
  and the rule that a collision renames on every harness still holds.
- Recognizing a Hermes scaffold (`RETIRED_HARNESSES`, the `.agents/skills`
  detection, the `hermes` entry in `HARNESS_ENTRY_PATHS`). Without it a
  Hermes project would get a bare argparse error, and the switch could not
  report the files it left behind. `--harness hermes` stays a valid
  argparse choice for the same reason.

The path off Hermes is the existing harness switch: `init-agent --harness
claude` (or `copilot`) writes the new set and moves every recorded
`.agents/` file into `.ai/agent/.harness-backup/hermes/`, keeping notes,
tasks and the project context. init with `--harness hermes`,
`--emit-reference --harness hermes` (what an old Hermes `/framework-update`
runs) and `--bootstrap-update` on a Hermes tree all exit 1 with those
instructions. A re-init naming no harness prints them and defaults to
claude. The profile entries in `~/.hermes/config.yaml` and the installed
dispatcher are outside the repository, which init never touches; the
message names them, and leaving them is harmless because the dispatcher is
a no-op without `.agents/hooks/`.

Test: `test_harness_switch.py` now switches claude to copilot, and its new
`off_retired` case builds a real Hermes scaffold with the 9.0 generator
from git history (`216e269` on main), checks the refusal and the message,
and checks that the switch retires all seven recorded `.agents/` files into
the backup with the notes intact. It skips on a shallow clone.

## 44. Task bookkeeping moves into tasks.py (2026-10-04, v10.1)

Source: the Layer 2 round 2 in section 42. Of the observations recorded
there, the permission friction is the one the framework causes. `do.md`
asked for five bookkeeping acts (set `in-progress`, write `.ai/.current`,
set `blocked` with a reason, set `done`, delete `.ai/.current`) and said
what, not how. Agents filled the gap with `printf > .ai/.current`, `rm
.ai/.current`, `sed -i` and Python heredocs on the task file, and committed
with `git -C <absolute path>/.ai`. The read-only allowlist matches none of
these, and a project path cannot be put in a template. Interactive sessions
prompt for each; headless runs deny them, which cost TC-D4 most of its 63
turns and left TC-D2 with `.ai` uncommitted. RTK was ruled out: its hook
auto-allows the relative `git -C .ai` chain and leaves the rest alone, and
0.51.0 fixed the doubled `-U0` diff output seen in the same round.

Change:

- `tasks.py start <id>`: `status: in-progress`, `updated:`, a `blocked:`
  line dropped, `.ai/.current` written, or kept when it already names the
  task so a resumed task keeps its `modified:` list.
- `tasks.py finish <id> blocked <reason>`: `status: blocked`, the one-line
  `blocked:` reason, `.ai/.current` kept for the resume, which TC-D3
  expects.
- `tasks.py finish <id> done`: refuses, exit 1, while a done-when
  criterion is unticked or Findings has no review line, the two things the
  table flags on a `done` task; otherwise sets the status and deletes
  `.ai/.current`. A rule `do.md` only stated is now checked.
- Both edit only the frontmatter block and `.ai/.current` and print the
  commit to run; neither commits, since committing `.ai` stays the agent's
  act under protocol rule 1 and the turn-end hook.
- `do.md` routes step 1, the block rule and step 8 through the script and
  says, once, to change status only that way, to edit task sections with
  the file-editing tool, and to commit with the relative `git -C .ai` from
  the project root. `create.md` step 5 names the same commit form.

Considered and dropped: a rule keeping machine facts ("no Rust toolchain on
this Mac") out of `.ai/notes.md`. `.ai` is private to one checkout, so such
a fact is real knowledge for the next session there; it looked like noise
only because the runbook removes `cargo` on purpose. The one note that was
wrong, a dated "checkout is behind main", came from the pinned detached
checkout; a rule waits for a second sighting outside that setup.

No AGENTS.md text changed (copilot stays at 644 of 650 words). Tests:
`test_tasks_table.py` covers start, finish done (refused and accepted),
finish blocked (reason required, written, flagged), resume clearing the
block, and the frontmatter rewrite leaving the body byte for byte. Runbook:
a bookkeeping criterion for every do case, and the three cases round 2 ran
outside the runbook, TC-D5 (mechanical diff, inline review), TC-E1 (trivial
direct change in one turn) and TC-E2 (an answered question stays settled).
Layer 2 for this change: rerun TC-D2, TC-D3 and TC-D4.

Layer 2 (2026-10-04): satty at `f578432`, scaffold from this branch
(`25548f3`, v10.1), harness claude, claude-opus-5-5, cargo not on PATH,
RTK 0.51.0, headless (`claude -p`, allowlist via `--allowedTools`), the
mode that produced round 2's failures. Bookkeeping denials count only
commands that set status, write or delete `.ai/.current`, or commit `.ai`.

| Case | Round 2 (10.0) | This run (10.1) |
|---|---|---|
| TC-D4 do | 63 turns, 7 denials, 6 bookkeeping | 60 turns, 11 denials, 0 bookkeeping |
| TC-D2 do | 65 turns, 16 denials, 5 bookkeeping, `.ai` left dirty | 47 turns, 9 denials, 1 bookkeeping, `.ai` clean |
| TC-D3 do | ran interactively | 22 turns, 4 denials, 0 bookkeeping |

- TC-D2 PASS, and round 2's defect is gone. 103-line diff, `reviewer`
  sub-agent, `done`, waiver marked, `.ai` committed. Transcript: `tasks.py
  start`, relative `git -C .ai` commits, `tasks.py finish ... done`. The
  one bookkeeping denial was a `sed -i` to tick boxes; the agent fell back
  to the edit tool.
- TC-D3 PASS. After the neutral runbook answer the agent ran `tasks.py
  finish ... blocked "<reason>"`: `status: blocked` with the reason,
  `.ai/.current` kept, ⛔ ❗ 👉 in the table, `.ai` clean.
- TC-D4 PASS on bookkeeping (`start`, `finish done`, relative commits,
  `.ai` clean), FAIL on its review criterion: a 27-line diff with a
  one-line Outcome went to the `reviewer` sub-agent instead of inline.
  The reviewer found four wrong claims in the prose, all fixed. Not caused
  by this change; recorded for the review-sizing rule.

What 10.1 did not fix: the turn count of D4 barely moved. Its bookkeeping
denials went from 6 to 0, but exploration denials went from 1 to 11 (runs
vary in how they explore), and those the allowlist cannot match: `sed -n` ranges,
`$(...)` command substitution, `git -C <absolute path> diff` on the host
repo, and heredocs. The allowlist matches none of them. In a headless run a
denied `cargo` also hides that cargo is missing: TC-D3's agent concluded
cargo "needs approval" and wrote that to `.ai/notes.md`.

## 45. /task tree: the dependency view (2026-10-15, v10.2)

Source: a user with several live tasks asked which one to unblock first;
the flat table answers "what is open" but not "what waits on what".

Change:

- Task frontmatter gains an optional `depends:` line: comma-separated
  ids of live tasks this task waits on. `/task create` asks for it in
  its Q&A and writes the line only when non-empty. Old task files need
  nothing: the frontmatter parser tolerates unknown keys and the
  bookkeeping rewrites preserve them byte for byte.
- `tasks.py tree` prints live tasks as an ASCII dependency tree with
  the branch characters bash `tree` uses. The tree hangs under the
  project name (the `project` key of `framework.json`, else the
  directory name); on the first level stand the tasks that block
  others, what waits on them nests below, and every task appears
  exactly once at its shallowest position (a task with two dependencies
  sits under the first of them in sort order, not twice). A done task
  stays on the first level: it is the blocker that cleared. Tasks with
  no dependency ties end on one `independent:` line. Status emoji, the
  resume pointer (before the task's line), the blocked reason, the
  legend and the summary footer are reused from the table. A `depends:`
  id that names no live task (unknown or archived) is flagged below the
  tree and ignored; a task whose whole chain is unresolvable stands on
  the first level; a dependency cycle is flagged once and shown from
  its first task in sort order, with the tasks waiting on it nested
  below, so the output stays deterministic. The
  view is read-only; `/task list` is unchanged.
- The `task` skill dispatches `tree` like `list` (the script's output,
  verbatim, as the whole reply; no file reads) and `ARG_HINTS` names
  the new subcommand.

The tree is a view, not a scheduler: `depends:` records an ordering
constraint, nothing runs or plans tasks in parallel. Tests:
`test_tasks_table.py` covers the nesting, appear-once-at-shallowest
(the diamond), the independent line, the cycle and unknown-id warnings,
the blocked annotation, the resume pointer on a nested task, a done
task as root, and both empty states. Runbook: TC-L2.

## 46. /task tree: cycle handling (2026-10-15, v10.3)

Review of section 45 found three defects in the cycle sweep: a task
waiting on a cycle appeared twice (nested and again on the first
level), one cycle was reported a second time under a path that was no
cycle, and a self-dependency read as a one-element cycle. The sweep now
walks each unreached task's first dependency upstream; a cycle it finds
is flagged once in edge order (`b -> a -> b`, a self-dependency as
`s -> s`), shown from its first member in sort order, and everything
downstream of it nests below. Tests: `test_tasks_table.py` adds a task
waiting on a cycle and a self-dependency.

## 47. /task tree: independents on the first level (2026-10-27, v10.4)

Source: a user with eleven independent tasks read the trailing
`independent:` line as an afterthought: one comma-separated run of ids
with no status emoji, no blocked reason and no resume pointer, detached
from the tree the other tasks stand in. The tree now puts a task with
no dependency ties on the first level under the project name, as a
leaf, after the tasks that block others and the cycles, in the same
sort order (status, then updated, then id). Its line carries the
status emoji, the blocked reason and the pointer like any other task.
The `independent:` line is gone. What counts as independent is
unchanged: nothing it waits on after pruning and nothing waiting on
it; a task whose every dependency is unresolvable still stands on the
first level with its warning. Tests: `test_tasks_table.py` checks the
independents close the first level in sort order and that no
`independent:` line is printed. Runbook: TC-L2 amended.

## 48. /task tree: placement fixes (2026-11-01, v10.5)

A code review of sections 45 to 47 found four defects in `tasks.py
tree`, each reproduced on throwaway task directories:

- Placement was depth-first: a task sat wherever the walk reached it
  first, not at its shallowest position. `b` waiting on `t` and `a`
  (with `a` under `t`) landed under `a`; `x` waiting on `a` and `t2`
  landed three levels down under `t1`, and `t2` showed as a leaf.
- Branch characters were chosen while the walk still moved siblings
  into earlier subtrees, so a last child could keep `├── ` and its
  descendants a stray `│`.
- The cycle check ran only on tasks no first-level task reached; a
  cycle below a task that blocks others nested without a warning.
- `depends:` ids matched case-sensitively, unlike `resolve`; `depends:
  bug-7` on a task directory `BUG-7` was flagged unknown and dropped.

Change: the first level comes from the dependency graph's strongly
connected components; a component that waits on nothing outside
itself is a first-level entry (from its first task in sort order).
A breadth-first pass from the first level gives each task its least
depth, and the task nests under its first dependency in sort order one
level up. Child lists are complete before drawing, so `└── ` marks the
last sibling. Every cycle is flagged once, in edge order from its first
task in sort order; `shown from` is added only when the cycle stands on
the first level. Ids match without case. The 10.2 fixture had baked in
the depth-first answer (`deep-a` under `mid-task` although it names
`root-task`); its expectation now follows the spec. Tests:
`test_tasks_table.py` adds the four review cases.

## 49. /task create asks for the tracker issue (2026-11-02, v10.6)

Source: the owner's teams plan work in trackers (GitHub issues, Jira),
so a `/task` task usually mirrors a ticket; until now the task file
never named it, the plan ignored the ticket's own description, and
nothing tied `12345` in a branch name back to a task.

Change:

- Create's first question, in the same message as the type question
  (TC-C1's one-message rule is unchanged), is whether a tracker issue
  exists for the task: an issue key, a URL, or none. An id or prompt
  that already names one (`/task create 12345-fix-ci-crash`, `issue
  #663`, a tracker URL) answers it and nothing is asked. The answer
  `none` is normal: Create offers once to file the issue from the
  Goal, and a decline stands.
- The issue's key becomes the task id's prefix (`12345-fix-ci-crash`,
  `PROJ-123-fix-ci-crash`), and the title is the id's words as a
  title, so the key leads both; a task sorts and greps with its
  ticket. `tasks.py resolve` rejects the bare key without a slug as
  INVALID, with the fixed form in the message; a CREATE verdict on an
  issue-prefixed id prints that the tracker question is answered.
- The fetched issue (title, body, open comments) feeds the Goal, the
  Done-when criteria and the Steps on equal footing with the user's
  input; a conflict between the issue and the user is the user's call
  and is asked. The task file gains a `## Tracker` section: key, URL,
  state, and a digest of what fed the plan, verbatim enough that
  `/task do` works from the file and never queries the tracker again;
  with no issue it says `none` and why. Old task files need nothing:
  the section is optional and nothing parses it.
- Which tracker access a checkout has is deterministic discovery, not
  the agent's guess: `tasks.py trackers` prints `.ai/trackers.conf`
  rows (`name`, `kind`, `command`), a detected `gh` CLI with the repo
  it resolves to, and a `jira` CLI on PATH. Read-only, stdlib only;
  the config file is hand-filled project knowledge and stays out of
  the frontmatter so no parser changes.

The task file remains the handoff: everything Do needs from the issue
is written down at create time, so the fresh session works offline of
the tracker. Tests: `test_tasks_table.py` covers the INVALID key
prefix, the CREATE note on an issue-prefixed id, and `trackers` with
config, without config, and with a fake `gh`. Runbook: TC-C3 (asked,
fetched, prefix, section), TC-C4 (declined, offered once, `none`).

## 50. /task do on a supervised cheaper-tier worker (2026-11-01, v11.0)

**Source.** Google's Elephant-Goldfish Model (EGM, open-sourced October
2026, github.com/google/elephant-goldfish-model, Apache-2.0). Its roles:
"Elephant holds your project context and drafts the specification.
Goldfish reviewers examine the draft and referenced source material
without the earlier conversation." A goldfish gets the document and the
files it links, never the conversation; if the harness cannot spawn a
fresh context the review stops, because "a review in the same context is
not a Goldfish review." Findings flow back to the elephant, which fixes or
contests each; loops are capped (five rounds, two clean rounds to
converge). EGM itself applies the pattern to design review only and says
nothing about model tiers. A third-party port (vshvedov/elephant-goldfish)
carries it into implementation: a no-code gate, then the elephant builds
and a goldfish reviews the diff.

**The mapping.** The framework already had the EGM shape for review: the
`/task do` gate's `reviewer` is a goldfish (task file and diff only). 11.0
turns the same idea one step earlier and makes the worker the goldfish.
The task file is EGM's design doc: written by `/task create` with the
user, it is the whole input. The `/task do` session is the elephant: it
holds the user, the notes and the verification history across rounds, and
writes nothing but Findings, Outcome and notes. The worker starts with no
conversation, which is the point: whatever the user said and the file
does not hold, it cannot act on, so the supervisor must move it into Notes
first, and a gap in the file becomes visible instead of being bridged by
the session's memory. Corrections travel the way EGM's findings do, as
written lines (`Supervisor round <n>`), capped at three rounds.

**Why this is not section 23 again.** Section 23 removed worker sub-agents
for two reasons and named the conditions for a revival. Each is met or
stated:

1. Harness leakage. The 5.12 prose named a claude-only agent. 11.0 names
   no agent definition: a Herdr tab runs either harness's own CLI, and a
   "fresh general-purpose sub-agent" exists on both; where none can be
   spawned the supervisor works inline. `delegate.py` reads the harness
   from the stamp, so the worker always runs under the scaffold's own
   hooks and permissions.
2. Cost at an equal tier (+35% tokens). 11.0 delegates only to a cheaper
   tier than the session's model, and the supervisor checks that before
   handing off. The brief costs nothing to build (the task file is the
   brief), and the report is one Findings line.
3. Ceremony on small work. Two or fewer open steps stay inline.

Section 3's "the framework pins no tier" no longer holds for `/task do`:
the script names a tier per task, the user overrides it with
`LLM_AGENT_WORKER_MODEL`, and `inline` turns delegation off for one run.
The tier is named by alias (`haiku`, `sonnet`) on claude so it does not
go stale; copilot gets `auto` because its model ids churn, and since
`auto` cannot be shown to be cheaper, a copilot supervisor works inline
unless the user sets the variable.

**Why Herdr first.** Inside Herdr the worker gets its own tab, so the user
sees it work and can step in. A permission prompt in that tab is the
user's to answer, and a sub-agent has no such surface. Herdr's lifecycle
states (`working`, `blocked`, `done`) give the supervisor a wait that does
not poll. `delegate.py launch` confirms the prompt started a turn
(`agent prompt --wait` with a short timeout: a stall or a dialog fails),
because the runbook had recorded a prompt that was never submitted. On
any failure it captures the worker's screen, closes the tab it opened,
and the supervisor falls back to a sub-agent. Each round starts a fresh
worker in a new tab: the first cut re-prompted a worker still alive from
the round before, which kept its context and made Herdr rounds differ from
sub-agent rounds. A correction must then stand on its own in the file.

**Folder trust.** The worker runs in the project folder, so it needs the
harness's trust for that folder, which an interactive session there has
already granted. A folder only ever run headless (`claude -p`, as in the
live test below), a fresh clone or a new worktree has none, and the worker
stops at the dialog. `plan` therefore reads the harness's own trust record
(claude's `.claude.json`, exact folder only, since the live test showed a
trusted parent does not cover it; copilot's `trustedFolders`, parents
included) and picks `subagent` for an untrusted folder, saying why. An
unreadable record counts as trusted and `launch` catches the dialog. The
other way round, a headless worker that skips the dialog, was rejected:
it gives up the tab the user can watch and step into.

**What the worker may not do.** Tick a done-when box, write Outcome, notes
or the review line, run `tasks.py start|finish` or `delegate.py`, hand the
steps on, or commit to the host repository. It commits `.ai` once per
round, which also satisfies the turn-end hook in its own tab. A worker's
`done` is a claim: the supervisor re-reads the evidence, the diff and the
full suite itself (the 2026-07-04 asymmetry rule of section 23).

**Live test, 2026-11-01** (claude, Opus 5.5 supervisor via `claude -p`,
a scratch Python repo, both tasks written by hand in Create's format):

- `add-median`, a 3-step `change`: plan said `herdr`/`haiku`. The worker
  tab stopped at the harness's folder-trust dialog (fresh scratch folder),
  `agent start` returned `agent_not_ready`, and the supervisor fell back
  to a haiku general-purpose sub-agent as the rules say. One round,
  accepted. The worker ticked steps only, reported its checks, and
  committed `.ai`. The supervisor reran the suite and sent the diff to the
  `reviewer` sub-agent. Cost: supervisor $0.483, worker $0.008. That run
  also exposed two bugs, both since fixed: the first `launch` left the tab
  open, and its wait timeout (30 min) exceeded a shell call.
- `top-words-order`, a 4-hypothesis `bug`, after the user trusted the
  folder: `herdr`/`sonnet`, `LAUNCHED` in its own tab, one `herdr agent
  wait` (Bash timeout 570 s), state `done`, tab closed. The supervisor
  reran the suite, proved fail-before and pass-after itself by stashing
  only the fix, and caught a worker citation off by two lines, which it
  corrected in Findings. The review ran inline (9-line diff). Supervisor:
  $0.361, 3.6k output tokens. Worker (sonnet): 2.3k output, 271k cache
  reads.
- Both: every Done-when ticked by the supervisor, `finish done`
  accepted, `.ai` log `worker round 1` before `done`, no host commit,
  no `task:` tab left behind.

What the runs do not show: that delegation is cheaper. On tasks this
small the supervisor's reading and verifying is most of the bill, and
inline Opus was not run as a twin. One pre-existing slip recurred in both
runs: the supervisor ticked done-when boxes with an in-place Python edit
rather than its edit tool, against `do.md`'s rule. That is not new to
11.0 and is left for a separate change.

**Fixes from the satty run, same day.** A runbook run on satty
(`f578432`, Opus 5.5 supervisor, sonnet workers in Herdr tabs) passed
TC-D2, TC-D6 and TC-D3: one change done with the `reviewer` sub-agent
finding four defects the supervisor's round check had missed, one change
`blocked` on the missing toolchain after the worker reported `stuck`. It
showed three faults, fixed here:
- The supervisor wrote a `Supervisor round 1` line on a round it
  accepted. That form is the correction a later worker acts on, so an
  accepted round now writes `Supervisor check: round <n> accepted` instead.
- Done-when boxes were ticked by a script replacing every `- [ ]` at once,
  in all three live runs (it predates 11.0). `tasks.py tick <id>
  done|steps <n>...` now ticks named items only, prints each with its text,
  and has no "all"; `do.md` and `work.md` route every tick through it, the
  worker only `steps`.
- In the runbook's Herdr driving, `enter` on a question form's "Type
  something" closes the form unanswered; the appendix says how to answer.

**Files.** `templates/tools/delegate.py` (`plan`, `launch`, `close`),
`templates/task/work.md` (the worker's body), the supervision block in
`templates/task/do.md` between steps 1 and 2, `inline` in the `/task`
dispatcher, permissions for `delegate.py plan` and the read-only
`herdr agent wait|get|read`. Tests: `tests/test_delegate.py`; runbook
TC-D6 and TC-D7.

## 51. Parallel tasks in one working tree (2026-11-01, v11.1)

**What blocked it.** Until 11.0, Part I said parallel work "is an intent
that was never built". Four things made two `/task` sessions in one
project unsafe:
1. One resume pointer: a second `tasks.py start` replaced the first
   task's `.ai/.current`, and with it the `modified:` list.
2. `git -C .ai add -A`, in AGENTS.md, Create, Do, the worker body, the
   turn-end hook and the commit `tasks.py` prints. It sweeps a parallel
   session's half-written task file into the other session's commit.
3. One host working tree: both tasks' edits land in one diff, which the
   review gate reads as scope creep, and nothing stops both from editing
   the same file.
4. The turn-end hook blocked on any dirty `.ai` and suggested `add -A`.

**Why not git worktrees.** A worktree per task is the physical answer and
was considered first. It fails three ways today. A new worktree path is
a folder the harness has never trusted, so a Herdr worker started there
stops at the trust dialog (section 50), and parallel work would lose the
worker tab. The scaffold's entry files (`.claude/`, `AGENTS.md`) are often
untracked in the host repo, so a fresh worktree has no skills, hooks or
instructions. And `.ai` is its own repository, so a worktree needs a
second worktree of `.ai` and a merge back that `/task list` cannot see
until it happens. Cooperative isolation in one tree needs none of that.

**The design.**
- Pointers: `tasks.py start` writes `.ai/.current` when it is free or
  names a task that is not `in-progress` (a blocked or finished task's
  pointer is replaced, as before), and `.ai/.current-<id>` otherwise
  (gitignored with `.current-*`). It prints each other running task with
  its claims (`PARALLEL`). `finish done` deletes the task's own pointer;
  `finish blocked` keeps it. `/task list` and `/task tree` mark every
  running task. `/task do` without an id resumes `.ai/.current`, or the
  only running pointer, and asks when there are several.
- Claims: `tasks.py claim <id> <path>...` appends to the task's
  `modified:` list and refuses, exit 1, a file another running task
  listed. A refused claim writes nothing. Do and the worker body claim a
  file before editing it; a worker that needs a claimed file reports
  `needs-user`.
- Commits: every documented and printed `.ai` commit names its paths.
  The turn-end hook lists the dirty paths and tells the session to
  commit only its own.
- Review scope: the task's diff is `git diff --` its claims.

**What is not isolated.** The test suite runs in the shared tree and sees
the other task's unfinished edits: a failure in a file another running
task claimed is recorded in Findings and rerun later, not fixed.
`notes.md` is shared and appended by both. Claims are cooperative: an
agent that edits without claiming is not stopped by a hook.

**Live test, 2026-11-01** (satty `f578432`, one Herdr workspace, two
Opus 5.5 supervisors side by side, sonnet workers):
- Both Creates ran at once: two `.ai` commits, each holding only its own
  task file (plus `notes.md` for the one that changed it).
- Both Dos ran at once: `readme-keybindings` held `.ai/.current`,
  `config-errors-no-abort` got `.ai/.current-config-errors-no-abort` and
  saw `PARALLEL readme-keybindings is running`. Two worker tabs ran
  together.
- The claim refusal fired for real: the second worker tried to claim
  `README.md`, got `CLAIMED README.md by running task
  readme-keybindings`, dropped it and went on.
- Supervisor A wrote a correction, the first live second round:
  `CLOSED previous worker` then `LAUNCHED ... round 2` in a new tab;
  round 2 was accepted. Its Findings name the other task's files as the
  parallel task's, not scope creep.
- End state: one task `done` (its pointer deleted), one `blocked` on the
  missing toolchain (its parallel pointer kept, marked in `/task list`).
  Ten `.ai` commits, none holding another task's files.

**Stops wait for the user (same version).** A report from work: the
worker stopped where intervention was needed, the supervisor said so,
then went on with the task itself and closed the worker's tab. The satty
transcripts show the same in all three `config-errors-no-abort` runs:
after the worker's `stuck` (no toolchain) the supervisor edited
`src/configuration.rs` itself (a line wrap, an unused import) before
asking, then closed the tab. 11.0's Do text allowed it: `stuck` meant
"work the rest yourself, ask the user, or finish blocked", in no order,
and the tab closed "after the last round". 11.1 orders it: a stop is a
question first. On `needs-user`, or `stuck` on something outside reach,
the supervisor asks, edits nothing and keeps the tab open until the
answer; on `stuck` on the work it asks how to go on and takes over only
with agreement, announcing it. Its own host-code edits are otherwise
limited to review-gate fixes. The worker body now files "outside your
reach" (a toolchain, access, hardware) under `needs-user`, not `stuck`.

**Files.** `templates/tools/tasks.py` (`pointers`, `claim`,
path-scoped commit lines), `templates/hooks/ai_repo_clean.py`, the
commit rule in `templates/instructions/agents.md`, `task/create.md`,
`task/do.md` (pointer, claims, suite and review scope), `task/work.md`,
the `.current-*` gitignore entry in `agentgen/scaffold.py`. Tests:
`test_tasks_table.py` (pointers, claims, resume, list marks: 144 checks).
Runbook: TC-P1.

## 52. The worker is the harness's own sub-agent (2026-11-03, v11.2)

**Source.** The owner's call after 11.1: `/task do` should use what the
coding agent does on its own, a sub-agent, and carry no steering for where
the worker runs. A Herdr tab stays possible when the user asks for it,
through the agent's own Herdr knowledge, not through the framework.

**Change.**

- `delegate.py` is gone, and with it `plan`, `launch`, `close`, the folder
  trust check, the round counter, the model table and the variables
  `LLM_AGENT_WORKER_MODEL`, `LLM_AGENT_WORKER_PERMISSION` and
  `LLM_AGENT_ROLE`. `/framework-update` deletes the file from existing
  projects through the recorded file list.
- Do states the dispatch in prose: a fresh general-purpose sub-agent,
  never a fork, on a cheaper model than the session's where the harness
  lets the agent pick one, with a fixed one-line prompt naming the task,
  the round (one more than the `Worker round` lines) and `work.md`.
  Inline when the user says `inline`, when two or fewer steps are open in
  the first round, or when no sub-agent can be spawned, which also covers
  a worker that would delegate again.
- Every Herdr paragraph of Do goes: launch, the 9-minute wait, a
  `blocked` dialog in the worker tab, keeping the tab open for the user,
  closing it. The `Delegation:` line loses its mode and kind.
- The permission allowlist loses `delegate.py plan` and `herdr agent
  wait|get|read`.

**Kept.** The supervisor and everything section 50 built around it: the
task file as the whole brief, `work.md` as the worker's contract, the
`Worker round` report, judgment from the files and a rerun of the suite,
`Supervisor round` corrections, three rounds, a stopped worker as a
question for the user, takeover only with agreement, and the review gate,
Outcome, notes and `finish` on the supervisor. Parallel tasks (section 51)
are untouched; each session has its own worker sub-agent.

**What this gives up.** The tab the user could watch and answer a
permission prompt in, and a model choice per task type. The tier gap that
section 50 required before delegating is now a request, not a check: a
harness that cannot pick the sub-agent's model runs the worker on the
session's tier, the +35% case of section 23. Part I says so under what the
framework does not claim.

**Why.** Section 50's dispatch was 330 lines of script, 234 of tests and
about 25 lines of Do for one terminal multiplexer, and its live runs
already fell back to the sub-agent once (folder trust). The sub-agent path
exists on both harnesses with no setup, which is property 3; the removed
script shrinks the footprint, property 4, and a removal needs no further
argument.

**Live test, 2026-11-03** (claude, Opus 5.5 supervisor via `claude -p`,
a scratch stdlib-Python repo, two 4-step `change` tasks written by hand in
Create's format):

- TC-D6, `/task do add-median-mode`: "Four steps open in round 1, so I'm
  delegating to a worker sub-agent on Sonnet", then one general-purpose
  sub-agent, `model: sonnet`, the fixed one-line prompt. No `delegate.py`,
  no `herdr` call. The worker ticked steps only and committed `worker
  round 1`; the supervisor read the diff, reran tests and lint itself,
  wrote `Supervisor check: round 1 accepted`, sent the 50-line diff to
  the `reviewer`, ticked each criterion with `tick`, and `finish done`
  passed. Cost: Opus $0.388, Sonnet $0.106.
- TC-D7, `/task do add-char-stats inline`: one line "Working inline",
  no worker, no `Worker round` or `Delegation:` line, the 35-line diff
  to the `reviewer`, `done`. Opus $0.301.

Tests: `check_templates` (no orphan, permissions render), the delegate
test file removed. Runbook: TC-D6 (worker sub-agent, no `delegate.py`, no
`herdr` call) and TC-D7 (`inline`) rewritten; TC-D3 loses the tab check;
TC-P1 counts worker sub-agents instead of tabs.

## 53. The worker does the whole job (2026-11-03, v11.3)

**Source.** The first 11.2 run on a real task (DART 1196, Opus 5.5
supervisor, Sonnet 5.5 worker, in Herdr). The worker did the code and
tests of steps 1 to 4 on Sonnet: 28 turns, 14.6k output tokens. Then it
reported `needs-user`, because `work.md` barred it from committing and
pushing, and steps 5 to 8 were a branch, a commit, a pull request, a CI
wait, a dev run, a prod check after the user's merge, and an issue
comment. Nothing was left for the user to decide: `needs-user` was the
only stop that fit a worker that had reached the edge of its rules. The
supervisor accepted the round and did steps 5 to 8 itself (`step 5+
supervisor`): 46 more Opus turns, 19.4k output tokens and 3.3M cache
reads, more than the worker. The owner's call: the supervisor acts like
the user's stand-in, a lead with a junior; the junior does nearly
everything, the lead does not open the junior's pull request.

**Change.**

- The worker works every step the task names, through to the pull
  request: commit, push, CI wait, dev run, tracker comment. The ban on
  host commits and pushes is gone; what limits every agent still limits
  it: the git guard hook blocks a merge into the default branch, and
  `AGENTS.md` stops at the branch or pull request and asks before
  anything destructive or outside the repository. A step that needs one
  of these and does not name it is a `question`.
- Code ships through the review gate. The worker reports `review` before
  its first host commit, and before a push of code changed since the
  last review; the supervisor runs the gate on the uncommitted diff and
  answers with a `Supervisor check: round <n> accepted` line or a
  `Supervisor round <n>` correction.
- Reports: `review`, `question`, `stuck`, `done`. `needs-user` is gone:
  the worker never addresses the user. The supervisor answers a
  `question` as the user would from the Goal, the Notes and the criteria,
  and asks the user only what it cannot decide for them: a changed Goal
  or criterion, a merge, production, deleting data, an open choice it
  cannot settle.
- The supervisor does none of the work. It makes no host edit, commit or
  push, not even to fix a review finding; the finding goes back to the
  worker. It takes over only when the user says so. Section 50's rule
  that two or fewer open steps stay inline is gone; `inline` and a
  harness with no sub-agent remain.
- After a report the supervisor continues the same worker with its
  context where the harness can resume a sub-agent (Claude Code sends it
  a message), and spawns a fresh worker that reads the file otherwise.
  This gives up a little of the goldfish property: a resumed worker
  remembers its own earlier rounds. The file still carries every answer
  and correction, so a fresh worker or a later session loses nothing.
- The supervisor trusts recorded evidence: a CI result on the pull
  request, or a command and its output in Findings. It reruns the tests
  only when there is no CI result and the recorded output is missing,
  partial or doubtful. Section 50 made it rerun the full suite after
  every round, which on Opus is the expensive half of a check that CI
  repeats anyway.

**Kept.** The task file as the brief, fresh-context spawning, the review
gate and its sizing, the `reviewer` on the session's model, the Outcome,
notes, Done-when ticks and `finish` on the supervisor, three tries at the
same correction before the user is asked.

**What this risks.** A cheaper model now pushes and runs things in shared
environments. The review before the first commit, the hook, and the
`question` stop for anything unnamed bound that; a task file that names a
risky step authorizes it, which is the user's call at create time.

**Live test, 2026-11-03** (claude, Opus 5.5 supervisor via `claude -p`, a
scratch stdlib-Python repo with a bare local `origin` standing in for the
pull request, a 5-step `change` whose last step is branch, commit, push):

- Run 1: one Sonnet worker reported `review` with the code uncommitted;
  the supervisor sent the 50-line diff to the `reviewer`, wrote
  `Supervisor check: round 1 accepted`, and continued the same worker with
  `SendMessage`, no second spawn. The worker branched, committed with no
  co-author line, pushed, and reported `done`; the supervisor checked
  `git ls-remote` (branch pushed, `main` untouched), ticked, and finished.
  No host edit, commit or push by the supervisor. One fault: it reran the
  tests twice, calling the worker's `9 tests OK` "only a summary". Opus
  $0.53, Sonnet $0.15.
- Fix: `work.md` records each check with its result line verbatim, and
  `do.md` names that as enough evidence, not to be rerun.
- Run 2, same task on a fresh copy: the same flow, the worker's Findings
  carry `Ran 9 tests in 0.000s OK`, and the supervisor ran no test at all.
  Opus $0.40, Sonnet $0.10.

## 54. An archived dependency is a cleared blocker (2026-11-05, v11.4)

**Source.** `/task tree` in a real project (DART, 13 live tasks, 28
archived) printed 13 ❗ lines, `depends on <id>, which is not a live task
(unknown or archived)`. All 13 named one of four tasks done and archived
weeks earlier, still listed in the `depends:` lines of eight live tasks.
The agent asked by the user called every warning noise and offered to edit
the eight `depends:` lines. A warning that fires on the normal life of a
task trains the user to skip the ❗ block, and a real typo in an id hides
among them.

**Change.** `tree` reads the status of the archived tasks too and sorts an
unresolved `depends:` id three ways:

- archived with `status: done`: the blocker cleared; the id is dropped
  without a word, as it already was from the nesting;
- archived in any other status: flagged, `depends on <id>, archived as
  <status>, not done.`;
- naming no task, live or archived: flagged, `depends on <id>, which names
  no task.`

The tree itself is unchanged: only edges between live tasks nest, as
before.

**Rejected.** Removing an id from every `depends:` line when its task is
archived. It edits several task files on each archive, loses the record of
what a task waited on, and adds a rule to `AGENTS.md`; reading the line
right costs a status lookup over the archive.

**Test.** `tests/test_tasks_table.py`: a live task depending on a task
archived as done gets no warning, one depending on a task archived as
`planned` gets the new flag, the unknown id the new wording.

## 55. A worker agent, `/agent-models`, small tasks inline (2026-11-09, v11.5)

**Source.** Ported from `feature/opencode-agent-models`, where it is 11.6
(its section 56), built on that branch's OpenCode harness (its 11.5). The
owner wanted these refinements in `main` without OpenCode, so this is the
same change minus the OpenCode artifacts; the numbers there and here
differ for that reason. The owner's call behind it, after the OpenCode
benchmark on that branch: set the worker and reviewer models per project,
by a command, on every harness.

**Finding that shaped it.** Each harness pins a sub-agent's model somewhere
else: Claude Code at spawn (which beats every project setting), Copilot
only in a custom agent file. What both share is a `model:` line in an agent
definition, which is how `reviewer` already shipped. So the worker became an
agent too.

**Change.**

- `worker` agent beside `reviewer`: `.claude/agents/worker.md`,
  `.github/agents/worker.agent.md`. Its body only points at `work.md`,
  which stays the worker's contract. Copilot gets `reviewer.agent.md` as
  well (read, search and shell tools), its first reviewer agent.
- Do spawns `worker`. A `model:` line in its file is the user's choice and Do
  passes no model at spawn (on Claude Code a spawn model would win); without
  one, Do picks a cheaper model where it can, as before. Without a `worker`
  agent, a fresh general-purpose sub-agent as before. The `Delegation:` line
  names the worker's model.
- `/agent-models [worker=<model>] [reviewer=<model>]`: with no argument it
  shows both, says what an unset line means on this harness, lists the names
  the harness accepts and asks; with arguments it changes only the `model:`
  line, and `default` removes it. `/framework-update` keeps that line as the
  user's choice.
- Small tasks inline: Do works the steps itself when the task is small, and
  says why in one line. The 11.3 rule delegated everything except `inline`,
  and the benchmark on the OpenCode branch found both harnesses it ran
  (Claude Code and OpenCode) working 3 of 4 tasks inline anyway; a rule the
  agents ignore is worse than a rule that matches them. What counts as small
  was refined in four follow-up commits there, carried over here: a count of
  open steps, not an estimate of lines, docs included, and the decision
  stated first.
- Sub-agents inherit the supervisor's effort: the `reviewer` agent file no
  longer pins one.
- Copilot's `AGENTS.md` CLI note lost two redundant lines to stay under 650
  words with the new command row.

**Live test, 2026-11-07, on the OpenCode branch** (a scratch stdlib-Python
repo per harness, two hand-written tasks: `add-stats`, a module with tests
well over 30 lines, and `fix-version`, a one-line README edit; judged from
the files, the `.ai` log and the transcripts). The Claude Code and Copilot
artifacts there are the ones ported here:

- `/agent-models` with no argument (Claude Code, Copilot): both shown as not
  set with what that means, accepted names listed, nothing changed until
  answered. Set on both (Claude `haiku`/`sonnet`, Copilot `gpt-5.6-luna`/
  `gpt-6-luna`): exactly one `model:` line added per file.
- `add-stats`: Claude Code said "The worker's agent file sets its model, so
  I'm passing none", spawned `worker` (ran on `claude-haiku-5-5`) and
  `reviewer` (`claude-sonnet-5-5`), `done` with the full record. Copilot
  CLI 1.0.89: "Worker (model: gpt-5.6-luna)" and later "Reviewer (model:
  gpt-6-luna)", so Copilot CLI honors an agent file's `model:`, which its
  documentation promises only for IDEs.
- `fix-version`: both worked inline and said why ("Small task (one-line
  edit), so I'll do it inline"), `done`, one `Review: inline` line, no worker.

**Seen, not changed.** On Copilot (session model Auto, which picked
`gpt-6-luna`), the worker rewrote the whole task file, ticked the done-when
boxes and ran `finish`, all of which `work.md` forbids; the supervisor then
sent the diff to the reviewer, and the record ends with the review line
before the worker's and `Delegation: reviewer sub-agent`. A model following
`work.md` loosely, not the model setting; Claude Code on Sonnet kept the
roles apart. Copilot asks before each command and file edit, so the run
needed per-prompt approval.

**Port check, 2026-11-09.** Layer 1 on `main`: `check_templates`, the
task-table test, both harnesses scaffolded and grepped for OpenCode, the
new agent files and `/agent-models` rendered on each. No live rerun: the
Claude Code and Copilot templates are those of the tested branch.

**Fix from the benchmark pilot, 2026-11-08.** In the pilot of the harness
benchmark (satty, Sonnet session, Haiku `worker`, Sonnet `reviewer`), both
Claude Code and OpenCode worked two README changes of about 110 lines inline,
with the same words: "Small docs-only task, so I'm doing it inline." The rule
said small meant an expected diff under ~30 lines; both read it as a kind of
task, not a size. A first fix asked for an estimated line count; in the
next run OpenCode still said "This is a small task, so I'll handle it
inline" without a count. So small is now read off the task file, not
estimated: at most one open step changes a host file, or none does. The
one-line reason names that count (`Inline: 1 of 3 steps edits a host
file.`), which also makes the decision checkable. Neither run counts as a
benchmark run; the pilot's content results were 6 of 6 on both
harnesses.

**Effort is inherited, 2026-11-08.** The first counted benchmark round
recorded the effort each role ran at: the supervisor at `medium` on both
harnesses, but Claude Code's `reviewer` at `high` (its agent file pinned
it) and OpenCode's two sub-agents at the `default` variant (a model pinned
without a variant does not take the session's). The owner's call: the
sub-agents inherit the supervisor's effort. The Claude `reviewer` loses its
`effort: high`, so it follows the session like the `worker`; on OpenCode
`/agent-models` writes the model with the session's variant
(`claude-agent/haiku#medium`). Copilot CLI keeps a sub-agent's effort in the
user's settings (`/subagents`), not in the agent file, so the framework
sets none there.

**Equal-effort round and a wording fix, 2026-11-08.** With every role at
`medium` on both harnesses (verified from Claude's requests and OpenCode's
session records), 3 runs each: 18/18 tasks on both, 17/18 correct
inline/worker decisions on both. The two misses: OpenCode counted "2 of 4
steps edit a host file (both in README.md, one file)" and went inline,
reading the rule as files, as Claude Code had in the first round; Claude
Code stated no decision and did the work itself. Do now says to count
steps, not the files they touch (two steps on one file are two), and that
the decision line comes first, before any other tool call. Cost per run,
list-price estimate: Claude Code $2.18 (2.02 to 2.30), OpenCode $1.23
(1.21 to 1.36); wall time per run overlapped (Claude Code 514 to 750 s,
OpenCode 552 to 609 s), so the earlier time difference did not hold.

## 56. OpenCode as a third harness (2026-11-07, v11.6)

**Source.** The owner's call: the framework should work on OpenCode the way it
works with Claude's slash commands.

**Change.** Property 3 now reads three harnesses. `--harness opencode` writes
`.opencode/`:

- `commands/{explore,task,framework-update}.md`: the same bodies, invoked the
  same way, with `$ARGUMENTS` for the argument string. A command only a user
  can run needs nothing like `disable-model-invocation`. The built-in commands
  found in the binary include `init` and `review`; none of ours collides.
- `agents/reviewer.md`: the same reviewer text, `mode: subagent`, edits denied.
- `opencode.json`: the same permission list, as `shell` rules. OpenCode allows
  by default, so it matters only where a user's global config asks.
- `hooks/`: the same two scripts as every other harness.
- `plugins/llm-agent.js`: the one new artifact. OpenCode has no command hooks,
  so a dependency-free plugin of 74 lines bridges to the scripts:
  `tool.hook("execute.before")` runs `git_guard.py` and throws on exit 2, and
  `session.hook("experimental.idle")` runs `ai_repo_clean.py` and turns a block
  into a synthetic message. It keeps the loop guard itself, because OpenCode
  has no `stop_hook_active`, and leaves alone a sub-agent's turn end and a
  session waiting on background work, matching Claude's `Stop`.

Written against OpenCode V2 and its `@opencode/plugin` types at 2.2.5, which
differ from the V1 documentation still found online: `permissions`, `shell`
and `subagent` replace `permission`, `bash` and `task`, and plugins register
hooks in `setup` instead of returning `tool.execute.before`. V1 was not tested
and is not supported. Upstream marks `experimental.idle` experimental, so the
turn-end check is the part most likely to need a follow-up.

**What differs from claude.** No per-skill `effort`. No per-invocation model
for a sub-agent, so the `/task do` worker runs on the session's model unless
the user configures `general` otherwise: the same-tier case Part I already
names. A difference in the other direction: the plugin's tool hook also fires
inside sub-agents.

**Live test, 2026-11-07** (OpenCode 2.2.5 in a Herdr pane, Sonnet 5.5, a
scratch stdlib-Python repo, judged from the files, the `.ai` log and the
screen):

- `/task list`: the script's output (see the fix below). `/task create add-ops ...`: the native question dialog, a well-formed
  task file, committed as `task: create add-ops`.
- `/task do add-ops`: one worker on `general`, `worker round 1` committed,
  `Supervisor check`, `Review: inline` (about 28 lines, under the gate's
  threshold), `Delegation:`, 3/3 steps and 5/5 criteria, `done`; the tests pass.
- `reviewer`: a second task with a larger diff (two new files) sent it through
  the gate itself, `Review: reviewer sub-agent`, 4/4 criteria, `done`. Asked for
  directly on the first task, it also ran read-only, verdict PASS.
- `/explore`: `probe.py`, the requirement questions, the block in `AGENTS.md`.
  `/framework-update dry-run`: no file changed.
- `/framework-update` for real, on a scaffold staged as 11.4 (`--standalone`,
  `LLM_AGENT_HOME` on a copy without git, so nothing was pulled): stamp 11.5, a
  stale command updated, a retired file deleted and off the file list, a missing
  file restored, and kept: a user rule in `AGENTS.md`, the generated section, a
  user command, a user permission, notes and the task. `.ai` committed as one
  update, backup in place.
- Guard: a `Co-Authored-By` commit and, from inside a `general` sub-agent, a
  merge on `main` were both refused with the script's message; neither ran.
- Idle: a line left uncommitted in `.ai/notes.md` produced the synthetic
  message; the agent reported it and the next idle passed.

A fix this run produced: after `/task list` the agent appended the AGENTS.md
closing headings (Blocked on me, Changed, Found) although List says to add
nothing, failing TC-L1. Claude Code with the same text replied with the script's
output alone, 3 of 3, so the two rules in conflict showed up as a harness
difference. List and Tree now say the headings do not apply, in the command
body because `AGENTS.md` on copilot has one word of budget left. Rerun on
OpenCode: `/task list` on an empty table in three fresh sessions, and `/task
list` and `/task tree` on two dependent tasks, each ended on the script's last
line. Claude once more after the change: unchanged.

Tests: `test_opencode_plugin.py` runs the rendered plugin under node against a
fake host (skips without node); `check_templates` gains `check_opencode_syntax`,
because a command template runs !`...` in a shell outside the permission flow
and replaces $1; `test_harness_switch` switches to OpenCode and back with a
user's command beside ours; `test_git_guard` adds the tool name `shell`.

## 57. OpenCode gets the worker agent and `/agent-models` (2026-11-07, v11.7)

**Note.** `main` took the Claude Code and Copilot half of this change as
section 55 (v11.5) before OpenCode (section 56) was rebased onto it. This
section is the full change as tested on three harnesses; the OpenCode parts
are what this version adds.

**Source.** The owner's call after the OpenCode benchmark (section 56):
OpenCode cannot pick a sub-agent's model at spawn, so its worker ran on the
session's model; the owner wanted the worker and reviewer models set per
project, by a command, on every harness.

**Finding that shaped it.** Each harness pins a sub-agent's model somewhere
else: OpenCode in `opencode.json` per agent, Claude Code at spawn (which
beats every project setting), Copilot only in a custom agent file. What all
three share is a `model:` line in an agent definition, which is how
`reviewer` already shipped. So the worker became an agent too.

**Change.**

- `worker` agent beside `reviewer`: `.claude/agents/worker.md`,
  `.opencode/agents/worker.md`, `.github/agents/worker.agent.md`. Its body
  only points at `work.md`, which stays the worker's contract. Copilot gets
  `reviewer.agent.md` as well (read, search and shell tools), its first
  reviewer agent.
- Do spawns `worker`. A `model:` line in its file is the user's choice and Do
  passes no model at spawn (on Claude Code a spawn model would win); without
  one, Do picks a cheaper model where it can, as before. Without a `worker`
  agent, a fresh general-purpose sub-agent as before. The `Delegation:` line
  names the worker's model.
- `/agent-models [worker=<model>] [reviewer=<model>]`: with no argument it
  shows both, says what an unset line means on this harness, lists the names
  the harness accepts and asks; with arguments it changes only the `model:`
  line, and `default` removes it. `/framework-update` keeps that line as the
  user's choice.
- Small tasks inline: Do works the steps itself when at most one open step
  changes a host file, or none does, and names that count in one line. The 11.3 rule delegated everything except `inline`, and the
  section 55 benchmark found both harnesses working 3 of 4 tasks inline
  anyway; a rule the agents ignore is worse than a rule that matches them.
- Copilot's `AGENTS.md` CLI note lost two redundant lines to stay under 650
  words with the new command row.

**Live test, 2026-11-07** (a scratch stdlib-Python repo per harness, two
hand-written tasks: `add-stats`, a module with tests well over 30 lines, and
`fix-version`, a one-line README edit; judged from the files, the `.ai` log
and the transcripts):

- `/agent-models` with no argument (Claude Code, Copilot): both shown as not
  set with what that means, accepted names listed, nothing changed until
  answered. Set on all three (Claude `haiku`/`sonnet`, OpenCode
  `claude-agent/haiku`/`claude-agent/sonnet`, Copilot `gpt-5.6-luna`/
  `gpt-6-luna`): exactly one `model:` line added per file;
  `opencode debug agents` resolved both.
- `add-stats`: Claude Code said "The worker's agent file sets its model, so
  I'm passing none", spawned `worker` (ran on `claude-haiku-5-5`) and
  `reviewer` (`claude-sonnet-5-5`), `done` with the full record. OpenCode: the
  worker child session on `haiku`, the reviewer on `sonnet`, `done`. Copilot
  CLI 1.0.89: "Worker (model: gpt-5.6-luna)" and later "Reviewer (model:
  gpt-6-luna)", so Copilot CLI honors an agent file's `model:`, which its
  documentation promises only for IDEs.
- `fix-version`: all three worked inline and said why ("Small task (one-line
  edit), so I'll do it inline"), `done`, one `Review: inline` line, no worker.

**Seen, not changed.** On Copilot (session model Auto, which picked
`gpt-6-luna`), the worker rewrote the whole task file, ticked the done-when
boxes and ran `finish`, all of which `work.md` forbids; the supervisor then
sent the diff to the reviewer, and the record ends with the review line
before the worker's and `Delegation: reviewer sub-agent`. A model following
`work.md` loosely, not the model setting; Claude Code and OpenCode on Sonnet
kept the roles apart. Copilot asks before each command and file edit, so
the run needed per-prompt approval.

**Fix from the benchmark pilot, 2026-11-08.** In the pilot of the harness
benchmark (satty, Sonnet session, Haiku `worker`, Sonnet `reviewer`), both
Claude Code and OpenCode worked two README changes of about 110 lines inline,
with the same words: "Small docs-only task, so I'm doing it inline." The rule
said small meant an expected diff under ~30 lines; both read it as a kind of
task, not a size. A first fix asked for an estimated line count; in the
next run OpenCode still said "This is a small task, so I'll handle it
inline" without a count. So small is now read off the task file, not
estimated: at most one open step changes a host file, or none does. The
one-line reason names that count (`Inline: 1 of 3 steps edits a host
file.`), which also makes the decision checkable. Neither run counts as a
benchmark run; the pilot's content results were 6 of 6 on both
harnesses.

**Effort is inherited, 2026-11-08.** The first counted benchmark round
recorded the effort each role ran at: the supervisor at `medium` on both
harnesses, but Claude Code's `reviewer` at `high` (its agent file pinned
it) and OpenCode's two sub-agents at the `default` variant (a model pinned
without a variant does not take the session's). The owner's call: the
sub-agents inherit the supervisor's effort. The Claude `reviewer` loses its
`effort: high`, so it follows the session like the `worker`; on OpenCode
`/agent-models` writes the model with the session's variant
(`claude-agent/haiku#medium`). Copilot CLI keeps a sub-agent's effort in the
user's settings (`/subagents`), not in the agent file, so the framework
sets none there.

**Equal-effort round and a wording fix, 2026-11-08.** With every role at
`medium` on both harnesses (verified from Claude's requests and OpenCode's
session records), 3 runs each: 18/18 tasks on both, 17/18 correct
inline/worker decisions on both. The two misses: OpenCode counted "2 of 4
steps edit a host file (both in README.md, one file)" and went inline,
reading the rule as files, as Claude Code had in the first round; Claude
Code stated no decision and did the work itself. Do now says to count
steps, not the files they touch (two steps on one file are two), and that
the decision line comes first, before any other tool call. Cost per run,
list-price estimate: Claude Code $2.18 (2.02 to 2.30), OpenCode $1.23
(1.21 to 1.36); wall time per run overlapped (Claude Code 514 to 750 s,
OpenCode 552 to 609 s), so the earlier time difference did not hold.

## 58. `/agent-models` removed (2026-11-09, v11.8)

**Source.** The owner's call: the feature needs to be rethought from the
start, so it leaves every harness now rather than ship half-considered.

**Change.** The command is gone from the roster (`const.SKILLS`,
`ARG_HINTS`, `SKILL_EFFORT`), with its skill body `templates/skills/
agent-models.md`, the three `skills/fragments/<harness>/models.md` files, the
`AGENT_FILES`, `MODEL_UNSET` and `MODEL_VERIFY` tables and the slots that fed
them, its row in `AGENTS.md`, its README section and test cases (TC-M1).
Property 3 reads three commands again; `AGENTS.md` before the generated
section is 514 words on claude, 512 on opencode, 630 on copilot; a claude and
a copilot scaffold record 15 framework files, an opencode one 16.

**Kept.** The `worker` agent beside `reviewer` (sections 55 and 57), the
small-task inline rule, and the rule that a `model:` line in either agent
file is the user's choice: Do passes no model at spawn when one is there, and
`/framework-update` keeps it in the merge. Nothing writes that line any more;
a user can add it by hand. Sections 55 to 57 stay as the record of what was
built and measured.

**Existing scaffolds.** `/framework-update` retires the `agent-models`
command file through the recorded file list and removes the `AGENTS.md` row.

## 59. Sub-agent models are explicit (2026-11-09, v11.9)

**Source.** The owner's call after removing `/agent-models` (section 58):
model selection must be explicit per project. If no model is set, do not
assume or inherit one, refuse. The owner also runs Claude Code through a
Copilot proxy whose model names (`gpt-6.1-sol`) are not tiers, so the
framework can know no names. Settings the owner chose: both roles required,
`inherit` is not a model, a setup tool that tests each name as a sub-agent
call, run from a project session.

**Finding that shaped it.** A spawn-time model can only be a tier alias on
Claude Code and beats the agent file; the file's `model:` line takes any
name the provider serves and is the one mechanism all three harnesses honor.
So the file is the single source and the spawn passes nothing.

**Change.**

- `tasks.py models` is the gate: it reads the agent file of each role on
  every harness that has one and prints `MODELS OK` or `MODELS MISSING`
  (exit 1). A missing file, a missing or empty line and `inherit` are all
  unset; the name is not validated. `/task do` runs it as step 0, before
  `start`, so a refusal changes no task state, and the agent may not pick a
  model to get past it.
- `do.md` lost every model guess: no cheaper model picked at spawn, no
  `session model` in `Delegation:`, no general-purpose fallback for the
  worker or the reviewer, no self-review of a result that needs a fresh
  context. A reviewer that cannot be spawned stops the task and asks the
  user.
- `init-agent --models [--worker M] [--reviewer M] [--no-test]`
  (`agentgen/models.py`): writes the `model:` line after `description:`,
  then tests each role. In a terminal it asks for missing names; under `!`
  from a session it takes flags. A name that fails the test is not saved: the
  file is restored byte for byte. The tool ends by running the gate and
  prints a restart hint, because a running session read the agent files at
  start.
- The test (Claude Code): a fresh `claude -p` session is told to spawn the
  role with the Agent tool and prompt "Reply with the single word hello",
  then print `SUBAGENT_REPLY: <reply>`. The verdict is that exact line, not
  the exit status, since a failed spawn still ends the parent's turn
  cleanly with `is_error: false`. The JSON `modelUsage` is shown as
  evidence. A fresh process sees the new files at once, so the test needs no
  restart.
- Copilot and OpenCode get the line and a note that no automatic test
  exists yet. Copilot's headless call needs `--allow-all-tools` with a
  custom agent, which was not run; OpenCode's was not installed on the
  machine of this revision. Neither is encoded until verified.

**Seen, 2026-11-09 (Claude Code 2.1.319, a scratch project).** Worker
`haiku` and reviewer `sonnet`: both replied, `modelUsage` showed
`claude-haiku-5-5` beside the Sonnet parent for the worker; about $0.06 per
role, mostly the parent session's cache. A nonexistent name: the sub-agent
failed with `model_not_found` (HTTP 404), stderr carried
`[claude-code:unrecognized_model]`, the parent said so in prose with
`is_error: false`, and the tool refused to save it. `inherit`: refused
before anything is written. Not run: the Copilot and OpenCode tests, and a
proxy-served name.

**Limits.** The test proves the name resolves and a sub-agent answers on
it, not that the model is good enough. A parent that invented the reply
without spawning would pass; the evidence line makes that visible, not
impossible. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` overrides the files and the
framework cannot see it. Layer 2: TC-M1 and TC-M2 in
`tests/task-commands.md` are written, not yet run on a live repo.

## 60. OpenCode model test (2026-11-09, v12.0)

**Source.** Section 59 shipped `init-agent --models` with a sub-agent test on
Claude Code only; OpenCode got the line and a note. The owner asked for full
OpenCode support. The branch that held the retired `/agent-models` (section
58) was rebased onto 11.9 and dropped; its OpenCode know-how was checked
again and carried over.

**Seen, 2026-11-09 (OpenCode 2.2.5, a scratch opencode scaffold,
`claude-agent` provider).**

- `opencode run --format json "<prompt>"` from the project spawns a
  sub-agent through the `subagent` tool (`input.agent` is the role). Its
  JSON lines carry the reply as `text` events and the call as a `tool_use`
  event whose output names the child session (`<subagent
  sessionID="...">`); `state.metadata.sessionID` held it in one run and was
  missing in another, so the output is the fallback.
- `opencode session export <child>` records the model the sub-agent ran on:
  `info.model = {providerID, id, variant}`. A `model:` line without a
  variant ran as `variant: default`; `claude-agent/sonnet#medium` ran as
  `variant: medium`. So the `#<variant>` suffix in the agent file is
  honored, and a pinned model without one gets the default variant, not
  the session's.
- A nonexistent name: the tool call ends `error`, "Model unavailable:
  claude-agent/nonexistent-9", and the parent reports it in its reply line,
  exit status 0. As on Claude Code, the reply line is the verdict.
- `opencode debug agents` shows each agent's parsed model, including the
  variant. `opencode` was not on PATH; its installer puts it in
  `~/.opencode/bin`.
- The background server (`opencode serve --service`) keeps the agent files
  it read first for a directory. After the `model:` line was added it
  still listed the worker without a model for 50 s and after a config
  touch, and a spawn through it ran on the user's default model
  (`opencode/iceman-free`), replying hello all the same. The first draft of
  the test passed a nonexistent name that way; the model check is what
  caught it. `opencode reload` made the server read the files at once and
  ended no session; `opencode run --standalone` reads them fresh.
- `opencode run` with stdin left open waited on it until the 240 s timeout;
  with stdin closed the same run took about 12 s.
- The export held the model in `info.model` in some runs and only in
  `messages[].model` in another.

**Change.**

- The OpenCode test runs `opencode run` with the same prompt as the Claude
  Code one, naming the `subagent` tool, and passes only when the reply line
  says hello and the exported child session ran on exactly the name in the
  file (`provider/model`, plus `#variant` when one is given). Claude Code's
  test can only show `modelUsage`; OpenCode's can check, so it does. Both
  test sessions are deleted afterwards. The binary is looked up on PATH,
  then in `~/.opencode/bin`. The test runs `--standalone` with stdin
  closed, and reads the model from `info.model` or else the messages.
- After saving on OpenCode the tool runs `opencode reload`, so the next
  `/task do` through the background server spawns on the new models; if
  that fails it says to run it by hand.
- README: OpenCode names are written as `opencode models` prints them,
  `<provider>/<model>`, with an optional `#<variant>`.
- Copilot still gets the line without a test.

**Run, 2026-11-09.** Switcher on OpenCode: both roles OK with the model
read back, a nonexistent name FAILED with the file unchanged, `inherit`
refused, a re-init kept both lines, no test session left behind; on Claude
Code again after the prompt refactor: OK and FAILED as before. TC-M1 on
OpenCode (TUI, Sonnet 5.5 via `claude-agent`): refused at `tasks.py models`
with no `start` and no spawn, also with `model: inherit`. TC-M2 on OpenCode:
models set with `!` from the TUI, then `/new` and `/task do` with no TUI
restart; the worker's and the reviewer's sessions ran on
`claude-agent/haiku` and `claude-agent/sonnet#medium`, no spawn passed a
model, `Delegation: claude-agent/haiku`. The reload alone was enough. Seen
beside it, not part of this change: the OpenCode worker committed on the
default branch. No rule forbade it then: rule 5 and the git guard cover
merging and pushing, not a local commit (section 61).

## 61. No commit on the default branch unasked (2026-11-09, v12.0)

**Source.** In the OpenCode TC-M2 run of section 60 the worker committed
`wordstat` straight onto `main`; the Claude Code worker of the same case
had made a branch on its own. Nothing shipped forbade it: rule 5 said
"never merge into the default branch unasked", the worker's contract said
the same, and the git guard blocks `git merge` on the default branch, a
`git push` to it and `gh pr merge`, not a local commit. The task named no
branch and the scratch repo had no remote, so there was no push to block.
Section 60 first called the commit a TC-D6 failure; TC-D6 checks merging,
so that was corrected.

**Owner's decision.** Add the rule, as protocol only. The owner sometimes
wants a commit on the default branch and asks for it; a hook would block
that request too, since it cannot tell an asked commit from an unasked one.

**Change.**

- `AGENTS.md` rule 5: "Never commit on or merge into the default branch
  unasked. Work on a feature branch and stop at it or its pull request."
- `work.md`: the worker's copy of the rule names committing too. A worker
  is asked only through its task: a step that names a commit on the
  default branch is the ask; one that needs it without naming it is a
  `question`, as for every rule there.
- Force-pushing is scoped the same way. `AGENTS.md` listed "force-pushing"
  among the destructive acts to ask about first, and `work.md` said "never
  force-push", which read as any branch; rewriting a feature branch is
  ordinary work. Both now name the default branch only.
- `work.md`'s rule paragraph for the worker is about the default branch
  only: work on a feature branch, and never commit on, merge into or
  force-push the default branch unless a step names it; a step that needs
  one without naming it is a `question`. The worker's former line "nothing
  destructive or outside this repository unless a step names it" is gone
  from `work.md` by the owner's decision: listing what lies outside read as
  a ban on work that is the job, such as a change to a production database.
- `AGENTS.md` Execution, which the worker also follows: stop and ask before
  anything destructive "nobody asked for". Before, the list (deleting data,
  changing anything outside this repository) had no such clause and pulled
  toward stopping even when the change was the task, such as one to a
  production database. A request from the user or a task step is the ask.
  Three words, because the copilot `AGENTS.md` stood at 645 of its 650-word
  budget; a sentence naming the production database did not fit.
- Part I's enforcement paragraph states the exception to "a checkable rule
  gets a hook". The git guard is unchanged.
- TC-D6 checks that the host repo's default branch got no commit.

**Not run.** No Layer 2 case was rerun for this; it is a text change to a
rule the agents already read. TC-D6's new check covers it on the next run.

## 62. `/framework-models` (2026-11-09, v12.0)

**Source.** Since 11.9 the models of `/task do`'s worker and reviewer are
set with `init-agent --models`, a shell command. The owner asked for a slash
command that at least prints what to run. Section 58 removed
`/agent-models`, which set the models itself; this one only shows them.

**Name.** `/framework-models`, the owner's pick, beside `/framework-update`.
Avoided: `/model` (Claude Code, Copilot), `/models` (OpenCode), `/agents`
(Claude Code), `/subagents` (Copilot).

**Change.**

- `tasks.py models [worker=<m>] [reviewer=<m>]` (also the two names bare,
  in that order) prints, after `MODELS OK` or `MODELS MISSING`, the setup
  command for the stamp's harness. Names come from the arguments, else the
  current `model:` lines, else placeholders. The command is `python3
  "$LLM_AGENT_HOME/init_agent.py"` with the absolute path when that
  checkout exists, else the `init-agent` shell function.
- Per harness: Claude Code, a `! ` line in the session and a restart (run
  that way on 2026-11-09); OpenCode, a `!` line and no restart, since the
  tool reloads the server (TC-M2 of section 60); Copilot, a terminal,
  because Copilot CLI 1.0.107's help documents no `!` prefix, and the note
  that Copilot gets no test.
- The skill runs that script with the arguments and replies with its
  output verbatim. It never runs the printed command, edits an agent file
  or suggests a name: the choice stays the user's, and `init-agent` tests
  it.
- The `/task do` gate prints the same command, so a refusal ends with the
  line to type.
- `AGENTS.md`'s command table has no row for it: the copilot file stood at
  648 of its 650 words. Every harness lists the command itself.

**Not run.** The command was rendered on all three harnesses and the
script's output checked there and in `test_tasks_table.py`; no live
session typed `/framework-models` yet.

## 63. The full suite runs once per task (2026-11-10, v12.1)

**Source.** The owner saw `/task do` progress slowly on a real project
(DART, `dart-data-pipelines`, a pytest suite of about 270 tests that takes 3
to 4.5 minutes because of its Postgres tests), and asked whether the
reviewer ran tests too. The sub-agent transcripts of one task
(`1221-prefect-chain`, 2026-11-09 and 10), split by their `agentType`:

| Sub-agent | pytest/ruff runs | Time | Full-suite runs | Time |
|---|---|---|---|---|
| `worker` | 101 | 50 min | 34 | 19 min |
| `reviewer`, one review | 17 | 58 min | 10 | 42 min |

Two of the reviewer's runs hit the 10-minute tool timeout and went to the
background. `work.md` required the full test and lint commands before every
report, and a worker reports every round (`review`, then `done`, then again
after each correction); `do.md` step 5 asked for them before every review
gate. The reviewer had `Bash` and a checklist line, "every Done-when
criterion is met and, where testable, tested", that read as an order to
run the tests again. CI then ran the same suite on the pull request.

**Change.**

- The worker iterates, answers a correction, and reports `review` on the
  tests that cover the change and lint on the changed files only.
- The project's full test and lint commands run once, on the final code. A
  green CI run on the last push is that run; without CI the worker runs
  them locally after the last code change, before it reports `done`. It
  records the command and its result line, or the CI run's URL and result.
- The supervisor checks on `done` that the one full run is recorded and ran
  on the final code, and does not ask for it before then.
- A review reads and runs nothing, inline or by the `reviewer`: it judges
  the diff, the task file and the results in Findings, and a missing or
  contradicted result is a finding for the worker. The `reviewer` keeps
  `Bash` for `git diff`, `git show`, `git log` and `grep`, since it reviews
  an uncommitted diff; its file says never to run tests, linters, builds or
  the code, and its checklist asks for a test in the diff or a recorded
  result instead of "tested".
- The supervisor never runs a check either. 11.3 let it rerun one when the
  command or result was missing from Findings or contradicted the diff;
  that now goes back to the worker as a `Supervisor round` correction. Only
  the worker runs tests, so each run is recorded where the next round reads
  it. Working inline (`inline`, a small task), the supervisor is the
  worker, and step 5 applies to it.
- Reading a CI result is not running it. On `done` the supervisor reads
  the status of a CI run Findings cite (on GitHub `gh pr checks`, `gh run
  view`), and the reviewer may read it too; both commands joined the
  read-only allowlist. A cited green run is the one claim about tests the
  supervisor can check without a run, so it does.
- The full-suite Done-when criterion stays: `create.md` writes it as one
  run on the final code. `AGENTS.md` rule 2 says the same for the direct
  path, three words shorter elsewhere in the rule to stay under the
  copilot budget.

**Kept.** The rule from the sequence round (Part II): never only the test
a task names. A fix that passes its own test and breaks another still
fails the criterion; it is caught once, at the end, not every round.

**What this risks.** A break outside the covered tests now surfaces at the
end instead of in the round that caused it, so a late failure can cost one
more round. On the measured task that round costs one 4-minute run; the
rules it replaces cost 44 full runs between worker and reviewer. A reviewer
that cannot run anything can miss a failure a run would show; the worker's
recorded results and the one full run at the end are the check for that.
Without CI that one run is the worker's recorded result line and nothing
else: no one reruns it, and the runbook records a worker reporting done
with 0 of 4 criteria ticked (2026-09-29). With CI the supervisor reads the
run's status, so a misreported green run is caught. A project without CI
that needs more can take the turn-end check hook `/explore` offers, which
runs its tests deterministically.

**Not run.** Layer 1 only: the templates render on all three harnesses and
`check_templates` holds the budget. TC-D6 gained the checks (one full run,
or none with a green CI run cited; no test or build in the reviewer's
transcript); no live run yet.

## 64. The update runs on a small model (2026-11-11, v12.2)

**Source.** On 2026-11-11 the owner had six projects updated from 10.6, 11.5
and 12.0 to 12.1, each by a Claude Code session on Haiku 5.5 in its own
Herdr tab, and asked whether Haiku is enough. Judged against a pristine
12.1 render per project, all six merges were right: the project sections,
the `model:` lines, a user's `data/` deny rules and user skills kept, the
retired `agent-models` gone, one `update:` commit each, a few minutes per
project. Two faults: one session stopped for "Reply go to run the plan",
which the skill does not ask for, and two wrote `rm -rf` on a variable or a
command substitution, which Claude Code's safety prompt held until it denied
it. The owner then asked for the update to run that way by default, in a
sub-agent or a Herdr tab, on a small model, adapted to the harness.

**Decisions, the owner's.** A new `updater` role with its own `model:` line,
not the worker's; the session waits for the updater and checks its result;
a project with no updater model updates inline, as before.

**Why no model list.** Section 59 stands: the framework knows no model names
(a proxy serves `gpt-6.1-sol`), and the `model:` line of an agent file is the
one source. The adaptation to harness and provider is the name the user
gives `init-agent --models --updater`, which tests it as a sub-agent on that
harness before saving it.

**Change.**

- `updater` agent file on every harness (`.claude/agents/updater.md`,
  `.github/agents/updater.agent.md`, `.opencode/agents/updater.md`). Its body
  is the contract: follow the harness's own `/framework-update` file from
  step 1 inline, never hand the update on, stop with `UPDATE QUESTION` where
  a step needs the user, end with `UPDATE DONE: <old> -> <new>` or `UPDATE
  DRY-RUN`.
- `init-agent --models --updater M` sets and tests it like the other two. An
  older scaffold without the file still sets worker and reviewer; asking for
  the updater there is an error that names `/framework-update`.
- `tasks.py models` prints an `updater:` line, its model or `not set` and
  that the update then runs inline. It never fails the gate: `/task do`
  needs only worker and reviewer. The setup line gains `--updater` when a
  name is known, else a hint to add one. `/framework-models` passes
  `updater=<m>` through.
- The update body gains step 0. With `inline`, or as the updater, go on at
  step 1. Otherwise read the `model:` line of the updater file directly; no
  file, no line or `inherit` means inline, said in one line. Not through
  `tasks.py models`: the first live run below had an older `tasks.py`
  beside the new skill, saw no `updater:` line and went inline. Note the stamp, the `model:` lines and the GENERATED
  section, hand off, wait for the last line, relay a question, and check
  the result from the files: new version, every listed file present, every
  dropped file gone, the `update:` commit and a clean `.ai`, the `model:`
  lines and the GENERATED section still there.
- Hand-off per harness. Claude Code in Herdr: a new tab labelled `update`,
  `claude --agent updater --permission-mode <this session's>`, the command
  `/framework-update inline`, a wait repeated in 9-minute steps (one Bash
  call may run 10), values written literally since no shell variable
  survives between calls. A `blocked` tab goes to the user; the session never
  answers a permission prompt. The tab stays open. Elsewhere, and on
  Copilot and OpenCode always, a fresh `updater` sub-agent with no model
  passed.
- The body no longer pauses for a go-ahead outside the steps that say to
  stop, and makes its temp directory with `mktemp -d` and deletes it by that
  literal path: the two faults of the Haiku run.

**Seen, 2026-11-11 (Claude Code 2.1.311, a scratch scaffold).** With
`model: haiku` in `.claude/agents/worker.md`, `claude -p --agent worker`
answered and its `modelUsage` held only `claude-haiku-5-5`: a session started
with `--agent` runs on the agent file's model, no model name passed.

**Not verified, so not encoded.** Copilot CLI 1.0.105 has `--agent` and
`--model`, but whether an `--agent` session takes the file's model was not
run: the headless call needs `--allow-all-tools`, which the auto-mode
classifier of this session refused. OpenCode is not installed on this
machine. Both use the sub-agent, whose `model:` line they honor (sections 56
and 60), and get no Herdr tab until their session start is checked.

**This reverses part of section 52** for the update only: there the
framework stopped steering Herdr for the `/task do` worker. The update is
one bounded job the user wants to watch and review in place, and the
evidence of this section is a Herdr run.

**What this risks.** A small model merges the framework files; the check in
step 0 catches a missing or stale file, a lost `model:` line and a lost
project section, not a subtle bad merge inside a file. The backup in
`.ai/agent/.update-backup/` and the open tab are the user's way back.

**Live test, 2026-11-11** (Claude Code 2.1.311, a scratch stdlib-Python
project staged at 12.1 with a hand-filled GENERATED section, a note, worker
and reviewer `sonnet`, updater `haiku` set with `init-agent --models
--updater haiku`, whose sub-agent test passed on `claude-haiku-5-5`; parent
session Sonnet 5.5 in auto mode):

- Run 1, in Herdr: the parent went inline, saying no updater model was set.
  The staging had put the 12.1 `tasks.py` beside the 12.2 skill, and step 0
  then read the gate, which printed no `updater:` line. That is TC-U1's
  behaviour, for the wrong reason; step 0 now reads the agent file.
- Run 2, in Herdr, after the fix: a new tab labelled `update` opened, its
  session the `updater` agent on Claude Haiku 5.5 in auto mode (the parent
  passed its own mode), and received `/framework-update inline`. No other
  tab got input. Haiku ended with `UPDATE DONE: 12.1 -> 12.2`, without a
  pause for a go-ahead and without a safety prompt. The parent checked the
  stamp, the file list, the `.ai` commit, the three `model:` lines and the
  GENERATED section from the files, changed nothing itself, left the tab
  open, and flagged that the framework checkout had uncommitted edits.
- Run 3, outside Herdr (`claude -p` with the Herdr variables removed): an
  `updater` sub-agent, no tab. `modelUsage`: Haiku 25.8k output tokens
  ($0.03), the Sonnet parent 1.7k ($0.10, most of it its context). The
  same checks, `update: framework 12.1 -> 12.2`, `.ai` clean.

Not run: TC-U1 on purpose (run 1 covers its path), Copilot and OpenCode,
and an update with real merges under the hand-off (the 12.1 and 12.2 task
files are identical, so only the stamp and file list moved).

## 65. `/framework-models` lists what can be named (2026-11-11, v12.3)

**Source.** After section 64 the owner asked whether a running session can
find out by itself which models are available, so that picking a small
updater (or worker) does not need the names from memory.

**Finding.** It depends on the harness and the backend, not the session:

- OpenCode: `opencode models` prints every name in the form the `model:`
  line takes (section 60).
- Claude Code: no list command (`claude --help` has `--model` only; `/model`
  is the user's picker). The backend may answer `GET /v1/models`: the owner's
  Copilot proxy (localhost:4140) did, 25 entries with `display_name`,
  `capabilities.type` and GitHub's `billing.token_prices`, embedding and
  image models among them. The owner's Azure Foundry endpoint did not: 401
  without the key, 404 with it. The Anthropic API serves the same endpoint
  with an API key; not run here, no such key in this environment.
- Copilot CLI 1.0.105: no list command in `copilot --help`; its `/model`
  picker shows the names.

**Change.**

- `tasks.py models --list` appends an `Available models` block after the
  setup command: the output of `opencode models`; on Claude Code the
  backend's `/v1/models` (`ANTHROPIC_BASE_URL`, else the Anthropic API),
  with the environment's `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` sent
  only to the base URL Claude Code sends it to, one line per chat model
  with its display name and, where the backend gives one, the in/out price;
  entries whose `type` is not `model` or whose `capabilities.type` is not
  `chat` are left out. A backend that does not answer, or no key, gives a
  line naming the reason and pointing at the picker. On Copilot, the
  pointer to the picker. Every list ends by saying the user chooses and the
  setup command tests the name.
- `/framework-models` passes `--list`, and may still not suggest or pick a
  name, from the list or otherwise. The `/task do` gate runs `models`
  without it: no network call there.

**Why still no pick.** Section 59 stands. A list says what can be named,
not what fits a role: names like `gpt-6.1-sol` carry no size, and only some
backends give prices. On the proxy's list the prices make the small ones
plain (`claude-haiku-5-5` 10/50, `gpt-6-luna` 10/50, `gpt-5.6-luna`
20/120), which is the user's information to act on.

**Seen, 2026-11-11.** In the scratch claude project: the proxy listed 21
chat models with prices and no embedding or image entry; the Foundry
endpoint gave `does not list them (HTTP 404)`; `models` without `--list`
printed no list. `test_tasks_table.py` runs the same against a local fake
`/v1/models` (chat filter, key header, 404, no key, Copilot, OpenCode
missing). Live, a Claude Code session on Sonnet 5.5 typed
`/framework-models` there (Foundry backend): it replied with the script's
output verbatim, the 404 line included, and suggested no name. Not run: the
Anthropic API direct, OpenCode.

## 66. The smallest thing that meets the Goal (2026-11-11, v12.4)

**Source.** The owner felt that agents overcomplicate their solutions and
had four long tasks read against their transcripts and diffs: dart
`1221-prefect-chain` (18 worker rounds, 12 corrections), dart
`team-meeting-showcase` (16 rounds) and `1216-worker-image-pinning`,
cleaning `BEGIFZ-6472-foss-doc` (a 1508-line task file) and
`sbom-generator-rename`. Three read-only sub-agents each took one cluster;
their key claims were spot-checked against the task files.

**Finding.** The delivered code was mostly the right size for what was
finally asked: the 1221 create plan was small, PR 2's first version met
the original criteria at 362 + 534 lines, the rename was mechanical. The
time went to, in order:

- Scope growing inside the task. 1221's Done-when 4-9 were ticked on
  2026-11-10 at 10:25 (`b1c0237`); the user's review reopened three, and
  Notes 21 and 23-27 cost about six hours and four pushes and doubled the
  flow (761 + 1032 lines). The FOSS task was reopened after `done` for a
  review stage, a pin change, artifact renaming (five new criteria) and a
  CI fix. The showcase's 16 rounds were 16 user design changes, logged
  as Notes, so Findings showed "0 corrections".
- The supervisor adding work. Each accepted 1221 round carried three
  more fixes (task.md L108, L119, L125); one made tests flaky, the user
  reversed another. Its option questions marked the larger option
  "Recommended" each time. The one real overcomplication: a 209-line
  scoped CI trust fix (FOSS, `f423512`) where a one-line `safe.directory`
  would do, after a correction ruled the broad fix out. In both projects
  the supervisor was the largest token consumer (about 340k and 238k
  output tokens in the task windows) and watched CI in the session; on
  1216 it did merges and production runs itself after round 5.
- Verification volume: 31-34 full-suite runs per task, reviewers rerunning
  the suite, Findings of 1123 lines with rules restated, five viewports
  measured for one-line CSS edits. 12.1 (section 63) already cut the runs.
- Waiting no rule removes: merges, CI at 11-12 minutes a push, provider
  504s, nights, classifier-blocked steps.

**Change.**

- A correction is only what keeps a Done-when criterion from being met or
  breaks something outside the task. Any other review finding is one
  `Not sent back` line and stays there unless the user asks. An accepted
  round carries no fixes.
- Between options the supervisor takes, and recommends, the smallest that
  meets the Goal; a choice put to the user gives each option's cost
  (rounds, lines, CI runs, risk). The worker's `question` does the same.
- A user ask beyond the written Goal and criteria, one that reopens a
  ticked criterion, or one that adds a repository, a pull request or a
  production change: the supervisor first offers to ship what meets the
  criteria and open a follow-up task, with the cost of each way. Folded in
  only on the user's word, then written into Notes and the criteria and
  logged as `User round <n>`.
- Findings: one line each, evidence as a pointer (the command and its
  result line, not the output), no restated rules and nothing about what
  was not done. A worker round line is a few lines at most.
- The worker builds the smallest thing the steps and criteria ask for and
  verifies in proportion to the change.
- New report `waiting`: CI that outlasts one blocking command (`gh run
  watch`, `gh pr checks --watch`), a merge, an approval, a deploy. The
  supervisor tells the user what the task waits for and ends its turn; it
  neither watches nor does the step.

**What this risks.** A follow-up task for each new ask can split work a
user sees as one; the user can always say "fold it in". `Not sent back`
findings may be real weaknesses left in place; they are on record, and
anything that breaks a criterion is still a correction.

**Not run.** Layer 1 only. The runbook gains TC-D9; the next delegated
task on dart or cleaning is the live check, against the counts above.

## 67. The session supervises; the worker runs in a sub-agent or a tab (2026-11-11, v12.5)

**Source.** On 2026-11-11 a DART session that had planned task 1114a ended
"Start (preferably in a fresh session, since this one is very long): /task
do 1114a-catalog-length-size". The owner opened a new Herdr tab, typed it
there, and found that tab acting as a second supervisor with a hidden
worker sub-agent. The owner's model: the main session is the supervisor,
the elephant with the memory; the only difference is whether the worker,
the goldfish, runs as the harness's sub-agent or in a Herdr tab.

**Why the advice existed.** AGENTS.md rule 4 and the end of `/task create`
said to run `/task do` in a fresh session, because instruction adherence
decays as a session grows. That predates 11.0: the session then did the
work itself. Since 11.2 the work is a fresh worker's, and the session only
supervises; the advice now split one supervisor into two.

**Change.**

- `do.md` is rendered per harness in one place, where the worker runs. On
  Claude Code inside Herdr (`HERDR_ENV=1`, `herdr` on PATH): a new tab
  `worker-<id>` (lowercased, at most 32 characters), `claude --agent
  worker --permission-mode <the supervisor's>`, the fixed prompt, `herdr
  agent wait` repeated in 9-minute steps, the report read from the task
  file, the same tab continued with `herdr agent prompt` for the next
  round, a still-open tab of that name continued rather than doubled, a
  `blocked` tab shown to the user (a permission prompt is never answered
  by the supervisor), the tab left open at the end. Elsewhere, and on
  Copilot and OpenCode always, a sub-agent as before. Everything else,
  the prompt, `work.md`, the reports and the review, is the same.
- AGENTS.md rule 4 keeps the fresh session for unrelated tasks and says
  `/task do` needs none, its worker starts fresh; Create's closing line
  says the work runs in this session or a later one. Copilot's AGENTS.md
  stays at 649 of 650 words.
- The reviewer stays a sub-agent: it runs nothing and is short-lived.

**Basis.** `claude --agent <name>` was seen in section 64 to run the whole
session on the agent file's model (`claude-haiku-5-5` for a `haiku` line),
and the updater tab of section 64 ran that way, live. Copilot's and
OpenCode's session start on an agent's model is still unverified, so they
keep the sub-agent.

**What this risks.** The supervisor's context still grows over a long
session, which the old advice guarded against; its share of the work is
reviews and decisions, and the task file still carries everything a later
session needs. A worker tab outlives a closed supervisor session, which
lets the next session continue it.

**Live test, 2026-11-11 (TC-D10)** (Claude Code 2.1.311 inside Herdr, a
scratch stdlib-Python project at 12.5, supervisor Sonnet 5.5 in the
session that had run the earlier tests, `worker.md` set to `haiku` after
that session started, a 4-step `change` with 3 host-editing steps):
`/task do calc-ops` gave no fresh-session advice and spawned no sub-agent
(zero `Agent` calls). It opened tab `worker-calc-ops`, `herdr agent start
... -- --agent worker`, the fixed prompt, `herdr agent wait`; the tab's
status line read Claude Haiku 5.5, so the new session took the model from
the file the supervisor's own session had read before the change. One
round, `Worker round 1: done` with `Ran 3 tests ... OK`, an inline review
of the 8-line diff, `Delegation: haiku, 1 report(s), done`, `finish done`;
the tab stayed open. It left out `--permission-mode`, as the rule allows
when the mode is unknown. Not run: a multi-round task continued through
`herdr agent prompt`, and the outside-Herdr path after this change.

## 68. Herdr only when asked, on every harness (2026-11-11, v12.6)

**Source.** The owner on 12.2 and 12.5: the default is the harness's own
sub-agent flow, as long as the `/task do` call does not ask for Herdr, and
it works the same way on Copilot, OpenCode and Claude Code. 12.2 and 12.5
had put the role in a Herdr tab whenever Herdr ran, and on Claude Code
only.

**Change.**

- Default on every harness: the worker of `/task do` and the updater of
  `/framework-update` are the harness's sub-agent, no model passed.
- `/task do <id> herdr` and `/framework-update herdr`: the role gets a
  Herdr tab of its own when Herdr runs; without Herdr the session says so
  and uses the sub-agent. The tab starts the harness's CLI on the role's
  model, one line per harness, from one helper (`content.herdr_tab`):
  Claude Code `claude --agent <role> --permission-mode <mode>`; Copilot
  `copilot --agent <role> --model <the file's model: line>`; OpenCode
  `opencode --model <the file's model: line>`, the prompt carrying the
  contract. The rest (name, literal values, repeated wait, `blocked` to the
  user, the tab left open, a still-open worker tab continued) is shared.
- The `/task` dispatcher passes `herdr` like `inline`; the argument hints
  and the update body's argument line name it.

**Basis.** Claude Code's `--agent` was seen to run the session on the
agent file's model (section 64, TC-D10 of section 67). Copilot CLI 1.0.105
lists `--agent` and `--model` in its help. OpenCode is not installed here;
its `--model` and `--agent` flags on the TUI are taken from the owner's
own setup notes (`claude-and-bash/opencode-setup/set-me-up.md`, `opencode
--agent aiq102 --model aiq102/claude-opus-5-5`). `--agent` is not used
there for the role, because whether OpenCode starts a `mode: subagent`
agent as the session's agent is unverified; `--model` with the file's line
keeps section 59's rule that the file is the only source.

**Live, 2026-11-11 (TC-D10, plain call, Claude Code inside Herdr).** A
Sonnet supervisor ran `/task do calc-ops2` without `herdr`: one `worker`
sub-agent (on `haiku` from `worker.md`), no herdr command, no tab, no
fresh-session advice; `Worker round 1: review`, `Supervisor check: round 1
accepted`, an inline review, `finish done`, 5 tests OK. The `herdr` path on
Claude Code is the one section 67 ran. Not run: the `herdr` path on Copilot
and OpenCode, whose start lines are unverified live.

## 69. A finding is a claim and a pointer (2026-11-11, v12.7)

**Source.** In the tfa-rpu-ws workspace, a task started under 12.6
(`BEGLRV-11591-mpc3-event-logger-poc`, Claude Code, worker `sonnet`) had 12
Findings after three worker rounds: median 601 characters, longest 1039,
7.5k in all. Each was one line, as 12.4 asked: a paragraph without a line
break, every check with its full command and result ("S3 ROS-less checks":
yamllint, xmllint, `bash -n`, shellcheck, `ast.parse`, `git diff --check`,
601 characters), a retold CI workflow contract ("S3 CI evidence", 781). The
owner asked why the framework logs so much.

**Why 12.4 did not hold.** "One line" carries no length, and two rules
pulled the other way: `do.md` step 3 listed the evidence to give (file and
line, command and result line, log excerpt, doc URL), read as a list to
fill; `work.md` said to record each command with its result line
verbatim. Nothing measured it: TC-D9's check counted lines.

**Change.**

- `do.md` step 3: one line of at most ~200 characters, the claim and one
  pointer, never the evidence itself; checks of a kind in one grouped
  line; longer evidence in `.ai/tasks/<id>/evidence.md` or nowhere.
- `work.md`: verbatim only for the one full test and lint run (or the CI
  run) the supervisor trusts; intermediate checks one grouped line; a
  `Worker round` line at most ~300 characters; shipping evidence as
  pointers, no log lines.
- `tasks.py` (`list` and `tree`) flags a task whose Findings hold lines
  over 300 characters (`LONG_FINDING`), with the count and the longest:
  the prose can be ignored, the flag cannot.
- The update body deletes an older backup by its literal path (`rm -rf
  .ai/agent/.update-backup`). Its "replacing any older backup" had Haiku
  write `rm -rf .ai/agent/.update-backup/*`, which Claude Code's safety
  check held for confirmation in the 12.6 rollout (cleaning-dev-ops).

**Not run.** Layer 1: `test_tasks_table.py` covers the flag (two lines
over, one at 298, a terse task unflagged). The running tfa-rpu-ws task read
its rules at start and keeps them; its next task is the live check, with
`tasks.py` showing whether any line goes over.

## 70. Review fixes for 12.2 to 12.7 (2026-11-11, v12.8)

**Source.** A review of the 12.x line (sections 60 to 69) before it goes to
the default branch. Six findings, each fixed here.

**1. OpenCode's Herdr tab could not start.** Section 68 rendered `herdr
agent start <name> --kind opencode --pane <pane> -- --model <model>` and
called the line unverified, OpenCode "not installed here". It is installed
(`~/.opencode/bin`, not on PATH), and its TUI has no model flag: OpenCode
2.2.5 answers `opencode --model claude-agent/haiku` with its usage text
and does not start; only `opencode run` takes `--model`. So `/task do <id>
herdr` and `/framework-update herdr` failed on OpenCode.

Now the tab starts plain `opencode` and its prompt has that session spawn
the role as its sub-agent: `Use the subagent tool with agent <role> and
this prompt, then print its last line: <prompt>`. The sub-agent runs on the
agent file's `model:` line, the mechanism section 60 measured. To go on
after a report the supervisor sends `Continue the same <role> sub-agent
with this prompt, ...`. The updater's prompt in that tab is `Run the
framework update inline.`, since a sub-agent's prompt cannot be a slash
command.

**Seen, 2026-11-11 (OpenCode 2.2.5 inside Herdr, a scratch opencode
scaffold, worker `claude-agent/haiku`).** `herdr tab create`, `herdr agent
start worker-oc8 --kind opencode --pane <pane>` and the spawn prompt: the
worker replied, and its exported session shows `claude-agent/haiku`,
variant `default`, under a Sonnet session in the tab. A second prompt to
continue the same worker carried the first one's `sessionID` in the
`subagent` call and ran on the same model. Not run: a whole `/task do
<id> herdr` or `/framework-update herdr` on OpenCode, and Copilot's tab.

**2. The update check did not cover the merges.** Step 0's check compared
the version, the file list, the `.ai` commit, the `model:` lines and the
GENERATED section. A small model that dropped a rule the project appended
to `AGENTS.md`, or a permission it added to the settings file, passed all
of it, and those additions are why the update is a merge at all. The
session now diffs each file the updater reports as merged against its copy
in `.ai/agent/.update-backup/`: a line that is gone must be one the new
framework version changed.

**3. The runbook still asked for a fresh session per `/task do`.** 12.5
took that out of `AGENTS.md` rule 4 and `create.md`; `tests/task-commands.md`
kept "`/clear` before each one, as the skill requires". It now says
`/clear` is for test isolation only. TC-D10 gains a check for the cost of
keeping the session: what the user says after `/task create` must be in the
task's Notes before the worker starts, since the supervisor knows it and
the worker reads only the files.

**4. The reviewer was not pointed at `evidence.md`.** 12.7 moved long
evidence out of Findings, and since 12.1 the review runs nothing and
judges from what is recorded. The reviewer's input named only the task file
and the diff. Its input, its "read, do not run" paragraph and `do.md`'s
review step now name the `evidence.md` a finding points at.

**5. The long-line flag hit lines that must be long.** `tasks.py` flagged
every Findings line over 300 characters. A `Supervisor round` line carries
every correction with its file and what done looks like; flagging it
pushes toward vaguer corrections, so it is not counted. A done task is not
flagged either: nobody rewrites its Findings, and it stayed flagged until
archived.

**6. `gh run watch` was not on the allowlist.** `work.md` (12.4) has the
worker wait with `gh run watch <id>` or `gh pr checks <n> --watch`; only
the second matched an entry, so the first prompted inside a sub-agent.

**Not changed, noted.** `AGENTS.md` rule 4 says "`/task do` needs none: its
worker starts fresh", which is not so for a small or `inline` task the
session works itself; the copilot file stands at its 650-word budget. A
task id with a character Herdr's names do not allow (`[a-z0-9_-]` only)
gives an invalid tab name. `tasks.py models --list` sends the API key from
the environment to the base URL Claude Code itself uses, from a script on
the read-only allowlist.

**Tests.** `test_models.py`: the OpenCode tab line has no model flag, the
other two keep theirs. `test_tasks_table.py`: a long `Supervisor round`
line and a done task's long line are not flagged. Both sets fail on 12.7.

## 71. The OpenCode paths, run live (2026-11-12, v12.9)

**Source.** After 12.8 the owner asked what was left for OpenCode and had it
tested in a new Herdr tab, worker `github-copilot/gpt-6.1-terra`, reviewer
`github-copilot/gpt-6.1-sol`. OpenCode 2.2.7 (`~/.opencode/bin`, started
through the owner's `opencode` shell function and launcher), a scratch
stdlib-Python project, the supervisor session on the default model, GPT-6.1
Terra. The updater got `gpt-6.1-terra` as well.

**Found and fixed.**

- `init-agent --models` failed for worker and updater: the parent refused to
  spawn them, quoting "Spawned by /task do only"; a sentence in the test
  prompt did not outweigh the description. The descriptions now name
  init-agent's model check as allowed. Then the sub-agents followed their
  own contract instead of replying: the worker asked for a task id, the
  updater started a real update and wrote a backup. The test prompt now
  says it is a model check and not a task, and both bodies give that check
  the one-word reply and nothing else. All three roles then passed, the
  model read back from each sub-agent's session.
- The updater in a Herdr tab (`gpt-6.1-terra`) wrote a note into
  `.ai/notes.md` (and shifted a line of the stub's comment) and split the
  update over three `.ai` commits. Step 0's check read only the last commit
  message and passed it. The body now says: one `.ai` commit for the whole
  update, no note and no task edit beyond a named migration; step 0 notes
  the start commit and checks `log <start>..HEAD` and `diff <start> --
  notes.md notes tasks`.

**Passed, live.**

- `/framework-models`: the gate, the setup line and `opencode models` (62
  names), verbatim, no name suggested.
- `/task do calc-ops`: one `worker` sub-agent, its session on
  `github-copilot/gpt-6.1-terra`; `Worker round 1: done`, an inline review,
  `Delegation:` naming the model, `finish done`, 3 tests OK; every Findings
  line short, no flag. The supervisor's one edit was its own Review and
  Outcome in the task file.
- `/task do calc-ops2 herdr`: tab `worker-calc-ops2`, plain `opencode`
  spawning the worker (12.8's start), the same record, 5 tests OK; the
  supervisor ran herdr commands and no sub-agent of its own.
- Turn-end check on 2.2.7: an uncommitted line in `.ai/notes.md` held the
  turn end; the agent inspected it and left it, not its own change.
- `/framework-update` from a scaffold staged at 12.7: an `updater`
  sub-agent asked `UPDATE QUESTION` (pull a framework checkout with
  uncommitted edits?), the supervisor relayed it, the answer continued the
  same updater session, stamp 12.8, every framework file equal to a fresh
  render but the three `model:` lines.
- `/framework-update herdr`: tab `update-062212`, `UPDATE DONE: 12.7 ->
  12.8`, the same result (and the notes slip above).

**Not run.** The reviewer on `gpt-6.1-sol`: both tasks were under the
inline threshold, so no review reached it beyond its model check. Copilot's
Herdr paths remain unrun.

## 72. Tests are for logic (2026-11-12, v12.10)

**Source.** The owner found a worker in tfa-rpu-ws had added
`scripts/test_mpc3_snap_app.py` for task BEGLRV-11591, whose first test loads
`snap/snapcraft.yaml` and asserts its fields against the literals just
written (command, `daemon: simple`, `restart-delay: 2s`, five plugs, even
the feature-branch pin in `fa_core_stack.repos`). The worker had reported
"covering tests" on its own; no correction asked for them. The same pattern
was found in DART: `dart-iac/tests/terraform/test_prefect_docker_proxy.py`
(a JSON job template's env dict, value by value), `test_sagemaker_ecr.py`
(regex for literal lines of `main.tf`), and two `test_deploy.py` tests that
count strings in a workflow YAML. Two other DART tests read config and are
worth keeping: `test_rds_storage_sizing.py` asserts a rule across every
`modules/rds` caller, written after a prod outage (#945), and
`test_the_cleanup_workflow_deletes_every_deployment_...` checks that a
workflow and the deploy script agree.

**Why the framework produced them.** `do.md` step 5 said to iterate with the
tests that cover the change; a YAML change has none, so the agent wrote one.
The reviewer's checklist asked that each criterion be "covered by a test in
the diff or a result recorded in Findings", and since 12.1 the reviewer runs
nothing, so a test in the diff was the cheap way through. Nothing said what
a test is for.

**Prior art (web, 2026-11-12).** Google's Testing on the Toilet,
"Change-Detector Tests Considered Harmful" (2015): tests that fail when the
code changes, not when behavior is wrong. *Software Engineering at Google*
ch. 12: test behavior, not implementation. On agents: Matt Pocock (AIHero)
calls these tautological tests; SpecStory states that a test catches a wrong
answer only when its expected value comes from a source that stays fixed
when the code changes, and cites a 2026 study of 86,156 agent test-file
changes, 80.2% with weak or no real check of the result; digdir-agents
issue #302 found a written rule was not enough and added the self-review
question "could each new or changed assertion fail if the code under test
broke?" and a separate reviewer. Simon Willison holds red/green TDD for
agent code and has agents run what they build; red/green alone does not
stop a config change-detector, which also fails first. IaC practice:
unit-test the logic (templates, conditionals, generated values), check
standards with linters and policy-as-code (tflint, Checkov, conftest),
ideally on the resolved plan.

**Change.**

- `do.md` step 5, which the worker follows too, states what gets a test:
  logic, code that computes, branches or transforms. A declarative file is
  checked by the tool that reads it (linter or schema validator, build,
  plan or dry run, CI, a start on the target). Before keeping a test: could
  this assertion fail for a reason other than an intended edit of the file
  it reads? If not, it is a change-detector test and is not written. The
  expected value comes from the requirement. Code inside a declarative file
  (`run:` steps) and code that rewrites one is logic. A rule across files
  that no linter expresses is a policy check and stays.
- `work.md` points at it in one sentence; `/task create` makes a criterion
  about a declarative file name its consuming check, never "has a test".
- The reviewer's coverage line asks for "the check that fits" (a test for
  logic, the consuming tool for a declarative file) instead of "a test in
  the diff", and a new check asks the "could it fail" question of every new
  or changed assertion; a change-detector test is a finding. In `do.md`
  it and new logic without a test are the two review findings outside the
  criteria that go back to the worker rather than into a `Not sent back`
  line.
- AGENTS.md rule 2 says it for the direct path in two sentences. That puts
  copilot's AGENTS.md at 678 words; the owner accepted the cost, so
  `check_templates`' tripwire moves from 650 to 700.

**Not done.** Mutation testing and per-test labels, both suggested in the
sources, need tooling per language. Existing change-detector tests in the
projects are left to their owners.

**Live test, 2026-11-12 (TC-D11, Claude Code, Sonnet supervisor, Haiku
worker, outside Herdr).** A task adding an `exporter` entry to
`config/services.yaml` and a `next_free_port(services)` function.

- Run 1, the rule as first written: no test read the YAML, `yamllint
  config/` was its recorded check. But `next_free_port` got no test at all:
  the worker ran it once by hand ("Check: ... gives 8002"), and the
  supervisor filed the gap as `Not sent back: no unit test covers
  next_free_port ... not a Done-when criterion`. The rule said what may be
  tested, not that new logic must be.
- Fix: logic the task adds or changes gets a test that stays in the suite,
  a run by hand is not one (`do.md` step 5, `work.md`, the reviewer); and
  new logic without a test is the second test finding that goes back to the
  worker, beside a change-detector test.
- Run 2: two tests for `next_free_port` with their own fixtures and
  expected values from the requirement, one for the highest-not-last case
  (9000, 8000 -> 9001); no test reads the YAML; `yamllint` recorded; the
  inline review noted "tests cover logic"; 2 tests OK.

Not run: the reviewer shown a planted change-detector test (TC-D11's third
check), Copilot and OpenCode.

## 73. Follow the existing pattern (2026-11-12, v12.11)

**Source.** The owner found tfa-rpu-ws task `BEGLRV-11591-mpc3-event-logger-poc`
right in result but slow: 21.6 h wall, 19 worker rounds, 13 Supervisor
rounds, 6 reviews, 8 User rounds, for a 20-line snap integration
(`447a8b7`, 2 files) on top of a 2,411-line PoC import into a new repo. A
read-only sub-agent reconstructed it from the supervisor (Kimi K3), worker
(gpt-6.1-sol) and three reviewer transcripts; the test churn, the 20-line
result and the classifier denials were checked by hand.

**Finding.** Agents were active 3.1 h; 15.8 h overnight, 72 min waiting for
the user's push and 49 min for the create Q&A were idle. Of the active
time:

- S4, the snap integration, took three designs in 57 min: a custom native
  wrapper (round 13), the `ros2` CLI direct (round 14), the sibling apps'
  `ros2-wrapper.sh` (round 15). The create plan's S4 never said how the new
  app launches, and the worker invented a wrapper instead of copying the
  apps beside it.
- The supervisor started the round-13 reviewer 7 s after the user's
  redirect was queued and wrote its advice ("must NOT route through
  ros2-wrapper.sh") into Findings; the worker built round 14 on it and the
  user reversed it (User round 2).
- A Supervisor round asked to mirror LICENSE files from a sibling repo
  without checking; there were none, costing a worker round.
- A change-detector test was edited ten times, run eight times and deleted
  (12.10 covers it); it had also pushed the diff past the inline-review
  size, forcing two reviewer runs.
- The supervisor read `do.md` once and ran 12.6 throughout; 12.7's short
  Findings never reached either agent, and 75 of 92 Findings lines exceed
  300 characters. Once the worker re-read `work.md` under 12.10 (07:32), its
  lines dropped to 167-349 characters.
- External, not changed here: the auto-mode classifier denied nine
  actions (pushes, repo creation, docker, delegation messages), and four
  pushes went to the user; the user's CI-only validation added two
  fix-push-CI cycles. The owner's `autoMode.environment` can name the
  company GitHub orgs as trusted.

A minimal path: about five worker rounds, one review, 1.5 h active.

**Change.**

- `create.md`: a step that adds something with siblings in the code names
  the sibling it copies and how, from reading it (file and line); new parts
  follow the existing pattern unless the user asks otherwise.
- `do.md`: a user redirect of how something is built drops the old design:
  no review of it starts, a running one stops where the harness can, none
  of its findings carry over, and a `Dropped:` line records it (not a
  `Review:` line, which `tasks.py` would count as the review `finish`
  needs).
- `do.md`: a correction that tells the worker to copy or follow something
  names it only after the supervisor has read it.
- `work.md` and the continue prompts (sub-agent and Herdr tab): a continued
  worker re-reads `work.md` first, so rule changes reach a running task.

**Not run.** Layer 1. A replay of this task in a sandbox (the owner's
proposal of a no-push replay) is the live check.

## 74. A workaround is not a pattern (2026-11-12, v12.12)

**Source.** After the owner fixed their auto-mode settings (company GitHub
orgs trusted, `$defaults` restored), the cleaning-dev-ops session still
asked them to run every push with `!`. It never tried itself: its
supervisor had written into the task's Findings (round 12, line 1590)
"publishing follows the session pattern: user pushes the branch
(`!`-run)", after the worker's push had been denied twice (line 1339) and
its own retry had been blocked as "Auto-Mode Bypass". The workaround fit
the denials; written as a pattern, it outlived them, and every later round
followed it. The framework has no such rule: `work.md` has the worker
commit, push and open the pull request after an accepted review.

**Change.** `do.md`: a workaround for a denied permission is recorded with
its cause (`Workaround: <what>, because <the denial>`), the worker takes
the normal way again in the next round, a new session or after a settings
change, and the workaround is dropped once that goes through. The
supervisor does not retry a denied action itself, which auto mode treats
as a bypass.

**Not run.** Layer 1.

## 75. The full suite is CI's (2026-11-13, v12.13)

**Source.** Reviewing the test rules as one list (which check runs for
which file type, and when), the owner dropped the full-suite run: in nearly
all their projects CI on the push or their own final test on the target
covers it, and that is not the framework's job. Only the rule on what
changed stays.

**Change.** A code change is checked by the tests that cover it, every test
that exercises the changed code and not only one a criterion names, and
lint on the changed files, recorded on the final code. No agent runs the
project's full test command: not the worker before `done`, not the
supervisor, not the reviewer, and `/task create` writes no full-suite
criterion or step unless the user asks for one. When a step waits for CI,
its result is recorded and the supervisor reads its status, as before.
Templates: `agents.md` rule 2, `do.md` step 2's `done` and step 5,
`work.md` step 2, `create.md`'s criteria by type, `reviewer.md`.

The same holds for declarative files, asked as a follow-up: section 72 gave
them "the tool that reads them", which listed a build, a plan, a CI run and
a start on the target next to a linter, and `create.md`'s examples ("the
snap builds", "the service starts on the target") made such a run a
criterion. Those are the same whole-project checks the owner keeps for CI
and the target. A changed declarative file now gets its linter or
validator on that file (`actionlint`, `yamllint`, a schema validator,
`hadolint`, `terraform validate`); a build, CI run, plan or start on the
target runs only when the user writes it into the task. The reviewer's
coverage line and its change-detector advice name a linter or validator
only.

**The measurement this has to answer.** Part I listed the full-suite
criterion among the rules that came from a failure: the 2026-09-14
sequence round lost correctness on a criterion that named a single test.
That failure was the narrowing, a fix that passed the named test and broke
others on the same code, and the covering-tests rule still forbids it: the
criterion names every test that exercises the changed code, never one. What
the full run added beyond that was a break in code the change does not
touch; in the owner's projects CI runs on every push and blocks the merge,
and changes that only show on the target are tested there by the owner. The
cost side is measured: section 63's 4-minute suite was run 44 times in one
task before 12.1 cut it to one.

**Left open.** A project with neither CI nor a test run of its own now
learns of such a break later than before. No such project was seen.

**Run live (OpenCode 2.2.7, 2026-11-13).** The calc benchmark again, main
session and worker on GPT-6.1 Sol, GPT-6.1 Terra and GPT-6 Luna, reviewer
GPT-6.1 Sol, with an unrelated 45-second test beside the covering one and a
CI workflow step. None of the nine agent sessions ran the full suite or
the slow test; every worker ran `python3 -m unittest tests.test_calc`,
`ruff` on the changed Python files and `actionlint` on the workflow, and no
test reads the workflow. All three results pass the hidden suite.

**Also found, and fixed.** `tasks.py` took any Findings line containing
"review" for the gate's record, and a worker's report status is `review`
(`Worker round 1: review: ...`), so a delegated task always passed: the
Luna run finished `done` without a `Review:` line, unflagged. Only a line
labeled `Review:` after its date counts now, for the `/task list` flag and
for `finish done`; `test_tasks_table.py` covers it. In the owner's six
projects this flags two done tasks of cleaning-dev-ops, both without a
review record.

## 76. Ask with the question tool (2026-11-13, v12.14)

**Source.** The owner saw the OpenCode session in cleaning-dev-ops put its
questions into the closing summary instead of asking. Its export (GPT-6.1
Terra, 70 turns, framework 12.12) holds no call of OpenCode's `question`
tool; three turns ended with the three headings and a question under
Blocked on me: "May I retry the failed jobs ... once?", "Is
`snapshot-artifactory-mirror` a suitable task ID?", and `/task create`'s
tracker and dependency questions. Every harness has a dialog tool for
this: `AskUserQuestion` on Claude Code, `ask_user` on Copilot (its
changelog; one question per call), `question` on OpenCode 2.2.7 (in the
binary, rendered by the TUI). The framework named none of them. Claude
Code's and Copilot's own prompts push theirs; whether OpenCode's does for
GPT models was not established.

**Change.** AGENTS.md's stop-and-ask line asks all open questions together
with the harness's tool (`ASK_TOOL` in `const.py`, the `${ask_tool}`
slot), and the closing line says Blocked on me never holds an open
question. `/task create` asks its type, tracker, criteria and dependency
questions together with the tool, and `/task do`'s supervisor asks the
user with it. `work.md` says a worker asks with a `question` report,
never with a question tool: the user talks to the supervisor. Copilot's
AGENTS.md stays under its 700 words (689) by folding the rule into the
existing two lines instead of adding a third.

**Run live (OpenCode 2.2.7, GPT-6.1 Terra, 12.13 against 12.14, fresh
sessions).**

- `/task create` with the type left open: both asked four questions in one
  dialog.
- `/task create` with the type named (the cleaning case): 12.14 asked the
  similar-task, tracker and dependency questions in one dialog; 12.13 in two
  dialogs, one after the other. Neither wrote a question as text.
- Push and open a pull request with no remote: both asked for the
  repository in a dialog.
- A resume pointer with an unrelated request: both did the request and
  mentioned the pointer under Found, no question asked; that is
  the rule (offer, do not block).

**What this does not show.** The fresh sessions did not reproduce the
text questions on 12.13; they appeared only deep in a long session, so the
measured gain is the batching. That the new lines stop the late-session
habit is expected, not measured: TC-E3 in a long session decides it.

## 77. The worker reads only its own steps (2026-11-14, v12.15)

**Source.** The review in `fable-review-results.md`. `work.md` told the
worker to work "by `do.md` steps 2 to 5" and to ignore the rest, so every
worker round loaded all of `do.md` (about 3,470 words rendered) to use
about 800 of them, and read the supervisor's models gate, review gate and
hand-off rules beside its own.

**Change.** `templates/task/do.md` is split in two, text moved and not
rewritten:

- `templates/task/steps.md`, written to `.ai/agent/task/steps.md`: the four
  working steps (work, findings, re-plan, tests; they were steps 2 to 5)
  and the escalation rule that closed `do.md`. Both roles need them.
- `do.md` keeps the supervisor's part: the models gate (step 0), start
  (1), the review gate (now 2), record (3), tick (4), and the hand-off,
  continuation and user-ask rules between steps 1 and 2. Where it needs
  the working steps it points at `steps.md`: a session that works a task
  itself (`inline`, no sub-agent possible, or a small task) reads it
  first. `Create` still sends an investigation to `do.md`, which sends
  it on.
- `work.md` points at `steps.md` and no longer mentions `do.md`. Its
  `stuck` report cites the escalation rule at the end of `steps.md`.

Only references changed: the old "step 6", "step 5" and "step 7" in `do.md`
are now step 2, `steps.md` step 4 and step 3, and the one phrase in the
working steps that named step 6 now says "the review gate". `steps.md` is
rendered by `render_task_part("steps")`, written beside the other three
parts, and so recorded in `framework_files` automatically; a claude
scaffold records 18 files, copilot 18, opencode 19.

**Size (rendered, claude).** `do.md` 3,474 to 2,717 words, `steps.md` new at
816, `work.md` 952 to 942. A worker loads `work.md` and `steps.md`, 1,758
words, where it loaded `work.md` and `do.md`, 4,426. All three harnesses
write the same files.

## 78. A turn limit on every sub-agent (2026-11-14, v12.16)

**Source.** The review in `fable-review-results.md`: a worker, reviewer or
updater caught in a tool-call loop had no stop but the user's.

**Facts, read in the docs on 2026-11-14.**

- Claude Code, https://code.claude.com/docs/en/sub-agents, frontmatter
  table: `maxTurns` is the "Maximum number of agentic turns before the
  subagent stops. When the subagent reaches the limit, Claude Code returns
  its output marked as partial, and Claude can resume it to continue"
  (partial marking needs Claude Code v2.1.246 or later; an older version
  stops it the same way without the mark).
- OpenCode, https://opencode.ai/v2/agents.md: "`steps` sets a positive
  maximum number of model steps. On the final step, OpenCode removes tools
  and asks the model to summarize in text." New user input resets it.
  `opencode debug agents` in a scratch scaffold printed `"steps": 200`,
  `50` and `100` for the three agents.
- Copilot: skipped. No turn limit key was verified for its agent files, so
  none is written.

**Change.** `const.ROLE_TURNS` holds the numbers; the three agent templates
carry `maxTurns: ${max_turns}` and the OpenCode renderers write `steps:`
(worker 200, reviewer 50, updater 100). They are set generously because
they are tripwires: a healthy worker round that ran the covering tests and
a CI wait stays far below 200 turns, a review reads and reports in well
under 50, and an update touches a few dozen files. Nothing in the docs gave
a reason for other values. `with_model` and `write_agent` keep the extra
line, since the model line is inserted after `description` and every other
line is untouched; `test_models.py` now checks that each role file holds
exactly one turn line, after `--models` and after a re-init.

At the limit the worker's round has no `Worker round` line. `do.md` tells
the supervisor to treat that as an unfinished round: read Findings, then
continue the worker. An OpenCode worker that reaches `steps` answers in
text, which is the same case.

## 79. The sub-agent roles are enforced by the harness (2026-11-14, v12.17)

**Source.** The review in `fable-review-results.md`. Two role rules lived
in text only: `work.md` says "Never hand the steps to another agent", and
the reviewer's body says "Read, do not run".

**Facts, read in the docs on 2026-11-14.**

- Claude Code, https://code.claude.com/docs/en/sub-agents: "By default, a
  subagent can spawn subagents of its own, up to three layers below the main
  conversation", and to stop one, "omit `Agent` from its `tools` list or add
  it to `disallowedTools`"; "In version 2.1.63, the Task tool was renamed to
  Agent." `disallowedTools` is a frontmatter field: "Tools to deny, removed
  from inherited or specified list."
- Claude Code, same page: "Subagents can define hooks that run during the
  subagent's lifecycle", declared in the agent file with the example
  `hooks: PreToolUse: - matcher: "Bash" hooks: - type: command`, and the
  script "exits with code 2 to block". These hooks "only run while that
  specific subagent is active". Hooks reference, https://code.claude.com/docs/en/hooks:
  `PreToolUse` exit 2 "Blocks the tool call", stderr goes to Claude.
  Frontmatter hooks of a project agent run only after the workspace trust
  dialog is accepted, and a `-p` session does not count as accepting it, so
  a headless reviewer is not guarded by the hook.
- OpenCode, https://opencode.ai/docs/config/: "`subagent_depth` sets how
  deeply subagents can start their own subagents. Defaults to `1`, so a
  subagent cannot start another subagent." Nothing is changed there.
- OpenCode, https://opencode.ai/docs/permissions/: rules are an ordered
  `permissions` list of `action`, `resource`, `effect`; "The last matching
  rule wins, so the specific exceptions follow the broad rule"; the shell
  action is `shell`; "A shell pattern ending in ` *` also matches the bare
  command" (the page shows it for `git status`); shell checks run per
  extracted subcommand of a compound command, and "Any `deny` denies the
  operation". `opencode debug agents` in a scratch scaffold printed the
  reviewer's rules in the written order, after the project's own.
- Copilot: skipped. Neither a tool deny nor an agent-scoped hook was
  verified for its agent files.

**Change.**

- Worker, Claude Code: `disallowedTools: Agent` in the agent file. The
  Claude default allows nesting, so the text rule alone was all there was.
  OpenCode needs nothing, its default depth is 1.
- Reviewer: the list of what its shell may run is `const.REVIEWER_SHELL`:
  `git diff|show|log|status`, `grep`, `rg`, `cat`, `ls`, `head`, `tail`, `wc`, `gh pr
  view|diff|checks`, `gh run view`. The body now names exactly these (it
  named four before; `git status`, `rg`, `cat`, `ls`, `head`, `tail`, `wc`, `gh pr view` and
  `gh pr diff` are added because a reviewer that may not run anything still
  reads files and the pull request). `tasks.py` is not on the list, the body
  never asks for it.
- OpenCode reviewer: `shell` `*` deny, then one `allow` per list entry
  (`<cmd> *`), after the existing `edit` deny.
- Claude Code reviewer: `templates/hooks/reviewer_guard.py`, written to
  `.claude/hooks/` and declared in the reviewer's frontmatter only. It
  accepts a leading `rtk` or `rtk proxy` (and `rtk run "<line>"`, and
  `rtk read` as `cat`); a compound command passes only when every part
  does; it blocks any redirect to a file (`2>&1` and `2>/dev/null` pass),
  command and process substitution, `--output` and `--pre`, and
  `git -c`. A block says to report what could not be checked. It fails open
  like `git_guard.py`: input that is not a JSON tool call with a string
  command, or a line the shell lexer cannot parse, passes.
  `tests/test_reviewer_guard.py` pins allowed and blocked commands and that
  the OpenCode list equals the hook's.

**What this does not do.** The OpenCode rules match a command prefix, so
`git diff --output=f` is not caught there (the hook catches it on Claude
Code); whether OpenCode's scanner sees a redirect target was not read in the
docs. The hook is not in force in a `-p` session until the workspace is
trusted. Both keep the body's text as the backstop, as every hook does
(Part I, The protocol).

## 80. One memory on Claude Code (2026-11-14, v12.18)

**Source.** The review in `fable-review-results.md`. Claude Code's auto
memory loads its own `MEMORY.md` at the start of every session beside the
framework's `.ai/notes.md`, so a durable fact can be written to either, and
the agent has no rule for which.

**Facts, read in the docs on 2026-11-14.**

- https://code.claude.com/docs/en/memory: "Auto memory is on by default in
  local sessions", and "To turn it off for a single project, set
  `autoMemoryEnabled` in that project's settings" with the example
  `{ "autoMemoryEnabled": false }`. The `/memory` toggle saves the key "to
  your user settings at `~/.claude/settings.json`".
- https://code.claude.com/docs/en/settings-reference, settings index: the
  `autoMemoryEnabled` row lists its scope as "Any file", so the committed
  `.claude/settings.json` honors it. Precedence, from the settings page:
  project local over shared project over user, so a project `false` beats a
  user `true`, and a `true` in `.claude/settings.local.json` beats the
  project `false`.
- OpenCode has no second memory: its only persistent instructions are
  `AGENTS.md` and the files the framework writes. Nothing to turn off there.
  Copilot is skipped: no equivalent key was verified.

**Change.** `render_settings_json` writes `"autoMemoryEnabled": false`.
This turns a Claude Code feature off for the project, which is the point
and also a decision the user may not want; the README section "One memory on
Claude Code" says so and how to undo it: `"autoMemoryEnabled": true` in
`.claude/settings.local.json` (untracked, wins over the shared file), or the
same change in `.claude/settings.json`.

**The user's own value survives.** `settings.json` is framework-owned and a
re-init with `-y` regenerates it whole; that is unchanged for every other
key. `scaffold.write_settings` reads the existing file first and, when it
holds a boolean `autoMemoryEnabled`, writes that value instead of the
default (a bare re-init without `-y` skips an existing file, as before). In
`/framework-update` the updater merges the file, and its merge case now says
a value the project already has stays and the reference's `false` fills only
a file with no such key, which is also how a scaffold older than 12.18 gets
the default. `tests/test_settings.py` pins all of it.

## 81. AGENTS.md loads on Claude Code in every case (2026-11-14, v12.19)

**Source.** The review in `fable-review-results.md`: one real project lost
its instructions. 7.1 (see its version log entry) dropped the
generated `CLAUDE.md` pointer because Claude Code 2.1.277 reads `AGENTS.md`
itself, and left the parent-directory case to the update agent's judgment.
In that project a `CLAUDE.md` sat in the parent workspace directory and none
in the project, so Claude Code read the parent's file only and never
`AGENTS.md`. Until 7.1 the generator wrote `CLAUDE.md` as "Canonical agent
instructions live in AGENTS.md (vendor-neutral).\n@AGENTS.md\n" through the
ordinary `write()`, so it was recorded as a framework file.

**Facts, read in the docs on 2026-11-14.**
https://code.claude.com/docs/en/memory:

- "An `AGENTS.md`, and no `CLAUDE.md` or `CLAUDE.local.md` in your working
  directory or above it: Your `AGENTS.md`"; "An `AGENTS.md` and a
  `CLAUDE.md` or `CLAUDE.local.md` in your working directory or above it:
  Your `CLAUDE.md` files only"; "A `CLAUDE.md` that already imports
  `AGENTS.md`: Your `CLAUDE.md`, with `AGENTS.md` included through the
  import".
- Loaded once, not twice: "A `CLAUDE.md` containing `@AGENTS.md`: you can
  leave it. Keeping the import never makes Claude read `AGENTS.md` twice,
  whichever Project instructions value you use." So the default setting
  does not double-load it, and neither do the other values.
- Import parsing "skips Markdown code spans and fenced code blocks", and a
  project CLAUDE.md may live in `./CLAUDE.md` or `./.claude/CLAUDE.md`. A
  `CLAUDE.md` symlinked to `AGENTS.md` is read once.
- Copilot and OpenCode read `AGENTS.md` natively and have no such file;
  this change is claude only.

**Change.**

- `scaffold.ensure_agents_import(root)`: no root `CLAUDE.md`, write the
  single line `@AGENTS.md`; one without the import, append the line and
  leave every other byte; one with it (outside code spans and fences), a
  symlink to `AGENTS.md`, or a `.claude/CLAUDE.md` that imports it, change
  nothing. It returns `created`, `appended` or `unchanged`, so a second
  run changes nothing.
- `init-agent` calls it on the claude harness, in a re-init too. The
  update's reference scaffold has no `CLAUDE.md`, because the update
  restores it on the project, not by diffing.
- `/framework-update` does it by a script, not by the updater's judgment:
  the new CLI flag `init_agent.py --ensure-agents-import` (beside
  `--detect` and `--emit-reference`) runs `ensure_agents_import` in the
  project and prints `CLAUDE.md: created|appended|unchanged`. The claude
  update body runs it in step 5 (verify), puts the line in the report, and
  backs up `CLAUDE.md` with the other host files in step 1. The 7.1
  migration note in `content.py`, which said to delete the pointer unless the
  user added text or a parent `CLAUDE.md` existed, now says the file is
  never retired and that step 5 restores it.
- Recorded file list: **no.** `CLAUDE.md` is written outside `write()`, so
  it is not in `framework_files`. Once it holds anything beyond the import
  line it is the user's, and a retire deletes what the list names. A
  harness switch away from claude reports it as left behind instead of
  moving it (`HARNESS_ENTRY_PATHS` names it). A pre-7.1 scaffold's list
  still names `CLAUDE.md`; the update note says it is not retired.
- `tests/test_claude_md.py` covers absent, present without the import, present
  with it, what counts as an import, a symlink, re-init twice, the flag, the
  recorded list, a switch, the other harnesses and the reference.

**What this does not do.** It adds a file to a claude project that did not
have one (the one line), and changes a `CLAUDE.md` the user wrote by one
appended line. That is the price of loading `AGENTS.md` deterministically; a
user who does not want it deletes the line, and a later re-init adds it again.

## 82. A freshness check for the notes (2026-11-14, v12.20)

**Source.** The review in `fable-review-results.md`, Priority 2, item 7.
Persistent notes go stale and nothing checked them: a note can cite a file
that was renamed a year ago, and a hub that grew past two screens is read
whole in every session that loads it.

**What the format prescribes, and so what is checked.** Read in
`templates/config/notes-stub.md`, `templates/instructions/agents.md`,
`templates/task/do.md` and Part I: the hub `.ai/notes.md` is appended and
telegraphic, "back under ~1 screen" and split into leaves once it passes "1-2
screens"; a leaf is `.ai/notes/<topic>.md`, "linked from the hub with a
one-line pointer" written `- [topic](notes/<topic>.md) - hook`; do.md ends
with "confirm every leaf under `.ai/notes/` is linked from `notes.md` and
every pointer resolves". Entries are not dated by any rule, so **there is no
undated-entry flag**: adding one would check something the format never asked
for.

**Change.** `tasks.py notes`, in the manner of the long-Findings flag: a
function that reads files and returns lines, shown by a subcommand and, when
non-empty, at the end of `/task list`. Four flags, each one line, file first:

- the hub over `NOTES_MAX_LINES = 100` lines or `NOTES_MAX_BYTES = 8000`
  bytes. 100 lines is two screens of 50, the point where the hub's own text
  says to split; 8,000 bytes is those 100 lines at the 80 characters a
  telegraphic line seldom passes, about 2,000 tokens. The two numbers are
  also the cap of the session-start text of section 83, so a hub is flagged
  for the same size at which it would be cut.
- a cited path that does not exist, in the hub or a leaf.
- a hub link to `notes/<x>.md` that does not exist.
- a leaf under `notes/` that no line of the hub links (a mention of its
  path counts).

**The path flag is built to stay quiet.** A backticked token counts only
when it has a `/`, no space, only `[\w.@+-]` and `/`, and its last component
ends in a file extension: so no bare file name (it could sit in any
directory), no directory (`iot/` was an MQTT topic prefix in a real hub), no
glob, `<placeholder>`, `$VAR`, URL, `~/`, absolute or `..` path (a sibling
repository), no `read/write` or `text/html`. It is skipped inside fenced
blocks and comments, and on a line that says a path was removed, is old,
earlier or planned (`GONE_RE`; the words inside the backticks do not count).
A path that exists anywhere under the project root as the tail of a longer
one counts as existing (a note may name it from inside a subdirectory; nested
repositories are walked too), and so does one the project's gitignore
ignores, because build output is absent from a fresh checkout. Without a git
repository nothing is flagged for a path. Run against seven real hubs, the
first version flagged one MQTT topic prefix and one deliberate "was removed"
mention; both led to the rules above. What is left in those hubs is a path
that is gone and one that moved.

**Exit code.** `tasks.py notes` exits 0 with no output when there is nothing
to flag and 1 with the lines when there is, as `tasks.py models` exits 1 when
a role is unset: non-zero says something needs a look. `/task list` ignores
the code and prints the lines. A missing hub gives no output; binary content
or an unreadable file gives one line naming the file and the reason; any
other error gives one `check failed` line. Nothing raises.

**Where it shows.** Only in `tasks.py notes` and at the end of `/task list`
(also with no live tasks), only when there is something to flag. The `/task`
dispatcher already copies the script's output verbatim, so no skill text
changed and no always-loaded word was added. All harnesses: the script is the
same file on each.

**Tests.** `tests/test_notes.py`: clean notes, each flag, each deliberate
silence, the exit codes, the list line, a missing, binary, unreadable and
non-UTF-8 hub, a dangling leaf, and no repository.

## 83. The notes hub is in context at session start (2026-11-14, v12.21)

**Source.** The review in `fable-review-results.md`, Priority 2, item 6.
Rule 1 of `AGENTS.md` told the agent to read `.ai/notes.md`: one tool call per
session and after each compaction, and only if the agent did it. The case for
adding it to what is always loaded is in Part I, Property 4.

**Facts, read in the docs on 2026-11-14.**

- https://code.claude.com/docs/en/hooks, SessionStart: "Runs when Claude Code
  starts a new session or resumes an existing session." Matchers: `startup`,
  `resume`, `clear`, `compact` ("Auto or manual compaction") and `fork`.
  Output: "A hook that only adds context can print it without building JSON,
  because Claude Code adds a SessionStart hook's plain-text stdout to
  Claude's context"; `additionalContext` is the JSON form, "added to Claude's
  context at the start of the conversation, before the first prompt". So the
  script prints plain text. Cap: "A hook's `additionalContext`,
  `systemMessage`, and `initialUserMessage` strings, and its plain stdout,
  are capped at 10,000 characters", over which the output becomes a file path
  and a preview of 2,000 characters; "keep anything Claude must always see
  within the cap". The hub cap (8,000 bytes) plus header, cut line and three
  flag lines stays under it (tested).
- Same page, the `timeout` field: "Seconds before canceling", default 600 for
  a command hook. The entry sets 15, because this hook blocks the start.
- Same page: SessionStart is listed as a per-session event and sub-agents
  have their own, `SubagentStart` ("Runs when Claude spawns a subagent with
  the Agent tool"). No sentence says outright that a sub-agent does not run
  SessionStart; it is a session event and a sub-agent is not a session. The
  worker therefore reads the hub itself, as `work.md` says. The one case the
  hook would reach a worker is a session started as `claude --agent worker`
  (the Herdr tab): its payload carries `agent_type`, "present when you start
  Claude Code with `claude --agent <name>`", and the script prints nothing for
  `worker`.
- Matcher choice: `fork` is left out of
  the matcher: a forked session carries the conversation, hub included.
  `resume` is in, because a session resumed from before this version has no
  hub and AGENTS.md now says not to read it, and a refresh after notes
  changed elsewhere is the documented use ("run again on resume ... so they
  can refresh their context").

**OpenCode: not shipped.** The plan was `instructions: [".ai/notes.md"]` in
`.opencode/opencode.json`. https://opencode.ai/docs/config/ and
https://opencode.ai/docs/rules/ confirm the key ("Declare additional
instruction files, globs, or HTTP(S) URLs", "OpenCode loads them alongside
discovered `AGENTS.md` files") and show project-relative examples
(`"CONTRIBUTING.md"`, `"docs/guidelines/*.md"`), but say nothing on what a
relative path resolves against (the config sits in `.opencode/`, not the
project root), on a missing file, on a size limit, or on whether sub-agents
get the file. `opencode debug config` (2.2.5) prints the key as written and
resolves nothing; `opencode api` creates a session but its context is empty
until a prompt, which is a model call. The rule is that an unverified fact
does not ship, so nothing was written for OpenCode: no `instructions` entry,
no merge logic in the config writer, and the text keeps the agent reading the
hub itself. A run that shows the file in a session's instructions, from the
project root and from a subdirectory, is what would let a later change add it;
it would also need its own cap, since the key has none (section 82's flag
covers a hub over the cap, nothing cuts it).

**Copilot: skipped.** No verified equivalent of a session-start context hook
(its hooks in `.github/hooks/llm-agent.json` are `preToolUse` and
`agentStop`).

**Change (claude).**

- `templates/hooks/notes_session.py`, written to `.claude/hooks/` and
  recorded as a framework file (claude scaffolds record 20 files, copilot 18,
  opencode 19). It runs `tasks.py notes --session` and prints its stdout, so
  the cap, the header and the flags have one source (section 82). Fails open:
  any error, a missing or slow `tasks.py` (10 seconds) prints nothing, exit 0.
- `tasks.py notes --session` prints: a header naming `.ai/notes.md`, the hub
  with HTML comments removed (the scaffold's authoring note is for whoever
  writes the hub, not for the model), cut at 100 lines or 8,000 bytes with
  one line saying so and that the rest is in the file, then at most three of
  the section 82 flags ("... and N more" after them; the size flag is left
  out when the cut line has said it). Nothing is printed for a missing hub, a
  binary or unreadable one, or the untouched stub (nothing left but the title
  once comments are gone). Exit 0 always.
- `.claude/settings.json`: `SessionStart`, matcher
  `startup|resume|clear|compact`, one command hook, `timeout` 15. In
  `/framework-update` the settings merge case says a framework hook the
  project lacks is added with its script, which is how a scaffold older than
  12.21 gets it; the update's existing check that every hook command in
  `settings.json` points at a file covers the script.
- Texts made true. `AGENTS.md` rule 1: "Read `.ai/notes.md` first unless in
  context." (one rule for every harness: where nothing loads the hub it is
  never in context, so the agent reads it); to keep the word count from
  growing, "Open only the leaves under `.ai/notes/` that a task needs" became
  "Open only leaves a task needs" (`.ai/notes/` is still named under Tasks
  layout). `create.md` step 1 and `do.md` step 1 say "unless it is in
  context". `work.md` is unchanged: the worker reads the hub itself. `explore`
  and the skills never told the session to read the hub. The notes stub's own
  "Read at the start of a task" is user-owned once written and left alone.
  AGENTS.md words before the generated section: claude 573 to 572, opencode
  571 to 570, copilot 689 to 688 (Part I's figures were stale and are
  corrected).

**What a live run must show.** On Claude Code: a new session in a project
with a filled hub starts with the hub text in context before the first
prompt (ask what the notes say about a given line, with no tool call
before), the same after `/compact` and `/clear`; a project with the stub
gets nothing; `/task do` still works, with its worker reading the hub; a
`claude --agent worker` tab gets no second copy. In a `-p` session the
hook runs without `--bare` (https://code.claude.com/docs/en/headless: "Without
`--bare`, a `-p` session runs the hooks in a project's `.claude/settings.json`
... even in a folder you've never trusted"), and not with it, so a `--bare`
run reads the hub itself, as the text allows.

## 84. Script output without a model round trip (2026-11-14, v12.22)

**Source.** The review in `fable-review-results.md`, Priority 2, item 8.
`/framework-models` only prints what `tasks.py models --list` computes, and
the model spent a turn calling it.

**Facts, read in the docs on 2026-11-14.**

- Claude Code, https://code.claude.com/docs/en/skills: "The `` !`<command>` ``
  syntax runs shell commands before the skill content is sent to Claude. The
  command output replaces the placeholder"; "The inline form is only
  recognized when `!` appears at the start of a line or immediately after
  whitespace"; "Substitution runs once ... Command output is inserted as
  plain text and is not re-scanned". Failure: "A failed command aborts the
  entire skill invocation ... Claude never sees the skill content for that
  invocation", and "any non-zero exit code counts as a failure", with
  `|| true` named as the way out. stderr is merged into stdout.
- Permissions, same page: "Injected commands never prompt for permission
  while the skill renders. Claude Code checks each one against your
  permission rules first", and outside auto mode "when a command's permission
  check returns anything other than allow, Claude Code aborts the
  invocation. To keep an unmatched command from aborting, pre-approve it with
  `allowed-tools`". So the project's own allow list (`Bash(python3
  .ai/agent/tools/tasks.py:*)` in `permissions.txt`) covers the command, and
  the skill also carries `allowed-tools: Bash(python3
  .ai/agent/tools/tasks.py *)` (the page's own example form, a grant for the
  turn) for a project whose list was edited. `disableSkillShellExecution`
  turns the whole feature off by policy; the command is then replaced by
  `[shell command execution disabled by policy]`, and the body then tells the
  model to run the script itself, as it does with arguments.
- Arguments, same page: "`$ARGUMENTS` always expands to the full argument
  string as typed" and an argument containing `$1` is inserted literally.
  Nothing says an argument is shell-escaped where it lands inside a `!`...``
  command; the page does not address it.
- OpenCode, https://opencode.ai/docs/commands/: "Wrap a shell command in `!`
  followed by backticks to insert its output before the prompt is
  submitted"; "OpenCode runs each block with the configured shell in the
  active project location and inserts its combined output"; "Shell blocks run
  when OpenCode evaluates the command, outside the agent's tool permission
  flow"; "Argument placeholders are expanded first" and "Do not place
  untrusted arguments inside shell blocks". What a failing command does is
  not stated.
- Copilot: skipped. No injection form was verified for prompt files.

**Change.** `/framework-models`, on Claude Code and OpenCode: the body
carries `` !`python3 .ai/agent/tools/tasks.py models --list --exit-zero` `` on
a line of its own and says to reply with that output verbatim; with
arguments (they only change the printed command) it runs the script again
with them, as before. The line has no `$ARGUMENTS`, so nothing the user types
reaches a shell. Copilot keeps the old body, so the bodies of this command
differ by harness while the names stay equal. The text comes from
`templates/skills/fragments/<harness>/models-run.md`.

**The wrapper is a flag, not `|| true`.** `tasks.py models` exits 1 to say a
role is unset, and that would abort the invocation. `|| true` makes a
compound command, and a compound passes the permission check only when every
part is allowed: `true` is not in the allow list. So `tasks.py models` takes
`--exit-zero`: exit 0 always, the first line still `MODELS OK` or `MODELS
MISSING`. `/task do`'s gate does not pass it and still gets exit 1.

**Not changed: `/task`.** The dispatcher starts with `tasks.py resolve
<arguments>`. The arguments are free text (`create fix the parser; it's
broken`, quotes, backticks). Neither harness's docs show them reaching the
shell safely (Claude Code's page is silent, OpenCode's warns against it), so
nothing that carries them is injected. An argument-free injection of the
`/task list` table was considered and rejected: the injection runs on every
`/task`, `create` and `do` included, and the dispatcher cannot make it
conditional on its first word, so every `create` and `do` would carry the
table (a few hundred tokens, more with flags) and the model would have to
ignore it, to save one tool call on `list`. Splitting `/task list` into a
command of its own would change the command set of Property 3. `/task list`
and `/task tree` keep running the script themselves.

**No `model:` field.** The review suggested one on skills; the framework
knows no model names, so none is written.

**Check.** `check_templates.check_injection_syntax` replaces the OpenCode
syntax check: every `!`...`` or ```` ```! ```` in a rendered command, on any
harness, must be the one allowed command with no `$` in it, and a Claude
skill with an injection must pre-approve it. `tests/test_inject.py` runs the
command through a shell in a real scaffold with the roles unset and set.

**What a live run must show.** `/framework-models` on Claude Code answers
with the script's output with no tool call, in a project whose allow list
has the rule and in one whose list lacks it (the `allowed-tools` grant), and
with `worker=<m>` arguments runs the script once more; the same on OpenCode,
where the failure behavior is unknown and `--exit-zero` makes it moot; a
session with `disableSkillShellExecution` set shows the policy notice and
falls back to running the script.

## 85. The worker's contract is in its agent file (2026-11-14, v12.23)

**Source.** The review in `fable-review-results.md`, Priority 2, item 9. A
worker started by reading `.ai/agent/task/work.md`: one turn before it did
anything, on every spawn.

**Who reads `work.md`** (grep of `templates/`, `README.md`,
`tests/task-commands.md`, Part I):

- The supervisor's spawn prompt in `do.md`: "Read work.md and follow it".
  Copilot's worker still follows it. On Claude Code and OpenCode the prompt
  is now only `You are the worker for task <id>.`
- A worker continued after a report: `do.md` and the Herdr continue prompt
  say "read `work.md` again" (section 73, that changed rules reach a
  running task). Kept, for every harness.
- The Herdr worker. On Claude Code the tab starts `claude --agent worker`,
  whose system prompt is the agent file, so it gets the contract at start
  like a sub-agent. On OpenCode the tab's session spawns the worker as a
  sub-agent, the same agent file. On Copilot `copilot --agent worker`, the
  pointer, as before.
- `steps.md` says it is read "from `work.md`"; `tests/task-commands.md` cases
  that look for the read in the transcript (changed: they no longer expect
  it on Claude Code and OpenCode); README.
- Not a reader any longer on Claude Code and OpenCode at start; so the file
  has readers on every harness (the continued worker, Copilot) and stays.
  Not removed in this change.

**Change.**

- `templates/agents/worker.md` is the frontmatter and a `body` slot. On Claude
  Code and OpenCode the body is `templates/agents/worker-preamble.md` (the
  model-check guard `init-agent --models` relies on: a prompt that says it is
  init-agent's model check is answered with one word, and the contract is
  all the instructions) followed by `render_task_part("work", harness)`: the
  text that writes `.ai/agent/task/work.md`, rendered once more, never a
  second copy. On Copilot the body is `templates/agents/worker-pointer.md`,
  the old text, because the brief for this change named the two harnesses
  and Copilot's agent file semantics were not re-verified.
- The agent body as the system prompt is already how both harnesses use it
  (the old body was the same field, only short). Frontmatter is unchanged:
  `maxTurns` or `steps`, `disallowedTools: Agent`.
- `do.md`'s spawn prompt is a slot filled from
  `templates/task/fragments/<harness>/worker-prompt.md`.
- `work.md` step 1 reads `.ai/notes.md`, the task file and `steps.md`
  together, as parallel reads in one turn (step 2 no longer has its own
  read). **The continuation sentence.** It said to read this file again
  when the supervisor continues the worker, because its rules may have
  changed. For a worker whose contract is its system prompt, that text is
  as old as the session's start; the file is current. The sentence now
  names the file and `steps.md`: a continued worker re-reads both in one
  turn, and says why. That costs a read only on a continuation, never on a
  start, which is the case this change is about. A fresh spawn picks up the
  new agent file by itself.
- `check_templates.check_worker_contract`: on Claude Code and OpenCode the
  rendered body contains the rendered `work.md`; the guard is there; `do.md`
  no longer sends that worker to read `work.md`; on Copilot it still does.
  The worker agents are now in the rendered artifacts the slot and
  unfilled checks scan.
- `/framework-update`'s merge case for agent files says the worker's body is
  a structural change to take, the `model:` line and user additions stay.
  `agentgen/models.py` (`with_model`, `current`) and `write_agent` only touch
  the `model:` line and are unchanged; `tests/test_models.py` and the new
  `tests/test_worker_contract.py` show one line after `--models` and after a
  forced re-init with the long body.

**Size, the worker's agent file in words (rendered).**

| harness | before | after |
|---|---|---|
| claude | 99 | 1,048 |
| opencode | 97 | 1,046 |
| copilot | 95 | 95 |

A worker's first turn used to read about 950 words by a tool call; it now
has them as its system prompt, a cached prefix of every round, and its
turn count falls by one. Nothing is added to any session that does not
spawn a worker.

**What a live run must show.** On Claude Code and OpenCode a `/task do`
worker's transcript starts with one turn that reads `.ai/notes.md`, the task
file and `steps.md` together, and never reads `work.md` before its first
report; a continued worker reads `work.md` and `steps.md` again; `init-agent
--models` still gets `hello` from the longer worker; a `claude --agent
worker` Herdr tab behaves as a sub-agent does. A Copilot worker still reads
`work.md` first.

## 86. The notes hub in context on OpenCode (2026-11-14, v12.24)

**Source.** Section 83 did not ship the OpenCode half because the docs did not
say what a relative `instructions` path resolves against. That is now seen
live, so the section's "OpenCode: not shipped" and "Where. Claude Code only"
no longer hold; this section replaces them (83 is left as written, a record of
what was known then). The Part I argument of Property 4 applies unchanged.

**Facts.** Verified by the supervisor on OpenCode 2.2.5 in a TUI session in a
scratch scaffold (session model sonnet): with `"instructions": [".ai/notes.md"]`
in the generated `.opencode/opencode.json`, a fresh session answered a
question whose answer exists only in `.ai/notes.md` with no tool call. So the
key is honored in the project config at `.opencode/opencode.json`, and the
relative path resolves against the project root. `opencode debug config` in a
scratch scaffold lists the key. https://opencode.ai/docs/config/: "Declare
additional instruction files, globs, or HTTP(S) URLs. OpenCode loads them
alongside discovered `AGENTS.md` files." **Not verified, open points:** what a
missing file does (the scaffold always writes `.ai/notes.md`, and the hub is
never deleted by the framework), whether sub-agents receive the instructions,
and any size limit.

**Change.**

- `render_opencode_config` writes `"instructions": [".ai/notes.md"]`
  (`const.NOTES_INSTRUCTION`).
- `scaffold.write_opencode_config`, as `write_settings` does for
  `autoMemoryEnabled`: a forced re-init reads the existing file first; when
  `instructions` is a list of strings it is kept, in order, with `.ai/notes.md`
  appended once if it is not there. Any other value (not a list, a non-string
  entry) and an unreadable file are replaced by the default. Every other key
  is regenerated as before; a bare re-init skips the file.
- `/framework-update`: the opencode merge case says entries the project has
  stay in their order and the reference's `.ai/notes.md` is added once, which
  is also how a scaffold older than 12.24 gets it.
- `tests/test_opencode_config.py`.

**What differs from Claude Code.**

- No cap. The key loads the file whole. A hub over 100 lines or 8,000 bytes
  is loaded in full; the `tasks.py notes` size flag (section 82) is what says
  so, in `/task list`.
- No stub suppression: the untouched stub, with its authoring comment, is
  loaded (about 170 words) until the hub holds something. HTML comments are
  not stripped either.
- The freshness flags are not shown at session start, only in `/task list`
  and `tasks.py notes`.
- The worker on OpenCode still reads the hub itself, per `work.md`. Whether
  its sub-agent session also receives `instructions` is the open point
  above; if it does, the read is a duplicate of a small file. `work.md` is
  unchanged.
- The texts say "unless in context" and needed no change; nothing says an
  OpenCode session must read the hub itself. Copilot stays skipped.

**What a live run must show.** A new OpenCode session answers from the hub
with no tool call (seen once); after a user's own `instructions` entry and a
`init-agent -y` it still loads both; whether a `/task do` worker sub-agent
has the hub in its first turn.

## 87. Considered, not built: updater effort, path-scoped notes (2026-11-14)

No version bump: nothing shipped. Both came from the review's third
priority; the record is here so neither is proposed again without new
evidence.

### A lower effort for the updater: not built

**Facts**, https://code.claude.com/docs/en/sub-agents: the `effort` field of
an agent file is "Effort level when this subagent is active. Overrides the
session effort level, but not the `CLAUDE_CODE_EFFORT_LEVEL` environment
variable. Options: `low`, `medium`, `high`, `xhigh`, `max`; available levels
depend on the model." https://code.claude.com/docs/en/model-config: a level
the model does not support falls back "to the highest supported level at or
below the one you set", and a model not in its table does not support effort
at all. Not stated anywhere read: how a skill's `effort` (`high` for
`framework-update`, `SKILL_EFFORT`) interacts with the field of a sub-agent
the skill hands work to. The field is real; the open interaction does not
matter here, because the update body hands the merge to the sub-agent and
the field says it overrides the session's level.

**Why not.**

- Section 56 made the sub-agents inherit the session's effort, the owner's
  call, so that one setting (`/effort`, `--effort`) governs a run and the
  agent files carry none. Nothing about the updater is different in kind
  from the worker or the reviewer on that point, and no measurement
  overturns it: the benchmark that motivated it did not run the updater.
- Section 64 names the risk of this role: a small model merging framework
  files, where the check from the files catches a missing file, a lost
  `model:` line or a lost project section "not a subtle bad merge inside a
  file". The merge is a three-way one with judgment on user edits, not a
  lookup. Lower effort moves exactly that risk up. The saving is one short
  run per update on a small model, and nobody measured it. The six
  Haiku-class updates of section 64 were all right at the session's effort;
  there is no run at `low`.
- Writing `effort: low` would be a value shipped into every scaffold on a
  guess, for a role whose failure is silent.

**OpenCode.** The variant is part of the `model:` line, the user's value
written as typed by `init-agent --models`; the framework writes none. The
README already says a name may carry a variant (`claude-agent/sonnet#medium`)
and that without one the sub-agent runs on the model's default variant, so no
hint text changes. https://opencode.ai/docs/config/ says "agent and command
model references can select one". Copilot keeps a sub-agent's effort in the
user's settings (section 56) and is skipped.

**A user who wants it** can add `effort: low` to `.claude/agents/updater.md`
by hand; `/framework-update`'s merge keeps a user's edit to an agent file
(a forced `init` regeneration keeps only the `model:` line, as before).

**What would change the decision.** A run of the update at `low` against a
pristine reference render, over projects where user edits sit in the files
the merge touches, with no merge error that the session's own effort did not
also make; or a measured cost that makes the saving worth a rule.

### Path-scoped notes on Claude Code: not built

The idea: a leaf under `.ai/notes/` with a `paths:` frontmatter, linked by
a deterministic step into `.claude/rules/`, so a gotcha loads when the agent
touches the directory it concerns.

**Verified**, https://code.claude.com/docs/en/memory: "A path-scoped rule
loads when Claude uses the Read, Write, or Edit tool on a matching file."
It also loads on a Bash read of a single file (`cat`, `head`). "The
`.claude/rules/` directory supports symlinks." A symlink whose target is
outside the working directory is treated "like an external import" and,
after approval, only rules without `paths` load from it; `.ai/notes/` is
inside the project directory, so that clause would not apply.
https://opencode.ai/docs/rules/ describes only directory-scoped
`AGENTS.md` ("only apply when you are working in this directory or its
sub-directories") and globs in `instructions` combined at start; it states
no loading that depends on the files touched. So OpenCode has no equivalent,
as the review found, and Copilot none known.

**Not verified, and each is a load-bearing fact.**

- Whether a gitignored file or link under `.claude/rules/` is loaded. The
  memory page says a gitignored `CLAUDE.local.md` loads, and says nothing
  for `rules/`. The design needs the links gitignored, since the notes are
  private and the host repository must not gain tracked files that point
  into `.ai/`.
- Whether a sub-agent (the `worker`, which does the code work under
  `/task do`) gets path-scoped rules when it reads a matching file. The
  page speaks of "Claude" using the tools; what a sub-agent starts with is
  described separately, and nothing read says path-scoped rules reach it.
  The worker is where most reading happens, so a mechanism that skips it
  covers little.

**Other reasons.**

- It adds a second loading path for one notes format, on one harness, with
  a script keeping links in the host repository in step with the leaves
  (create, update, remove, and a user's own files in `.claude/rules/` never
  touched). Property 3 is not broken by loading differently (section 83
  already does that for the hub), but each such path is a thing to keep
  right, and it is machinery for a case nobody measured: no run showed an
  agent missing a leaf it should have opened.
- Property 4 is untouched in principle (no always-loaded text), but a
  `paths:` glob that matches nothing is a silent dead note, which would need
  a check in `tasks.py notes` (section 82) and guidance in the stub and
  `explore`.
- A symlink in the host working tree is a Windows problem (the memory page
  names it for `CLAUDE.md`).

**What would change the decision.** The two facts above confirmed in the
docs or seen in a session with the `InstructionsLoaded` hook the memory page
names (a gitignored link in `.claude/rules/` with `paths:` loads on a read,
also in a sub-agent), and a run where an agent missed a gotcha that sat in a
leaf. Then the design above is sound as sketched; build it as version 12.x
with tests for the link step.

Built in 12.26 once the first two points were seen live: see section 89.

## 88. Compaction on OpenCode, and a user's keys survive a re-init (2026-11-14, v12.25)

**Source.** The review's item on `compaction.keep.tokens` and
`compaction.buffer` for long OpenCode sessions, "set once a real session shows
the default hurting".

**Facts**, https://opencode.ai/docs/config/: the example is
`"compaction": {"auto": true, "keep": {"tokens": 15000}, "buffer": "15%"}`;
"`buffer` is the share of the model's context window kept free before
automatic compaction starts"; "Top-level `compaction.auto: false` disables
new automatic compaction without discarding installed checkpoints." **Not
stated:** the defaults. The example values are an example, not a documented
default, so the README does not give any.

**Not built: values in the generated config.** No measurement shows the
default hurting; a number shipped into every scaffold would be a guess, and
with the premise of Part II that the value is organizational, not speed, there
is no run to tune against. The README says the framework leaves the default,
names the three keys and when a user might change them. Claude Code is
skipped (its compaction is not configured this way), and Copilot.

**A bug found while checking, fixed.** `write_opencode_config` (section 86)
kept the user's `instructions` on a forced re-init and regenerated every other
key from the template, so a user's `compaction` block was dropped, and with it
a `model` or `mcp` entry. The update body already says settings a user added
are not framework state and are kept, so only the CLI path lost them. Now
every top-level key the generator does not itself write is carried over;
`permissions` is regenerated, `instructions` merges as before, and an
unreadable file or a non-object is replaced. A fresh scaffold is
byte-identical. `tests/test_opencode_config.py` gains the cases, and fails on
the old code.

**What a live run must show.** `opencode debug config` in a scaffold with a
`compaction` block, after `init-agent -y`, still lists it.

## 89. Path-scoped notes leaves on Claude Code (2026-11-14, v12.26)

**Source.** Section 87 recorded this item as not built because two facts were
unverified. Both were then seen live by the supervisor, on Claude Code
2.1.325, in headless sessions on a small model, in a scratch project where
`.ai/` and `.claude/rules/src.md` are gitignored, `.claude/rules/src.md` is a
relative symlink (`../../.ai/notes/src.md`) and the leaf starts with a
frontmatter `paths:` list holding `"src/**"`:

1. Main session: after one Read of `src/a.py` and nothing else, the session
   knew a fact that exists only in the leaf, and said the harness attached it
   as a context block naming `.ai/notes/src.md`. A gitignored symlink under
   `.claude/rules/` is loaded.
2. Sub-agent: a general-purpose sub-agent given the same instruction did one
   Read of `src/a.py`; its transcript shows a system reminder with the
   leaf's contents right after that Read, and it answered correctly. Sub-agents
   receive path-scoped rules, so the `worker` does.

**Not tested, so not relied on.** Loading on Edit or Write (the memory page
states it, https://code.claude.com/docs/en/memory: "A path-scoped rule loads
when Claude uses the Read, Write, or Edit tool on a matching file"), and
whether the rule is injected once per session or on every matching read. The
leaf is short by construction; a repeat costs its own size and nothing
else.

**Change.**

- A leaf `.ai/notes/<topic>.md` may start with a frontmatter holding only
  `paths:`, a list of quoted globs relative to the project root. The hub
  `.ai/notes.md` never carries one. Written guidance is in the notes stub
  comment and the `explore` body, two or three sentences, harness-neutral:
  where the harness loads a leaf only when a matching file is read it is
  linked for that, elsewhere it is read on demand. `agents.md` is untouched,
  so its word count is.
- `tasks.py notes --link [--quiet]`, the one implementation. On the claude
  harness (the stamp in `.ai/agent/framework.json`) it keeps one relative
  symlink `.claude/rules/ai-notes-<topic>.md` per leaf with a usable
  `paths:`, target `../../.ai/notes/<topic>.md` (a nested leaf joins its
  path with `--`). It creates, retargets a link that points elsewhere inside
  `.ai/notes/`, and removes a link whose leaf is gone or lost its `paths:`.
  It manages only a symlink that has the prefix `ai-notes-` AND points into
  `.ai/notes/`; a user's own file, own link, a prefixed link pointing
  elsewhere and a regular file holding the name are never touched (the last
  is reported and the leaf is not linked). On any other harness it prints one
  line saying there is nothing to do. `--quiet` hides the "up to date" and
  "nothing to do" lines.
- The host `.gitignore` gets one line, `.claude/rules/ai-notes-*.md`, added
  by the link step when it has something to link, only in a git checkout and
  only when `git check-ignore` says the links are not already ignored, the
  way `ensure_gitignore` treats `.ai/`. The notes stay private: the host
  repository gains no tracked file and no content of `.ai/`.
- Where it runs: `scaffold.link_notes` after the gitignore step on init and
  re-init of a claude project (it runs the project's own `tasks.py`, so there
  is no second implementation; a failure is one line, never a failed
  scaffold); `/framework-update` on claude, as a line in its verification
  steps that runs the project's `tasks.py notes --link` after the files are
  updated, which is also how an existing project gets its links; the agent,
  after it writes or changes a leaf's `paths:`. `--emit-reference` is not
  touched. Switching away from claude leaves the links (gitignored, inert on
  the other harnesses, relinked on a switch back); they are not retired.
- A filesystem that cannot make the link (a Windows checkout without the
  privilege, or `.claude/rules` not a directory): one line, exit 0, the leaf
  is read on demand. The step never raises.
- The frontmatter shape is strict, on purpose. Claude Code reads the block as
  YAML and, when it does not parse, "loads the rule as if it had no `paths`":
  at every session start, the opposite of the point. An unquoted glob that
  starts with `*` is a YAML alias and fails to parse. So the script links
  only `paths:` followed by `  - "glob"` or `  - 'glob'` lines; any other
  frontmatter (another key, `paths: a, b`, unquoted items, an empty list) is
  not linked and is flagged.
- The freshness check (section 82) parses the frontmatter, so it is not note
  text (a cited path is looked for in the body only), and adds two kinds of
  flag. A `paths:` glob that matches no file in the project, on every harness
  (the note is stale whichever harness reads it); the glob is read the way
  the memory page's table reads it: a pattern with no slash matches at any
  depth, a leading slash anchors it, `**` crosses directories, `{a,b}`
  expands. On the claude harness: links missing or stale, a frontmatter that
  cannot be linked, a name a user's file holds. A leaf with `paths:` still
  needs its hub pointer, so the "no line of notes.md links it" flag is
  unchanged.
- `notes --session` and the SessionStart hook print the hub only (section 83)
  and are unchanged; a new flag may appear among the at most three flag lines
  as any other. Verified: `tests/test_notes_link.py` checks the `--session`
  text has no frontmatter.
- `tests/test_notes_link.py`; `TESTING.md`; README.

**Property 3.** One command set and one notes format on three harnesses: a
leaf stays a plain markdown file, the commands and their bodies are the same,
and the frontmatter is inert on OpenCode and Copilot, which read the leaf on
demand as today. Only when a leaf reaches the context differs, as with the
hub in section 83 (Claude Code) and section 86 (OpenCode). OpenCode has no
loading that depends on the files touched (https://opencode.ai/docs/rules/
describes only directory-scoped `AGENTS.md` and `instructions` globs loaded
at start) and Copilot none known, so both are skipped.

**Property 4.** Nothing always-loaded is added: no text in `agents.md`, no
file in the session start. A leaf is read only when a matching file is
touched, and only on Claude Code. The own footprint grows by one subcommand
of `tasks.py` and the guidance sentences in a stub comment and a skill body.
It is an argument, not a measurement: no run shows an agent missing a leaf it
should have opened. The decision is the supervisor's, taken on the two live
observations above, and a leaf without `paths:` behaves as before.

**What a live run must show.** On Claude Code: a leaf with `paths:` written by
the agent after `/explore`, then `notes --link` run by it; a fresh session
that reads a matching file gets the leaf's text, and one that reads another
file does not; a worker sub-agent under `/task do` gets it on a Read of a
matching file; an Edit of a matching file loads it (untested); `git status`
in the host shows no new tracked file; a `/framework-update` of an older
project with a leaf that has `paths:` links it. On OpenCode and Copilot the
leaf is read when the agent opens it and the frontmatter does no harm.

## 90. The end of a task in one call (2026-11-15, v12.27)

**Source.** The supervisor's benchmark of nine fresh sessions on OpenCode
(six `/task do`, two `/task create`, one `/task list`), per model call from
the exported sessions: every call re-reads the whole context from the prompt
cache, so a session costs about the sum of the context over its calls, and
the last calls are the largest (45,000 tokens and more). The end of a task
took four to five separate calls: tick the steps, edit the task file
(Outcome), tick the Done-when criteria and `finish`, commit `.ai`, final
answer. Run totals (cache-read tokens): 12.14 3.06M and 3.20M, 12.26 3.45M
and 3.62M. These figures are the supervisor's; this change measured nothing.

**Change.**

- `tasks.py finish <id> done` takes `--tick <n>...` (Done-when criteria),
  `--tick-steps <n>...`, `--commit`, `--add <path>...` (paths relative to
  `.ai`, `notes.md` or a leaf) and `-m <message>`. The numbers stay
  explicit: which criterion is met is the agent's judgment, there is no
  "all". `--commit` runs `git add -- <paths>` and `git commit -- <paths>`
  with `tasks/<id>` and the `--add` paths only, so another task's staged or
  half-written files stay out of the commit (no `add -A`, no bare
  `git commit`, which would take whatever is staged). `finish <id> blocked
  <reason> --commit` commits the same way.
- All or nothing. A number the task does not have, an unmet gate (a
  criterion left unticked, no `Review:` line), no `.ai` repository or an
  `--add` path outside `.ai` refuses with exit 1 and leaves the task file
  and the repository as they were, the ticks included. Without flags
  `finish` behaves as before and prints the commit to run.
- `tick <id> done|steps <n>... --commit [-m <message>] [--add <path>...]`
  commits after a successful tick, for the worker's report: the Findings
  line is appended, then one call ticks the finished steps and commits
  `task: <id> worker round <n>` (the subject the benchmark grader looks for
  stays).
- `start` does not commit: the protocol never committed after it, and the
  pointer is gitignored, so there was nothing to join.
- `do.md` step 4 is the one call and then the final answer; step 3 says the
  Outcome and any `Review:` or `Delegation:` line not yet written go in with
  one edit. A session that works the task itself ticks its steps in the
  closing call (`steps.md` step 1). `work.md` ticks and commits in one call
  at the report. The models gate and `start` are one command line joined
  with `&&` (`models` exits 1 on `MODELS MISSING`, so `start` does not run).
  The commit of a correction and the continuation of the worker are issued
  in one turn. No rule was dropped; no script step takes a judgment.

**Calls at the end of a task** (protocol-required, a session that works the
task itself): before, tick steps, edit Outcome, tick criteria and `finish`,
commit, answer: five. After: edit Outcome, `finish ... --commit`, answer:
three. A worker's report: before,
append the Findings line, commit (and a `tick` call per step finished);
after, append the line, one `tick ... --commit` call.

**Property 3.** The script is the same on every harness; the text changes
are the same on all three.

**Property 4.** `do.md` grows from 2,755 to 2,911 words, `steps.md` from 814
to 846, `work.md` from 968 to 1,004 (rendered, claude), because the one-call
form is spelled out. That is a cost on every later call of a session that
reads them, argued against the calls it removes at the end. `tasks.py` grows by about 150 lines.

**What a live run must show.** A `/task do` session that ends with an edit,
one `finish ... --commit` call and its answer; `git -C .ai log` shows one
`task: done <id>` commit holding the task's paths only; a worker's rounds
end with one `tick ... --commit` call.

## 91. The start of a task in fewer calls (2026-11-15, v12.28)

**Source.** The same benchmark as section 90. The start of a `/task do`
session took three calls before it did any work: `resolve`, a read of
`do.md`, a read of the task file and the notes (the models gate and `start`
came after). Every call re-reads the context so far.

**Change.**

- `tasks.py resolve <id>` with a `DO` verdict prints the task file after its
  verdict line and the sentence, whole, between `-----` lines that say it
  has been read. The verdict stays the first line. Consumers checked: the
  dispatcher (`templates/skills/task.md`, rendered the same for the Copilot
  prompt file) reads the first line only; `tests/test_tasks_table.py`'s
  `verdict()` takes the first line; nothing else parses the output.
  `ARCHIVED`, `DONE`, `CREATE`, `INVALID` and `NONE` print what they printed.
  A `create` of an existing id prints the file too and wastes it; that case
  is rare and the verdict sentence still says to offer `do`.
- The dispatcher: for `do` and `create` the session runs `resolve` and reads
  `do.md` or `create.md` in one turn, two parallel tool calls, then acts on
  the verdict; for a bare id it still reads after the verdict. A part file
  read for a verdict that sends nowhere (`DONE`) is wasted: the price of one
  fewer turn.
- `do.md` step 1: the task file is already in the context (from `resolve`,
  or written by Create for an investigation) and is read again only when the
  output was cut off. The session decides worker or inline from it, says
  which, and then runs the models gate with `start`, the notes read and,
  when it works the task itself, the `steps.md` read, in one turn.

**Calls at the start** (a `/task do` session that works the task itself):
before, `resolve`, read `do.md`, models gate, `start`, read task file, read
notes, read `steps.md`: seven calls, three turns at the fewest and five as
measured; after, `resolve` with the read of `do.md` in one turn, then the
models gate with `start`, the notes and `steps.md` in a second: two turns and
six calls. The task file read is gone.

**Property 4.** The dispatcher grows by about 330 bytes. It is loaded on every
`/task` call and the part files are not shorter; the saving is the calls, not
the text.

**What a live run must show.** A `/task do` transcript whose first turn holds
`resolve` and a read of `do.md`, whose second turn holds the models gate
with `start`, and which never reads `task.md` before its first edit.

## 92. A session that works the task itself does not load the supervision (2026-11-15, v12.29)

**Source.** The same benchmark as section 90: reading `do.md` adds about
8,000 tokens to a session, and every later call carries them; five of the six
`/task do` sessions worked the task themselves (the small-task rule, or
`inline`) and never used the middle of `do.md`, the part on supervising a
worker.

**Change.** Done as section 77 did it for `steps.md`: text moved, not
rewritten. `templates/task/supervise.md`, written to
`.ai/agent/task/supervise.md` (a claude scaffold now records 21 framework
files, copilot 19, opencode 20), holds, in their old order:

- the hand-over: the worker is the `worker` agent, started fresh, its model
  from its agent file, the one spawn prompt and where it runs (the sub-agent,
  or a Herdr tab for `herdr`);
- the supervision: change no file while it runs, judge each report from the
  files, trust recorded evidence, answer by report kind (`review`,
  `question`, `done`, `stuck`, `waiting`, a round cut off by the turn
  limit), the corrections rule and the `Not sent back` line, continuing the
  same worker, the `Delegation:` line.

`do.md` keeps the decision rule (when to work the task itself, when a
worker; the count of open steps that edit a host file; the line that states
the decision), and what both paths need: the models gate, start, the
user-ask, redirect and workaround rules, the review gate, record, and the
close. At the decision it says: otherwise read `supervise.md`, in the turn of
step 1, and follow it. A session that works the task itself reads `do.md` and
`steps.md`. Only connective text changed (a word-for-word comparison of
the old `do.md` against the new `do.md` and `supervise.md` leaves exactly
the sentences that join them); the references that named a step of `do.md`
from `supervise.md` now say `do.md` step 2 and step 3. `supervise.md` is
rendered by `render_task_part("supervise")`; the worker spawn prompt and the
Herdr placement slots moved with it, so the `check_templates` and
`test_worker_contract` checks on the spawn prompt read `supervise.md`.
`check_templates` also fails when `work.md` or `steps.md` names it.

**Size (rendered, claude, words).** Before this change `do.md` was 2,995
(12.28; 2,755 at 12.26). After: `do.md` 1,869, `supervise.md` 1,235,
`steps.md` 843. A session that works the task itself loads `do.md` and
`steps.md`: 2,712, against 3,838 before. A supervising session loads `do.md`
and `supervise.md`: 3,104, against 2,995, the 109 words more being the
connective text and the header of the new file. A worker loads what it
loaded before.

**Property 3.** The file is written on every harness; the Herdr placement
differs per harness exactly as before.

**Property 4.** One more framework file; no always-loaded text.

**What a live run must show.** A `/task do` that works the task itself never
reads `supervise.md`; one that spawns a worker reads it in the turn of the
models gate and before the spawn.

## 93. A shorter dispatcher (2026-11-15, v12.30)

**Source.** `templates/skills/task.md` is loaded on every `/task` call and
holds the List and Tree sections whole, which a `do` or `create` call does
not need. The command is not split: the command set stays equal across
harnesses (Property 3). Section 91 had added 61 words to it.

**Change.** Wording only, each rule kept once:

- The `list` and `tree` bullets of Dispatch now point at the List and Tree
  sections, which already say to run the script, reply with its complete
  output verbatim and open no file; the one rule only the bullet held, to
  read no file first, stays in the `list` bullet.
- The Create bullet no longer restates the tracker question: `create.md`
  step 2 holds it (when to ask, `tasks.py trackers`, the issue key as the id
  prefix).
- Tree restates List's rules by reference instead of in full; the read-only
  rule, the no-heading rule and the no-start rule are in the sentence.
- The two "two tool calls together" notes of section 91 became one.

**Size (rendered, any harness, words).** 643 at 12.26, 704 at 12.29, 601
after: 103 fewer than 12.29 and 42 fewer than 12.26 (bytes: 3,735, 4,063,
3,380).

**What a live run must show.** `/task list` and `/task tree` unchanged in
output; a `/task create` asks the tracker question from `create.md` as
before (TC-C1b).

## 94. Tried and dropped: a cold worker (2026-11-15)

No version bump: nothing shipped. The record is here so the idea is not
built a second time without new evidence.

**The idea.** A worker whose only knowledge of the project and the job is
the task file: no notes hub, no project instructions file. The supervisor
has both in context and decides what the worker needs. The worker keeps its
protocol (its contract and `steps.md`), which is how it reports, what gets a
test and when it stops and asks, not project context.

**What was built** (one commit on a branch that was not merged, on top of
12.30):

- The worker's first step read the task file and `steps.md` only; it opened
  `.ai/notes.md` or a leaf only when the task file named it.
- The hand-over in `supervise.md` required the task's Notes to hold, before
  the spawn, the notes entries that bear on the task, the build, test and
  lint commands its steps need, and each project rule that constrains it.
- Claude Code: `omitClaudeMd: true` in the worker's agent file. The
  sub-agents docs: it starts the sub-agent "without the user, project, and
  local CLAUDE.md files in its initial context", from v2.1.271; ignored when
  the agent runs as the main session (`claude --agent worker`, the Herdr
  tab); path-scoped rules still load when the sub-agent works with matching
  files, so section 89 was unaffected.
- Because the worker then had no `AGENTS.md`, three of its rules were copied
  into the contract: keep going while a step needs no input; ask before
  anything destructive nobody asked for; no co-author line and no `.ai`
  content in a host commit.
- OpenCode: nothing could be changed. Its agents docs: "Project
  instructions, skills, references, and other instruction sources are still
  added", and no per-agent opt-out is documented, so its worker receives
  `AGENTS.md` and the `instructions` hub (section 86) without asking.
  Copilot: not looked at.

**What the live runs showed.**

- Claude Code 2.1.325, a project whose notes held an unusual test command,
  an unwritten owner rule and an unrelated fact; mid-size supervisor, small
  worker. The worker's transcript held no `CLAUDE.md`, `AGENTS.md` or hub
  text and no trace of the unrelated fact; it read the task file and
  `steps.md` and nothing else at its start; it ran the test command that
  existed only in the notes, which `/task create` had written into the task
  file. The task ended `done` in two worker rounds. The design works.
- The harness benchmark (`tests/harness-benchmark.md`, OpenCode 2.2.5, same
  profile, two runs per version), cache-read tokens:

  | | 12.30 | cold worker |
  |---|---|---|
  | grader | 6, 6 of 6 | 6, 6 of 6 |
  | run total | 2.60M, 2.57M | 2.53M, 2.64M |
  | the worker | 521k, 426k | 393k, 497k |
  | supervisor of the worker task | 210k, 201k | 264k, 312k |
  | session time | 316 s, 310 s | 312 s, 330 s |

  No regression and no saving: the totals overlap, the worker's runs
  overlap, and the supervisor of the worker task cost more in both runs.
  Whether the hand-over rule caused that was not checked in the sessions.

**Why dropped.**

- No cost benefit could be shown. On OpenCode the worker cannot be cold, so
  the change removes one read of the hub and adds hand-over work. On Claude
  Code the worker would lose `AGENTS.md` (about 800 tokens) and the hub on
  each call: an estimated 5 to 10% of the worker's share, in one task type,
  against a run-to-run spread of about 20%. It was not measured there.
- It has a standing cost: three rules live in two places and can drift, and
  a thin task file costs a correction round.
- What it gives is isolation (one input for the worker), which the runs
  showed to work but not to matter.

**What would change this.** Two things together: a harness-level opt-out on
OpenCode, and a measurement on a project with a long notes hub and a small
worker model that shows fewer correction rounds or lower cost with the cold
worker than without. The fair first test is the benchmark on Claude Code,
12.30 against the cold worker, two runs each.

## 95. The best-practice review of 12.14: what it changed, what came out, and its sources (2026-11-15, v14.0)

14.0 changes no behavior. It closes the review cycle that ran from 12.15 to
12.30 and records it in one place, with the sources, so the review can be
repeated and compared against this one. The version number marks the end of
the cycle; there is no 13.

**What was reviewed.** Framework 12.14 (tag `bravo`) against the published
practice for coding agents as of 2026-11-14, on four questions: token cost,
persistent project memory, stable sub-agent use, speed. Claude Code and
OpenCode; Copilot was left out on purpose.

**Method.** A fresh 12.14 scaffold per harness was measured (words per
artifact, what is loaded when) and compared with the harness documentation
and the studies listed under Sources. Every harness fact was then checked
live before it went into a template (Claude Code 2.1.325, OpenCode 2.2.5).
Each batch was built on a branch, run live on both harnesses and judged from
files and transcripts.

**What already matched and was left alone.** Short requirements-only
instructions; nothing loaded until needed; the model of a role set in its
agent file, not by prompt text; judging from files, not summaries; hooks for
hard rules; no generated codebase summary; the task file as the hand-over
between sessions.

**Key changes** (the section in brackets has the detail):

- The worker reads only its own steps, not the supervisor's protocol:
  `steps.md` split from `do.md` (77).
- A turn limit on every sub-agent (78).
- Roles enforced by tools, not by text: the worker cannot spawn agents, the
  reviewer's shell is limited to read commands (79).
- One memory on Claude Code: auto memory off in the project settings (80).
- `AGENTS.md` loads on Claude Code in every case: a script writes the
  `@AGENTS.md` import (81).
- A freshness check for the notes: hub size, dead paths, broken and
  unlinked leaves (82).
- The notes hub is in context at session start, on Claude Code through a
  `SessionStart` hook and on OpenCode through `instructions` (83, 86). This
  is the one change that grew the always-loaded part; Property 4 argues it.
- Script output without a model round trip in `/framework-models` (84).
- The worker's contract is the body of its agent file (85).
- A re-init keeps the keys a user added to `opencode.json` (88).
- Path-scoped notes leaves on Claude Code (89).
- The end of a task in one call, the start in fewer calls, the supervision
  text loaded only by a session that supervises, a shorter dispatcher (90
  to 93).

**Considered and not built.** A lower effort for the updater (87: risk of a
subtle bad merge, saving unmeasured). Compaction settings for OpenCode
(README only, until a real session shows the default hurting). A cold worker
(94: built, worked, no measurable saving, dropped). Agent teams (about seven
times the tokens by the vendor's own cost page). Sub-agent `memory:` (a
third memory). `isolation: worktree` (`.ai` is a gitignored nested repo, so a
worktree would hold neither tasks nor notes). Output-compression layers
(token reduction and billed cost correlate weakly, arXiv 2607.12161).

**Outcome, measured.** The harness benchmark (`tests/harness-benchmark.md`:
satty, nine fresh sessions per run, OpenCode 2.2.5, mid-tier supervisor and
reviewer, small worker, every role at medium effort). Three versions carry a
git tag so each can be scaffolded again:

| Tag | Version | Runs | Grader, of 6 | Cache-read tokens per run |
|---|---|---|---|---|
| `alpha` | 11.6 | 5 | not re-graded here | 2.64M to 3.05M, median 2.76M |
| `bravo` | 12.14 | 2 | 5, 6 | 3.06M, 3.20M |
| (untagged) | 12.26 | 2 | 5, 6 | 3.45M, 3.62M |
| `charlie` | 12.30 | 2 | 6, 6 | 2.60M, 2.57M |

- The review's first three batches (12.15 to 12.26) made a run about 12%
  more expensive in cache reads than 12.14, not cheaper: the hub in context
  and the longer `do.md` are re-read on every model call. A session starts
  at about 17,400 tokens, `do.md` added about 8,000, a task session makes 11
  to 17 model calls, and closing a task took 4 to 5 of them.
- 12.27 to 12.30 attacked the number of calls and what a session loads. Both
  12.30 runs read less from cache than every run of 12.14 and of 12.26, and
  had the shortest session time (316 s, 310 s). Against 12.14 that is about
  17% fewer cache-read tokens.
- Cache-write tokens (235k to 306k) and output tokens (about 41k) did not
  move, so the billed saving is smaller than the cache-read figure. No
  dollar figure was computed.
- Limits: two runs per version from 12.14 on, one harness, one project, one
  model profile. The decision rule of the benchmark (every run of one arm
  beats every run of the other) is met for 12.30 against 12.14 and 12.26.
  Against 11.6 it is met by a hair (2.60M against 2.64M), which is no
  finding: 12.30 does far more than 11.6 for about the same cost.
- This does not touch Property 4: a session with the framework still costs
  more than one without. What changed is the framework's cost against its
  own earlier versions.
- `alpha` is not an ancestor of `main`. `main` was rebased on 2026-11-09 and
  its commits were renumbered; the tag points at the tree that ran, whose
  stamp reads 11.6.

**Not covered live.** A run that hits its turn limit; the reviewer inside a
real review gate; whether `MEMORY.md` stops loading with auto memory off; a
path-scoped leaf loading on an edit, not a read; `/framework-update`
carrying 12.20 to 12.30 into an older project; the 12.27 to 12.30 forms on
Claude Code and Copilot; whether OpenCode sub-agents receive `instructions`.

**Harness facts the changes rest on.** Check each again before the next
review; a changed one is a finding.

- Claude Code: sub-agent frontmatter takes `maxTurns`, `disallowedTools`,
  `hooks`, `omitClaudeMd`, `effort`, `model`. Frontmatter hooks need
  workspace trust and do not run in headless `-p`. `AGENTS.md` is read
  natively only when no `CLAUDE.md` exists in the directory or above;
  otherwise through an `@AGENTS.md` import, without loading twice.
  `autoMemoryEnabled: false` in project settings turns auto memory off.
  `SessionStart` hook output enters context (matchers `startup`, `resume`,
  `clear`, `compact`; 10,000 characters) and does not run for sub-agents. A
  skill's `` !`cmd` `` injection runs before the model sees the skill; a
  failing command aborts it. `.claude/rules/` files with `paths:` load on a
  read of a matching file, also through a symlink, when gitignored, and in
  sub-agents.
- OpenCode: agents take `steps` and ordered `permissions` rules (last match
  wins). `experimental.subagent_depth` defaults to 1. `instructions` in
  `opencode.json` loads extra files, relative to the project root, with no
  cap and no per-agent opt-out. Command templates support `` !`cmd` ``.
  `opencode run "/command"` does not dispatch slash commands. The
  background service keeps the agent files it read first.

**Sources**, as read on 2026-11-14. Parts of the Claude Code pages came back
truncated; what rested on them was verified live.

- Claude Code best practices: https://code.claude.com/docs/en/best-practices
- Claude Code costs: https://code.claude.com/docs/en/costs
- Claude Code sub-agents: https://code.claude.com/docs/en/sub-agents
- Claude Code memory: https://code.claude.com/docs/en/memory
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- OpenCode V2 agents: https://opencode.ai/v2/agents.md
- OpenCode config: https://opencode.ai/docs/config/
- Token Reduction Is Not Cost Reduction, arXiv 2607.12161:
  https://arxiv.org/abs/2607.12161
- Do Context Files Help Coding Agents?, arXiv 2607.27250:
  https://arxiv.org/abs/2607.27250
- AGENTS.md files, a 138-repo study:
  https://dev.to/umesh_malik/agentsmd-files-dont-work-the-way-you-think-a-138-repo-study-proves-it-2k1g
- AGENTS.md efficiency study, ICSE 2026 workshop:
  https://codex.danielvaughan.com/2026/08/07/agents-md-efficiency-impact-icse-2026-jaws-codex-cli-token-savings-runtime-reduction/
- Sub-agent model selection by prompt text, issue 34480:
  https://claudeissues.com/issue/34480-bug-the-dispatching-model-has-no-reliable-mechanism-to-enforce-subagent-model-se
- Model selection for agents:
  https://ctxt-dev-35d.pages.dev/posts/en/model-selection-agents
- Multi-agent pipeline postmortem:
  https://dev.to/dibi8/multi-agent-pipeline-postmortem-5-ways-subagent-orchestration-goes-wrong-2026-i0e

Coding-agent skills evaluated later (2026-11-25, section 97). Read them again
with the rest; a new version or benchmark of either reopens section 97.

- ponytail, "the laziest senior dev in the room" (adopted as one AGENTS.md
  line): https://github.com/DietrichGebert/ponytail, its SKILL.md
  https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md
- The critique that a plain YAGNI line nearly matches ponytail's benchmark:
  https://dev.to/yashddesai/ponytail-the-ai-coding-skill-taking-github-by-storm-and-the-one-question-nobodys-answered-yet-46mc
- i-have-adhd, ADHD-friendly output (evaluated, left out):
  https://github.com/ayghri/i-have-adhd, its SKILL.md
  https://github.com/ayghri/i-have-adhd/blob/main/skills/i-have-adhd/SKILL.md;
  the decision-budget variant https://github.com/alexh/i-really-have-adhd

**Repeating the review.**

1. Scaffold the current version per harness into a temp directory and
   measure it: words per artifact, what is always loaded, what each role
   reads at its start.
2. Read every source above again, and search for what has appeared since
   2026-11-14 on the same four questions. Note each difference from this
   section: a new frontmatter field, a changed default, a new loading rule,
   a study that contradicts one cited here.
3. Check the harness facts above live on the current CLI versions.
4. Sort what differs into: already matches, change, leave out, each with
   its reason. A change that adds always-loaded text is argued in Part I
   first.
5. Prove a cost claim with the benchmark against `charlie`, the same
   profile, at least two runs per arm, and judge by its decision rule.
6. Append the result as a new section that names this one, and tag the
   versions compared.

## 96. A sub-agent that runs in the background (2026-11-15, v14.1)

**What changed outside.** OpenCode 2.3.0 (2026-11-13) runs every sub-agent
in the background. Its release notes: "Subagents now always run in the
background, return their session ID immediately, and report results to
their parent whenever they become idle." Until 2.2.7 the spawn call returned
the sub-agent's report.

**Seen** (OpenCode 2.3.0 beside an untouched 2.2.5, framework 14.0, the
harness benchmark):

- `init-agent --models` passed unchanged: `opencode run` waits for the
  background sub-agent, and the sub-agent's session named the model of its
  agent file.
- The supervisor of a worker task spawned the worker, got a session id, said
  "the worker is still running" and ended its turn. When the report came, it
  woke by itself and judged it. Nothing in `supervise.md` told it to; it read
  the situation correctly.
- The benchmark driver did not. It took the idle session for a finished
  turn, sent its fixed reply twice and started the next task after 20
  seconds, while the worker still ran. The next task claimed `README.md`,
  the worker was refused with `CLAIMED` (section 51 working as built), and
  the task stayed `in-progress`: 5 of 6.
- The same task alone, with a driver that waits: `done` in 85 s, no nudge.

**Changes.**

- `supervise.md`: a spawn that returns before the worker has finished is
  not a report. Say in one line that the worker runs, end the turn, judge
  when the report arrives; no second worker meanwhile.
- `do.md`, the review gate: when the spawn returns before the reviewer has
  finished, wait for its verdict.
- `/framework-update`, the hand-over: wait for the updater's last line
  before checking anything.
- The wording names no harness: it describes what the session sees, and is
  inert where the spawn returns the report.
- `tests/harness-bench/drive.py`: a turn is over only when no sub-agent of
  the run is busy (OpenCode's `/api/session`, child sessions whose `busy`
  time is later than their `idle` time). `drive.py` and `metrics.py` take
  the binary from `OPENCODE_BIN` when it is set.
- README: OpenCode support names 2.3.0 and says the session ends its turn
  while a sub-agent runs.

**Live, framework 14.1, same benchmark profile, one run each.**

| | Grader | Nudges | Cache read | Session time |
|---|---|---|---|---|
| OpenCode 2.3.0 | 6 of 6 | 0 | 2.64M | 322 s |
| Claude Code 2.1.325 | 6 of 6 | 0 | 5.38M | 487 s |

- OpenCode: the worker task ran worker, then `reviewer` sub-agent, then
  `done`, both in the background. 12.30 on 2.2.5 read 2.60M and 2.57M; one
  run does not show a difference.
- Claude Code: the first live run of the one-call `finish`, the task file
  printed by `resolve`, `supervise.md` and the shorter dispatcher (sections
  90 to 93) on that harness, which section 95 listed as not covered. The
  three 11.6 runs on Claude Code read 4.55M, 6.58M and 5.89M; one run inside
  that range is no cost claim.
- A first run on the upgraded install halted before any task: the TUI had
  not come up in the pane right after the upgrade. Started again, it ran.

**Not covered.** The updater as a background sub-agent. A user typing into
the session while the worker runs. Copilot.

## 97. The smallest complete change, and two skills evaluated (2026-11-25, v14.2)

**Source.** The owner asked how two popular coding-agent skills would affect
the framework's speed, quality and token cost: ponytail
(DietrichGebert/ponytail, 592 words) and i-have-adhd (ayghri/i-have-adhd,
1,242 words). Both SKILL.md files were read as published on 2026-11-25 and
compared with the 14.1 templates. Their sources are listed with section 95's,
so a later review reads them again.

**ponytail.** A ladder before any new code: not needed at all, already in
the codebase, standard library or platform, an installed dependency, one
line, then the minimum that works; never cut trust-boundary validation,
data-loss handling, security or accessibility; finish every caller the
change breaks. Its README reports, on Haiku 4.5 with twelve tickets and four
runs each, 54% fewer lines, 22% fewer tokens, 20% lower cost and 27% less
time than no skill. A published critique found that one plain line ("Follow
YAGNI principles, and prefer one-liner solutions") nearly matched that
benchmark: most of the effect is the instruction, not the 592 words.

- Already in the framework, on the `/task` path only: the smallest way that
  meets the steps (`work.md`, section 66), the smallest option
  (`supervise.md`), the sibling to copy (`create.md`, section 73). The
  direct path, which carries most tasks, had no such rule.
- Not taken: its closing lines on what was skipped (the run already ends
  with Blocked on me, Changed, Found), `shortcut:` comments in the code
  (durable knowledge goes to `.ai/notes.md`), an assert-based self-check in
  place of a test that stays in the suite (section 72), and the "ultra"
  level that questions the request (an answered question stays settled).
- Seen in this framework's own benchmark (section 75): GPT-6 Luna added a
  `TypeError` for non-string input nobody asked for, the kind of extra the
  ladder removes.

**Change.** AGENTS.md's Right-sizing paragraph, after "check it per rule
2": "Make the smallest complete change: reuse what the code, the standard
library or an installed dependency already has; add no option, abstraction
or dependency nobody asked for; finish every caller the change breaks and
the tests rule 2 asks for." It costs 40 words in every session's cached
prefix. That puts Copilot's AGENTS.md at 728 words, so the tripwire moves
from 700 to 730 (Property 4): the number guards against a digest, and a
rule stated whole beats one cut to fit. Part I's default path names the
rule. The tests clause was added after the first live run (below).

**i-have-adhd.** Shapes every answer for a reader with ADHD: the next
action first, numbered steps, state restated each turn, no tangents, lists
of at most five, concrete time estimates, no preamble, recap or closing
pleasantry. Left out of the framework:

- It shapes how answers read to one user; generated projects serve every
  user and stay neutral. Code, tests, task files and worker reports are
  unaffected, so it changes neither the agent's speed nor the result.
- Cost: about 1,700 tokens in context per session it is active (cached),
  against shorter answers; output is about 1% of a session's tokens, so the
  net is near zero.
- Conflicts: its "no recap" rule meets the required Changed heading, and its
  own rule ranks the system prompt above it, so which wins is unstable; its
  per-turn state restatement repeats what the task file holds; its time
  estimates are guesses an agent cannot ground; a variant that applies to
  every message would reach worker reports and their fixed `Worker round`
  line.
- Worth knowing, not adopted: the first-and-last-line check (read only
  those two, and the reader knows what happened and what to do next), and
  the debug-spiral rule (after three "still broken" turns, stop editing,
  name the assumption that may be wrong, ask one diagnostic question).
  A user who wants the style installs the skill for themselves.

**Run live: 14.1 against 14.2** (2026-11-25, Claude Code 2.1.311 headless,
`claude -p`, Claude Haiku 5.5, the direct path, scratch stdlib project with
a `parse_quantity`/`to_kg` helper to reuse; each run scored by hidden checks
and its host diff).

| Task, arm | Runs | Hidden checks | Median s | Turns | Cost $ | Out tok | Code lines | Runs with a test |
|---|---|---|---|---|---|---|---|---|
| weights, 14.1 | 4 | 6/6 all | 37.5 | 16 | .0089 | 7,310 | 18 | 4 |
| weights, 14.2 first wording | 4 | 6/6 all | 33.5 | 18 | .0092 | 6,554 | 17.5 | 4 |
| CSV export, 14.1 | 12 | 5/5 all | 25 | 13 | .0061 | 4,015 | 14 | 12 |
| CSV export, 14.2 first wording | 6 | 5/5 all | 23.5 | 10.5 | .0058 | 3,604 | 14 | **4** |
| CSV export, 14.2 final wording | 6 | 5/5 all | 22.5 | 12 | .0058 | 3,814 | 14 | 6 |

- No arm over-engineered: no new class, option, file or dependency in any
  of the 32 runs; every run reused the helper or `csv`. On these tasks
  Haiku 5.5 under 14.1 already writes the minimal change, so the rule had
  nothing to remove; the size effect the skill's benchmark reports is not
  reproduced here, and not refuted.
- The first wording made two of six CSV runs skip the test for the new
  logic ("add nothing nobody asked for" read as license). The skill itself
  guards this ("lazy code without its check is unfinished"); the final
  wording adds "and the tests rule 2 asks for", and six of six wrote one.
- Speed and cost moved a little in 14.2's favour (CSV final: 22.5 s against
  25 s, $0.0058 against $0.0061, paired in time with 14.1 runs 7 to 12);
  within run-to-run spread, no claim.
- Verdict: the rule costs nothing measurable and lost nothing once the
  tests clause was in; its benefit needs a task or model that over-builds.
  Not covered: Copilot, OpenCode, the `/task` path (which had the rule
  already), larger models.

## 98. The work runs on what create settled (2026-11-26, v14.3)

**Source.** The owner felt `/task do` came back to them too often, and asked
whether the task file was not enough for the supervisor and worker to run
on their own. Every point where a `/task do` session stopped for the user
was extracted from the six projects' transcripts (Claude Code) and session
exports (OpenCode): 269 stops holding 543 questions, 486 on Claude Code, 57
on OpenCode. A sub-agent classified each question without being told the
expected answer.

| Kind | Questions | Share |
|---|---|---|
| Spec gap: what proves a criterion, behavior and edge cases, test environment, scope, content, access, naming | 251 | 46% |
| Routine outward action: push, pull request, comment, issue edit, CI rerun | 119 | 22% |
| Risky: merge, production, deleting data, force-push | 43 | 8% |
| Offer of extra work ("should I also", a follow-up task, the next phase) | 39 | 7% |
| Process, a check by hand, a wait, other | 91 | 17% |

- 190 of the 543 (35%) re-asked a decision already asked: an open question
  stayed in the closing Blocked on me list and came back every turn (one
  criterion question in 23 turns, one upload question in 18).
- Claude Code asked 340 questions as text and 146 in a dialog; OpenCode 54
  of 57 in its `question` dialog.
- The worker asked 69 times across 134 task files; the supervisor answered
  39 itself. The stops came from the supervisor.
- One project held 416 of the 543, one session 138.
- The largest spec themes, each settleable by one question while planning:
  what proves a criterion and what to do when it cannot be produced here
  (45), behavior and edge cases (52), the test environment and the writes
  allowed there (33), the scope (22).

**Change.**

- `create.md`: for a `change`, `bug` or `test`, the one dialog also asks
  what would otherwise stop the work: the evidence per criterion and its
  fallback (defer, reword, block), where it is proven, the scope, the
  outward actions allowed without asking (recommended: push the task's
  branch, open and update its pull request, comment on it and the issue,
  rerun its CI; never a merge into the default branch, production,
  deleting data or a force-push), and open decisions found in the code,
  each with the recommended answer first. Each command a criterion names
  is run once while planning. The answers go into `## Autonomy`.
- `supervise.md`: a reversible choice inside the Autonomy section is the
  supervisor's to decide and report as made; it asks only a changed Goal or
  criterion, an irreversible choice, or an action the section does not
  list. Each question is asked once (`Pending:` in Findings) and not
  repeated. No extra work is offered. What the user could check by
  looking, it reads itself first.
- `steps.md` (worker and inline session): `Decision:` lines for reversible
  choices, reported as made; listed outward actions need no question; no
  extra work and no offer, an out-of-scope defect is one `Out of scope:`
  line; a question goes out once.
- `work.md`: an action the Autonomy section lists is not a `question`.
- The owner ruled out offers of extra work outright, a collected list of
  them included: they add work nobody asked for.

**Run live: 14.2 against 14.3** (2026-11-25, Claude Code 2.1.311 headless,
`claude -p`, Claude Haiku 5.5 as supervisor, worker and reviewer, the
stdlib inventory project with a local `origin`; `/task create` then `/task
do`, each run scored by hidden checks).

- An easy task (CSV export, push to origin), six runs per arm: both
  reached `done` where create wrote a plan, 5 of 5 checks each; 14.2 handed
  open points back in its closing message (branch name, header, tracker),
  14.3 recorded `Decision:` lines instead. Two runs per arm stopped in
  create to ask, which a headless run cannot answer, and one 14.3 run hit a
  permission the harness denied; neither is a difference between the
  versions.
- A hard task, the same plus a criterion that cannot be proven here (a
  staging host that does not resolve), with "no one is available to answer"
  in the prompt, every shell command allowed, six runs per arm:

| | 14.2 | 14.3 |
|---|---|---|
| Hidden checks | 6 of 6 | 6 of 6 |
| Branch pushed | 5 of 6 | 6 of 6 |
| Clean end (`blocked` with the reason, or the criterion deferred and stated) | 3 of 6 | 5 of 6 |
| Questions back to the user at the end | 2, plus 1 asking to confirm | 2, plus 2 asking to confirm |
| `Decision:` lines | 0 | 2 |
| Median time, cost | 52 s, $0.046 | 70 s, $0.044 |

- A first 14.3 round had two hand-backs from criteria whose command did not
  work here (a test command needing `tests/__init__.py`, a linter not
  installed); running each criterion's command once while planning removed
  both. The requests to confirm a decision led to "report it as made, never
  as a question to confirm", added after the runs and not rerun.
- In one 14.3 run, create, told no one could answer, wrote the unprovable
  criterion as deferred and the run closed `done` with that stated in
  Notes and Outcome: the brief's fallback, which an interactive create
  asks.
- Verdict: no loss, a cleaner end, every push made. Fewer questions to the
  user is not shown: a headless run is one turn, so the three largest
  levers of the analysis, the repeats across turns (35%), the outward
  approvals during the work (22%) and create's own questions, cannot occur
  in it. The test of 14.3 is the same extraction over the owner's sessions
  after some use, against the numbers above.

## 99. Compaction left to the user's setup (2026-11-26)

**Source.** Section 88 had the README advise OpenCode's `compaction` block
per project (`keep.tokens`, `buffer`) and used `compaction` as the example of
a user key a re-init keeps. The owner decided compaction is not the
framework's: it belongs to each user's harness setup, not to a scaffold.

**Seen, OpenCode 2.4.2.** The summary prompt can be steered after all, which
section 88's docs did not show: an undocumented plugin hook,
`ctx.session.hook("compaction", req => ...)`, gets the summary request, and
text added to `req.system[0]` reaches the summary (appended as a part of its
own it did not, with the Copilot GPT models). The owner's setup agent built a
plugin on it that applies the same policy as the owner's Claude Code
PreCompact hook, plus `compaction.keep.tokens: 100000`, in the owner's
OpenCode setup repository; a compaction in a scratch session then kept the
user's rule verbatim, put a file in as a pointer, and ended with the line
naming `opencode session export <id>`.

**Removed.** The README's "Long sessions" paragraph. The re-init keeps
every key a user adds to `.opencode/opencode.json`, a `compaction` block
included, as before (section 88); its examples now name a model, MCP servers
and sharing. Nothing in a scaffold changes, so no version bump.
