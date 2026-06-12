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
  archive                no command: ask the agent to archive a finished
                         ticket; the rules live in AGENTS.md

Prompts: project name, one-line description, harness (claude/copilot).
Enter accepts the default. Non-TTY runs use all defaults. If a scaffold
already exists, init asks before overwriting framework files; hand-filled
KB content (nodes, manifest, INDEX, generated project-context section) is
always preserved, never reverted to stubs.

Context layout:
  AGENTS.md                    canonical instructions (vendor-neutral): KB
                               protocol, budgets, generated project-context,
                               phase pointers. Read natively by Copilot;
                               imported via CLAUDE.md for Claude Code
  CLAUDE.md (claude)           one-line pointer: @AGENTS.md
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
  python init_agent.py        (or: init-agent)
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

"""
    hook_note = (" A Stop hook in `.claude/settings.json`\n"
                 "    reminds you when `.ai` is dirty." if harness == "claude"
                 else "")
    entry_note = ("packaged as Agent Skills under `.claude/skills/`"
                  if harness == "claude"
                  else "exposed as prompt files under `.github/prompts/`")
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

Right-sizing: a change you can describe in one sentence and that touches a
single file needs no ticket. Do it directly, update the affected KB nodes,
and commit `.ai`. Use the ticket pipeline for everything larger.

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
   `python3 {TOOLS_DIR}/gen_index.py`. Never edit `INDEX.md` directly.
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
11. When compacting the session, always preserve: the current ticket id, the
    current task file path, the list of modified files, and the build/test
    commands.

## Ticket Layout

```
.ai/tickets/      # inbox: <ID>-<slug>.md (e.g. JIRA1234-do-this-and-that.md),
                  # added via /add-ticket or dropped in by the user
tasks/<ticket-id>/
  ticket.md       # original ticket + recorded Q&A answers
  plan.md         # task index; frontmatter: read-first pointer, kb-commit
  NN-<slug>.md    # one file per task, self-contained
  kb-delta.yaml   # accumulated KB patches
tasks/_archive/   # finished tickets; never load
```

Status in frontmatter (`planned|in-progress|done|blocked`), never in folder
names. `/plan <id>` turns an inbox ticket into `tasks/<id>/`.

Archive only when the user asks for it, then: verify every task file in
`tasks/<id>/` has `status: done` (if not, list the open ones and ask);
verify `kb-delta.yaml` was applied to the KB; move `tasks/<id>/` to
`tasks/_archive/<id>/`; commit the `.ai` repo (`archive: <id>`).

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
"""
    return f"""# Phase 1: Initialization

Read this before analyzing the project.

## Strategy
- If a project description was seeded at init (overview node summary and the
  Project Context section), treat it as a hint, not a fact: use it to pick
  what to sample first, then verify and refine it against the code.
- Sample, do not scan everything: per module, read entry points, public API,
  and tests.
- Prefer the harness's native read and search tools (Read, Grep, Glob) over
  shell `grep`/`cat`/`awk`: same result, no permission prompts.{perms}
- Run exploration in isolated sub-agent contexts when the harness supports
  them. Each sub-agent returns a condensed summary of at most 2000 tokens.
  Keep raw file dumps out of the synthesizing context.
- Build KB nodes bottom-up: module nodes first, then the architecture
  overview.
- After node changes, update `manifest.yaml`, then regenerate the index:
  `python3 {TOOLS_DIR}/gen_index.py`. Never edit `INDEX.md` directly.
- Regenerate the `GENERATED:project-context` section in AGENTS.md from the
  hot-tier nodes, condensed: project one-liner, tech stack, build/test/lint
  commands, top conventions, module map (one line per module plus cold-node
  ref), core glossary terms. Cap: 1500 tokens.

## Non-derivable knowledge
Ask the user about domain terms, unwritten conventions, and ownership.
Record the answers directly in the matching KB nodes.
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
2. Create `tasks/<id>/`: move the inbox file's content into `ticket.md`
   (format below), then delete the inbox file.
3. Load matched KB nodes (protocol budgets apply).
4. Run interactive Q&A with the user until the acceptance criteria are
   unambiguous. Keep the rounds bounded. Record answers in `ticket.md`.
5. Write one task file per task. `plan.md` stays a thin index.
6. Plan-review gate: have the plan reviewed in a fresh context that did not
   produce it. Use the `reviewer` sub-agent where the harness supports
   sub-agents; otherwise ask the user to review. Fix gaps that touch the
   acceptance criteria, then get user sign-off on `plan.md` before
   implementation starts. A weak plan poisons every downstream task.
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
Frontmatter: `status: planned`, `depends: []`.
Body, self-contained:
- Goal and testable acceptance criteria
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
`| # | Task file | Depends on | Status |`.
`kb-commit` records the KB state the plan was built against; the
implementation phase diffs against it to detect drift. The `read-first`
pointer forces the implementing session to load its phase doc. Do not
remove either.
"""


