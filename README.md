# llm-agent-framework

Universal, project-configurable LLM agent for large software projects.
Concept: CONCEPT.md. All agent docs: telegraphic English, token-optimized.

## Usage

```
python init_agent.py init [project_dir] [--force] [--project-name NAME]
python init_agent.py new-ticket TICKET_ID [project_dir] [--title TITLE]
python init_agent.py archive TICKET_ID [project_dir] [--force]
```

`init` creates `.ai/knowledgebase/` (manifest.yaml, INDEX.md, hot/cold nodes),
`.ai/agent/phases/` (on-demand phase docs) and slim core `CLAUDE.md`.
