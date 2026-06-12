#!/usr/bin/env python3
"""
init_agent.py - Scaffold and manage a project-aware LLM agent.

Subcommands:
  init        Create .ai/knowledgebase/, .ai/agent/phases/, CLAUDE.md and
              .claude/commands/ (slash commands /explore, /plan, /implement)
  new-ticket  Scaffold tasks/<ticket-id>/ (ticket.md, plan.md)
  add-reference  Register external material (other repos, docs): raw copy in
              .ai/external/<name>/, describing KB node in references/<name>.md
  archive     Move a finished ticket to tasks/_archive/ (all tasks must be done)

Context layout:
  CLAUDE.md                    always loaded: KB protocol, budgets, generated
                               project-context section, phase pointer table
  .ai/agent/phases/*.md        loaded on demand, only when the phase runs
  .claude/commands/*.md        Claude Code slash commands; thin pointers that
                               tell the agent which phase doc to read
  .claude/settings.json        permission allow list: read-only shell commands
                               run without prompts (incl. parts of && chains)

Versioning:
  .ai/ is excluded from the host project's repo (init appends it to the
  project .gitignore) and tracked in its own git repo at .ai/.git. Every
  subcommand commits its changes there. CLAUDE.md stays in the host repo.

Generated docs use two language registers (concept v4, CONCEPT.md section 8):
normative docs (CLAUDE.md protocol, phase docs) in plain imperative English,
KB content (node summaries, tickets) telegraphic. Identifiers verbatim.

Usage:
  python init_agent.py init [project_dir] [description] [--force] [--project-name NAME]
                            description: one-line project summary, seeded into
                            the overview node, manifest and CLAUDE.md context
  python init_agent.py init . "ROS Docker container, builds ROS2 snaps"
  python init_agent.py new-ticket TICKET_ID [project_dir] [--title TITLE]
  python init_agent.py add-reference NAME ORIGIN [project_dir] [--summary TEXT]
  python init_agent.py archive TICKET_ID [project_dir] [--force]
"""

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

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


def render_claude_md(project_name: str, description: str = "") -> str:
    seed = f"{description}\n" if description else ""
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
    available). Never bulk-load raw external material into context.

## Ticket Layout

```
tasks/<ticket-id>/
  ticket.md       # original ticket + recorded Q&A answers
  plan.md         # task index; frontmatter carries read-first pointer
  NN-<slug>.md    # one file per task, self-contained
  kb-delta.yaml   # accumulated KB patches
tasks/_archive/   # finished tickets; never load
```

Status in frontmatter (`planned|in-progress|done|blocked`), never in folder
names. Archive finished tickets: `python init_agent.py archive <id>`.

## Model Routing (default)

Planning + tasks `complexity: high` → high-reasoning model. `low`/`med` →
cost-efficient model. Escalation rules in `{PHASES_DIR}/implementation.md`
override.

## Project Context

<!-- BEGIN GENERATED:project-context (source: hot-tier nodes, max 1500 tokens) -->
{seed}<!-- Populated in Phase 1. Do not edit. -->
<!-- END GENERATED:project-context -->
"""


def render_phase_init() -> str:
    return f"""# Phase 1: Initialization

Read this before analyzing the project.

## Strategy
- If a project description was seeded at init (overview node summary and the
  Project Context section), treat it as a hint, not a fact: use it to pick
  what to sample first, then verify and refine it against the code.
- Sample, do not scan everything: per module, read entry points, public API,
  and tests.
- Prefer the harness's native read and search tools (Read, Grep, Glob) over
  shell `grep`/`cat`/`awk`: same result, no permission prompts. Shell
  commands you do need are pre-allowed in `.claude/settings.json`
  (read-only list).
- Run exploration in isolated sub-agent contexts when the harness supports
  them. Each sub-agent returns a condensed summary of at most 2000 tokens.
  Keep raw file dumps out of the synthesizing context.
- Build KB nodes bottom-up: module nodes first, then the architecture
  overview.
- After node changes, regenerate `manifest.yaml` and `INDEX.md`.
- Regenerate the `GENERATED:project-context` section in CLAUDE.md from the
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
1. Scaffold: `python init_agent.py new-ticket <ticket-id>`.
2. Load matched KB nodes (protocol budgets apply).
3. Run interactive Q&A with the user until the acceptance criteria are
   unambiguous. Keep the rounds bounded. Record answers in `ticket.md`.
