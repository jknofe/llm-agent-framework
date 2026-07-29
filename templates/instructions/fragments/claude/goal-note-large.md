
## Autonomous dispatch (/goal)
`/goal` adds no new definition of done - `/implement` already has one:
every task in `plan.md` at `status: done`, plus the ticket review gate's
sign-off. `/goal` only changes whether the agent stops to ask permission
between tasks or keeps going on its own until the plan is fully done.
Reach for it when both hold: each task's acceptance criteria are checkable
by a machine (tests, lint, a named gate script), and no mid-flight
judgment call is expected - a `/goal` loop cannot ask you a question, so
save it for tickets that already cleared planning's Q&A. Invoke
`/implement <id>` first, then set the goal: skills here are not
model-invocable, so the loop can only follow the phase procedure if its
instructions are already in context. Point the condition at `plan.md`
(never restate a looser version), make the agent prove it in output -
the goal evaluator reads only the transcript, never files - and bound
the run with a turn cap:
```
/goal every task in .ai/knowledgebase/tasks/<id>/plan.md is status:done
and shown, the transcript shows the ticket review gate passing, and .ai
is committed; or stop after 30 turns
```
Pair it with the same stall rule as a manual `/implement` run: on
`test-fail` twice on the same task, stop rather than a third blind
attempt - the loop has no one else to escalate to.
