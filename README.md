# llm-agent-framework

Two pillars, one command set on any supported harness (Claude Code,
Copilot, OpenCode):

1. **Durable project knowledge that the repository cannot state itself.**
   `.ai/notes.md` (decisions and why, gotchas, unwritten rules, runbooks) as
   private memory across sessions, plus a short requirements block in
   `AGENTS.md` holding the commands this project is checked with and the
   tools it requires or forbids.
2. **An opt-in plan-and-do path for any task.** `/task create` writes down
   what the agent intends before any work is done, so you can redirect it;
   `/task do` works the plan, records findings as they happen, and reviews
   the result against the task's done-when criteria. A task is a code
   change, a bug, an investigation or a test, and each has its own
   definition of done. You start it. By default the agent just does the
   task.

Concept: CONCEPT.md.

What the benchmarks support and what they do not (CONCEPT.md Part II
and sections 36 to 39). A plan-and-review chain on every task costs two to three
times a bare agent and did not make later tasks on the same repo cheaper or
more correct with Sonnet 5, so 6.1 made it opt-in. An always-loaded
repository overview does not help agents find anything (ETH Zurich
evaluation of context files, measured on repos from django to 12 niche
ones), so 6.0 stopped emitting one and 7.0 stopped writing one anywhere.
What does measure: naming a required tool causes it to be used, and the
notes carry real gotchas between sessions for almost nothing.

**This framework does not make a session cheaper.** Every round measured
more tokens, by design. It is economical about its own text (`AGENTS.md`
under 650 words, everything else read on demand), which is a different
claim. Untested: weak models, projects dense in non-derivable context, and
sessions where a human answers the questions.

