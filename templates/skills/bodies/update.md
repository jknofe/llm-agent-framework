Update this project's agent framework to the current version, in
place, without losing what this project knows. Argument (optional,
`dry-run` reports the plan and changes nothing): ${arg}

The knowledge this project accumulated is the expensive artifact and
the framework files are cheap. So: never re-run /explore as part of an
update, and never regenerate hand-filled content from a stub. That
covers ${owned}.

1. Preflight.
   - Read `${framework_json}` for the recorded framework version,
     profile, harness, project name, description, and the list of
     framework files that version emitted. If the file is missing, this
     scaffold predates the stamp: run
     `python3 "$LLM_AGENT_HOME/init_agent.py" --detect` for
     profile/harness/name and treat the recorded file list as empty.
     A `description` of null means the scaffold predates the field; ask
     the user for the one-liner rather than inventing one.
     Retirement then rests entirely on the orphan test in step 3, so do
     not skip it on a pre-stamp scaffold.
   - Commit anything pending in `.ai` so the update is one revertable
     diff: `git -C .ai add -A && git -C .ai commit -m "pre-update
     snapshot"`.
   - The `.ai` repo does not cover the framework files that live in the
     host repo, and those are the ones an update overwrites. Copy
     ${backup_paths} into `.ai/agent/.update-backup/`, replacing any
     older backup. Older scaffolds do not ignore that path yet, so make
     sure `.ai/.gitignore` contains `agent/.update-backup/` first; a
     backup committed into the KB history is not a backup.
   - Report `git status` for those paths. Untracked is the normal state
     for a scaffold the host repo never committed: note it and carry on,
     the backup already covers the content. Tracked *and modified* is the
     one that stops you, because the user has work in a file this update
     will overwrite: say which files and let them decide first.

2. Render the reference, for the profile and harness step 1 established
   (from the stamp, or from `--detect` when there is none). The generator
   is at
   `$LLM_AGENT_HOME/init_agent.py` (set by the framework's install.sh).
   If `$LLM_AGENT_HOME` is unset, ask the user where the checkout is;
   do not guess a path. Pull it first when it has a remote
   (`git -C "$LLM_AGENT_HOME" pull --ff-only`), then render a pristine
   scaffold into a temp directory:

       python3 "$LLM_AGENT_HOME/init_agent.py" --emit-reference <tmpdir> \
         --harness ${harness} --name <project> --desc <description>

   Pass the `project` and `description` the stamp recorded, verbatim.
   They are what the reference renders its title and seeded context
   from, so substituting the directory name or a description of your own
   makes the comparison report differences this project never had.

   The reference is a read-only comparison target. Never copy it over
   the project wholesale; that is the blind overwrite this skill exists
   to replace.

3. Classify every path in the reference and in this scaffold, then act
   per file. Framework-owned means listed in the reference's or the
   recorded `framework_files`.
   - Added (in the reference, absent here): copy it in.
   - Identical: leave it.
   - Changed by the framework, untouched by the user: take the
     reference's version. Treat a file as user-edited whenever you
     cannot establish that it is still what its recorded version
     emitted, and merge instead of overwriting.
   - Changed by the user: merge. Take the framework's structural
     changes, keep every user addition, and state in the report what
     you kept. The cases that actually come up:
${merge_cases}   - Retired (in the recorded `framework_files`, absent from the
     reference): delete it, then grep the whole scaffold for its name
     and remove the instructions that still point at it. A retired file
     that stays referenced is worse than one that stays on disk.
   - Renamed (a command that answers to a different name in the
     reference): one command must have one definition, so move the
     directory or file rather than adding the new name beside the old
     one. Framework 5.25 renames the update command itself from
     `update` to `framework-update` on every harness, so this case
     applies to the very skill you are running; finish the update, then
     the old entry is the one to remove.

   Orphan test, for every file here that the reference does not have and
   the recorded list does not name. On a pre-stamp scaffold that is every
   such file, so this is the only thing standing between the project and
   framework files that can never be retired. Do not guess from the
   file's location or its contents; ask the generator whether it ever
   emitted that path:

       git -C "$LLM_AGENT_HOME" log --oneline -S'<file basename>' \
         -- init_agent.py agentgen/ templates/

   Search all three paths, not just `init_agent.py`. Up to framework 5.16
   the generator was that one file and every emitted path appeared in it;
   from 5.17 the emitted content lives under `templates/` and the write
   calls under `agentgen/`, so a file introduced after 5.17 leaves no
   trace in `init_agent.py` at all. Narrowing the search to it would
   report "no commits" for framework output and quietly make that file
   unretirable.

   Commits found means the framework emitted this file and a later
   version dropped it: it is orphaned framework output, so retire it like
   any other retired file. No commits means the user wrote it: leave it
   alone and do not mention it again. If `$LLM_AGENT_HOME` is not a git
   checkout the test cannot run, so leave every candidate in place and
   list them in the report as undecidable.

4. Migrate hand-filled content in place; do not regenerate it. The
   reference's stubs show the shape the new version expects, this
   project's files hold the content. Where the shape changed, edit this
   project's files:
${migrate}   If a new field cannot be derived from what the project already
   records, leave it empty and list it in the report for the user.
   Do not invent a value, and do not read the codebase to fill it:
   that is /explore's job and it is not part of an update.

5. Verify before reporting success.
   - Every tool the instructions name exists and exits 0:
     ${verify_tools}.
${verify_extra}   - AGENTS.md still holds this project's context between its
     GENERATED markers, and the marker text matches the reference's.
   - No instruction in the scaffold names a file that no longer exists.

6. Record and report.
   - Write `${framework_json}` from the reference's copy: new version,
     new file list, and this project's name and description carried
     across unchanged. Neither is derived from the codebase; they are
     what the user answered at init, and only this file still holds
     them.
   - Print one row per file: added / updated / merged (with what was
     kept) / retired / migrated / untouched, then anything left for the
     user to decide.
   - Commit `.ai` (`update: framework <old> -> <new>`). Leave the
     host-repo files uncommitted for the user to review; this framework
     never commits the host project repo.
   - Delete the temp reference directory. Keep
     `.ai/agent/.update-backup/` until the user confirms the result.

Switching harness is not an update either: the entry files are pure
framework output with nothing to merge, so `init-agent --harness <name>`
does it, writing the new set and retiring the old one. If the user asks
for a different harness, say that and stop.

A scaffold stamped `"profile": "large"` predates framework 5.22, which
removed the large profile. There is no reference to render for it, so
stop and report that: moving such a project across is a deliberate
re-init plus `/import-agent`, not an update.

With `dry-run`: do steps 1-3 as analysis only, print the table of what
would change, and stop without writing anything. The backup and the
pre-update commit are still worth doing.
