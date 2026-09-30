## Running the commands (VS Code vs Copilot CLI)

The prompt files under `.github/prompts/` are a VS Code feature. In Copilot
Chat, run one by typing its basename as a slash command, with any argument
after it: `/explore`, `/task create <id> <title>`, `/task do <id>`,
`/task list`, `/framework-update dry-run`. The bare word without the slash does not run
it.

Copilot CLI does not read `.github/prompts/`, so no slash command works
there. Name the command and its argument instead, and follow that file; the
input placeholders in it stand for the argument given:

- `Run task create FEAT-42 "<title>": read .github/prompts/task.prompt.md and follow it.`
- `Run task do FEAT-42: read .github/prompts/task.prompt.md and follow it.`
- `Run task list: read .github/prompts/task.prompt.md and follow it.`

