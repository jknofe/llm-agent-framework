# Rust package - 2026-07-06 - satty (framework, small profile)

## Configuration

| Field | Value |
|---|---|
| Run ID | rust-package-2026-07-06 |
| Cell | rust-package |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-06T16:50:21 |
| End | 2026-07-06T16:55:43 |
| Duration | ~5m22s (wall clock between recorded timestamps) |
| Gate | PASS |

## Auto-size line

`--size small` was passed explicitly to `init_agent.py`, which bypasses the
LOC-based auto-detection path (`init_agent.py`: `if requested and requested
!= "auto":` skips `choose_size()`/the `auto-size: ... -> ... profile` print).
No auto-size line was printed as a result — this is expected given the
scaffold command used, not an omission. For reference, a same-session
`probe.py` run reports Code LOC = 10276 (docs/data/markup excluded), i.e.
right at the small/large ~10k boundary the auto-sizer uses.

## Spec produced

`.ai/changes/deb-packaging/spec.md` (status: done), goal: add
`[package.metadata.deb]` to `Cargo.toml` mirroring the Makefile `install`
target's assets, and a `deb: build-release` Makefile target running `cargo
deb --no-build`. Acceptance criteria enumerated exact asset-path/mode parity
with `install`, the bash-completion destination-filename quirk (`satty`, not
`satty.bash`), Makefile target shape, and TOML validity. Full text committed
to `.ai`; key excerpt of the Notes section (premise verification + numbered
assumptions):

```
Premise verification (done during /explore, repeated here for the record):
- Grepped the whole repo (*.toml, *.yml, Makefile) for cargo deb/cargo-deb/
  metadata.deb: no hits. No existing deb packaging exists, so this is a pure
  addition, not a merge/conflict situation.
- Makefile install target (read in full) is the authoritative source of
  paths/modes to mirror: binary 755 -> usr/bin/satty; satty.desktop 644;
  assets/satty.svg 644; LICENSE 644; completions/_satty (zsh) 644;
  completions/satty.bash -> installed as "satty" (not "satty.bash") 644;
  completions/satty.fish 644; completions/satty.elv 644; completions/satty.nu
  644; completions/satty.ts (fig) 644; man/satty.1 644. $(PREFIX) defaults to
  /usr/local in the Makefile, but Debian packages conventionally install
  under /usr, and the task explicitly names usr/bin/satty - so deb asset
  destinations use usr/... (dropping "local"), not a literal $PREFIX copy.

Assumption 1: completion destination dirs mirror Makefile's $(PREFIX)/share/...
  suffixes verbatim, rooted at usr/ instead of usr/local/ (standard Debian
  FHS locations).
Assumption 2: only `assets` is added to [package.metadata.deb] - no
  maintainer/depends/section/etc. cargo-deb derives those from existing
  [package]/[workspace.package] fields and defaults depends to $auto already.
  Task text only asked for assets + Makefile target (EFFORT=medium: minimal,
  literal change).
Assumption 3: build.rs's ci-release feature gate is what makes completions/
  and man/ exist at repo root; make build-release already forces this via
  `cargo build --release --features ci-release` - so `deb: build-release` is
  sufficient, no separate --features flag needed on the cargo deb line.
Assumption 4: man page asset target path is usr/share/man/man1/satty.1
  (uncompressed name); if cargo-deb auto-gzips man-page assets at build time
  that's cargo-deb's own behavior, not something Cargo.toml needs to encode.
```

## Premise verification finding

Task premise held exactly: the Makefile `install:` target (read in full
during /explore) enumerates every required asset 1:1 with a path and an
explicit mode, no existing `[package.metadata.deb]`/cargo-deb references
existed anywhere in the repo (grepped `*.toml`, `*.yml`, `Makefile`), and
`build.rs`'s `cfg!(feature = "ci-release")` gate is exactly why the new `deb`
target must depend on `build-release` (which already forces
`--features ci-release` through its `target/release/satty` prerequisite),
not plain `build`. No premise mismatch found.

## `.ai` commit history

```
60df9d3 build: deb-packaging
  changes/deb-packaging/spec.md | 8 +++++++-
  notes.md                      | 9 +++++++++
