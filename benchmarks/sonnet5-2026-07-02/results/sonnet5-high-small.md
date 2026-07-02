# Benchmark Results: sonnet5-high-small

## Configuration
| Field | Value |
|---|---|
| Run ID | sonnet5-high-small |
| Profile | small |
| Model | claude-sonnet-5 |
| Effort | high |
| Start | 2026-07-02T08:39:23 |
| End | 2026-07-02T08:56:17 |
| Duration | 1014 s |
| Docker status | PASS |

## Spec produced

    ---
    id: debian-pkg
    title: add debian format to satty build
    status: done
    created: 2026-07-02
    ---
    
    ## Goal
    
    Satty currently ships tarball releases (x86_64/aarch64) and a Flatpak, but no
    native Debian/Ubuntu package. Add `cargo-deb` metadata to `Cargo.toml` and a
    `make deb` target so a `.deb` can be produced from a release build,
    installing the same files at the same paths as `make install` (binary,
    desktop entry, icon, license, shell completions, man page), adjusted to
    Debian filesystem policy where it differs from the Makefile's
    `/usr/local`-oriented layout (notably zsh completions). This lets users on
    Debian/Ubuntu-derived distros install and remove Satty via `dpkg`/`apt`
    with correct dependency and metadata declarations, and gives CI a path to
    publish a `.deb` release asset alongside the existing tarballs and Flatpak.
    
    ## Acceptance criteria
    
    - [x] `Cargo.toml` has a `[package.metadata.deb]` table (on the root
          `satty` package, not the `cli` workspace member) with `name`,
          `maintainer` (sourced from `workspace.package.authors`), `depends`,
          and `assets` entries that reproduce every `install` line in the
          Makefile's `install:` target (binary, `.desktop`, SVG icon, LICENSE,
          all 6 shell completions, man page) at matching destination paths and
          modes.
    - [x] `section = "graphics"` and `priority = "optional"` are set.
    - [x] `extended-description` is present (multi-line, distinct from the
          short `description` inherited from `workspace.package.description`).
    - [x] License is declared via `license-file = ["LICENSE", "0"]` (a
          `cargo-deb` directive that generates `usr/share/doc/satty/copyright`),
          not by also listing `LICENSE` a second time as a raw `assets` entry
          pointing at `usr/share/licenses/satty/LICENSE` (that would duplicate
          Makefile behavior in a way `cargo-deb`/lintian does not expect and
          trip a duplicate-license lintian tag).
    - [x] `depends` includes `$auto` (so `cargo-deb` inspects the built ELF
          binary for shared-library deps at package time) plus explicit,
          version-pinned entries for the GNOME platform libraries the app is
          built against (GTK4 via relm4's `gnome_42` feature, libadwaita), so
          the package cannot be installed against a too-old desktop stack even
          if `$auto` under-detects.
    - [x] zsh completion asset targets the Debian-policy path
          `usr/share/zsh/vendor-completions/_satty` (not the Makefile's Arch/
          local-oriented `usr/share/zsh/site-functions/_satty`).
    - [x] `Makefile` has a `deb:` target that depends on `build-release` (so
          the `ci-release` feature runs first and populates `completions/` and
          `man/` in the source tree, which `cargo-deb --no-build` reads) and
          runs `cargo deb --no-build`.
    - [x] A CI workflow can build the `.deb`: either a new job/step in
          `.github/workflows/release.yml` (x86_64 leg, since that's the leg
          with an apt/deb-compatible base) or a note in `.ai/notes.md` if
          wiring it into release.yml is out of scope for this change; either
          way `cargo-deb` must be installable in that CI environment.
    - [x] `cargo deb --no-build --no-strip` succeeds against a release build
          and produces `target/debian/satty_*.deb` containing all assets above
          at their declared paths (verified via `dpkg-deb --contents`).
    
    ## Tasks
    
    - [x] `Cargo.toml` — add `[package.metadata.deb]` under `[package]` (root
          crate section), including `name`, `maintainer`, `copyright`,
          `license-file`, `extended-description`, `section`, `priority`,
          `depends`, `assets` (binary + 8 non-binary assets from the Makefile
          install list, zsh path adjusted per criteria above).
    - [x] `Makefile` — add:
          ```
          deb: build-release
          	cargo deb --no-build
          ```
          placed near the existing `package:` target.
    - [x] `.github/workflows/release.yml` — add a `deb` job (or a step in the
          existing x86_64 release job) that installs `cargo-deb`
          (`cargo install cargo-deb` or a prebuilt-binary install action),
          runs `make deb`, and uploads `target/debian/*.deb` via
          `softprops/action-gh-release@v1` alongside the tarball/Flatpak
          assets.
    - [x] `.ai/notes.md` — record the cargo-deb dependency-pinning decision and
          the zsh path deviation from the Makefile as durable packaging
          knowledge.
    
    ## Notes
    
    Autonomous assumptions (no human available; resolved from repo evidence):
    
    1. **Maintainer**: use `workspace.package.authors[0]`, i.e.
       `"Matthias Gabriel <gabm+aur@mailbox.org>"`, as `maintainer`, matching
       every other packaging metadata field already sourced from
       `workspace.package` in `Cargo.toml`.
    2. **Package name**: `"satty"`, matching the binary name and existing
       Makefile/release artifact naming.
    3. **`section`/`priority`**: `graphics` / `optional` — Satty is a
       screenshot/image annotation GUI tool with no system-level implications,
       the standard Debian classification for comparable tools (e.g. `flameshot`
       ships as `section: graphics`).
    4. **Version-pinned depends**: relm4 is pulled in with the `gnome_42`
       feature flag, which in the relm4/gtk4-rs versioning convention denotes
       the platform library versions the bindings target (GTK 4.6+, libadwaita
       1.1+ per the gnome_42 profile). Pin `libgtk-4-1 (>= 4.6)` and
       `libadwaita-1-0 (>= 1.1)` in addition to `$auto`, since `$auto`
       detection against a *mock* binary (used for local/Docker validation of
       this change) will not find real linkage and could under-constrain; the
       explicit pins are a safety net for real builds too.
    5. **zsh completion path**: Debian policy (`zsh` package docs,
       `/usr/share/zsh/vendor-completions/`) differs from the Makefile's
       `site-functions` path, which targets Arch/local installs where zsh's
       `fpath` includes `site-functions` by default but not on Debian. Use the
       Debian-correct path for the `.deb` asset even though the Makefile itself
       is left unchanged (its `install`/`uninstall` targets remain valid for
       non-Debian manual installs).
    6. **CI scope**: added a `deb` job to `release.yml` gated on the same tag
       trigger as the rest of the release workflow, running on `ubuntu-latest`
       (a real Debian-family base, unlike the Fedora container used for the
       main x86_64 build) so `dpkg-deb`/`lintian`-compatible tooling is native;
       it rebuilds with `--features ci-release` rather than reusing artifacts
       from the matrix job, since GitHub Actions jobs don't share a filesystem
       without explicit artifact upload/download, which is out of scope here.
    7. **`license-file` offset**: `cargo-deb`'s `license-file = [path, N]`
       directive skips the first `N` lines of the file when embedding it into
       `usr/share/doc/<pkg>/copyright`; `0` skips nothing, appropriate since
       `LICENSE` (MPL-2.0 full text) has no throwaway header line to skip.
    8. **No `org.satty.Satty.metainfo.xml` asset**: not part of `make install`
       today (Flatpak-only), so excluded from `.deb` assets too, for
       Makefile-parity per the acceptance criteria's framing. Can be added
       later if AppStream metadata is desired for Debian's software centers.

## .ai commit history

```
4d3b8e6 build: debian-pkg
c39ab35 spec: debian-pkg
9cd96ad explore: project context
01c6910 init: small-profile scaffold (satty)
```

## Satty changes (git diff --stat HEAD)

```
 .github/workflows/release.yml | 35 +++++++++++++++++++++++++++++++++++
 .gitignore                    |  2 +-
 Cargo.toml                    | 27 +++++++++++++++++++++++++++
 Makefile                      |  3 +++
 4 files changed, 66 insertions(+), 1 deletion(-)
```

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
./usr/share/man/
./usr/share/man/man1/
./usr/share/man/man1/satty.1.gz
./usr/share/nushell/
./usr/share/nushell/completions/
./usr/share/nushell/completions/satty.nu
./usr/share/zsh/
./usr/share/zsh/vendor-completions/
./usr/share/zsh/vendor-completions/_satty
```

## .deb contents

Note: the Docker validation above ran against a mock ELF stub binary (hence the expected `$auto` warning). The reviewer subagent subsequently did a real `cargo build --release --features ci-release` + `cargo deb --no-build --no-strip` in the same tree, so the listing below reflects the final .deb with the real 6.2 MB binary and generated man page/completions — same paths, stronger evidence.

```
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/bash-completion/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/bash-completion/completions/
-rw-r--r-- 0/0            6207 2026-07-02 02:00 ./usr/share/bash-completion/completions/satty
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/zsh/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/zsh/vendor-completions/
-rw-r--r-- 0/0            6058 2026-07-02 02:00 ./usr/share/zsh/vendor-completions/_satty
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/applications/
-rw-r--r-- 0/0             313 2026-07-02 02:00 ./usr/share/applications/satty.desktop
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/elvish/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/elvish/lib/
-rw-r--r-- 0/0            5450 2026-07-02 02:00 ./usr/share/elvish/lib/satty.elv
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/fish/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/fish/vendor_completions.d/
-rw-r--r-- 0/0            5278 2026-07-02 02:00 ./usr/share/fish/vendor_completions.d/satty.fish
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/nushell/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/nushell/completions/
-rw-r--r-- 0/0            5695 2026-07-02 02:00 ./usr/share/nushell/completions/satty.nu
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/icons/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/icons/hicolor/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/icons/hicolor/scalable/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/icons/hicolor/scalable/apps/
-rw-r--r-- 0/0            3538 2026-07-02 02:00 ./usr/share/icons/hicolor/scalable/apps/satty.svg
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/fig/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/fig/autocomplete/
-rw-r--r-- 0/0            9513 2026-07-02 02:00 ./usr/share/fig/autocomplete/satty.ts
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/man/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/man/man1/
-rw-r--r-- 0/0            2404 2026-07-02 02:00 ./usr/share/man/man1/satty.1.gz
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/doc/
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/share/doc/satty/
-rw-r--r-- 0/0           16938 2026-07-02 02:00 ./usr/share/doc/satty/copyright
drwxr-xr-x 0/0               0 2026-07-02 02:00 ./usr/bin/
-rwxr-xr-x 0/0         6254664 2026-07-02 02:00 ./usr/bin/satty
```

## Observations

The small-profile workflow (explore -> spec -> build with a review gate) mapped cleanly onto this task: probe.py plus targeted reads of the Makefile, build.rs, and release.yml surfaced the one non-obvious constraint (completions/ and man/ only exist after a --features ci-release build), which then drove both the spec's `deb: build-release` criterion and the notes.md gotcha entry. The reviewer subagent went beyond a read-through — it actually built the crate and the .deb and verified contents, catching one real non-blocking issue (duplicate Depends constraints when `$auto` and the manual pins detect the same libraries), which was recorded in notes.md as an accepted trade-off. The only friction points were mechanical: the orchestrator-supplied spec skeleton and the framework's spec SKILL.md template differ slightly (both were satisfiable), and the mock-binary validation path means `$auto` dependency resolution is never exercised end-to-end outside real CI.
