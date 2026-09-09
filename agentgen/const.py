"""Shared constants: paths, markers, the node tables, and the skill rosters.

Split out so `content` (which renders) and `scaffold` (which writes) can both
import them without importing each other.
"""

from datetime import date

from agentgen import render

TODAY = date.today().isoformat()

FRAMEWORK_VERSION = "5.21"

FRAMEWORK_JSON = ".ai/agent/framework.json"

KB_DIRS = [
    "architecture",
    "conventions",
    "domain",
    "infra",
    "decisions",
    "references",
    "tasks",
    "tasks/_archive",
]

HOT_NODES = {
    "architecture/overview.md": {
        "id": "architecture/overview",
        "summary": "High-level architecture: modules, data flow, entry points",
        "tags": ["architecture", "overview"],
        "covers": ["src/**"],
        "tier": "hot",
        "body": (
            "# Architecture Overview\n\n"
            "<!-- Filled in Phase 1 (Initialization). -->\n\n"
            "## Modules\n\n## Data Flow\n\n## Entry Points\n"
        ),
    },
    "conventions/code-style.md": {
        "id": "conventions/code-style",
        "summary": "Code style, naming, formatting, linting rules",
        "tags": ["conventions", "style", "lint"],
        "covers": ["**/*"],
        "tier": "hot",
        "body": (
            "# Code Style\n\n"
            "<!-- Source: linter configs + user Q&A at init. -->\n"
        ),
    },
    "domain/glossary.md": {
        "id": "domain/glossary",
        "summary": "Domain terms and their precise project meaning",
        "tags": ["domain", "glossary"],
        "covers": [],
        "tier": "hot",
        "body": "# Glossary\n\n| Term | Meaning |\n|---|---|\n",
    },
}

COLD_NODE_TEMPLATES = {
    "conventions/testing.md": {
        "id": "conventions/testing",
        "summary": "Test layout, frameworks, coverage expectations",
        "tags": ["conventions", "testing"],
        "covers": ["tests/**", "**/*test*"],
        "tier": "cold",
        "body": "# Testing Conventions\n\n<!-- Filled at init. -->\n",
    },
    "conventions/git-workflow.md": {
        "id": "conventions/git-workflow",
        "summary": "Branching, commit message rules, review gates",
        "tags": ["conventions", "git"],
        "covers": [],
        "tier": "cold",
        "body": "# Git Workflow\n\n<!-- Filled at init. -->\n",
    },
    "infra/build.md": {
        "id": "infra/build",
        "summary": "Build system, targets, local dev setup",
        "tags": ["infra", "build"],
        "covers": ["Makefile", "*.toml", "*.gradle", "CMakeLists.txt", "package.json"],
        "tier": "cold",
        "body": "# Build\n\n<!-- Filled at init. -->\n",
    },
    "infra/ci-cd.md": {
        "id": "infra/ci-cd",
        "summary": "CI/CD pipelines, stages, deployment targets",
        "tags": ["infra", "ci", "cd"],
        "covers": [".github/**", ".gitlab-ci.yml", "Jenkinsfile"],
        "tier": "cold",
        "body": "# CI/CD\n\n<!-- Filled at init. -->\n",
    },
}

ALL_NODES = {**HOT_NODES, **COLD_NODE_TEMPLATES}

PHASES_DIR = ".ai/agent/phases"

TOOLS_DIR = ".ai/agent/tools"

GEN_BEGIN = ("<!-- BEGIN GENERATED:project-context "
             "(source: hot-tier nodes, max 1500 tokens) -->")

GEN_BEGIN_SMALL = ("<!-- BEGIN GENERATED:project-context "
                   "(source: /explore, max 1500 tokens) -->")

GEN_END = "<!-- END GENERATED:project-context -->"

SKILLS_LARGE = ["explore", "add-ticket", "plan", "implement", "add-reference",
                "import-kb", "import", "tidy-up", "update"]

SKILLS_SMALL = ["explore", "spec", "build", "import-kb", "import",
                "tidy-up", "update"]

# Where the hermes harness looks for project skills. Hermes reads both
# `.hermes/skills/` and `.agents/skills/` under the nearest git root; the
# scaffold uses the second because it is the cross-tool location, so a project
# that later adds another SKILL.md reader does not need a second copy.
HERMES_SKILLS_DIR = ".agents/skills"

# Hermes ships built-in slash commands, and three of the framework's names are
# taken: /update, /import and /plan. A project skill cannot be counted on to
# reach past a built-in, so on that harness those three are emitted under a
# different name. Every other command keeps its name everywhere. Prose that
# names one of the three goes through the `cmd_*` slots (see
# `content.command_slots`) so a renamed command is not referred to by a name
# that does not exist there.
HERMES_COMMAND_NAMES = {
    "update": "framework-update",
    "import": "import-agent",
    "plan": "plan-ticket",
}

# Hermes caps a skill description at 60 characters, which the descriptions in
# the skill templates (written for the claude and copilot frontmatter) exceed.
# One short, self-contained, period-terminated line per command; the roster
# names, not the hermes names, are the keys.
HERMES_DESCRIPTIONS = {
    "explore": "Survey the codebase and record what it finds.",
    "add-ticket": "Add a ticket to the inbox.",
    "plan": "Turn an inbox ticket into a task plan.",
    "implement": "Implement a planned ticket.",
    "add-reference": "Register external material as a reference.",
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

_SKILL_DESCRIPTIONS = {
    ("large", "tidy-up"): ("Hygiene sweep that may not change behavior: remove "
                           "dead code, propose obsolete files, shorten "
                           "comments, drop em dashes"),
    ("small", "tidy-up"): ("Hygiene sweep that may not change behavior: remove "
                           "dead code, propose obsolete files, shorten "
                           "comments, drop em dashes"),
    ("large", "update"): ("Update this scaffold to the current framework "
                          "version: merge the framework files, migrate the KB "
                          "in place, never re-explore"),
    ("small", "update"): ("Update this scaffold to the current framework "
                          "version: merge the framework files, migrate notes "
                          "and specs, never re-explore"),
}

ARG_HINTS = {
    "explore": "[focus]",
    "add-ticket": "<id> <title...>",
    "plan": "<ticket-id>",
    "implement": "<ticket-id>",
    "add-reference": "<name> <origin>",
    "import-kb": "<source>",
    "import": "<source>",
    "spec": "<id> <title...>",
    "build": "<id>",
    "tidy-up": "[scope]",
    "update": "[dry-run]",
}

# Shared manifest-parsing code spliced into the three KB tools that need
# it. Lives as a real file so it is linted once instead of three times.
_MANIFEST_PARSER = render.load("tools/_manifest_parser.py")

RULES_MARKER = "by gen_rules.py. Edit the source node, not this file."

CODE_EXTS = {
    ".py", ".rs", ".go", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".java",
    ".kt", ".rb", ".php", ".c", ".h", ".hpp", ".cpp", ".cc", ".cs",
    ".swift", ".scala", ".sh", ".bash", ".sql",
}

SKIP_DIRS = {
    ".git", ".ai", "node_modules", "vendor", "target", "dist", "build",
    ".venv", "venv", "__pycache__", ".mypy_cache", ".tox", ".next", "out",
}

SIZE_LOC_THRESHOLD = 10000
