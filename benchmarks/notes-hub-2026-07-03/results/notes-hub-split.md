# notes-hub-split

## Configuration

| Field | Value |
|---|---|
| Run ID | notes-hub-split |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Repo | simonw/sqlite-utils @ 79117b9 |
| Start | 2026-07-03T07:24:00 |
| End | 2026-07-03T09:01:03 |
| Duration | ~1h37m |
| Code container status | **PASS** (1084 passed, 16 skipped, 0 failed) |

## .ai commit history

```
bfb7fd4 init: small-profile scaffold (sqlite-utils)
7945162 explore: accumulated project notes (seeded)
1feb158 spec: rename-column
68c057f build: rename-column
```

## Host repo diff --stat (HEAD)

```
 .gitignore             |  1 +
 docs/changelog.rst     |  7 +++++++
 docs/cli-reference.rst | 20 ++++++++++++++++++++
 docs/cli.rst           | 13 +++++++++++++
 docs/python-api.rst    | 11 +++++++++++
 sqlite_utils/cli.py    | 30 ++++++++++++++++++++++++++++++
 sqlite_utils/db.py     | 13 +++++++++++++
 tests/test_cli.py      | 48 ++++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_create.py   | 15 +++++++++++++++
 9 files changed, 158 insertions(+)
```
(`.gitignore` `+.ai/` line is leftover from the init-time scaffold step, not
from `/build`. Untracked `AGENTS.md`, `CLAUDE.md`, `.claude/` are the
init-time scaffold files, also outside the `.ai` repo by design.)

## Container output

```
[notice] To update, run: pip install --upgrade pip
................ssssssssssss............................................ [ 78%]
........................................................................ [ 85%]
........................................................................ [ 91%]
........................................................................ [ 98%]
....................                                                     [100%]
=============================== warnings summary ===============================
../usr/local/lib/python3.12/site-packages/_pytest/python.py:124
  PytestRemovedIn10Warning: Passing a non-Collection iterable to parametrize is deprecated.
  Test: tests/test_sniff.py::test_sniff, argvalues type: generator
  (pre-existing, unrelated to this change)
1084 passed, 16 skipped, 1 warning in 9.29s
```

## NOTES-HUB OUTCOME

**Split happened: YES.**

The seeded `.ai/notes.md` (84 lines / 7 topic sections) was already past the
"~1-2 screens" threshold at session start. During `/build`'s step 5, after
appending this build's durable notes (3 new bullets: the `rename-column`
CLI/API addition under "CLI conventions", the confirmed
`transform(rename=...)` silent-no-op-on-missing-column gotcha under "Type
system / transform", and removal of one now-stale bullet — "No rename-column
command (gap)" — that the new feature made false), the file sat at 85 lines
across 7 sections:

| Section | Bullets |
|---|---|
| Build / dev environment | 13 (largest) |
| CLI conventions | 10 |
| Testing | 11 |
| FTS internals | 10 |
| Type system / transform | 9 |
| Gotchas | 8 |
| Packaging / release | 7 |

Per the skill's literal instruction ("move the **largest** topic cluster"),
I moved **"Build / dev environment"** (13 bullets — install/PEP 735 deps,
docs/cog build, black/flake8/mypy/codespell/ty gates, Python version pin)
into a new leaf, replacing it with a one-line pointer.

**Leaf file created:**
- `.ai/notes/build-dev-environment.md` (17 lines incl. header/comment, 13
  content bullets, verbatim from the extracted section)

**Resulting `.ai/notes.md` hub:**

```markdown
# Project Notes

<!-- Running memory. Append, telegraphic. Read at start of a task. -->

- [build-dev-environment](notes/build-dev-environment.md) - install/PEP 735 deps, docs/cog build, black/flake8/mypy/codespell gates, Python version.

## Testing
- pytest + hypothesis. Full suite ~1080 tests, runs in <30s.
- `tests/test_docs.py` auto-fails any CLI command missing from docs. Add doc when adding command.
- `tests/test_tracer.py::test_with_tracer` pins the exact SQL params dict for FTS detection.
- Parametrized docs-coverage cases inflate collected count (1096 -> 1100 range).
- hypothesis profiles: default is fine locally; CI uses more examples.
- Fixtures build fresh in-memory DBs per test; no shared state.
- `--detect-types` CSV tests live in test_cli_insert.py.
- FTS tests in test_fts.py; transform tests in test_create.py.
- Run a single test file fast: `pytest tests/test_fts.py -q`.
- Some tests assert exact CLI output text; keep help strings stable.
- test_cli.py covers argument parsing and error paths.

## FTS internals
- `enable_fts(replace=True)` calls `disable_fts()` which relies on `detect_fts()`.
- `detect_fts()` locates the FTS shadow table via two LIKE patterns (`like`, `like2`).
- Legacy bracket-quoted `content=[table]` vs double-quote `content="table"` both must match.
- A copy-paste where both LIKE patterns are identical silently breaks bracket-quoted detection.
- Symptom of that bug: `table "X_fts" already exists` on re-enable, two hops from the defect.
- FTS4 and FTS5 both supported; version detection via sqlite_version.
- `rebuild-fts` command re-populates the index; `populate-fts` appends.
- SQLite `LIKE` does not treat `[`/`]` as wildcards, so bracket patterns need no escaping.
- FTS shadow tables named `<table>_fts`; content= references the base table.
- disable-fts drops the shadow table and its triggers.

## CLI conventions
- Commands defined with `@cli.command(name="kebab-case")` in sqlite_utils/cli.py.
- rename-table exists (cli.py ~1681) delegating to db.rename_table (db.py ~1233).
- Table mutations often delegate to `transform()` machinery (rename, drop, alter).
- `transform(rename={old: new})` silently destroys data if new name collides with existing column.
- Output format flags (--csv, --json, --nl) are shared via a decorator.
- click-default-group provides the default subcommand behaviour.
- add-column / add-foreign-key / create-index follow the same command shape.
- Most commands take db path + table as first two positional args.
- `--load-extension` is threaded through many commands via a shared option.
- rename-column added (cli.py, mirrors rename-table); `Table.rename_column(old, new)` (db.py) delegates to `transform()`.

## Type system / transform
- `transform()` rebuilds the table via a temp table + copy + swap.
- Column type changes go through transform, not ALTER.
- REAL not FLOAT is the canonical SQLite column type (issue #680).
- Foreign key add/drop also rebuild via transform.
- STRICT table support added (#604); affects type coercion.
- transform preserves indexes and FKs unless told otherwise.
- Type detection maps Python types to SQLite affinities in a central dict.
- `--detect-types` guesses INTEGER/REAL/TEXT from sampled values.
- `transform(rename={old: new})` silently no-ops if `old` isn't an existing column (confirmed by manual test) - no error, no data change. `Table.rename_column()` guards this by checking `columns_dict` first and raising `InvalidColumns`.

## Packaging / release
- Version in pyproject.toml `[project].version` (currently 4.0rc1).
- Release via GitHub Actions on tag; publishes to PyPI.
- `sqlite-utils` console_scripts entry point -> sqlite_utils.cli:cli.
- Plugins loaded via pluggy; entry-point group `sqlite_utils`.
- Wheels are pure-python, no compiled extension.
- Docs published to Read the Docs from docs/.
- Changelog in docs/changelog.rst, hand-maintained, refs issue numbers.

## Gotchas
- `np.int8` and numpy scalar types need explicit handling on insert (#632).
- CSV with only a header row must not crash --detect-types (#702/#707).
- detect_fts failing on `[]` bracket content is the classic regression (#694).
- Cursor "eaten" by click on some terminals (#433).
- `--editable` insert path had a bug (#568-era).
- datetime deprecation on Python 3.14 required a test fix.
- Click "sentinel" default handling caused a batch of fixes.
- mypy false positives around Optional returns need targeted ignores.
```

