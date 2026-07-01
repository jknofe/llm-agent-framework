# Benchmark Results: haiku-low-small

## Configuration

| Property | Value |
|---|---|
| Run ID | hs-2026-07-01/haiku-low-small |
| Profile | small |
| Model | claude-haiku-4-5 |
| Effort | low |
| Start | 2026-07-01T18:47:01 |
| End | 2026-07-01T18:55:18 |
| Duration (seconds) | 497 |
| Docker Status | PASS |

## Spec produced

```yaml
---
id: debian-pkg
title: "add debian format to satty build"
status: done
created: 2026-07-01
---

## Goal
Add Debian package metadata to Cargo.toml and a `make deb` target to the Makefile so `cargo deb --no-build` produces a working .deb with all bundled assets (binary, desktop file, icon, completions, man page, license).

## Acceptance criteria
- [ ] `make deb` target depends on build-release and runs `cargo deb --no-build`
- [ ] target/debian/satty_*.deb file is created
- [ ] .deb contains binary, desktop file, icon, all completions (bash/zsh/fish/elvish/nushell/fig), man page, and license

## Tasks
- [ ] Add [package.metadata.deb] section to Cargo.toml with all assets - files: Cargo.toml
- [ ] Add `deb: build-release` target to Makefile - files: Makefile

## Notes
1. build.rs generates completions/ and man/satty.1 only when ci-release feature is enabled; Makefile build-release already does this
2. metadata.deb.assets must map source paths (completions/satty.bash, etc.) to destination paths (/usr/share/bash-completion/completions/satty, etc.)
3. cargo-deb reads maintainer from Cargo.toml authors field (already set: Matthias Gabriel); license from license field (MPL-2.0)
4. Lintian will warn if extended description is missing, but --quiet suppresses it for this low-effort implementation
5. Desktop file validation is not performed by deb build; assume satty.desktop is well-formed
```

## .ai commit history

```
254d584 build: debian-pkg
b9d0694 spec: debian-pkg
f349e77 explore: project context
0569bfc init: small-profile scaffold (satty)
```

## Satty changes

```
.gitignore |  2 +-
 Cargo.toml | 18 ++++++++++++++++++
 Makefile   |  9 ++++++---
 3 files changed, 25 insertions(+), 4 deletions(-)
```

Changes summary:
- Added [package.metadata.deb] section to Cargo.toml with full asset manifest (binary, desktop, icon, completions, man page, license)
- Added `deb: build-release` Makefile target that runs `cargo deb --no-build`
- .gitignore updated to exclude .ai/ directory

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

Status: PASS - target/debian/satty_0.21.1-1_arm64.deb successfully created with all required assets.

## .deb contents (dpkg-deb listing)

```
./usr/bin/satty
./usr/share/applications/satty.desktop
./usr/share/bash-completion/completions/satty
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

Framework workflow executed autonomously at low-effort tier without blocking: explore step extracted project context from probe/Cargo.toml/Makefile; spec step produced 2-3 acceptance criteria mapping Makefile install paths to FHS locations; build step implemented metadata.deb asset manifest and Makefile deb target with proper build-release dependency chain. Docker validation confirmed .deb generation and verified all assets present (binary, desktop, icon, completions, man page, license). Zsh completion path correctly mapped to /usr/share/zsh/site-functions per FHS spec.
