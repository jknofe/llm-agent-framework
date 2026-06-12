#!/usr/bin/env python3
"""
init_agent.py - Scaffold a project-aware LLM agent (interactive, run in the
project root). The script only initializes; everything afterwards is done by
the agent through slash commands and folder conventions:

  /explore               Phase 1: build the knowledge base
  /add-ticket            store a ticket as markdown in the .ai/tickets/ inbox
                         (or drop a <ID>-<slug>.md file there yourself)
  /plan <id>             Phase 2: turn an inbox ticket into tasks/<id>/
  /implement <id>        Phase 3: work the planned task files
  /add-reference         register external material (repos, docs) under
                         .ai/external/ + a references/<name> KB node
                         (or place material in .ai/external/ yourself)
  archive                no command: ask the agent to archive a finished
                         ticket; the rules live in the instructions file

Prompts: project name, one-line description, harness (claude/copilot).
Enter accepts the default. Non-TTY runs use all defaults. If a scaffold
already exists, init asks before overwriting (overwrite regenerates stubs
and reverts hand-filled KB content).

Context layout:
  CLAUDE.md (claude) /         always loaded: KB protocol, budgets, generated
  .github/copilot-instructions.md (copilot)  project-context, phase pointers
  .ai/agent/phases/*.md        loaded on demand, only when the phase runs
  .claude/commands/*.md /      slash commands; thin pointers to phase docs,
  .github/prompts/*.prompt.md  self-contained for the add-* helpers
  .claude/settings.json        permission allow list (claude only): read-only
                               shell commands run without prompts

Versioning:
  .ai/ is excluded from the host project's repo (init appends it to the
  project .gitignore) and tracked in its own git repo at .ai/.git. init
  makes the first commit; afterwards the agent commits .ai changes itself
  (protocol rule in the instructions file).

Generated docs use two language registers (concept v4, CONCEPT.md section 8):
normative docs (instructions file, phase docs) in plain imperative English,
KB content (node summaries, tickets) telegraphic. Identifiers verbatim.

Usage:
  python init_agent.py        (or: init-agent)
"""

import argparse
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
        "  claude_md_max_tokens: 2000",
        "  generated_section_max_tokens: 1500",
        "  per_task_max_nodes: 4",
        "  per_task_max_tokens: 6000",
        "  related_hops: 1",
        "  budget_policy: soft  # overrun allowed; state reason in one line, log it",
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
        "<!-- GENERATED from manifest.yaml. Do not edit. -->",
        "",
        "| Node | Tier | Load when |",
        "|---|---|---|",
    ]
    for path, meta in sorted(ALL_NODES.items()):
        lines.append(f"| `{path}` | {meta['tier']} | {meta['summary']} |")
    return "\n".join(lines) + "\n"


