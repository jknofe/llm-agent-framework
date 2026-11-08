---
id: readme-config-reference
title: Configuration reference table in the README
type: change
status: planned
created: 2026-11-08
updated: 2026-11-08
---
## Goal
Add `### Configuration reference` to README.md, right after the `### Configuration File` block: one Markdown table row per option in the `[general]` section of config.toml, with the columns Option, Default and Meaning. Default is the value config.toml sets; Meaning is one line taken from the comment above the option.

## Done when
- [ ] Every option set in `[general]` of config.toml has exactly one row; commented-out alternatives are not rows.
- [ ] Each Default matches the value in config.toml.
- [ ] No other README section and no source file changes.

## Steps
- [ ] List the `[general]` options with value and comment - where: config.toml
- [ ] Write the table - where: README.md
- [ ] Check the row count and every default against config.toml - where: README.md

## Findings

## Outcome

## Notes
Docs only. No Rust toolchain; cargo-based criteria waived. Leave host changes uncommitted.

## Tracker
none: the user stated there is no tracker issue.
