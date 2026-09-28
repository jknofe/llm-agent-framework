# rust-package-5.26-2026-09-14 (Satty)

## Configuration

| Field | Value |
|---|---|
| Run ID | rust-package-5.26-2026-09-14 |
| Cell | rust-package |
| Framework | 5.26 |
| Arm | framework |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-09-14T08:27:16 |
| End | 2026-09-14T08:30:13 |
| Duration | ~3 min |
| Gate | PASS |

## Spec produced

File: `.ai/changes/deb-packaging/spec.md`

```
---
id: deb-packaging
title: Add cargo-deb packaging metadata and Makefile target
status: done
created: 2026-09-14
---

## Goal
Enable building a Debian package for Satty via `cargo deb`. Add
`[package.metadata.deb]` to Cargo.toml with an `assets` list that mirrors
every path the Makefile `install` target installs (binary, .desktop file,
SVG icon, all six shell completions including fig, man page, license), and
add a `deb: build-release` Makefile target that runs `cargo deb --no-build`
after `build-release` has produced the release binary and (via the
`ci-release` feature that `build-release` depends on) `completions/` and
`man/`.

## Premise verification (findings, recorded before acting)
1. The Makefile `install` target (Makefile:38-49) installs exactly these
   paths, which is the source of truth for the asset list:
   - `target/release/satty` -> `$(BINDIR)/satty`, mode 755 (`install -s -Dm755`)
   - `satty.desktop` -> `$(PREFIX)/share/applications/satty.desktop`, 644
   - `assets/satty.svg` -> `$(PREFIX)/share/icons/hicolor/scalable/apps/satty.svg`, 644
   - `LICENSE` -> `$(PREFIX)/share/licenses/satty/LICENSE`, 644
   - `completions/_satty` (zsh) -> `share/zsh/site-functions/_satty`, 644
   - `completions/satty.bash` -> `share/bash-completion/completions/satty`, 644
   - `completions/satty.fish` -> `share/fish/vendor_completions.d/satty.fish`, 644
   - `completions/satty.elv` -> `share/elvish/lib/satty.elv`, 644
   - `completions/satty.nu` -> `share/nushell/completions/satty.nu`, 644
   - `completions/satty.ts` (fig) -> `share/fig/autocomplete/satty.ts`, 644
   - `man/satty.1` -> `share/man/man1/satty.1`, 644
2. `completions/` and `man/` do not exist in a plain checkout; `build.rs`
   only writes them to the repo root when the `ci-release` cargo feature is
   enabled (build.rs:19-23, :38-42). The Makefile's `build-release` target
   already forces this: `target/release/satty` recipe runs
   `cargo build --release --features ci-release` (Makefile:29-30). So a
   `deb` target that depends on `build-release` gets both the binary and
   the generated completions/man for free, matching the task's stated
   assumption ("build-release dependency runs the ci-release feature
   first"). Verified true, no gap to flag.
3. No existing Debian packaging exists anywhere in the repo (no
   `[package.metadata.deb]`, no `cargo-deb` mention in Makefile/CI, no
   `.deb` output path). This is a net-new addition, not a fix.
4. `cargo deb` (the `cargo-deb` subcommand) reads `[package.metadata.deb]`
   from `Cargo.toml` and each `assets` entry is a 4-tuple
   `["source", "dest", "mode"]` (dest is a directory path ending in `/`
   when the filename is kept as-is, or a full file path to rename).
   `cargo deb --no-build` skips the cargo build step and packages
   whatever is already present in `target/release/`.

## Assumptions (no human available, resolved from evidence)
1. Package metadata (`name`, `section`, `priority`, `extended-description`,
   `depends`) is not specified by the task or derivable from the Makefile;
   use conservative, standard cargo-deb defaults: `name = "satty"`,
   `section = "graphics"` (screenshot/annotation tool), `priority =
   "optional"`, `depends = "$auto"` (cargo-deb's dynamic ldd-based
   dependency resolution, the standard default and explicitly expected by
   the gate's "$auto deps warning on the mock binary is expected").
   `license-file` is set to `["LICENSE", "0"]` per cargo-deb convention
   even though `install` also copies LICENSE as an asset (both are
   standard cargo-deb practice and do not conflict).
2. `[package.metadata.deb]` goes on the root `satty` package's own table in
   the root Cargo.toml (the package that owns `build.rs`/main.rs and is
   what `make install`/`make package` build), not the `cli` workspace
   member, since the install target only ever installs the root binary.
3. Asset file modes: binary keeps 755 (matches `install -Dm755`), all
   other assets use 644 (matches `install -Dm644` for every non-binary
   line in the Makefile install target).
4. The new Makefile `deb` target is named `deb` (task says: add a
   `"deb: build-release"` target, i.e. target name `deb` with prerequisite
   `build-release`) and its recipe is exactly `cargo deb --no-build`,
   matching the task text verbatim. It is not wired into `package` or `install`
   since the task does not ask for that.
5. `cargo-deb` itself is not added as a build-dependency or installed by
   the Makefile/CI (the task only asks for the Cargo.toml metadata + the
   Makefile target that invokes the already-installed `cargo-deb`
   subcommand). Out of scope.

## Acceptance criteria
- [x] `Cargo.toml` (root package) has a `[package.metadata.deb]` table
      whose `assets` list has one entry per Makefile-installed path listed
      in Premise verification #1, with matching destination path and mode
      (755 for the binary, 644 for everything else).
- [x] `Makefile` has a `deb` target with prerequisite `build-release` and
      recipe `cargo deb --no-build`.
- [x] `Cargo.toml` remains valid TOML (verified: `python3 -c
      "import tomllib; tomllib.load(open('Cargo.toml','rb'))"` parses
      without error) - stands in for a deb-specific linter since none is
      present in this repo.
- [ ] Gate (STEP 5, run by the orchestrator): `cargo deb --no-build
      --no-strip` against a mocked release binary + generated
      completions/man produces `target/debian/satty_*.deb`, and
      `dpkg-deb --contents` on it lists the binary, .desktop file, icon,
      all six completions, and the man page.
      [confirmed PASS at gate time, see below]

## Tasks
- [x] Add `[package.metadata.deb]` with full `assets` list to
      Cargo.toml - files: Cargo.toml
- [x] Add `deb: build-release` Makefile target - files: Makefile

## Notes
Q&A: none possible (autonomous run); all open questions resolved as
numbered assumptions above. Reviewed against Makefile as sole source of
truth for asset paths/modes, per task wording ("mirroring every path in
the Makefile install target").
```

