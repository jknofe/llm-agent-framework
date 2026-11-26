#!/usr/bin/env python3
"""The generated `.opencode/opencode.json` and the `instructions` key of it
that carries the notes hub (CONCEPT.md section 86).

Run: python3 tests/test_opencode_config.py

Stdlib only. Scaffolds an opencode project with the real init_agent.py: a
fresh one has `instructions: [".ai/notes.md"]` and the permissions; a forced
re-init keeps a user's own entries in their order and adds the hub once;
never twice; a value that is not a list of strings and an unreadable file
are replaced; `permissions` is regenerated and any other key a user added
(a model, MCP servers, sharing) survives, section 87; claude and copilot have no
such file; the update body names the merge case.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from agentgen import content  # noqa: E402

FAILS = []
N = [0]


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAILS.append(msg)


def init(root, harness="opencode"):
    return subprocess.run(
        [sys.executable, str(REPO / "init_agent.py"), "--name", "p",
         "--description", "d", "--harness", harness, "-y"], cwd=root,
        capture_output=True, text=True, input="n\n")


def main():
    root = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    init(root)
    f = root / ".opencode/opencode.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    check(d.get("instructions") == [".ai/notes.md"],
          f"fresh: the hub is the one entry: {d.get('instructions')}")
    check(d.get("permissions"), "fresh: permissions still there")

    def reinit(value, extra=None):
        data = json.loads(f.read_text(encoding="utf-8"))
        data["instructions"] = value
        data["permissions"] = []
        data.update(extra or {})
        f.write_text(json.dumps(data), encoding="utf-8")
        init(root)
        return json.loads(f.read_text(encoding="utf-8"))

    d = reinit(["docs/a.md", ".ai/notes.md", "z/*.md"])
    check(d["instructions"] == ["docs/a.md", ".ai/notes.md", "z/*.md"],
          f"user entries and order kept, no duplicate: {d['instructions']}")
    check(d["permissions"], "the permissions are regenerated")
    d = reinit(["docs/a.md"])
    check(d["instructions"] == ["docs/a.md", ".ai/notes.md"],
          f"the hub is added once at the end: {d['instructions']}")
    init(root)
    d = json.loads(f.read_text(encoding="utf-8"))
    check(d["instructions"] == ["docs/a.md", ".ai/notes.md"],
          "a second re-init changes nothing")
    d = reinit([])
    check(d["instructions"] == [".ai/notes.md"], "an empty list gets the hub")
    for bad in ("x.md", 3, None, {"a": 1}, ["a", 2]):
        d = reinit(bad)
        check(d["instructions"] == [".ai/notes.md"],
              f"{bad!r} is replaced by the default: {d['instructions']}")
    f.write_text("{not json", encoding="utf-8")
    init(root)
    d = json.loads(f.read_text(encoding="utf-8"))
    check(d["instructions"] == [".ai/notes.md"], "unreadable file replaced")
    f.write_text("[1]", encoding="utf-8")
    init(root)
    check(json.loads(f.read_text())["instructions"] == [".ai/notes.md"],
          "a JSON non-object is replaced")

    # A user's own keys survive a forced re-init (section 87).
    d = reinit(["docs/a.md"], {"share": "disabled", "model": "p/m",
                               "mcp": {"x": {"type": "local"}}})
    check(d.get("share") == "disabled", f"share kept: {d.get('share')}")
    check(d.get("model") == "p/m" and d.get("mcp") == {"x": {"type": "local"}},
          "other user keys kept")
    check(d["permissions"], "permissions regenerated beside user keys")
    init(root)
    d2 = json.loads(f.read_text(encoding="utf-8"))
    check(d2 == d, "a second re-init changes nothing")
    f.write_text("{not json", encoding="utf-8")
    init(root)
    check("share" not in json.loads(f.read_text()),
          "an unreadable file is replaced, nothing to keep")

    # An unforced re-init leaves the file alone.
    f.write_text(json.dumps({"instructions": ["mine.md"]}), encoding="utf-8")
    subprocess.run([sys.executable, str(REPO / "init_agent.py"), "--name",
                    "p", "--description", "d", "--harness", "opencode"],
                   cwd=root, capture_output=True, text=True, input="n\n")
    check(json.loads(f.read_text())["instructions"] == ["mine.md"],
          "a bare re-init skips the existing file, as before")

    for harness in ("claude", "copilot"):
        d = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        init(d, harness)
        check(not (d / ".opencode").exists(), f"{harness}: no opencode file")
    body = [b for n, _d, b in content.command_specs("opencode", "$A", "$A")
            if n == "framework-update"][0]
    check("`instructions` in `.opencode/opencode.json`" in body
          and "never twice" in body, "the update body names the merge case")
    if FAILS:
        for x in FAILS:
            print(f"FAIL {x}")
        return 1
    print(f"ok: opencode config, {N[0]} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
