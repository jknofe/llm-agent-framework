# Results: rust-package-s5m-2026-07-03

## Configuration

| Field | Value |
|---|---|
| Run ID | rust-package-s5m-2026-07-03 |
| Cell | rust-package (Satty, tag v0.21.1) |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-03T20:03:27 |
| End | 2026-07-03T20:08:44 |
| Duration | ~5m17s |
| Gate | **PASS** |

Scaffold used explicit `--size small` (not `--size auto`); no auto-size
informational line applicable.

## Spec/plan produced

`.ai/changes/deb-packaging/spec.md` (status: done). Goal: add
`[package.metadata.deb]` to `Cargo.toml` mirroring `make install`'s 11
destination paths, plus a `deb: build-release` Makefile target running
`cargo deb --no-build`. 6 acceptance criteria, 4 tasks, 5 numbered
assumptions in Notes (all resolved from code evidence, no human available):

1. Metadata goes in the root `Cargo.toml` (mixed package+workspace manifest),
   not `cli/Cargo.toml` (cli is a library, not the packaged binary).
2. Zsh completion asset uses `usr/share/zsh/site-functions/_satty` (literal
   Makefile mirror via `$(ZSHDIR)`), not the Debian-purist
   `zsh/vendor-completions/` path called out as a high-effort-only extra in
   the task brief.
3. Completion filename renames mirrored exactly per-shell (bash renames
   `satty.bash` -> `satty` on install; fish/elv/nu/fig keep their extension).
4. No explicit `strip` setting added (task scope is asset mapping + target
   only; GATE runs `--no-strip` anyway).
5. High-effort extras (section, priority, extended-description,
   license-file, versioned depends, vendor-completions path) intentionally
   omitted per the task's EFFORT=medium instruction ("optional... only if
   the code makes them obvious"), none are derivable from the repo (no
   existing Debian control file/changelog).

## .ai commit history

```
392da2c build: deb-packaging
25ad1c9 spec: deb-packaging
fbce710 explore: project context
86ada44 init: small-profile scaffold (satty)
```

Matches expected small-profile sequence: init -> explore -> spec -> build.

## Premise-verification finding

