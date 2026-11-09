---
description: Show or set the models of the worker and reviewer sub-agents that /task do uses
---
Show or set which model the two sub-agents of `/task do` run on in this
project. Arguments: ${arg_models}

The `worker` works a delegated task; the `reviewer` is its review gate.
Each is an agent file, and a `model:` line in its frontmatter pins its
model:
- worker: `${worker_file}`
- reviewer: `${reviewer_file}`
Without a `model:` line, ${unset_note}

1. No arguments: show each agent's current `model:` value, or `not set`
   and what that means here, list the model names this harness accepts
   (below), and ask which to set. Change nothing until the user answers.
2. `worker=<model>`, `reviewer=<model>`, or both: check each name against
   the accepted names below; report an unknown one and do not write it.
   Then change only the `model:` line in the named file's frontmatter:
   replace it, or add it after `description:`. `default` removes the line.
   Touch nothing else in the file.
3. Read the frontmatter back and report each change, old to new.
   ${verify_note}

Keep the reviewer at least as strong as the worker: it is the gate that
catches what a cheaper worker gets wrong. If the user asks for the
reverse, say so once, then do as asked.

Effort is not set here: both sub-agents think at the session's effort
level, the supervisor's, on every harness.

The two files belong to the framework; `/framework-update` keeps a
`model:` line in them as the user's choice.

Accepted model names:
${model_names}
