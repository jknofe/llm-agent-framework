# Rust package baseline - 2026-07-06 - satty

## Configuration

| Field | Value |
|---|---|
| Run ID | rust-package-baseline-2026-07-06 |
| Cell | rust-package |
| Arm | baseline (no framework) |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-06T16:50:30 |
| End | 2026-07-06T16:51:41 |
| Duration | ~1m11s (wall clock between recorded timestamps; excludes report-writing tail) |
| Gate | PASS |

## Premise verification

Task premise checked against actual repo code before acting (see full numbered
assumptions in `$WORK_DIR/../BASELINE-NOTES.md`, copied below):

1. Cargo.toml at repo root is both the `satty` package manifest AND the
   workspace root (`[workspace] members = ["cli"]`) - `[package.metadata.deb]`
   belongs directly in this file, there is no separate top-level manifest.
2. Makefile `install` target (lines 36-47) is the source of truth for asset
   paths/modes: binary (usr/bin/satty, 755), satty.desktop (644),
   assets/satty.svg icon (644), completions/_satty (zsh), completions/satty.bash,
   completions/satty.fish, completions/satty.elv, completions/satty.nu,
   completions/satty.ts (fig), man/satty.1, and LICENSE - all mapped 1:1 to
   the deb asset paths cargo-deb expects, same modes as `install -Dm...`.
3. build.rs (lines 15-44) only populates `completions/` and `man/` on disk when
   built with `--features ci-release` (`cfg!(feature = "ci-release")` gate);
   Makefile's `build-release` target already invokes
   `cargo build --release --features ci-release`, so making `deb:` depend on
   `build-release` is necessary and sufficient - confirms the task's
   parenthetical about `ci-release` running first.
4. `.gitignore` confirms `completions/` and `man/` are generated/gitignored,
   consistent with (3).
5. No pre-existing cargo-deb config/references anywhere in the repo
   (Cargo.toml, Makefile, .github/workflows, release.nu, flake.nix) - this is
   a net-new addition, not a fix.
6. Left `depends` unset so cargo-deb uses its default `$auto` runtime-dependency
   inference (expected to warn against the mock ELF binary in the gate, not a
   real failure).
7. Did not add an explicit `maintainer` field; cargo-deb derives it from
   `[workspace.package] authors`, which is present.

No premise mismatches found; task description matched the codebase exactly.

## Diff

```
$ git diff --stat HEAD
Cargo.toml | 15 +++++++++++++++
Makefile   |  3 +++
2 files changed, 18 insertions(+)
```

```diff
--- a/Cargo.toml
+++ b/Cargo.toml
@@ -62,6 +62,21 @@ clap_complete_fig = "4.5.2"
 relm4-icons-build = "0.11"
 clap_mangen = "0.3.0"

+[package.metadata.deb]
+assets = [
+  ["target/release/satty", "usr/bin/satty", "755"],
+  ["satty.desktop", "usr/share/applications/satty.desktop", "644"],
+  ["assets/satty.svg", "usr/share/icons/hicolor/scalable/apps/satty.svg", "644"],
+  ["completions/_satty", "usr/share/zsh/site-functions/_satty", "644"],
+  ["completions/satty.bash", "usr/share/bash-completion/completions/satty", "644"],
+  ["completions/satty.fish", "usr/share/fish/vendor_completions.d/satty.fish", "644"],
+  ["completions/satty.elv", "usr/share/elvish/lib/satty.elv", "644"],
+  ["completions/satty.nu", "usr/share/nushell/completions/satty.nu", "644"],
+  ["completions/satty.ts", "usr/share/fig/autocomplete/satty.ts", "644"],
+  ["man/satty.1", "usr/share/man/man1/satty.1", "644"],
+  ["LICENSE", "usr/share/licenses/satty/LICENSE", "644"],
+]
+
 [workspace]
 members = [ "cli" ]

--- a/Makefile
+++ b/Makefile
@@ -79,6 +79,9 @@ uninstall:
 	rm $(FIGDIR)/satty.ts
 	rmdir -p $(FIGDIR) || true

+deb: build-release
+	cargo deb --no-build
+
 package: clean build-release
 	$(eval TMP := $(shell mktemp -d))
 	echo "Temporary folder ${TMP}"
```

