---
description: Store a ticket as markdown in the .ai/tickets/ inbox without planning it
---
Add a ticket to the inbox. Ticket id, title, description: ${arg_ticket}

1. Build the filename `<ID>-<slug>.md` from id and title, e.g.
   `JIRA1234-do-this-and-that.md`.
2. Write `.ai/tickets/<ID>-<slug>.md` with frontmatter `id`, `title`,
   `status: new`, `created: <today>` and the description as body.
   Ask for a one-line description if none was given.
3. Commit the `.ai` repo (`add-ticket: <ID>`).

Do not start planning or implementing; that begins with /plan <ID>,
which moves the ticket into `.ai/knowledgebase/tasks/<ID>/` and
promotes its status from `new` to `planned`.
