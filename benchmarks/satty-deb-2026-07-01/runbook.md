# Benchmark Runbook: llm-agent-framework on a Target Repo
**Template for:** autonomous agent benchmark runs  
**Reference run:** [report.md](report.md) (Satty debian-pkg, 2026-07-01)

---

## How to use this runbook

An orchestrator (human or agent) sets the configuration variables at the top of
each agent's prompt before spawning. The agent reads those values and executes
all steps below. The runbook is self-contained — the agent needs no prior
context beyond what is written here.

To repeat the Satty benchmark: fill in the `## Configuration` block below,
copy the relevant `## Agent prompt` section (small or large profile), and spawn
the agent with the chosen model.

---

## Configuration (filled by user/orchestrator)

```
TARGET_REPO:   https://github.com/Satty-org/Satty.git
TARGET_BRANCH: main
RUN_ID:        <unique string, e.g. "sonnet-high-small">
MODEL:         <claude-sonnet-latest | claude-opus-4-8 | ...>
EFFORT:        <medium | high>
PROFILE:       <small | large>
WORK_DIR:      /tmp/benchmark/runs/<RUN_ID>/satty
RESULTS_FILE:  /tmp/benchmark/results/<RUN_ID>.md
FRAMEWORK:     /path/to/llm-agent-framework/init_agent.py
DOCKER_IMAGE:  satty-deb-builder   # see "Docker image" section below
CHANGE_ID:     debian-pkg          # small profile
TICKET_ID:     DEBIAN-1            # large profile
CHANGE_TITLE:  "add debian format to satty build"
```

**Effort guidance (encode in agent prompt):**
- `medium`: be efficient; make decisions from evidence directly; keep spec/ticket focused.
- `high`: be thorough; explore all asset types, workflows, and edge cases; consider Debian policy details; verify all acceptance criteria explicitly.

---

## Prerequisites

### 1. Docker image with cargo-deb

Build once and reuse across all runs:

```bash
docker build -t satty-deb-builder - <<'EOF'
FROM rust:latest
RUN cargo install cargo-deb --locked
WORKDIR /workspace
EOF
```

Takes ~8 minutes; subsequent builds use the cache.

### 2. Framework installed

```bash
# Already installed as init-agent shell function, or call directly:
python3 /path/to/llm-agent-framework/init_agent.py --help
```

### 3. Results directory

```bash
mkdir -p /tmp/benchmark/{runs,results}
```

---

## Agent Prompt — Small Profile

> Copy this entire block as the agent's prompt. Replace `{...}` placeholders.