**Which cluster moved and why:** "Build / dev environment" — it was the
single largest section (13 bullets vs. next-largest at 11), and its content
(install method, docs/cog build, black/flake8/mypy/codespell/ty gates,
Python version) forms a coherent, self-contained topic that a task not
touching packaging/CI tooling doesn't need to load. I did not force further
splitting: per the skill, only the largest cluster moves in one pass; the
remaining hub (72 lines / 6 sections) is left as-is for a future build to
split again once/if it re-crosses the threshold.

**Are all leaves linked from notes.md?** Yes — verified programmatically:
the sole leaf (`build-dev-environment.md`) is referenced by exactly one
pointer in `notes.md`, and no other leaf files exist to check.

**Do all pointers resolve (no dangling/orphaned)?** Yes — the one pointer
`notes/build-dev-environment.md` resolves to an existing file, and there are
no leaf files without a matching pointer.

**Session-start read size, hub vs. whole file:**

| | Lines | Words | Chars (~tokens/4) |
|---|---|---|---|
| Whole notes.md before split (85 lines, 7 sections) | 85 | ~740 | ~5150 (~1290 tok) |
| Hub only, after split (72 lines, 6 sections + 1 pointer) | 72 | 631 | 4450 (~1110 tok) |
| Leaf only (`build-dev-environment.md`) | 17 | 147 | 1000 (~250 tok) |

A task that does **not** need the build/dev-environment topic now reads
~14% fewer lines/tokens at session start (72 vs. 85 lines) by reading the
hub alone. A task that **does** need it reads hub + leaf (89 lines total),
essentially a wash versus the original monolith (85 lines) — the win compounds
over future sessions/builds as more topic clusters accumulate and get
extracted, rather than in this single pass, since the guidance calls for
moving one cluster per pass, not compressing everything at once.

## Did you read hub-first?

**Honestly: no, not for this session** — because the hub did not exist yet
until I created it near the end of `/build` step 5. During `/explore` and
`/spec` I read the full (still-monolithic, 84-86 line) `notes.md`, since
that was the only form it had at the time. The split is something `/build`
step 5 produces as its last action, for the benefit of *future* sessions —
this run's own explore/spec work happened before the hub existed to read
hub-first from. I did read the hub myself when doing the final "confirm
every leaf is linked" verification pass, and the resulting file is now a
true hub for the next task to open first.

## Observations

- The guidance was clear and mechanically followable: "past ~1-2 screens ->
  move the largest cluster -> one-line linked pointer -> keep pointers in
  sync" is unambiguous enough to execute without judgment calls beyond
  "which section is largest" (a simple line count).
- Minor friction: the guidance doesn't say what to do about a stale note
  that a code change invalidates (here: "No rename-column command (gap)"
  became false once the command was added). I treated the general "append
  durable notes" instruction as also license to correct/remove notes made
  false by the change, rather than leaving a contradictory bullet next to
  the new one - reasonable, but it's an implicit extension of the written
  guidance rather than something the skill spells out.
- The instruction to split only the *single* largest cluster (not
  recursively split until short) means one pass doesn't necessarily bring
  the hub back under the 1-2 screen target if there were originally many
  similarly-sized sections (here: after removing the largest, 72 lines
  across 6 sections remains borderline-long) - this appears to be
  intentional incrementalism (spread the cost across builds) rather than a
  gap, but it does mean "past threshold" can still be true immediately
  after a split.
- No friction with mechanics: picking the file name (`<topic>.md` inferred
  from the section heading, kebab-cased), writing the pointer line format,
  and verifying link integrity were all straightforward with the tools
  available (`grep`, a small shell loop).
