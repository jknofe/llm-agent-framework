# Testing

How to validate a change to this framework. Two layers: fast mechanical checks
(run on every change) and live agent-behavior cases (run for behavior changes
worth shipping). The generator renders templates, so the tests are "does it render,
does it run, does an agent behave" plus a property check over the templates
themselves.

## Layer 1: Mechanical checks (every change, <1 min)

0. **Template properties and bootstrap**
   ```bash
   python3 tests/check_templates.py
   python3 tests/test_bootstrap_update.py
   python3 tests/test_harness_switch.py
   python3 tests/test_tasks_table.py
   ```
   The last one checks everything `tasks.py` promises, without an agent: the
   `/task list` table (live tasks only, sort order, emoji and legend, the
   flags, the resume pointer, no ANSI through a pipe) and the `/task`
   create-or-do resolver (every verdict, near-duplicates). Agent behavior of
   `/task` is covered by [tests/task-commands.md](tests/task-commands.md),
   run after changing it.
   The third scaffolds one harness, switches to another, and checks that the
   old command set is gone, that a user-added skill next to it is not, that
   retired files land in the backup, and that a switch is never silent.
   The second builds real v5.12/v5.13 scaffolds from this repo's git history
   and checks that `--bootstrap-update` delivers `/framework-update`, stamps
   `framework_version: null`, and modifies nothing else. It skips cleanly on a
   shallow clone.
   Asserts no orphaned template, every declared slot filled, no `${...}` left
   in any rendered artifact, rendered tools parse as Python, rendered settings
   parse as JSON, no em dash in a template (CONCEPT.md section 8), and the
   hermes skill descriptions inside that harness's 60-character cap with no
   command name colliding with a hermes built-in, and AGENTS.md under 650
   words before its generated section on every harness (CONCEPT.md
   section 36) with no leftover text describing the retired overview digest.
   `safe_substitute` leaves a mistyped slot in place silently, so the slot
   check is the only thing between a typo and a broken scaffold.
1. **Syntax**
   ```bash
   python3 -c "import ast; ast.parse(open('init_agent.py').read())"
   for f in agentgen/*.py; do python3 -c "import ast; ast.parse(open('$f').read())"; done
   ```
2. **Scaffold all three harnesses** into a throwaway dir (init writes to CWD;
   never scaffold into this repo root):
   ```bash
   d=$(mktemp -d)
   for h in claude copilot hermes; do
     mkdir -p "$d/$h"
     ( cd "$d/$h" && python3 /path/to/init_agent.py \
         --name t --description d --harness $h -y >/dev/null )
   done
   ```
3. **Grep the rendered output** for your template change in every affected
   variant. A change that renders on only one harness is usually a bug.
4. **Referenced paths exist and run.** Any tool path a template mentions
   (e.g. `.ai/agent/tools/probe.py`) must exist in the scaffold and exit 0. A dangling path in a template is a silent break.
5. **Re-init preservation:** scaffold, hand-edit a KB node / notes.md / the
   `GENERATED:project-context` section, re-run init, confirm the report says
   `preserved` and nothing reverted to a stub.
6. **Update plumbing** (after any change to the file set or the stamp):
   `--emit-reference` renders into an empty dir with no git side effects,
   `--detect` prints the stamp for a stamped scaffold and the inspected
   fallback for one without, and every path in `framework_files` exists in
   the scaffold that recorded it. Retiring a file means removing its
   `write()` call: verify the old scaffold's `framework_files` still lists it
   so `/framework-update` can delete it.
7. **Byte-identity** (after any refactor that must not change output):
   capture all three rendered variants before the change, re-render after, and
   require an empty diff. This is the only cheap guard against silent
   corruption when moving content between templates and code; it caught two
   real defects during the v5.17 restructuring that reading the diff did not.
8. **Leakage sweep** (after changing normative text): grep the scaffolds for
   terms specific to any test target (satty, debian, cargo deb, angular,
   sqlite-utils, bats, ros, nav2, navigation2, colcon, ...). Generated
   artifacts must stay ecosystem-neutral; named linters are allowed only as
   diverse example lists.

## Layer 2: Agent behavior (behavior changes)

Run the affected cases of [tests/task-commands.md](tests/task-commands.md)
live on the pinned target repository, before and after the change. It covers
`/task create`, `/task do`, `/task list` and the create-or-do resolver, each
case with its prompt, pass criteria and the command that decides it. A FAIL that comes from
the skill text gets a template fix, a CONCEPT.md version entry citing the
case, and a rerun of that case before the commit.

Judge a run from the task files, the `.ai` git log and the session
transcript, never from the agent's own summary.

The earlier benchmark rounds (fixed runbook, sequence and constraint rounds,
Docker gates) were removed on 2026-09-29 after the measurement program was
halted. Their results are summarized in CONCEPT.md Part II, which also says
how to restore the files from git history.
