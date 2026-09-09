## Running the workflows in Hermes

The commands are skills under `.agents/skills/`. Hermes loads project skills
only from a repository it has been told to trust, so run `hermes skills trust`
once in the repository root. After a skill file changes, run `/reload-skills`
in a running session.

Run one by typing its name as a slash command, with any argument after it
(`/framework-update dry-run`): `/explore`, `/add-ticket`, `/plan-ticket`,
`/implement`, `/add-reference`, `/import-kb`, `/import-agent`, `/tidy-up`,
`/framework-update`.

Three of them are named differently here than elsewhere in this framework.
Hermes reserves `/plan`, `/import` and `/update` for built-in commands of its
own, so this scaffold ships `/plan-ticket`, `/import-agent` and
`/framework-update` instead. The workflows behind them are unchanged.

Whatever follows the command name reaches the agent as the user instruction;
nothing is substituted into the skill file. Take ticket ids and paths from
that text exactly as the user typed them, and ask when it is missing.