```
You are benchmark agent {RUN_ID} running the llm-agent-framework SMALL profile.
Model: {MODEL} | Effort: {EFFORT}

AUTONOMOUS RUN. No human available. Resolve all Q&A from code evidence.
Record numbered assumptions in .ai files. Proceed without blocking.

Record start time: date '+%Y-%m-%dT%H:%M:%S'

================================================================
STEP 1 — SETUP
================================================================
mkdir -p /tmp/benchmark/runs/{RUN_ID}
git clone --depth=1 {TARGET_REPO} /tmp/benchmark/runs/{RUN_ID}/satty
cd /tmp/benchmark/runs/{RUN_ID}/satty
python3 {FRAMEWORK} \
  --name satty \
  --description "Modern screenshot annotation tool (Rust/GTK4)" \
  --size small --harness claude -y

================================================================
STEP 2 — EXPLORE  (read .claude/skills/explore/SKILL.md, follow it)
================================================================
All file operations from: /tmp/benchmark/runs/{RUN_ID}/satty

1. Run: python3 .ai/agent/tools/probe.py
2. Read: Cargo.toml, Makefile, build.rs, src/ entry point and key modules,
         .github/workflows/ (all files)
   {EFFORT=high}: also read README.md, org.satty.Satty.metainfo.xml, release.nu
3. Fill AGENTS.md GENERATED:project-context section
   (purpose, tech stack, build/test/lint commands, module map, conventions)
4. Fill .ai/notes.md (build quirks, domain terms, asset types, ci-release note)
5. Commit: git -C .ai add -A && git -C .ai commit -m "explore: project context"

================================================================
STEP 3 — SPEC  (read .claude/skills/spec/SKILL.md, follow it)
================================================================
ID: {CHANGE_ID} | Title: {CHANGE_TITLE}

- Read Makefile install target carefully — it defines every asset path for the .deb
- Write .ai/changes/{CHANGE_ID}/spec.md with:
    frontmatter: id, title, status=planned, created=<today>
    ## Goal        (one paragraph: what and why)
    ## Acceptance criteria
      - [ ] Cargo.toml has [package.metadata.deb] with name, maintainer,
            depends, assets matching Makefile install targets
      - [ ] Makefile has a `deb:` target that depends on build-release and
            calls cargo deb --no-build
      {EFFORT=high}: also require section/priority, extended-description,
      license-file directive, correct Debian zsh path (vendor-completions/),
      CI deb workflow
    ## Tasks       (explicit file paths for each change)
    ## Notes       (numbered autonomous assumptions)
- Commit: git -C .ai add -A && git -C .ai commit -m "spec: {CHANGE_ID}"

================================================================
STEP 4 — BUILD  (read .claude/skills/build/SKILL.md, follow it)
================================================================
Implement {CHANGE_ID}:

1. Add [package.metadata.deb] to Cargo.toml:
   - Study EVERY Makefile install target for asset source→dest paths
   - name, maintainer (from workspace.package.authors), depends
   - assets: binary (usr/bin/satty, 755), .desktop, SVG icon, all shell
     completions (bash/zsh/fish/elvish/nushell/fig), man page, LICENSE
   {EFFORT=high}: also add section="graphics", priority="optional",
   license-file=["LICENSE","0"] (not a raw asset), extended-description,
   version-pinned depends, zsh path = usr/share/zsh/vendor-completions/

2. Add `deb: build-release` target to Makefile running `cargo deb --no-build`
   (the build-release dependency ensures ci-release feature runs first,
   generating completions/ and man/ into the source tree)

   {EFFORT=high}: also add .github/workflows/ deb job if CI structure fits

3. Update .ai/notes.md with implementation decisions

4. Review gate:
   - Read .claude/agents/reviewer.md
   - Use the Agent tool to spawn a reviewer subagent with ONLY:
     (a) git diff HEAD output from the satty directory
     (b) the acceptance criteria from spec.md
   - If spawning fails (you are a subagent), do a self-review against the
     acceptance criteria and note "reviewer subagent unavailable"
   - Fix any correctness gaps found (not style issues)

5. Update spec status: status=done
6. Commit: git -C .ai add -A && git -C .ai commit -m "build: {CHANGE_ID}"

================================================================
STEP 5 — DOCKER VALIDATION
================================================================
Create mock build artifacts (completions/man are generated by build.rs
under ci-release; binary doesn't exist until compiled):

mkdir -p target/release completions man
printf '\x7fELF\x02\x01\x01\x00' > target/release/satty && chmod +x target/release/satty
for f in satty.bash _satty satty.fish satty.elv satty.nu satty.ts; do
  [ -f completions/$f ] || touch completions/$f
done
[ -f man/satty.1 ] || touch man/satty.1
# If you included metainfo.xml in assets:
[ -f org.satty.Satty.metainfo.xml ] || touch org.satty.Satty.metainfo.xml

Run validation inside Ubuntu Docker:
docker run --rm \
  -v /tmp/benchmark/runs/{RUN_ID}/satty:/workspace \
  {DOCKER_IMAGE} \
  bash -c "
    cd /workspace
    cargo deb --no-build --no-strip 2>&1
    echo '=== .deb contents ==='
    dpkg-deb --contents target/debian/satty_*.deb 2>/dev/null | awk '{print \$6}' | sort
  "

Record FULL output.
Status: PASS if a .deb path line is printed (e.g. target/debian/satty_*.deb).
The '$auto deps' warning is expected with a mock binary — not a failure.

================================================================
STEP 6 — WRITE RESULTS to {RESULTS_FILE}
================================================================
mkdir -p /tmp/benchmark/results
Write {RESULTS_FILE} with:

# Benchmark Results: {RUN_ID}

## Configuration
| Field | Value |
|---|---|
| Run ID | {RUN_ID} |
| Profile | small |
| Model | {MODEL} |
| Effort | {EFFORT} |
| Start | <from step 1> |
| End | <now: date '+%Y-%m-%dT%H:%M:%S'> |
| Duration | <seconds> |
| Docker status | PASS / FAIL |

## Spec produced
<full content of .ai/changes/{CHANGE_ID}/spec.md>

## .ai commit history
<git -C .ai log --oneline>

## Satty changes (git diff --stat HEAD)
<output>

## Docker validation output
<full output>

## .deb contents
<dpkg-deb --contents output>

## Observations
<2-3 sentences on framework workflow, what worked, what was unclear>

EFFORT NOTE — {EFFORT}:
  medium: be efficient; decide from evidence directly; keep spec focused.
  high:   be thorough; explore all assets, workflows, edge cases; verify
          every acceptance criterion explicitly.
```

---

## Agent Prompt — Large Profile

> Same structure as small, but replace STEP 3–4 with the ticket pipeline below.
> STEP 1, 2, 5, 6 are identical (change `--size small` to `--size large`).