Verified before acting (recorded in `.ai/notes.md`):
- `completions/` and `man/satty.1` are **not** checked into the repo; `build.rs`
  only writes them to the repo root when built with `--features ci-release`
  (a plain `cargo build` buries them under `$OUT_DIR` instead). Confirmed the
  Makefile's `build-release` -> `target/release/satty` -> `cargo build
  --release --features ci-release` chain always passes `ci-release`, so `make
  deb`'s `build-release` prerequisite is sufficient to populate both
  `completions/` and `man/` before `cargo deb --no-build` runs.
- Confirmed no pre-existing `[package.metadata.deb]` / cargo-deb usage
  anywhere in the repo (Cargo.toml, cli/Cargo.toml, `.github/workflows/*`,
  README); `.github/workflows/release.yml` only produces a tarball + a
  Flatpak, no `.deb`. This is new packaging surface, not a fix to an existing
  one.
- Makefile's `ZSHDIR` is defined as `$(PREFIX)/share/zsh/site-functions`
  everywhere; the Makefile never references `zsh/vendor-completions`
  (confirming assumption 2 above is a correct literal mirror, not a guess).
- Reviewer sub-agent (spawned via `Agent` tool, general-purpose, given only
  the diff + acceptance criteria) flagged one **pre-existing, not
  newly-introduced** fragility: `build-release`'s make prerequisite is the
  *file* `target/release/satty`; if that file already exists from a prior
  plain (non-`ci-release`) build, make would treat it as up to date and skip
  regenerating `completions/`/`man/`, so `cargo deb --no-build` could see
  stale/missing assets. This exposure is identical to the one `install` has
  always had, not a regression, recorded in `.ai/notes.md` as a gotcha with
  a `make clean` mitigation.

## Target diff

```
$ git diff --stat HEAD
 .gitignore |  1 +
 Cargo.toml | 15 +++++++++++++++
 Makefile   |  3 +++
 3 files changed, 19 insertions(+)
```

(`.gitignore`'s `+.ai/` line is scaffold-generated, not part of the task.)

```diff
diff --git a/Cargo.toml b/Cargo.toml
index 1e1d3c9..a44b4e4 100644
--- a/Cargo.toml
+++ b/Cargo.toml
@@ -20,6 +20,21 @@ include = [
 [features]
 ci-release = []
 
+[package.metadata.deb]
+assets = [
+    ["target/release/satty", "usr/bin/satty", "755"],
+    ["satty.desktop", "usr/share/applications/satty.desktop", "644"],
+    ["assets/satty.svg", "usr/share/icons/hicolor/scalable/apps/satty.svg", "644"],
+    ["LICENSE", "usr/share/licenses/satty/LICENSE", "644"],
+    ["completions/_satty", "usr/share/zsh/site-functions/_satty", "644"],
+    ["completions/satty.bash", "usr/share/bash-completion/completions/satty", "644"],
+    ["completions/satty.fish", "usr/share/fish/vendor_completions.d/satty.fish", "644"],
+    ["completions/satty.elv", "usr/share/elvish/lib/satty.elv", "644"],
+    ["completions/satty.nu", "usr/share/nushell/completions/satty.nu", "644"],
+    ["completions/satty.ts", "usr/share/fig/autocomplete/satty.ts", "644"],
+    ["man/satty.1", "usr/share/man/man1/satty.1", "644"],
+]
+
 [dependencies]
 satty_cli.workspace = true
 relm4 = { version = "0.10.1", features = ["macros", "libadwaita", "gnome_42"] }
diff --git a/Makefile b/Makefile
index b1bbc93..7a6b9b7 100644
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

## Full gate output

Mock artifact setup (per fixed runbook, exact commands):
```
mkdir -p "$WORK_DIR"/target/release "$WORK_DIR"/completions "$WORK_DIR"/man
printf '\x7fELF\x02\x01\x01\x00' > "$WORK_DIR"/target/release/satty
chmod +x "$WORK_DIR"/target/release/satty
for f in satty.bash _satty satty.fish satty.elv satty.nu satty.ts; do
  [ -f "$WORK_DIR"/completions/$f ] || touch "$WORK_DIR"/completions/$f; done
[ -f "$WORK_DIR"/man/satty.1 ] || touch "$WORK_DIR"/man/satty.1
```

GATE command and full output:
```
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

`target/debian/satty_0.21.1-1_arm64.deb` produced (arch is `arm64`, matching
the Docker host's native architecture; the PASS rule does not require
`x86_64`). `dpkg-deb --contents` lists the binary (`usr/bin/satty`), the
`.desktop` entry, the SVG icon, the LICENSE, all 6 shell completions (bash,
zsh `_satty`, fish, elvish, nushell, fig `.ts`), and the man page
(auto-gzipped by cargo-deb to `satty.1.gz`, standard Debian convention, not a
gap). The `$auto` deps warning against the mock non-ELF-real binary is
expected per the GATE spec, not a failure. `usr/share/doc/satty/copyright`
is cargo-deb's own auto-generated addition (from `license`/`license-file`
metadata), not one of the 11 mapped assets, and is additive/harmless.

**PASS**: deb produced, all assets listed.

## Observations

1. The single highest-value verification step was reading `build.rs` before
   writing the Makefile target: the `ci-release` feature gate (repo-root vs
   `$OUT_DIR` for completions/man) is not mentioned anywhere in the task
   brief's surface text and would have been easy to miss, silently producing
   a `deb` target that only works if a prior `ci-release` build happened to
   already exist.
2. The bash-completion install-time rename (`completions/satty.bash` ->
   `.../completions/satty`, dropping the extension) is the one entry in an
   11-item list that breaks the naming pattern the other 5 completions
   follow; both the spec and the independent reviewer sub-agent called it
   out explicitly as the likely error point, and it was correct in the
   diff, worth flagging as a good adversarial-review test point for this
   task in future runs.
3. The task text pre-announces its own EFFORT=high extras and explicitly
   labels them optional at medium, which made the scope decision
   mechanical rather than judgment-heavy; the "no code evidence for
   section/priority/extended-description" reasoning in spec assumption 5
   is the honest justification, not just deference to the brief.
4. The Debian zsh path (`usr/share/zsh/vendor-completions/`) mentioned in the
   task as a high-effort extra does not actually exist anywhere in this
   Makefile (`ZSHDIR` is hardcoded to `site-functions`), so at medium effort
   the literal "mirror the Makefile" instruction and the "skip high-effort
   extras" instruction agree rather than conflict, a case where the
   premise-check made an otherwise-ambiguous scope call unambiguous.
5. `cargo deb`'s automatic `usr/share/doc/<pkg>/copyright` generation means
   the produced `.deb` has 12 real files under `usr/` (11 mapped + the
   auto-copyright, plus directory entries), which is expected cargo-deb
   behavior and does not indicate an asset-mapping bug.
6. Total task turnaround (clone through gate PASS) was about 5 minutes at
   medium effort for a 2-file, 19-line diff; the spec/build/review
   overhead was small relative to the premise verification (reading
   `build.rs`, the full `Makefile`, and confirming no prior deb metadata
   existed).
