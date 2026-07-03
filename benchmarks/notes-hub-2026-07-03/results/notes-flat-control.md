# Benchmark Result: notes-flat-control

CONTROL cell for the notes-hub feature. Expected correct outcome: notes.md
stays a single flat file; NO `.ai/notes/` hub is created because notes stay
short.

## Configuration

| Field | Value |
|---|---|
| Run ID | notes-flat-control |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Project | sqlite-utils (simonw/sqlite-utils @ 79117b9) |
| Task | rename-column: add `rename-column` CLI command + `Table.rename_column(old, new)` API |
| Start | 2026-07-03T11:56:40 |
| End | 2026-07-03T12:22:39 |
| Duration | ~26 min |
| Code container status | PASS |

## .ai commit history

```
03f9211 build: rename-column
a532418 spec: rename-column
0b8ae97 explore: project context
a62daeb init: small-profile scaffold (sqlite-utils)
```

## git diff --stat HEAD (host repo, implementation)

```
docs/changelog.rst      |  1 +
docs/cli-reference.rst  | 20 ++++++++++++++++++++
docs/cli.rst            | 15 +++++++++++++++
docs/python-api.rst     | 13 +++++++++++++
sqlite_utils/cli.py     | 29 +++++++++++++++++++++++++++++
sqlite_utils/db.py      | 16 ++++++++++++++++
tests/test_cli.py       | 41 +++++++++++++++++++++++++++++++++++++++++
tests/test_transform.py | 37 ++++++++++++++++++++++++++++++++++++-
8 files changed, 171 insertions(+), 1 deletion(-)
```

Implementation summary:
- `Table.rename_column(name, new_name)` in `db.py`: delegates to
  `self.transform(rename={name: new_name})`, returns `self`. Guards: `NoTable`
  if table missing, `AlterError` if `name` missing or `new_name` already
  exists (collision guard added after review, see below).
- `rename-column` CLI command in `cli.py`:
  `sqlite-utils rename-column PATH TABLE COLUMN NEW_NAME`, `--ignore`,
  `--load-extension`, wraps failures in `click.ClickException`. Mirrors
  `rename-table`.
- Tests: 4 new (test_transform.py: success, missing-column, missing-table,
  existing-column-collision) + 1 CLI test (test_cli.py: success,
  missing-table, missing-column, --ignore).
- Docs: python-api.rst subsection, cli.rst subsection, changelog.rst entry,
  cli-reference.rst cog block (refs entry + regenerated `--help` via
  `cog -r`).

## Review gate

A fresh general-purpose sub-agent reviewed the full diff against the
acceptance criteria. It found ONE genuine correctness bug: renaming a column
onto an existing column name (`rename_column("age", "name")`) silently dropped
data instead of erroring, because `transform()` tolerates a duplicate column
in its generated CREATE TABLE. Fixed by adding a
`new_name in self.columns_dict` pre-check that raises
`AlterError("Column already exists: X")`, plus a regression test
(`test_rename_column_to_existing_column_errors`). Everything else verified
correct (error conventions consistent with `duplicate()`/`add_foreign_key`,
CLI exception handling, test meaningfulness, flake8/mypy/pytest all green,
cli-reference.rst regenerated correctly, test_docs.py passes).

## Container output (STEP 5)

```
docker run --rm -v .../sqlite-utils:/workspace -w /workspace python:3.12 ...
pip install -q -e . pytest hypothesis
python -m pytest -q
=> 1087 passed, 16 skipped, 1 warning in 9.48s
```

Also verified locally: `flake8` clean, `mypy sqlite_utils` clean
("Success: no issues found in 9 source files").

**Code status: PASS** (full suite green including the 5 new tests).

## NOTES-HUB OUTCOME (core evaluation)

- Final `.ai/notes.md` line count: **43 lines** (includes the 10-line
  boilerplate header comment; ~33 lines of actual content across an
  "Explore" section and a "Build: rename-column" section).
- Did I create a `.ai/notes/` hub? **NO.** No `.ai/notes/` directory exists.
- Reasoning for staying flat: The framework guidance (AGENTS.md protocol
  step 2, build SKILL step 5, and the notes.md header) says to become a hub
  only "once this file passes ~1-2 screens" and explicitly: "Do not split
  while notes stay short - one file is cheaper to read whole than an index
  plus a leaf." A screen is roughly 40-50 lines; the ~1-2 screen threshold
  is on the order of 80-100 lines. At 43 lines the file is well under half a
  screen of the lower bound. There is also only one clearly separable topic
  cluster (the two dated sections both concern this same small project), so
  splitting would produce an index-plus-one-leaf structure that is strictly
  more expensive to read than the single file. Correct outcome for this
  control cell: stay flat.

This is the EXPECTED CORRECT outcome for the control cell. The threshold
guidance behaved correctly: it did not push a premature split.

## Observations

- The "do not split while short" guidance was clear and unambiguous. It
  appears in three places (notes.md header comment, AGENTS.md protocol
  step 2, build SKILL step 5), all consistent, all naming the same ~1-2
  screen threshold and the same rationale (one file cheaper than
  index+leaf).
- No temptation to split prematurely. At 43 lines the file is trivially
  read whole; creating a hub would have added an index file and a leaf for
  no benefit, and the link-integrity bookkeeping the guidance describes
  (keeping pointers in sync) would be pure overhead. The instruction to
  split only the "largest topic cluster" also implies you need multiple
  distinct clusters worth separating, which this project does not yet have.
- The build-skill STEP 5 sequencing worked cleanly: append notes ->
  notes-hub judgement (stay flat) -> project-context refresh (probe showed
  only LOC deltas on existing modules, which the skill says are not
  actionable, so AGENTS.md was left unchanged) -> link-integrity check
  (no-op, no hub exists). No friction.
- The review gate earned its keep here: it caught a real silent-data-loss
  bug that all pre-review tests missed, exactly the kind of ecosystem
  correctness issue the spec asked to guard against.
