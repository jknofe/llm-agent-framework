---
id: nextrelease-typo
title: Release leaves a NEXTRELEASE placeholder in the README
type: bug
status: planned
created: 2026-11-08
updated: 2026-11-08
---
## Goal
After a release, the README still shows a `NEXTRELEASE` placeholder for the pixelate entry. Find the cause and fix it, docs and release text only.

## Done when
- [ ] Cause stated in Findings with file:line evidence.
- [ ] A reproduction fails before the fix and passes after (for example the release replacement run on a copy of README.md, then a grep).
- [ ] Fixed without changing any Rust source.

## Steps
- [ ] H1: the placeholder in README.md is spelled differently from what release.nu replaces - check: grep NEXTRE README.md, release.nu
- [ ] Reproduce on a copy, fix, rerun the reproduction - where: README.md

## Findings

## Outcome

## Notes
No Rust toolchain here; cargo-based criteria waived by the user. Leave host changes uncommitted.

## Tracker
none: the user stated there is no tracker issue.