def render_phase_implementation() -> str:
    return f"""# Phase 3: Implementation

Read this before executing any task.

## Load discipline
Load only: `plan.md`, the single current task file, its pre-bound KB nodes,
and the listed files. You may run at most 5 targeted searches beyond that.
Never load the whole ticket folder.

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
before declaring the ticket done: run the `reviewer` sub-agent (or, without
sub-agent support, ask the user to review) on the full diff against the
acceptance criteria in `ticket.md` and `plan.md`. Fix gaps that affect
correctness or the stated requirements; ignore style-only findings. Record
the outcome in `plan.md` (`reviewed: <date>`).

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
  AGENTS.md.
- After `manifest.yaml` changes, run `python3 {TOOLS_DIR}/gen_index.py`.
- ADRs (`decisions/`) are append-only. Supersede via link, never edit.
- Staleness: `python3 {TOOLS_DIR}/check_stale.py` lists nodes whose `covers`
  globs match host-repo commits newer than the node. Run it after merges and
  at the start of operational sessions; refresh flagged nodes.
"""


def command_specs(arg_focus: str, arg_ticket: str) -> list:
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
            "Do not start planning or implementing; that begins with /plan <ID>.\n",
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
            "4. Append the node to `manifest.yaml`, then run\n"
            f"   `python3 {TOOLS_DIR}/gen_index.py`.\n"
            '5. Commit the `.ai` repo (`add-reference: <name>`).\n\n'
            "Reminder: search raw copies with targeted queries; never bulk-load.\n",
        ),
    ]


def render_skills() -> dict:
    """Agent Skills (SKILL.md, open standard): .claude/skills/<name>/SKILL.md.
    Read by Claude Code and other SKILL.md-compatible harnesses; descriptions
    enable model invocation, /name invokes directly."""
    out = {}
    for name, desc, body in command_specs("$ARGUMENTS", "$ARGUMENTS"):
        out[f"{name}/SKILL.md"] = (
            "---\n"
            f"name: {name}\n"
            f'description: "{desc}"\n'
            "---\n"
            f"{body}"
        )
    return out


def render_prompt_files() -> dict:
    """Copilot prompt files: .github/prompts/<name>.prompt.md, VS Code only."""
    out = {}
    for name, desc, body in command_specs("${input:focus}", "${input:ticket}"):
        out[f"{name}.prompt.md"] = (
            "---\n"
            f'description: "{desc}"\n'
            "mode: agent\n"
            "---\n"
            f"{body}"
        )
    return out


def render_reviewer_agent() -> str:
    return """---
name: reviewer
description: Adversarial fresh-context review of a plan or diff against
  acceptance criteria. Use for the plan-review gate (Phase 2) and the ticket
  review gate (Phase 3).
tools: Read, Grep, Glob, Bash
---
You review work you did not produce. You see only the artifact and the
acceptance criteria, never the reasoning that produced it. Evaluate the
result on its own terms.

Input: a plan (`.ai/knowledgebase/tasks/<id>/plan.md` plus its task files)
or a code diff, plus the ticket's acceptance criteria
(`.ai/knowledgebase/tasks/<id>/ticket.md`).

Check:
- Every acceptance criterion is covered by a task (plan) or implemented and
  tested (diff).
- Nothing outside the stated scope changed.
- Stated edge cases have tests.
- Task files are self-contained: paths explicit, interfaces stated.

Report only gaps that affect correctness or the stated requirements, with
file and line references. Do not report style preferences. If the work is
sound, say so plainly; do not invent findings to have something to report.
"""


