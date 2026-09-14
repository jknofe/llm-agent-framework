# llm-agent-framework

Two pillars, one command set on any supported harness (Claude Code,
Copilot, Hermes):

1. **Durable project knowledge that the repository cannot state itself.**
   `.ai/notes.md` (decisions and why, gotchas, unwritten rules, runbooks) as
   private memory across sessions, plus a short requirements block in
   `AGENTS.md` holding the commands this project is checked with and the
   tools it requires or forbids.
2. **An opt-in spec-and-build path.** `/spec` writes down what the agent
   intends before any code exists, so you can redirect it; `/build`
   implements it and reviews the diff against the criteria. You start both.
   By default the agent just does the task.

Concept: CONCEPT.md.

What the benchmarks support and what they do not (`benchmarks/`, CONCEPT.md
sections 36 to 38). A spec-and-review chain on every task costs two to three
times a bare agent and did not make later tasks on the same repo cheaper or
more correct with Sonnet 5, so 6.1 made it opt-in. An always-loaded
repository overview does not help agents find anything (ETH Zurich
evaluation of context files, measured on repos from django to 12 niche
ones), so 6.0 stopped emitting one and 7.0 stopped writing one anywhere.
What does measure: naming a required tool causes it to be used, and the
notes carry real gotchas between sessions for almost nothing.

**This framework does not make a session cheaper.** Every round measured
more tokens, by design. It is economical about its own text (`AGENTS.md`
under 500 words, everything else read on demand), which is a different
claim. Untested: weak models, projects dense in non-derivable context, and
sessions where a human answers the questions.

Framework 7.0 cut `/tidy-up`, `/import-kb`, `/import-agent` and the
generated module map; 5.22 removed the large (knowledge-base) profile. See
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
description, claude/copilot/hermes); Enter accepts the defaults. If a
scaffold already exists it asks before regenerating framework files
(instructions, skills, hooks, settings); hand-filled notes and specs are
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
never rebuilt: `notes.md`, change specs, and the generated project-context
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

**Switching harness** (say claude to hermes) is not an update either: the
entry files are pure framework output with nothing to merge, so the CLI does
it. Run `init-agent --harness hermes` in the project. It writes the new
command set, then retires the old one: every file the version stamp recorded
for the previous harness is **moved** to
`.ai/agent/.harness-backup/<old-harness>/`, never deleted, and directories it
empties are removed. Files it did not record are yours, so a skill you added
next to the framework's stays where it is and is reported. Notes, change
specs and the generated project-context section are preserved as in any
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
2. **Work**: ask for what you want. The agent reads what it needs, makes
   the change, runs the project's full test and lint commands, notes
   anything durable in `.ai/notes.md` and commits `.ai`. This is the default
   path for every task.
3. **Opt in to a spec** when you want a change written down and reviewed:
   `/spec FEAT-42 Add a jazzy build` writes `.ai/changes/FEAT-42/spec.md`
   (goal, acceptance criteria, task checklist); `/build FEAT-42` works the
   checklist and ends with a fresh-context review of the full diff against
   the criteria (the `reviewer` subagent where the harness has one). The
   agent never starts a spec on its own.
4. **Archive**: just ask the agent ("archive FEAT-42"). It verifies
   `status: done` and moves the change to `.ai/changes/_archive/`.

The framework is model-agnostic: it never tells the harness which model to
run, you decide via the harness (for example `/model opusplan` in Claude
Code to plan on Opus and implement on Sonnet). The self-contained spec and
the fresh-context review gate are what keep cheap execution safe. If you do
split models, keep the direction: spec on the strong one.

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
  topic leaves under `notes/`, and per-change specs under
  `changes/<id>/spec.md`.