## .ai commit history

```
15a50d2 build: deb-packaging
 changes/deb-packaging/spec.md | 17 +++++++++--------
 notes.md                      | 15 +++++++++++++++
 2 files changed, 24 insertions(+), 8 deletions(-)
66bccf6 spec: deb-packaging
 changes/deb-packaging/spec.md | 104 ++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 104 insertions(+)
34880a0 explore: project context
 notes.md | 9 +++++++++
 1 file changed, 9 insertions(+)
c355ee1 init: scaffold (satty)
 .gitignore                |   4 +
 agent/framework.json      |  24 +++++
 agent/tools/probe.py      | 232 ++++++++++++++++++++++++++++++++++++++++++++++
 changes/_archive/.gitkeep |   0
 notes.md                  |  15 +++
 5 files changed, 275 insertions(+)
```

## Target diff

`git diff --stat HEAD` (host repo, HEAD = 2d18065ea534bd12792865784eed86a617ffbdc7):

```
 .gitignore |  1 +
 Cargo.toml | 21 +++++++++++++++++++++
 Makefile   |  3 +++
 3 files changed, 25 insertions(+)
```

Note: `.gitignore` (adds `.ai/`) was already modified by the orchestrator's
STEP 1 scaffolding, before this session started; not touched during
explore/spec/build. `AGENTS.md` and `.claude/` are untracked (`??`) in the
host repo from that same scaffolding step, so `AGENTS.md`'s
GENERATED:project-context edits made during /explore do not appear in
`git diff HEAD` (there is no tracked baseline to diff against) - they are
visible only as the current file content.

Full diff:

```diff
diff --git a/.gitignore b/.gitignore
index xxxxxxx..xxxxxxx 100644
--- a/.gitignore
+++ b/.gitignore
@@ -17,3 +17,4 @@ man/
 # ...
+.ai/

diff --git a/Cargo.toml b/Cargo.toml
@@ -20,6 +20,27 @@ include = [
 [features]
 ci-release = []

+[package.metadata.deb]
+name = "satty"
+section = "graphics"
+priority = "optional"
+license-file = ["LICENSE", "0"]
+extended-description = "Modern Screenshot Annotation."
+depends = "$auto"
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
@@ -30,6 +30,9 @@ target/debug/satty: $(SOURCEFILES) Cargo.lock Cargo.toml
 target/release/satty: $(SOURCEFILES) Cargo.lock Cargo.toml
 	cargo build --release --features ci-release

+deb: build-release
+	cargo deb --no-build
+
 clean:
 	cargo clean
```

