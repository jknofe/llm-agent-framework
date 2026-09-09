## Running the workflows in Hermes

The commands are skills under `.agents/skills/`. Hermes loads project skills
only from a repository it has been told to trust, so run `hermes skills trust`
once in the repository root. After a skill file changes, run `/reload-skills`
in a running session.

Run one by typing its name as a slash command, with any argument after it
(`/framework-update dry-run`): `/explore`, `/spec`, `/build`, `/import-kb`,
`/import-agent`, `/tidy-up`, `/framework-update`.

These are the same names on every harness this framework supports. Two of
them are spelled out rather than shortened, `/framework-update` and
`/import-agent`, because Hermes reserves `/update` and `/import` for built-in
commands of its own.

Whatever follows the command name reaches the agent as the user instruction;
nothing is substituted into the skill file. Take change ids and paths from
that text exactly as the user typed them, and ask when it is missing.

