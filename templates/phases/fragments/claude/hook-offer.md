
## Verification hook (offer once)
Once the build, test, and lint commands are known, offer the user a Stop
hook in `.claude/settings.json` that runs lint (and fast tests if cheap)
when the agent finishes a turn with code changes. A deterministic check
beats an instruction the model may skip. Add it only with user consent.
Mention the lighter alternative too: a session-scoped `/goal` condition
(e.g. "tests and lint pass") that an evaluator re-checks each turn, good
for a single unattended run without touching settings.
