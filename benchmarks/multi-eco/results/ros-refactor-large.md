# Benchmark Results: ros-refactor-large

## Configuration

| Field | Value |
|---|---|
| Run ID | ros-refactor-large |
| Profile | large |
| Model | claude-sonnet-5 |
| Effort | medium |
| Target repo | ros-planning/navigation @ noetic-devel (f44bb1fc2810399165115cc98b530fe4b9397c18, depth-1 clone) |
| Ticket | NAV-2: extract MapServer class from main.cpp (map_server package) |
| Start | 2026-07-02T19:05:18 |
| End | 2026-07-03T01:45 (approx) |
| Duration | ~6h40m wall clock; work time much lower -- the run was suspended mid-implementation by a session limit and resumed by the coordinator. Active phases: explore+plan ~35 min, implement+validate+review ~25 min |
| Container status | **PASS** |

## KB nodes created / filled (Phase 1, lean explore)

- `architecture/overview.md` (hot) -- verified metapackage structure, module
  table from probe.py LOC, data-flow (move_base as integration point,
  map_server upstream/independent), entry points, host commit recorded.
- `infra/build.md` (cold) -- catkin build/test commands, the dual test
  mechanism (catkin_add_gtest utest + add_rostest rtest.xml), the
  map_server_image_loader precedent, yaml-cpp version detection, test-data
  copy function.
- `conventions/code-style.md` (hot) -- no linter configured (verified);
  observed conventions: 2-space indent, trailing-underscore members,
  `#ifndef PKG_NAME_H` guards, header/cpp split precedent, verbatim BSD
  license header rule.
- `modules/map_server.md` (hot) -- module node for the touched package:
  purpose, structure, public ROS interface (services/topics/params/CLI),
  test coupling analysis (rtest is black-box -> extract-class is safe),
  and three named refactor traps (operator>> shim TU placement, the
  image_loader.h guard misnomer `MAP_SERVER_MAP_SERVER_H`, exit(-1)
  contract).
- `infra/ci-cd.md` (cold) -- filled as "none in-repo, ROS buildfarm".
- `domain/glossary.md`, `conventions/testing.md`, `conventions/git-workflow.md`
  -- left at scaffold level (lean explore, nothing non-derivable surfaced).
- `AGENTS.md` GENERATED:project-context populated (~450 tokens, under the
  1500 cap); manifest.yaml updated per node; INDEX.md regenerated via tool.
- Coverage report recorded in `.ai/notes.md` (read vs skipped; all
  non-map_server package internals flagged shallow / lazy-init candidates).

## ticket.md (final)

Located `.ai/knowledgebase/tasks/NAV-2/ticket.md`, `status: done`. Original
body plus a Q&A section with 7 numbered autonomous-run assumptions, the
load-bearing ones being:

1. File names `include/map_server/map_server.h` + `src/map_server.cpp`.
2. **Header-guard collision avoidance**: `image_loader.h` already occupies
   the token `MAP_SERVER_MAP_SERVER_H`; new header uses
   `MAP_SERVER_MAP_SERVER_NODE_H`.
5. The `HAVE_YAMLCPP_GT_0_5_0` `operator>>` shim moves to `map_server.cpp`
   (same TU as `loadMapFromYaml`, before first use).
6. Preserve exactly: `exit(-1)` on load failure, all log strings, defaults
   (0 / 0.65 / 0.196), deprecated 2-arg CLI, verbatim license headers.
7. New .cpp added to the existing executable target; no new library.

## plan.md + task files

Trivial path per planning.md (single self-contained area): one task file
`01-extract-mapserver-class.md` (status: done) with explicit affected
files, full expected header interface, guardrails, and 5 acceptance
criteria (build green; tests pass unmodified; behavioral invariants
enumerated; CMake constraints; diff confinement). plan.md is a thin index
with kb-commit pinning (dfb6071) and both review-gate records.

**Plan-review gate** (fresh general-purpose sub-agent, given only plan +
task file + ticket + source): verdict FAIL-with-gaps. It confirmed the two
trap claims (guard collision, operator>> TU) against the source and the
interface transcription, and found one real compile-breaking gap: the task
file's expected `map_server.h` did not include `image_loader.h` even though
`MapMode` appears in method signatures, while hedging prose said "header or
cpp". Fixed in the task file before implementation. This was a genuine
catch, not ceremony.

## .ai commit history

```
2e08de8 implement: NAV-2   (KB delta applied, plan/task/ticket -> done, notes)
16b7cc9 plan: NAV-2        (ticket.md + plan.md + task file, review-gate fix)
dfb6071 add-ticket: NAV-2  (inbox ticket)
d4e52cd explore: seed architecture/build/code-style + map_server module node
9ef4eda init: scaffold KB + phase docs (navigation)
```

5 commits total (init + explore + ticket + plan + implement).

## Diff stat (host repo)

```
map_server/CMakeLists.txt |   2 +-     (one line: add src/map_server.cpp to target)
map_server/src/main.cpp   | 259 +----  (3 insertions, 256 deletions -> 73-line thin entry point)
new: map_server/include/map_server/map_server.h  (93 lines)
new: map_server/src/map_server.cpp               (263 lines)
```

Plus framework scaffolding outside the reviewed change: `.gitignore` (+.ai/),
`AGENTS.md`, `CLAUDE.md`, `.claude/` (all created by init_agent.py, not part
of NAV-2).

## Container output (final validating run)

