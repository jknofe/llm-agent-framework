# llm-agent-framework

Universal, project-configurable LLM agent for large software projects.
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

A typical project lifecycle, from zero to working tickets:

1. **Scaffold**, in your project root, with a one-line project description:
   `init-agent init . "ROS Docker container, builds ROS2 humble and jazzy snaps"`
2. **Build the knowledge base**: start Claude Code and run `/explore`.
   The agent samples the codebase, fills the KB nodes and asks you about
   non-derivable knowledge (domain terms, unwritten rules).
3. **Register external material** the agent will need, e.g. an upstream
   library or its docs:
   `init-agent add-reference ros2-docs https://github.com/ros2/ros2_documentation.git`
4. **Plan a ticket**: `init-agent new-ticket FEAT-42 --title "Add jazzy build"`,
   then `/plan FEAT-42` in Claude Code. Answer the Q&A rounds and sign off
   on the plan.
5. **Implement**: `/implement FEAT-42`. The agent works the task files in
   order and records KB updates in `kb-delta.yaml`.
6. **Archive** the finished ticket: `init-agent archive FEAT-42`.

## CLI commands

```
init-agent init [project_dir] [description] [--force] [--project-name NAME]
init-agent new-ticket TICKET_ID [project_dir] [--title TITLE]
init-agent add-reference NAME ORIGIN [project_dir] [--summary TEXT]
init-agent archive TICKET_ID [project_dir] [--force]
```

Or directly without installing: `python init_agent.py <subcommand> ...`

## Slash commands (Claude Code)

`init` scaffolds these into `.claude/commands/` of your project:

| Command | Phase | What it does |
|---|---|---|
| `/explore [focus]` | 1 Initialization | Samples the codebase, fills the KB, regenerates manifest/INDEX and the CLAUDE.md project context. Optional free-text focus, e.g. `/explore focus on the docker setup`. |
| `/plan <ticket-id>` | 2 Planning | Decomposes the ticket into self-contained task files via Q&A, ends with the plan-review gate. |
| `/implement <ticket-id>` | 3 Implementation | Works the planned task files in order; tests, KB delta, typed escalation on blockers. |

The commands are thin pointers to the phase docs in `.ai/agent/phases/`, so
phase instructions stay in one place.

## What init creates

`init` creates `.ai/knowledgebase/` (manifest.yaml, INDEX.md, hot/cold
nodes), `.ai/agent/phases/` (on-demand phase docs), slim core `CLAUDE.md`,
the slash commands above and `.claude/settings.json` with a read-only
permission allow list (grep, find, ls, cat, awk, read-only git, ...) so
exploration runs without a confirmation prompt per command. Compound
commands (`a && b`) only skip the prompt when every part of the chain is
allowed, so common chain members like `cd`, `echo` and `pwd` are included.
`CLAUDE.md` and `.claude/` belong to the host repo.

The optional `description` is a one-line project summary. It is seeded into
the architecture overview node, `manifest.yaml` and the CLAUDE.md project
context section, so the agent's first ramp-up (Phase 1) starts from a known
project intent instead of discovering it from scratch. Phase 1 verifies and
refines it against the code.

`add-reference` registers external material (another repo, documentation,
example code) for the agent. The raw copy goes to `.ai/external/<name>/`
(cloned from a git URL or copied from a local path, excluded from `.ai`'s
git repo) and a small KB node `references/<name>.md` records origin, fetch
date, pinned version and usage notes. The agent loads only the node and
searches the raw copy with targeted queries instead of reading it whole.

`.ai/` is versioned in its own git repo (`.ai/.git`) and excluded from the
host project via a `.gitignore` entry written by `init`. All subcommands
auto-commit their `.ai/` changes; `CLAUDE.md` remains in the host repo.
