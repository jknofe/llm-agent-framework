# Benchmarks

Autonomous-agent benchmark runs of the `llm-agent-framework` on real target repos. Each run drives an
agent through the framework's phases (init → explore → spec/ticket → [plan] → build/implement) on a
concrete change, then validates the produced artifact in a container.

## Runs

| Run | Date | Target | Task | Matrix | Result |
|---|---|---|---|---|---|
| [satty-deb-2026-07-01](satty-deb-2026-07-01/report.md) | 2026-07-01 | [Satty](https://github.com/Satty-org/Satty.git) | Add Debian packaging (`[package.metadata.deb]` + `deb:` target) | opus/sonnet × medium/high × small/large (8 runs) | 8/8 built a valid `.deb` |
| [haiku-sonnet-2026-07-01](haiku-sonnet-2026-07-01/report.md) | 2026-07-01 | [Satty](https://github.com/Satty-org/Satty.git) | Same Debian-packaging task | haiku/sonnet × low/medium × small (4 runs) | 4/4 built a valid `.deb` |
| [sonnet5-2026-07-02](sonnet5-2026-07-02/report.md) | 2026-07-02 | [Satty](https://github.com/Satty-org/Satty.git) | Same Debian-packaging task, on the v5.6 framework | sonnet-5 × medium/high × small (2 runs) | 2/2 built a valid `.deb`; high matched the opus-high policy bar |
| [ua-plan-2026-07-02](ua-plan-2026-07-02/report.md) | 2026-07-02 | [Understand-Anything](https://github.com/Egonex-AI/Understand-Anything.git) | Add Angular detection to the framework registry (`FrameworkConfig` + registration + test) | sonnet-5 × medium/high × large, **explore + plan only** (2 runs) | 2/2 produced schema-valid, implementable plans; effort axis held (breadth + assumption quality), no source touched |

## Planned

| Run | Purpose | Spec |
|---|---|---|
| two-register-ab | Validate CONCEPT.md §8 (plain normative docs + telegraphic KB content) against plain-only and telegraphic-only variants: escalation/re-plan rates, process fidelity, tokens | [two-register-ab/runbook.md](two-register-ab/runbook.md) |
| multi-eco | Empirical counterpart to the 2026-07-02 overfitting audit: 5 cells across Python (sqlite-utils), Shell (bats-core), C++/ROS (navigation) x bugfix/cross-file-feature/refactor task types, deterministic container gates, no packaging task | [multi-eco/runbook.md](multi-eco/runbook.md) |

## Shared runbook

Both runs use the small/large-profile procedure in
[satty-deb-2026-07-01/runbook.md](satty-deb-2026-07-01/runbook.md). It is a self-contained,
model/effort-agnostic template: fill the `## Configuration` block, copy the relevant agent-prompt
section, and spawn. Effort tiers `low`, `medium`, and `high` are defined there.

## What the runs measured

- **Correctness:** does `cargo deb --no-build --no-strip` produce an installable `.deb` inside Docker,
  with the full asset set (binary, `.desktop`, icon, all shell completions, man page, license)?
- **Ecosystem/policy quality:** zsh completion path (`vendor-completions/` vs `site-functions/`),
  license handling (`copyright` vs raw asset), `depends` correctness, `section`/`priority`, CI wiring.
- **Process:** clean `.ai` commit audit trail, autonomous assumption quality, self-review efficacy.

## Cross-run conclusions

- **Effort is the dominant quality axis.** Across both runs, the effort tier predicted more of the
  output than the model did. `low` yields a minimal installable artifact; policy-correct details
  (Debian `vendor-completions/` zsh path, `extended-description`, `license-file`) reliably need `high`.
- **Model choice degrades on specific axes, not uniformly.** At matched effort, a smaller model tends
  to lose precision (dedup, exact package names) and speed rather than failing outright — see the
  haiku-vs-sonnet divergence in the 2026-07-01 haiku/sonnet run.
- **The framework fixes from the first run held in the second.** The load-bearing `deb: build-release`
  invariant, fig-completion inclusion, and lintian-aware spec criteria (commits `2f8343a`, `5f8ec4f`)
  all carried through with no regressions.
- **A stronger model raises the effort tier's floor, not its ceiling.** Sonnet 5 at medium
  (2026-07-02) added policy details prior mediums missed (`section`/`priority`,
  `extended-description`) and stated its remaining deviations as explicit assumptions, but the
  tier-defining details (zsh `vendor-completions/`, `license-file`) still required high — the
  effort axis kept its shape. At high, the reviewer began verifying empirically (real build +
  `.deb` content diff), a new behavior.

## Adding a run

1. Copy the runbook's `## Configuration` block and fill it (model, effort, profile, target).
2. Spawn one agent per matrix cell with the appropriate agent-prompt section.
3. Collect each cell's results file, verify against the runbook's Evaluation Checklist.
4. Write a `report.md` under a new dated folder and add a row to the table above. Preserve raw
   per-cell results under `<run>/results/` (the working `/tmp` copies are ephemeral).