```
--- deps installed: 0
navigation: Cannot locate rosdep definition for [move_base_msgs]
costmap_2d: Cannot locate rosdep definition for [map_msgs]
#### Running command: "cmake ... -DCATKIN_WHITELIST_PACKAGES=map_server ..." OK
#### Running command: "make -j10 -l10"
[100%] Built target run_tests_map_server_rostest
[100%] Built target run_tests_map_server
#### Running command: "make run_tests_map_server -j10 -l10"
Summary: 17 tests, 0 errors, 0 failures, 0 skipped
```

**Environment note (pre-existing, verified independent of the refactor):**
the ros-nav-builder image as shipped cannot configure map_server at all --
it is missing `ros-noetic-tf2` (fails at `find_package(catkin ... tf2)`,
CMakeLists.txt:4) and Bullet/SDL/SDL_image/yaml-cpp dev packages
(CMakeLists.txt:11), and its rosdep db cannot resolve `tf2`. These failures
occur at CMake configure time, before any source file is compiled, so they
are provably unrelated to the diff (equivalent to a pristine-checkout
failure). The validation run therefore prepends
`apt-get install -y ros-noetic-tf2 ros-noetic-tf2-ros libbullet-dev
libsdl1.2-dev libsdl-image1.2-dev libyaml-cpp-dev`. With deps present:
build green, 17/17 tests pass. The unresolved rosdep warnings for
`move_base_msgs`/`map_msgs` belong to other packages outside the
`--only-pkg-with-deps map_server` whitelist. Runbook recorded in
`.ai/notes.md`.

PASS = map_server builds AND `catkin_test_results` reports 17 tests / 0
errors / 0 failures AND `git diff`/`git status` show nothing under
`map_server/test/`.

## Invariance evidence (zero behavior change)

- **test/ untouched**: `git status --short -- map_server/test/` and
  `git diff --name-only -- map_server/test/` both empty; confirmed twice
  (by the implementing session and independently by the review sub-agent).
- **How zero behavior change was argued**: (a) structural argument in the
  KB -- the rostest launches the real executable and interacts only via ROS
  services/topics, and utest only exercises image_loader, so an internal
  extract-class refactor cannot be observed by the suite as long as the
  moved code is identical; (b) mechanical verification -- the review
  sub-agent extracted `main()` and the moved class region from
  `git show HEAD:map_server/src/main.cpp` and diffed them against the new
  files: `main()` and `USAGE` byte-identical; every log string, param
  default (0/0.65/0.196), service/topic name, `RESULT_*` constant,
  `waitForValid`, and the `exit(-1)` path identical; only deltas were the
  mechanical class-split scaffolding (`MapServer::` qualification, header
  declaration); (c) empirical -- full test suite (including the black-box
  rostest against the rebuilt executable) green in the container.
- **Trap handling verified**: operator>> shim placed in the same TU before
  first use; distinct header guard (`MAP_SERVER_MAP_SERVER_NODE_H` vs the
  pre-existing misnamed `MAP_SERVER_MAP_SERVER_H` in image_loader.h);
  license headers byte-identical in both new files.

## Project-context refresh

Fired as prescribed by implementation.md before declaring the ticket done.
Re-ran `probe.py`: detected build/test/lint commands unchanged (probe
detects none; KB documents the catkin commands), module map unchanged
except a bare LOC delta on map_server (1350 -> 1097) -- explicitly not
actionable per the phase doc. **No drift; AGENTS.md GENERATED section not
changed** (its map_server line and conventions summary remain accurate
post-refactor). Outcome recorded in `.ai/notes.md`. The hot node
`modules/map_server.md` and cold `infra/build.md` were updated via
`kb-delta.yaml` (structure section now reflects the split; traps section
retained with the guard-misnomer warning made durable).

## Observations (large profile on a focused single-package change)

- **What paid off:** (1) The module-node deep dive genuinely front-loaded
  the three things that could have broken the build or the "unmodified
  tests" constraint: the guard-token misnomer in image_loader.h, the
  yaml-cpp operator>> TU requirement, and the rtest black-box coupling
  analysis that justified "tests need zero changes". All three were written
  into the KB before planning and flowed into the task file. (2) The
  plan-review gate caught a real compile-breaking omission (missing
  image_loader.h include in the header spec) that the planning context had
  hedged over -- fresh-context review demonstrably added value twice. (3)
  `.ai/.current` + per-phase .ai commits made the mid-implementation
  session-limit interruption a non-event: the resumed session re-derived
  its position from git status + .current in one command.
- **What was ceremony for this ticket size:** the full 7-node KB scaffold
  (glossary, git-workflow, testing nodes stayed effectively empty),
  manifest/INDEX/rules regeneration machinery, and the AGENTS.md digest --
  none of it influenced this single-package refactor beyond what the module
  node + build node alone provided. The kb-delta.yaml indirection also
  added a step over just editing the two nodes directly (both were done).
  For a one-task ticket, the trivial path (which the framework itself
  prescribes and which was taken) is the right escape hatch; the overhead
  that remains is mostly the fixed exploration cost, which would amortize
  over subsequent tickets against the same KB.
- **Net judgment:** for THIS ticket alone, roughly half the machinery was
  load-bearing (module node, traps, review gates, resume cursor) and half
  was fixed-cost scaffolding that a second ticket would start amortizing.
  The framework's own right-sizing guidance kept planning proportionate
  (one task file, no Q&A theater).
