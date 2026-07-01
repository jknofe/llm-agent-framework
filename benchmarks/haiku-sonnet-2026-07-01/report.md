# Benchmark Report: llm-agent-framework on Satty (Haiku vs Sonnet)

**Date:** 2026-07-01
**Task:** Add Debian packaging to [Satty](https://github.com/Satty-org/Satty.git) (`[package.metadata.deb]` + Makefile `deb:` target)
**Matrix:** 2 models × 2 effort levels × 1 profile = **4 runs** (all small profile)
**Validation:** `cargo deb --no-build --no-strip` inside the `satty-deb-builder` image (Ubuntu + cargo-deb)
**Runbook:** [../satty-deb-2026-07-01/runbook.md](../satty-deb-2026-07-01/runbook.md) (small profile)
**Raw results:** [results/](results/)

This is a follow-up to the [2026-07-01 opus/sonnet run](../satty-deb-2026-07-01/report.md). Same task
and validation, but it swaps the model axis to **haiku vs sonnet** and the effort axis to **low vs
medium** (the prior run used medium vs high). It answers: how far down the model/effort scale can you
go and still get a correct `.deb`?

---

## New effort tier: `low`

The reference runbook defines only `medium` and `high`. This run introduces a **`low`** (minimal) tier:

- **Explore:** read only `probe.py` output + `Cargo.toml` + `Makefile` (skip README, workflows, `src/`).
- **Spec:** terse — 2-3 acceptance criteria, one-line assumptions.
- **Build:** implement `[package.metadata.deb]` + `deb:` target directly. **No** CI workflow, `section`/
  `priority`, `extended-description`, `license-file` directive, `vendor-completions` zsh path, or
  version-pinned depends. `$auto` depends is fine.
- **Invariant kept at all tiers:** `deb:` must depend on `build-release` and call `cargo deb --no-build`
  (the load-bearing `ci-release` constraint — see prior report §Makefile Correctness).

`medium` is unchanged from the runbook (efficient; decide from evidence; policy extras optional; no CI).

---

## Matrix and Results

| Run ID | Model | Effort | .ai commits | Files changed | `.deb` built | Docker | Wall time | Tool calls |
|---|---|---|---|---|---|---|---|---|
| haiku-low-small | claude-haiku-4-5 | low | 4 (init→explore→spec→build) | Cargo.toml + Makefile | ✅ | **PASS** | 534s | 40 |
| haiku-medium-small | claude-haiku-4-5 | medium | 4 | Cargo.toml + Makefile | ✅ | **PASS** | 279s | 41 |
| sonnet-low-small | claude-sonnet-4-6 | low | 4 | Cargo.toml + Makefile | ✅ | **PASS** | 179s | 28 |
| sonnet-medium-small | claude-sonnet-4-6 | medium | 4 | Cargo.toml + Makefile | ✅ | **PASS** | 196s | 39 |

All four produced a valid `satty_0.21.1-1_arm64.deb` verified by `dpkg-deb --contents`. Every run
completed the full `init → explore → spec → build` commit sequence in a single session.

---

## `.deb` Contents and Debian-Policy Quality

Every run shipped the full asset set — binary, `.desktop`, SVG icon, **all six** completions
(bash/zsh/fish/elvish/nushell/**fig**), and the auto-gzipped man page. The differences are in the
Debian-correctness details:

| Dimension | haiku-low | haiku-medium | sonnet-low | sonnet-medium |
|---|---|---|---|---|
| Fig completion | ✅ | ✅ | ✅ | ✅ |
| zsh path | `site-functions/` | `site-functions/` | `site-functions/` | `site-functions/` |
| `depends` | `$auto` | `libgtk-4-1, libadwaita-1-0, libssl3` | `$auto` | `libgtk-4-1, libadwaita-1-0` |
| Debian dep names correct | n/a (`$auto`) | ✅ | n/a (`$auto`) | ✅ |
| License handling | raw asset → `usr/share/licenses/satty/LICENSE` (Arch path) | `usr/share/doc/satty/LICENSE` + auto `copyright` (redundant) | raw asset → `usr/share/licenses/satty/LICENSE` (Arch path) | `LICENSE` → `usr/share/doc/satty/copyright` (Debian-correct, single file) |
| `section`/`priority` | ❌ | ✅ `graphics` / `optional` | ❌ | ❌ |
| Cites linter (lintian) | in notes (extended-desc) | ❌ | ❌ | ✅ spec + notes (`no-copyright-file`) |

**No run used the Debian `vendor-completions/` zsh path.** `low` forbids it; `medium` makes it optional
and neither medium run opted in. So both medium packages would still draw a `lintian` note on the zsh
path — the one Debian detail that consistently needs `high` effort (confirmed by the prior run, where
only high-effort runs used `vendor-completions/`).

---

## Key Findings

### 1. Effort is still the dominant axis; the `low` tier behaves as designed

Both `low` runs (regardless of model) converged on the same minimal shape: `$auto` depends, LICENSE as
a raw asset at the Arch path, no `section`/`priority`, no CI. Both `medium` runs added
Debian-correct dependency names and moved the license toward `doc/`. The effort tier, not the model,
predicted the bulk of the output. This matches finding #1 of the prior report.

### 2. The model axis is real but *diverges in direction*, not just quality

At `medium`, haiku and sonnet did not rank cleanly — they made different Debian-correctness choices:

- **haiku-medium** was the more *maximal* packager: it added `section = "graphics"` and
  `priority = "optional"` (which even sonnet-medium omitted) and an extra `libssl3` dependency. But it
  shipped the license twice — a raw `doc/satty/LICENSE` asset alongside cargo-deb's auto-generated
  `doc/satty/copyright` (a `lintian: extra-license-file`-class redundancy).
- **sonnet-medium** was the more *precise* packager: it mapped `LICENSE` directly to the canonical
  `usr/share/doc/satty/copyright`, giving a single correct copyright file, and explicitly cited
  `lintian`'s `no-copyright-file` check in both its spec and notes. Its depends were minimal and
  correct (`libgtk-4-1, libadwaita-1-0`), and it used the more readable inline-table asset syntax.

Net: **sonnet-medium is the cleanest package; haiku-medium is the most feature-complete but slightly
redundant.** Neither is strictly better — a useful reminder that "smaller model" degrades along
specific axes (precision, dedup) rather than uniformly.

### 3. Haiku is materially slower and churnier per tier

Same-tier wall-clock and tool-call counts favor sonnet decisively:

| Tier | haiku | sonnet | haiku slowdown |
|---|---|---|---|
| low | 534s / 40 calls | 179s / 28 calls | 3.0× |
| medium | 279s / 41 calls | 196s / 39 calls | 1.4× |

Token counts were comparable across all four (31k–43k), so the cost gap is dominated by wall-clock and
tool churn, not context. The standout is **haiku-low — the slowest run of the four despite being the
leanest brief** (40 tool calls for a "minimal" task vs sonnet-low's 28). The cheapest model did not
produce the cheapest run in latency terms.

### 4. The prior benchmark's framework fixes held

Failure modes fixed after the previous run did not recur:

- **`deb: build-release` invariant:** all four respected it (the prior run's opus-medium-small shipped a
  broken `cargo deb` without the dependency). The load-bearing-constraint note + review cross-check
  (commit `2f8343a`) is doing its job.
- **Fig completion:** all four included it (prior sonnet-medium missed it).
- **Ecosystem-correctness criteria** (commit `5f8ec4f`): lintian awareness surfaced even at `low`
  (haiku-low's notes flag the missing extended-description warning), and sonnet-medium's spec names the
  exact `no-copyright-file` check — the intended effect of requiring linter/policy criteria in the spec.

---

## Recommendations

| Goal | Config | Rationale |
|---|---|---|
| **Fastest functional `.deb` draft** | `sonnet + low` | 179s, correct build, all assets, `$auto` deps. Expect a policy pass later (Arch license path, zsh `site-functions`). |
| **Best single-pass package at this tier band** | `sonnet + medium` | Correct `copyright`, correct minimal deps, cites lintian. Cleanest of the four. |
| **If you want section/priority auto-added** | `haiku + medium` | More Debian metadata out of the box, but dedupe the license and drop `libssl3`. |
| **Avoid** | `haiku + low` for latency-sensitive runs | 3× sonnet's wall time for an equivalent minimal result. |

For a fully `lintian`-clean package (correct `vendor-completions/` zsh path, `extended-description`),
`high` effort is still required regardless of model — see the [prior report](../satty-deb-2026-07-01/report.md).

---

## Framework Observations

- The `low` tier is a useful addition: it reliably produces an installable package with the least
  overhead and cleanly separates "make it work" from "make it policy-clean." Worth folding the tier
  definition into the runbook's effort guidance.
- No new framework defects surfaced. The explore→spec→build sequence, `probe.py` bootstrap, and
  self-review fallback (reviewer subagent unavailable to sub-agents) all functioned across all four.
- The spec `Notes` section again carried the most decision value: sonnet-medium's assumption #3
  (copyright vs Arch license path, with the lintian rationale) is exactly the kind of traceable,
  non-obvious call the section is meant to capture.
