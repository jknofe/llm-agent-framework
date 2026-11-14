---
description: Show the sub-agent models (worker and reviewer of /task do, updater of /framework-update) and print the command that sets them
---
Show the models of the two sub-agents of `/task do`, `worker` and
`reviewer`, and of the optional `updater` that `/framework-update` hands
the update to, and the command that sets them. Arguments:
${arg_ticket}

${models_run}

Do not run the command it prints, do not edit an agent file, and do not
suggest or pick a model name, from the list or otherwise: the choice is the user's, and the printed
command tests each name as a sub-agent before it saves it.
