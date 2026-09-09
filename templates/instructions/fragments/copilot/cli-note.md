## Running the commands (VS Code vs Copilot CLI)

The prompt files under `.github/prompts/` are a VS Code feature. In VS Code
Copilot Chat, run one by typing its name as a slash command: `/explore`,
`/spec`, `/build`, `/import-kb`, `/import`, `/tidy-up`, `/update`, with any
argument after it (`/update dry-run`). The name is the file's basename without
`.prompt.md`. Typing the bare word without the slash does not run it.
`Chat: Run Prompt` in the Command Palette, and the play button in an open
prompt file, do the same.

Copilot CLI does not read `.github/prompts/` at all, so no slash command works
there. It does read this file, so state the intent directly instead; the
Protocol and Workflows above apply:

- `Explore the project and fill the Project Context section + .ai/notes.md.`
- `Spec change <id> "<title>": write .ai/changes/<id>/spec.md (goal, acceptance criteria, tasks).`
- `Build change <id>: implement .ai/changes/<id>/spec.md, then review the diff against the criteria.`
- `Tidy up [scope]: read .github/prompts/tidy-up.prompt.md first and follow it exactly.`
- `Update the framework: read .github/prompts/update.prompt.md first and follow it exactly.`

