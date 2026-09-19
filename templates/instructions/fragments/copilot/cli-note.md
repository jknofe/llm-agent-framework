## Running the commands (VS Code vs Copilot CLI)

The prompt files under `.github/prompts/` are a VS Code feature. In Copilot
Chat, run one by typing its basename as a slash command, with any argument
after it: `/explore`, `/spec`, `/build`, `/framework-update dry-run`. The
bare word without the slash does not run it.

Copilot CLI does not read `.github/prompts/`, so no slash command works
there. It does read this file, so state the intent directly instead; the
Protocol and Workflows above apply:

- `Explore the project: ask me the questions, then fill the requirements section.`
- `Spec change <id> "<title>": write .ai/changes/<id>/spec.md.`
- `Build change <id>: implement the spec, then review the diff against the criteria.`
- `Update the framework: read .github/prompts/framework-update.prompt.md and follow it.`

