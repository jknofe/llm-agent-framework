# Benchmark Results: sonnet5-medium-small

## Configuration
| Field | Value |
|---|---|
| Run ID | sonnet5-medium-small |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | medium |
| Start | 2026-07-02T08:39:02 |
| End | 2026-07-02T08:49:49 |
| Duration | 647 s |
| Docker status | PASS |

## Spec produced

```markdown
---
id: debian-pkg
title: add debian format to satty build
status: done
created: 2026-07-02
---

## Goal
Satty currently ships tarball releases (x86_64/aarch64) and a Flatpak, but no
Debian package, forcing Debian/Ubuntu users onto manual `make install` or
third-party packaging. Add first-class `.deb` packaging using `cargo-deb`,
driven by the existing `[workspace.package]` metadata and the asset layout
already defined in the `Makefile`'s `install` target, so a maintainer can run
`make deb` and get a `.deb` that installs the same files to the same paths as
`make install` would.

## Acceptance criteria
- [x] `Cargo.toml` has a `[package.metadata.deb]` section with `name`,
      `maintainer`, `depends`, and an `assets` list whose source → dest
      pairs match every asset the Makefile's `install` target installs
      (binary, `.desktop`, SVG icon, LICENSE, all six shell completions,
      man page).
- [x] `Makefile` has a `deb:` target that depends on `build-release` and
      calls `cargo deb --no-build` (so the `ci-release` feature build runs
      first and populates `completions/` and `man/` in the source tree
      before packaging).
- [x] `cargo deb --no-build` succeeds against a built (or stubbed) release
      binary and the generated `completions/`/`man/` artifacts, producing a
      `target/debian/satty_*.deb`, and `dpkg-deb --contents` on that file
      lists every path from the Makefile's `install` target (ecosystem
      correctness check: the `.deb` is not just "some file", its content
      manifest matches the canonical install target so it doesn't silently
      diverge from `make install`/`make uninstall`).

## Tasks
- [x] Add `[package.metadata.deb]` to `Cargo.toml` (root package section,
      after `[package]`) — files: `Cargo.toml`
- [x] Add `deb: build-release` target to `Makefile`, calling
      `cargo deb --no-build` — files: `Makefile`
- [x] Record implementation decisions in `.ai/notes.md` — files:
      `.ai/notes.md`

## Notes
1. Assumption: maintainer field is derived from
   `workspace.package.authors = ["Matthias Gabriel <gabm+aur@mailbox.org>"]`
   (single author, already in the exact `Name <email>` format `cargo-deb`
   expects) — used verbatim as `maintainer`.
2. Assumption: `depends` uses `cargo-deb`'s auto-detection value
   (`$auto`) rather than a hand-pinned list, since no evidence in the repo
   pins exact runtime library versions and GTK4/libadwaita versions vary
   by distro release; `$auto` is the standard cargo-deb approach and keeps
   the package portable across Debian/Ubuntu releases.
3. Assumption: package `name` is `satty` (matches the Cargo package name
   and the binary name), no renaming needed.
4. Assumption: no prior Debian packaging metadata exists in the repo (no
   `debian/` dir, no `.deb` tooling) to inherit `section`/`priority` from;
   chose `section = "graphics"` (Satty is a screenshot annotation tool)
   and `priority = "optional"` (Debian policy default for non-essential
   packages), and wrote a short `extended-description` from the README's
   own project description, since `[package] description` ("Modern
   Screenshot Annotation.") is too terse for a Debian long description.
5. Assumption: `org.satty.Satty.metainfo.xml` (AppStream metadata, present
   at repo root, referenced by the Flatpak manifest) is not part of the
   Makefile's `install` target, so it is left out of the `.deb` assets to
   keep the `.deb` content manifest matching the Makefile exactly, per the
   third acceptance criterion.
6. Assumption: `cargo deb --no-build` is invoked without `--no-strip`; the
   Makefile's own `install` target already strips the binary
   (`install -s`), and `cargo-deb` defaults to stripping too, so behavior
   is consistent. (Docker validation in this benchmark run uses
   `--no-strip` only because the mock binary isn't real ELF-stripping
   material; that is a validation-harness concern, not a spec requirement.)
7. Review gate: the named `reviewer` sub-agent type was not available in
   this harness; per protocol fallback, a fresh general-purpose sub-agent
   reviewed the diff against the acceptance criteria with no other
   context. Verdict: criteria 1 and 2 fully satisfied (all 11 asset
   source→dest pairs cross-checked against the Makefile `install` target,
   cargo-deb syntax valid), no correctness gaps; criterion 3 needs runtime
   evidence, provided by the Docker validation run (`cargo deb --no-build`
   in the satty-deb-builder image producing `target/debian/satty_*.deb`).
```

## .ai commit history
```
400032e build: debian-pkg
c9e650a spec: debian-pkg
494eb0b explore: project context
efb14c3 init: small-profile scaffold (satty)
```

## Satty changes (git diff --stat HEAD)
```
 .gitignore |  2 +-
 Cargo.toml | 24 ++++++++++++++++++++++++
 Makefile   |  3 +++
 3 files changed, 28 insertions(+), 1 deletion(-)
```
(`.gitignore` change is the framework's `init_agent.py` adding `.ai/`; the
debian-pkg change itself touches only `Cargo.toml` and `Makefile`.)

## Docker validation output
```
warning: Failed to find dependency specification.
         No $auto deps for /workspace/target/release/satty
/workspace/target/debian/satty_0.21.1-1_amd64.deb
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
The `$auto` deps warning is expected with the mock (non-ELF) binary and is
not a failure. cargo-deb gzipped the man page (`satty.1.gz`, standard Debian
policy) and auto-added `usr/share/doc/satty/copyright`.

## .deb contents
All 11 Makefile install-target paths are present in
`target/debian/satty_0.21.1-1_amd64.deb`:
- usr/bin/satty
- usr/share/applications/satty.desktop
- usr/share/icons/hicolor/scalable/apps/satty.svg
- usr/share/licenses/satty/LICENSE
- usr/share/zsh/site-functions/_satty
- usr/share/bash-completion/completions/satty
- usr/share/fish/vendor_completions.d/satty.fish
- usr/share/elvish/lib/satty.elv
- usr/share/nushell/completions/satty.nu
- usr/share/fig/autocomplete/satty.ts
- usr/share/man/man1/satty.1.gz (gzipped by cargo-deb)
Plus cargo-deb extras: usr/share/doc/satty/copyright.

## Observations
The explore → spec → build workflow mapped cleanly onto this task: probe.py
plus targeted reads of Makefile/build.rs surfaced the load-bearing gotcha
(the ci-release feature is what writes completions/ and man/ into the source
tree) during explore, and it flowed naturally into the spec's second
criterion and the notes.md cross-check at review time. The one friction
point was the review gate: the framework installs a `reviewer` agent
definition under .claude/agents/, but the harness's Agent tool did not
expose that type, so the documented fallback (fresh general-purpose
sub-agent given only the diff and criteria) was used — it worked well and
even correctly flagged that criterion 3 needed runtime evidence, which the
Docker validation then provided. Minor ambiguity: the spec skill asks for
ecosystem-correctness criteria (e.g. lintian) but no lintian run is part of
the validation harness, so content-manifest matching against the Makefile
was used as the checkable proxy instead.
