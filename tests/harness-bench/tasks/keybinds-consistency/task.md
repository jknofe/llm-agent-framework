---
id: keybinds-consistency
title: Keybind actions consistent across config, code and README
type: test
status: planned
created: 2026-11-08
updated: 2026-11-08
---
## Goal
Check that every action under `[keybinds]` in config.toml exists in src/keybindings.rs and is documented in README.md. Record each mismatch as a finding; fix nothing.

## Done when
- [ ] Every `[keybinds]` action has a result: in code yes/no, in README yes/no, with file:line.
- [ ] Each mismatch is a finding with evidence.
- [ ] No file outside `.ai` changed.

## Steps
- [ ] List the actions in config.toml [keybinds] - where: config.toml
- [ ] Check each against src/keybindings.rs - where: src/keybindings.rs
- [ ] Check each against README.md - where: README.md

## Findings

## Outcome

## Notes
Static checks only; no Rust toolchain, cargo-based criteria waived.

## Tracker
none: the user stated there is no tracker issue.
