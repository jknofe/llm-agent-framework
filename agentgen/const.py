"""Shared constants: paths, markers, and the skill roster.

Split out so `content` (which renders) and `scaffold` (which writes) can both
import them without importing each other.
"""

from datetime import date

TODAY = date.today().isoformat()

FRAMEWORK_VERSION = "11.5"

FRAMEWORK_JSON = ".ai/agent/framework.json"

TOOLS_DIR = ".ai/agent/tools"

# /task's Create and Do bodies, read on demand by the dispatching skill
# (CONCEPT.md section 42): one harness-neutral copy beside the tools, so
# `/task list` loads only the dispatcher.
TASK_DIR = ".ai/agent/task"

GEN_BEGIN = ("<!-- BEGIN GENERATED:project-context "
             "(source: /explore, requirements only, max 300 tokens) -->")

GEN_END = "<!-- END GENERATED:project-context -->"

# Three commands (CONCEPT.md sections 38, 39 and 41). /tidy-up, /import-kb and
# /import-agent were retired in v7.0: a hygiene sweep serves neither pillar,
# the KB profile they imported into is gone, and converting an existing setup
# is a plain request to the agent now that the scaffold is six files. 8.0
# replaced /spec and /build with the typed task path: most of a working day
# is investigating, bug hunting and testing, not only changing code. 9.0
# folded /task-create, /task-do and /task-list-all into one /task whose
# create-or-do decision is made by `tasks.py resolve`, not by the agent.
# 11.5 added /agent-models: the models of the worker and reviewer sub-agents,
# set the same way on every harness (CONCEPT.md section 55).
SKILLS = ["explore", "task", "agent-models", "framework-update"]

# Claude Code `effort` frontmatter per skill (CONCEPT.md section 42). It
# overrides the session level only for the turn that invokes the skill, so
# the direct path keeps the user's own /effort default. Claude only: no
# equivalent is documented for copilot.
SKILL_EFFORT = {"explore": "medium", "task": "medium",
                "agent-models": "low", "framework-update": "high"}

# The harnesses this generator renders. Hermes was the third until 10.0
# (CONCEPT.md section 43); a scaffold still stamped `hermes` is recognized
# only so init can switch it to one of these.
HARNESSES = ["claude", "copilot"]
RETIRED_HARNESSES = {"hermes": ".agents/skills"}

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
    "copilot": [".github/prompts", ".github/agents", COPILOT_HOOKS_DIR],
    # Retired in 10.0, kept so a switch away from it reports leftovers.
    "hermes": [".agents/skills", ".agents/hooks"],
}

# A command name that collides with a harness built-in is renamed on every
# harness, not just the one that reserves it (CONCEPT.md sections 34 and 35).
# Hermes reserved /update, so this framework ships /framework-update
# everywhere; the name stayed when hermes support was dropped (10.0), since
# renaming it would break every existing project. There is deliberately no per-harness name table any more: one
# command, one name, so every document can name a command without asking
# where it is being read.

# Bodies composed in Python because they vary on harness beyond slot filling.
# Their descriptions live here because they have no template frontmatter.
_SKILL_DESCRIPTIONS = {
    "framework-update": ("Update this scaffold to the current framework "
                         "version: merge the framework files, migrate notes "
                         "and specs, never re-explore"),
}

ARG_HINTS = {
    "explore": "[focus]",
    "task": "[create|do|list|tree] <id> [title...|inline]",
    "agent-models": "[worker=<model>] [reviewer=<model>]",
    "framework-update": "[dry-run]",
}

# The two sub-agents of /task do, per harness: where their agent files live
# and what a missing `model:` line means there (CONCEPT.md section 55).
AGENT_FILES = {
    "claude": (".claude/agents/worker.md", ".claude/agents/reviewer.md"),
    "copilot": (".github/agents/worker.agent.md",
                ".github/agents/reviewer.agent.md"),
}

MODEL_UNSET = {
    "claude": ("the worker runs on the model `/task do` passes when it "
               "spawns it\n(a cheaper one where it can), and the reviewer "
               "on the session's model."),
    "copilot": "the sub-agent runs on the session's model.",
}

MODEL_VERIFY = {
    "claude": "A session reads agent files when it starts; new sessions use "
              "the change.",
    "copilot": "A session reads agent files when it starts; new sessions "
               "use the change.",
}
