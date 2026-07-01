# Benchmarks

Autonomous-agent benchmark runs of the `llm-agent-framework` on real target repos. Each run drives an
agent through the framework's phases (init → explore → spec/ticket → [plan] → build/implement) on a
concrete change, then validates the produced artifact in a container.

## Runs

| Run | Date | Target | Task | Matrix | Result |
|---|---|---|---|---|---|
| [satty-deb-2026-07-01](satty-deb-2026-07-01/report.md) | 2026-07-01 | [Satty](https://github.com/Satty-org/Satty.git) | Add Debian packaging (`[package.metadata.deb]` + `deb:` target) | opus/sonnet × medium/high × small/large (8 runs) | 8/8 built a valid `.deb` |
| [haiku-sonnet-2026-07-01](haiku-sonnet-2026-07-01/report.md) | 2026-07-01 | [Satty](https://github.com/Satty-org/Satty.git) | Same Debian-packaging task | haiku/sonnet × low/medium × small (4 runs) | 4/4 built a valid `.deb` |

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

## Adding a run

1. Copy the runbook's `## Configuration` block and fill it (model, effort, profile, target).
2. Spawn one agent per matrix cell with the appropriate agent-prompt section.
3. Collect each cell's results file, verify against the runbook's Evaluation Checklist.
4. Write a `report.md` under a new dated folder and add a row to the table above. Preserve raw
   per-cell results under `<run>/results/` (the working `/tmp` copies are ephemeral).