4. Write one task file per task. `plan.md` stays a thin index.
5. Plan-review gate: review the finished plan against the acceptance
   criteria yourself, then get user sign-off on `plan.md` before
   implementation starts. A weak plan poisons every downstream task.

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

## plan.md
Index only: order, dependencies, complexity, routing, status. The
frontmatter `read-first` pointer forces the implementation model to load its
phase doc. Do not remove it.

## Routing
Set `complexity` per task. `high` routes to the high-reasoning model, even
during the implementation phase.
"""


def render_phase_implementation() -> str:
    return """# Phase 3: Implementation (cost-efficient model)

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
  CLAUDE.md.
- ADRs (`decisions/`) are append-only. Supersede via link, never edit.
- Narrow the triggers of nodes that are loaded but unused in more than 50%
  of tasks.
"""


def render_commands() -> dict:
    """Slash commands for Claude Code (.claude/commands/). Thin pointers:
    each command tells the agent which phase doc to read; the phase docs
    stay the single source of truth."""
    return {
        "explore.md": (
            "---\n"
            'description: "Run Phase 1 (Initialization): build the knowledge base"\n'
            "---\n"
            "Run Phase 1 (Initialization) of the project-aware agent framework.\n\n"
            f"Read `{PHASES_DIR}/init.md` first, before any other step, and follow\n"
            "it exactly. Outcome: filled KB nodes in `.ai/knowledgebase/`,\n"
            "regenerated `manifest.yaml` and `INDEX.md`, populated\n"
            "`GENERATED:project-context` section in `CLAUDE.md`, and a coverage\n"
            "report.\n\n"
            "$ARGUMENTS\n"
        ),
        "plan.md": (
            "---\n"
            'description: "Run Phase 2 (Planning): decompose a ticket into task files"\n'
            "---\n"
            "Run Phase 2 (Planning) for ticket: $ARGUMENTS\n\n"
            f"Read `{PHASES_DIR}/planning.md` first, before any other step, and\n"
            "follow it exactly, including the Q&A rounds and the plan-review gate.\n"
        ),
        "implement.md": (
            "---\n"
            'description: "Run Phase 3 (Implementation): work the planned tasks"\n'
            "---\n"
            "Run Phase 3 (Implementation) for ticket: $ARGUMENTS\n\n"
            f"Read `{PHASES_DIR}/implementation.md` first, before any other step,\n"
            "and follow it exactly. Load the ticket's `plan.md` and work the task\n"
            "files in order.\n"
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


def render_reference_node(name: str, origin: str, summary: str, pinned: str) -> str:
    return (
        "---\n"
        f"id: references/{name}\n"
        f"summary: {summary}\n"
        "tags: [external, reference]\n"
        "covers: []\n"
        "tier: cold\n"
        f"updated: {TODAY}\n"
        f"origin: {origin}\n"
        f"fetched: {TODAY}\n"
        f"pinned: {pinned or 'n/a'}\n"
        "related: []\n"
        "---\n\n"
        f"# Reference: {name}\n\n"
        f"Local copy: `.ai/external/{name}/`\n"
        f"Origin: {origin}\n\n"
        "Consult for: <!-- fill: which questions this material answers -->\n"
        "Entry points: <!-- fill: key files or dirs to start searching -->\n\n"
        "Search the raw copy with targeted queries; never bulk-load it.\n"
    )


def append_reference_to_indexes(kb: Path, name: str, summary: str):
    """Register a reference node in manifest.yaml and INDEX.md (append-only;
    node entries form a flat list, order is irrelevant)."""
    manifest = kb / "manifest.yaml"
    if manifest.exists():
        with manifest.open("a", encoding="utf-8") as f:
            f.write(
                f"  - id: references/{name}\n"
                f"    path: references/{name}.md\n"
                f"    summary: {summary}\n"
                "    tags: [external, reference]\n"
                "    covers: []\n"
                "    tier: cold\n"
                f"    updated: {TODAY}\n"
            )
    index = kb / "INDEX.md"
    if index.exists():
        with index.open("a", encoding="utf-8") as f:
            f.write(f"| `references/{name}.md` | cold | {summary} |\n")


def render_ticket_md(ticket_id: str, title: str) -> str:
    return (
        "---\n"
        f"id: {ticket_id}\n"
        f"title: {title}\n"
        "status: planned\n"
        f"created: {TODAY}\n"
        "---\n\n"
        f"# {ticket_id}: {title}\n\n"
        "## Description\n\n<!-- Original ticket here. -->\n\n"
        "## Q&A (Planning)\n\n<!-- Recorded clarification answers. -->\n"
    )


def render_plan_md(ticket_id: str) -> str:
    return (
        "---\n"
        f"ticket: {ticket_id}\n"
        "status: planned\n"
        f"read-first: {PHASES_DIR}/implementation.md\n"
        f"updated: {TODAY}\n"
        "---\n\n"
        f"# Plan: {ticket_id}\n\n"
        "<!-- Implementation model: read read-first file above before any task. -->\n\n"
        "| # | Task file | Depends on | Complexity | Model | Status |\n"
        "|---|---|---|---|---|---|\n"
        "<!-- One row per NN-<slug>.md task file. -->\n"
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
        print(f"skipped  {p.relative_to(root)} (exists, use --force)")


def read_status(path: Path) -> str:
    m = re.search(r"^status:\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "unknown"


def project_root(project_dir: str) -> Path:
    root = Path(project_dir).resolve()
    if not root.is_dir():
        sys.exit(f"error: {root} is not a directory")
    return root


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


# -------------------------------------------------------------- subcommands

def cmd_init(args) -> int:
    root = project_root(args.project_dir)
    name = args.project_name or root.name
    desc = (args.description or "").strip()
    if desc:
        seed_description(desc)
    kb = root / ".ai" / "knowledgebase"
    created, skipped = [], []

    for d in KB_DIRS:
        (kb / d).mkdir(parents=True, exist_ok=True)
        if not any((kb / d).iterdir()):
            (kb / d / ".gitkeep").touch()

    for rel, meta in ALL_NODES.items():
        write(kb / rel, frontmatter(meta) + meta["body"], args.force, created, skipped)

    write(kb / "manifest.yaml", render_manifest(name, desc), args.force, created, skipped)
    write(kb / "INDEX.md", render_index(name), args.force, created, skipped)

    phases = root / PHASES_DIR
    write(phases / "init.md", render_phase_init(), args.force, created, skipped)
    write(phases / "planning.md", render_phase_planning(), args.force, created, skipped)
    write(phases / "implementation.md", render_phase_implementation(),
          args.force, created, skipped)

    write(root / "CLAUDE.md", render_claude_md(name, desc), args.force, created, skipped)

    commands = root / ".claude" / "commands"
    for fname, content in render_commands().items():
        write(commands / fname, content, args.force, created, skipped)
    write(root / ".claude" / "settings.json", render_settings_json(),
          args.force, created, skipped)

    ensure_gitignore(root)
    ensure_ai_gitignore(root)
    ai_commit(root, f"init: scaffold KB + phase docs ({name})")

    report(root, created, skipped)
    print(f"\nKB: {kb.relative_to(root)}  |  phases: {PHASES_DIR}"
          f"  |  nodes: {len(ALL_NODES)}  |  project: {name}")
    return 0


def cmd_new_ticket(args) -> int:
    root = project_root(args.project_dir)
    tdir = root / ".ai" / "knowledgebase" / "tasks" / args.ticket_id
    if tdir.exists():
        sys.exit(f"error: ticket {args.ticket_id} already exists at {tdir}")
    title = args.title or args.ticket_id
    created, skipped = [], []
    write(tdir / "ticket.md", render_ticket_md(args.ticket_id, title), False, created, skipped)
    write(tdir / "plan.md", render_plan_md(args.ticket_id), False, created, skipped)
    report(root, created, skipped)
    ai_commit(root, f"new-ticket: {args.ticket_id}")
    return 0


def cmd_archive(args) -> int:
    root = project_root(args.project_dir)
    tasks_dir = root / ".ai" / "knowledgebase" / "tasks"
    tdir = tasks_dir / args.ticket_id
    if not tdir.is_dir():
        sys.exit(f"error: ticket {args.ticket_id} not found at {tdir}")

    open_items = []
    plan = tdir / "plan.md"
    if plan.exists() and read_status(plan) != "done":
        open_items.append((plan, read_status(plan)))
    for task_file in sorted(tdir.glob("[0-9][0-9]-*.md")):
        st = read_status(task_file)
        if st != "done":
            open_items.append((task_file, st))

    if open_items and not args.force:
        print(f"error: ticket {args.ticket_id} has unfinished items:", file=sys.stderr)
        for p, st in open_items:
            print(f"  {p.relative_to(root)}  status={st}", file=sys.stderr)
        print("use --force to archive anyway", file=sys.stderr)
        return 1

    if not (tdir / "kb-delta.yaml").exists():
        print("warning: no kb-delta.yaml found; verify KB updates were applied")

    dest = tasks_dir / "_archive" / args.ticket_id
    if dest.exists():
        sys.exit(f"error: {dest} already exists in archive")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(tdir), str(dest))
    print(f"archived  {tdir.relative_to(root)} -> {dest.relative_to(root)}")
    ai_commit(root, f"archive: ticket {args.ticket_id}")
    return 0


def cmd_add_reference(args) -> int:
    root = project_root(args.project_dir)
    kb = root / ".ai" / "knowledgebase"
    if not kb.is_dir():
        sys.exit("error: no .ai/knowledgebase found; run init first")

    name = args.name
    node_path = kb / "references" / f"{name}.md"
    if node_path.exists():
        sys.exit(f"error: reference {name} already exists at {node_path}")
    ext_dir = root / ".ai" / "external" / name
    if ext_dir.exists():
        sys.exit(f"error: {ext_dir} already exists")

    origin = args.origin
    src = Path(origin).expanduser()
    pinned = ""
    ext_dir.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir() and not (src / ".git").exists():
        shutil.copytree(src, ext_dir)
        print(f"copied   {origin} -> {ext_dir.relative_to(root)}")
    else:
        if shutil.which("git") is None:
            sys.exit("error: git not found; cannot clone origin")
        r = run_git(["clone", "--depth", "1", origin, str(ext_dir)], root)
        if r.returncode != 0:
            sys.exit(f"error: clone failed: {r.stderr.strip()}")
        rp = run_git(["rev-parse", "--short", "HEAD"], ext_dir)
        pinned = rp.stdout.strip() if rp.returncode == 0 else ""
        print(f"cloned   {origin} -> {ext_dir.relative_to(root)} (@{pinned})")

    summary = args.summary or f"External reference {name}; fill in what it answers"
    node_path.parent.mkdir(parents=True, exist_ok=True)
    node_path.write_text(render_reference_node(name, origin, summary, pinned),
                         encoding="utf-8")
    print(f"created  {node_path.relative_to(root)}")
    append_reference_to_indexes(kb, name, summary)
    print("updated  manifest.yaml, INDEX.md")

    ensure_ai_gitignore(root)
    ai_commit(root, f"add-reference: {name}")
    print(f"\nNext: fill 'Consult for' and 'Entry points' in "
          f"{node_path.relative_to(root)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="scaffold KB, phase docs and CLAUDE.md")
    p.add_argument("project_dir", nargs="?", default=".")
    p.add_argument("description", nargs="?", default=None,
                   help="one-line project summary, seeded into overview node, "
                        "manifest and CLAUDE.md project context")
    p.add_argument("--force", action="store_true")
    p.add_argument("--project-name", default=None)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("new-ticket", help="scaffold a ticket folder")
    p.add_argument("ticket_id")
    p.add_argument("project_dir", nargs="?", default=".")
    p.add_argument("--title", default=None)
    p.set_defaults(func=cmd_new_ticket)

    p = sub.add_parser("add-reference",
                       help="register external material (git URL or local path)")
    p.add_argument("name", help="reference name, becomes references/<name>")
    p.add_argument("origin", help="git URL to clone or local path to copy")
    p.add_argument("project_dir", nargs="?", default=".")
    p.add_argument("--summary", default=None,
                   help="one-line summary for manifest and node frontmatter")
    p.set_defaults(func=cmd_add_reference)

    p = sub.add_parser("archive", help="archive a finished ticket")
    p.add_argument("ticket_id")
    p.add_argument("project_dir", nargs="?", default=".")
    p.add_argument("--force", action="store_true",
                   help="archive even with unfinished tasks")
    p.set_defaults(func=cmd_archive)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
