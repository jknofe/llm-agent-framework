#!/usr/bin/env python3
"""
init_agent.py - Scaffold a project-aware LLM agent (interactive, run in the
project root). The script only initializes; everything afterwards is done by
the agent through skills and folder conventions:

  /explore               Phase 1: build the knowledge base
  /add-ticket            store a ticket as markdown in the .ai/tickets/ inbox
                         (or drop a <ID>-<slug>.md file there yourself)
  /plan <id>             Phase 2: turn an inbox ticket into tasks/<id>/
  /implement <id>        Phase 3: work the planned task files
  /add-reference         register external material (repos, docs) under
                         .ai/external/ + a references/<name> KB node
                         (or place material in .ai/external/ yourself)
  /import-kb <source>    import an existing knowledge base of any structure:
                         read, classify, and transform it into .ai (KB nodes +
                         notes.md large; project-context + notes.md small)
  /import <source>       migrate an existing .ai/ folder (older framework
                         version or other layout) into the current structure:
                         knowledge and lifecycle state (tickets, tasks, changes)
  /tidy-up [scope]       hygiene sweep that may not change behavior: remove
                         dead code, propose obsolete files for removal,
                         shorten overlong comments, drop em dashes from prose
  /update                move the scaffold to the current framework version:
                         merge the framework files, retire what the framework
                         dropped, migrate hand-filled content into the new
                         shape. Never re-explores; the KB is carried forward
  archive                no command: ask the agent to archive a finished
                         ticket; the rules live in AGENTS.md

Prompts: project name, one-line description, project size (auto/large/small),
harness (claude/copilot). Enter accepts the default. The size prompt defaults
to auto: the profile auto-detected from the codebase LOC (small <=10k, large
above); pick large or small to override. --size auto selects it without
prompting and --size large|small forces a profile. Non-TTY runs use the
auto-detected size (and the other defaults) unless overridden by the flags
below. If a scaffold
already exists, init asks before
overwriting framework files; hand-filled content (KB nodes, manifest, INDEX,
notes, specs, the generated project-context section) is always preserved,
never reverted to stubs. To move an existing scaffold to a newer framework
version, run the agent's /update skill rather than re-running init: updating
is a merge (keep user edits, retire dropped files, migrate hand-filled content
into a changed shape), and merges need judgment this script does not have.

Size profiles (auto-selected from codebase LOC when --size is omitted or auto):
  large            Full framework: KB (manifest, hot/cold nodes, INDEX),
                   on-demand phase docs, deterministic KB tools, ticket
                   pipeline. For large codebases where context must be rationed.
  small            For codebases up to ~10k LOC, where the source is small
                   enough to read on demand. No KB/manifest/phase docs/tools:
                   a dense AGENTS.md (commands + conventions + generated
                   project-context), running memory in .ai/notes.md, a
                   lightweight per-change spec (.ai/changes/<id>/spec.md) and
                   one fresh-context review gate. Skills: /explore /spec /build
                   /import-kb /import /tidy-up /update.

Context layout:
  AGENTS.md                    canonical instructions (vendor-neutral): KB
                               protocol, budgets, generated project-context,
                               phase pointers. Read natively by Copilot;
                               imported via CLAUDE.md for Claude Code
  CLAUDE.md (claude)           one-line pointer: @AGENTS.md
  .ai/notes.md                 running memory (both profiles): gotchas,
                               runbooks, unwritten rules; promote durable
                               items into KB nodes (large profile)
  .ai/.current                 gitignored task cursor: cross-session resume
                               pointer (active ticket/change, task file, files)
  .ai/agent/phases/*.md        phase docs, single source of truth, loaded on
                               demand only when the phase runs
  .ai/agent/tools/*.py         deterministic helpers (gen_index, check_stale)
  .claude/skills/*/SKILL.md    Agent Skills (open standard): thin pointers to
                               the phase docs, self-contained add-* helpers
  .github/prompts/*.prompt.md  copilot harness: same content as prompt files
  .claude/settings.json        permission allow list + hooks (claude only)
  .claude/hooks/*.py           hook scripts: protect generated files, remind
                               about uncommitted .ai changes
  .claude/agents/reviewer.md   fresh-context adversarial reviewer subagent

Versioning:
  .ai/ is excluded from the host project's repo (init appends it to the
  project .gitignore) and tracked in its own git repo at .ai/.git. init
  makes the first commit; afterwards the agent commits .ai changes itself
  (protocol rule in AGENTS.md, enforced by a Stop hook on claude).

Generated docs use two language registers (concept v5, CONCEPT.md section 8):
normative docs (AGENTS.md, phase docs) in plain imperative English, KB
content (node summaries, tickets) telegraphic. Identifiers verbatim.

Usage:
  python init_agent.py        (or: init-agent)            interactive
  python init_agent.py --size auto  --name foo --desc "…"  auto-pick profile
  python init_agent.py --size small --name foo --desc "…" force small profile
  Flags: --name, --description/--desc, --size {large,small,auto}, --harness
  {claude,copilot}, -y/--yes (overwrite framework files without prompting).
  Any omitted value is prompted for, or uses its default on a non-TTY.

  Two flags exist only to serve the agent's /update skill, which is how an
  existing scaffold moves to a newer framework version:
  --detect                print this directory's scaffold stamp as JSON
                          (profile, harness, framework version, file list)
  --emit-reference DIR    render a pristine scaffold of the current framework
                          into DIR, with no git or host-project side effects,
                          as the comparison target /update diffs against
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    # Enables arrow keys / line editing in input() prompts (ask()).
    import readline  # noqa: F401
except ImportError:
    pass  # not available on all platforms (e.g. Windows); plain input then

TODAY = date.today().isoformat()

# Framework revision this generator emits; mirrors CONCEPT.md's version. Every
# scaffold records it in .ai/agent/framework.json, which is what makes an
# agent-driven /update able to tell what changed since the project was built.
FRAMEWORK_VERSION = "5.16"

FRAMEWORK_JSON = ".ai/agent/framework.json"

# ---------------------------------------------------------------- structure

KB_DIRS = [
    "architecture",
    "conventions",
    "domain",
    "infra",
    "decisions",
    "references",
    "tasks",
    "tasks/_archive",
]

HOT_NODES = {
    "architecture/overview.md": {
        "id": "architecture/overview",
        "summary": "High-level architecture: modules, data flow, entry points",
        "tags": ["architecture", "overview"],
        "covers": ["src/**"],
        "tier": "hot",
        "body": (
            "# Architecture Overview\n\n"
            "<!-- Filled in Phase 1 (Initialization). -->\n\n"
            "## Modules\n\n## Data Flow\n\n## Entry Points\n"
        ),
    },
    "conventions/code-style.md": {
        "id": "conventions/code-style",
        "summary": "Code style, naming, formatting, linting rules",
        "tags": ["conventions", "style", "lint"],
        "covers": ["**/*"],
        "tier": "hot",
        "body": (
            "# Code Style\n\n"
            "<!-- Source: linter configs + user Q&A at init. -->\n"
        ),
    },
    "domain/glossary.md": {
        "id": "domain/glossary",
        "summary": "Domain terms and their precise project meaning",
        "tags": ["domain", "glossary"],
        "covers": [],
        "tier": "hot",
        "body": "# Glossary\n\n| Term | Meaning |\n|---|---|\n",
    },
}

COLD_NODE_TEMPLATES = {
    "conventions/testing.md": {
        "id": "conventions/testing",
        "summary": "Test layout, frameworks, coverage expectations",
        "tags": ["conventions", "testing"],
        "covers": ["tests/**", "**/*test*"],
        "tier": "cold",
        "body": "# Testing Conventions\n\n<!-- Filled at init. -->\n",
    },
    "conventions/git-workflow.md": {
        "id": "conventions/git-workflow",
        "summary": "Branching, commit message rules, review gates",
        "tags": ["conventions", "git"],
        "covers": [],
        "tier": "cold",
        "body": "# Git Workflow\n\n<!-- Filled at init. -->\n",
    },
    "infra/build.md": {
        "id": "infra/build",
        "summary": "Build system, targets, local dev setup",
        "tags": ["infra", "build"],
        "covers": ["Makefile", "*.toml", "*.gradle", "CMakeLists.txt", "package.json"],
        "tier": "cold",
        "body": "# Build\n\n<!-- Filled at init. -->\n",
    },
    "infra/ci-cd.md": {
        "id": "infra/ci-cd",
        "summary": "CI/CD pipelines, stages, deployment targets",
        "tags": ["infra", "ci", "cd"],
        "covers": [".github/**", ".gitlab-ci.yml", "Jenkinsfile"],
        "tier": "cold",
        "body": "# CI/CD\n\n<!-- Filled at init. -->\n",
    },
}

ALL_NODES = {**HOT_NODES, **COLD_NODE_TEMPLATES}

PHASES_DIR = ".ai/agent/phases"
TOOLS_DIR = ".ai/agent/tools"

GEN_BEGIN = ("<!-- BEGIN GENERATED:project-context "
             "(source: hot-tier nodes, max 1500 tokens) -->")
GEN_BEGIN_SMALL = ("<!-- BEGIN GENERATED:project-context "
                   "(source: /explore, max 1500 tokens) -->")
GEN_END = "<!-- END GENERATED:project-context -->"


def seed_description(description: str):
    """Seed the user-supplied one-liner into the overview node.

    HOT_NODES and ALL_NODES share meta dicts, so mutating in place updates
    the node file, manifest.yaml and INDEX.md in one go.
    """
    meta = HOT_NODES["architecture/overview.md"]
    meta["summary"] = description
    meta["body"] = (
        "# Architecture Overview\n\n"
        f"{description}\n\n"
        "<!-- Description seeded at init: verify against the code in Phase 1. -->\n\n"
        "## Modules\n\n## Data Flow\n\n## Entry Points\n"
    )


# --------------------------------------------------------------- rendering

def frontmatter(meta: dict) -> str:
    tags = ", ".join(meta["tags"])
    covers = ", ".join(f'"{c}"' for c in meta["covers"])
    return (
        "---\n"
        f"id: {meta['id']}\n"
        f"summary: {meta['summary']}\n"
        f"tags: [{tags}]\n"
        f"covers: [{covers}]\n"
        f"tier: {meta['tier']}\n"
        f"updated: {TODAY}\n"
        "related: []\n"
        "---\n\n"
    )


def render_manifest(project_name: str, description: str = "") -> str:
    lines = [
        f"# Generated by init_agent.py on {TODAY}. Machine-readable KB index.",
        f"project: {project_name}",
    ]
    if description:
        lines.append(f"description: {description}")
    lines += [
        "budgets:",
        "  agents_md_max_tokens: 2000",
        "  generated_section_max_tokens: 1500",
        "  per_task_max_nodes: 4",
        "  per_task_max_tokens: 6000",
        "  related_hops: 1",
        "  budget_policy: soft  # overrun allowed; state reason in one line",
        "nodes:",
    ]
    for path, meta in sorted(ALL_NODES.items()):
        covers = ", ".join(f'"{c}"' for c in meta["covers"])
        tags = ", ".join(meta["tags"])
        lines += [
            f"  - id: {meta['id']}",
            f"    path: {path}",
            f"    summary: {meta['summary']}",
            f"    tags: [{tags}]",
            f"    covers: [{covers}]",
            f"    tier: {meta['tier']}",
            f"    updated: {TODAY}",
        ]
    return "\n".join(lines) + "\n"


def render_index(project_name: str) -> str:
    lines = [
        f"# Knowledge Base Index: {project_name}",
        "",
        "<!-- GENERATED from manifest.yaml by gen_index.py. Do not edit. -->",
        "",
        "| Node | Tier | Load when |",
        "|---|---|---|",
    ]
    for path, meta in sorted(ALL_NODES.items()):
        lines.append(f"| `{path}` | {meta['tier']} | {meta['summary']} |")
    return "\n".join(lines) + "\n"


def render_agents_md(project_name: str, description: str = "",
                     harness: str = "claude",
                     generated_body: str = None) -> str:
    if generated_body is None:
        seed = f"{description}\n" if description else ""
        generated_body = f"{seed}<!-- Populated in Phase 1. Do not edit. -->"
    cli_note = ""
    if harness == "copilot":
        cli_note = f"""## Copilot CLI

Prompt files (`/explore`, `/plan`, `/implement`) work in VS Code only. In
Copilot CLI, start a phase with its kickoff line:

- `Run Phase 1: read {PHASES_DIR}/init.md first and follow it exactly.`
- `Plan ticket <id>: read {PHASES_DIR}/planning.md first, then the ticket.`
- `Implement ticket <id>: read {PHASES_DIR}/implementation.md first, then plan.md.`
- `Tidy up [scope]: read .github/prompts/tidy-up.prompt.md first and follow it exactly.`
- `Update the framework: read .github/prompts/update.prompt.md first and follow it exactly.`

"""
    hook_note = (" A Stop hook in `.claude/settings.json`\n"
                 "    reminds you when `.ai` is dirty, but only when this repo is\n"
                 "    the active Claude project directory; otherwise commit by\n"
                 "    hand and never assume the hook ran." if harness == "claude"
                 else "")
    rules_note = (" Rule files under `.claude/rules/` marked\n"
                  "   GENERATED are likewise build artifacts (of cold\n"
                  "   `conventions/*` nodes): edit the node; a hook runs\n"
                  f"   `{TOOLS_DIR}/gen_rules.py`." if harness == "claude"
                  else "")
    entry_note = ("packaged as Agent Skills under `.claude/skills/`"
                  if harness == "claude"
                  else "exposed as prompt files under `.github/prompts/`")
    goal_note = ""
    if harness == "claude":
        goal_note = """
## Autonomous dispatch (/goal)
`/goal` adds no new definition of done - `/implement` already has one:
every task in `plan.md` at `status: done`, plus the ticket review gate's
sign-off. `/goal` only changes whether the agent stops to ask permission
between tasks or keeps going on its own until the plan is fully done.
Reach for it when both hold: each task's acceptance criteria are checkable
by a machine (tests, lint, a named gate script), and no mid-flight
judgment call is expected - a `/goal` loop cannot ask you a question, so
save it for tickets that already cleared planning's Q&A. Invoke
`/implement <id>` first, then set the goal: skills here are not
model-invocable, so the loop can only follow the phase procedure if its
instructions are already in context. Point the condition at `plan.md`
(never restate a looser version), make the agent prove it in output -
the goal evaluator reads only the transcript, never files - and bound
the run with a turn cap:
```
/goal every task in .ai/knowledgebase/tasks/<id>/plan.md is status:done
and shown, the transcript shows the ticket review gate passing, and .ai
is committed; or stop after 30 turns
```
Pair it with the same stall rule as a manual `/implement` run: on
`test-fail` twice on the same task, stop rather than a third blind
attempt - the loop has no one else to escalate to.
"""
    return f"""# Agent: {project_name}

Project-aware agent (concept v5). KB = `.ai/knowledgebase/`. Token efficiency
is a hard requirement; this file stays under 2000 tokens. Phase instructions
live in `{PHASES_DIR}/` and are loaded only when the phase runs
({entry_note}). Write normative instructions in plain
imperative English; write KB content telegraphic. Keep identifiers, paths,
and commands verbatim.

## Phases

| Phase | Read first (mandatory, before any other step) |
|---|---|
| 1 Initialization | `{PHASES_DIR}/init.md` |
| 2 Planning | `{PHASES_DIR}/planning.md` |
| 3 Implementation | `{PHASES_DIR}/implementation.md` |
| 4 Operational | none. Protocol below = default behavior |

Maintenance is not a phase. `/update` moves this scaffold to the current
framework version, merging the framework files and migrating the KB in place;
it never re-runs Phase 1. `/tidy-up [scope]` sweeps the host code for dead
code, obsolete files, overlong comments, and em dashes, and may not change
behavior; anything that would is a ticket.

Right-sizing: a change you can describe in one sentence and that touches a
single file needs no ticket. Do it directly, update the affected KB nodes,
and commit `.ai`. Use the ticket pipeline for everything larger, but for a
change confined to one self-contained area (e.g. a packaging descriptor or a
self-contained CLI subcommand), take
planning.md's trivial path: one task file, one review gate, no Q&A rounds. Do
not pay ceremony that exceeds the task.
{goal_note}
## KB Protocol

1. Parse `.ai/knowledgebase/manifest.yaml` first. Never load all nodes.
2. Hot-tier content is embedded in the Project Context section below. Never
   load `tier: hot` nodes separately.
3. Match the task against `covers` globs and `tags` first (stage 1, exact).
   Only on a miss, keyword-score the manifest summaries (stage 2).