def render_claude_md(project_name: str, description: str = "",
                     harness: str = "claude") -> str:
    seed = f"{description}\n" if description else ""
    cli_note = ""
    if harness == "copilot":
        cli_note = f"""## Copilot CLI

Prompt files (`/explore`, `/plan`, `/implement`) work in VS Code only. In
Copilot CLI, start a phase with its kickoff line:

- `Run Phase 1: read {PHASES_DIR}/init.md first and follow it exactly.`
- `Plan ticket <id>: read {PHASES_DIR}/planning.md first, then the ticket.`
- `Implement ticket <id>: read {PHASES_DIR}/implementation.md first, then plan.md.`

"""
    return f"""# Agent: {project_name}

Project-aware agent (concept v4). KB = `.ai/knowledgebase/`. Token efficiency
is a hard requirement; this file stays under 2000 tokens. Phase instructions
live in `{PHASES_DIR}/` and are loaded only when the phase runs. Write
normative instructions in plain imperative English; write KB content
telegraphic. Keep identifiers, paths, and commands verbatim.

## Phases

| Phase | Read first (mandatory, before any other step) |
|---|---|
| 1 Initialization | `{PHASES_DIR}/init.md` |
| 2 Planning | `{PHASES_DIR}/planning.md` |
| 3 Implementation | `{PHASES_DIR}/implementation.md` |
| 4 Operational | none. Protocol below = default behavior |

## KB Protocol

1. Parse `.ai/knowledgebase/manifest.yaml` first. Never load all nodes.
2. Hot-tier content is embedded in the Project Context section below. Never
   load `tier: hot` nodes separately.
3. Match the task against `covers` globs and `tags` first (stage 1, exact).
   Only on a miss, keyword-score the manifest summaries (stage 2).
4. Budgets are soft targets: aim for at most 4 cold nodes / 6000 tokens per
   task, and follow `related` links at most 1 hop. If you must exceed a
   budget, state the reason in one line, proceed, and log the overrun.
   Recall beats precision: never skip context you need just to stay under
   budget.
5. Cache loaded node ids per session. Invalidate the cache after context
   compaction; summarized content no longer counts as loaded.
6. Mark loaded nodes as used or unused (compaction telemetry).
7. Never load `tasks/_archive/`.
8. Session hygiene: clear bulky tool results after extracting what you need.
   Run exploration in sub-agent contexts when the harness supports them.
9. Invariants: single source of truth, never duplicate. Split a node over
   ~1500 tokens and cross-link the parts.
10. External references: nodes under `references/` describe material in
    `.ai/external/` (other repos, docs, example code). Load the node first,
    then search the raw copy with targeted queries (in a sub-agent when
    available). Never bulk-load raw external material into context. If you
    find material in `.ai/external/` without a `references/` node, create
    the node (see the /add-reference command for the format).
11. Persist `.ai` changes: after changing files under `.ai/`, commit them in
    its own repo with a short message, e.g.
    `git -C .ai add -A && git -C .ai commit -m "plan: JIRA-1234"`.
    Never commit `.ai` content to the host project repo.

## Ticket Layout

```
.ai/tickets/      # inbox: <ID>-<slug>.md (e.g. JIRA1234-do-this-and-that.md),
                  # added via /add-ticket or dropped in by the user
tasks/<ticket-id>/
  ticket.md       # original ticket + recorded Q&A answers
  plan.md         # task index; frontmatter carries read-first pointer
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

## Model Routing (default)

Planning + tasks `complexity: high` → high-reasoning model. `low`/`med` →
cost-efficient model. Escalation rules in `{PHASES_DIR}/implementation.md`
override.

{cli_note}## Project Context

<!-- BEGIN GENERATED:project-context (source: hot-tier nodes, max 1500 tokens) -->
{seed}<!-- Populated in Phase 1. Do not edit. -->
<!-- END GENERATED:project-context -->
"""


def render_phase_init(inst: str = "CLAUDE.md", harness: str = "claude") -> str:
    perms = (
        " Shell\n"
        "  commands you do need are pre-allowed in `.claude/settings.json`\n"
        "  (read-only list)." if harness == "claude" else ""
    )
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
- After node changes, regenerate `manifest.yaml` and `INDEX.md`.
- Regenerate the `GENERATED:project-context` section in {inst} from the
  hot-tier nodes, condensed: project one-liner, tech stack, build/test/lint
  commands, top conventions, module map (one line per module plus cold-node
  ref), core glossary terms. Cap: 1500 tokens.

## Non-derivable knowledge
Ask the user about domain terms, unwritten conventions, and ownership.
Record the answers directly in the matching KB nodes.

## Incrementality
Record the commit SHA and per-file hashes. A re-init processes only the diff.

## Output
Produce a coverage report: areas read vs skipped (lazy-init candidates for
Phase 4).
"""


def render_phase_planning() -> str:
    return f"""# Phase 2: Planning (high-reasoning model)

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
6. Plan-review gate: review the finished plan against the acceptance
   criteria yourself, then get user sign-off on `plan.md` before
   implementation starts. A weak plan poisons every downstream task.
7. Commit the `.ai` repo (`plan: <id>`).

## ticket.md format
Frontmatter: `id`, `title`, `status: planned`, `created: <date>`.
Body: the original ticket description, then a `## Q&A (Planning)` section
with the recorded answers.

## Task file format (`NN-<slug>.md`)
Frontmatter: `status: planned`, `complexity: low|med|high`, `depends: []`.
Body, self-contained:
- Goal and testable acceptance criteria
- Affected files with explicit paths
- Pre-bound KB node ids with content hashes
- Expected signatures/interfaces
- Test skeletons

Pre-binding is a warm start, not a contract: implementation starts from the
bound nodes and files and may run at most 5 targeted searches of its own
before escalating `missing-context`.

## plan.md format
Frontmatter: `ticket: <id>`, `status: planned`,
`read-first: {PHASES_DIR}/implementation.md`, `updated: <date>`.
Body: index only, a task table
`| # | Task file | Depends on | Complexity | Model | Status |`.
The frontmatter `read-first` pointer forces the implementation model to load
its phase doc. Do not remove it.