```
================================================================
STEP 2 — EXPLORE  (read .claude/skills/explore/SKILL.md, then .ai/agent/phases/init.md)
================================================================
(Same as small, PLUS:)
- Fill KB nodes in .ai/knowledgebase/:
    architecture/overview.md, infra/build.md (document ci-release!),
    infra/ci-cd.md, conventions/code-style.md
    {EFFORT=high}: also conventions/testing.md, conventions/git-workflow.md
- Update .ai/knowledgebase/manifest.yaml after each node
  (gen_index.py runs automatically via hook; or run:
   python3 .ai/agent/tools/gen_index.py)
- Commit: git -C .ai add -A && git -C .ai commit -m "explore: initial KB"

================================================================
STEP 3 — ADD TICKET  (read .claude/skills/add-ticket/SKILL.md, follow it)
================================================================
Create .ai/tickets/{TICKET_ID}-add-debian-format-to-satty-build.md:
  id={TICKET_ID}, title="{CHANGE_TITLE}", status=new, created=<today>
  body: description of adding cargo-deb Debian packaging
git -C .ai add -A && git -C .ai commit -m "add-ticket: {TICKET_ID}"

================================================================
STEP 4 — PLAN  (read .claude/skills/plan/SKILL.md, then .ai/agent/phases/planning.md)
================================================================
Follow planning.md exactly. Create .ai/knowledgebase/tasks/{TICKET_ID}/ with:

  ticket.md   — inbox content + Q&A section with autonomous assumptions
  plan.md     — thin index (task table, kb-commit, read-first pointer)
  01-cargo-deb-metadata.md — SELF-CONTAINED task:
    goal, acceptance criteria, affected files (Cargo.toml, Makefile),
    pre-bound KB nodes (infra/build, architecture/overview),
    exact [package.metadata.deb] TOML block to add
  {EFFORT=high}: 02-ci-deb-workflow.md if CI integration is planned

Plan-review gate (same as build skill review gate above).
git -C .ai add -A && git -C .ai commit -m "plan: {TICKET_ID}"

================================================================
STEP 5 — IMPLEMENT  (read .claude/skills/implement/SKILL.md, then .ai/agent/phases/implementation.md)
================================================================
Follow implementation.md exactly.

1. Write .ai/.current cursor (ticket id, task file, date)
2. Drift check: git -C .ai diff <kb-commit> -- knowledgebase/<node>
3. Work each task file in plan.md order:
   - Make actual changes to Cargo.toml and Makefile (same as build step above)
   - {EFFORT=high}: also CI workflow
4. Maintain kb-delta.yaml (op: update, node: infra/build, diff: <content>)
5. Update task frontmatter: status=done; delete .ai/.current
6. Ticket review gate (reviewer or self-review)
7. Update plan.md: status=done, reviewed=<today>
8. Update manifest.yaml if KB changed; gen_index.py runs automatically
9. Commit: git -C .ai add -A && git -C .ai commit -m "implement: {TICKET_ID}"

(STEP 5 Docker validation and STEP 6 results are identical to small profile)
```

---

## Evaluation Checklist

After all runs complete, verify each run against this checklist:

```
[ ] .ai has the expected commit sequence (init → explore → spec/ticket → [plan] → build/implement)
[ ] Cargo.toml has [package.metadata.deb] section
[ ] Makefile has a `deb:` target that depends on build-release
[ ] cargo deb --no-build --no-strip produces a .deb inside Ubuntu Docker
[ ] dpkg-deb --contents shows: binary, .desktop, icon, all completions, man page
[ ] results file exists at RESULTS_FILE
```

### Quality dimensions for comparison

| Dimension | Check |
|---|---|
| Zsh completion path | `vendor-completions/` (Debian) vs `site-functions/` (wrong) |
| License handling | `license-file` directive vs raw asset at wrong path |
| `section`/`priority` present | yes/no |
| `extended-description` present | yes/no |
| CI workflow added | yes/no; single-arch vs multi-arch |
| `depends` quality | `$auto` only vs explicit with version pins |
| `ci-release` constraint captured | in spec Notes / Makefile dep |
| Fig completion included | yes/no |
| metainfo.xml included | yes/no (bonus) |
| Makefile `build-release` dependency | present (required) vs missing (bug) |

---

## Notes on Session Limits

If an agent hits a session limit mid-run:

**Small profile:** the agent usually completes explore and spec. Resume by spawning a new agent with prompt: "The explore and spec phases are complete at {WORK_DIR}. Read spec.md, implement the changes, run Docker validation, write results." (The heavy work is done; build is fast.)

**Large profile:** separate explore and implement into two sessions deliberately. Session 1: `init + explore` (KB building is expensive). Session 2: `ticket + plan + implement` (reads existing KB, fast). The `plan.md` `read-first` pointer and `.ai/.current` cursor are designed for cross-session continuity.
