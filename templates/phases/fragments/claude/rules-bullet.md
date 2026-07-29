- Path-scoped rules under `.claude/rules/` are generated from cold
  `conventions/*` nodes; the PostToolUse hook regenerates them on
  conventions-node and manifest writes. Never edit a GENERATED rule
  file; edit the node (run `python3 ${tools_dir}/gen_rules.py` by hand
  only if no hook fired).
