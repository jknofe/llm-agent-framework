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

The CLI has exactly one job: scaffolding. Run `init-agent` (no arguments)
in your project root and answer the prompts (project name, one-line
description, claude or copilot); Enter accepts the defaults. If a scaffold
already exists it asks before overwriting. `init-agent -h` shows help.
Everything after init is done by the agent through slash commands and
folder conventions:

1. **Build the knowledge base**: run `/explore`. The agent samples the
   codebase, fills the KB nodes and asks you about non-derivable knowledge
   (domain terms, unwritten rules).
2. **Register external material** the agent will need (an upstream library,
   its docs): `/add-reference ros2-docs https://github.com/ros2/ros2_documentation.git`,
   or put the material into `.ai/external/<name>/` yourself.
3. **Add a ticket**: `/add-ticket JIRA-1234 Add jazzy build`, or drop a
   markdown file into the `.ai/tickets/` inbox yourself, named like
   `JIRA1234-do-this-and-that.md`.
4. **Plan it**: `/plan JIRA-1234`. Answer the Q&A rounds and sign off on
   the plan.
5. **Implement**: `/implement JIRA-1234`. The agent works the task files in
   order and records KB updates in `kb-delta.yaml`.
6. **Archive**: just ask the agent ("archive JIRA-1234"). It verifies all
   tasks are done and the KB delta is applied, then moves the ticket to
   `tasks/_archive/`.

## Slash commands

`init` scaffolds these into your project (`.claude/commands/` for Claude
Code, `.github/prompts/` for Copilot):

| Command | What it does |
|---|---|
| `/explore [focus]` | Phase 1: samples the codebase, fills the KB, regenerates manifest/INDEX and the instructions-file project context. Optional free-text focus. |
| `/add-ticket <id> <title...>` | Stores the ticket as markdown in the `.ai/tickets/` inbox. No planning yet. |
| `/plan <ticket-id>` | Phase 2: turns the inbox ticket into `tasks/<id>/` with self-contained task files via Q&A, ends with the plan-review gate. |
| `/implement <ticket-id>` | Phase 3: works the planned task files in order; tests, KB delta, typed escalation on blockers. |
| `/add-reference <name> <origin>` | Clones/copies external material to `.ai/external/<name>/` and registers a `references/<name>` KB node (origin, fetch date, pinned version). |

The phase commands are thin pointers to the phase docs in
`.ai/agent/phases/`, so phase instructions stay in one place. The add-*
commands are self-contained. Archiving has no command: prompt the agent;
the rules live in the instructions file.

## GitHub Copilot support

Choosing `copilot` at the harness prompt targets Copilot instead of Claude
Code:

- instructions file: `.github/copilot-instructions.md` instead of `CLAUDE.md`
- prompt files: `.github/prompts/*.prompt.md` instead of
  `.claude/commands/`, invoked the same way (`/explore`, `/plan`, ...) in
  VS Code Copilot Chat; arguments are passed as input variables, e.g.
  `/plan: ticket=FEAT-42`
- no `.claude/settings.json` (Copilot has no equivalent permission allow list)

Prompt files require VS Code with the `chat.promptFiles` setting enabled.
Copilot CLI does not load prompt files; it does read
`.github/copilot-instructions.md`, which therefore contains the phase
kickoff lines to type instead (also printed at the end of `init`), e.g.
`Run Phase 1: read .ai/agent/phases/init.md first and follow it exactly.`

The `.ai/` knowledge base and phase docs are identical for both harnesses;
only the entry files differ.

## What init creates

`init` creates `.ai/knowledgebase/` (manifest.yaml, INDEX.md, hot/cold
nodes), the `.ai/tickets/` inbox, `.ai/agent/phases/` (on-demand phase
docs), the slim core instructions file, the slash commands above and, for
Claude Code, `.claude/settings.json` with a read-only permission allow list
(grep, find, ls, cat, awk, read-only git, `git -C .ai`, ...) so exploration
and `.ai` commits run without a confirmation prompt per command. Compound
commands (`a && b`) only skip the prompt when every part of the chain is
allowed, so common chain members like `cd`, `echo` and `pwd` are included.
The instructions file and `.claude/` / `.github/` belong to the host repo.

The description prompted at init is seeded into the architecture overview
node, `manifest.yaml` and the project context section of the instructions
file, so the agent's first ramp-up (Phase 1) starts from a known project
intent instead of discovering it from scratch. Phase 1 verifies and refines
it against the code.

`.ai/` is versioned in its own git repo (`.ai/.git`) and excluded from the
host project via a `.gitignore` entry written by `init`. `init` makes the
first commit; afterwards the agent commits `.ai` changes itself (a protocol
rule in the instructions file). Raw external material under `.ai/external/`
stays out of that repo too (re-fetchable, would bloat history).