4. Budgets are soft targets: aim for at most 4 cold nodes / 6000 tokens per
   task, and follow `related` links at most 1 hop. If you must exceed a
   budget, state the reason in one line and proceed. Recall beats precision:
   never skip context you need just to stay under budget.
5. Never load `tasks/_archive/`.
6. Run exploration and review in sub-agent contexts when the harness
   supports them. Keep raw file dumps out of the main context.
7. Invariants: single source of truth, never duplicate. Split a node over
   ~1500 tokens and cross-link the parts.
8. `INDEX.md` is generated. To change it, edit `manifest.yaml` and run
   `python3 {TOOLS_DIR}/gen_index.py`. Never edit `INDEX.md` directly.{rules_note}
9. External references: nodes under `references/` describe material in
   `.ai/external/` (other repos, docs, example code). Load the node first,
   then search the raw copy with targeted queries (in a sub-agent when
   available). Never bulk-load raw external material into context. If you
   find material in `.ai/external/` without a `references/` node, create
   the node (see the /add-reference skill for the format).
10. Persist `.ai` changes: after changing files under `.ai/`, commit them in
    its own repo with a short message, e.g.
    `git -C .ai add -A && git -C .ai commit -m "plan: JIRA-1234"`.
    Never commit `.ai` content to the host project repo.{hook_note}
11. Running memory: `.ai/notes.md` holds operational gotchas, runbooks
    (validation loops, CI quirks, merge-order rules), and unwritten rules too
    volatile for a curated node. Read it at session start; append
    telegraphically as you learn. Promote anything durable and structural into
    a KB node via `kb-delta.yaml`; keep `notes.md` as the volatile layer.
12. Task cursor: `.ai/.current` (gitignored working state) records the active
    ticket id, the current task file, the modified-files list, and the date.
    Read it at session start and offer to resume; update it when you start or
    finish a task; delete it when the ticket is done. It is the durable resume
    pointer across sessions, independent of compaction.
13. When compacting the session, always preserve: the current ticket id, the
    current task file path, the list of modified files, and the build/test
    commands (`.ai/.current` is the on-disk backup of exactly this).

## Ticket Layout

```
.ai/tickets/      # inbox: <ID>-<slug>.md (e.g. JIRA1234-do-this-and-that.md),
                  # added via /add-ticket or dropped in by the user
.ai/knowledgebase/tasks/<ticket-id>/
  ticket.md       # original ticket + recorded Q&A answers
  plan.md         # task index; frontmatter: read-first pointer, kb-commit
  NN-<slug>.md    # one file per task, self-contained
  kb-delta.yaml   # accumulated KB patches
.ai/knowledgebase/tasks/_archive/   # finished tickets; never load
```

Status in frontmatter (`planned|in-progress|done|blocked`), never in folder
names. `/plan <id>` turns an inbox ticket into `.ai/knowledgebase/tasks/<id>/`
(and promotes its `status` from `new` to `planned`).

Archive only when the user asks for it, then: verify every task file in
`.ai/knowledgebase/tasks/<id>/` has `status: done` (if not, list the open ones
and ask); verify `kb-delta.yaml` was applied to the KB; move it to
`.ai/knowledgebase/tasks/_archive/<id>/`; commit the `.ai` repo (`archive: <id>`).

{cli_note}## Project Context

{GEN_BEGIN}
{generated_body}
{GEN_END}
"""


def render_claude_pointer() -> str:
    return (
        "# CLAUDE.md\n\n"
        "Canonical agent instructions live in AGENTS.md (vendor-neutral).\n"
        "Imported below; do not duplicate content here.\n\n"
        "@AGENTS.md\n"
    )


def render_agents_md_small(project_name: str, description: str = "",
                           harness: str = "claude",
                           generated_body: str = None) -> str:
    """Small-profile AGENTS.md: dense, self-contained. No KB protocol, no
    budgets table, no phase pointers. The generated project-context section is
    the only knowledge store; the source code is read on demand."""
    if generated_body is None:
        seed = f"{description}\n" if description else ""
        generated_body = (f"{seed}<!-- Populated by /explore. "
                          "Do not edit by hand. -->")
    hook_note = (" A Stop hook in `.claude/settings.json`\n"
                 "   reminds you when `.ai` is dirty, but only when this repo is\n"
                 "   the active Claude project directory; otherwise commit by hand\n"
                 "   and never assume the hook ran." if harness == "claude"
                 else "")
    entry_note = ("packaged as Agent Skills under `.claude/skills/`"
                  if harness == "claude"
                  else "exposed as prompt files under `.github/prompts/`")
    cli_note = ""
    if harness == "copilot":
        cli_note = """## Copilot CLI

Prompt files (`/explore`, `/spec`, `/build`) work in VS Code only. In Copilot
CLI, state the intent directly; the Protocol and Workflows above apply:

- `Explore the project and fill the Project Context section + .ai/notes.md.`
- `Spec change <id> "<title>": write .ai/changes/<id>/spec.md (goal, acceptance criteria, tasks).`
- `Build change <id>: implement .ai/changes/<id>/spec.md, then review the diff against the criteria.`
- `Tidy up [scope]: read .github/prompts/tidy-up.prompt.md first and follow it exactly.`
- `Update the framework: read .github/prompts/update.prompt.md first and follow it exactly.`

"""
    goal_note = ""
    if harness == "claude":
        goal_note = """## Autonomous dispatch (/goal)
`/goal` adds no new definition of done - `/build` already has one: the
spec's acceptance criteria, the gate command, the reviewer's sign-off.
`/goal` only changes whether the agent stops to ask permission between
those steps or keeps going on its own until they are met. Reach for it
when both hold: the finish line is something a machine can check (tests
pass, lint clean, a named gate script exits 0), and no mid-flight judgment
call is expected - a `/goal` loop cannot ask you a question. Invoke
`/build <id>` first, then set the goal: skills here are not
model-invocable, so the loop can only follow the build procedure if its
instructions are already in context. Point the condition at the artifact
that already defines done (never restate a looser version), make the
agent prove it in output - the goal evaluator reads only the transcript,
never files - and bound the run with a turn cap:
```
/goal every acceptance criterion in .ai/changes/<id>/spec.md is checked
off and shown, the transcript shows the gate command exiting 0, and the
reviewer reports no correctness gaps; or stop after 20 turns
```
Pair it with the same stall rule as a manual `/build` run: if 2
consecutive turns make no measurable progress on the same blocker, stop
and report it instead of a third blind attempt - the loop has no one else
to escalate to.

"""
    return f"""# Agent: {project_name}

Small-project agent (concept v5, small profile). Token efficiency is a hard
requirement: keep this file dense and scannable. At this scale the source code
is the knowledge base, so explore it on demand with your read/search tools
(just-in-time) instead of maintaining a separate knowledge store. Workflow
entry points are {entry_note}. Write normative instructions in plain imperative
English; write notes telegraphic. Keep identifiers, paths, and commands
verbatim.

## Right-sizing
A change you can describe in one sentence that touches one or two files needs
no spec: make it, update `.ai/notes.md` if a decision or gotcha emerged, and
commit `.ai`. Use `/spec` then `/build` for everything larger.

{goal_note}## Protocol
1. Explore the codebase with native read/search tools (Read, Grep, Glob), not
   by loading everything. The source is the knowledge base. Check the Project
   Context section below first: if it still holds only the seed one-liner (or
   the raw `<!-- Populated by /explore -->` marker) with no module map or
   build/test/lint commands, `/explore` was never run. Run it before non-trivial
   work: a stale or missing digest costs more discovery tokens over the
   session than the one-time `/explore` pass.
