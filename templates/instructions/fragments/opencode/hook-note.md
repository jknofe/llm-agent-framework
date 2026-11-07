 The plugin `.opencode/plugins/llm-agent.js` blocks ending a turn
   while `.ai` is dirty and blocks rules 5 and 6 at the shell, but
   only when this repo is the session's project directory; otherwise
   follow them by hand and never assume a hook ran.