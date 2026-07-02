# llm-agent-framework

Universal, project-configurable LLM agent for software projects of any size.
At init you pick a size profile: **large** (the full knowledge-base framework,
for big codebases where context must be rationed) or **small** (a stripped-down
profile for codebases up to ~10k LOC, see [Small projects](#small-projects)).
Concept: CONCEPT.md. All agent docs: telegraphic English, token-optimized.

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
description, project size, claude or copilot); Enter accepts the defaults
(size **large**). If a scaffold already exists it asks before regenerating
framework files (instructions, skills, hooks, settings); hand-filled KB
content, notes, and specs are always preserved, never reverted to stubs.
`init-agent -h` shows help. The numbered steps below describe the **large**
profile; for **small**, see [Small projects](#small-projects). Everything
after init is done by the agent through skills and folder conventions:

1. **Build the knowledge base**: run `/explore`. The agent samples the
   codebase, fills the KB nodes and asks you about non-derivable knowledge
   (domain terms, unwritten rules).
2. **Register external material** the agent will need (an upstream library,
   its docs): `/add-reference ros2-docs https://github.com/ros2/ros2_documentation.git`,
   or put the material into `.ai/external/<name>/` yourself.
3. **Add a ticket**: `/add-ticket JIRA-1234 Add jazzy build`, or drop a
   markdown file into the `.ai/tickets/` inbox yourself, named like
   `JIRA1234-do-this-and-that.md`.
4. **Plan it**: `/plan JIRA-1234`. Answer the Q&A rounds; the plan is then
   reviewed in a fresh context (reviewer subagent) and you sign off.
5. **Implement**: `/implement JIRA-1234`. The agent works the task files in
   order, records KB updates in `kb-delta.yaml`, and ends with a
   fresh-context review of the full diff against the acceptance criteria.
6. **Archive**: just ask the agent ("archive JIRA-1234"). It verifies all
   tasks are done and the KB delta is applied, then moves the ticket to
   `tasks/_archive/`.

Small changes need no ticket: a fix you can describe in one sentence that
touches a single file is done directly; the agent updates the affected KB
nodes and commits `.ai`. The pipeline is for everything larger.

The framework is model-agnostic: it never tells the harness which model to
run, you decide via the harness (for example `/model opusplan` in Claude
Code to plan on Opus and implement on Sonnet). The self-contained task
files and the fresh-context review gates are what keep cheap execution
safe. If you do split models, keep the direction: plan on the strong one.

The same task-file property enables parallel execution: `/plan` marks tasks
with no dependencies and no overlapping files as `parallel: ok`, and those
may be worked by concurrent sessions (one task file each). The constraints
— single writer for `.ai`, one serial review gate at the end, and the fact
that git worktrees do not carry the gitignored `.ai/` — are spelled out in
the implementation phase doc.

## Small projects

Choosing **small** at the size prompt targets codebases up to roughly 10k LOC,
where the whole source is cheap to read on demand and the full knowledge base
is overkill. The small profile keeps only what still pays at that scale and
drops the rest:

- **AGENTS.md** stays the canonical, dense instructions file: protocol,
  right-sizing rule, build/test/lint commands, conventions, and a generated
  project-context section (the only "knowledge store"). Roughly half the size
  of the large profile's AGENTS.md.
- **`.ai/`** is still a private nested git repo (gitignored from the host), but
  holds just `notes.md` (running memory: decisions, gotchas, domain terms) and
  per-change specs under `changes/<id>/spec.md`.
- Four skills: **`/explore`** fills the project-context
  section and `notes.md`; **`/spec <id> <title>`** writes a lightweight spec
  (goal + acceptance criteria + task checklist) for a non-trivial change;
  **`/build <id>`** implements it and ends with **one** fresh-context review of
  the diff against the acceptance criteria (the `reviewer` subagent); and
  **`/import-kb <source>`** distills an existing knowledge base of any structure
  into the project-context section and `notes.md`. A change you can describe in
  one sentence skips the spec entirely.
- Kept: the `reviewer` subagent, the `.ai`-clean Stop hook, the read-only
  permission allow list, and `probe.py` (the deterministic repo inventory has
  no KB dependency, so it fits here too). Dropped: the `INDEX.md`-protection
  hook.

Dropped versus large (all of it exists to ration context in big codebases):
the `manifest.yaml`/`INDEX.md` KB with hot/cold tiers and per-task token
budgets, drift detection, the staleness/index tools (`gen_index.py`,
`check_stale.py`), the on-demand phase docs, the `kb-delta.yaml` patches, and
the second review gate. At ~10k LOC the agent re-reads the real source faster
than it could maintain a synced index.

If a small project outgrows the profile, re-run `init-agent` and pick
**large**: it preserves your hand-filled content (the existing project-context
section is carried over), after which you move what you want from `notes.md`
into KB nodes by hand.

## Skills

`init` scaffolds the workflow as Agent Skills, the open SKILL.md standard
read by Claude Code and a growing set of other harnesses
(`.claude/skills/<name>/SKILL.md`); the copilot harness gets the same
content as VS Code prompt files (`.github/prompts/*.prompt.md`). All
skills carry `disable-model-invocation: true`: they are pipeline steps
with side effects (KB writes, code changes, `.ai` commits), so only an
explicit `/name` from you triggers them, never the model mid-conversation.
Both harnesses invoke them the same way:

| Command | What it does |
|---|---|
| `/explore [focus]` | Phase 1: samples the codebase, fills the KB, regenerates manifest/INDEX and the AGENTS.md project context. Optional free-text focus. |
| `/add-ticket <id> <title...>` | Stores the ticket as markdown in the `.ai/tickets/` inbox. No planning yet. |
| `/plan <ticket-id>` | Phase 2: turns the inbox ticket into `tasks/<id>/` with self-contained task files via Q&A, ends with the fresh-context plan-review gate. |
| `/implement <ticket-id>` | Phase 3: works the planned task files in order; tests, KB delta, drift check against the plan's `kb-commit`, ticket review gate. |
| `/add-reference <name> <origin>` | Clones/copies external material to `.ai/external/<name>/` and registers a `references/<name>` KB node (origin, fetch date, pinned version). |
| `/import-kb <source>` | Reads an existing knowledge base of **any** structure (a docs/wiki folder, a legacy `.ai/`, a README-heavy repo) and transforms it into the framework KB: classifies the content into nodes, writes frontmatter, sets `covers` globs, updates `manifest.yaml`/`INDEX.md` and the project-context section, routes gotchas/runbooks to `notes.md`. Distinct from `/add-reference`, which keeps raw material for search instead of transforming it. |

The phase skills are thin pointers to the phase docs in
`.ai/agent/phases/`, so phase instructions stay in one place. The add-*
skills are self-contained. Archiving has no command: prompt the agent;
the rules live in AGENTS.md.

## Instructions file: AGENTS.md

The canonical, vendor-neutral instructions file is `AGENTS.md` (KB
protocol, budgets, ticket layout, generated project-context section). For
Claude Code, init also writes a one-line `CLAUDE.md` that imports it via
`@AGENTS.md`; Copilot (VS Code and CLI) reads `AGENTS.md` natively, so no
extra file is needed there.

## Deterministic tools and hooks

Protocol rules that can be enforced mechanically are not left to model
obedience:

- `.ai/agent/tools/probe.py` prints a deterministic repo inventory (host
  commit, language mix, detected build/test/lint commands, module map with
  LOC, dependency manifests, entry points). The agent runs it first in
  Phase 1 / `/explore` and seeds the mechanical project-context fields from
  it instead of re-deriving them, then samples by its map. Present in both
  size profiles.
- `.ai/agent/tools/gen_index.py` regenerates `INDEX.md` from
  `manifest.yaml`. `INDEX.md` is never edited by hand or by the agent.
- `.ai/agent/tools/check_stale.py` lists KB nodes whose `covers` globs
  match host-repo commits newer than the node's `updated` date (exit 1
  when stale, so it can run in CI).
- `.ai/agent/tools/gen_rules.py` (claude harness only) renders cold
  `conventions/*` KB nodes that carry `covers` globs into path-scoped rule
  files under `.claude/rules/` (`paths:` frontmatter). Claude Code then
  injects the convention deterministically whenever matching files are
  touched — the model no longer has to remember the manifest lookup for
  conventions. The rule files are build artifacts (marked GENERATED, stale
  ones auto-removed); the KB node stays the single source of truth. On
  Copilot, conventions stay on the manifest protocol.
- `.claude/hooks/protect_generated.py` (PreToolUse) blocks direct writes
  to `INDEX.md` and to GENERATED rule files, pointing to `gen_index.py` /
  `gen_rules.py` (hand-written files in `.claude/rules/` stay editable).
- `.claude/hooks/regen_index.py` (PostToolUse) regenerates `INDEX.md`
  whenever `manifest.yaml` is written and the path-scoped rules whenever
  the manifest or a conventions node is written, so the generated views
  never drift and the agent need not remember to run the `gen_*` tools.
- A SessionStart hook runs `check_stale.py` at the start of every session;
  its output surfaces stale nodes without a standing "remember to run it"
  instruction.
- `.claude/hooks/ai_repo_clean.py` (Stop) blocks ending a turn while the
  `.ai` repo has uncommitted changes, so KB updates are not silently
  dropped. Not absolute: Claude Code overrides a Stop hook after repeated
  consecutive blocks, so the protocol rule in `AGENTS.md` remains the
  backstop.
- `.claude/agents/reviewer.md` defines the fresh-context adversarial
  reviewer used by the plan-review and ticket-review gates.

During Phase 1 the agent additionally offers a project-specific Stop hook
that runs your lint/tests, turning "done = checks pass" into a hard gate.
Hooks and the reviewer subagent are scaffolded for the claude harness;
Copilot has no equivalent mechanism, there the rules stay protocol text.

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
  the same way (`/explore`, `/plan`, ...) in VS Code Copilot Chat;
  arguments are passed as input variables, e.g. `/plan: ticket=FEAT-42`
- no `.claude/settings.json`, hooks or reviewer subagent (no equivalent)

Prompt files require VS Code with the `chat.promptFiles` setting enabled.
Copilot CLI does not load prompt files; it does read `AGENTS.md`, which
therefore contains the phase kickoff lines to type instead (also printed
at the end of `init`), e.g.
`Run Phase 1: read .ai/agent/phases/init.md first and follow it exactly.`

The `.ai/` knowledge base and phase docs are identical for both harnesses;
only the entry files differ.

## What init creates

This section describes the **large** profile; the **small** profile creates the
reduced set described under [Small projects](#small-projects).

`init` creates `.ai/knowledgebase/` (manifest.yaml, INDEX.md, hot/cold
nodes), `.ai/notes.md` (running memory for operational gotchas and runbooks
that don't warrant a curated node), the `.ai/tickets/` inbox,
`.ai/agent/phases/` (on-demand phase docs), `.ai/agent/tools/` (probe,
gen_index, check_stale), the canonical `AGENTS.md`, the skills above and, for Claude
Code, the `CLAUDE.md`
pointer, the reviewer subagent, the hook scripts and
`.claude/settings.json` with the hooks plus a read-only permission allow
list (grep, find, ls, cat, awk, read-only git, `git -C .ai`, the KB
tools, ...) so exploration and `.ai` commits run without a confirmation
prompt per command. Compound commands (`a && b`) only skip the prompt when
every part of the chain is allowed, so common chain members like `cd`,
`echo` and `pwd` are included. If you work interactively, Claude Code's
auto permission mode (a classifier reviews commands and blocks only risky
ones) is a lower-maintenance alternative; the allowlist is what keeps
headless and CI runs deterministic. `AGENTS.md` and `.claude/` / `.github/`
belong to the host repo.

The description prompted at init is seeded into the architecture overview
node, `manifest.yaml` and the project context section of `AGENTS.md`, so
the agent's first ramp-up (Phase 1) starts from a known project intent
instead of discovering it from scratch. Phase 1 verifies and refines it
against the code.

Re-running init never reverts agent or user work: KB nodes, manifest and
INDEX that differ from their stubs are reported as `preserved`, and an
existing `GENERATED:project-context` section is carried over into the
regenerated `AGENTS.md` (also from legacy `CLAUDE.md` scaffolds).

`.ai/` is versioned in its own git repo (`.ai/.git`) and excluded from the
host project via a `.gitignore` entry written by `init`. `init` makes the
first commit; afterwards the agent commits `.ai` changes itself (a protocol
rule in `AGENTS.md`, enforced by the Stop hook on the claude harness). Raw
external material under `.ai/external/` stays out of that repo too
(re-fetchable, would bloat history), as does `.ai/.current` — a gitignored
task cursor (active ticket/change id, current task file, modified files) the
agent reads at session start to resume work after a break, independent of
session compaction.
