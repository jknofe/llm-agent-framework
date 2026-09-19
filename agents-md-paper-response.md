# Response to "Evaluating AGENTS.md" (ETH Zurich / LogicStar, ICLR 2026 workshop)

Date: 2026-09-14. Framework at v5.26 (branch `feature/hermes-support`).
Source: `29_Evaluating_AGENTS_md_Are_Re.pdf` (Gloaguen, Muendler, Mueller,
Raychev, Vechev). Read in full, 20 pages including appendix.

Verdict up front: **the framework is not obsolete, but its founding
rationale is.** The paper invalidates the claim that a generated,
always-loaded project digest in AGENTS.md helps a coding agent. It does not
test the things the framework has since become: a workflow (spec, build,
review gate), a private memory across sessions, and a command set that is
the same on three harnesses. Those parts survive, but the framework's own
benchmarks show they have not been proven either. The proposal below cuts
what the paper falsified, moves what is unproven behind an experiment, and
leaves the harness axis untouched.

---

## 1. What the paper says

Setup: 4 agent/model pairs (Claude Code + Sonnet 4.5, Codex + GPT-5.2,
Codex + GPT-5.1 mini, Qwen Code + Qwen3-30B), two benchmarks (SWE-bench
Lite, 300 tasks; AGENTbench, 138 new tasks from 12 niche Python repos that
ship a developer-written context file). Three arms: no context file,
LLM-generated file (each agent's own `/init`), developer-written file.

Findings, all on one-shot single-session tasks:

| Claim | Number |
|---|---|
| LLM-generated context files change success rate | -0.5% (SWE-bench Lite), -2% (AGENTbench) |
| Developer-written files change success rate | +4% avg; Claude Code + Sonnet 4.5 loses ~2.5% |
| Both kinds raise steps and cost | +2.5 to +3.9 steps, +20% to +23% cost |
| Files help find relevant files faster | No. Steps to first PR-relevant file do not drop |
| Instructions in files are followed | Yes. `uv` used 1.6x per task when mentioned vs 0.01x when not |
| Files cause more testing, grep, reads, reasoning tokens | Yes, across all models (+14% to +22% reasoning tokens) |
| Stronger generator model makes better files | No. GPT-5.2-generated files: +2% on SWE-bench, -3% on AGENTbench |
| Codex vs Claude Code init prompt matters | No consistent difference |
| Files help when the repo has no docs | Yes. With all `.md` and `docs/` removed, LLM files give +2.7% and beat human files |
| Mean developer context file | 641 words, 9.7 sections |

Their recommendation: skip LLM-generated context files for now; keep
human-written ones to minimal requirements such as specific tooling to use.

Explicit limits the authors state: Python only; task resolution only, not
code quality or security; no multi-session or memory setting. Implicit
limits that matter here: no skills or slash commands, no hooks, no
sub-agent review, no workflow layer at all. The only variable is the file.

## 2. What the framework emits today (measured on a fresh scaffold)

| Artifact | Size | Loaded |
|---|---|---|
| `AGENTS.md` (protocol, workflows, layout, project-context stub) | 1007 words, ~1600 tokens before `/explore` fills it | every session |
| Project-context section after `/explore` | cap ~1500 tokens (purpose, stack, commands, conventions, module map, glossary) | every session |
| 7 skills | 3915 words total; `/build` 482, `/explore` 277, `/spec` 206 | on trigger |
| `reviewer` sub-agent | 224 words | on `/build` gate |
| `probe.py`, Stop hook, permission allowlist | code | on demand / claude only |

So the always-on payload after `/explore` is roughly 3000 tokens, of which
about half is protocol prose and half is an LLM-generated repository
overview. The paper's developer files average 641 words. The framework
ships something 2 to 3 times larger, and the larger half is exactly the
kind the paper found useless or harmful.

## 3. Feature-by-feature impact

### 3.1 Project-context digest (the `/explore` output): falsified

This is the direct hit. CONCEPT.md §6 calls AGENTS.md the "hot-tier
transport" and §9 item 5 lists it as a token-efficiency mechanism: load the
module map once so the agent does not rediscover it. The paper measured
that mechanism and it does not work. Every Sonnet-generated file contained
an overview; agents with overviews reached the relevant file no faster than
agents without. Worse, the digest is an LLM-written file, the arm the paper
found net negative, and on repos that have a README or `docs/` it is
redundant with documentation the agent would read anyway.

The framework's own numbers agree. Every one-shot pair in
`benchmarks/sonnet5-medium-small-2026-07-06/` passed on both arms while
the framework arm cost +84% to +403% more tokens. The framework predicted
the one-shot loss (§13) and staked the digest's value on the second session
(amortization). That test ran once, on haiku, and failed: the warm second
session cost +28% total, not less (`haiku-high-2026-07-04/baseline-comparison.md`).
The planned Sonnet 5 and large-repo re-runs (`amortization-playbook.md`)
were never executed.

Net: the digest has zero supporting evidence, two independent negative
results, and one open experiment.

### 3.2 Build, test, lint commands: confirmed as the part worth keeping

The paper's one positive recommendation, "minimal requirements such as
specific tooling", is what `probe.py` produces deterministically and what
`/explore` writes as the "highest priority" fields. The instruction-following
data (`uv`, `pytest`, repo tools used almost only when mentioned) says these
lines change behavior. Keep them, and keep them short.

### 3.3 Protocol prose in AGENTS.md: consistent with the paper's cost finding

The paper found that every instruction is followed and every instruction
adds steps. The AGENTS.md protocol is eight numbered rules, a notes-hub
splitting procedure, a compaction rule, and a task-cursor rule, all loaded
every turn including the one-line fixes the right-sizing rule says need no
ceremony. Most of it is only relevant inside `/spec` or `/build`, which the
harness already loads on demand. The framework has progressive disclosure
(CONCEPT.md §7) and does not use it for its own protocol.

### 3.4 Spec, review gate, `.ai` memory, Stop hook: not tested by the paper

These are workflow, not context. The paper is silent. The framework's own
evidence is split: the haiku round showed a real reliability gain (the only
valid bugfix that day came from the framework arm; the baseline confabulated
a fix), the Sonnet 5 round showed none (8/8 pass both arms). The paper's
Figure 3 adds a weak signal in the same direction: Claude Code + Sonnet 4.5
is the one agent that loses even with human-written files. Strong model in
its native harness is the setting least helped by added structure.

These features are defensible for weaker models, autonomous runs (`/goal`),
and multi-session work. They are not defensible as a default tax on every
one-line change. That is already the right-sizing rule; the problem is the
protocol text that carries the tax anyway.

### 3.5 The harness axis (claude, copilot, hermes): unaffected

Two readings of "does the harness still make sense":

- **The framework as a harness.** It is not one. Claude Code, Codex, Copilot
  and Hermes are the harnesses; the framework is a context file plus a
  command set plus memory. The paper evaluates each model inside its own
  harness and finds harness-specific init prompts make no consistent
  difference. So the harness-neutral design (one skill body, harness
  fragments only for mechanics; CONCEPT.md §27, §30) is the right shape and
  needs no change.
- **The harness axis in the generator.** It costs almost nothing (fragment
  files, frontmatter, file paths) and it is the only reason the commands
  exist on copilot and hermes at all. The claude-only extras (Stop hook,
  reviewer, allowlist) are exactly the mechanical enforcement the paper
  cannot speak to. Keep the axis. The pending hermes work in
  `add-hermes-support-to-do.md` is orthogonal to this paper.

### 3.6 Token efficiency as the headline goal: retire it

README line one says "token-optimized". CONCEPT.md §9 lists eleven
token-efficiency mechanisms. Every measurement, the paper's and the
framework's, shows the scaffold costs more tokens on one-shot tasks, and the
only amortization test failed. The framework should stop claiming token
economy and claim what it can still argue: correctness discipline and
continuity across sessions. If a later experiment shows amortization on
large repos, the claim can come back with a number attached.

## 4. Options

| Option | What changes | Assessment |
|---|---|---|
| A. Keep as is, treat paper as out of scope | nothing | Not honest. The framework's own benchmarks already replicate the paper's cost result, and the digest has no positive evidence anywhere. |
| B. Minimal AGENTS.md, workflow kept, digest on demand | AGENTS.md shrinks to requirements; overview leaves the always-on path; benchmark gains a context-only arm | **Recommended.** Cuts what is falsified, keeps what is untested, adds the test. |
| C. Retire AGENTS.md generation, keep only skills and `.ai` | no instructions file at all | Too far. Commands and the `.ai` commit rule are the parts with evidence for them, and they need an always-loaded home. |

## 5. Proposal (v5.27): "Minimal requirements"

Ordered by evidence strength. Items 1 to 4 follow directly from the paper.
Items 5 to 7 are the framework's own follow-through.

1. **Shrink AGENTS.md to requirements.** Target under 500 words before
   project context (the paper's human files average 641 words including
   overviews). Keep: the right-sizing rule, the `.ai` commit rule with the
   exact command, the workflow table, the changes layout, and the
   build/test/lint commands. Move Protocol items 1, 2 (notes-hub
   mechanics), 4 (gate sizing), 7 (task cursor), 8 (compaction) into the
   skills that need them. `/build` already repeats most of item 4 and item 2
   verbatim, so this is deduplication, not loss.
   Files: `templates/instructions/agents.md`, `templates/skills/build.md`,
   `templates/skills/spec.md`.

2. **Take the overview out of the always-on path.** `/explore` writes only
   commands, top conventions and user-supplied non-derivable rules into
   `GENERATED:project-context` (cap ~300 tokens). Module map, purpose
   paragraph and glossary go to `.ai/notes/map.md`, linked from
   `notes.md`, read on demand. Nothing is lost; it stops being loaded on
   every one-line fix. `/build` step 5's refresh compares probe against
   `map.md` instead of AGENTS.md.
   Files: `templates/skills/explore.md`, `templates/skills/build.md`,
   `templates/instructions/agents.md`, `agentgen/content.py` (the
   generated-section stub), `tests/check_templates.py`.

3. **Do not summarize what the repo already documents.** If `probe.py`
   reports a README above a threshold or a `docs/` tree, `/explore` records
   pointers to those files instead of re-describing the codebase. This is
   the paper's Figure 5 result: LLM digests only pay when there is no
   documentation. `probe.py` gains a one-line "docs present" field.
   Files: `templates/tools/probe.py`, `templates/skills/explore.md`.

4. **Make human input the primary `/explore` output.** The paper's only
   winning arm is developer-written. `/explore` already asks the user about
   unwritten rules and ownership; move that Q&A from the last bullet to the
   first, and have the sampling fan-out serve the questions rather than the
   digest. Record answers in the requirements block of AGENTS.md (they are
   the "specific tooling" class of instruction), not only in notes.
   File: `templates/skills/explore.md`.

5. **Drop the explore-before-work nag.** Protocol item 1 (v5.10 freshness
   guard) tells the agent to run `/explore` before any non-trivial work
   because "a stale digest costs more discovery tokens". The paper measured
   discovery with and without a digest and found no difference. Keep
   `/explore` as an offered command; stop mandating it. Commands come from
   `probe.py` in one call regardless.
   File: `templates/instructions/agents.md`. CONCEPT.md §21 becomes history.

6. **Benchmark: separate the file from the workflow.** Add a fixed arm
   "C-cells": scaffold, run `/explore`, then give the task with no `/spec`,
   no `/build`, no review. This isolates the context-file effect (what the
   paper measured) from the workflow effect (what the framework claims).
   Add the paper's two behavioral metrics to `count_tokens.py` output or
   the report format: step count and steps to first task-relevant file.
   Then run `amortization-playbook.md` Experiment A on Sonnet 5, which has
   been planned since July and never executed. Until it runs, the README
   makes no amortization claim.
   Files: `benchmarks/fixed-runbook.md`, `benchmarks/tools/count_tokens.py`.

7. **Reposition.** README first paragraph and CONCEPT.md preamble: from
   "token-optimized knowledge transport" to "one command set on any harness,
   a spec-and-review discipline sized to the change, and private memory
   across sessions; costs more tokens on a one-shot task by design". CONCEPT
   gets a §36 recording the paper, marks §6 and §9 item 5 as superseded,
   and bumps `FRAMEWORK_VERSION` to 5.27.

Not changed: harness axis, skill names, `.ai` private repo, Stop hook,
reviewer, permission allowlist, `/tidy-up`, `/framework-update`,
`/import-*`. The existing update path carries scaffolds forward since the
change is a template edit plus a moved section, both of which
`/framework-update` already handles (it migrates the generated section in
place; item 2 needs one added rule: split the old section into the new
stub plus `map.md`).

## 6. Bug found while reading

`templates/skills/build.md` step 5 still says: if probe's Code LOC exceeds
~10k, "propose re-initializing as large". The large profile was removed in
v5.22. Every `/build` on a repo over 10k LOC now proposes a migration that
cannot run. Delete the sentence. Independent of the paper; fix in the same
version or before.

## 7. Open questions the paper cannot answer

- Whether the review gate reduces invalid results on modern models. One
  haiku data point says yes, one Sonnet 5 round says no gap. Needs the
  C-cell arm to say which part of the scaffold the haiku gain came from.
- Whether memory across sessions pays on repos where discovery is expensive
  (the large-repo Experiment B). Never run on any model.
- Non-Python ecosystems. The framework's cells already cover shell, Rust
  and C++; the paper does not. The paper's authors flag this as the case
  where context files might matter more, which is a reason to keep the
  ecosystem-neutral cells, not to drop them.