## Routing
Set `complexity` per task. `high` routes to the high-reasoning model, even
during the implementation phase.
"""


def render_phase_implementation(inst: str = "CLAUDE.md") -> str:
    return f"""# Phase 3: Implementation (cost-efficient model)

Read this before executing any task.

## Load discipline
Load only: `plan.md`, the single current task file, its pre-bound KB nodes,
and the listed files. You may run at most 5 targeted searches beyond that.
Never load the whole ticket folder.

## Hash check (diff-aware)
Verify the pre-bound node content hashes before starting. On drift, diff the
current node content against the bound hash:
- If the delta does not touch the task's interfaces or acceptance criteria,
  proceed on the fresh content.
- If it does, stop and re-plan the affected task only (escalate to the
  planning model).
Never proceed silently on stale context. Never trigger a full re-plan for
cosmetic drift.

## Definition of done (per task)
- Tests pass and lint is clean
- Task frontmatter is `status: done`
- A KB patch is appended to `kb-delta.yaml`:
  `op: update|create|split`, `node: <id>`, `diff: <content>`

## Escalation (typed; never improvise around a blocker)
- `missing-context`: use your bounded discovery first, then reload KB (1 hop,
  in a sub-agent when available), then upgrade the model.
- `ambiguity`: ask the user.
- `test-fail` twice: upgrade the model, for this task only.

## KB maintenance
- `kb-delta.yaml` auto-apply covers metadata and `covers` changes only.
  Structural changes go through the review gate.
- After hot-tier node updates, regenerate `GENERATED:project-context` in
  {inst}.
- ADRs (`decisions/`) are append-only. Supersede via link, never edit.
- Narrow the triggers of nodes that are loaded but unused in more than 50%
  of tasks.
