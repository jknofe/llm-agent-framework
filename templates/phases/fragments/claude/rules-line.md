- Cold `conventions/*` nodes with `covers` globs also render to
  path-scoped rule files under `.claude/rules/` (loaded by the
  harness when matching files are touched). The same PostToolUse
  hook regenerates them on every conventions-node or manifest
  write. Never edit the rule files; edit the node.
