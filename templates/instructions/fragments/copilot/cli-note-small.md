## Copilot CLI

Prompt files (`/explore`, `/spec`, `/build`) work in VS Code only. In Copilot
CLI, state the intent directly; the Protocol and Workflows above apply:

- `Explore the project and fill the Project Context section + .ai/notes.md.`
- `Spec change <id> "<title>": write .ai/changes/<id>/spec.md (goal, acceptance criteria, tasks).`
- `Build change <id>: implement .ai/changes/<id>/spec.md, then review the diff against the criteria.`
- `Tidy up [scope]: read .github/prompts/tidy-up.prompt.md first and follow it exactly.`
- `Update the framework: read .github/prompts/update.prompt.md first and follow it exactly.`

