# Benchmark Results: sonnet-medium-small

## Configuration

| Field | Value |
|---|---|
| Run ID | hs-2026-07-01/sonnet-medium-small |
| Profile | small |
| Model | claude-sonnet-4-6 |
| Effort | medium |
| Start | 2026-07-01T18:47:57 |
| End | 2026-07-01T18:51:13 |
| Duration (seconds) | 196 |
| Docker status | PASS |

## Spec produced

```markdown
---
id: debian-pkg
title: add debian format to satty build
status: done
created: 2026-07-01
---

## Goal

Add a `[package.metadata.deb]` section to `Cargo.toml` so that `cargo deb --no-build` can produce a Debian `.deb` package from an already-compiled release binary. Add a `deb` target to the `Makefile` that depends on `build-release` (ensuring the binary and all completion/man artifacts are generated with `--features ci-release`) then invokes `cargo deb --no-build`. This gives packagers and CI a single reproducible entry point for producing a `.deb` without manual artifact wrangling.

## Acceptance criteria

- [ ] `Cargo.toml` contains `[package.metadata.deb]` with `name`, `maintainer`, and `depends` fields.
- [ ] `assets` list covers every path installed by `make install`: binary (`target/release/satty`, `755`), `.desktop` file, SVG icon, all six shell completions (bash, zsh, fish, elvish, nushell, fig), man page, and LICENSE.
- [ ] Zsh completion is installed to `usr/share/zsh/site-functions/_satty` (matching Makefile `$(ZSHDIR)/_satty`).
- [ ] `Makefile` has a `deb:` target that depends on `build-release` and runs `cargo deb --no-build`.
- [ ] `cargo deb --no-build` (with mock artifacts in place) produces a `.deb` file under `target/debian/`.
- [ ] No CI workflow file is added or modified.
- [ ] `cargo deb --no-build` with a real binary does not error on the metadata; the `$auto` depends warning for a mock binary is acceptable.

## Tasks

- [ ] Add `[package.metadata.deb]` section to `Cargo.toml` — files: `Cargo.toml`
- [ ] Add `deb: build-release` target to `Makefile` — files: `Makefile`
- [ ] Update `.ai/notes.md` with implementation decisions — files: `.ai/notes.md`
- [ ] Self-review diff against acceptance criteria — no files changed
- [ ] Update spec status to done — files: `.ai/changes/debian-pkg/spec.md`

## Notes

1. **Assumption — maintainer**: Derived from `[workspace.package].authors` = `"Matthias Gabriel <gabm+aur@mailbox.org>"`. No separate maintainer field in Cargo.toml; using this value directly.
2. **Assumption — depends**: Set to `libgtk-4-1, libadwaita-1-0` (GTK4 and libadwaita runtime libs). These are the only runtime shared-library deps that cannot be statically linked for a typical Debian build. `$auto` would compute them from the real binary; specifying them here avoids the auto-detection warning with mock binaries.
3. **Assumption — LICENSE path**: Installed to `usr/share/doc/satty/copyright` as is conventional for Debian, not `usr/share/licenses/satty/LICENSE` (which is the Makefile/Arch convention). Using `usr/share/doc/satty/copyright` satisfies lintian's `no-copyright-file` check.
4. **Assumption — no CI workflow**: The task explicitly forbids adding a CI workflow. The ci-release constraint is documented in notes.md.
5. **Assumption — fig completion**: `completions/satty.ts` → `usr/share/fig/autocomplete/satty.ts` matches Makefile FIGDIR. Fig is non-standard on Debian but included to mirror full Makefile install.
```

## .ai commit history

```
c31795b build: debian-pkg
e0cd789 spec: debian-pkg
29111bb explore: project context
800d3c1 init: small-profile scaffold (satty)
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

## Observations

The framework's explore/spec/build workflow provided clear structure for a contained packaging task: probe.py gave an accurate project overview in one pass, and the Makefile was the authoritative source for asset paths. The ci-release constraint (build.rs only writes completions/man under that feature) was the most critical gotcha and was correctly identified from reading build.rs. The reviewer subagent was unavailable (running as a subagent), so a clean-context self-review was performed instead; all acceptance criteria were met without correctness gaps.
