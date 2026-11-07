// OpenCode V2 plugin: runs the framework's two hook scripts, the same ones the
// other harnesses call directly. OpenCode has no command hooks, so this file
// is only the bridge; the rules stay in the Python.
//
// `tool.hook("execute.before")`: git_guard.py inspects any tool call carrying
// a `command`. Exit 2 blocks it; a throw is how a hook refuses a tool call.
// `session.hook("experimental.idle")`: ai_repo_clean.py checks `.ai` when a
// session is about to go idle. A synthetic message keeps it working, once.
//
// A missing python3 or script passes: like the scripts, the bridge never
// blocks work it could not judge.
import { spawnSync } from "node:child_process"
import { existsSync } from "node:fs"
import { join } from "node:path"

const HOOKS = ".opencode/hooks"

function run(directory, script, payload) {
  return spawnSync("python3", [join(directory, HOOKS, script)], {
    cwd: directory,
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: 15000,
  })
}

export default {
  id: "llm-agent",
  setup: async (ctx) => {
    // A worktree's own directory first, then the project root.
    const directory = [ctx.location.directory, ctx.location.project?.directory]
      .find((dir) => dir && existsSync(join(dir, HOOKS)))
    if (!directory) return

    await ctx.tool.hook("execute.before", (call) => {
      const result = run(directory, "git_guard.py", {
        tool_name: call.tool,
        tool_input: call.input,
        cwd: directory,
      })
      if (result.status === 2) {
        throw new Error(result.stderr.trim() || "Blocked by git_guard.py")
      }
    })

    // Sessions told about a dirty `.ai`: their next idle passes, so a repo
    // the agent cannot commit never traps the loop.
    const told = new Set()
    await ctx.session.hook("experimental.idle", async ({ sessionID, background }) => {
      // Its own worker is still running and will wake it; a sub-agent's turn
      // end is not the user's, as with Claude Code's Stop.
      if (background.length > 0) return
      const session = await ctx.session.get({ sessionID })
      if (session.parentID) return
      const result = run(directory, "ai_repo_clean.py", {
        cwd: directory,
        stop_hook_active: told.delete(sessionID),
      })
      let verdict = {}
      try {
        verdict = JSON.parse(result.stdout)
      } catch {
        return
      }
      if (verdict.decision !== "block") return
      told.add(sessionID)
      await ctx.session.synthetic({
        sessionID,
        text: verdict.reason,
        description: "Uncommitted .ai changes",
      })
    })
  },
}