- **Four skills**, listed under [Skills](#skills).
- **Kept from the framework machinery:** the `reviewer` subagent, the
  `.ai`-clean Stop hook, the read-only permission allow list, and `probe.py`
  (command and documentation detection).

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
the gotchas and decisions into `notes.md`, and any in-flight change into
`changes/<id>/spec.md`. Framework 7.0 dropped the `/import-agent` skill that
used to script this; with the scaffold at six files it is a plain request.

## Skills

`init` scaffolds the workflow as Agent Skills, the open SKILL.md standard
read by Claude Code and a growing set of other harnesses
(`.claude/skills/<name>/SKILL.md`); the hermes harness gets the same
bodies as project skills (`.agents/skills/<name>/SKILL.md`) and the copilot
harness as VS Code prompt files (`.github/prompts/*.prompt.md`). On claude
the skills carry `disable-model-invocation: true`: they are pipeline steps
with side effects (notes writes, code changes, `.ai` commits), so only an
explicit `/name` from you triggers them, never the model mid-conversation.
All three harnesses invoke them the same way, under the same names:

| Command | What it does |
|---|---|
| `/explore [focus]` | Detects the build/test/lint commands, asks you what the code cannot tell it, writes the answers into the AGENTS.md requirements section and `notes.md`. Optional free-text focus. |
| `/spec <id> <title...>` | Opt-in. Writes `.ai/changes/<id>/spec.md` for a change you want specified: goal, acceptance criteria (always including the full suite green), task checklist. No implementation yet. |
| `/build <id>` | Opt-in. Works that spec's task checklist, then one fresh-context review of the full diff against the acceptance criteria. |
| `/framework-update [dry-run]` | Moves the scaffold to the current framework version: merges the framework files, retires what the framework dropped, migrates hand-filled content into the new shape. Never re-explores. |

Every skill body is self-contained; there is no phase-doc layer to follow.
Archiving has no command: prompt the agent; the rules live in AGENTS.md.

### Autonomous dispatch with Claude Code's `/goal`

Not part of the framework, but the way to run one of these unattended.
`/goal` changes only whether the agent stops to ask between steps, so use it
when the finish line is machine-checkable and no judgment call is expected.
Point the condition at the artifact that defines done (the gate command, or
for a spec'd change its acceptance criteria), make the agent show it in
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
section). For Claude Code, init also writes a one-line `CLAUDE.md` that
imports it via `@AGENTS.md`; Copilot (VS Code and CLI) and Hermes read
`AGENTS.md` natively, so no extra file is needed there.

## Deterministic tools and hooks

Protocol rules that can be enforced mechanically are not left to model
obedience:

- `.ai/agent/tools/probe.py` prints the build/test/lint commands it can
  detect, the dependency manifests, and the documentation the repo already
  has. The agent runs it first in `/explore` as a starting point for the
  questions; your answers override it. It deliberately prints no module map
  or LOC table: that is a repository overview, and an overview does not help
  an agent find anything.
- `.claude/hooks/ai_repo_clean.py` (Stop) blocks ending a turn while the
  `.ai` repo has uncommitted changes, so notes and specs are not silently
  dropped. Not absolute: Claude Code overrides a Stop hook after repeated
  consecutive blocks, so the protocol rule in `AGENTS.md` remains the
  backstop.
- `.claude/agents/reviewer.md` defines the fresh-context adversarial
  reviewer used by `/build`'s review gate.

During `/explore` the agent additionally offers a project-specific Stop hook
that runs your lint/tests, turning "done = checks pass" into a hard gate.
Hooks and the reviewer subagent are scaffolded for the claude harness;
Copilot and Hermes have no equivalent mechanism, there the rules stay
protocol text.

These hooks only fire when the scaffolded repo is the **active Claude Code
project directory**. Driving the agent from a parent directory, a monorepo
subdir, or a sub-agent means the hooks do not run (`$CLAUDE_PROJECT_DIR`
points elsewhere) — in that case the protocol rules in `AGENTS.md` are the
only guarantee, so commit `.ai` by hand and do not assume a hook ran.

## GitHub Copilot support

Choosing `copilot` at the harness prompt targets Copilot instead of Claude
Code:

- instructions file: `AGENTS.md` (read natively, no pointer file)
- prompt files: `.github/prompts/*.prompt.md` instead of skills, invoked
  the same way (`/explore`, `/spec`, ...) in VS Code Copilot Chat;
  arguments are passed as input variables, e.g. `/spec: ticket=FEAT-42`
- no `.claude/settings.json`, hooks or reviewer subagent (no equivalent)

Prompt files require VS Code with the `chat.promptFiles` setting enabled.
Copilot CLI does not load prompt files; it does read `AGENTS.md`, which
therefore contains the kickoff lines to type instead (also printed at the end
of `init`), e.g.
`Explore the project and fill the project requirements + .ai/notes.md.`

## Hermes support

Choosing `hermes` at the harness prompt targets the Hermes agent:

- instructions file: `AGENTS.md` (read natively, no pointer file)
- project skills: `.agents/skills/<name>/SKILL.md`, the same SKILL.md
  standard and the same bodies as the claude harness, with hermes
  frontmatter (`version`, `platforms`, `metadata.hermes.tags`, and a
  description trimmed to the 60-character cap)
- no `.claude/settings.json`, hooks or reviewer subagent (no equivalent)

Hermes loads project skills only from a repository you have trusted, so run
`hermes skills trust` once in the project root; in a running session
`/reload-skills` picks up edited skills.

Every command carries the same name here as on the other harnesses. One of
them is spelled out rather than shortened, `/framework-update`, because
Hermes reserves `/update` for a built-in command of its own. A name that
collides with a harness built-in is renamed
on **every** harness: a command whose name depends on where you type it is
worse than a longer name that is always right.

Hermes substitutes nothing into a skill: whatever you type after the command
name reaches the agent as your instruction, and the skill says so.

`AGENTS.md` and everything under `.ai/` are identical for all harnesses;
only the entry files differ.

## What init creates

`init` creates `.ai/notes.md` (running memory for gotchas, runbooks and
domain terms), `.ai/changes/` (per-change specs, with `_archive/` for
finished ones), `.ai/agent/tools/probe.py`, the canonical `AGENTS.md`, the
skills above and, for Claude Code, the `CLAUDE.md` pointer, the reviewer
subagent, the Stop hook script and `.claude/settings.json` with that hook
plus a read-only permission allow list (grep, find, ls, cat, awk, read-only
git, `git -C .ai`, `probe.py`) so exploration and `.ai` commits run without a
confirmation prompt per command. Compound commands (`a && b`) only skip the
prompt when every part of the chain is allowed, so common chain members like
`cd`, `echo` and `pwd` are included. If you work interactively, Claude Code's
auto permission mode (a classifier reviews commands and blocks only risky
ones) is a lower-maintenance alternative; the allowlist is what keeps
headless and CI runs deterministic. `AGENTS.md` and `.claude/` /
`.agents/` / `.github/` belong to the host repo.

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

Re-running init never reverts agent or user work: `.ai/notes.md` and specs
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
