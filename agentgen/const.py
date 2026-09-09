"""Shared constants: paths, markers, and the skill roster.

Split out so `content` (which renders) and `scaffold` (which writes) can both
import them without importing each other.
"""

from datetime import date

TODAY = date.today().isoformat()

FRAMEWORK_VERSION = "5.22"

FRAMEWORK_JSON = ".ai/agent/framework.json"

TOOLS_DIR = ".ai/agent/tools"

GEN_BEGIN = ("<!-- BEGIN GENERATED:project-context "
             "(source: /explore, max 1500 tokens) -->")

GEN_END = "<!-- END GENERATED:project-context -->"

SKILLS = ["explore", "spec", "build", "import-kb", "import", "tidy-up",
          "update"]

# Where the hermes harness looks for project skills. Hermes reads both
# `.hermes/skills/` and `.agents/skills/` under the nearest git root; the
# scaffold uses the second because it is the cross-tool location, so a project
# that later adds another SKILL.md reader does not need a second copy.
HERMES_SKILLS_DIR = ".agents/skills"

# Hermes ships built-in slash commands, and two of the framework's names are
# taken: /import and /update. A project skill cannot be counted on to reach
# past a built-in, so on that harness those two are emitted under a different
# name. Every other command keeps its name everywhere. Prose that names one of
# the two goes through the `cmd_*` slots (see `content.command_slots`) so a
# renamed command is not referred to by a name that does not exist there.
HERMES_COMMAND_NAMES = {
    "update": "framework-update",
    "import": "import-agent",
}

# Hermes caps a skill description at 60 characters, which the descriptions in
# the skill templates (written for the claude and copilot frontmatter) exceed.
# One short, self-contained, period-terminated line per command.
HERMES_DESCRIPTIONS = {
    "explore": "Survey the codebase and record what it finds.",
    "import-kb": "Import an existing knowledge base.",
    "import": "Migrate an existing agent folder into .ai.",
    "spec": "Write a spec for a non-trivial change.",
    "build": "Implement a change spec, then review it.",
    "tidy-up": "Hygiene sweep that may not change behavior.",
    "update": "Move this scaffold to the current framework.",
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
    "tidy-up": ("Hygiene sweep that may not change behavior: remove "
                "dead code, propose obsolete files, shorten "
                "comments, drop em dashes"),
    "update": ("Update this scaffold to the current framework "
               "version: merge the framework files, migrate notes "
               "and specs, never re-explore"),
}

ARG_HINTS = {
    "explore": "[focus]",
    "import-kb": "<source>",
    "import": "<source>",
    "spec": "<id> <title...>",
    "build": "<id>",
    "tidy-up": "[scope]",
    "update": "[dry-run]",
}