0c4b9cc spec: deb-packaging
  changes/deb-packaging/spec.md | 91 +++++++++++++++++++++++++++++++++++++++++++
282828f explore: project context
  notes.md | 18 ++++++++++++++++++
1ce00ff init: small-profile scaffold (satty)
  .gitignore                | 2 +
  agent/tools/probe.py      | 232 +++...
  changes/_archive/.gitkeep | 0
  notes.md                  | 15 +++
  [+1 file omitted, scaffold-generated]
```

## Target diff

```
$ git diff --stat HEAD
 .gitignore |  1 +
 Cargo.toml | 15 +++++++++++++++
 Makefile   |  3 +++
 3 files changed, 19 insertions(+)
```
(The `.gitignore` `+.ai/` line is a scaffold side effect from `init_agent.py`,
not part of this spec's task scope; `Cargo.toml`/`Makefile` are the spec's
actual deliverable.)

```diff
diff --git a/Cargo.toml b/Cargo.toml
index 1e1d3c9..be5c674 100644
--- a/Cargo.toml
+++ b/Cargo.toml
@@ -20,6 +20,21 @@ include = [
 [features]
 ci-release = []
 
+[package.metadata.deb]
+assets = [
+  ["target/release/satty", "usr/bin/satty", "755"],
+  ["satty.desktop", "usr/share/applications/satty.desktop", "644"],
+  ["assets/satty.svg", "usr/share/icons/hicolor/scalable/apps/satty.svg", "644"],
+  ["LICENSE", "usr/share/licenses/satty/LICENSE", "644"],
+  ["completions/_satty", "usr/share/zsh/site-functions/_satty", "644"],
+  ["completions/satty.bash", "usr/share/bash-completion/completions/satty", "644"],
+  ["completions/satty.fish", "usr/share/fish/vendor_completions.d/satty.fish", "644"],
+  ["completions/satty.elv", "usr/share/elvish/lib/satty.elv", "644"],
+  ["completions/satty.nu", "usr/share/nushell/completions/satty.nu", "644"],
+  ["completions/satty.ts", "usr/share/fig/autocomplete/satty.ts", "644"],
+  ["man/satty.1", "usr/share/man/man1/satty.1", "644"],
+]
+
 [dependencies]
 satty_cli.workspace = true
 relm4 = { version = "0.10.1", features = ["macros", "libadwaita", "gnome_42"] }
diff --git a/Makefile b/Makefile
index b1bbc93..b9eecdb 100644
--- a/Makefile
+++ b/Makefile
@@ -18,6 +18,9 @@ build: target/debug/satty
 
 build-release: target/release/satty
 
+deb: build-release
+	cargo deb --no-build
+
 force-build:
 	cargo build --features ci-release
```

## Review gate

`reviewer` sub-agent spawned with only the diff (Cargo.toml + Makefile) and
the spec's acceptance criteria. Result: PASS on all criteria (asset
path/mode parity incl. the bash-completion filename quirk, no missed/extra
assets, valid TOML with no key collision, Makefile target shape/indentation,
`build-release` -> `ci-release` -> completions/man chain confirmed via
build.rs). No correctness bugs found. It flagged the `.gitignore` `+.ai/`
scaffold line as out-of-scope-but-harmless, for visibility only. No fixes
were required as a result of the review.

## Gate output (full)

```
$ mkdir -p target/release completions man
$ printf '\x7fELF\x02\x01\x01\x00' > target/release/satty; chmod +x target/release/satty
$ touch completions/{satty.bash,_satty,satty.fish,satty.elv,satty.nu,satty.ts}
$ touch man/satty.1

$ docker run --rm -v "$WORK_DIR":/workspace satty-deb-builder bash -c '
    cd /workspace && cargo deb --no-build --no-strip 2>&1
    echo "=== contents ==="; dpkg-deb --contents target/debian/satty_*.deb | awk "{print \$6}" | sort'

warning: Failed to find dependency specification.
         No $auto deps for /workspace/target/release/satty
/workspace/target/debian/satty_0.21.1-1_arm64.deb
=== contents ===
./usr/
./usr/bin/
./usr/bin/satty
./usr/share/
./usr/share/applications/
./usr/share/applications/satty.desktop
./usr/share/bash-completion/
./usr/share/bash-completion/completions/
./usr/share/bash-completion/completions/satty
./usr/share/doc/
./usr/share/doc/satty/
./usr/share/doc/satty/copyright
./usr/share/elvish/
./usr/share/elvish/lib/
./usr/share/elvish/lib/satty.elv
./usr/share/fig/
./usr/share/fig/autocomplete/
./usr/share/fig/autocomplete/satty.ts
./usr/share/fish/
./usr/share/fish/vendor_completions.d/
./usr/share/fish/vendor_completions.d/satty.fish
./usr/share/icons/
./usr/share/icons/hicolor/
./usr/share/icons/hicolor/scalable/
./usr/share/icons/hicolor/scalable/apps/
./usr/share/icons/hicolor/scalable/apps/satty.svg
./usr/share/licenses/
./usr/share/licenses/satty/
./usr/share/licenses/satty/LICENSE
./usr/share/man/
./usr/share/man/man1/
./usr/share/man/man1/satty.1.gz
./usr/share/nushell/
./usr/share/nushell/completions/
./usr/share/nushell/completions/satty.nu
./usr/share/zsh/
./usr/share/zsh/site-functions/
./usr/share/zsh/site-functions/_satty
```

`target/debian/satty_0.21.1-1_arm64.deb` (15408 bytes) was produced.

Gate result: **PASS** — the `.deb` path was produced, and `dpkg-deb
--contents` lists the binary (`usr/bin/satty`), the `.desktop` file, the SVG
icon, all six shell completions (bash, zsh, fish, elvish, nu, fig), the man
page (auto-gzipped by cargo-deb to `satty.1.gz`), and the license. The
`$auto` deps warning against the mocked ELF binary appeared exactly as
expected per the task's PASS definition and is not treated as a failure.

## Observations

1. The framework's `/explore` step paid off directly: reading the Makefile's
   `install:` target in full during exploration produced the exact asset
   list (including the easy-to-miss bash-completion rename to `satty`)
   needed later in `/spec`, with no re-discovery needed during `/build`.
2. `cargo-deb` derives `maintainer`/`copyright`/`license` from the existing
   `[package]`/`[workspace.package]` fields and defaults `depends` to
   `$auto` without being told to — the spec's Assumption 2 (add only
   `assets`, nothing else) held up against the actual gate run; no missing
   `maintainer` error occurred.
3. `cargo-deb` synthesizes `usr/share/doc/satty/copyright` and gzips the man
   page on its own; neither required a corresponding `assets` entry — both
   are cargo-deb's own packaging behavior layered on top of the explicit
   asset list.
4. The `reviewer` sub-agent caught nothing wrong in this diff (it was small
   and mechanical: an 11-row TOML array plus a 2-line Makefile target), but
   it did independently re-derive and confirm the `build-release` ->
   `--features ci-release` -> `completions/`/`man/` chain from `build.rs`
   rather than taking the spec's claim on faith — useful as a genuine
   correctness check, not a rubber stamp.
5. Total framework overhead (scaffold + explore + spec + build + review) for
   a 2-file, ~19-line change was ~5m22s wall clock, dominated by the
   sub-agent review round-trip (~38s) and the docker-based gate itself; the
   spec/build steps for a change this narrow were mechanical rather than
   requiring back-and-forth exploration.

## Token usage (count_tokens.py, informational)

Note: dispatched as a Task-tool sub-agent; the `reviewer` sub-agent it spawned
is a sibling transcript in the same `subagents/` dir (spawnDepth 2), not nested
inside the benchmark agent's own file, so it is counted separately and added
in per the runbook rule ("reviewer cost stays in").

Main agent (`agent-a145158ff58a5296a.jsonl`):

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 102 | 61040 | 2433749 | 9196 | 2504087 |

Reviewer sub-agent (`agent-a25a660ea6a51d212.jsonl`, "Review deb-packaging diff"):

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 18 | 22227 | 145885 | 1193 | 169323 |

**Combined total (framework price, incl. reviewer): 2,673,410 tokens**
(input 120, cache write 83267, cache read 2579634, output 10389)
