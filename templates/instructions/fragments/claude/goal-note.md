## Autonomous dispatch (/goal)
`/goal` changes only whether you stop to ask between steps. Use it when the
finish line is machine-checkable and no judgment call is expected. Point the
condition at the artifact that defines done (the gate command; for a spec'd
change also the spec's criteria and the reviewer), make the agent show it in
output, and cap the turns:
```
/goal the transcript shows the full test and lint commands exiting 0; or
stop after 20 turns
```
If 2 consecutive turns make no progress on the same blocker, stop and
report instead of a third blind attempt.

