"""Shared constants: paths, markers, the node tables, and the skill rosters.

Split out so `content` (which renders) and `scaffold` (which writes) can both
import them without importing each other.
"""

from datetime import date

from agentgen import render

TODAY = date.today().isoformat()

FRAMEWORK_VERSION = "5.17"

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
