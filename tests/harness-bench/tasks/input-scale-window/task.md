---
id: input-scale-window
title: Why --input-scale inverts the window size (issue #689)
type: investigation
status: planned
created: 2026-11-08
updated: 2026-11-08
---
## Goal
Question: "Why does --input-scale have the inverse effect on the window size (issue #689)?"
Answer it with the cause in the code, so a fix can be decided.

## Done when
- [ ] Outcome answers the question; every claim cites file:line or command output.
- [ ] No code change.

## Steps
- [ ] H1: the window size computation uses input-scale in some direction - check: where the initial window size is set
- [ ] H2: the canvas zoom also uses input-scale - check: where the initial zoom is set
- [ ] H3: history shows when each use was introduced - check: git log -S input_scale

## Findings

## Outcome

## Notes
No Rust toolchain here; read the code, do not build. Cargo-based criteria waived by the user.

## Tracker
issue: #689
