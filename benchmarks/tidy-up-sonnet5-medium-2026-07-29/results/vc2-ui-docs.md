# tidy-up report

Scope: `src/ui`, `src/configuration.rs`, and the repository documentation and
templates (`README.md`, `.github/`).

Repo: Satty (Rust/GTK4 screenshot annotation tool), worktree at
`/tmp/claude-1000/-home-johannes-git-llm-agent-framework/b54d2723-8077-4aa6-830d-a05ca946eea0/scratchpad/vc2`.

## Operator waiver (step 0 deviation)

`cargo build` / `cargo test` cannot run in this environment: the system
library `gtk4-layer-shell` is missing, so the crate cannot link. The operator
explicitly **waived** the build/test/lint baseline that step 0 normally
requires as a hard gate.

What I did instead, as permitted ("cargo subcommands that do not require
linking"):
- Confirmed worktree clean before starting. HEAD detached at
  `2d18065` + one local `scaffold` commit, working tree clean.
  Commit SHA at start: `b9c20c554fae53e341aa6162def14354eb519a3f`.
- `cargo check --all-targets --all-features`: clean, 0 warnings (verified
  twice, once after `touch`-ing every file in scope to force
  recompilation rather than trust the cache).
- `cargo clippy --all-features --all-targets -- -W dead_code -W unused`:
  "No issues found" after forcing recompilation of the scoped files.
- `cargo fmt --check`: clean.
- Did **not** attempt `cargo build`/`cargo test` (would require linking
  `gtk4-layer-shell`) or `cargo build --release`.

This is a partial baseline, not the full one the skill specifies. It covers
type-checking, lints, and formatting for the scope touched, but not an
actual link/run/test cycle. Recorded here per the operator's instruction so
this gap is visible rather than silently assumed away.

## Pass 1: dead code — none removed

Candidates checked and evidence collected:
- Every `pub fn` getter on `Configuration`/`FontConfiguration`/`ColorPalette`
  (`src/configuration.rs`) grepped across `src/` and `cli/`: all have at
  least one external call site (e.g. `focus_toggles_toolbars()` used in
  `src/main.rs:385`, `.family()/.style()/.fallback()` used in
  `src/femtovg_area/imp.rs`, `.palette()` used in `src/main.rs` and
  `src/style.rs`, `.custom()` used in `src/ui/toolbars.rs`).
- Private helpers `update_keybind`, `validate_keybind`, `merge_general`,
  `merge` (Keybinds/FontConfiguration/ColorPalette): all called from
  `Configuration::merge` or `Keybinds::merge`, in use.
- `Keybinds::get_tool`: used from `src/sketch_board.rs:884`.
- `ToolbarEvent`, `ToolsToolbarInput`, `StyleToolbarInput`,
  `AnnotationSizeDialogInput/Output`, `ColorButtons` (`src/ui/toolbars.rs`):
  every variant referenced from `src/main.rs` and `src/sketch_board.rs`
  (checked with per-symbol grep, not just presence of the type name).
- `cargo clippy` with explicit `-W dead_code -W unused` on top of
  `--all-features --all-targets`, run against a forced-clean recompile of
  the scoped files, reported no issues. This is the ecosystem's own
  unused-code detector confirming the manual grep survey.
- Checked `src/ui/mod.rs` (1 line, just `pub mod toolbars;`) - no dead
  re-exports.
- `.github/` and `README.md` have no unreachable-branch or
  commented-out-code equivalent: no HTML comments in `README.md`, no
  disabled/dead steps in `lint.yml` or `release.yml`. The one place that
  looks like "commented-out code" (`#fullscreen = false` etc. inside the
  README's TOML example, config.toml sample) is intentional
  documentation showing alternative option syntax, not dead code, so it
  was left alone.

Result: nothing met the removal bar. Nothing deleted in this pass.

## Pass 2: obsolete files — proposal table

| Path | Why it looks obsolete | What breaks if wrong | Confidence |
|---|---|---|---|
| (none) | — | — | — |

No candidates surfaced. Every file in scope is either actively referenced by
Rust source (`src/ui/mod.rs`, `src/ui/toolbars.rs`, `src/configuration.rs`),
or is a GitHub-platform-recognized config that GitHub itself discovers by
path convention regardless of in-repo cross-references (`README.md`,
`.github/ISSUE_TEMPLATE/*.yml`, `.github/dependabot.yml`,
`.github/workflows/*.yml`). Checked for editor/merge droppings
(`*.orig`, `*.rej`, `*.bak`, `*~`) in scope: none found. Checked git log for
these paths: continuously active, most recently touched by real feature/fix
commits, no dormant tail.

## Pass 3: overlong comments — touched

Rust files (`src/ui/mod.rs`, `src/ui/toolbars.rs`, `src/configuration.rs`):
no change. Every comment in these files is already 1-2 lines
(the longest, the `Keybinds::merge` doc comment, is exactly 2 lines).

Docs/templates, 4 comment blocks shortened from 3+ lines to 1-2 lines while
preserving every fact (version markers, deprecation notes, URLs):

1. `README.md`, config example, `output-filename` (was 3 lines → now 2):
   kept the strftime URL, the 0.20.0 tilde-expansion note, and the 0.21.0
   save-as behavior note.
2. `README.md`, config example, `input-scale` (was 3 lines → now 2): kept
   the DPI-scale explanation, the "more useful via CLI" note, and the
   0.21.0 resize-interaction caveat.
3. `README.md`, config example, `fallback` fonts (was 3 lines → now 2):
   kept the 0.20.1 marker and the "not shipped, must be present on system"
   caveat.
4. `.github/dependabot.yml` header (was 4 lines of generic
   Dependabot-scaffold boilerplate → now 1 line): kept the documentation
   URL, dropped only the boilerplate paraphrase of what the file below it
   already says.

Left alone (real information / published contract, excluded by the skill's
own rule): the `--help` output block embedded in `README.md` (lines
~244-327) is the literal `clap`-generated CLI help text, i.e. an
expected-output artifact, not a comment to compress. The commented-out
alternative values inside the README's TOML sample (`#fullscreen = false`,
etc.) are intentional "here are the other valid spellings" documentation,
not narrative clutter.

## Pass 4: em dashes — removed

Repo-wide grep for U+2014 restricted to the four scope paths found exactly
2 instances, both in prose, both rewritten by clause per the skill's rule,
both re-verified with a fresh grep (0 remaining in scope):

1. `README.md` (color-shortcut line): `<kbd>0</kbd> — select nth color...`
   → `<kbd>0</kbd>: select nth color...` (abrupt break → colon; matches the
   colon convention already used by every other shortcut bullet in that
   same list).
2. `.github/ISSUE_TEMPLATE/feature.yml`: `even better — but no pressure.`
   → `even better, but no pressure.` (parenthetical-ish break → comma).
   The two trailing spaces at end of line (a YAML block-scalar markdown
   hard-linebreak, needed so the next bullet renders on its own line) were
   preserved.

Final em-dash count in scope: 0.

## Step 5 verification

- Re-ran `cargo check --all-targets --all-features` and `cargo fmt --check`
  after all edits: still clean (no Rust files were touched, so this was
  primarily a sanity check that nothing bled outside the intended files).
- Validated the two edited YAML files (`dependabot.yml`, `feature.yml`)
  plus their siblings (`bug.yml`, `config.yml`) with `yaml.safe_load`: all
  parse.
- Ran a `general-purpose` sub-agent as reviewer against the full diff with
  the explicit instruction "behavior must not change" (the dedicated
  `reviewer` sub-agent type was not available in this environment). Its
  verdict: diff is safe and behavior-preserving; every version marker,
  URL, and caveat present in the original comments is retained in the
  shortened form; both em-dash rewrites read as correct, same-meaning
  sentences; the markdown hard-linebreak in `feature.yml` is intact; no
  structural YAML/Markdown issues.
- No module disappeared or was renamed, so no `AGENTS.md` module-map
  update was needed.
- Appended 3 durable findings to `.ai/notes.md` (telegraphic, per this
  repo's KB register): the cargo-check/clippy/fmt-only verification
  workaround for this sandbox, the drift between `README.md`'s config
  example and the actual repo-root `config.toml` (missing several newer
  keys, a stale `NEXTRELEASE` placeholder), and the stale
  pre-rename filenames in the issue-template header comments plus the
  mixed `gabm/satty` vs `Satty-org/Satty` GitHub org in `README.md` links.
  None of these were touched by the sweep itself (all are content-accuracy
  issues, not dead code / obsolete files / overlong comments / em dashes),
  they are flagged for a future pass.

## Places I could not fully follow the skill

- Step 0's "run the project's build, test, and lint commands" was not
  done in full: `cargo build`/`cargo test` were skipped per the explicit
  operator waiver (gtk4-layer-shell missing, cannot link in this sandbox).
  Substituted `cargo check`, `cargo clippy`, `cargo fmt --check` (all
  non-linking) as the closest available static baseline, both before and
  after edits.
- Step 5's "Run the `reviewer` sub-agent" - that named sub-agent type was
  not present in this environment's agent roster, so a fresh
  general-purpose sub-agent was used instead, given only the diff and the
  no-behavior-change rule, per the skill's own fallback instruction.
- A few real inconsistencies surfaced during the survey (stale
  `bug-report.yml`/`feature-request.yml` header comments in the issue
  templates, `gabm/satty` vs `Satty-org/Satty` org drift in `README.md`
  links, `config.toml` vs `README.md`'s embedded example drift) do not
  fit any of the skill's four pass definitions (not dead code, not an
  obsolete file, not an overlong comment, not an em dash) and were left
  unedited, only recorded in `.ai/notes.md` as required by step 5's
  "durable finding" instruction.

## Commits

- `.ai` (nested repo): committed `notes.md` update as
  `tidy-up: src/ui, src/configuration.rs, README.md, .github/`
  (commit `7139424`), per step 6.
- Host repo (Satty worktree): left uncommitted, per step 6 and the
  instruction not to commit anything in the host repository. Current
  `git status` shows 3 modified files pending review:
  `.github/ISSUE_TEMPLATE/feature.yml`, `.github/dependabot.yml`,
  `README.md`.
