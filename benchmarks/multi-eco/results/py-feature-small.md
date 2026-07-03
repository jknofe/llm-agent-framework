# Benchmark results: py-feature-small

## Configuration

| Key | Value |
|---|---|
| Run ID | py-feature-small |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Target repo | simonw/sqlite-utils @ 79117b9 |
| Feature | rename-column CLI command + Table.rename_column() API |
| Start | 2026-07-02T19:04:32 |
| End | 2026-07-03T01:46:16 |
| Duration | ~6h42m wall clock; ~35-40 min active. Run was interrupted by a Claude session limit right after the review sub-agent was dispatched (~19:15) and resumed after the limit reset (~01:35). |
| Container status | PASS |

## Spec produced

`.ai/changes/rename-column/spec.md` — goal, 6 acceptance criteria (implementation,
error taxonomy, CLI shape, tests, docs incl. cog regeneration, and the repo's own
CI gates: pytest / mypy / flake8 / black --check / cog --check), 7 tasks, and 5
numbered assumptions. Assumption 4 (inherit transform()'s silent column-name-collision
quirk) was revised after the review gate: the reviewer verified the quirk silently
destroys data, so a guard was added (see below). Status: done.

## .ai commit history

```
5791612 build: rename-column
429e7a5 spec: rename-column
587f601 explore: project context
96d394b init: small-profile scaffold (sqlite-utils)
```

4 commits total (1 scaffold + 3 workflow).

## Diff stat (host repo, uncommitted working tree)

```
.gitignore             |  1 +   (init_agent.py scaffold: ignores .ai/)
docs/cli-reference.rst | 20 +   (cog refs entry + regenerated --help block)
docs/cli.rst           | 15 +   (new "Renaming a column" section)
docs/python-api.rst    | 15 +   (new "Renaming a column" section)
sqlite_utils/cli.py    | 29 +   (rename-column command)
sqlite_utils/db.py     | 17 +   (Table.rename_column method)
tests/test_cli.py      | 55 +   (test_rename_column)
tests/test_create.py   | 18 +   (test_rename_column)
8 files changed, 170 insertions(+)
```

## Container output (python:3.12, final diff)

```
pip install -q -e . pytest hypothesis   -> ok
python -m pytest -q                     -> 1084 passed, 16 skipped, 1 warning in 7.57s
```

PASS — full suite green including the new tests. Baseline at 79117b9 collects
1096 tests; the diff adds 4 collected test cases (2 new test functions +
2 new parametrized cases in tests/test_docs.py that automatically cover any
new CLI command).

## Feature shape

- Files touched: sqlite_utils/db.py, sqlite_utils/cli.py, tests/test_create.py,
  tests/test_cli.py, docs/cli.rst, docs/python-api.rst, docs/cli-reference.rst.
- CLI mirrors rename-table UX: yes — same positional shape
  (`PATH TABLE COLUMN NEW_NAME`), same `--ignore` flag, same
  `_register_db_for_cleanup` / `_load_extensions` body, same
  `'X could not be renamed. <reason>'` ClickException message shape, placed
  directly after rename-table in cli.py.
- Delegation to transform(): yes — `Table.rename_column` validates
  (NoTable / AlterError) then calls `self.transform(rename={old: new})`;
  no new SQL written.
- Tests added: 2 test functions (tests/test_create.py::test_rename_column,
  tests/test_cli.py::test_rename_column) covering happy path with data
  preservation, missing column, missing table, `--ignore`, and
  new-name-already-in-use; +2 auto-parametrized docs-coverage cases.
- Extra correctness hardening from the review gate: `rename_column` raises
  `AlterError("Column already exists: ...")` when the new name collides with
  another column — the reviewer demonstrated that raw `transform(rename=...)`
  silently destroys the target column's data in that case.
- Local ecosystem checks (the repo's CI gates) all green: pytest (1084 passed),
  mypy sqlite_utils tests (clean), flake8 (clean), black --check (clean on
  package+tests; one pre-existing scaffold hook file outside the feature is
  not black-formatted), cog --check (clean), codespell (clean).

## Project-context refresh

- Fired: yes (probe.py re-run after implementation per build skill step 5).
- Drift: none actionable — build/test/lint commands unchanged, module map
  unchanged except bare LOC deltas on existing modules (tests 11915->11973,
  sqlite_utils 8737->8779), which the skill says to leave.
- AGENTS.md changed by refresh: no (project-context section left as filled
  by /explore).

## Observations

- The repo's own test suite enforces documentation: tests/test_docs.py
  parametrizes over `cli.cli.commands` and fails for any command not shown in
  docs/cli.rst — this caught the missing prose docs before any human review
  would have (1 failed on first full run, fixed by the planned docs task).
- docs/cli-reference.rst being cog-generated worked exactly as recorded in
  .ai/notes.md during explore: one refs-dict entry + `cog -r` produced the
  correct reference section; `cog --check` then passed.
- Review gate value was real: the fresh-context reviewer went beyond
  criteria-checking and executed the collision case, converting a documented
  assumption ("inherit the transform quirk") into a found data-loss bug that
  was then fixed with a 4-line guard + tests + docs.
- Session-limit resilience: the first reviewer dispatch died on the session
  limit; state (spec, .ai/.current, working tree) survived untouched and the
  run resumed cleanly, re-dispatching the reviewer with the same diff file.
- rtk hook quirks on the host (grep/pytest output rewriting) required falling
  back to `rtk proxy` / python one-liners for reliable output; container run
  was unaffected.
