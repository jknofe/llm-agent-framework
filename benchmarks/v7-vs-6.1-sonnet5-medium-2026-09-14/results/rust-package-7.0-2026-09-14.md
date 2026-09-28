# Benchmark result: rust-package-7.0-2026-09-14 (satty)

## Configuration

| Field | Value |
|---|---|
| Run ID | rust-package-7.0-2026-09-14 |
| Cell | rust-package |
| Framework version | 7.0 (profile: small, harness: claude) |
| Model | claude-sonnet-5 |
| Effort | medium |
| Repo | gabm/Satty @ 2d18065ea534bd12792865784eed86a617ffbdc7 |
| Start | 2026-09-14T16:49:34 |
| End | 2026-09-14T16:55:30 |
| Duration | ~6 min |
| Gate | **PASS** |

## Spec produced

`.ai/changes/DEB-1/spec.md`, id `DEB-1`, status `done`. Goal: add
`[package.metadata.deb]` to `Cargo.toml` (11-entry `assets` array mirroring
the Makefile `install` target path-for-path: binary, `.desktop`, SVG icon,
LICENSE, 6 shell completions incl. fig, man page) and a `deb: build-release`
Makefile target running `cargo deb --no-build`. Acceptance criteria included
exact path/mode matches, lint/fmt passing, TOML validity, and `dpkg-deb
--contents` covering every mirrored path. Notes section recorded 5 numbered
assumptions (no human available): asset list = literal Makefile mirror;
`assets` array replaces cargo-deb's implicit default so the binary must be
listed explicitly; no extra metadata keys (maintainer/depends) invented
since defaults cover them; LICENSE included as a plain asset (not via
`license-file`) to match the Makefile's literal step; `deb` depends on
`build-release` (not `force-build-release`) per the task's own wording.

## .ai commit history

```
b76c132 build: DEB-1
518e5a8 spec: DEB-1
f42ebb3 explore: project context
c82a961 init: scaffold (satty)
```

(`c82a961` was the orchestrator's pre-existing scaffold commit; the other
three were made during this run.)

## Target diff

`git -C $WORK_DIR diff --stat HEAD`:
```
 .gitignore |  1 +
 Cargo.toml | 15 +++++++++++++++
 Makefile   |  3 +++
 3 files changed, 19 insertions(+)
```
(The `.gitignore` `+.ai/` line predates this task, added by the
orchestrator's scaffold step, not by DEB-1.)

Full diff (`Cargo.toml`, `Makefile`):
```diff
diff --git a/Cargo.toml b/Cargo.toml
index 1e1d3c9..f8c8052 100644
--- a/Cargo.toml
+++ b/Cargo.toml
@@ -52,6 +52,21 @@ keycode = "1.0.0"
 [dependencies.relm4-icons]
 version = "0.10.0"
 
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
 
 [build-dependencies]
 clap.workspace = true
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

## Full gate output

Setup commands (mock binary, completions, man page) ran clean, then:

```
$ docker run --rm -v $WORK_DIR:/workspace satty-deb-builder bash -c '
    cd /workspace && cargo deb --no-build --no-strip 2>&1
    echo "=== contents ==="
    dpkg-deb --contents target/debian/satty_*.deb | awk "{print \$6}" | sort
  '

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

PASS check: `target/debian/satty_0.21.1-1_arm64.deb` was produced, and
`dpkg-deb --contents` lists the binary (`usr/bin/satty`), `.desktop`, SVG
icon, LICENSE, all 6 completions (bash, zsh `_satty`, fish, elvish,
nushell, fig), and the man page. The man page appears as
`satty.1.gz` — cargo-deb auto-gzips files under `usr/share/man/`
per Debian policy; this is correct, expected packaging behavior, not a
path mismatch (the source asset path we declared was the plain `.1`).
`usr/share/doc/satty/copyright` is cargo-deb's own auto-generated file,
unrelated to our `assets` list. The `$auto deps` warning is the
documented expected non-failure (mock ELF has no real dynamic
dependencies to inspect). **Gate: PASS.**

## Observations

1. The task's own claim about `build-release` ("the build-release
   dependency runs the ci-release feature first, generating completions/
   and man/") checked out exactly against `build.rs` and the Makefile:
   `target/release/satty`'s recipe passes `--features ci-release`, and
   `build.rs` only writes `completions/`/`man/` to the repo root (rather
   than `$OUT_DIR`) under that feature. No guesswork needed — good sign the
   task author had read the code.
2. `cargo`/GTK4 were not available in the sandbox, so the spec's lint/test
   acceptance criterion (`cargo fmt --check`, `cargo clippy ...`) could not
   actually be executed locally; only reasoned about (diff touches no
   `.rs` files) and left explicitly unchecked with a note in the spec
   rather than silently marked done. The Docker gate in Step 5 is what
   actually exercises `cargo deb`.
3. Framework friction: the `.claude/agents/reviewer.md` custom sub-agent
   defined by the scaffold is not spawnable from this run — the Agent tool's
   available `subagent_type`s here don't include the project-scoped
   `reviewer` type (that only exists inside a live Claude Code session
   rooted at the project). Per the build skill's own fallback ("spawn a
   fresh general-purpose sub-agent given only the diff and the criteria"),
   used `general-purpose` with the reviewer agent's own instructions +
   diff + criteria as the prompt. Worth noting in case the harness intends
   custom sub-agents to be reachable cross-session — currently they are not
   from an external orchestrator.
4. The explore skill's request to "ask the user" degenerated cleanly to
   "resolve from evidence" per the autonomous-run framing baked into both
   the top-level task and the skill text itself (`If no human is available
   ... record what probe detected`); no friction there, the skill already
   anticipates unattended runs.
5. `cargo-deb`'s implicit man-page gzip (`satty.1.gz` vs. declared
   `satty.1`) is a case where "mirror the Makefile path literally" and
   "produce a policy-correct .deb" diverge slightly at the packaging-tool
   layer; the gate's PASS wording ("lists ... man page") absorbed this
   without needing a workaround, but a stricter path-equality check
   would have needed to special-case it.

## Key files

- `/tmp/benchmark/runs/rust-package-7.0-2026-09-14/satty/Cargo.toml`
- `/tmp/benchmark/runs/rust-package-7.0-2026-09-14/satty/Makefile`
- `/tmp/benchmark/runs/rust-package-7.0-2026-09-14/satty/AGENTS.md`
- `/tmp/benchmark/runs/rust-package-7.0-2026-09-14/satty/.ai/notes.md`
- `/tmp/benchmark/runs/rust-package-7.0-2026-09-14/satty/.ai/changes/DEB-1/spec.md`
