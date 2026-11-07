#!/usr/bin/env python3
"""The OpenCode plugin against a fake host, without OpenCode or a model.

A scratch scaffold's own plugin file runs under node with a stand-in for the
V2 plugin context: `tool.hook` and `session.hook` hand their callbacks to the
checks below. It proves the bridge: a guarded command throws the script's
message, a harmless one passes, a dirty `.ai` gets one synthetic message and
the next idle passes, and a sub-agent or a session waiting on background work
is left alone. A live run is in tests/task-commands.md. Skips without node.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INIT = REPO / "init_agent.py"

DRIVER = r"""
import { pathToFileURL } from "node:url"
const [plugin, root] = process.argv.slice(2)
const mod = (await import(pathToFileURL(plugin).href)).default
const hooks = {}
const synthetic = []
await mod.setup({
  location: { directory: root },
  tool: { hook: async (name, fn) => { hooks[name] = fn } },
  session: {
    hook: async (name, fn) => { hooks[name] = fn },
    get: async ({ sessionID }) =>
      sessionID === "child" ? { parentID: "root" } : {},
    synthetic: async (m) => { synthetic.push(m) },
  },
})
const out = { hooks: Object.keys(hooks).sort() }
const shell = async (command) => {
  try {
    await hooks["execute.before"]({ tool: "shell", input: { command } })
    return null
  } catch (e) { return e.message }
}
out.harmless = await shell("git status")
out.coauthor = await shell('git commit -m "x\n\nCo-Authored-By: a <a@b>"')
out.merge = await shell("git merge topic")
const idle = async (sessionID, background = []) => {
  await hooks["experimental.idle"]({ sessionID, background })
  return synthetic.length
}
out.child = await idle("child")
out.waiting = await idle("s1", [{}])
out.first = await idle("s1")
out.text = synthetic[0]?.text ?? ""
out.second = await idle("s1")
out.third = await idle("s1")
console.log(JSON.stringify(out))
"""

failures = []


def fail(msg):
    failures.append(msg)


def main():
    if shutil.which("node") is None:
        print("skip: node not found")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "p"
        root.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root,
                       check=True)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "i"],
                       cwd=root, check=True,
                       env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                            "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t",
                            "PATH": "/usr/bin:/bin:/opt/homebrew/bin"})
        subprocess.run([sys.executable, str(INIT), "--name", "t",
                        "--description", "d", "--harness", "opencode", "-y"],
                       cwd=root, check=True, capture_output=True)
        with (root / ".ai" / "notes.md").open("a") as f:
            f.write("- dirty\n")
        driver = Path(tmp) / "driver.mjs"
        driver.write_text(DRIVER)
        r = subprocess.run(
            ["node", str(driver),
             str(root / ".opencode/plugins/llm-agent.js"), str(root)],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"FAIL: driver exit {r.returncode}: {r.stderr}")
            return 1
        out = json.loads(r.stdout)

    if out["hooks"] != ["execute.before", "experimental.idle"]:
        fail(f"registered hooks: {out['hooks']}")
    if out["harmless"] is not None:
        fail(f"git status was blocked: {out['harmless']}")
    if "co-author" not in (out["coauthor"] or ""):
        fail(f"co-author commit not blocked with the reason: {out['coauthor']}")
    if "default branch" not in (out["merge"] or ""):
        fail(f"merge into main not blocked with the reason: {out['merge']}")
    if out["child"] != 0:
        fail("a sub-agent's idle was told about .ai")
    if out["waiting"] != 0:
        fail("a session waiting on background work was told about .ai")
    if out["first"] != 1 or "notes.md" not in out["text"]:
        fail(f"dirty .ai: {out['first']} message(s), text {out['text']!r}")
    if out["second"] != 1:
        fail("the idle after the message did not pass, so the loop can trap")
    if out["third"] != 2:
        fail("a later turn end with .ai still dirty was not told again")

    for msg in failures:
        print(f"FAIL: {msg}")
    if not failures:
        print("ok: plugin blocks, passes, and keeps the idle loop finite")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
