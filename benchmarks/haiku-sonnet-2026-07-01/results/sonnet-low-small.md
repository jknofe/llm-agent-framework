# Benchmark Results: sonnet-low-small

## Configuration

| Field | Value |
|---|---|
| Run ID | hs-2026-07-01/sonnet-low-small |
| Profile | small |
| Model | claude-sonnet-4-6 |
| Effort | low |
| Start | 2026-07-01T18:47:36 |
| End | 2026-07-01T18:50:01 |
| Duration | 145 seconds |
| Docker status | PASS |

## Spec produced

```
---
id: debian-pkg
title: add debian format to satty build
status: done
created: 2026-07-01
---

## Goal

Add `[package.metadata.deb]` to Cargo.toml and a `deb` Makefile target so that `make deb` produces an installable .deb containing the binary, desktop file, icon, shell completions, man page, and license.

## Acceptance criteria

1. `cargo deb --no-build --no-strip` succeeds and produces `target/debian/satty_*.deb`.
2. The .deb contains all assets from the Makefile install target: binary (usr/bin/satty), .desktop, SVG icon, all 6 shell completions, man page, LICENSE.
3. `make deb` depends on `build-release` (which uses --features ci-release) so completions and man page are generated before packaging.

## Tasks

- `Cargo.toml`: add `[package.metadata.deb]` with name, maintainer, depends=$auto, and assets array covering all Makefile install paths.
- `Makefile`: add `deb: build-release` target running `cargo deb --no-build`.

## Notes

1. Assumes cargo-deb is available in the build environment.
2. `ci-release` feature is required; build.rs only emits completions/ and man/satty.1 under that feature.
3. Zsh completion path follows Makefile: usr/share/zsh/site-functions (not vendor-completions).
4. LICENSE asset covers the install target; no separate license_file directive needed.
```

## .ai commit history

```
602c82c build: debian-pkg
c5df41e spec: debian-pkg
59989cc explore: project context
b7c063d init: small-profile scaffold (satty)
```

## Satty changes

```
.gitignore |  2 +-
 Cargo.toml | 18 ++++++++++++++++++
 Makefile   |  3 +++
 3 files changed, 22 insertions(+), 1 deletion(-)
```

## Docker validation output

```
warning: Failed to find dependency specification.
         No $auto deps for /workspace/target/release/satty
/workspace/target/debian/satty_0.21.1-1_arm64.deb
=== .deb contents ===
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

## .deb contents

```
./usr/bin/satty
./usr/share/applications/satty.desktop
./usr/share/bash-completion/completions/satty
./usr/share/doc/satty/copyright
./usr/share/elvish/lib/satty.elv
./usr/share/fig/autocomplete/satty.ts
./usr/share/fish/vendor_completions.d/satty.fish
./usr/share/icons/hicolor/scalable/apps/satty.svg
./usr/share/licenses/satty/LICENSE
./usr/share/man/man1/satty.1.gz
./usr/share/nushell/completions/satty.nu
./usr/share/zsh/site-functions/_satty
```

## Observations

The explore-spec-build workflow mapped cleanly onto a Cargo/Makefile project: probe.py gave an accurate module map and the Makefile install target was the authoritative source of truth for asset paths. The $auto deps warning with a mock ELF binary is expected and non-fatal. The ci-release feature dependency was the main gotcha -- the deb target must chain build-release to ensure completions and man page exist before cargo deb runs.
