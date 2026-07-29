# Phase 2: Planning

Read this before decomposing a ticket.

## Workflow
1. Locate the ticket in the inbox: `.ai/tickets/<id>*.md` (created via
   /add-ticket or dropped in by the user). If it is missing, ask the user
   for the ticket content.
2. Create `.ai/knowledgebase/tasks/<id>/`: move the inbox file's content into
   `ticket.md` (format below) and set its frontmatter `status: planned` (it
   was `status: new` in the inbox), then delete the inbox file.
3. Load matched KB nodes (protocol budgets apply).
4. Run interactive Q&A with the user until the acceptance criteria are
   unambiguous. Keep the rounds bounded. Record answers in `ticket.md`. If no
   human is available (autonomous run), do not block: resolve each open
   question from the evidence, record it as a single numbered assumption (the
   decision, not your deliberation) in `ticket.md`, and proceed.
5. Write one task file per task. `plan.md` stays a thin index.
6. Plan-review gate: have the plan reviewed in a fresh context that did not
   produce it. Use the `reviewer` sub-agent where the harness supports
   sub-agents. If it cannot be spawned (e.g. you are yourself a sub-agent) and
   no human is available (autonomous run), spawn a fresh general-purpose
   sub-agent given only the plan and the acceptance criteria, never your own
   working context; if no fresh context is reachable at all, do a
   clean-context self-review against this gate's checklist and record that the
   `reviewer` sub-agent was unavailable. Never silently skip the gate. Fix gaps
   that touch the acceptance criteria, then get user sign-off on `plan.md` (in
   an autonomous run, record the assumptions instead) before implementation
   starts. A weak plan poisons every downstream task.
7. Commit the `.ai` repo (`plan: <id>`).

## Trivial tickets
If the ticket touches one or two files and the diff fits in one sentence,
skip the Q&A rounds and write a single task file `01-task.md`. The
plan-review gate shrinks to a one-line user sign-off. Do not pay planning
ceremony that exceeds the task.

## ticket.md format
Frontmatter: `id`, `title`, `status: planned`, `created: <date>`.
Body: the original ticket description, then a `## Q&A (Planning)` section
with the recorded answers.

## Task file format (`NN-<slug>.md`)
Frontmatter: `status: planned`, `depends: []`, `parallel: ok|no`.
Set `parallel: ok` only when the task has no `depends` entries and its
affected files overlap with no other task's; such tasks may be dispatched to
concurrent sessions (see implementation.md, Parallel dispatch). When in
doubt, `no`.
Body, self-contained:
- Goal and testable acceptance criteria that cover ecosystem correctness, not
  just "it runs": where a linter or policy check exists for the ecosystem you
  touch (eslint, mypy/ruff, clippy, shellcheck, lintian, a schema validator),
  name it and make passing it a criterion
- Affected files with explicit paths
- Pre-bound KB node ids
- Expected signatures/interfaces
- Test skeletons

Pre-binding is a warm start, not a contract: implementation starts from the
bound nodes and files and may run at most 5 targeted searches of its own
before escalating `missing-context`.

## plan.md format
Frontmatter: `ticket: <id>`, `status: planned`,
`read-first: ${phases_dir}/implementation.md`,
`kb-commit: <output of git -C .ai rev-parse HEAD>`, `updated: <date>`.
Body: index only, a task table
`| # | Task file | Depends on | Parallel | Status |`.
`kb-commit` records the KB state the plan was built against; the
implementation phase diffs against it to detect drift. The `read-first`
pointer forces the implementing session to load its phase doc. Do not
remove either.
