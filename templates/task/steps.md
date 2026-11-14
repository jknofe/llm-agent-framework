# /task: Steps

The working steps of a task, read by the worker from `work.md` and by a
session that works a task itself instead of handing it to a worker. Both roles work the steps the same way.

1. Work the steps in order. Explore the real code, logs, and docs with
   read/search tools as needed; do not load the whole tree. Tick a step
   when it is done (`tasks.py tick <id> steps <n>`). Code ships through
   the review gate: before its first commit, and before a push of code
   changed since the last review, the review gate runs on the uncommitted diff
   (a worker asks for it with a `review` report).
2. Record findings as they happen, not at the end: append each to
   `## Findings`, dated, telegraphic, one line of at most ~200
   characters: the claim and one pointer to its evidence (file and line,
   a command and its result line, a URL), never the evidence itself.
   Group checks of the same kind in one line (`checks: yamllint,
   xmllint, bash -n OK`). Evidence too long for that (a list of
   commands, a log, a summary of a document read) goes into
   `.ai/tasks/<id>/evidence.md`, and the finding points at it; often it
   is not worth keeping at all. Do not restate a rule, or what you did
   not do (`no merge, no push`): the rules hold without it.
   `tasks.py` flags a Findings line over 300 characters, except a
   `Supervisor round` line: a correction stays as long as it must to be
   exact. A finding the file does not hold is lost at the next session. Commit `.ai` after each finding that changes the
   direction of the task.
3. Re-plan openly. When a result invalidates the plan (a hypothesis is
   ruled out, a new lead appears, a scenario cannot run), edit `##
   Steps`: mark the dead step `- [x] ~~H1~~ ruled out: <evidence>`, add
   the new steps, and say so in Findings. Do not drift away from the
   written plan without changing it. If the new direction changes the
   Goal or a Done-when criterion, stop and ask the user: they approved
   the old ones (a worker asks with a `question` report). When the task
   cannot continue without something outside your reach (hardware,
   access, another team), put the detail in Findings and run `python3 ${tools_dir}/tasks.py finish <id> blocked
   <reason in one line>`: it sets `status: blocked` and the `blocked:`
   line `/task list` shows, and keeps the pointer. `tasks.py start`
   clears the block when the task resumes.
4. Whenever the task changes code, whatever its type: run the tests
   that cover the change, every one that exercises the changed code and
   not only one a criterion names, and lint on the changed files; that
   is also all a review round needs. The project's full suite is not the
   task's: CI on a push or the user's run on the target covers it. While
   a task runs in parallel, those tests also see its unfinished edits: a failure in a
   file that task claimed is not yours to fix; record it in Findings and
   rerun once that task finishes.
   What gets a test: tests are for logic, code that computes, branches or
   transforms, and every piece of logic the task adds or changes gets one
   that stays in the suite; running it once by hand is not a test. Declarative files only state what they are:
   configuration, manifests, build files, CI workflows, package metadata,
   data (YAML, JSON, TOML, XML, CMake, Dockerfiles, workflow files and
   the like). Their check is the linter or validator that reads the changed file
   (`actionlint`, `yamllint`, a schema validator, `hadolint`, `terraform
   validate`). A build, a CI run, a plan or a start on the target is CI's
   or the user's, never the task's unless the user asks for it.
   Before you keep any test, ask: could this assertion fail for a reason
   other than someone editing, on purpose, the file it reads? If not, it
   is a change-detector test: do not write it. A test that loads a
   declarative file and compares its values to literals is one. A
   test's expected value comes from the requirement, never from the file
   or the code under test. Code inside a declarative file (a workflow's
   `run:` step, a CMake function with logic) and code that generates or
   rewrites one is logic and gets tested like other code. A rule across
   files that no linter expresses is a policy check, not a change
   detector, and is kept: it asserts a rule, not a value (every database
   module passes its storage size; the cleanup workflow removes every
   deployment the deploy script registers).

Escalate instead of improvising: on missing context, do bounded
discovery then ask the user; if a test fails twice on the same step, or
two hypotheses in a row die without a new lead, stop and rethink the
approach rather than make a third blind attempt.
