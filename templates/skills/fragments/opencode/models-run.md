The harness ran `python3 ${tools_dir}/tasks.py models --list` for you,
without the arguments; its output is here:

!`python3 ${tools_dir}/tasks.py models --list --exit-zero`

With no arguments above, reply with that output, complete, verbatim, and
nothing else. With arguments, or if the output is not the script's (a
notice that shell commands are disabled, an error), run
`python3 ${tools_dir}/tasks.py models --list --exit-zero` followed by the
arguments as given (`worker=<model>`, `reviewer=<model>`,
`updater=<model>`, or the names in that order) and reply with its
complete output, verbatim, and nothing else. `--list` adds the models this
harness or its backend can name, where it can list them.