## Gate output (full)

```
$ docker image inspect satty-deb-builder  ->  IMAGE EXISTS

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
EXIT_CODE=0
```

Additional verification (permission modes inside the built deb):

```
-rwxr-xr-x 0/0               8 2026-07-06 00:00 ./usr/bin/satty
-rw-r--r-- 0/0           16725 2026-07-06 00:00 ./usr/share/licenses/satty/LICENSE
-rw-r--r-- 0/0               0 2026-07-06 00:00 ./usr/share/zsh/site-functions/_satty
-rw-r--r-- 0/0             313 2026-07-06 00:00 ./usr/share/applications/satty.desktop
-rw-r--r-- 0/0            3538 2026-07-06 00:00 ./usr/share/icons/hicolor/scalable/apps/satty.svg
-rw-r--r-- 0/0              20 2026-07-06 00:00 ./usr/share/man/man1/satty.1.gz
```

Gate result: **PASS** - `target/debian/satty_0.21.1-1_arm64.deb` was produced,
and `dpkg-deb --contents` lists the binary (mode 755), the .desktop file, the
SVG icon, all six completions (bash, zsh, fish, elvish, nu, fig), the man page,
and the license. The `$auto` deps warning against the placeholder ELF binary
appeared as expected and is not a failure.

## Observations

1. The task's premise held exactly: the Makefile `install` target enumerates
   every asset path 1:1, and `build.rs`'s `cfg!(feature = "ci-release")` gate
   is exactly why `deb:` must depend on `build-release` (not plain `build`)
   for `completions/` and `man/` to exist on disk before `cargo deb --no-build`
   runs.
2. cargo-deb automatically gzips the man page (`satty.1` -> `satty.1.gz`) and
   adds a synthesized `usr/share/doc/satty/copyright` file derived from the
   license/metadata - neither is an asset entry, both are cargo-deb's own
   packaging behavior, so no corresponding Cargo.toml lines were needed for them.
3. Root Cargo.toml doubles as the workspace manifest (`[workspace] members =
   ["cli"]`); `[package.metadata.deb]` still works fine there since cargo-deb
   keys off the `[package]` table, which coexists with `[workspace]` in the
   same virtual/mixed manifest.
4. Left `depends` unspecified (cargo-deb defaults to `$auto`, i.e. `ldd`-based
   inference) since no explicit runtime dependency list existed anywhere in the
   repo (no existing .deb/rpm packaging metadata to crib from) - flagged as
   assumption 6 in BASELINE-NOTES.md rather than guessed at silently.
5. No repo tests/lint were affected (only Cargo.toml metadata and Makefile
   changed); did not run `cargo fmt`/`clippy` since neither file is Rust source
   and the task scope was packaging-only, consistent with EFFORT=medium.
## Token usage (count_tokens.py, informational)

Note: this round dispatched cells as Task-tool sub-agents inside one orchestrator
session rather than standalone `claude` CLI processes per cell, so transcripts
live under the parent session's `subagents/` dir, not a work-dir-keyed project
dir. Counted by isolating this agent's `agent-<id>.jsonl` and pointing
`count_tokens.py --projects-dir` at it.

- Transcript dir: `subagents/agent-ab0cb8f24a7fc92a9.jsonl` (isolated)
- Sessions: 1 | API calls: 17 | duplicate lines skipped: 16

| Model | Input | Cache write | Cache read | Output | Total |
|---|---|---|---|---|---|
| claude-sonnet-5 | 34 | 27106 | 513410 | 4279 | 544829 |
| **all** | 34 | 27106 | 513410 | 4279 | 544829 |
