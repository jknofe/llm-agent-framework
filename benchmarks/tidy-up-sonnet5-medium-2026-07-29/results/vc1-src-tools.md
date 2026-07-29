# tidy-up: src/tools

Repo: /tmp/claude-1000/-home-johannes-git-llm-agent-framework/b54d2723-8077-4aa6-830d-a05ca946eea0/scratchpad/vc1
Baseline commit: b9c20c554fae53e341aa6162def14354eb519a3f (worktree clean at start, HEAD detached from 2d18065)
Scope: src/tools (12 files, 4441 lines: arrow.rs, blur.rs, brush.rs, crop.rs, ellipse.rs,
highlight.rs, line.rs, marker.rs, mod.rs, pointer.rs, rectangle.rs, text.rs)

## Operator waiver (deviation from skill step 0 and step 5)

`cargo build` / `cargo test` cannot run in this environment: the system library
`gtk4-layer-shell` is missing, so the crate cannot link. The operator explicitly
waived the build/test/lint baseline that the skill's step 0 requires and the
re-run in step 5. I did not attempt a full build or test run at any point.

As a partial substitute, since it needs no linking, I ran `rustfmt --check --edition 2024`
against all 12 files in scope before and after editing. Result: exit 0 (no
diff) both times, on the full set of 12 files, confirming every file in scope
is syntactically valid Rust and already conforms to the project's formatting,
including the 6 files I edited. This is a syntax/format check only, not a
substitute for a real compile, type-check, borrow-check, or test run. No
cargo-based verification of runtime behavior was performed or is claimed.

I did use non-linking static methods to gather dead-code evidence: repo-wide
`grep` for symbol references, `git log` on the scope, and manual reading of
all 4441 lines across the 12 files (plus cross-referencing symbol usage
outside `src/tools`).

## Pass 1: Dead code (removed, with evidence)

Removed 3 commented-out code fragments. Evidence for each: grepped the whole
repo for any dynamic/string reference to the removed line's target and found
none; each is a `//`-prefixed line containing dead Rust syntax, not prose;
this repo is an application binary (not a library), so no public-API
carve-out applies to internal tool wiring.

| File | Line(s) removed | What it was | Evidence |
|---|---|---|---|
| `src/tools/mod.rs` | 236 | `//tools.insert(Tools::Crop, Rc::new(RefCell::new(CropTool::default())));` | `Crop` is registered separately via the dedicated `crop_tool` field a few lines below (`ToolsManager::new` / `get_crop_tool`); this commented insert into the generic `tools` HashMap is superseded and unreachable even if uncommented (crop is never looked up through that map — `get()` special-cases `Tools::Crop` to return `crop_tool`). |
| `src/tools/blur.rs` | 61 | `//canvas.delete_image(src_image_id);` | Leftover/no-op comment; `src_image_id` and `dst_image_id` handling is otherwise complete in `Blur::blur`; nothing references this call site elsewhere. |
| `src/tools/text.rs` | 1630 | `// current_offset - start as i32` | Stray duplicate of the live statement directly above it (`let temp = current_offset - start as i32;` at line 1629); confirmed via grep that this exact expression string appears 4 times as live code and only this one instance is commented out, immediately adjacent to its live twin. |