Framework 8.0 replaced `/spec` and `/build` with the typed task commands;
7.0 cut `/tidy-up`, `/import-kb`, `/import-agent` and the generated module
map; 5.22 removed the large (knowledge-base) profile. See
[One profile](#one-profile).

## Install

```
git clone https://github.com/jknofe/llm-agent-framework.git
cd llm-agent-framework
./install.sh
```

Adds an `init-agent` function to your shell rc (zsh or bash). On every call
it pulls the latest version from git (when a remote is configured) and runs
`init_agent.py`. Re-running `install.sh` is safe; it replaces its own rc
block. Without a checkout: `LLM_AGENT_REPO_URL=<url> bash install.sh` clones
to `~/.llm-agent-framework` first.

## How to use

The CLI has exactly one job: scaffolding. Run `init-agent` (no arguments)
in your project root and answer the prompts (project name, one-line
description, claude/copilot/opencode); Enter accepts the defaults. If a
scaffold already exists it asks before regenerating framework files
(instructions, skills, hooks, settings); hand-filled notes and tasks are
always preserved, never reverted to stubs. `init-agent -h` shows help.
Everything after init is done by the agent through skills and folder
conventions:

**Updating an existing project to a newer framework:** run
`/framework-update` in the project. Updating is a merge, not a regeneration, so the agent does it rather
than the CLI. It reads the scaffold's version stamp
(`.ai/agent/framework.json`), renders a pristine reference scaffold of the
current framework, and then works file by file: adds what is new, takes the
framework's version of files you never touched, **merges** the ones you did
(extra permissions in `.claude/settings.json`, rules you appended to
AGENTS.md), and **deletes** files the framework has retired along with the
instructions that still referenced them. Your knowledge is migrated in place,
never rebuilt: `notes.md`, task files, and the generated project-context
section are carried into the new shape, so `/framework-update` never re-runs
`/explore`. It reports every file it touched and what it kept.
`/framework-update dry-run` prints that report without changing anything.

Before touching anything it commits `.ai` and copies the host-repo framework
files to `.ai/agent/.update-backup/`, so the whole update is revertable. It
commits `.ai` itself and leaves host-repo changes for you to review.

**Scaffolds older than the update skill** (built before framework 5.14) have
none to run. Bootstrap it once with `init-agent --bootstrap-update` in the
project: that writes the skill and a stamp, detects the harness itself, and
touches nothing else. Then run `/framework-update` as above. Do **not** re-run
plain `init-agent` to
update an existing scaffold: it overwrites framework files whole, so it
discards rules you appended to AGENTS.md and permissions you added to
`.claude/settings.json`, and it cannot retire files the framework has
dropped.

A plain re-run of `init-agent` regenerates framework files if you confirm the
overwrite prompt (or pass `-y`), but it cannot merge or retire, which is why
`/framework-update` exists.

**Switching harness** (say claude to copilot) is not an update either: the
entry files are pure framework output with nothing to merge, so the CLI does
it. Run `init-agent --harness copilot` in the project. It writes the new
command set, then retires the old one: every file the version stamp recorded
for the previous harness is **moved** to
`.ai/agent/.harness-backup/<old-harness>/`, never deleted, and directories it
empties are removed. Files it did not record are yours, so a skill you added
next to the framework's stays where it is and is reported. Notes, task
files and the generated project-context section are preserved as in any
re-init, and AGENTS.md is regenerated so it describes the harness you are
actually on. It asks first unless you pass `-y`; a scaffold with no recorded
file list retires nothing and prints what to remove by hand.

1. **Ground the agent**: run `/explore` and answer it. It detects the
   build/test/lint commands as a starting point, then asks you what the code
   cannot tell it (the commands you actually run before pushing, tools to use
   or avoid, unwritten rules, domain terms) and writes those requirements
   into `AGENTS.md`. Your answers are the part that measured positive, so
   letting it run unattended gets you most of the cost and little of the
   benefit.
2. **Work**: ask for what you want. The agent reads what it needs, does it,
   runs the project's full test and lint commands if code changed, notes
   anything durable in `.ai/notes.md` and commits `.ai`. This is the default
   path for every task.
3. **Opt in to a plan** when you want a task written down and reviewed:
   `/task create BUG-7 Nav goal lost after reboot` asks you for its type
   (`change`, `bug`, `investigation`, `test`) unless you named it, and
   whether a tracker issue (GitHub, Jira) exists for it: a fetched issue
   feeds the plan and its key prefixes the task id
   (`12345-fix-ci-crash`); declining leaves an ordinary issueless task.
   It writes `.ai/tasks/BUG-7/task.md` (goal, done-when criteria for that
   type, steps; for bugs and investigations the steps are hypotheses with a
   check each). `/task BUG-7 ...` without `create` or `do` works too: a
   script checks whether BUG-7 exists and picks create or do, and asks
   first if a similar id is already there. An investigation is planned and
   worked in one go, with no questions after the type. Anything else waits
   for you: in a fresh session, `/task do BUG-7` works it, appends findings with their evidence
   as they happen, re-plans in the file when a hypothesis dies, and ends
   with a fresh-context review (the `reviewer` subagent where the harness
   has one): a diff against the criteria, an outcome against its evidence.
   The work itself, through to the pull request, goes to a cheaper-model
   worker, a sub-agent of the harness that starts fresh from the task
   file; the session you talk to reviews, answers and decides for you (see
   [Supervised workers](#supervised-workers)). `/task do BUG-7 inline`
   keeps the work in your session.
   Findings the repository cannot state go into `notes.md`. The agent never
   starts a task plan on its own.
4. **See where things stand**: `/task list` prints every live task as
   one table (type, status, steps and criteria checked, last update),
   read-only, and flags stale, blocked and half-done tasks below it.
   `/task tree` prints the same tasks as a dependency tree, built from
   the optional `depends:` frontmatter line: a task that blocks others
   is the root and what waits on it nests below. A script produces all
   of it; to skip the model entirely, run
   `python3 .ai/agent/tools/tasks.py` in a shell (in Claude Code:
   `! python3 .ai/agent/tools/tasks.py`). Archived tasks are only counted.
5. **Archive**: just ask the agent ("archive BUG-7"). It verifies
   `status: done` and moves the task to `.ai/tasks/_archive/`.

What counts as done, by type:

| `type` | Done when |
|---|---|
| `change` | your criteria, plus the full test and lint suite green |
| `bug` | root cause with evidence; a reproduction that fails before the fix and passes after; suite green (or, cause only, a write-up someone can act on) |
| `investigation` | the question answered with every claim citing evidence, or "inconclusive" naming what was ruled out; covers research |
| `test` | every named scenario run and its result recorded; new tests pass with the full suite |

The framework is model-agnostic: it never tells the harness which model to
run, you decide via the harness (for example `/model opusplan` in Claude
Code to plan on Opus and implement on Sonnet). The self-contained task file
and the fresh-context review gate are what keep cheap execution safe. If you
do split models, keep the direction: `/task create` on the strong one.

## One profile

Framework 5.22 removed the large profile. What is left is what used to be the
small one, and it is now the only shape the generator emits:

- **AGENTS.md** is the canonical, short instructions file: protocol,
  right-sizing rule, workflow table, and a generated project-requirements
  section holding only build/test/lint commands, required or forbidden
  tools, project rules, and pointers to docs the repo already has (cap
  ~300 tokens).
- **`.ai/`** is a private nested git repo (gitignored from the host) holding
  `notes.md` (running memory: decisions, gotchas, domain terms), optional
  topic leaves under `notes/`, and per-task plans under
  `tasks/<id>/task.md`.
- **Five skills**, listed under [Skills](#skills).
- **Kept from the framework machinery:** the `reviewer` subagent, the
  `.ai`-clean Stop hook, the read-only permission allow list, `probe.py`
  (command and documentation detection), `tasks.py` (the task table,
  the create-or-do resolver, and `start`/`tick`/`finish`, the bookkeeping of
  `/task do`).

Gone with the large profile: the `manifest.yaml`/`INDEX.md` knowledge base
with hot/cold tiers and per-task token budgets, drift detection, the
staleness/index tools (`gen_index.py`, `check_stale.py`, `gen_rules.py`), the
on-demand phase docs, the `kb-delta.yaml` patches, the ticket pipeline
(`/add-ticket`, `/plan`, `/implement`, `/add-reference`), and the second
review gate. The agent re-reads the real source instead of maintaining a
synced index of it.

**Existing large-profile scaffolds** cannot be carried across with
`/framework-update`: there is no reference to render for them, so it stops
and says so. Scaffold fresh with `init-agent`, then ask the agent to carry
the old `.ai/` across: the commands and rules into the requirements section,
the gotchas and decisions into `notes.md`, and any in-flight work into
`tasks/<id>/task.md`. Framework 7.0 dropped the `/import-agent` skill that
used to script this; with the scaffold at six files it is a plain request.

## Skills

`init` scaffolds the workflow as Agent Skills, the open SKILL.md standard
read by Claude Code and a growing set of other harnesses
(`.claude/skills/<name>/SKILL.md`); the copilot harness gets the same
bodies as VS Code prompt files (`.github/prompts/*.prompt.md`), the opencode
harness as commands (`.opencode/commands/*.md`). On claude
the skills carry `disable-model-invocation: true`: they are pipeline steps
with side effects (notes writes, code changes, `.ai` commits), so only an
explicit `/name` from you triggers them, never the model mid-conversation.
Every harness invokes them the same way, under the same names:

| Command | What it does |
|---|---|
| `/explore [focus]` | Detects the build/test/lint commands, asks you what the code cannot tell it, writes the answers into the AGENTS.md requirements section and `notes.md`. Optional free-text focus. |
| `/task create <id> <title...>` | Opt-in. Plans a task you name in `.ai/tasks/<id>/task.md`: type (`change`, `bug`, `investigation`, `test`), goal, done-when criteria for that type (any code change includes the full suite green), steps or hypotheses. Asks first whether a tracker issue exists; its content feeds the plan and its key prefixes the task id. A change, bug or test stops there; an investigation runs straight on into `do`. |
| `/task do [<id>] [inline]` | Opt-in. A `worker` sub-agent on a cheaper model works the steps under the session's supervision; a small task (at most one step that edits a file) and `inline` are worked by the session itself. Works that plan, records findings with evidence as they happen, re-plans in the file when a result invalidates it, then one review of the result (diff, outcome, or both) against the done-when criteria, every cited file and line checked. Distills durable findings into `notes.md`. Without an id: the task `.ai/.current` points at. |
| `/task list` | Read-only. Every live task as one table (archived ones are only counted): type, status, steps and criteria checked, last update, the one `.ai/.current` points at, flags for stale, blocked, half-done and unreviewed tasks. The output of `.ai/agent/tools/tasks.py`, shown as printed; run the script directly to skip the model. |
| `/task tree` | Read-only. The same live tasks as an ASCII dependency tree under the project name, built from the optional `depends:` frontmatter line (`tasks.py tree`): tasks that block others stand on the first level, what waits on them nests below, each task appears once at its shallowest position, and tasks with no dependency ties stand on the first level too, after the tasks that block others. Unknown ids and cycles are flagged below the tree. |
| `/task <id> [title...]` | `.ai/agent/tools/tasks.py resolve <id>` decides: an existing, unfinished task is worked, a new id is created, a done or archived one is reported, a similar existing id is asked about. |
| `/framework-update [dry-run]` | Moves the scaffold to the current framework version: merges the framework files, retires what the framework dropped, migrates hand-filled content into the new shape. Never re-explores. |

Every skill body is self-contained; there is no phase-doc layer to follow.
Archiving has no command: prompt the agent; the rules live in AGENTS.md.

### Autonomous dispatch with Claude Code's `/goal`

Not part of the framework, but the way to run one of these unattended.
`/goal` changes only whether the agent stops to ask between steps, so use it
when the finish line is machine-checkable and no judgment call is expected.
Point the condition at the artifact that defines done (the gate command, or
for a planned task its done-when criteria), make the agent show it in
output, and cap the turns:

```
/goal the transcript shows the full test and lint commands exiting 0; or
stop after 20 turns
```

If two consecutive turns make no progress on the same blocker, have it stop
and report rather than make a third blind attempt. This note used to sit in
every scaffold's `AGENTS.md`; 7.0 moved it here, because it is advice about
a harness, not a requirement of your project.

## Instructions file: AGENTS.md

The canonical, vendor-neutral instructions file is `AGENTS.md` (protocol,
right-sizing rule, change layout, generated project-requirements
section). Every harness reads it natively; no `CLAUDE.md` is written.
Claude Code reads `AGENTS.md` since 2.1.277, but only when no `CLAUDE.md`
or `CLAUDE.local.md` exists in the project directory or any directory
above it (a personal `~/.claude/CLAUDE.md` does not count). If you keep a
`CLAUDE.md` in a parent folder, or run Claude Code through Amazon Bedrock
or with telemetry disabled, add a `CLAUDE.md` containing `@AGENTS.md`
yourself, or set the Claude Code project-instructions option to
`claude-md-and-agents-md` in `~/.claude/settings.json`. Scaffolds from 7.0
and earlier carry the pointer; `/framework-update` retires it where it is
safe to.

## Deterministic tools and hooks

Protocol rules that can be enforced mechanically are not left to model
obedience:

- `.ai/agent/tools/probe.py` prints the build/test/lint commands it can
  detect, the dependency manifests, and the documentation the repo already
  has. The agent runs it first in `/explore` as a starting point for the
  questions; your answers override it. It deliberately prints no module map
  or LOC table: that is a repository overview, and an overview does not help
  an agent find anything.
- `ai_repo_clean.py` (turn end) blocks ending a turn while the `.ai` repo
  has uncommitted changes, so notes and task files are not silently dropped. Not
  absolute: every harness overrides a turn-end block after a few consecutive
  passes, so the protocol rule in `AGENTS.md` remains the backstop.
- `git_guard.py` (before a shell command) blocks the two git guardrails at
  the shell: merging into the default branch (`git merge` while on it,
  `git push` targeting it, `gh pr merge`) and any commit whose message, or
  `-F` message file, carries a co-author line. The reason is fed back to the
  agent, which stops at the branch or pull request instead. Only tool calls
  carrying a shell command are inspected; a command the hook cannot parse as
  one of those cases passes.

Both scripts are identical on every harness. Claude Code and Copilot
pipe the same JSON shape (`cwd`, `tool_name`, `tool_input.command`)
to stdin and accept the same `{"decision": "block", "reason": ...}` on
stdout; only where they live and how they are registered differs:

| Harness | Scripts | Registered in |
|---|---|---|
| claude | `.claude/hooks/` | `.claude/settings.json` (`PreToolUse` on `Bash`, `Stop`) |
| opencode | `.opencode/hooks/` | `.opencode/plugins/llm-agent.js`, a small plugin that calls the scripts from `tool.hook("execute.before")` and `session.hook("experimental.idle")` |
| copilot | `.github/hooks/` | `.github/hooks/llm-agent.json` (`preToolUse`, `agentStop`); Copilot CLI, VS Code and the cloud agent read it, the cloud agent from the default branch. Loaded only from a trusted folder: the CLI asks on first interactive start in the repo, and a non-interactive run needs `COPILOT_ALLOW_ALL=true` (exactly `true`) to trust its working directory |

- `reviewer` and `worker` are the two sub-agents of `/task do`: the
  fresh-context adversarial reviewer of its review gate, and the worker that
  does the steps. Their agent files are `.claude/agents/{reviewer,worker}.md`,
  `.opencode/agents/{reviewer,worker}.md` and
  `.github/agents/{reviewer,worker}.agent.md`.

During `/explore` the agent additionally offers a project-specific turn-end
hook that runs your lint/tests, turning "done = checks pass" into a hard
gate. Where the `reviewer` cannot be spawned, `/task do` hands a large result
to a fresh general-purpose sub-agent, and only otherwise reviews it itself,
saying why.

Hooks only fire when the scaffolded repo is the session's working directory
(on claude: the active project directory, `$CLAUDE_PROJECT_DIR`). Driving
the agent from a parent directory, a monorepo subdir, or a sub-agent means
the hooks do not run; in that case the protocol rules in `AGENTS.md` are the
only guarantee, so commit `.ai` by hand and do not assume a hook ran. On
opencode the git guard does run inside a sub-agent.

## Supervised workers

`/task do` runs as two roles, after Google's Elephant-Goldfish Model
(CONCEPT.md sections 50 and 53). The worker is a junior who does the
whole job; the session you talk to is its lead and stands in for you.

- **The worker** is the `worker` sub-agent, on the model its agent file
  pins (a `model:` line you add by hand), else on a cheaper model
  than the session's where the harness lets the agent pick one. A small
  task, where at most one step edits a file, gets no worker: the
  session works it itself and says why. It starts fresh and knows only `notes.md`, the task file and
  `.ai/agent/task/work.md`. It does every step the task names: the code,
  the tests, and after them the branch, commit, push, pull request,
  waiting for CI, dev runs, a tracker comment. Before code ships it asks
  for a review. It reports with a `Worker round <n>` line in Findings:
  `review`, `question`, `stuck` or `done`.
- **The supervisor** answers those reports and does none of the work: it
  reviews the diff before it ships (the `reviewer` sub-agent for a large
  one), answers questions as you would from the task file, and asks you
  only what it cannot decide for you: a changed goal or criterion, a
  merge, production, deleting data. It trusts CI and the evidence in
  Findings, and reruns the tests only when that evidence is missing or
  doubtful. A review finding goes back to the worker as a `Supervisor
  round` line. The Outcome, `notes.md`, the done-when ticks and `finish`
  stay with the supervisor.

After a report the supervisor continues the same worker where the harness
can resume a sub-agent (Claude Code), and spawns a fresh one that reads
the task file otherwise. It works the steps itself only with `/task do
<id> inline`, when it cannot spawn a sub-agent, or when you tell it to
take over. To have the worker run somewhere else, for example in a
terminal pane you can watch, say so when you start `/task do`. The
worker's commits, pushes and pull requests go through the same guards as
yours: the git guard hook blocks a merge into the default branch, and
`AGENTS.md` stops every agent at the branch or pull request. Delegation
is not claimed to be cheaper: reviews and decisions stay on your model.

## Parallel tasks

Two `/task create` or `/task do` sessions can run side by side in the same
project, for example in two terminals, each with its own worker sub-agent
(CONCEPT.md section 51). Nothing to switch on:

- The first running task holds `.ai/.current`; a task started while it
  runs gets `.ai/.current-<id>`, and `tasks.py start` names every task
  already running and the files it has claimed. `/task list` marks all
  running tasks.
- Before editing a file, a task claims it: `python3
  .ai/agent/tools/tasks.py claim <id> <path>...`. A file another running
  task claimed is refused, so two tasks never edit the same file.
- `.ai` commits name their own paths (`git -C .ai add tasks/<id>`), never
  `add -A`, so one session never commits the other's half-written files.

Both tasks still share one working tree: a test run sees the other task's
unfinished edits. Give parallel tasks disjoint files, and expect a
failure in a file the other task claimed to be its business, not yours.

## GitHub Copilot support

Choosing `copilot` at the harness prompt targets Copilot instead of Claude
Code:

- instructions file: `AGENTS.md` (read natively, no pointer file)
- prompt files: `.github/prompts/*.prompt.md` instead of skills, invoked
  the same way (`/explore`, `/task`, ...) in VS Code Copilot Chat;
  arguments are passed as input variables, e.g.
  `/task: ticket=do FEAT-42`
- hooks: `.github/hooks/llm-agent.json` plus the two scripts (see
  [Deterministic tools and hooks](#deterministic-tools-and-hooks))
- `reviewer` and `worker` as custom agents in `.github/agents/` (Copilot CLI
  honors their `model:` line)
- no `.claude/settings.json` (no equivalent); Copilot CLI asks before each
  command and file edit unless you allow tools

Prompt files require VS Code with the `chat.promptFiles` setting enabled.
Copilot CLI does not load prompt files; it does read `AGENTS.md`, which
therefore contains the kickoff lines to type instead (also printed at the end
of `init`), e.g.
`Run task do FEAT-42: read .github/prompts/task.prompt.md and follow it.`

## OpenCode support

Choosing `opencode` at the harness prompt targets OpenCode V2 (written and
tested against 2.2.5; V1 is not supported). The commands work as they do with
Claude Code's slash commands:

- instructions file: `AGENTS.md` (read natively, no pointer file)
- commands: `.opencode/commands/*.md`, invoked the same way (`/explore`,
  `/task do FEAT-42`, `/framework-update dry-run`)
- reviewer: `.opencode/agents/reviewer.md`, a sub-agent that cannot edit
- permissions: `.opencode/opencode.json`, the same read-only list as `shell`
  rules. OpenCode allows by default, so these matter if your global config
  asks about shell commands
- hooks: the two scripts in `.opencode/hooks/`, run by
  `.opencode/plugins/llm-agent.js` (needs `python3`)

Two differences from Claude Code: OpenCode has no per-command `effort`, and a
sub-agent cannot be given a model when it is spawned, so the worker runs on
the session's model unless you add a `model:` line to its agent file. The turn-end `.ai` check uses a hook
OpenCode marks experimental.

## Hermes (dropped in 10.0)

Framework 10.0 no longer renders the Hermes harness. A scaffold built for
it keeps working as it is, but init and `/framework-update` will not
regenerate it. Move it to a supported harness with
`init-agent --harness claude` (or `copilot`, or `opencode`): the switch retires every
`.agents/` file the version stamp recorded into
`.ai/agent/.harness-backup/hermes/` and keeps notes, tasks and the project
context. Init cannot reach outside the repository, so once no project uses
Hermes, remove the `llm-agent-hook` entries from `~/.hermes/config.yaml`
and `~/.hermes/agent-hooks/llm-agent-hook.py` yourself.

The command name `/framework-update` dates from Hermes, which reserves
`/update`. It stays, because renaming a command breaks every existing
project, and a name that collides with a harness built-in is still renamed
on every harness, not only the one that reserves it.

`AGENTS.md` and everything under `.ai/` are identical for all harnesses;
only the entry files differ.

## What init creates

`init` creates `.ai/notes.md` (running memory for gotchas, runbooks and
domain terms), `.ai/tasks/` (per-task plans, with `_archive/` for
finished ones), `.ai/agent/tools/probe.py` and `tasks.py`, the canonical
`AGENTS.md`, the
skills above and, for Claude Code, the reviewer
subagent, the Stop hook script and `.claude/settings.json` with that hook
plus a read-only permission allow list (grep, find, ls, cat, awk, read-only
git, `git -C .ai`, `probe.py`, `tasks.py`) so exploration and `.ai` commits run without a
confirmation prompt per command. Compound commands (`a && b`) only skip the
prompt when every part of the chain is allowed, so common chain members like
`cd`, `echo` and `pwd` are included. If you work interactively, Claude Code's
auto permission mode (a classifier reviews commands and blocks only risky
ones) is a lower-maintenance alternative; the allowlist is what keeps
headless and CI runs deterministic. `AGENTS.md` and `.claude/` /
`.github/` / `.opencode/` belong to the host repo.

The name and description prompted at init are recorded in
`.ai/agent/framework.json`, and the description is also seeded into the
project-context section of `AGENTS.md`, so the agent's first ramp-up starts
from a known project intent instead of discovering it from scratch.
`/explore` verifies and refines it against the code, overwriting that
section, which is why the stamp keeps its own copy: re-running init, switching
harness and `/framework-update` all read the name and description back from there
instead of falling back to the directory name and a blank line. On an existing
scaffold the prompts are pre-filled with them, so Enter keeps the project as
it is.

Re-running init never reverts agent or user work: `.ai/notes.md` and tasks
that differ from their stubs are reported as `preserved`, and an existing
`GENERATED:project-context` section is carried over into the regenerated
`AGENTS.md` (also from legacy `CLAUDE.md` scaffolds).

`.ai/` is versioned in its own git repo (`.ai/.git`) and excluded from the
host project via a `.gitignore` entry written by `init`. `init` makes the
first commit; afterwards the agent commits `.ai` changes itself (a protocol
rule in `AGENTS.md`, enforced by the Stop hook on the claude harness). The
`/framework-update` rescue backup stays out of that repo, as does `.ai/.current`, a
gitignored task cursor (active change id, modified files) the agent reads at
session start to resume work after a break, independent of session
compaction.
