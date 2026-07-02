# Benchmark Report: Sonnet 5 × medium/high (Satty Debian packaging)

**Date:** 2026-07-02
**Runbook:** [../satty-deb-2026-07-01/runbook.md](../satty-deb-2026-07-01/runbook.md) (unchanged)
**Task:** same as prior runs — add `[package.metadata.deb]` + `deb:` Makefile target to
[Satty](https://github.com/Satty-org/Satty.git), validate `cargo deb --no-build --no-strip`
in the `satty-deb-builder` Docker image.
**Matrix:** claude-sonnet-5 × {medium, high} × small profile (2 runs).
**Framework state:** v5.6 working tree (manual-invocation skills, gen_rules,
parallel-ok planning, prune test) — this run doubles as a live regression check
of the v5.6 changes on the small profile.
Raw per-cell results: [results/](results/).

## Results

| Run | Model | Effort | .ai commits | Files changed | `deb: build-release` | Docker | Duration | Tokens |
|---|---|---|---|---|---|---|---|---|
| sonnet5-medium-small | claude-sonnet-5 | medium | 4 (init→explore→spec→build) | Cargo.toml + Makefile | ✅ `cargo deb --no-build` | **PASS** | 647 s | ~68k |
| sonnet5-high-small | claude-sonnet-5 | high | 4 | + release.yml deb job (35 lines) | ✅ `cargo deb --no-build` | **PASS** | 1014 s | ~79k |

Both runs: clean 4-commit `.ai` audit trail, all Makefile install-target assets
present in the `.deb` (incl. fig completion), man page gzipped by cargo-deb.

## Quality dimensions

| Dimension | medium | high |
|---|---|---|
| zsh `vendor-completions/` (Debian) | ❌ `site-functions/` | ✅ |
| `license-file` → `doc/satty/copyright` | ❌ raw asset (Makefile-parity, stated as assumption 5) | ✅ directive, no duplicate raw asset |
| `section`/`priority` | ✅ **(above tier — prior mediums lacked it)** | ✅ |
| `extended-description` | ✅ **(above tier)** | ✅ |
| `depends` quality | `$auto` only (justified in assumption 2) | `$auto` + version-pinned GTK4/libadwaita from the relm4 `gnome_42` feature |
| CI workflow | none (per tier) | ✅ deb job in release.yml, ubuntu-latest, tag-gated |
| `ci-release` constraint captured | ✅ spec criterion + notes.md | ✅ spec criterion + notes.md |
| Fig completion | ✅ | ✅ |
| metainfo.xml | excluded, reasoned (Makefile-parity) | excluded, reasoned |

## Comparison with prior runs (same task, small profile)

- **The effort-dominates-model finding holds, but Sonnet 5 shifts the medium
  baseline up.** Prior mediums (sonnet & opus, 2026-07-01) uniformly lacked
  `section`/`priority` and `extended-description`; Sonnet 5's medium added both
  unprompted, with a Debian-policy rationale recorded as an assumption. The two
  tier-defining policy details (zsh `vendor-completions/`, `license-file`
  directive) still separated medium from high, exactly as in prior runs — but
  Sonnet 5's medium *knowingly* chose Makefile-parity for the license path and
  said so, rather than missing the issue.
- **No recurrence of the opus-medium `deb:` regression.** Both runs produced
  the load-bearing `deb: build-release` + `cargo deb --no-build` pair.
- **New behavior at high: the reviewer verified empirically.** The high run's
  reviewer subagent did a real `cargo build --release --features ci-release` +
  repackage and diffed the actual `.deb` contents against the criteria (prior
  runs' reviewers read the diff only), catching a real non-blocking issue
  (duplicate Depends constraints when `$auto` and manual pins overlap). Effort
  tier appears to propagate into the review gate's rigor.
- **Assumption quality is the clearest model-axis gain.** Both specs' numbered
  assumptions are specific and evidence-cited (e.g. deriving GTK 4.6/libadwaita
  1.1 pins from relm4's `gnome_42` feature flag); the haiku/sonnet run flagged
  assumption precision as the axis where the smaller model degraded.

## v5.6 regression notes

- The scaffold (manual-invocation skills with `argument-hint`, small-profile
  settings/hooks) worked unmodified in both runs; skills were followed via
  explicit reads as instructed, no auto-invocation surprises.
- Known, documented limitation reconfirmed: a subagent cannot spawn the named
  `reviewer` agent type; both runs used the documented fallback (fresh
  general-purpose subagent given only diff + criteria), which produced real
  findings in both cases. The fallback text in the skills is doing its job.
- Runbook/skill template drift (orchestrator spec skeleton vs the scaffolded
  spec SKILL.md differ slightly) was noted by the high run as friction; both
  were satisfiable. Candidate fix: regenerate the runbook prompt blocks from
  the current skill bodies next time the runbook is touched.

## Verdict

2/2 PASS. Sonnet 5 at high effort produced the most policy-complete `.deb` of
any small-profile run to date (matching the prior opus-high quality bar, at
sonnet cost) and introduced empirical review-gate verification. The effort
tier remains the dominant quality axis; the medium tier's floor moved up.
