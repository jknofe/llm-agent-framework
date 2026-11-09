---
description: Show the worker and reviewer models of /task do and print the command that sets them
---
Show the models of the two sub-agents of `/task do`, `worker` and
`reviewer`, and the command that sets them. Arguments:
${arg_ticket}

Run `python3 ${tools_dir}/tasks.py models` followed by the arguments as
given (`worker=<model>`, `reviewer=<model>`, or the two names in that
order; none is fine), and reply with its complete output, verbatim, and
nothing else.

Do not run the command it prints, do not edit an agent file, and do not
suggest or pick a model name: the choice is the user's, and the printed
command tests each name as a sub-agent before it saves it.
