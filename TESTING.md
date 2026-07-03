# Testing and Benchmarks

How to validate a change to this framework. Two layers: fast mechanical checks
(run on every change) and benchmark runs (run for behavior changes worth
shipping). There is no unit-test suite; the generator is a set of string
templates, so the tests are "does it render, does it run, does an agent behave".

## Layer 1: Mechanical checks (every change, <1 min)

1. **Syntax**
   ```bash
   python3 -c "import ast; ast.parse(open('init_agent.py').read())"
   ```
2. **Scaffold all four variants** into a throwaway dir (init writes to CWD;
   never scaffold into this repo root):
   ```bash
   d=$(mktemp -d)
   for size in small large; do for h in claude copilot; do
     mkdir -p "$d/$size-$h"
     ( cd "$d/$size-$h" && python3 /path/to/init_agent.py \
         --name t --description d --size $size --harness $h -y >/dev/null )
   done; done
   ```
3. **Grep the rendered output** for your template change in every affected
   variant. A change that only renders in one profile/harness is usually a bug.
4. **Referenced paths exist and run.** Any tool path a template mentions
   (e.g. `.ai/agent/tools/probe.py`) must exist in that profile's scaffold and
   exit 0. A dangling path in a template is a silent break.
5. **Re-init preservation:** scaffold, hand-edit a KB node / notes.md / the
   `GENERATED:project-context` section, re-run init, confirm the report says
   `preserved` and nothing reverted to a stub.
6. **Leakage sweep** (after changing normative text): grep the scaffolds for
   terms specific to any benchmark target (satty, debian, cargo deb, angular,
   sqlite-utils, bats, ros, nav2, navigation2, colcon, ...). Generated
   artifacts must stay ecosystem-neutral; named linters are allowed only as
   diverse example lists.

## Layer 2: Benchmark runs (behavior changes)

A benchmark run = spawn an autonomous agent on a real target repo, drive it
through the framework phases (init -> explore -> spec/ticket -> [plan] ->
build/implement), then gate the produced artifact deterministically in Docker.
Rule of thumb: a behavior change worth shipping is worth one benchmark cell
before and after.

**Run cells sequentially, one at a time** — never dispatch a multi-cell round
in parallel. Parallel cells burn the usage window several times faster and
strand each other on session limits (round 1's lesson). Wait for a cell's
results file + gate verdict before starting the next; if a cell stalls on a
limit, resume that same agent after the reset rather than launching a
duplicate. Details and cell order: the fixed runbook's Execution section.

All procedure lives in one self-contained, fully-pinned runbook:
[benchmarks/fixed-runbook.md](benchmarks/fixed-runbook.md). It defines the
7-cell cross-ecosystem set (Python, Shell, Rust, TS/Angular, C++/ROS 2) with
exact repo SHAs, seeds, scaffold commands, Docker images, deterministic gates,
the agent-prompt template, and the results format. The only inputs are MODEL and
EFFORT (tiers low/medium/high defined there).

### Which cell to use

- **Smoke (default for framework changes):** one small-profile cell,
  sonnet + medium — fixed-runbook cell 1 (`sh-refactor`, no package install,
  ~10-20 min) or cell 2 (`rust-package`). Exercises explore/spec/build, the
  review gate, and the Docker gate end to end.
- **Anti-overfitting / new normative text:** the Python/Shell cells (1, 3, 4),
  because they check ecosystem-correctness outside Rust/Debian (right linter
  named unprompted, refactor invariants, root-cause bugfixing).
- **Large-profile / KB changes:** a large-profile cell (the `ros-*` cells 5-6),
  because small-profile smoke never touches
  manifest/INDEX/kb-delta/drift-check machinery.

### Invariants every run must satisfy

- Clean `.ai` commit sequence for the profile
  (small: init -> explore -> spec -> build).
- PASS/FAIL decided only by the deterministic container gate, never by
  impressions; quality dimensions are recorded separately.
- Raw per-cell results preserved under `benchmarks/<run>/results/`
  (the `/tmp` working copies are ephemeral), plus a `report.md`.
- Findings feed back: a failure mode fixed in `init_agent.py` gets its commit
  hash cited in the report, and the next run confirms no regression.

## Prerequisites

- Docker daemon running; per-runbook images built once
  (`satty-deb-builder`, `bats-eco-builder`, `ros-nav-builder`).
- Network access to clone the target repos (pinned SHAs in the runbooks).
- Agent runs write to `/tmp/benchmark/{runs,results}/`.
