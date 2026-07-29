## Autonomous dispatch (/goal)
`/goal` adds no new definition of done - `/build` already has one: the
spec's acceptance criteria, the gate command, the reviewer's sign-off.
`/goal` only changes whether the agent stops to ask permission between
those steps or keeps going on its own until they are met. Reach for it
when both hold: the finish line is something a machine can check (tests
pass, lint clean, a named gate script exits 0), and no mid-flight judgment
call is expected - a `/goal` loop cannot ask you a question. Invoke
`/build <id>` first, then set the goal: skills here are not
model-invocable, so the loop can only follow the build procedure if its
instructions are already in context. Point the condition at the artifact
that already defines done (never restate a looser version), make the
agent prove it in output - the goal evaluator reads only the transcript,
never files - and bound the run with a turn cap:
```
/goal every acceptance criterion in .ai/changes/<id>/spec.md is checked
off and shown, the transcript shows the gate command exiting 0, and the
reviewer reports no correctness gaps; or stop after 20 turns
```
Pair it with the same stall rule as a manual `/build` run: if 2
consecutive turns make no measurable progress on the same blocker, stop
and report it instead of a third blind attempt - the loop has no one else
to escalate to.

