"""Template loading and slot filling.

Content the generator emits lives under `templates/` as real files: the tools
and hooks as `.py` that a linter can actually read, the instructions, phase
docs, and skill bodies as markdown. This module is the only thing that reads
them.

Slots use `string.Template` syntax (`$name`, `${name}`) rather than
`str.format`. The reason is escaping: the emitted content is full of literal
braces (JSON, dict literals, f-strings inside the generated tools) that
`str.format` would demand be doubled, and a missed escape there is a silent
corruption. `Template.safe_substitute` ignores braces entirely and leaves
unknown `$NAME` alone, so the harness variables that must survive into the
output verbatim (`$ARGUMENTS`, `$LLM_AGENT_HOME`, `$CLAUDE_PROJECT_DIR`) need
no escaping either. Keep slot names lowercase so they cannot collide with
those.
"""

from pathlib import Path
from string import Template

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

# Reserved: uppercase names that appear literally in emitted content and must
# never be used as slot names, or safe_substitute would eat them.
PASSTHROUGH = ("ARGUMENTS", "LLM_AGENT_HOME", "CLAUDE_PROJECT_DIR")

_cache = {}


def load(rel: str) -> str:
    """Read a template verbatim. Cached: a scaffold run reads some of these
    once per profile and the files never change mid-run."""
    if rel not in _cache:
        path = TEMPLATES / rel
        if not path.is_file():
            raise FileNotFoundError(f"template missing: {path}")
        _cache[rel] = path.read_text()
    return _cache[rel]


def fill(rel: str, **slots) -> str:
    """Read a template and substitute its slots.

    Unknown `$NAME` passes through untouched, which is what keeps the harness
    variables intact. That also means a typo in a slot name fails silently, so
    `check_slots` exists to catch it in the test layer instead.
    """
    for key in slots:
        if key.upper() in PASSTHROUGH:
            raise ValueError(f"slot name collides with a passthrough var: {key}")
    return Template(load(rel)).safe_substitute(**slots)


def render(text: str, **slots) -> str:
    """Same substitution for a string already in hand (a composed body)."""
    return Template(text).safe_substitute(**slots)


def sectioned_list(rel: str, sections: tuple, **slots) -> list:
    """Read a line-per-entry data file split by `[section]` headers and return
    the entries of the named sections, in file order, slots substituted.

    Blank lines and `#` comments are dropped. Used for list data that varies by
    profile (the permission allow list), where the entries are data but which
    subset applies is logic.
    """
    out, keep = [], False
    for line in load(rel).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            keep = line[1:-1] in sections
            continue
        if keep:
            out.append(Template(line).safe_substitute(**slots))
    return out


def slots_in(rel: str) -> set:
    """Every `$name`/`${name}` the template declares, lowercase ones only.

    Uppercase matches are passthrough harness variables, not slots. Used by
    the test layer to assert that what a template asks for is what the caller
    passes, since `safe_substitute` will not complain on its own.
    """
    import re
    text = load(rel)
    found = set(re.findall(r"\$\{?([a-z_][a-z_0-9]*)\}?", text))
    return found