No unreferenced private functions/types/fields, no unreachable branches, no
dead feature-flag arms, and no unused parameters were found as unambiguous
candidates in this scope. I could not run clippy/`cargo check` to get a
compiler-verified unused-code list (waived per the operator's note above), so
I relied on manual, per-file reading plus repo-wide `grep` for each pub
symbol's name. Concrete types like `ArrowTool`, `BlurTool`, `EllipseTool`,
`LineTool`, `RectangleTool`, `TextTool`, `HighlightTool` show 0 references
outside `src/tools/`, but this is expected encapsulation, not dead code: they
are only ever obtained through `ToolsManager::get(&Tools)` returning
`Rc<RefCell<dyn Tool>>`, so callers outside the module reference them only via
the `Tools` enum, never the concrete type name. I did not remove anything on
this basis. Where I was not certain a symbol was truly dead, I left it alone
per the skill's "when evidence is ambiguous, do not remove" rule, rather than
promote it to the proposal list (nothing in scope met the obsolete-file bar
either — see Pass 2).

## Pass 2: Obsolete files (proposal table)

No candidates. All 12 files in `src/tools` are actively referenced from
`mod.rs` and, transitively, from `sketch_board.rs`/`ui` outside the scope
via the `Tools` enum and `ToolsManager`. `git log --oneline -- src/tools`
shows continuous history through recent feature/fix commits (most recent:
"feat: indicate active editing in toolbar (#444)", "fix: do not create empty
text objects (#518)"); none of the files have "gone quiet." No `.orig`,
`.rej`, or `.bak` droppings were found in the scope. Proposal table is empty.

| Path | Why it looks obsolete | What breaks if wrong | Confidence |
|---|---|---|---|
| (none) | — | — | — |

## Pass 3: Overlong comments (shortened)

Swept every `src/tools/*.rs` file for consecutive `//` comment blocks of 3+
lines. Found and handled:

| File | Location | Before (lines) | Action |
|---|---|---|---|
| `arrow.rs` | canvas-rotation note | 3 | Compressed to 1 line. |
| `arrow.rs` | midpoint_offset semantics | 4 | Compressed to 2 lines; kept the sign-meaning invariant (0 / negative / positive effect on head shape). |
| `crop.rs` | `CropTool::get_drawable` rationale | 3 | Compressed to 1 line; kept the "why" (drawn separately via `get_crop`). |
| `highlight.rs` | BeginDrag mode-toggle intro | 3 | Compressed to 1 line. |
| `highlight.rs` | "This matches when CTRL is not pressed..." | 3 | Deleted outright: it only restated the tuple pattern immediately below it (`(Highlighters::Block, false) \| (Highlighters::Freehand, true)`), which already says the same thing. |
| `highlight.rs` | "This matches the remaining two cases..." | 3 | Deleted outright, same reason as above. |
| `highlight.rs` | freehand shift-model explanation | 10 | Compressed to 2 lines; kept the operative facts (15-degree snap, anchor point on release, chainable without moving the mouse). |
| `highlight.rs` | "if shift was pressed before we remove..." | 3 | Compressed to 1 line. |
| `highlight.rs` | `handle_key_release_event` shift-release note | 3 | Compressed to 2 lines. |

Left untouched (deliberate judgment call, not an oversight): `arrow.rs` lines
~150-178, a 29-line ASCII diagram documenting the arrow-head geometry
(labels A-G for start/end/head/tail/midpoint points). This is exactly the
carve-out the skill describes ("explains why... cites an algorithm... keep
the information"): the diagram is not restating what the code says, it's the
only place the geometry is derivable from, and the code that follows
annotates individual `path.line_to(...)` calls with the diagram's own
single-letter labels (`// G`, `// C`, `// B`, ...) that are meaningless
without it. There is no docs location in this application repo suited to an
inline geometry diagram tightly coupled to specific `path.line_to` call
order, so moving it out and leaving a pointer would cost more clarity than it
saves. I kept it in place, unshortened, and I'm flagging the decision
explicitly here rather than silently leaving it.

No licence/SPDX headers or `///` API-doc comments exist anywhere in this
scope (grepped for both, zero hits), so that carve-out did not come up.

## Pass 4: Em dashes

Grepped (byte-exact `—` U+2014, both `grep` and a Python substring count) all
12 files in scope: 0 occurrences. No changes made in this pass.

## Pass 5: Verify and record

Build/test/lint re-run: waived, per the operator note above (cannot link
gtk4-layer-shell in this environment). Substitute check: `rustfmt --check
--edition 2024` over all 12 files in scope, before and after editing —
exit 0 both times (no formatting diff), confirming syntactic validity.
Brace/paren balance was also manually confirmed equal on every edited file.

Reviewer sub-agent: no `reviewer` agent type was available to me (the
session's registered agent types were `claude`, `claude-code-guide`,
`Explore`, `general-purpose`, `Plan`, `statusline-setup` — this project does
scaffold its own `.claude/agents/reviewer.md`, but that custom agent
definition was not reachable from my Agent tool in this session). Per the
skill's fallback ("If it cannot be spawned, use a fresh general-purpose
sub-agent given only the diff and the rule that behavior must not change"),
I dispatched a fresh general-purpose sub-agent with only the unified diff and
the no-behavior-change rule. Verdict: **PASS**. It confirmed every removed or
changed line was comment-only in the original (no live code line was turned
into a comment or altered), all match-arm patterns and logic in `highlight.rs`
are byte-identical before/after the comment edits, and no removed comment
carried a safety invariant or licence notice.

Module map / `.ai/notes.md`: no module disappeared or was renamed, so the
`GENERATED:project-context` section of AGENTS.md needs no update. No durable
finding emerged (no subsystem turned out unreachable; the arrow.rs
keep-the-diagram judgment call is recorded here in this report, not in
`.ai/notes.md`, since it's local to one file/pass rather than a KB-level
fact). Consequently there is nothing to append to `.ai/notes.md`.

## Commit status (per the skill's own rule)

`.ai` is its own nested git repo in this project (`.ai/.git`), separate from
the host project's git. I checked it (`git -C .ai status` / `git -C .ai log`):
it is clean, one existing commit ("init: small-profile scaffold (satty)"),
and nothing in it changed during this sweep — no notes.md append, no module
map edit was warranted (see above). Since there is nothing to commit there, I
did not create an empty or fabricated `.ai` commit just to satisfy the "commit
`.ai`" instruction; I'm stating this explicitly rather than silently skipping
it.

Host repo (`src/tools/*.rs`, the actual tidy-up changes): left **uncommitted**,
as the skill mandates ("Leave the host-repo changes uncommitted for the user
to review; this framework never commits the host project repo") and per your
explicit instruction not to commit anything in the host repository. Current
host-repo diff is exactly:

```
src/tools/arrow.rs     | 10 +++-------
src/tools/blur.rs      |  1 -
src/tools/crop.rs      |  4 +---
src/tools/highlight.rs | 31 ++++++-------------------------
src/tools/mod.rs       |  1 -
src/tools/text.rs      |  1 -
6 files changed, 10 insertions(+), 38 deletions(-)
```

Nothing outside `src/tools` was touched; `brush.rs`, `ellipse.rs`, `line.rs`,
`marker.rs`, `pointer.rs`, `rectangle.rs` had no findings in any pass and are
untouched.

## Where I could not fully follow the skill

- Step 0 baseline and the step-5 re-run: waived by the operator (documented
  above); I substituted a non-linking `rustfmt --check` sweep, which is not
  equivalent to a real build/test/lint and I am not claiming it is.
- The `reviewer` sub-agent named in step 5 was not spawnable from my tool
  surface; used the general-purpose fallback the skill itself specifies for
  that case.
- Dead-code hunting (step 1) without a compiler: I could not get an
  authoritative "unused" list from `cargo`/clippy, so I only removed what I
  could verify unambiguously by hand (commented-out code with no other
  reference anywhere in the repo). I deliberately did not attempt to declare
  any private function, field, or type "dead" on manual inspection alone,
  since a wrong call there is a correctness risk the skill's evidence bar is
  meant to prevent, and I have no compiler to catch a mistake.
