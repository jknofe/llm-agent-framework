Tidy up this codebase without changing what it does. Scope (optional:
a path, module, or area; default is the whole repo): ${arg}

Four passes, in this order, so nothing is polished that is about to be
removed. A tidy-up is a hygiene sweep, not a refactor: it may not
change behavior, public API, or output. If a cleanup you want needs a
behavior change, stop and write it up as a change spec instead.

0. Baseline first. Confirm the worktree is clean, or ask the user
   whether to proceed with pending edits. Run the project's build,
   test, and lint commands and record the result. If they are already
   failing, say so and stop: without a green baseline you cannot tell
   your sweep from a pre-existing break. Note the current commit SHA.

1. Dead code: remove it, with evidence.
   Candidates: unreferenced private functions, types, and variables;
   unused imports; unreachable branches; commented-out code blocks;
   parameters no caller passes; feature-flag arms whose flag no longer
   exists.
   Evidence before every removal. Search the whole repo, not just the
   source tree: tests, build files, CI config, packaging metadata,
   templates, and docs. Check the dynamic-reference sites a plain
   search misses, whichever apply to this ecosystem: reflection and
   name-based lookup, plugin or command registries, dependency
   injection, serialized field names, conditional compilation,
   generated bindings, and entry points declared in packaging
   manifests.
   Decide first whether this repo is a library or an application. In a
   library, an exported symbol is not dead merely because nothing in
   this repo calls it; removing it is an API break, which this skill
   does not do. Treat the public surface as used.
   Where the ecosystem has a tool that reports unused code (a linter,
   a compiler warning, a coverage report), run it and use its output as
   a candidate list, then verify each hit yourself. A tool's verdict is
   evidence, not authority.
   When the evidence is ambiguous, do not remove it. Move it to the
   proposal list in step 2 and let the user decide.
${survey_note}
2. Obsolete files: propose, never delete.
   Candidates: scripts nothing invokes, config for a tool the project
   no longer uses, generated output committed by mistake, editor and
   merge droppings (`.orig`, `.rej`, `.bak`), duplicated vendored
   copies, and docs describing a removed feature.
   Evidence: nothing references the path, no build, CI, or packaging
   config names it (including by string), and its git history shows it
   went quiet. All three, not one.
   Never delete a file in this pass, and never mass-delete on a guess.
   Report a table instead: path, why it looks obsolete, what breaks if
   that is wrong, and your confidence. Let the user choose. Leave
   licence files, CI config, and anything a packaging manifest names
   out of the proposal unless the evidence is conclusive.

3. Overlong comments: shorten to at most 1-2 lines.
   Target the narrative blocks that restate what the code already
   says. Shorten those to a single line, or delete them when the code
   is clearer without.
   Do not shorten, regardless of length: licence and copyright
   headers, SPDX tags, generated-file banners, and API documentation
   comments that are the published contract for a symbol.
   A long comment that carries real information is not clutter. If it
   explains why, records a non-obvious invariant, justifies a
   workaround, or cites an algorithm or issue, keep the information:
   compress it to 1-2 lines if it fits, otherwise move it into the
   project's docs and leave a one-line pointer. Never delete knowledge
   to satisfy a line count.

4. Em dashes: remove them from prose.
   Rewrite every em dash in source strings, comments, docs, and
   markdown. Replace by clause, do not swap character for character: a
   parenthetical pair becomes commas or parentheses, an abrupt break
   becomes a colon or a full stop, a range becomes `to`. Read the
   result back; if it no longer parses as a sentence, rewrite it.
   Leave alone: test fixtures and golden or expected-output files,
   vendored third-party sources, licence texts, data files, URLs, and
   any string where the character is the data under test. Changing
   those changes behavior, which this skill may not do.

5. Verify and record.
   Re-run the same build, test, and lint commands from step 0 and
   compare against the recorded baseline. Any new failure means the
   sweep broke something: fix it or revert that hunk. A golden-file
   mismatch after pass 4 means you edited data, not prose.
${review_note}${record}
6. Report and hand over.
   Print one section per pass: what was removed with the evidence, the
   proposal table for files, the comments touched, and the em-dash
   count. Commit `.ai` (`tidy-up: <scope>`). Leave the host-repo
   changes uncommitted for the user to review; this framework never
   commits the host project repo.

Right-size the sweep. On a large repo, take the scope argument
seriously and do one area at a time: a diff nobody can review is worse
than untidy code. Keep the passes in separate commits-worth of changes
so a reviewer can read them independently.
