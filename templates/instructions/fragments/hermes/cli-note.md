## Running the workflows in Hermes

The commands are skills under `.agents/skills/`. Hermes loads project skills
only from a repository it has been told to trust, so run `hermes skills trust`
once in the repository root. After a skill file changes, run `/reload-skills`
in a running session.

Run one by typing its name as a slash command, with any argument after it
(`/framework-update dry-run`): `/explore`, `/spec`, `/build`,
`/framework-update`.

The names are the same on every harness; `/framework-update` is spelled out
because Hermes reserves `/update`.

Whatever follows the command name reaches the agent as the user instruction;
nothing is substituted into the skill file. Take change ids and paths from
that text exactly as the user typed them, and ask when it is missing.

