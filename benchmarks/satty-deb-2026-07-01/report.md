# Benchmark Report: llm-agent-framework on Satty
**Date:** 2026-07-01  
**Task:** Add Debian packaging to [Satty](https://github.com/Satty-org/Satty.git) (`[package.metadata.deb]` + Makefile `deb:` target)  
**Matrix:** 2 models × 2 effort levels × 2 profiles = **8 runs**  
**Validation:** `cargo deb --no-build --no-strip` inside `ubuntu:latest` Docker  
**Runbook:** [runbook.md](runbook.md)

---

## Matrix and Results

| Run ID | Model | Effort | Profile | .ai commits | Files changed | `.deb` built | Docker |
|---|---|---|---|---|---|---|---|
| sonnet-medium-small | claude-sonnet-latest | medium | small | 4 (init→explore→spec→build) | Cargo.toml + Makefile | ✅ | **PASS** |
| opus-medium-small | claude-opus-4-8 | medium | small | 4 | Cargo.toml + Makefile | ✅ | **PASS** |
| sonnet-high-small | claude-sonnet-latest | high | small | 4 | +release.yml | ✅ | **PASS** |
| opus-high-small | claude-opus-4-8 | high | small | 4 | +release.yml | ✅ | **PASS** |
| sonnet-medium-large | claude-sonnet-latest | medium | large | 4 (init→explore→ticket→implement) | Cargo.toml + Makefile | ✅ | **PASS** |
| opus-medium-large | claude-opus-4-8 | medium | large | 5 | Cargo.toml + Makefile | ✅ | **PASS** |
| sonnet-high-large | claude-sonnet-latest | high | large | 5 (…→plan→implement) | +release.yml | ✅ | **PASS** |
| opus-high-large | claude-opus-4-8 | high | large | 5 | +release.yml | ✅ | **PASS** |

All 8 agents produced a valid `satty_0.21.1-1_arm64.deb` verified by `dpkg-deb --contents`.

---

## What Each Run Produced

### .deb Package Contents

| Asset | med-small | high-small | med-large | high-large |
|---|---|---|---|---|
| `usr/bin/satty` | ✅ both | ✅ both | ✅ both | ✅ both |
| `.desktop` / SVG icon | ✅ | ✅ | ✅ | ✅ |
| Bash / Fish / Elvish / Nushell | ✅ | ✅ | ✅ | ✅ |
| Fig completion | ❌ sonnet, ✅ opus | ✅ | ✅ | ✅ |
| Man page (auto-gzipped) | ✅ | ✅ | ✅ | ✅ |
| zsh `vendor-completions/` (Debian) | ❌ | ✅ | ❌ | ✅ |
| `license-file` → `doc/satty/copyright` | ❌ raw asset | ✅ | ❌ or raw | ✅ |
| `extended-description` | ❌ | ✅ | ❌ | ✅ |
| `metainfo.xml` (AppStream) | ❌ | ❌ sonnet / ✅ opus | ❌ | ❌ sonnet / ✅ opus |
| CI `deb` workflow added | ❌ | ✅ (opus: multi-arch) | ❌ | ✅ |

### Makefile `deb:` Target Correctness

| Run | `build-release` dep | Invocation | Verdict |
|---|---|---|---|
| sonnet-medium-small | ✅ | `cargo deb --no-build` | correct |
| opus-medium-small | ❌ | `cargo deb` | **broken** — rebuilds without `ci-release`; completions/man missing |
| sonnet/opus-high-small | ✅ | `cargo deb --no-build` | correct |
| all large runs | ✅ | `cargo deb --no-build` | correct |

`ci-release` is load-bearing: `build.rs` only writes `completions/` and `man/satty.1` into the source tree under that feature. Any `deb:` target that doesn't depend on `build-release` (which uses `--features ci-release`) silently packages an empty completions directory.

---

## Key Findings

### 1. Effort level is the decisive quality axis

High effort consistently added Debian-correct details that medium missed:

| Detail | medium | high |
|---|---|---|
| zsh path | `site-functions/` (wrong for Debian) | `vendor-completions/` ✅ |
| License handling | raw asset at Arch path | `license-file` directive → correct `copyright` ✅ |
| `extended-description` | missing | present ✅ |
| CI integration | none | deb job added ✅ |
| Dep version pins | none | with version minimums ✅ |

These are real correctness issues (`lintian` would flag the zsh path; Arch-style license path is non-policy). High effort is recommended for packaging tasks.

### 2. Opus is more insightful; Sonnet is leaner

At medium effort: **opus** explicitly identified the `ci-release` load-bearing constraint and explained `$auto` vs explicit-deps tradeoff. **Sonnet** missed `ci-release` but was saved by the Makefile dependency chain.

At high effort: both models produced production-quality output. Opus added `metainfo.xml` (AppStream compliance), multi-arch CI matrix, and version-pinned deps with cited minimums. Sonnet produced cleaner, more concise CI YAML that integrated better with the existing release.yml job structure.

### 3. Small profile is the right fit for this task size

Satty is ~7k LOC. The small profile (explore→spec→build, `notes.md` + per-change `spec.md`) completed in a single session. The large profile (7 KB nodes + ticket pipeline) produced richer planning artifacts (self-contained task files with test skeletons) but the KB overhead was not recovered for a 2-file change. Large profile advantage shows on multi-file refactors with complex domain context.

### 4. Large profile explore consumes a full session

In the first round, all 4 large-profile agents hit session limits during the explore+KB-fill phase before reaching implementation. The fix: treat explore and implement as separate sessions (or use focused resume prompts). The framework's `read-first` pointer in `plan.md` and `.ai/.current` cursor are designed for exactly this — starting implementation in a fresh session.

### 5. Autonomous mode worked well

All 8 agents resolved Q&A from code evidence and recorded numbered assumptions in spec.md / ticket.md. The assumption quality correlated with effort level: medium-effort assumptions were terse ("use $auto"), high-effort assumptions cited sources ("relm4's gnome_42 feature requires GTK 4.6, libadwaita 1.2 minimum").

---

## Best Configuration for Packaging Tasks

**Recommended:** `opus + high + small`
- All Debian policy details correct
- Most thorough assumptions documented
- Smallest framework overhead for this task size
- CI integration included automatically

**Minimum viable:** `sonnet + medium + small`
- Functional `.deb` produced
- Missing some Debian policy details
- Good for a first draft, expect a follow-up pass for policy compliance

---

## Framework Observations

- `probe.py` is essential: the deterministic repo inventory bootstrapped all agents correctly without re-derivation of build commands, module layout, or asset types.
- The spec/ticket `Notes` section (autonomous assumptions) is the most valuable output for traceability — it captures the non-obvious decisions that future developers would otherwise have to rediscover.
- The reviewer subagent was unavailable (agents are themselves subagents); self-reviews functioned as a substitute and caught the broken Makefile in opus-medium-small's first draft.
- The `.ai` commit sequence (`init → explore → spec/ticket → [plan] → build/implement`) provides a clean audit trail of the agent's work separate from the host repo history.
