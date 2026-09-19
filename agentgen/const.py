"""Shared constants: paths, markers, and the skill roster.

Split out so `content` (which renders) and `scaffold` (which writes) can both
import them without importing each other.
"""

from datetime import date

TODAY = date.today().isoformat()

FRAMEWORK_VERSION = "7.1"

FRAMEWORK_JSON = ".ai/agent/framework.json"

TOOLS_DIR = ".ai/agent/tools"

GEN_BEGIN = ("<!-- BEGIN GENERATED:project-context "
             "(source: /explore, requirements only, max 300 tokens) -->")

GEN_END = "<!-- END GENERATED:project-context -->"

# Four commands (CONCEPT.md section 38). /tidy-up, /import-kb and
# /import-agent were retired in v7.0: a hygiene sweep serves neither pillar,
# the KB profile they imported into is gone, and converting an existing setup
# is a plain request to the agent now that the scaffold is six files.
SKILLS = ["explore", "spec", "build", "framework-update"]

# Where the hermes harness looks for project skills. Hermes reads both
# `.hermes/skills/` and `.agents/skills/` under the nearest git root; the
# scaffold uses the second because it is the cross-tool location, so a project
# that later adds another SKILL.md reader does not need a second copy.
HERMES_SKILLS_DIR = ".agents/skills"
HERMES_HOOKS_DIR = ".agents/hooks"
COPILOT_HOOKS_DIR = ".github/hooks"

# Where a harness switch parks the entry files of the harness it replaces.
# Inside `.ai` so it travels with the scaffold, gitignored there because it is
# a rescue snapshot rather than history.
HARNESS_BACKUP_DIR = ".ai/agent/.harness-backup"

# The directories and files each harness owns as its command entry points.
# Used to report what a switch left behind: anything still sitting there that
# the version stamp did not record is the user's own, not the framework's.
HARNESS_ENTRY_PATHS = {
    "claude": [".claude", "CLAUDE.md"],
    "copilot": [".github/prompts", COPILOT_HOOKS_DIR],
    "hermes": [HERMES_SKILLS_DIR, HERMES_HOOKS_DIR],
}

# A command name that collides with a harness built-in is renamed on every
# harness, not just the one that reserves it (CONCEPT.md sections 34 and 35).
# Hermes reserves /update, so this framework ships /framework-update
# everywhere. There is deliberately no per-harness name table any more: one
# command, one name, so every document can name a command without asking
# where it is being read.

# Hermes caps a skill description at 60 characters, which the descriptions in
# the skill templates (written for the claude and copilot frontmatter) exceed.
# One short, self-contained, period-terminated line per command.
HERMES_DESCRIPTIONS = {
    "explore": "Record the commands and rules this project runs on.",
    "spec": "Opt-in: write a spec for a change the user names.",
    "build": "Implement a change spec, then review it.",
    "framework-update": "Move this scaffold to the current framework.",
}

# What `$ARGUMENTS` (claude) and `${input:...}` (copilot) stand in for on
# hermes: nothing is substituted there, the text after the command name simply
# reaches the agent as the user instruction, so the skill has to say so.
HERMES_ARG_FOCUS = ("Focus: the text after the command name, if there was "
                    "any.\nWith none, cover the whole project.")
HERMES_ARG_TICKET = "the text after the command name, verbatim"

# Bodies composed in Python because they vary on harness beyond slot filling.
# Their descriptions live here because they have no template frontmatter.
_SKILL_DESCRIPTIONS = {
    "framework-update": ("Update this scaffold to the current framework "
                         "version: merge the framework files, migrate notes "
                         "and specs, never re-explore"),
}

ARG_HINTS = {
    "explore": "[focus]",
    "spec": "<id> <title...>",
    "build": "<id>",
    "framework-update": "[dry-run]",
}