2. Durable knowledge (decisions, gotchas, domain terms, unwritten rules,
   operational runbooks, pointers to related repos/paths this project depends
   on, e.g. a sibling repo's venv used for tests, or prior-art to mirror) goes
   in `.ai/notes.md` (append, telegraphic). Read it at the start of a task.
   Architecture/module-map knowledge belongs in the Project Context section
   instead (`/explore`'s output). Never duplicate it here. `notes.md` may grow
   into a hub: once it passes ~1-2 screens, move topic clusters (largest first)
   into `.ai/notes/<topic>.md`, each leaving a one-line linked pointer
   (`- [topic](notes/<topic>.md) - hook`) behind, until the hub is back under
   ~1 screen. Then read the hub first and open only the leaves a task needs;
   keep the pointer list in sync (add on split, remove on delete). Do not split
   while notes stay short - one file is cheaper to read whole than an index
   plus a leaf.
3. Non-trivial work: `/spec <id>` writes `.ai/changes/<id>/spec.md` (goal,
   acceptance criteria, task checklist); `/build <id>` implements it.
4. Before declaring a change done, have the full diff reviewed in a fresh
   context against the acceptance criteria: the `reviewer` sub-agent where
   available; in an autonomous run, a fresh general-purpose sub-agent or, if
   none is reachable, a recorded clean-context self-review. The review also
   confirms the diff honors every build/CI gotcha recorded in `.ai/notes.md`,
   not just the acceptance criteria. Fix correctness gaps; ignore style-only
   findings.
5. Tests and lint must pass. Done = checks green and review clean.
6. After changing files under `.ai/`, commit them in its own repo:
   `git -C .ai add -A && git -C .ai commit -m "<short summary>"`. Never commit
   `.ai` content to the host project repo.{hook_note}
7. Task cursor: `.ai/.current` (gitignored working state) records the active
   change id, the spec file path, the modified-files list, and the date. Read
   it at session start and offer to resume; update it when you start or finish
   a change; delete it when the change is done. It is the durable resume
   pointer across sessions, independent of compaction.
8. When compacting the session, preserve: the current change id, the spec file
   path, the list of modified files, and the build/test commands
   (`.ai/.current` is the on-disk backup of exactly this).

## Workflows
| Command | What it does |
|---|---|
| `/explore` | Sample the code; fill the Project Context below and `.ai/notes.md`. |
| `/spec <id> <title>` | Write `.ai/changes/<id>/spec.md` for a non-trivial change. |
| `/build <id>` | Implement the spec's tasks, review the diff, finish. |
| `/tidy-up [scope]` | Hygiene sweep that may not change behavior: dead code, obsolete files, comments, em dashes. |
| `/update` | Move this scaffold to the current framework version, keeping what the project knows. |

## Changes layout
```
.ai/changes/<id>/spec.md   # goal, acceptance criteria, task checklist, notes
.ai/changes/_archive/      # finished changes; never load
.ai/notes.md               # running memory hub: decisions, gotchas, domain terms
.ai/notes/<topic>.md       # optional leaves, linked from notes.md once it grows
```
Status lives in the spec frontmatter (`planned|in-progress|done`), never in
folder names. Archive only when the user asks: verify `status: done`, move
`changes/<id>/` to `changes/_archive/`, commit `.ai`.

{cli_note}## Project Context

{GEN_BEGIN_SMALL}
{generated_body}
{GEN_END}
"""


def render_notes_stub() -> str:
    return (
        "# Project Notes\n\n"
        "<!-- Running memory for the agent: durable decisions, gotchas, domain\n"
        "terms, unwritten rules, operational runbooks (validation loops, CI\n"
        "quirks, merge-order rules), and pointers to related repos/paths this\n"
        "project depends on (e.g. a sibling repo's venv used for tests, prior-art\n"
        "to mirror) that do not fit a curated KB node. Append, telegraphic. Read\n"
        "at the start of a task. Architecture/module-map knowledge belongs in the\n"
        "AGENTS.md Project Context section (/explore's output) instead - never\n"
        "duplicate it here. The code is the source of truth for structure; this\n"
        "file captures what the code does not say.\n"
        "Once this file passes ~1-2 screens, become a hub: move topic clusters\n"
        "(largest first) into .ai/notes/<topic>.md, each leaving a linked\n"
        "one-line pointer here, until the hub is back under ~1 screen. Read the\n"
        "hub first, open only the leaves a task needs. -->\n"
    )


def render_phase_init(harness: str = "claude") -> str:
    perms = (
        " Shell\n"
        "  commands you do need are pre-allowed in `.claude/settings.json`\n"
        "  (read-only list)." if harness == "claude" else ""
    )
    hook_offer = ""
    if harness == "claude":
        hook_offer = """
## Verification hook (offer once)
Once the build, test, and lint commands are known, offer the user a Stop
hook in `.claude/settings.json` that runs lint (and fast tests if cheap)
when the agent finishes a turn with code changes. A deterministic check
beats an instruction the model may skip. Add it only with user consent.
Mention the lighter alternative too: a session-scoped `/goal` condition
(e.g. "tests and lint pass") that an evaluator re-checks each turn, good
for a single unattended run without touching settings.
"""
    rules_line = ""
    if harness == "claude":
        rules_line = (
            "- Cold `conventions/*` nodes with `covers` globs also render to\n"
            "  path-scoped rule files under `.claude/rules/` (loaded by the\n"
            "  harness when matching files are touched). The same PostToolUse\n"
            "  hook regenerates them on every conventions-node or manifest\n"
            "  write. Never edit the rule files; edit the node.\n"
        )
    return f"""# Phase 1: Initialization

Read this before analyzing the project.

## Strategy
- Run the deterministic inventory first: `python3 {TOOLS_DIR}/probe.py`. It
  prints host commit, language mix, detected build/test/lint commands, a
  module map (files + LOC), dependency manifests, and entry-point candidates.
  Seed the mechanical `GENERATED:project-context` fields (stack, commands,
  module map) straight from it, and use its map to decide what to sample.
  Do not re-derive by hand what probe already reports.
- If a project description was seeded at init (overview node summary and the
  Project Context section), treat it as a hint, not a fact: use it to pick
  what to sample first, then verify and refine it against the code.
- Sample, do not scan everything: per module, read entry points, public API,
  and tests.
- Prefer the harness's native read and search tools (Read, Grep, Glob) over
  shell `grep`/`cat`/`awk`: same result, no permission prompts.{perms}
- Run exploration in isolated sub-agent contexts when the harness supports
  them. Each sub-agent returns a condensed summary of at most 2000 tokens.
  Keep raw file dumps out of the synthesizing context. KB nodes and the
  digest stay yours to write: never let a sub-agent fill them - digest
  errors compound across every later session.
- If you cannot spawn sub-agents (you are yourself a sub-agent, or a headless
  run without them), every raw file read lands in this one context, so explore
  is a full session on its own. Do not try to reach planning or implementation
  in the same session: sample the highest-value modules, build the KB, commit,
  and hand off. A fresh session resumes from the committed KB and `.ai/.current`.
- Build KB nodes bottom-up: module nodes first, then the architecture
  overview. Commit `.ai` after each node (or small batch), not once at the
  end: exploration is where the session budget runs out, and a per-node commit
  makes a mid-explore stop resumable instead of lost work.
- Record operational gotchas and runbooks you hit (build quirks, test-setup
  traps, CI requirements) in `.ai/notes.md`; reserve curated nodes for stable
  architecture and conventions.
- After node changes, update `manifest.yaml`. `INDEX.md` regenerates
  automatically: a PostToolUse hook runs `gen_index.py` on every manifest
  write. Never edit `INDEX.md` directly. If no hook fires (non-claude
  harness), run `python3 {TOOLS_DIR}/gen_index.py` yourself.
{rules_line}- Regenerate the `GENERATED:project-context` section in AGENTS.md from the
  hot-tier nodes, condensed: project one-liner, tech stack, build/test/lint
  commands, top conventions, module map (one line per module plus cold-node
  ref), core glossary terms. Cap: 1500 tokens.

## Non-derivable knowledge
Ask the user about domain terms, unwritten conventions, and ownership.
Record the answers directly in the matching KB nodes.

## Autonomous mode
If no human is available to answer (headless or sub-agent run): do not block.
Decide each open question from the evidence in the code and configs, record it
as a single numbered assumption (the resolved decision, not your deliberation),
and proceed. Surface assumptions a maintainer would likely want to revisit.
{hook_offer}
## Incrementality
Record the commit SHA of the host repo in the overview node. A re-init
processes only changes since that SHA (`git log --name-only <sha>..HEAD`).

## Output
Produce a coverage report: areas read vs skipped (lazy-init candidates for
Phase 4).
"""


def render_phase_planning() -> str:
    return f"""# Phase 2: Planning

Read this before decomposing a ticket.

## Workflow
1. Locate the ticket in the inbox: `.ai/tickets/<id>*.md` (created via
   /add-ticket or dropped in by the user). If it is missing, ask the user
   for the ticket content.
2. Create `.ai/knowledgebase/tasks/<id>/`: move the inbox file's content into
   `ticket.md` (format below) and set its frontmatter `status: planned` (it
   was `status: new` in the inbox), then delete the inbox file.
3. Load matched KB nodes (protocol budgets apply).
4. Run interactive Q&A with the user until the acceptance criteria are
   unambiguous. Keep the rounds bounded. Record answers in `ticket.md`. If no
   human is available (autonomous run), do not block: resolve each open
   question from the evidence, record it as a single numbered assumption (the
   decision, not your deliberation) in `ticket.md`, and proceed.
5. Write one task file per task. `plan.md` stays a thin index.
6. Plan-review gate: have the plan reviewed in a fresh context that did not
   produce it. Use the `reviewer` sub-agent where the harness supports
   sub-agents. If it cannot be spawned (e.g. you are yourself a sub-agent) and
   no human is available (autonomous run), spawn a fresh general-purpose
   sub-agent given only the plan and the acceptance criteria, never your own
   working context; if no fresh context is reachable at all, do a
   clean-context self-review against this gate's checklist and record that the
   `reviewer` sub-agent was unavailable. Never silently skip the gate. Fix gaps
   that touch the acceptance criteria, then get user sign-off on `plan.md` (in
   an autonomous run, record the assumptions instead) before implementation
   starts. A weak plan poisons every downstream task.
7. Commit the `.ai` repo (`plan: <id>`).

## Trivial tickets
If the ticket touches one or two files and the diff fits in one sentence,
skip the Q&A rounds and write a single task file `01-task.md`. The
plan-review gate shrinks to a one-line user sign-off. Do not pay planning
ceremony that exceeds the task.

## ticket.md format
Frontmatter: `id`, `title`, `status: planned`, `created: <date>`.
Body: the original ticket description, then a `## Q&A (Planning)` section
with the recorded answers.

## Task file format (`NN-<slug>.md`)
Frontmatter: `status: planned`, `depends: []`, `parallel: ok|no`.
Set `parallel: ok` only when the task has no `depends` entries and its
affected files overlap with no other task's; such tasks may be dispatched to
concurrent sessions (see implementation.md, Parallel dispatch). When in
doubt, `no`.
Body, self-contained:
- Goal and testable acceptance criteria that cover ecosystem correctness, not
  just "it runs": where a linter or policy check exists for the ecosystem you
  touch (eslint, mypy/ruff, clippy, shellcheck, lintian, a schema validator),
  name it and make passing it a criterion
- Affected files with explicit paths
- Pre-bound KB node ids
- Expected signatures/interfaces
- Test skeletons

Pre-binding is a warm start, not a contract: implementation starts from the
bound nodes and files and may run at most 5 targeted searches of its own
before escalating `missing-context`.

## plan.md format
Frontmatter: `ticket: <id>`, `status: planned`,
`read-first: {PHASES_DIR}/implementation.md`,
`kb-commit: <output of git -C .ai rev-parse HEAD>`, `updated: <date>`.
Body: index only, a task table
`| # | Task file | Depends on | Parallel | Status |`.
`kb-commit` records the KB state the plan was built against; the
implementation phase diffs against it to detect drift. The `read-first`
pointer forces the implementing session to load its phase doc. Do not
remove either.
"""


def render_phase_implementation(harness: str = "claude") -> str:
    rules_bullet = ""
    if harness == "claude":
        rules_bullet = (
            "- Path-scoped rules under `.claude/rules/` are generated from cold\n"
            "  `conventions/*` nodes; the PostToolUse hook regenerates them on\n"
            "  conventions-node and manifest writes. Never edit a GENERATED rule\n"
            "  file; edit the node (run `python3 "
            f"{TOOLS_DIR}/gen_rules.py` by hand\n"
            "  only if no hook fired).\n"
        )
    return f"""# Phase 3: Implementation

Read this before executing any task.

## Load discipline
Load only: `plan.md`, the single current task file, its pre-bound KB nodes,
and the listed files. You may run at most 5 targeted searches beyond that.
Never load the whole ticket folder.

## Task cursor
At the start of a task, write `.ai/.current` (gitignored) with the active
ticket id, this task file, the modified-files list, and the date; refresh the
modified-files list as you edit. On task completion, point it at the next task;
when the ticket is done, delete it. A fresh session reads `.ai/.current` first
to resume exactly where the last one stopped.

## Drift check (diff-aware)
`plan.md` frontmatter records `kb-commit`, the `.ai` commit the plan was
built against. Before starting a task, check each pre-bound node for drift:
`git -C .ai diff <kb-commit> -- knowledgebase/<node path>`.
- Empty diff: proceed.
- Non-empty: read the diff. If it does not touch the task's interfaces or
  acceptance criteria, proceed on the fresh content. If it does, stop and
  re-plan the affected task only.
Never proceed silently on stale context. Never trigger a full re-plan for
cosmetic drift.

## Definition of done (per task)
- Tests pass and lint is clean
- Task frontmatter is `status: done`
- A KB patch is appended to `kb-delta.yaml`:
  `op: update|create|split`, `node: <id>`, `diff: <content>`

## Ticket review gate
After the last task is done, review the combined change in a fresh context
before declaring the ticket done: run the `reviewer` sub-agent on the full
diff against the acceptance criteria in `ticket.md` and `plan.md`. If the
harness cannot spawn it (e.g. you are yourself a sub-agent) and no human is
available, spawn a fresh general-purpose sub-agent given only the diff and the
criteria; if no fresh context is reachable at all, do a clean-context
self-review against those criteria and record that the `reviewer` sub-agent
was unavailable. Never silently skip the gate. Fix gaps that affect
correctness or the stated requirements; ignore style-only findings. The gate
also cross-checks captured constraints: for every build, CI, or packaging
gotcha recorded in `.ai/notes.md` or the bound KB nodes, confirm the diff
honors it. A change that ignores a known build side effect or feature flag is
a correctness gap even when the acceptance criteria read as met. Record the
outcome in `plan.md` (`reviewed: <date>`).

## Parallel dispatch (optional)
Tasks marked `parallel: ok` in their frontmatter may be worked by concurrent
sessions, one task file per session. Constraints:
- Each session gets only its self-contained task file plus this doc; never
  share working context between parallel sessions.
- `.ai` stays single-writer: only the coordinating session updates `plan.md`
  status, `kb-delta.yaml`, `.ai/.current`, and makes `.ai` commits. Parallel
  workers report their result and proposed KB patch back instead of writing.
- Git worktrees of the host repo do not contain the gitignored `.ai/`; run
  parallel sessions in the same checkout (parallel-ok tasks touch disjoint
  files by definition) or copy `.ai/` into the worktree.
- The ticket review gate stays serial: one fresh-context review of the
  combined diff after the last task, never per worker.

## Escalation (typed; never improvise around a blocker)
- `missing-context`: use your bounded discovery first, then reload KB (1 hop,
  in a sub-agent when available). Still blocked: ask the user.
- `ambiguity`: ask the user.
- `test-fail` twice on the same task: stop. Have a fresh context (the
  `reviewer` sub-agent) critique the approach, or re-plan the task. Never
  make a third blind attempt.

## KB maintenance
- `kb-delta.yaml` auto-apply covers metadata and `covers` changes only.
  Structural changes go through the review gate.
- After hot-tier node updates, regenerate `GENERATED:project-context` in
  AGENTS.md. Before declaring the ticket done, run the project-context
  refresh so the always-loaded digest cannot silently drift: re-run
  `python3 {TOOLS_DIR}/probe.py` and compare its build/test/lint commands and
  module map against that section. Refresh only for a changed command or a
  new/removed/renamed module; a bare LOC delta on an existing module is not
  actionable, leave it. This is a bounded diff check, not a re-explore.
- After `manifest.yaml` changes, `INDEX.md` regenerates automatically (a
  PostToolUse hook runs `gen_index.py`); run it by hand only on a non-claude
  harness. Never edit `INDEX.md` directly.
{rules_bullet}- ADRs (`decisions/`) are append-only. Supersede via link, never edit.
- Prune test (for every standing rule or instruction you maintain): if the
  agent already behaves correctly without it, delete it. Always-on
  instruction bloat is why real rules get ignored.
- Append operational gotchas and runbooks (validation loops, CI quirks,
  merge-order rules) to `.ai/notes.md` as you hit them; promote durable
  structural knowledge into a node via `kb-delta.yaml`. `notes.md` is the
  volatile layer, curated nodes are the source of truth.
- Staleness: `check_stale.py` lists nodes whose `covers` globs match host-repo
  commits newer than the node. A SessionStart hook runs it automatically; its
  output at session start flags nodes to refresh. Run
  `python3 {TOOLS_DIR}/check_stale.py` by hand after a merge or on a non-claude
  harness.
"""


def render_update_body(size: str, harness: str, arg: str) -> str:
    """Body of the /update skill: an agent-driven framework update.

    A scaffolder can only own files whole (regenerate or freeze), which is why
    updating used to lose user edits, keep retired files, and never migrate the
    shape of hand-filled content. Those are merge decisions, so the agent makes
    them. The rule the whole procedure serves: the knowledge base is the
    expensive artifact, so an update migrates it and never re-derives it.

    Varies on both axes: the large profile has a KB, manifest, INDEX and
    generated tools to migrate; the small profile has notes and specs. Harness
    decides which framework files exist to merge (settings/hooks/skills on
    claude, prompt files on copilot).
    """
    if harness == "claude":
        backup_paths = "AGENTS.md, CLAUDE.md, and `.claude/`"
        merge_cases = (
            "     - `.claude/settings.json`: permission entries and hooks a user\n"
            "       added are not framework state. Union them with the\n"
            "       reference's; drop only entries the reference retired.\n"
            "     - AGENTS.md outside the GENERATED markers: project-specific\n"
            "       rules a user appended below the framework text.\n"
            "     - skills, hooks, or sub-agents present here but not in the\n"
            "       reference: the user's own, unless the generator's history\n"
            "       says otherwise. Settle it with the orphan test below rather\n"
            "       than assuming either way.\n")
        verify_extra = (
            "   - `.claude/settings.json` parses as JSON and every hook command\n"
            "     it names points at a file that exists.\n")
    else:
        backup_paths = "AGENTS.md and `.github/prompts/`"
        merge_cases = (
            "     - AGENTS.md outside the GENERATED markers: project-specific\n"
            "       rules a user appended below the framework text.\n"
            "     - prompt files under `.github/prompts/` present here but not in\n"
            "       the reference: the user's own, unless the generator's history\n"
            "       says otherwise. Settle it with the orphan test below rather\n"
            "       than assuming either way.\n")
        verify_extra = ""

    if size == "large":
        owned = ("KB nodes under `.ai/knowledgebase/`, `manifest.yaml`,\n"
                 "`INDEX.md`, `.ai/notes.md`, tickets, task files, and the\n"
                 "`GENERATED:project-context` section of AGENTS.md")
        migrate = (
            "   - New or renamed frontmatter keys on KB nodes: add them, deriving\n"
            "     values from the node's own content and `covers` globs.\n"
            "   - New fields or sections in `manifest.yaml`: fill them from the\n"
            "     KB, never from the reference's stub values.\n"
            "   - Moved or renamed directories: `git mv` inside `.ai` so the KB\n"
            "     history survives the move.\n")
        regen = (
            f"   Then rebuild only what is derived: `python3 {TOOLS_DIR}/gen_index.py`\n"
            "   regenerates `INDEX.md` from `manifest.yaml`, so it is always safe.\n")
        verify_tools = (f"`{TOOLS_DIR}/probe.py`, `{TOOLS_DIR}/gen_index.py`,\n"
                        f"     and `{TOOLS_DIR}/check_stale.py`")
    else:
        owned = ("`.ai/notes.md`, `.ai/notes/<topic>.md`, change specs under\n"
                 "`.ai/changes/`, and the `GENERATED:project-context` section of\n"
                 "AGENTS.md")
        migrate = (
            "   - New or renamed sections in the project-context digest: add the\n"
            "     heading and move the matching content that is already there\n"
            "     under it. Do not re-derive the content from the codebase.\n"
            "   - A changed spec format: bring existing `.ai/changes/<id>/spec.md`\n"
            "     files up to it, keeping every goal, criterion, and task intact.\n"
            "   - Moved or renamed directories: `git mv` inside `.ai` so the notes\n"
            "     history survives the move.\n")
        regen = ""
        verify_tools = f"`{TOOLS_DIR}/probe.py`"

    return (
        "Update this project's agent framework to the current version, in\n"
        "place, without losing what this project knows. Argument (optional,\n"
        f"`dry-run` reports the plan and changes nothing): {arg}\n\n"
        "The knowledge this project accumulated is the expensive artifact and\n"
        "the framework files are cheap. So: never re-run /explore as part of an\n"
        "update, and never regenerate hand-filled content from a stub. That\n"
        f"covers {owned}.\n\n"
        "1. Preflight.\n"
        f"   - Read `{FRAMEWORK_JSON}` for the recorded framework version,\n"
        "     profile, harness, and the list of framework files that version\n"
        "     emitted. If the file is missing, this scaffold predates the stamp:\n"
        "     run `python3 \"$LLM_AGENT_HOME/init_agent.py\" --detect` for\n"
        "     profile/harness/name and treat the recorded file list as empty.\n"
        "     Retirement then rests entirely on the orphan test in step 3, so do\n"
        "     not skip it on a pre-stamp scaffold.\n"
        "   - Commit anything pending in `.ai` so the update is one revertable\n"
        "     diff: `git -C .ai add -A && git -C .ai commit -m \"pre-update\n"
        "     snapshot\"`.\n"
        "   - The `.ai` repo does not cover the framework files that live in the\n"
        "     host repo, and those are the ones an update overwrites. Copy\n"
        f"     {backup_paths} into `.ai/agent/.update-backup/`, replacing any\n"
        "     older backup. Older scaffolds do not ignore that path yet, so make\n"
        "     sure `.ai/.gitignore` contains `agent/.update-backup/` first; a\n"
        "     backup committed into the KB history is not a backup.\n"
        "   - Report `git status` for those paths. Untracked is the normal state\n"
        "     for a scaffold the host repo never committed: note it and carry on,\n"
        "     the backup already covers the content. Tracked *and modified* is the\n"
        "     one that stops you, because the user has work in a file this update\n"
        "     will overwrite: say which files and let them decide first.\n\n"
        "2. Render the reference, for the profile and harness step 1 established\n"
        "   (from the stamp, or from `--detect` when there is none). The generator\n"
        "   is at\n"
        "   `$LLM_AGENT_HOME/init_agent.py` (set by the framework's install.sh).\n"
        "   If `$LLM_AGENT_HOME` is unset, ask the user where the checkout is;\n"
        "   do not guess a path. Pull it first when it has a remote\n"
        "   (`git -C \"$LLM_AGENT_HOME\" pull --ff-only`), then render a pristine\n"
        "   scaffold into a temp directory:\n\n"
        "       python3 \"$LLM_AGENT_HOME/init_agent.py\" --emit-reference <tmpdir> \\\n"
        f"         --size {size} --harness {harness} --name <project-name>\n\n"
        "   The reference is a read-only comparison target. Never copy it over\n"
        "   the project wholesale; that is the blind overwrite this skill exists\n"
        "   to replace.\n\n"
        "3. Classify every path in the reference and in this scaffold, then act\n"
        "   per file. Framework-owned means listed in the reference's or the\n"
        "   recorded `framework_files`.\n"
        "   - Added (in the reference, absent here): copy it in.\n"
        "   - Identical: leave it.\n"
        "   - Changed by the framework, untouched by the user: take the\n"
        "     reference's version. Treat a file as user-edited whenever you\n"
        "     cannot establish that it is still what its recorded version\n"
        "     emitted, and merge instead of overwriting.\n"
        "   - Changed by the user: merge. Take the framework's structural\n"
        "     changes, keep every user addition, and state in the report what\n"
        "     you kept. The cases that actually come up:\n"
        f"{merge_cases}"
        "   - Retired (in the recorded `framework_files`, absent from the\n"
        "     reference): delete it, then grep the whole scaffold for its name\n"
        "     and remove the instructions that still point at it. A retired file\n"
        "     that stays referenced is worse than one that stays on disk.\n\n"
        "   Orphan test, for every file here that the reference does not have and\n"
        "   the recorded list does not name. On a pre-stamp scaffold that is every\n"
        "   such file, so this is the only thing standing between the project and\n"
        "   framework files that can never be retired. Do not guess from the\n"
        "   file's location or its contents; ask the generator whether it ever\n"
        "   emitted that path:\n\n"
        "       git -C \"$LLM_AGENT_HOME\" log --oneline -S'<file basename>' \\\n"
        "         -- init_agent.py\n\n"
        "   Commits found means the framework emitted this file and a later\n"
        "   version dropped it: it is orphaned framework output, so retire it like\n"
        "   any other retired file. No commits means the user wrote it: leave it\n"
        "   alone and do not mention it again. If `$LLM_AGENT_HOME` is not a git\n"
        "   checkout the test cannot run, so leave every candidate in place and\n"
        "   list them in the report as undecidable.\n\n"
        "4. Migrate hand-filled content in place; do not regenerate it. The\n"
        "   reference's stubs show the shape the new version expects, this\n"
        "   project's files hold the content. Where the shape changed, edit this\n"
        "   project's files:\n"
        f"{migrate}"
        "   If a new field cannot be derived from what the project already\n"
        "   records, leave it empty and list it in the report for the user.\n"
        "   Do not invent a value, and do not read the codebase to fill it:\n"
        "   that is /explore's job and it is not part of an update.\n"
        f"{regen}\n"
        "5. Verify before reporting success.\n"
        f"   - Every tool the instructions name exists and exits 0:\n"
        f"     {verify_tools}.\n"
        f"{verify_extra}"
        "   - AGENTS.md still holds this project's context between its\n"
        "     GENERATED markers, and the marker text matches the reference's.\n"
        "   - No instruction in the scaffold names a file that no longer exists.\n\n"
        "6. Record and report.\n"
        f"   - Write `{FRAMEWORK_JSON}` from the reference's copy: new version,\n"
        "     new file list, this project's name and profile.\n"
        "   - Print one row per file: added / updated / merged (with what was\n"
        "     kept) / retired / migrated / untouched, then anything left for the\n"
        "     user to decide.\n"
        "   - Commit `.ai` (`update: framework <old> -> <new>`). Leave the\n"
        "     host-repo files uncommitted for the user to review; this framework\n"
        "     never commits the host project repo.\n"
        "   - Delete the temp reference directory. Keep\n"
        "     `.ai/agent/.update-backup/` until the user confirms the result.\n\n"
        "Switching profile (small <-> large) is not an update: it is a deliberate\n"
        "re-init with `init-agent --size <profile>`. If this codebase has grown\n"
        "past the profile it was scaffolded for, say so in the report and let the\n"
        "user decide.\n\n"
        "With `dry-run`: do steps 1-3 as analysis only, print the table of what\n"
        "would change, and stop without writing anything. The backup and the\n"
        "pre-update commit are still worth doing.\n")


def render_tidy_up_body(size: str, harness: str, arg: str) -> str:
    """Body of the /tidy-up skill: a bounded hygiene sweep over the host code.

    Four passes with deliberately different authority. Removing dead code and
    rewriting comments or prose is reversible and locally verifiable, so the
    agent does it. Deleting a file is neither, so that pass only proposes. The
    rule the whole procedure serves: a tidy-up may not change behavior, so
    every pass is gated on the same test and lint baseline captured up front.

    Varies on both axes: the large profile has KB nodes whose `covers` globs
    can point at removed paths; the small profile has notes plus the
    project-context digest. Harness decides whether the survey fan-out and the
    review gate can run in sub-agents.
    """
    if harness == "claude":
        survey_note = (
            "   Dispatch the survey fan-out to sub-agents where the harness\n"
            "   supports them: each returns a candidate list with evidence, not\n"
            "   file dumps. Decide every removal yourself.\n")
        review_note = (
            "   Run the `reviewer` sub-agent on the full diff. If it cannot be\n"
            "   spawned, use a fresh general-purpose sub-agent given only the\n"
            "   diff and the rule that behavior must not change.\n")
    else:
        survey_note = (
            "   Survey with your read and search tools; keep raw file dumps out\n"
            "   of context by searching for evidence, not by reading whole trees.\n")
        review_note = (
            "   Re-read the full diff in a clean context against the rule that\n"
            "   behavior must not change, and note that no reviewer sub-agent\n"
            "   was available.\n")

    if size == "large":
        record = (
            "   Removing code can invalidate the KB. For every node whose\n"
            "   `covers` globs matched a removed path, update the node and its\n"
            f"   `manifest.yaml` entry, then run `python3 {TOOLS_DIR}/gen_index.py`.\n"
            "   Update the `GENERATED:project-context` module map only if a\n"
            "   module disappeared or was renamed.\n")
    else:
        record = (
            "   If a module disappeared or was renamed, update the module map in\n"
            "   the `GENERATED:project-context` section of AGENTS.md. Append any\n"
            "   durable finding to `.ai/notes.md`, for example a subsystem that\n"
            "   turned out to be unreachable.\n")

    return (
        "Tidy up this codebase without changing what it does. Scope (optional:\n"
        f"a path, module, or area; default is the whole repo): {arg}\n\n"
        "Four passes, in this order, so nothing is polished that is about to be\n"
        "removed. A tidy-up is a hygiene sweep, not a refactor: it may not\n"
        "change behavior, public API, or output. If a cleanup you want needs a\n"
        "behavior change, stop and write it up as a change spec instead.\n\n"
        "0. Baseline first. Confirm the worktree is clean, or ask the user\n"
        "   whether to proceed with pending edits. Run the project's build,\n"
        "   test, and lint commands and record the result. If they are already\n"
        "   failing, say so and stop: without a green baseline you cannot tell\n"
        "   your sweep from a pre-existing break. Note the current commit SHA.\n\n"
        "1. Dead code: remove it, with evidence.\n"
        "   Candidates: unreferenced private functions, types, and variables;\n"
        "   unused imports; unreachable branches; commented-out code blocks;\n"
        "   parameters no caller passes; feature-flag arms whose flag no longer\n"
        "   exists.\n"
        "   Evidence before every removal. Search the whole repo, not just the\n"
        "   source tree: tests, build files, CI config, packaging metadata,\n"
        "   templates, and docs. Check the dynamic-reference sites a plain\n"
        "   search misses, whichever apply to this ecosystem: reflection and\n"
        "   name-based lookup, plugin or command registries, dependency\n"
        "   injection, serialized field names, conditional compilation,\n"
        "   generated bindings, and entry points declared in packaging\n"
        "   manifests.\n"
        "   Decide first whether this repo is a library or an application. In a\n"
        "   library, an exported symbol is not dead merely because nothing in\n"
        "   this repo calls it; removing it is an API break, which this skill\n"
        "   does not do. Treat the public surface as used.\n"
        "   Where the ecosystem has a tool that reports unused code (a linter,\n"
        "   a compiler warning, a coverage report), run it and use its output as\n"
        "   a candidate list, then verify each hit yourself. A tool's verdict is\n"
        "   evidence, not authority.\n"
        "   When the evidence is ambiguous, do not remove it. Move it to the\n"
        "   proposal list in step 2 and let the user decide.\n"
        f"{survey_note}"
        "\n"
        "2. Obsolete files: propose, never delete.\n"
        "   Candidates: scripts nothing invokes, config for a tool the project\n"
        "   no longer uses, generated output committed by mistake, editor and\n"
        "   merge droppings (`.orig`, `.rej`, `.bak`), duplicated vendored\n"
        "   copies, and docs describing a removed feature.\n"
        "   Evidence: nothing references the path, no build, CI, or packaging\n"
        "   config names it (including by string), and its git history shows it\n"
        "   went quiet. All three, not one.\n"
        "   Never delete a file in this pass, and never mass-delete on a guess.\n"
        "   Report a table instead: path, why it looks obsolete, what breaks if\n"
        "   that is wrong, and your confidence. Let the user choose. Leave\n"
        "   licence files, CI config, and anything a packaging manifest names\n"
        "   out of the proposal unless the evidence is conclusive.\n\n"
        "3. Overlong comments: shorten to at most 1-2 lines.\n"
        "   Target the narrative blocks that restate what the code already\n"
        "   says. Shorten those to a single line, or delete them when the code\n"
        "   is clearer without.\n"
        "   Do not shorten, regardless of length: licence and copyright\n"
        "   headers, SPDX tags, generated-file banners, and API documentation\n"
        "   comments that are the published contract for a symbol.\n"
        "   A long comment that carries real information is not clutter. If it\n"
        "   explains why, records a non-obvious invariant, justifies a\n"
        "   workaround, or cites an algorithm or issue, keep the information:\n"
        "   compress it to 1-2 lines if it fits, otherwise move it into the\n"
        "   project's docs and leave a one-line pointer. Never delete knowledge\n"
        "   to satisfy a line count.\n\n"
        "4. Em dashes: remove them from prose.\n"
        "   Rewrite every em dash in source strings, comments, docs, and\n"
        "   markdown. Replace by clause, do not swap character for character: a\n"
        "   parenthetical pair becomes commas or parentheses, an abrupt break\n"
        "   becomes a colon or a full stop, a range becomes `to`. Read the\n"
        "   result back; if it no longer parses as a sentence, rewrite it.\n"
        "   Leave alone: test fixtures and golden or expected-output files,\n"
        "   vendored third-party sources, licence texts, data files, URLs, and\n"
        "   any string where the character is the data under test. Changing\n"
        "   those changes behavior, which this skill may not do.\n\n"
        "5. Verify and record.\n"
        "   Re-run the same build, test, and lint commands from step 0 and\n"
        "   compare against the recorded baseline. Any new failure means the\n"
        "   sweep broke something: fix it or revert that hunk. A golden-file\n"
        "   mismatch after pass 4 means you edited data, not prose.\n"
        f"{review_note}"
        f"{record}"
        "\n"
        "6. Report and hand over.\n"
        "   Print one section per pass: what was removed with the evidence, the\n"
        "   proposal table for files, the comments touched, and the em-dash\n"
        "   count. Commit `.ai` (`tidy-up: <scope>`). Leave the host-repo\n"
        "   changes uncommitted for the user to review; this framework never\n"
        "   commits the host project repo.\n\n"
        "Right-size the sweep. On a large repo, take the scope argument\n"
        "seriously and do one area at a time: a diff nobody can review is worse\n"
        "than untidy code. Keep the passes in separate commits-worth of changes\n"
        "so a reviewer can read them independently.\n")


def command_specs(harness: str, arg_focus: str, arg_ticket: str) -> list:
    """(name, description, body) for each command. Single source for both
    skill (claude) and prompt-file (copilot) rendering; the phase pointers
    keep the phase docs the single source of truth."""
    return [
        (
            "explore",
            "Run Phase 1 (Initialization): sample the codebase and build "
            "the .ai knowledge base",
            "Run Phase 1 (Initialization) of the project-aware agent framework.\n\n"
            f"Read `{PHASES_DIR}/init.md` first, before any other step, and follow\n"
            "it exactly. Outcome: filled KB nodes in `.ai/knowledgebase/`,\n"
            "regenerated `manifest.yaml` and `INDEX.md`, populated\n"
            "`GENERATED:project-context` section in `AGENTS.md`, and a coverage\n"
            "report.\n\n"
            f"{arg_focus}\n",
        ),
        (
            "add-ticket",
            "Store a ticket as markdown in the .ai/tickets/ inbox without "
            "planning it",
            f"Add a ticket to the inbox. Ticket id, title, description: {arg_ticket}\n\n"
            "1. Build the filename `<ID>-<slug>.md` from id and title, e.g.\n"
            "   `JIRA1234-do-this-and-that.md`.\n"
            "2. Write `.ai/tickets/<ID>-<slug>.md` with frontmatter `id`, `title`,\n"
            "   `status: new`, `created: <today>` and the description as body.\n"
            "   Ask for a one-line description if none was given.\n"
            '3. Commit the `.ai` repo (`add-ticket: <ID>`).\n\n'
            "Do not start planning or implementing; that begins with /plan <ID>,\n"
            "which moves the ticket into `.ai/knowledgebase/tasks/<ID>/` and\n"
            "promotes its status from `new` to `planned`.\n",
        ),
        (
            "plan",
            "Run Phase 2 (Planning): decompose an inbox ticket into "
            "self-contained task files with a review gate",
            f"Run Phase 2 (Planning) for ticket: {arg_ticket}\n\n"
            f"Read `{PHASES_DIR}/planning.md` first, before any other step, and\n"
            "follow it exactly, including the Q&A rounds and the plan-review gate.\n"
            "The ticket is in the `.ai/tickets/` inbox.\n",
        ),
        (
            "implement",
            "Run Phase 3 (Implementation): work a ticket's planned task "
            "files in order",
            f"Run Phase 3 (Implementation) for ticket: {arg_ticket}\n\n"
            f"Read `{PHASES_DIR}/implementation.md` first, before any other step,\n"
            "and follow it exactly. Load the ticket's `plan.md` and work the task\n"
            "files in order.\n",
        ),
        (
            "add-reference",
            "Register external material (repo, docs) under .ai/external/ "
            "with a references KB node",
            f"Register an external reference. Name and origin (git URL or local\n"
            f"path): {arg_ticket}\n\n"
            "1. Fetch the material into `.ai/external/<name>/`:\n"
            "   git URL or local git repo: `git clone --depth 1 <origin>`;\n"
            "   plain local folder: copy it.\n"
            "2. Ensure `.ai/.gitignore` contains `external/`.\n"
            "3. Create `.ai/knowledgebase/references/<name>.md` with frontmatter:\n"
            "   `id: references/<name>`, one-line `summary`,\n"
            "   `tags: [external, reference]`, `covers: []`, `tier: cold`,\n"
            "   `updated`, `origin`, `fetched: <today>`,\n"
            "   `pinned: <commit sha or n/a>`, `related: []`.\n"
            "   Body: local copy path, what the material answers, entry points.\n"
            "4. Append the node to `manifest.yaml`. `INDEX.md` regenerates via a\n"
            "   hook on the claude harness; on others run\n"
            f"   `python3 {TOOLS_DIR}/gen_index.py`.\n"
            '5. Commit the `.ai` repo (`add-reference: <name>`).\n\n'
            "Reminder: search raw copies with targeted queries; never bulk-load.\n",
        ),
        (
            "import-kb",
            "Import an existing knowledge base of any structure into the .ai KB: "
            "read, classify, and transform its docs into framework nodes",
            "Import an existing knowledge base into the `.ai` KB, regardless of\n"
            f"its source structure. Source (folder, file, or repo of docs, wiki,\n"
            f"or notes): {arg_ticket}\n\n"
            "This transforms curated knowledge INTO framework KB nodes. It is not\n"
            "/add-reference: that registers raw external material for targeted\n"
            "search without transforming it. If the source is upstream code or\n"
            "docs you only want to search later, use /add-reference instead.\n\n"
            "1. Survey the source without bulk-loading it into context: list the\n"
            "   tree and sample representative files (entry docs, READMEs, index\n"
            "   or TOC files) to learn its structure and content types. Run the\n"
            "   survey in a sub-agent where available; bring back a condensed map\n"
            "   (<=2000 tokens) of what topics exist, where, and in what shape.\n"
            "2. Classify each piece of source content into the target taxonomy:\n"
            "   architecture/ (structure, modules, data flow, entry points),\n"
            "   conventions/ (code style, testing, git workflow), domain/\n"
            "   (glossary, business rules), infra/ (build, CI/CD, deploy),\n"
            "   decisions/ (ADRs and rationale, append-only), references/\n"
            "   (pointers to external material; do not inline large bodies).\n"
            "   Operational gotchas, runbooks, and CI quirks go to `.ai/notes.md`,\n"
            "   not a node.\n"
            "3. Transform, do not copy verbatim. Synthesize each source topic into\n"
            "   telegraphic KB content under the node cap (~1500 tokens; split and\n"
            "   cross-link if larger), with full frontmatter (id, summary, tags,\n"
            "   covers globs, tier hot|cold, updated, related). Set `covers` by\n"
            "   matching source topics to real code paths. Merge into existing\n"
            "   nodes instead of duplicating; never create a second source of\n"
            "   truth.\n"
            "4. Record provenance: note the source origin (path or URL) in each\n"
            "   created or updated node so the transform is auditable.\n"
            "5. Update `manifest.yaml` for every new or changed node. `INDEX.md`\n"
            "   regenerates via a hook on the claude harness; on others run\n"
            f"   `python3 {TOOLS_DIR}/gen_index.py`. Regenerate the\n"
            "   GENERATED:project-context section of AGENTS.md if hot-tier nodes\n"
            "   changed.\n"
            "6. Report a mapping table: source item -> target node\n"
            "   (created/merged/skipped), and list anything you could not classify\n"
            "   for the user to decide.\n"
            "7. Do not delete or modify the source. Commit the `.ai` repo\n"
            "   (`import-kb: <source>`).\n\n"
            "If the source is itself a legacy `.ai/` (e.g. docs/ chapters plus a\n"
            "tasks/ tree), transform docs/ into nodes and ignore its task and\n"
            "ticket state.\n",
        ),
        (
            "import",
            "Migrate an existing .ai/ folder (older framework version or other "
            "layout) into the current structure: knowledge and lifecycle state",
            "Migrate an existing `.ai/` directory into the current large-profile\n"
            f"structure. Source `.ai/` (an older version of this framework, or a\n"
            f"differently-shaped agent folder): {arg_ticket}\n\n"
            "This converts a whole prior `.ai/` working directory - both the\n"
            "knowledge AND the lifecycle state - into the current layout. It is\n"
            "not /import-kb: that transforms arbitrary curated knowledge (a\n"
            "docs/wiki dump) into KB nodes and deliberately ignores task and\n"
            "ticket state. /import additionally carries the ticket, task, plan,\n"
            "decision, and notes state across. If the source is a docs/wiki dump\n"
            "rather than a `.ai/`-style working folder, use /import-kb instead.\n"
            "It is also not /update: that moves a scaffold this framework already\n"
            "wrote (one carrying `.ai/agent/framework.json`) to the current\n"
            "version in place. Use /update when the folder is a stamped scaffold\n"
            "of an earlier version, /import when it is unstamped or foreign.\n"
            "Run this after scaffolding, against a copy of the old folder: move\n"
            "the pre-existing `.ai/` aside (e.g. to `.ai.old/`) before init, then\n"
            "`/import .ai.old`.\n\n"
            "1. Survey without bulk-loading. List the source tree; sample its\n"
            "   entry points (`manifest.yaml`, `INDEX.md`, `AGENTS.md`,\n"
            "   `tickets/`, `knowledgebase/`, `changes/`, notes). Identify the\n"
            "   layout and roughly which framework version it is (large markers:\n"
            "   `knowledgebase/` + `manifest.yaml`; small markers: `changes/` +\n"
            "   `notes.md`, no manifest; foreign: neither). Run the survey in a\n"
            "   sub-agent where available; bring back a condensed map (<=2000\n"
            "   tokens) of what exists and where.\n"
            "2. Migrate the knowledge. For source content already in framework\n"
            "   node shape, upgrade it in place: remap each node into the six\n"
            "   categories (architecture/, conventions/, domain/, infra/,\n"
            "   decisions/, references/) and rewrite its frontmatter to the\n"
            "   current schema (id, summary, tags, covers globs, tier hot|cold,\n"
            "   updated, related), re-matching `covers` to real code paths. For\n"
            "   content not already node-shaped, apply the /import-kb\n"
            "   read->classify->transform protocol (synthesize telegraphic nodes\n"
            "   under the ~1500-token cap, dedup by merging, never a second source\n"
            "   of truth). Operational gotchas and runbooks route to\n"
            "   `.ai/notes.md`, not a node.\n"
            "3. Migrate the lifecycle state (what /import-kb drops):\n"
            "   - Inbox tickets -> `.ai/tickets/<ID>-<slug>.md`, frontmatter\n"
            "     preserved.\n"
            "   - Planned or in-progress tickets ->\n"
            "     `.ai/knowledgebase/tasks/<id>/` (ticket.md, plan.md,\n"
            "     NN-<slug>.md task files, kb-delta.yaml), preserving each task's\n"
            "     status (planned|in-progress|done|blocked) in frontmatter, not\n"
            "     folder names. Finished tickets ->\n"
            "     `.ai/knowledgebase/tasks/_archive/`.\n"
            "   - Decisions/ADRs -> `decisions/` nodes, append-only, keep the\n"
            "     rationale.\n"
            "   - External references -> `references/` nodes; if the source held\n"
            "     raw material under its own `external/`, copy it into\n"
            "     `.ai/external/<name>/` and ensure `.ai/.gitignore` lists\n"
            "     `external/`.\n"
            "   - `notes.md` / notes hub -> `.ai/notes.md` (+ leaves),\n"
            "     telegraphic.\n"
            "4. Regenerate, do not copy, the derived artifacts: append every\n"
            "   migrated node to `manifest.yaml` (INDEX.md regenerates via the\n"
            "   claude hook; on other harnesses run\n"
            f"   `python3 {TOOLS_DIR}/gen_index.py`), and regenerate the\n"
            "   GENERATED:project-context section of AGENTS.md from the migrated\n"
            "   hot-tier nodes rather than importing the old AGENTS.md text.\n"
            "   Never carry the source's INDEX.md or generated section over\n"
            "   verbatim, and never overwrite `.ai/agent/framework.json` with the\n"
            "   source's copy: init already stamped this scaffold at the current\n"
            "   version, and that stamp is what /update reads later.\n"
            "5. Record provenance: note the source origin in each migrated node so\n"
            "   the migration is auditable.\n"
            "6. Report a mapping table: source item -> target\n"
            "   (migrated/merged/skipped), and list anything you could not map for\n"
            "   the user to decide. Do not delete or modify the source. Commit the\n"
            "   `.ai` repo (`import: <source>`).\n\n"
            "Profile mismatch: if the source was a small-profile `.ai`\n"
            "(project-context + notes, no node store), promote its distilled facts\n"
            "into KB nodes here. Map the source's content onto this profile's\n"
            "targets; do not recreate the source's shape.\n",
        ),
        (
            "tidy-up",
            "Hygiene sweep that may not change behavior: remove dead code, "
            "propose obsolete files, shorten comments, drop em dashes",
            render_tidy_up_body("large", harness, arg_ticket),
        ),
        (
            "update",
            "Update this scaffold to the current framework version: merge the "
            "framework files, migrate the KB in place, never re-explore",
            render_update_body("large", harness, arg_ticket),
        ),
    ]


def command_specs_small(harness: str, arg_focus: str, arg_ticket: str) -> list:
    """(name, description, body) for the small-profile skills/prompt files:
    explore, spec, build. Self-contained (no phase-doc layer); rendered to both
    Agent Skills (claude) and prompt files (copilot)."""
    hook_offer = ""
    if harness == "claude":
        hook_offer = (
            "- Once the build/test/lint commands are known, offer the user a Stop\n"
            "  hook in `.claude/settings.json` that runs lint (and fast tests if\n"
            "  cheap) on turn end, so \"done = checks pass\" is a hard gate. Add it\n"
            "  only with consent; mention the lighter session-scoped alternative,\n"
            "  a `/goal` condition (e.g. \"tests and lint pass\") re-checked each\n"
            "  turn without touching settings.\n"
        )
    return [
        (
            "explore",
            "Explore the codebase and fill the AGENTS.md project context plus "
            ".ai/notes.md",
            "Explore this project to ground the agent.\n\n"
            "- Run the deterministic inventory first: `python3\n"
            f"  {TOOLS_DIR}/probe.py`. It prints host commit, language mix,\n"
            "  detected build/test/lint commands, a module map (files + LOC),\n"
            "  dependency manifests, and entry-point candidates. Seed the\n"
            "  mechanical project-context fields from it; use its map to sample.\n"
            "- Sample the code with your read/search tools (Read, Grep, Glob); do\n"
            "  not load everything. Read entry points, each area's public API, and\n"
            "  the tests. At this size the source is the knowledge base. Where the\n"
            "  harness supports sub-agents, dispatch the sampling fan-out to them:\n"
            "  each returns a condensed evidence map and keeps raw file dumps out\n"
            "  of this context. Write the digest yourself; never let a sub-agent\n"
            "  fill `AGENTS.md` or `notes.md` - digest errors compound across\n"
            "  every later session.\n"
            "- Fill the `GENERATED:project-context` section of `AGENTS.md`,\n"
            "  condensed (cap ~1500 tokens): one-line purpose, tech stack,\n"
            "  build/test/lint commands (highest priority), top conventions, a\n"
            "  one-line-per-area module map, and core glossary terms.\n"
            "- Ask the user about non-derivable knowledge (domain terms, unwritten\n"
            "  rules, ownership); record the answers in `.ai/notes.md` (if it is\n"
            "  already a hub with `.ai/notes/` leaves, read the hub first and\n"
            "  update the matching leaf).\n"
            f"{hook_offer}"
            "- Commit `.ai` (`explore: project context`).\n\n"
            f"{arg_focus}\n",
        ),
        (
            "spec",
            "Write a lightweight spec for a non-trivial change: goal, acceptance "
            "criteria, task checklist",
            f"Write a spec for a non-trivial change. Id and title: {arg_ticket}\n\n"
            "1. Read `.ai/notes.md` and explore the relevant code first.\n"
            "2. Run a short, bounded Q&A with the user until the acceptance\n"
            "   criteria are unambiguous. If no human is available (autonomous\n"
            "   run), resolve each open question from the evidence and record it\n"
            "   as a single numbered assumption in the spec Notes, then proceed.\n"
            "3. Write `.ai/changes/<id>/spec.md`:\n"
            "   ---\n"
            "   id: <id>\n"
            "   title: <title>\n"
            "   status: planned\n"
            "   created: <today>\n"
            "   ---\n"
            "   ## Goal               one paragraph: what and why\n"
            "   ## Acceptance criteria\n"
            "   - [ ] testable criterion\n"
            "   Cover ecosystem correctness, not just \"it runs\": where a linter\n"
            "   or policy check for the ecosystem you touch would catch a\n"
            "   wrong-but-working result (eslint, mypy/ruff, clippy, shellcheck,\n"
            "   lintian, a schema validator), name it and make passing it a\n"
            "   criterion.\n"
            "   ## Tasks\n"
            "   - [ ] task - files: <paths>\n"
            "   ## Notes              Q&A answers, decisions\n"
            "4. Commit `.ai` (`spec: <id>`).\n\n"
            "Do not implement yet; that is `/build <id>`. A change you can\n"
            "describe in one sentence touching one or two files needs no spec:\n"
            "edit it directly and update `.ai/notes.md` if a decision emerged.\n",
        ),
        (
            "build",
            "Implement a change's spec: work the task checklist, review the diff, "
            "finish",
            f"Implement a planned change. Id: {arg_ticket}\n\n"
            "1. Load `.ai/changes/<id>/spec.md`; set `status: in-progress`. Read\n"
            "   `.ai/notes.md`. Write `.ai/.current` (gitignored) with the change\n"
            "   id, the spec path, and the date, so the work can be resumed.\n"
            "2. Work the task checklist in order. Explore the real code with\n"
            "   read/search tools as needed; do not load the whole tree.\n"
            "3. Keep tests and lint green.\n"
            "4. Review gate: before declaring the change done, have the full diff\n"
            "   reviewed in a fresh context against the acceptance criteria. Run\n"
            "   the `reviewer` sub-agent where the harness supports sub-agents. If\n"
            "   it cannot be spawned (e.g. you are yourself a sub-agent) and no\n"
            "   human is available, spawn a fresh general-purpose sub-agent given\n"
            "   only the diff and the criteria; failing that, do a clean-context\n"
            "   self-review and note that the `reviewer` sub-agent was unavailable.\n"
            "   The review also cross-checks captured constraints: for each\n"
            "   build, test, or CI gotcha in `.ai/notes.md`, confirm the diff\n"
            "   honors it, not just that the acceptance criteria read as met.\n"
            "   Never skip the gate. Fix gaps that affect correctness or the\n"
            "   stated criteria; ignore style-only findings.\n"
            "5. Append any durable decision or gotcha to `.ai/notes.md`. If\n"
            "   `notes.md` has grown past ~1-2 screens, move topic clusters\n"
            "   (largest first) into `.ai/notes/<topic>.md`, each leaving a\n"
            "   linked one-line pointer (`- [topic](notes/<topic>.md) - hook`),\n"
            "   until the hub is back under ~1 screen, so later sessions read the\n"
            "   hub first and open only the leaves they need; do not split while\n"
            "   notes stay short. Then run the\n"
            "   project-context refresh so the always-loaded digest cannot\n"
            "   silently drift: re-run `python3\n"
            f"   {TOOLS_DIR}/probe.py` and compare its build/test/lint commands\n"
            "   and module map against the `GENERATED:project-context` section\n"
            "   of `AGENTS.md`. Update that section only for a changed command or\n"
            "   a new/removed/renamed module; a bare LOC delta on an existing\n"
            "   module is not actionable, leave it. Keep it under ~1500 tokens.\n"
            "   This is a bounded diff check, not a re-explore. One exception on\n"
            "   the LOC rule: if probe's `Code LOC` line exceeds ~10k, tell the\n"
            "   user this project has outgrown the small profile and propose\n"
            "   re-initializing as large (hand-filled content is preserved);\n"
            "   propose only, never migrate on your own. Last, if a\n"
            "   `.ai/notes/` hub exists, confirm every leaf is linked from\n"
            "   `notes.md` and every pointer resolves (no orphaned or dangling\n"
            "   leaves).\n"
            "6. Set `status: done`, delete `.ai/.current`, and commit `.ai`\n"
            "   (`build: <id>`).\n\n"
            "Escalate instead of improvising: on missing context, do bounded\n"
            "discovery then ask the user; if a test fails twice on the same task,\n"
            "stop and rethink the approach rather than make a third blind attempt.\n",
        ),
        (
            "import-kb",
            "Import an existing knowledge base of any structure into the small "
            "profile: distill it into the AGENTS.md project context and notes.md",
            "Import an existing knowledge base into the small-profile `.ai`,\n"
            f"regardless of source structure. Source (folder, file, or repo):\n"
            f"{arg_ticket}\n\n"
            "At this scale there is no KB node store; the targets are the\n"
            "GENERATED:project-context section of AGENTS.md and `.ai/notes.md`.\n\n"
            "1. Survey the source without bulk-loading it: list the tree and\n"
            "   sample entry/index files (sub-agent where available; bring back a\n"
            "   condensed map).\n"
            "2. Distill, do not copy. Fold stable, high-value facts (purpose, tech\n"
            "   stack, build/test/lint commands, top conventions, module map,\n"
            "   glossary) into the project-context section of AGENTS.md\n"
            "   (cap ~1500 tokens). Put operational gotchas, runbooks, decisions,\n"
            "   and domain terms into `.ai/notes.md` (append, telegraphic).\n"
            "3. If a body of material is large and only worth searching later (an\n"
            "   upstream repo or doc dump), clone or copy it into\n"
            "   `.ai/external/<name>/` and note it in `.ai/notes.md` instead of\n"
            "   inlining it.\n"
            "4. Report a short mapping: source -> project-context / notes.md /\n"
            "   external / skipped. Do not delete the source. Commit `.ai`\n"
            "   (`import-kb: <source>`).\n",
        ),
        (
            "import",
            "Migrate an existing .ai/ folder (older version or other layout) into "
            "the small profile: project-context, notes.md, and in-flight changes",
            "Migrate an existing `.ai/` directory into the current small-profile\n"
            f"structure. Source `.ai/` (an older version of this framework, or a\n"
            f"differently-shaped agent folder): {arg_ticket}\n\n"
            "This converts a whole prior `.ai/` working directory into the small\n"
            "profile. The small-profile targets are the GENERATED:project-context\n"
            "section of AGENTS.md, `.ai/notes.md`, and `.ai/changes/<id>/spec.md`\n"
            "for in-flight changes; there is no KB node store. It is not\n"
            "/import-kb: that transforms arbitrary curated knowledge (a docs/wiki\n"
            "dump) and ignores lifecycle state, whereas /import also carries\n"
            "ticket/change and notes state across. If the source is a docs/wiki\n"
            "dump rather than a `.ai/`-style working folder, use /import-kb. It\n"
            "is also not /update: that moves a scaffold this framework already\n"
            "wrote (one carrying `.ai/agent/framework.json`) to the current\n"
            "version in place. Use /update when the folder is a stamped scaffold\n"
            "of an earlier version, /import when it is unstamped or foreign. Run\n"
            "this after scaffolding, against a copy of the old folder (e.g. move\n"
            "the pre-existing `.ai/` aside to `.ai.old/` before init, then\n"
            "`/import .ai.old`).\n\n"
            "1. Survey without bulk-loading: list the source tree; sample its\n"
            "   entry/index files and any manifest, notes, `changes/`, `tickets/`,\n"
            "   `knowledgebase/` (sub-agent where available; bring back a\n"
            "   condensed map). Note whether the source was large (knowledgebase/\n"
            "   + manifest) or small.\n"
            "2. Distill knowledge, do not copy. Fold stable, high-value facts\n"
            "   (purpose, tech stack, build/test/lint commands, top conventions,\n"
            "   module map, glossary) into the project-context section of\n"
            "   AGENTS.md (cap ~1500 tokens); if the source was a large-profile\n"
            "   KB, distill its hot-tier nodes down, do not reproduce the node\n"
            "   store. Route operational gotchas, runbooks, decisions, and domain\n"
            "   terms to `.ai/notes.md` (append, telegraphic; use the notes hub if\n"
            "   it grows).\n"
            "3. Migrate lifecycle state: unfinished tickets or changes ->\n"
            "   `.ai/changes/<id>/spec.md` (goal, acceptance criteria, task\n"
            "   checklist, status preserved); finished ones ->\n"
            "   `.ai/changes/_archive/`. A large body worth only searching later\n"
            "   -> clone or copy into `.ai/external/<name>/` and note it in\n"
            "   `.ai/notes.md` instead of inlining it.\n"
            "4. Regenerate, do not copy: refresh project-context from the migrated\n"
            "   facts, not the old AGENTS.md text. Never overwrite\n"
            "   `.ai/agent/framework.json` with the source's copy: init already\n"
            "   stamped this scaffold at the current version, and that stamp is\n"
            "   what /update reads later. Report a short mapping (source\n"
            "   -> project-context / notes.md / changes / external / skipped). Do\n"
            "   not delete the source. Commit `.ai` (`import: <source>`).\n",
        ),
        (
            "tidy-up",
            "Hygiene sweep that may not change behavior: remove dead code, "
            "propose obsolete files, shorten comments, drop em dashes",
            render_tidy_up_body("small", harness, arg_ticket),
        ),
        (
            "update",
            "Update this scaffold to the current framework version: merge the "
            "framework files, migrate notes and specs, never re-explore",
            render_update_body("small", harness, arg_ticket),
        ),
    ]


# Shown by the harness next to /name completion; also documents the expected
# arguments for each skill.
ARG_HINTS = {
    "explore": "[focus]",
    "add-ticket": "<id> <title...>",
    "plan": "<ticket-id>",
    "implement": "<ticket-id>",
    "add-reference": "<name> <origin>",
    "import-kb": "<source>",
    "import": "<source>",
    "spec": "<id> <title...>",
    "build": "<id>",
    "tidy-up": "[scope]",
    "update": "[dry-run]",
}


def render_skills(specs) -> dict:
    """Agent Skills (SKILL.md, open standard): .claude/skills/<name>/SKILL.md.
    Read by Claude Code and other SKILL.md-compatible harnesses. Every skill is
    a user-sequenced pipeline step with side effects (KB writes, code changes,
    `.ai` commits), so `disable-model-invocation: true` keeps the model from
    auto-triggering them mid-conversation; only an explicit /name invokes them.
    `specs` is a command_specs list (full or small profile)."""
    out = {}
    for name, desc, body in specs:
        hint = ARG_HINTS.get(name)
        hint_line = f"argument-hint: \"{hint}\"\n" if hint else ""
        out[f"{name}/SKILL.md"] = (
            "---\n"
            f"name: {name}\n"
            f'description: "{desc}"\n'
            f"{hint_line}"
            "disable-model-invocation: true\n"
            "---\n"
            f"{body}"
        )
    return out


def render_prompt_files(specs) -> dict:
    """Copilot prompt files: .github/prompts/<name>.prompt.md, VS Code only.
    `specs` is a command_specs list (full or small profile)."""
    out = {}
    for name, desc, body in specs:
        out[f"{name}.prompt.md"] = (
            "---\n"
            f'description: "{desc}"\n'
            "mode: agent\n"
            "---\n"
            f"{body}"
        )
    return out


def render_reviewer_agent(small: bool = False) -> str:
    if small:
        desc = ("Adversarial fresh-context review of a change's diff against "
                "its acceptance criteria. Use for the review gate in /build.")
        input_block = (
            "Input: a code diff plus the change's acceptance criteria in\n"
            "`.ai/changes/<id>/spec.md`."
        )
        coverage = ("- Every acceptance criterion is implemented and, where "
                    "testable, tested.\n"
                    "- The spec is self-contained: paths explicit, interfaces "
                    "stated.")
    else:
        desc = ("Adversarial fresh-context review of a plan or diff against "
                "acceptance criteria. Use for the plan-review gate (Phase 2) "
                "and the ticket review gate (Phase 3).")
        input_block = (
            "Input: a plan (`.ai/knowledgebase/tasks/<id>/plan.md` plus its "
            "task files)\nor a code diff, plus the ticket's acceptance "
            "criteria\n(`.ai/knowledgebase/tasks/<id>/ticket.md`)."
        )
        coverage = ("- Every acceptance criterion is covered by a task (plan) "
                    "or implemented and\n  tested (diff).\n"
                    "- Task files are self-contained: paths explicit, "
                    "interfaces stated.")
    return f"""---
name: reviewer
description: {desc}
tools: Read, Grep, Glob, Bash
---
You review work you did not produce. You see only the artifact and the
acceptance criteria, never the reasoning that produced it. Evaluate the
result on its own terms.

{input_block}

Check:
{coverage}
- Nothing outside the stated scope changed.
- Stated edge cases have tests.
- For build, CI, or packaging config you cannot run here: reason about whether
  it would actually build or run: required toolchain/compiler versions, and
  whether declared dependencies exist in the target distro/registry, not just
  whether the files are well-formed.

Report only gaps that affect correctness or the stated requirements, with
file and line references. Do not report style preferences. If the work is
sound, say so plainly; do not invent findings to have something to report.
"""


def render_hook_protect_generated() -> str:
    return f'''#!/usr/bin/env python3
"""PreToolUse hook: block direct writes to generated files.

INDEX.md is generated from manifest.yaml, and marked rule files under
.claude/rules/ are generated from conventions KB nodes; direct edits would
silently diverge. Hand-written rule files (no marker) stay editable. Exit 2
blocks the tool call and tells the agent the fix.
"""
import json
import sys
from pathlib import Path

MARKER = "{RULES_MARKER}"

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = str((data.get("tool_input") or {{}}).get("file_path", "")).replace("\\\\", "/")
if path.endswith(".ai/knowledgebase/INDEX.md"):
    print(
        "INDEX.md is generated. Edit .ai/knowledgebase/manifest.yaml, then "
        "run: python3 {TOOLS_DIR}/gen_index.py",
        file=sys.stderr,
    )
    sys.exit(2)
if "/.claude/rules/" in f"/{{path}}" and path.endswith(".md"):
    try:
        existing = Path(path).read_text(encoding="utf-8")
    except OSError:
        existing = ""
    if MARKER in existing:
        print(
            "This rule file is generated from a conventions KB node. Edit "
            "the node under .ai/knowledgebase/conventions/, then run: "
            "python3 {TOOLS_DIR}/gen_rules.py (a hook also does this "
            "automatically).",
            file=sys.stderr,
        )
        sys.exit(2)
sys.exit(0)
'''


def render_hook_ai_repo_clean() -> str:
    return '''#!/usr/bin/env python3
"""Stop hook: block ending the turn while .ai has uncommitted changes.

Enforces the AGENTS.md protocol rule "commit .ai after changing it"
deterministically. Exit 2 feeds the message back to the agent, which
commits and ends the turn cleanly. stop_hook_active guards against loops.
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

if data.get("stop_hook_active"):
    sys.exit(0)  # second pass; let the turn end even if still dirty

if not Path(".ai/.git").is_dir():
    sys.exit(0)

r = subprocess.run(
    ["git", "-C", ".ai", "status", "--porcelain"],
    capture_output=True, text=True,
)
if r.returncode == 0 and r.stdout.strip():
    print(
        "Uncommitted .ai changes. Commit them now: "
        'git -C .ai add -A && git -C .ai commit -m "<short summary>"',
        file=sys.stderr,
    )
    sys.exit(2)
sys.exit(0)
'''


def render_hook_regen_index() -> str:
    return '''#!/usr/bin/env python3
"""PostToolUse hook: keep generated KB artifacts in sync.

- manifest.yaml written  -> regenerate INDEX.md (gen_index.py) and the
  path-scoped rules (gen_rules.py; covers/tier live in the manifest)
- conventions node written -> regenerate the path-scoped rules only

Regenerating deterministically removes the "remember to run gen_*"
instructions from the phase docs. Non-blocking: the triggering write already
succeeded, so this only keeps the generated views in sync. Always exits 0.
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = str((data.get("tool_input") or {}).get("file_path", "")).replace("\\\\", "/")
is_manifest = path.endswith(".ai/knowledgebase/manifest.yaml")
is_convention = (".ai/knowledgebase/conventions/" in path
                 and path.endswith(".md"))
if not (is_manifest or is_convention):
    sys.exit(0)

jobs = []
if is_manifest:
    jobs.append(("INDEX.md", Path(".ai/agent/tools/gen_index.py")))
jobs.append((".claude/rules", Path(".ai/agent/tools/gen_rules.py")))

for label, gen in jobs:
    if not gen.exists():
        continue
    r = subprocess.run([sys.executable, str(gen)], capture_output=True, text=True)
    msg = (r.stdout or r.stderr).strip()
    if msg:
        print(f"{label} regenerated: {msg}", file=sys.stderr)
sys.exit(0)
'''


# Shared by gen_index.py and check_stale.py; manifest.yaml is regular enough
# (generated by this script family) that a line parser beats a yaml dependency.
_MANIFEST_PARSER = '''
def parse_manifest(text: str):
    """Parse the flat, regular manifest.yaml written by init/the agent."""
    project, nodes, cur, in_nodes = "", [], None, False
    for line in text.splitlines():
        if line.startswith("project:"):
            project = line.split(":", 1)[1].strip()
        elif line.startswith("nodes:"):
            in_nodes = True
        elif in_nodes:
            s = line.strip()
            if s.startswith("- id:"):
                cur = {"id": s.split(":", 1)[1].strip()}
                nodes.append(cur)
            elif cur is not None and line.startswith("    ") and ":" in s:
                k, v = s.split(":", 1)
                cur[k.strip()] = v.strip()
    return project, nodes


def parse_yaml_list(value: str) -> list:
    return [
        item.strip().strip("\\"").strip("'")
        for item in value.strip().strip("[]").split(",")
        if item.strip().strip("\\"")
    ]
'''


def render_tool_gen_index() -> str:
    return f'''#!/usr/bin/env python3
"""Regenerate .ai/knowledgebase/INDEX.md from manifest.yaml.

Deterministic; run this instead of editing INDEX.md by hand (a hook blocks
direct edits). Usage: python3 {TOOLS_DIR}/gen_index.py
"""
import sys
from pathlib import Path

KB = Path(__file__).resolve().parents[2] / "knowledgebase"

{_MANIFEST_PARSER}

def main() -> int:
    manifest = KB / "manifest.yaml"
    if not manifest.exists():
        print(f"not found: {{manifest}}", file=sys.stderr)
        return 1
    project, nodes = parse_manifest(manifest.read_text(encoding="utf-8"))
    lines = [
        f"# Knowledge Base Index: {{project}}",
        "",
        "<!-- GENERATED from manifest.yaml by gen_index.py. Do not edit. -->",
        "",
        "| Node | Tier | Load when |",
        "|---|---|---|",
    ]
    for n in sorted(nodes, key=lambda n: n.get("path", "")):
        lines.append(
            f"| `{{n.get('path', '')}}` | {{n.get('tier', '')}}"
            f" | {{n.get('summary', '')}} |"
        )
    (KB / "INDEX.md").write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print(f"wrote {{KB / 'INDEX.md'}} ({{len(nodes)}} nodes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def render_tool_check_stale() -> str:
    return f'''#!/usr/bin/env python3
"""List stale KB nodes: nodes whose `covers` globs match files changed in
the host repo since the node's `updated` date.

Usage: python3 {TOOLS_DIR}/check_stale.py   (from the project root or anywhere)
Exit code 1 when stale nodes were found (CI-friendly), else 0.

Glob matching uses fnmatch (`*` crosses `/`), checked against the full path
and the basename, so `src/**`, `*.toml` and `Makefile` all behave as expected.
"""
import fnmatch
import subprocess
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[2]
KB = AI / "knowledgebase"
ROOT = AI.parent

{_MANIFEST_PARSER}

def changed_since(date: str, cache: dict) -> list:
    """Files touched by commits strictly after the given day. Bare dates in
    git --since resolve to the current time of day; pin to end of day so a
    node is never stale on the day it was updated."""
    if date not in cache:
        r = subprocess.run(
            ["git", "log", f"--since={{date}} 23:59:59", "--name-only",
             "--pretty=format:"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"git log failed: {{r.stderr.strip()}}", file=sys.stderr)
            sys.exit(2)
        cache[date] = sorted({{
            line.strip() for line in r.stdout.splitlines() if line.strip()
        }})
    return cache[date]


def main() -> int:
    manifest = KB / "manifest.yaml"
    if not manifest.exists():
        print(f"not found: {{manifest}}", file=sys.stderr)
        return 2
    _, nodes = parse_manifest(manifest.read_text(encoding="utf-8"))
    cache, stale = {{}}, []
    for n in nodes:
        covers = parse_yaml_list(n.get("covers", ""))
        updated = n.get("updated", "")
        if not covers or not updated:
            continue
        hits = sorted({{
            f for f in changed_since(updated, cache) for g in covers
            if fnmatch.fnmatch(f, g) or fnmatch.fnmatch(Path(f).name, g)
        }})
        if hits:
            stale.append((n.get("id", "?"), updated, hits))
    if not stale:
        print("OK: no stale nodes")
        return 0
    for node_id, updated, hits in stale:
        sample = ", ".join(hits[:5]) + (" ..." if len(hits) > 5 else "")
        print(f"STALE {{node_id}} (updated {{updated}}): {{sample}}")
    print(f"{{len(stale)}} stale node(s). Refresh them and bump `updated`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
'''


RULES_MARKER = "by gen_rules.py. Edit the source node, not this file."


def render_tool_gen_rules() -> str:
    return f'''#!/usr/bin/env python3
"""Regenerate path-scoped Claude Code rules from conventions KB nodes.

Cold `conventions/*` nodes with non-empty `covers` globs render to
`.claude/rules/<id>.md` with `paths:` frontmatter, so the harness injects the
convention deterministically whenever matching files are touched, with no manifest
lookup by the model needed. Hot nodes are excluded (already embedded in the
AGENTS.md project-context section); nodes without `covers` cannot be
path-scoped and stay on the manifest protocol.

The rule files are build artifacts: a marker line tags them, stale ones are
deleted on regeneration, and a PreToolUse hook blocks direct edits. Claude
harness only; on others the manifest protocol covers conventions.

Usage: python3 {TOOLS_DIR}/gen_rules.py
"""
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[2]
KB = AI / "knowledgebase"
RULES = AI.parent / ".claude" / "rules"
MARKER = "{RULES_MARKER}"

{_MANIFEST_PARSER}

def node_body(path: Path) -> str:
    """Node content without its frontmatter block."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\\n")
    return text


def main() -> int:
    manifest = KB / "manifest.yaml"
    if not manifest.exists():
        print(f"not found: {{manifest}}", file=sys.stderr)
        return 1
    _, nodes = parse_manifest(manifest.read_text(encoding="utf-8"))
    written = set()
    for n in nodes:
        node_id = n.get("id", "")
        covers = parse_yaml_list(n.get("covers", ""))
        if (not node_id.startswith("conventions/")
                or n.get("tier") != "cold" or not covers):
            continue
        src = KB / n.get("path", "")
        if not src.exists():
            continue
        name = node_id.replace("/", "-") + ".md"
        paths = ", ".join(f'"{{g}}"' for g in covers)
        RULES.mkdir(parents=True, exist_ok=True)
        (RULES / name).write_text(
            "---\\n"
            f"paths: [{{paths}}]\\n"
            "---\\n"
            f"<!-- GENERATED from .ai/knowledgebase/{{n.get('path', '')}} "
            f"{{MARKER}} -->\\n\\n"
            + node_body(src),
            encoding="utf-8",
        )
        written.add(name)
        print(f"wrote {{RULES / name}}")
    # Remove generated rules whose node vanished or lost its covers/cold tier.
    if RULES.is_dir():
        for f in RULES.glob("*.md"):
            if f.name not in written and MARKER in f.read_text(encoding="utf-8"):
                f.unlink()
                print(f"removed stale {{f}}")
    if not written:
        print("no cold conventions nodes with covers; nothing to render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def render_tool_probe() -> str:
    # Plain string (not f-string): the script is full of braces and its own
    # f-strings; the tool path is hardcoded to keep it readable.
    return r'''#!/usr/bin/env python3
"""Deterministic repo inventory for Phase 1 (Initialization).

Prints a compact, stable-sorted Markdown snapshot of the host project so the
agent can seed the mechanical project-context fields (stack, build/test/lint
commands, module map) without spending tokens on discovery, and sample the tree
instead of scanning it. Read-only; stdlib only.

Usage: python3 .ai/agent/tools/probe.py   (from anywhere)
"""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2].parent  # host repo root (above .ai/)
TOP_LANGS = 12
TOP_DIRS = 20
TOP_ENTRIES = 20

LANGS = {
    ".py": "Python", ".rs": "Rust", ".go": "Go", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".java": "Java", ".kt": "Kotlin", ".rb": "Ruby",
    ".php": "PHP", ".c": "C", ".h": "C/C++ header", ".hpp": "C++ header",
    ".cpp": "C++", ".cc": "C++", ".cs": "C#", ".swift": "Swift",
    ".scala": "Scala", ".sh": "Shell", ".bash": "Shell", ".sql": "SQL",
    ".md": "Markdown", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".json": "JSON", ".html": "HTML", ".css": "CSS", ".scss": "CSS",
}
DEP_MANIFESTS = [
    "package.json", "Cargo.toml", "go.mod", "pyproject.toml", "setup.cfg",
    "setup.py", "requirements.txt", "tox.ini", "Gemfile", "Rakefile",
    "pom.xml", "build.gradle", "composer.json", "Makefile", "CMakeLists.txt",
    "snapcraft.yaml", "package.xml", "Dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "compose.yml", "compose.yaml",
]
# Manifests that live below the repo root (checked against relative paths).
NESTED_MANIFESTS = ["snap/snapcraft.yaml", "debian/control"]


def run(args):
    try:
        r = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr
    except OSError:
        return 1, "", ""


def tracked_files():
    """git ls-files: deterministic + gitignore-aware. Fallback: os.walk."""
    code, out, _ = run(["git", "ls-files"])
    if code == 0 and out.strip():
        return [ROOT / line for line in out.splitlines() if line.strip()]
    files = []
    for p in ROOT.rglob("*"):
        if p.is_file() and "/.git/" not in str(p):
            files.append(p)
    return files


def host_sha():
    code, out, _ = run(["git", "rev-parse", "HEAD"])
    return out.strip() if code == 0 and out.strip() else "n/a (not a git repo)"


def loc(path):
    try:
        with path.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def read(name):
    try:
        return (ROOT / name).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect_commands(names, rels):
    """names = basenames at repo root; rels = all tracked paths, relative,
    forward-slashed (for manifests that live below the root)."""
    out = []
    if "package.json" in names:
        try:
            scripts = json.loads(read("package.json")).get("scripts", {})
        except ValueError:
            scripts = {}
        if scripts:
            out.append(("package.json scripts",
                        ["npm run " + k for k in sorted(scripts)]))
    if "Cargo.toml" in names:
        out.append(("Cargo", ["cargo build", "cargo test", "cargo clippy"]))
    if "go.mod" in names:
        out.append(("Go", ["go build ./...", "go test ./..."]))
    if names & {"pyproject.toml", "setup.cfg", "tox.ini", "setup.py"}:
        out.append(("Python", ["(see pyproject.toml / tox.ini for test+lint)"]))
    if names & {"Gemfile", "Rakefile"}:
        out.append(("Ruby", ["rake", "rspec"]))
    if "Makefile" in names:
        targets = sorted(set(
            re.findall(r"(?m)^([A-Za-z0-9_.-]+):(?!=)", read("Makefile"))))
        targets = [t for t in targets if t.lower() != ".phony"]
        if targets:
            out.append(("Makefile targets",
                        ["make " + t for t in targets[:15]]))
    ros_pkgs = sorted(r for r in rels
                      if r == "package.xml" or r.endswith("/package.xml"))
    if ros_pkgs and any(k in read(r) for r in ros_pkgs[:5]
                        for k in ("ament", "catkin")):
        out.append(("ROS 2 / colcon", [
            "rosdep install --from-paths . --ignore-src -y",
            "colcon build", "colcon test", "colcon test-result --verbose"]))
    repos_files = sorted(r for r in rels if r.endswith(".repos"))
    if repos_files:
        out.append(("vcstool", ["vcs import < " + f
                                for f in repos_files[:3]] + ["vcs pull"]))
    if "snapcraft.yaml" in names or "snap/snapcraft.yaml" in rels:
        out.append(("Snapcraft", ["snapcraft pack"]))
    if "debian/control" in rels or "debian/rules" in rels:
        out.append(("Debian packaging",
                    ["dpkg-buildpackage -us -uc -b", "lintian"]))
    dockerfiles = sorted(r for r in rels
                         if r == "Dockerfile" or r.endswith("/Dockerfile"))
    if dockerfiles:
        out.append(("Docker", [
            "docker build " + (f[:-len("Dockerfile")] or ".")
            for f in dockerfiles[:3]]))
    if names & {"docker-compose.yml", "docker-compose.yaml",
                "compose.yml", "compose.yaml"}:
        out.append(("Docker Compose",
                    ["docker compose build", "docker compose up -d"]))
    workflows = sorted(r for r in rels
                       if r.startswith(".github/workflows/")
                       and r.endswith((".yml", ".yaml")))
    if workflows:
        shown = workflows[:5]
        if len(workflows) > 5:
            shown.append("+" + str(len(workflows) - 5) + " more")
        out.append(("GitHub Actions (CI gates)", shown))
    return out


ENTRY_BASENAMES = ("main.", "index.", "app.", "__main__.py", "cli.")
ENTRY_PREFIXES = ("cmd/", "bin/", "src/main", "src/bin/")

# Code-only subset of LANGS for the total-LOC line: docs, data, and markup are
# excluded so the number matches the size-profile boundary (~10k LOC).
NON_CODE_EXTS = {".md", ".yaml", ".yml", ".toml", ".json",
                 ".html", ".css", ".scss"}


def main():
    files = tracked_files()
    names_at_root = {p.name for p in files if p.parent == ROOT}
    rel_paths = set()
    exts = Counter()
    dir_files = defaultdict(int)
    dir_loc = defaultdict(int)
    code_loc = 0
    entries = []
    for p in files:
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            continue
        rels = str(rel).replace("\\", "/")
        rel_paths.add(rels)
        seg = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        dir_files[seg] += 1
        ext = p.suffix.lower()
        if ext in LANGS:
            exts[LANGS[ext]] += 1
            n = loc(p)
            dir_loc[seg] += n
            if ext not in NON_CODE_EXTS:
                code_loc += n
        base = p.name
        if base.startswith(ENTRY_BASENAMES) or rels.startswith(ENTRY_PREFIXES):
            entries.append(rels)

    lines = ["# Repo inventory (probe.py)", ""]
    lines.append("- Host commit: " + host_sha())
    lines.append("- Tracked files: " + str(len(files)))
    lines.append("- Code LOC (docs/data/markup excluded): " + str(code_loc)
                 + " (size-profile boundary ~10k)")
    lines.append("")

    lines += ["## Languages", "", "| Language | Files |", "|---|---|"]
    for lang, n in exts.most_common(TOP_LANGS):
        lines.append("| " + lang + " | " + str(n) + " |")
    lines.append("")

    cmds = detect_commands(names_at_root, rel_paths)
    lines += ["## Build / test / lint (detected)", ""]
    if cmds:
        for tool, cs in cmds:
            lines.append("- **" + tool + "**: " + "; ".join(cs))
    else:
        lines.append("- none detected (ask the user)")
    lines.append("")

    lines += ["## Module map (top-level, by LOC)", "",
              "| Path | Files | LOC |", "|---|---|---|"]
    ranked = sorted(dir_files, key=lambda d: (-dir_loc[d], d))[:TOP_DIRS]
    for d in ranked:
        lines.append("| " + d + " | " + str(dir_files[d]) + " | "
                     + str(dir_loc[d]) + " |")
    lines.append("")

    deps = sorted(names_at_root & set(DEP_MANIFESTS))
    deps += [m for m in NESTED_MANIFESTS if m in rel_paths]
    lines += ["## Dependency manifests", "",
              (", ".join(deps) if deps else "none at repo root"), ""]

    lines += ["## Entry-point candidates", ""]
    if entries:
        for e in sorted(set(entries))[:TOP_ENTRIES]:
            lines.append("- " + e)
    else:
        lines.append("- none matched (inspect the module map)")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def render_settings_json(small: bool = False) -> str:
    """Project settings (.claude/settings.json): a read-only permission allow
    list so exploration runs without a prompt per command, plus hooks that
    enforce protocol rules deterministically. Compound commands (a && b) prompt
    unless every part of the chain matches a rule, so common chain members (cd,
    echo, pwd, read-only git) are included as well. The small profile omits the
    KB tools and the INDEX-protection hook; neither exists there."""
    allow = [
        "Bash(cd:*)",
        "Bash(pwd:*)",
        "Bash(echo:*)",
        "Bash(ls:*)",
        "Bash(tree:*)",
        "Bash(cat:*)",
        "Bash(head:*)",
        "Bash(tail:*)",
        "Bash(wc:*)",
        "Bash(grep:*)",
        "Bash(rg:*)",
        "Bash(find:*)",
        "Bash(awk:*)",
        "Bash(sort:*)",
        "Bash(uniq:*)",
        "Bash(cut:*)",
        "Bash(tr:*)",
        "Bash(which:*)",
        "Bash(file:*)",
        "Bash(stat:*)",
        "Bash(git status:*)",
        "Bash(git log:*)",
        "Bash(git diff:*)",
        "Bash(git show:*)",
        "Bash(git branch:*)",
        "Bash(git -C .ai:*)",
        f"Bash(python3 {TOOLS_DIR}/probe.py:*)",
    ]
    if not small:
        allow += [
            f"Bash(python3 {TOOLS_DIR}/gen_index.py:*)",
            f"Bash(python3 {TOOLS_DIR}/check_stale.py:*)",
            f"Bash(python3 {TOOLS_DIR}/gen_rules.py:*)",
        ]
    hooks = {}
    if not small:
        hooks["PreToolUse"] = [
            {
                "matcher": "Write|Edit|MultiEdit",
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python3 "$CLAUDE_PROJECT_DIR/'
                                   '.claude/hooks/protect_generated.py"',
                    }
                ],
            }
        ]
        hooks["PostToolUse"] = [
            {
                "matcher": "Write|Edit|MultiEdit",
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python3 "$CLAUDE_PROJECT_DIR/'
                                   '.claude/hooks/regen_index.py"',
                    }
                ],
            }
        ]
        hooks["SessionStart"] = [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python3 "$CLAUDE_PROJECT_DIR/'
                                   f'{TOOLS_DIR}/check_stale.py" || true',
                    }
                ],
            }
        ]
    hooks["Stop"] = [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": 'python3 "$CLAUDE_PROJECT_DIR/'
                               '.claude/hooks/ai_repo_clean.py"',
                }
            ],
        }
    ]
    settings = {"permissions": {"allow": allow}, "hooks": hooks}
    return json.dumps(settings, indent=2) + "\n"


# ------------------------------------------------------------------ helpers

# Every framework-owned path this run writes, absolute. Recorded in
# framework.json so /update can diff a project's list against a fresh
# reference render and see exactly which files a newer version retired.
# One scaffold runs per process, so a module-level list is enough; each
# scaffold_* entry point clears it first.
_framework_paths: list = []


def write(path: Path, content: str, force: bool, created: list, skipped: list):
    """Framework-owned files (phase docs, skills, hooks, settings): the
    overwrite confirmation (force) regenerates them."""
    _framework_paths.append(path)
    if path.exists() and not force:
        skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)


def render_framework_json(root: Path, name: str, size: str,
                          harness: str) -> str:
    """The scaffold's version stamp: which framework revision built it, under
    which profile/harness, and every framework-owned path it emitted. /update
    reads this to know what to compare, migrate, and retire; without it an
    update can only overwrite blindly. Call after all other writes."""
    files = sorted({str(p.relative_to(root)) for p in _framework_paths}
                   | {FRAMEWORK_JSON})
    return json.dumps({
        "framework_version": FRAMEWORK_VERSION,
        "profile": size,
        "harness": harness,
        "project": name,
        "generated": TODAY,
        "framework_files": files,
    }, indent=2) + "\n"


def write_owned(path: Path, stub: str, created: list, skipped: list,
                preserved: list):
    """Agent/user-owned content (KB nodes, manifest, INDEX): write once.
    Existing content that differs from the stub is never overwritten, not
    even on overwrite-confirm; hand-filled knowledge must survive re-init."""
    if path.exists():
        if path.read_text(encoding="utf-8") == stub:
            skipped.append(path)
        else:
            preserved.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stub, encoding="utf-8")
    created.append(path)


def extract_generated(root: Path) -> str:
    """Recover an existing GENERATED:project-context section so re-init never
    reverts Phase 1 output. Checks AGENTS.md first, then legacy locations."""
    for rel in ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"):
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Marker text changed over versions; match on the stable prefix.
        begin = text.find("<!-- BEGIN GENERATED:project-context")
        if begin == -1:
            continue
        begin = text.find("-->", begin)
        end = text.find(GEN_END)
        if begin == -1 or end == -1 or end <= begin:
            continue
        body = text[begin + len("-->"):end].strip("\n")
        if body and "Populated in Phase 1" not in body:
            return body
    return None


def report(root: Path, created: list, skipped: list, preserved: list):
    for p in created:
        print(f"created   {p.relative_to(root)}")
    for p in skipped:
        print(f"skipped   {p.relative_to(root)} (exists)")
    for p in preserved:
        print(f"preserved {p.relative_to(root)} (hand-filled, not overwritten)")


def ask(text: str, default: str = "") -> str:
    """Interactive prompt with default. Returns the default without prompting
    when stdin is not a terminal (scripted/CI use)."""
    if not sys.stdin.isatty():
        return default
    suffix = f" [{default}]" if default else " (Enter to skip)"
    try:
        return input(f"{text}{suffix}: ").strip() or default
    except EOFError:
        return default


def ask_choice(text: str, options: list, default: str) -> str:
    """Numbered selection prompt: pick by number or name, Enter = default.
    Returns the default without prompting when stdin is not a terminal."""
    if not sys.stdin.isatty():
        return default
    print(f"{text}:")
    for i, opt in enumerate(options, 1):
        mark = "  (default)" if opt == default else ""
        print(f"  {i}) {opt}{mark}")
    while True:
        try:
            raw = input(f"Select [Enter = {default}]: ").strip().lower()
        except EOFError:
            return default
        if not raw:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        print(f"  invalid choice: {raw}")


# ----------------------------------------------------------------------- git

def run_git(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def ensure_gitignore(root: Path):
    """Exclude .ai/ from the host project's repo (only if root is a git repo)."""
    if not (root / ".git").exists():
        return
    gitignore = root / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    if any(line.strip().lstrip("/").rstrip("/") == ".ai" for line in lines):
        return
    content = "\n".join(lines).rstrip("\n")
    content = (content + "\n" if content else "") + ".ai/\n"
    gitignore.write_text(content, encoding="utf-8")
    print(f"updated  {gitignore.relative_to(root)} (+ .ai/)")


def ensure_ai_gitignore(root: Path):
    """Keep volatile working state out of .ai's own repo: raw external copies
    (re-fetchable, would bloat KB history), the `.current` task cursor
    (per-checkout session state, not shared knowledge), and the /update
    rescue copy of the host-repo framework files (a throwaway snapshot, not
    history - the `.ai` repo already versions everything it owns)."""
    ai_dir = root / ".ai"
    if not ai_dir.is_dir():
        return
    gi = ai_dir / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    have = {line.strip().rstrip("/") for line in lines}
    add = [e for e in ("external/", ".current", "agent/.update-backup/")
           if e.rstrip("/") not in have]
    if not add:
        return
    content = "\n".join(lines).rstrip("\n")
    content = (content + "\n" if content else "") + "\n".join(add) + "\n"
    gi.write_text(content, encoding="utf-8")
    print(f"updated  .ai/.gitignore (+ {', '.join(add)})")


def ai_commit(root: Path, message: str):
    """Track .ai/ in its own repo; commit pending changes with message."""
    ai_dir = root / ".ai"
    if not ai_dir.is_dir():
        return
    if shutil.which("git") is None:
        print("warning: git not found; .ai changes not committed")
        return
    if not (ai_dir / ".git").exists():
        r = run_git(["init"], ai_dir)
        if r.returncode != 0:
            print(f"warning: git init failed in .ai: {r.stderr.strip()}")
            return
        print("initialized git repo in .ai/")
    run_git(["add", "-A"], ai_dir)
    if run_git(["diff", "--cached", "--quiet"], ai_dir).returncode == 0:
        return  # nothing staged
    r = run_git(["commit", "-m", message], ai_dir)
    if r.returncode != 0:
        print(f"warning: commit in .ai failed: {r.stderr.strip() or r.stdout.strip()}")
    else:
        print(f"committed in .ai: {message}")


# --------------------------------------------------------------------- init

# ------------------------------------------------------------- auto-sizing

# Source extensions counted toward the codebase LOC estimate that drives
# automatic profile selection. Deliberately code-only: docs, data, and markup
# (.md, .json, .yaml, .toml, .html, .css) are excluded so the number reflects
# code the agent must reason about, not prose or generated lockfiles.
CODE_EXTS = {
    ".py", ".rs", ".go", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".java",
    ".kt", ".rb", ".php", ".c", ".h", ".hpp", ".cpp", ".cc", ".cs",
    ".swift", ".scala", ".sh", ".bash", ".sql",
}

# Directories skipped by the os.walk fallback (git ls-files already excludes
# gitignored paths, so these only matter when root is not a git repo).
SKIP_DIRS = {
    ".git", ".ai", "node_modules", "vendor", "target", "dist", "build",
    ".venv", "venv", "__pycache__", ".mypy_cache", ".tox", ".next", "out",
}

# Codebases at or below this many lines of code get the small profile; larger
# ones get the full large profile. Matches CONCEPT.md's ~10k-LOC boundary.
SIZE_LOC_THRESHOLD = 10000


def source_files(root: Path):
    """Files to weigh for sizing. Prefers `git ls-files` (deterministic,
    gitignore-aware) when root is a git repo; else walks the tree, skipping
    SKIP_DIRS. Returns absolute paths."""
    r = run_git(["ls-files"], root)
    if r.returncode == 0 and r.stdout.strip():
        return [root / line for line in r.stdout.splitlines() if line.strip()]
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        files.append(p)
    return files


def estimate_loc(root: Path) -> int:
    """Recursively count lines across the host repo's source files (CODE_EXTS
    only), so the count reflects code rather than docs/data/lockfiles. Binary
    or unreadable files are skipped."""
    total = 0
    for p in source_files(root):
        if p.suffix.lower() not in CODE_EXTS:
            continue
        try:
            with p.open("rb") as fh:
                total += sum(1 for _ in fh)
        except OSError:
            continue
    return total


def choose_size(loc: int) -> str:
    """Pick the profile from a codebase LOC estimate: small at or below the
    threshold (source is cheap to re-read on demand), large above it."""
    return "small" if loc <= SIZE_LOC_THRESHOLD else "large"


def detect_scaffold(root: Path):
    """Inspect an existing scaffold and return (size, harness, name), or None
    if this directory has none. The fallback behind --detect, for scaffolds
    built before framework.json existed.

    size: 'large' when the KB manifest exists, else 'small' when AGENTS.md does.
    harness: 'claude' when `.claude/` exists, else 'copilot' when
             `.github/prompts/` exists, else 'claude'.
    name: parsed from the AGENTS.md '# Agent: <name>' title, else the dir name.
    """
    agents = root / "AGENTS.md"
    if (root / ".ai" / "knowledgebase" / "manifest.yaml").exists():
        size = "large"
    elif agents.exists():
        size = "small"
    else:
        return None
    if (root / ".claude").exists():
        harness = "claude"
    elif (root / ".github" / "prompts").exists():
        harness = "copilot"
    else:
        harness = "claude"
    name = root.name
    if agents.exists():
        for line in agents.read_text(encoding="utf-8",
                                     errors="replace").splitlines()[:3]:
            if line.startswith("# Agent:"):
                name = line.split(":", 1)[1].strip() or name
                break
    return size, harness, name


def write_debug_probe(root: Path) -> None:
    """--debug-probe: run the freshly scaffolded probe.py and drop its report
    as PROBE.md in the current directory, so the inventory can be inspected
    without running /explore. Plain debug artifact, not a scaffold file."""
    probe = root / TOOLS_DIR / "probe.py"
    try:
        r = subprocess.run([sys.executable, str(probe)],
                           capture_output=True, text=True, cwd=str(root))
    except OSError as e:
        print(f"warning: --debug-probe failed to run probe.py: {e}")
        return
    if r.returncode != 0 or not r.stdout.strip():
        print("warning: --debug-probe: probe.py failed: "
              + (r.stderr.strip() or f"exit {r.returncode}"))
        return
    (root / "PROBE.md").write_text(r.stdout, encoding="utf-8")
    print("wrote PROBE.md (debug inventory; delete or gitignore it)")


def cmd_detect(root: Path) -> int:
    """--detect: describe the scaffold in this directory as JSON, for the
    /update skill. Prefers the recorded framework.json (authoritative: it also
    lists the framework files that version emitted); falls back to inspecting
    the tree for scaffolds built before the stamp existed."""
    stamp = root / FRAMEWORK_JSON
    if stamp.exists():
        try:
            print(stamp.read_text(encoding="utf-8").rstrip())
            return 0
        except OSError:
            pass
    detected = detect_scaffold(root)
    if detected is None:
        print("No agent scaffold found in this directory.", file=sys.stderr)
        return 1
    size, harness, name = detected
    print(json.dumps({
        "framework_version": None,   # predates the stamp
        "profile": size,
        "harness": harness,
        "project": name,
        "generated": None,
        "framework_files": [],       # unknown: nothing to retire from
    }, indent=2))
    return 0


def cmd_emit_reference(target: str, args) -> int:
    """--emit-reference DIR: render a pristine scaffold into DIR and stop.
    No git init, no gitignore edits, no commits, no host-project side effects.
    This is the comparison target the /update skill diffs a real project
    against, so it must be a plain render of the current framework."""
    dest = Path(target).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"error: --emit-reference target is not empty: {dest}",
              file=sys.stderr)
        return 1
    size = args.size if args.size and args.size != "auto" else "large"
    harness = args.harness or "claude"
    name = args.name if args.name is not None else "reference"
    desc = args.description if args.description is not None else ""
    dest.mkdir(parents=True, exist_ok=True)
    if size == "small":
        rc = scaffold_small(dest, name, desc, harness, True, reference=True)
    else:
        rc = scaffold_large(dest, name, desc, harness, True, reference=True)
    if rc == 0:
        print(f"reference {size}/{harness} scaffold "
              f"(framework {FRAMEWORK_VERSION}) rendered to {dest}")
    return rc


def cmd_init(args=None) -> int:
    root = Path.cwd()

    if args and getattr(args, "detect", False):
        return cmd_detect(root)
    if args and getattr(args, "emit_reference", None):
        return cmd_emit_reference(args.emit_reference, args)

    name = (args.name if args and args.name is not None
            else ask("Project name", root.name))
    desc = (args.description if args and args.description is not None
            else ask("Project description, one line"))
    requested = args.size if args and args.size else None
    if requested and requested != "auto":
        size = requested
    else:
        # No profile given, or "auto": weigh the codebase and recommend one.
        est = estimate_loc(root)
        auto_size = choose_size(est)
        print(f"auto-size: {est} lines of code across source files "
              f"-> {auto_size} profile")
        size = auto_size
        if requested != "auto":     # unspecified + interactive: let user vet it
            choice = ask_choice("Project size", ["auto", "large", "small"],
                                "auto")
            size = auto_size if choice == "auto" else choice
    harness = (args.harness if args and args.harness
               else ask_choice("Harness", ["claude", "copilot"], "claude"))

    marker = (root / ".ai" / "knowledgebase" / "manifest.yaml"
              if size == "large" else root / "AGENTS.md")
    force = bool(args and args.yes)
    if marker.exists() and not force:
        answer = ask("Scaffold exists. Overwrite regenerates framework files "
                     "(instructions, skills, hooks, settings); hand-filled "
                     "content (KB, notes, specs) is preserved either way. "
                     "Overwrite? (y/N)", "n")
        force = answer.lower() in ("y", "yes")

    if size == "small":
        rc = scaffold_small(root, name, desc, harness, force)
    else:
        rc = scaffold_large(root, name, desc, harness, force)
    if rc == 0 and args and getattr(args, "debug_probe", False):
        write_debug_probe(root)
    return rc


def scaffold_large(root: Path, name: str, desc: str, harness: str,
                   force: bool, commit_message: str = None,
                   reference: bool = False) -> int:
    kb = root / ".ai" / "knowledgebase"
    if desc:
        seed_description(desc)
    created, skipped, preserved = [], [], []
    _framework_paths.clear()

    for d in KB_DIRS:
        (kb / d).mkdir(parents=True, exist_ok=True)
        if not any((kb / d).iterdir()):
            (kb / d / ".gitkeep").touch()

    tickets = root / ".ai" / "tickets"
    tickets.mkdir(parents=True, exist_ok=True)
    if not any(tickets.iterdir()):
        (tickets / ".gitkeep").touch()

    # Agent/user-owned content: never clobbered once hand-filled.
    for rel, meta in ALL_NODES.items():
        write_owned(kb / rel, frontmatter(meta) + meta["body"],
                    created, skipped, preserved)
    write_owned(kb / "manifest.yaml", render_manifest(name, desc),
                created, skipped, preserved)
    write_owned(kb / "INDEX.md", render_index(name),
                created, skipped, preserved)
    write_owned(root / ".ai" / "notes.md", render_notes_stub(),
                created, skipped, preserved)

    # Framework-owned files: force regenerates them.
    phases = root / PHASES_DIR
    write(phases / "init.md", render_phase_init(harness),
          force, created, skipped)
    write(phases / "planning.md", render_phase_planning(), force, created, skipped)
    write(phases / "implementation.md", render_phase_implementation(harness),
          force, created, skipped)

    tools = root / TOOLS_DIR
    write(tools / "gen_index.py", render_tool_gen_index(), force, created, skipped)
    write(tools / "check_stale.py", render_tool_check_stale(),
          force, created, skipped)
    write(tools / "probe.py", render_tool_probe(), force, created, skipped)
    if harness == "claude":
        # Path-scoped rules are a Claude Code mechanism; on other harnesses
        # conventions stay on the manifest protocol, so the tool is not
        # scaffolded there.
        write(tools / "gen_rules.py", render_tool_gen_rules(),
              force, created, skipped)

    # AGENTS.md is framework-owned except its generated section, which is
    # Phase 1 output: recover it (also from legacy CLAUDE.md scaffolds).
    generated = extract_generated(root)
    write(root / "AGENTS.md", render_agents_md(name, desc, harness, generated),
          force, created, skipped)

    if harness == "claude":
        write(root / "CLAUDE.md", render_claude_pointer(), force, created, skipped)
        for rel, content in render_skills(
                command_specs(harness, "$ARGUMENTS", "$ARGUMENTS")).items():
            write(root / ".claude" / "skills" / rel, content,
                  force, created, skipped)
        write(root / ".claude" / "agents" / "reviewer.md",
              render_reviewer_agent(), force, created, skipped)
        hooks = root / ".claude" / "hooks"
        write(hooks / "protect_generated.py", render_hook_protect_generated(),
              force, created, skipped)
        write(hooks / "regen_index.py", render_hook_regen_index(),
              force, created, skipped)
        write(hooks / "ai_repo_clean.py", render_hook_ai_repo_clean(),
              force, created, skipped)
        write(root / ".claude" / "settings.json", render_settings_json(),
              force, created, skipped)
    else:
        for fname, content in render_prompt_files(
                command_specs(harness, "${input:focus}",
                              "${input:ticket}")).items():
            write(root / ".github" / "prompts" / fname, content,
                  force, created, skipped)

    # Version stamp last: it records every framework path written above.
    write(root / FRAMEWORK_JSON,
          render_framework_json(root, name, "large", harness),
          force, created, skipped)

    if reference:
        return 0

    ensure_gitignore(root)
    ensure_ai_gitignore(root)
    ai_commit(root, commit_message or f"init: scaffold KB + phase docs ({name})")

    report(root, created, skipped, preserved)
    print(f"\nKB: {kb.relative_to(root)}  |  phases: {PHASES_DIR}"
          f"  |  nodes: {len(ALL_NODES)}  |  project: {name}"
          f"  |  harness: {harness}")
    if harness == "copilot":
        print("\nPrompt files (/explore, /plan, /implement) work in VS Code only.")
        print("Copilot CLI reads AGENTS.md; kickoff lines (copy-paste, also "
              "listed there):")
        print(f"  Run Phase 1: read {PHASES_DIR}/init.md first and follow it exactly.")
        print(f"  Plan ticket <id>: read {PHASES_DIR}/planning.md first, then the ticket.")
        print(f"  Implement ticket <id>: read {PHASES_DIR}/implementation.md first, then plan.md.")
    return 0


def scaffold_small(root: Path, name: str, desc: str, harness: str,
                   force: bool, commit_message: str = None,
                   reference: bool = False) -> int:
    """Small profile: dense AGENTS.md + running notes + per-change specs, no KB
    manifest, phase docs, or deterministic KB tools. `.ai/` is still a private
    nested repo (notes + specs); AGENTS.md and .claude/.github live in the host
    repo, as in the full profile."""
    created, skipped, preserved = [], [], []
    _framework_paths.clear()

    archive = root / ".ai" / "changes" / "_archive"
    archive.mkdir(parents=True, exist_ok=True)
    if not any(archive.iterdir()):
        (archive / ".gitkeep").touch()

    # Agent/user-owned content: never clobbered once hand-filled.
    write_owned(root / ".ai" / "notes.md", render_notes_stub(),
                created, skipped, preserved)

    # Deterministic repo inventory: the one KB tool that fits the small profile
    # (no manifest dependency), used at the start of /explore.
    write(root / TOOLS_DIR / "probe.py", render_tool_probe(),
          force, created, skipped)

    # AGENTS.md is framework-owned except its generated section: recover it
    # (also from legacy CLAUDE.md scaffolds) so re-init never reverts /explore.
    generated = extract_generated(root)
    write(root / "AGENTS.md",
          render_agents_md_small(name, desc, harness, generated),
          force, created, skipped)

    if harness == "claude":
        write(root / "CLAUDE.md", render_claude_pointer(), force, created, skipped)
        for rel, content in render_skills(
                command_specs_small(harness, "$ARGUMENTS", "$ARGUMENTS")).items():
            write(root / ".claude" / "skills" / rel, content,
                  force, created, skipped)
        write(root / ".claude" / "agents" / "reviewer.md",
              render_reviewer_agent(small=True), force, created, skipped)
        write(root / ".claude" / "hooks" / "ai_repo_clean.py",
              render_hook_ai_repo_clean(), force, created, skipped)
        write(root / ".claude" / "settings.json",
              render_settings_json(small=True), force, created, skipped)
    else:
        for fname, content in render_prompt_files(
                command_specs_small(harness, "${input:focus}",
                                    "${input:ticket}")).items():
            write(root / ".github" / "prompts" / fname, content,
                  force, created, skipped)

    # Version stamp last: it records every framework path written above.
    write(root / FRAMEWORK_JSON,
          render_framework_json(root, name, "small", harness),
          force, created, skipped)

    if reference:
        return 0

    ensure_gitignore(root)
    ensure_ai_gitignore(root)
    ai_commit(root, commit_message or f"init: small-profile scaffold ({name})")

    report(root, created, skipped, preserved)
    entry = ".claude" if harness == "claude" else ".github/prompts"
    print(f"\n.ai: notes.md + changes/  |  AGENTS.md + {entry}"
          f"  |  profile: small  |  project: {name}  |  harness: {harness}")
    if harness == "copilot":
        print("\nPrompt files (/explore, /spec, /build) work in VS Code only.")
        print("Copilot CLI reads AGENTS.md; state the workflow intent directly:")
        print("  Explore the project and fill the Project Context + .ai/notes.md.")
        print('  Spec change <id> "<title>": write .ai/changes/<id>/spec.md.')
        print("  Build change <id>: implement the spec, then review the diff.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", help="project name (skip the prompt)")
    ap.add_argument("--description", "--desc", dest="description",
                    help="one-line project description (skip the prompt)")
    ap.add_argument("--size", choices=["large", "small", "auto"],
                    help="size profile (skip the prompt). Omit or use 'auto' "
                         "to pick automatically from the codebase LOC "
                         "(small <=10k, large above)")
    ap.add_argument("--harness", choices=["claude", "copilot"],
                    help="target harness (skip the prompt); default claude")
    ap.add_argument("-y", "--yes", action="store_true",
                    help="overwrite framework files without prompting")
    ap.add_argument("--detect", action="store_true",
                    help="print this directory's scaffold stamp as JSON "
                         "(profile, harness, framework version, framework "
                         "file list) and exit; used by the /update skill")
    ap.add_argument("--emit-reference", metavar="DIR",
                    help="render a pristine scaffold of the current framework "
                         "into DIR (must be empty or absent) and exit, with "
                         "no git or host-project side effects. The comparison "
                         "target for the /update skill; use --size/--harness "
                         "to match the project being updated")
    ap.add_argument("--debug-probe", action="store_true",
                    help="after scaffolding, run the generated probe.py and "
                         "write its report to PROBE.md in the current "
                         "directory (inspection aid, not part of the "
                         "scaffold; delete or gitignore it)")
    return cmd_init(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())