## Premise verification finding

Task text asserted: "the build-release dependency runs the ci-release
feature first, generating completions/ and man/". Verified true against
`build.rs` (lines 19-23 gate `completions/` on `cfg!(feature =
"ci-release")`; lines 38-42 gate `man/` the same way) and `Makefile`
(`target/release/satty`'s recipe already passes `--features ci-release`,
and `build-release` depends on `target/release/satty`). No correction
needed; recorded as spec Premise verification item #2.

Also verified: no pre-existing Debian packaging anywhere in the repo
(`[package.metadata.deb]`, `cargo-deb`, `.deb`) before this change - task
is additive, not corrective.

## Gate output (STEP 5)

Command run exactly as specified from WORK_DIR.

```
warning: Failed to find dependency specification.
         No $auto deps for /workspace/target/release/satty
/workspace/target/debian/satty_0.21.1-1_amd64.deb
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

**Gate result: PASS.**

- `target/debian/satty_0.21.1-1_amd64.deb` produced.
- `dpkg-deb --contents` lists: binary (`usr/bin/satty`), `.desktop` file,
  icon (SVG), all six completions (bash, zsh `_satty`, fish, elvish,
  nushell, fig), and the man page (`usr/share/man/man1/satty.1.gz`,
  auto-gzipped by cargo-deb - expected cargo-deb behavior, not a
  divergence from the spec, whose asset source path `man/satty.1` matches
  exactly what's on disk before packaging).
- The `$auto deps` warning is the expected/allowed one per the gate
  instructions (mock ELF binary has no real ldd-resolvable dependencies).

## Observations

1. The task's stated premise (ci-release feature auto-generates
   completions/man via build-release) held up under direct code
   verification (build.rs + Makefile) - no correction was needed, which
   kept the spec short. Premise-checking cost two file reads and paid off
   as a documented non-finding rather than a blind trust call.
2. AGENTS.md's `GENERATED:project-context` section and `.ai/notes.md` were
   both used directly during /spec and /build: the Makefile `install`
   target and build.rs details captured during /explore were the primary
   input for the asset list and the build-release/ci-release dependency
   chain reasoning, avoiding a second full read of those files during
   /spec. Roughly: high use of the explore digest, since the task is
   packaging-metadata-only and the digest already named every load-bearing
   file (Makefile, build.rs, Cargo.toml, asset paths).
3. The `reviewer` sub-agent type named in `.claude/agents/reviewer.md`
   was not spawnable through this environment's Agent tool (only
   `claude`, `claude-code-guide`, `Explore`, `general-purpose`, `Plan`,
   `statusline-setup` were available); per the build skill's documented
   fallback, a fresh `general-purpose` sub-agent was used instead, given
   only the diff and acceptance criteria. It returned PASS with one
   non-blocking observation (uncompressed man page asset path, which
   matches the Makefile's own uncompressed `install` convention and cargo
   deb gzips it automatically on packaging regardless).
4. The change was metadata/build-config only (no Rust source touched), so
   `cargo test`/`cargo clippy` were not re-run as part of build - the
   spec's ecosystem-correctness criterion for this task was TOML validity
   (checked) plus the packaging gate itself (STEP 5), not a Rust linter,
   which the spec noted explicitly under "ecosystem correctness."
5. `.gitignore`'s `.ai/` line and the untracked `AGENTS.md`/`.claude/`
   files predate this session (STEP 1 scaffolding); the target diff
   above only reflects genuinely new work (Cargo.toml, Makefile) plus
   that pre-existing `.gitignore` line, which is included in `--stat`
   output but was not authored in this session.

## Token usage (count_tokens.py, informational)

Note: dispatched as a Task-tool sub-agent inside one orchestrator session; counted by isolating this agent's transcript. The reviewer sub-agent is a sibling transcript (spawnDepth 2), counted separately below and added per the runbook rule.

- Sessions: 1 | API calls: 39 | duplicate lines skipped: 39

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 78 | 83669 | 2333773 | 3864 | 2421384 |
| **all** | 78 | 83669 | 2333773 | 3864 | 2421384 |

Reviewer sub-agent:

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 2 | 12668 | 25056 | 2 | 37728 |
| **all** | 2 | 12668 | 25056 | 2 | 37728 |
