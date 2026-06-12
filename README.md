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

## Usage

```
init-agent init [project_dir] [--force] [--project-name NAME]
init-agent new-ticket TICKET_ID [project_dir] [--title TITLE]
init-agent archive TICKET_ID [project_dir] [--force]
```

Or directly without installing: `python init_agent.py <subcommand> ...`

`init` creates `.ai/knowledgebase/` (manifest.yaml, INDEX.md, hot/cold nodes),
`.ai/agent/phases/` (on-demand phase docs) and slim core `CLAUDE.md`.

`.ai/` is versioned in its own git repo (`.ai/.git`) and excluded from the
host project via a `.gitignore` entry written by `init`. All subcommands
auto-commit their `.ai/` changes; `CLAUDE.md` remains in the host repo.
