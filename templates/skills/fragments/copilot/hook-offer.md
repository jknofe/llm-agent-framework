Once the build/test/lint commands are known, offer the user an `agentStop`
hook in `.github/hooks/llm-agent.json` that runs lint (and fast tests if
cheap) on turn end, so "done = checks pass" is a hard gate. Add it only
with consent.