def render_hook_protect_generated() -> str:
    return f'''#!/usr/bin/env python3
"""PreToolUse hook: block direct writes to generated KB files.

INDEX.md is generated from manifest.yaml; direct edits would silently
diverge. Exit 2 blocks the tool call and tells the agent the fix.
"""
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = str((data.get("tool_input") or {{}}).get("file_path", ""))
if path.replace("\\\\", "/").endswith(".ai/knowledgebase/INDEX.md"):
    print(
        "INDEX.md is generated. Edit .ai/knowledgebase/manifest.yaml, then "
        "run: python3 {TOOLS_DIR}/gen_index.py",
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


def render_settings_json() -> str:
    """Project settings (.claude/settings.json): a read-only permission allow
    list so Phase 1 exploration runs without a prompt per command, plus hooks
    that enforce protocol rules deterministically. Compound commands (a && b)
    prompt unless every part of the chain matches a rule, so common chain
    members (cd, echo, pwd, read-only git) are included as well."""
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
        f"Bash(python3 {TOOLS_DIR}/gen_index.py:*)",
        f"Bash(python3 {TOOLS_DIR}/check_stale.py:*)",
    ]
    settings = {
        "permissions": {"allow": allow},
        "hooks": {
            "PreToolUse": [
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
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 "$CLAUDE_PROJECT_DIR/'
                                       '.claude/hooks/ai_repo_clean.py"',
                        }
                    ],
                }
            ],
        },
    }
    return json.dumps(settings, indent=2) + "\n"


# ------------------------------------------------------------------ helpers

def write(path: Path, content: str, force: bool, created: list, skipped: list):
    """Framework-owned files (phase docs, skills, hooks, settings): the
    overwrite confirmation (force) regenerates them."""
    if path.exists() and not force:
        skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)


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
    """Keep raw external copies out of .ai's own repo; they are re-fetchable
    from their origin and would bloat the KB history."""
    ai_dir = root / ".ai"
    if not ai_dir.is_dir():
        return
    gi = ai_dir / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    if any(line.strip().rstrip("/") == "external" for line in lines):
        return
    content = "\n".join(lines).rstrip("\n")
    content = (content + "\n" if content else "") + "external/\n"
    gi.write_text(content, encoding="utf-8")
    print(f"updated  .ai/.gitignore (+ external/)")


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

def cmd_init() -> int:
    root = Path.cwd()
    kb = root / ".ai" / "knowledgebase"

    name = ask("Project name", root.name)
    desc = ask("Project description, one line")
    harness = ask_choice("Harness", ["claude", "copilot"], "claude")

    force = False
    if (kb / "manifest.yaml").exists():
        answer = ask("Scaffold exists. Overwrite regenerates framework files "
                     "(phase docs, skills, hooks, settings); hand-filled KB "
                     "content is preserved either way. Overwrite? (y/N)", "n")
        force = answer.lower() in ("y", "yes")

    if desc:
        seed_description(desc)
    created, skipped, preserved = [], [], []

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

    # Framework-owned files: force regenerates them.
    phases = root / PHASES_DIR
    write(phases / "init.md", render_phase_init(harness),
          force, created, skipped)
    write(phases / "planning.md", render_phase_planning(), force, created, skipped)
    write(phases / "implementation.md", render_phase_implementation(),
          force, created, skipped)

    tools = root / TOOLS_DIR
    write(tools / "gen_index.py", render_tool_gen_index(), force, created, skipped)
    write(tools / "check_stale.py", render_tool_check_stale(),
          force, created, skipped)

    # AGENTS.md is framework-owned except its generated section, which is
    # Phase 1 output: recover it (also from legacy CLAUDE.md scaffolds).
    generated = extract_generated(root)
    write(root / "AGENTS.md", render_agents_md(name, desc, harness, generated),
          force, created, skipped)

    if harness == "claude":
        write(root / "CLAUDE.md", render_claude_pointer(), force, created, skipped)
        for rel, content in render_skills().items():
            write(root / ".claude" / "skills" / rel, content,
                  force, created, skipped)
        write(root / ".claude" / "agents" / "reviewer.md",
              render_reviewer_agent(), force, created, skipped)
        hooks = root / ".claude" / "hooks"
        write(hooks / "protect_generated.py", render_hook_protect_generated(),
              force, created, skipped)
        write(hooks / "ai_repo_clean.py", render_hook_ai_repo_clean(),
              force, created, skipped)
        write(root / ".claude" / "settings.json", render_settings_json(),
              force, created, skipped)
    else:
        for fname, content in render_prompt_files().items():
            write(root / ".github" / "prompts" / fname, content,
                  force, created, skipped)

    ensure_gitignore(root)
    ensure_ai_gitignore(root)
    ai_commit(root, f"init: scaffold KB + phase docs ({name})")

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


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()
    return cmd_init()


if __name__ == "__main__":
    sys.exit(main())
