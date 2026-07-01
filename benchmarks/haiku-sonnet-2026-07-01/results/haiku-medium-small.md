# Benchmark Results: haiku-medium-small

## Configuration

| Key | Value |
|---|---|
| Run ID | hs-2026-07-01/haiku-medium-small |
| Profile | small |
| Model | claude-haiku-4-5 |
| Effort | medium |
| Start | 2026-07-01T18:47:20 |
| End | 2026-07-01T18:51:11 |
| Duration (seconds) | 231 |
| Docker Status | PASS |

## Spec Produced

```
---
id: debian-pkg
title: Add debian format to satty build
status: done
created: 2026-07-01
---

## Goal

Enable cargo-deb to build .deb packages for Satty with all required assets (binary, icons, completions, man pages, desktop file, license) following the paths defined in the existing Makefile install target.

## Acceptance Criteria

A Debian package (.deb) built with `make deb` must:

1. **Binary inclusion**: Include satty binary at /usr/bin/satty (755, stripped)
2. **Desktop file**: Include satty.desktop at /usr/share/applications/satty.desktop
3. **Icon**: Include assets/satty.svg at /usr/share/icons/hicolor/scalable/apps/satty.svg
4. **License**: Include LICENSE file at /usr/share/doc/satty/LICENSE
5. **Shell completions** (all 6):
   - _satty (zsh) at /usr/share/zsh/site-functions/_satty
   - satty.bash at /usr/share/bash-completion/completions/satty
   - satty.fish at /usr/share/fish/vendor_completions.d/satty.fish
   - satty.elv at /usr/share/elvish/lib/satty.elv
   - satty.nu at /usr/share/nushell/completions/satty.nu
   - satty.ts (fig) at /usr/share/fig/autocomplete/satty.ts
6. **Man page**: Include man/satty.1 at /usr/share/man/man1/satty.1.gz
7. **Metadata**: 
   - Package name: satty
   - Maintainer: Matthias Gabriel <gabm+aur@mailbox.org>
   - Version: 0.21.1 (from Cargo.toml [workspace.package])
   - Architecture: x86_64 (implicit in cargo-deb)
8. **Dependencies**: linux-gnu GTK4/libadwaita runtime dependencies declared
9. **Build command**: Makefile target `make deb` runs `cargo deb --no-build` and produces target/debian/satty_*.deb
10. **No CI workflow**: Do not add a GitHub Actions workflow for deb release

## Tasks

1. **Cargo.toml [package.metadata.deb]**:
   - Add [package.metadata.deb] section to Cargo.toml
   - Set name = "satty"
   - Set maintainer = "Matthias Gabriel <gabm+aur@mailbox.org>"
   - Set depends = ["gtk4", "libadwaita-1", "libssl3"]
   - Define assets: binary, desktop, icon, completions (all 6), man page, license

2. **Makefile deb target**:
   - Add `deb: build-release` target
   - Run `cargo deb --no-build`
   - Depend on build-release so ci-release feature is active

3. **Verify completions and man page generation**:
   - Confirm build.rs writes to completions/ and man/ when ci-release feature is enabled
   - Makefile already builds with --features ci-release; no changes needed to build.rs

4. **Test asset paths**:
   - Verify all 8 assets (binary + 7 files) are included in .deb
   - Use dpkg-deb --contents to verify paths match acceptance criteria

## Notes

1. **Assumption: GTK4 dependencies**: Using gtk4, libadwaita-1, libssl3 as base depends. Actual transitive dependencies can be inspected post-build with `dpkg-deb -I`.

2. **Assumption: Stripped binary**: cargo-deb strips binaries by default; no --strip flag needed.

3. **Assumption: License destination**: cargo-deb auto-installs LICENSE to /usr/share/doc/satty/COPYRIGHT or /usr/share/doc/satty/LICENSE; will verify in docker validation.

4. **Assumption: No AppStream metadata**: .metainfo.xml not required for a functional deb; can be added later if needed.

5. **Assumption: No CI workflow added**: Per spec, do not modify .github/workflows/; only modify Cargo.toml and Makefile.

6. **Assumption: deb target depends on build-release**: Ensures ci-release feature runs build.rs to write completions/ and man/ to tree, critical for packaging.

7. **Assumption: Completion shell names**: Names match build.rs: satty.bash, _satty (zsh, underscore prefix), satty.fish, satty.elv, satty.nu, satty.ts (fig).
```

## .ai Commit History

```
cdc8493 build: debian-pkg
af66c21 spec: debian-pkg
b145bc0 explore: project context
3bf490f init: small-profile scaffold (satty)
```

## Satty Changes

```
.gitignore |  2 +-
 Cargo.toml | 20 ++++++++++++++++++++
 Makefile   |  9 ++++++---
 3 files changed, 27 insertions(+), 4 deletions(-)
```

## Docker Validation Output

```
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
./usr/share/doc/satty/LICENSE
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

## .deb Contents Verification

All acceptance criteria assets present:

1. Binary: `./usr/bin/satty` - PASS
2. Desktop file: `./usr/share/applications/satty.desktop` - PASS
3. Icon: `./usr/share/icons/hicolor/scalable/apps/satty.svg` - PASS
4. License: `./usr/share/doc/satty/LICENSE` - PASS
5. Shell completions (all 6):
   - `./usr/share/zsh/site-functions/_satty` - PASS
   - `./usr/share/bash-completion/completions/satty` - PASS
   - `./usr/share/fish/vendor_completions.d/satty.fish` - PASS
   - `./usr/share/elvish/lib/satty.elv` - PASS
   - `./usr/share/nushell/completions/satty.nu` - PASS
   - `./usr/share/fig/autocomplete/satty.ts` - PASS
6. Man page: `./usr/share/man/man1/satty.1.gz` - PASS

## Observations

The llm-agent-framework small-profile workflow successfully implemented Debian packaging support for Satty in medium effort. The agent correctly identified all required assets from the Makefile install target, mapped them to their Debian paths using cargo-deb, and structured the implementation via spec-driven design (.ai/changes/debian-pkg/spec.md). The critical insight was recognizing that the deb: Makefile target must depend on build-release to activate the ci-release feature, which causes build.rs to write completions and man pages to the source tree before cargo-deb packages them. Docker validation confirmed all 11 assets (binary + desktop + icon + license + 6 completions + man page) are present in the .deb at correct paths. The workflow was efficient: explore identified the project architecture, spec codified acceptance criteria as numbered autonomous assumptions, build implemented Cargo.toml and Makefile changes, and Docker validation verified the output in a single container run.

## CI/Release Constraint

Per spec, no GitHub Actions workflow was added. Deb packaging is available via `make deb` locally and in CI environments with cargo-deb installed; no release automation was configured.
