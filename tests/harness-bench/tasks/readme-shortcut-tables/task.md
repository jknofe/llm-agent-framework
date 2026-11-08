---
id: readme-shortcut-tables
title: Shortcut lists in the README as tables
type: change
status: planned
created: 2026-11-08
updated: 2026-11-08
---
## Goal
Turn the two shortcut lists under `### Shortcuts` in README.md, `#### General` and `#### Tool Selection Shortcuts (configurable)`, into Markdown tables with the columns Key, Action and Config action. Config action is the action name used under `[keybinds]` in config.toml as parsed in src/keybindings.rs, or `-` when the shortcut is not configurable.

## Done when
- [ ] Both lists are tables; every entry of both lists is kept, with its `<sup>` version tags.
- [ ] Every Config action value exists in src/keybindings.rs (file:line in Findings), or is `-`.
- [ ] No other README section and no source file changes.

## Steps
- [ ] Map each shortcut to its action name in src/keybindings.rs - where: src/keybindings.rs
- [ ] Rewrite the General list as a table - where: README.md
- [ ] Rewrite the Tool Selection list as a table - where: README.md
- [ ] Check every entry and tag survived against the original list - where: README.md

## Findings

## Outcome

## Notes
Docs only. No Rust toolchain; cargo-based criteria waived. Leave host changes uncommitted.

## Tracker
none: the user stated there is no tracker issue.
