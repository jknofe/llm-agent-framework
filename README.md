# llm-agent-framework

One command set on any supported harness (Claude Code, Copilot, Hermes),
private memory across sessions, and an opt-in spec-and-review path.
`AGENTS.md` is a short requirements file (commands, rules, workflow entry
points), running memory lives in `.ai/notes.md`, and the agent does tasks
directly by default. A change you want written down and reviewed before it
counts as done goes through `/spec` and `/build`, on your request.
Concept: CONCEPT.md.

What the benchmarks support and what they do not (`benchmarks/`,
CONCEPT.md sections 36 and 37): a spec-and-review chain on every task costs
two to three times a bare agent and did not make later tasks on the same
repo cheaper or more correct with Sonnet 5, which is why 6.1 made it
opt-in. An always-loaded repository overview does not help agents (ETH
Zurich evaluation of context files), which is why 6.0 stopped emitting one.
The notes carry real gotchas between sessions and cost little. Untested:
weak models, large repos, and sessions where a human answers the questions.
Framework 5.22 removed the large (knowledge-base) profile; see
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

1. **Ground the agent**: run `/explore`. It runs the deterministic inventory,
   asks you what the code cannot tell it (commands you run before pushing,
   tools to use or avoid, unwritten rules), writes those requirements into
   `AGENTS.md`, and maps the code into `.ai/notes/map.md`, read on demand.
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
  `notes.md` (running memory: decisions, gotchas, domain terms), the
  on-demand module map `notes/map.md`, and per-change specs under
  `changes/<id>/spec.md`.
- **Seven skills**, listed under [Skills](#skills).
- **Kept from the framework machinery:** the `reviewer` subagent, the
  `.ai`-clean Stop hook, the read-only permission allow list, and `probe.py`
  (the deterministic repo inventory).

Gone with the large profile: the `manifest.yaml`/`INDEX.md` knowledge base
with hot/cold tiers and per-task token budgets, drift detection, the
staleness/index tools (`gen_index.py`, `check_stale.py`, `gen_rules.py`), the
on-demand phase docs, the `kb-delta.yaml` patches, the ticket pipeline
(`/add-ticket`, `/plan`, `/implement`, `/add-reference`), and the second
review gate. The agent re-reads the real source instead of maintaining a
synced index of it.

**Existing large-profile scaffolds** cannot be carried across with `/framework-update`:
there is no reference to render for them, so it stops and says so. Scaffold
fresh with `init-agent` and run `/import-agent <old-.ai>`, which distills the KB
into the requirements section, `notes/map.md` and `notes.md` and carries
in-flight change state over.

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
| `/explore [focus]` | Runs the deterministic inventory, asks about non-derivable knowledge, writes commands and rules into the AGENTS.md requirements section and the module map into `.ai/notes/map.md`. Optional free-text focus. |
| `/spec <id> <title...>` | Opt-in. Writes `.ai/changes/<id>/spec.md` for a change you want specified: goal, acceptance criteria (always including the full suite green), task checklist. No implementation yet. |
| `/build <id>` | Opt-in. Works that spec's task checklist, then one fresh-context review of the full diff against the acceptance criteria. |
| `/import-kb <source>` | Reads an existing knowledge base of **any** structure (a docs/wiki folder, a legacy `.ai/`, a README-heavy repo) and distills it into the project-context section and `notes.md`, routing gotchas and runbooks to `notes.md`. |
| `/import-agent <source>` | Migrates a whole existing `.ai/` folder (an older framework version, including a large-profile one, or a differently-shaped agent folder) into the current structure, carrying both the knowledge **and** in-flight change state. Distinct from `/import-kb`, which ignores change state, and from `/framework-update`, which upgrades a scaffold this framework already stamped. |
| `/tidy-up [scope]` | Hygiene sweep over the host code in four passes: removes dead code with evidence (a library's exported surface counts as used), **proposes** obsolete files without deleting them, compresses overlong comments to 1-2 lines while relocating rather than discarding the knowledge in them, and rewrites em dashes out of prose. Gated on a green build/test/lint baseline captured before the sweep and re-checked after; it may not change behavior, and anything that would is a change spec instead. |
| `/framework-update [dry-run]` | Moves the scaffold to the current framework version: merges the framework files, retires what the framework dropped, migrates hand-filled content into the new shape. Never re-explores. |

Every skill body is self-contained; there is no phase-doc layer to follow.
Archiving has no command: prompt the agent; the rules live in AGENTS.md.

## Instructions file: AGENTS.md

The canonical, vendor-neutral instructions file is `AGENTS.md` (protocol,
right-sizing rule, change layout, generated project-requirements
section). For Claude Code, init also writes a one-line `CLAUDE.md` that
imports it via `@AGENTS.md`; Copilot (VS Code and CLI) and Hermes read
`AGENTS.md` natively, so no extra file is needed there.

## Deterministic tools and hooks

Protocol rules that can be enforced mechanically are not left to model
obedience:

- `.ai/agent/tools/probe.py` prints a deterministic repo inventory (host
  commit, language mix, detected build/test/lint commands, module map with
  LOC, dependency manifests, entry points). The agent runs it first in
  `/explore` and seeds the commands from it instead of re-deriving them,
  then samples by its map. It also reports which documentation the repo
  already has, so `/explore` points at it instead of restating it.
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

Every command carries the same name here as on the other harnesses. Two of
them are spelled out rather than shortened, `/framework-update` and
`/import-agent`, because Hermes reserves `/update` and `/import` for built-in
commands of its own. A name that collides with a harness built-in is renamed
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