"""


def render_commands(inst: str = "CLAUDE.md", harness: str = "claude") -> dict:
    """Slash commands as thin pointers: each tells the agent which phase doc
    to read; the phase docs stay the single source of truth.

    claude:  .claude/commands/<name>.md, args via $ARGUMENTS
    copilot: .github/prompts/<name>.prompt.md, args via ${input:...}
    """
    if harness == "copilot":
        ext = ".prompt.md"
        fm_extra = "mode: agent\n"
        arg_focus = "${input:focus}"
        arg_ticket = "${input:ticket}"
    else:
        ext = ".md"
        fm_extra = ""
        arg_focus = "$ARGUMENTS"
        arg_ticket = "$ARGUMENTS"
    return {
        f"explore{ext}": (
            "---\n"
            'description: "Run Phase 1 (Initialization): build the knowledge base"\n'
            f"{fm_extra}"
            "---\n"
            "Run Phase 1 (Initialization) of the project-aware agent framework.\n\n"
            f"Read `{PHASES_DIR}/init.md` first, before any other step, and follow\n"
            "it exactly. Outcome: filled KB nodes in `.ai/knowledgebase/`,\n"
            "regenerated `manifest.yaml` and `INDEX.md`, populated\n"
            f"`GENERATED:project-context` section in `{inst}`, and a coverage\n"
            "report.\n\n"
            f"{arg_focus}\n"
        ),
        f"add-ticket{ext}": (
            "---\n"
            'description: "Store a ticket as markdown in the .ai/tickets/ inbox"\n'
            f"{fm_extra}"
            "---\n"
            f"Add a ticket to the inbox. Ticket id, title, description: {arg_ticket}\n\n"
            "1. Build the filename `<ID>-<slug>.md` from id and title, e.g.\n"
            "   `JIRA1234-do-this-and-that.md`.\n"
            "2. Write `.ai/tickets/<ID>-<slug>.md` with frontmatter `id`, `title`,\n"
            "   `status: new`, `created: <today>` and the description as body.\n"
            "   Ask for a one-line description if none was given.\n"
            '3. Commit the `.ai` repo (`add-ticket: <ID>`).\n\n'
            "Do not start planning or implementing; that begins with /plan <ID>.\n"
        ),
        f"plan{ext}": (
            "---\n"
            'description: "Run Phase 2 (Planning): decompose a ticket into task files"\n'
            f"{fm_extra}"
            "---\n"
            f"Run Phase 2 (Planning) for ticket: {arg_ticket}\n\n"
            f"Read `{PHASES_DIR}/planning.md` first, before any other step, and\n"
            "follow it exactly, including the Q&A rounds and the plan-review gate.\n"
            "The ticket is in the `.ai/tickets/` inbox.\n"
        ),
        f"implement{ext}": (
            "---\n"
            'description: "Run Phase 3 (Implementation): work the planned tasks"\n'
            f"{fm_extra}"
            "---\n"
            f"Run Phase 3 (Implementation) for ticket: {arg_ticket}\n\n"
            f"Read `{PHASES_DIR}/implementation.md` first, before any other step,\n"
            "and follow it exactly. Load the ticket's `plan.md` and work the task\n"
            "files in order.\n"
        ),
        f"add-reference{ext}": (
            "---\n"
            'description: "Register external material (repo, docs) as a reference"\n'
            f"{fm_extra}"
            "---\n"
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
            "4. Append the node to `manifest.yaml` and `INDEX.md`.\n"
            '5. Commit the `.ai` repo (`add-reference: <name>`).\n\n'
            "Reminder: search raw copies with targeted queries; never bulk-load.\n"
        ),
    }


def render_settings_json() -> str:
    """Project permission allow list (.claude/settings.json) so Phase 1
    exploration runs without a prompt per command. Read-only commands only.
    Compound commands (a && b) prompt unless every part of the chain matches
    a rule, so common chain members (cd, echo, pwd, read-only git) are
    included as well."""
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
    ]
    rules = ",\n".join(f'      "{r}"' for r in allow)
    return (
        "{\n"
        '  "permissions": {\n'
        '    "allow": [\n'
        f"{rules}\n"
        "    ]\n"
        "  }\n"
        "}\n"
    )
# ------------------------------------------------------------------ helpers

def write(path: Path, content: str, force: bool, created: list, skipped: list):
    if path.exists() and not force:
        skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)


def report(root: Path, created: list, skipped: list):
    for p in created:
        print(f"created  {p.relative_to(root)}")
    for p in skipped:
        print(f"skipped  {p.relative_to(root)} (exists)")


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
        answer = ask("Scaffold exists. Overwrite regenerates stubs and "
                     "reverts hand-filled KB content. Overwrite? (y/N)", "n")
        force = answer.lower() in ("y", "yes")

    if desc:
        seed_description(desc)
    created, skipped = [], []

    for d in KB_DIRS:
        (kb / d).mkdir(parents=True, exist_ok=True)
        if not any((kb / d).iterdir()):
            (kb / d / ".gitkeep").touch()

    tickets = root / ".ai" / "tickets"
    tickets.mkdir(parents=True, exist_ok=True)
    if not any(tickets.iterdir()):
        (tickets / ".gitkeep").touch()

    for rel, meta in ALL_NODES.items():
        write(kb / rel, frontmatter(meta) + meta["body"], force, created, skipped)

    write(kb / "manifest.yaml", render_manifest(name, desc), force, created, skipped)
    write(kb / "INDEX.md", render_index(name), force, created, skipped)

    inst_rel = ("CLAUDE.md" if harness == "claude"
                else ".github/copilot-instructions.md")

    phases = root / PHASES_DIR
    write(phases / "init.md", render_phase_init(inst_rel, harness),
          force, created, skipped)
    write(phases / "planning.md", render_phase_planning(), force, created, skipped)
    write(phases / "implementation.md", render_phase_implementation(inst_rel),
          force, created, skipped)

    write(root / inst_rel, render_claude_md(name, desc, harness),
          force, created, skipped)

    commands = (root / ".claude" / "commands" if harness == "claude"
                else root / ".github" / "prompts")
    for fname, content in render_commands(inst_rel, harness).items():
        write(commands / fname, content, force, created, skipped)
    if harness == "claude":
        write(root / ".claude" / "settings.json", render_settings_json(),
              force, created, skipped)

    ensure_gitignore(root)
    ensure_ai_gitignore(root)
    ai_commit(root, f"init: scaffold KB + phase docs ({name})")

    report(root, created, skipped)
    print(f"\nKB: {kb.relative_to(root)}  |  phases: {PHASES_DIR}"
          f"  |  nodes: {len(ALL_NODES)}  |  project: {name}"
          f"  |  harness: {harness}")
    if harness == "copilot":
        print("\nPrompt files (/explore, /plan, /implement) work in VS Code only.")
        print("Copilot CLI kickoff lines (copy-paste; also listed in "
              f"{inst_rel}):")
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
