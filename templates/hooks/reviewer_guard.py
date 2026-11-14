#!/usr/bin/env python3
"""Pre-tool hook of the `reviewer` sub-agent (Claude Code): it reads, it does
not run.

The reviewer's body says to use the shell only to read. This hook makes it
so: it is declared in the reviewer's own frontmatter (`hooks`, `PreToolUse`,
matcher `Bash`), so it runs only while the reviewer does. A shell command
outside the read-only list is blocked, exit 2 with the reason on stderr, and
the reason tells the reviewer to report what it could not check.

Allowed: `git diff|show|log|status` (optionally `git -C <dir> ...`),
`grep`, `rg`, `cat`, `ls`, `head`, `tail`, `wc`,
`gh pr view|diff|checks`, `gh run view`, behind
a leading `rtk` or `rtk proxy` as git_guard.py accepts them. A compound
command (`&&`, `||`, `;`, `|`) passes only when every part is allowed.
Blocked whatever the command: a redirect to a file, a command or process
substitution, `--output` and `--pre`, which make `git` and `rg` write or run.

Fails open like git_guard.py: input that is not a JSON tool call with a
string `command`, or a line the shell lexer cannot parse, passes.
"""
import json
import shlex
import sys

# The same list as `const.REVIEWER_SHELL`, which the OpenCode reviewer's
# permission rules are written from; tests/test_reviewer_guard.py keeps the
# two equal.
ALLOWED = ["git diff", "git show", "git log", "git status", "grep", "rg",
           "cat", "ls", "head", "tail", "wc", "gh pr view", "gh pr diff", "gh pr checks",
           "gh run view"]

SEPARATORS = ("&&", "||", ";", "|")
WRITERS = ("--output", "--pre")


def tokens(command):
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    return list(lex)


def segments(toks):
    out, cur = [], []
    for t in toks:
        if t in SEPARATORS:
            out.append(cur)
            cur = []
        else:
            cur.append(t)
    out.append(cur)
    return out


def unwrap(seg):
    """`rtk <cmd>`, `rtk proxy <cmd>`, `rtk run "<line>"` (whose string is a
    shell line of its own) and `rtk read <file>`, RTK's `cat`."""
    if not seg or seg[0] != "rtk":
        return [seg]
    rest = [w for w in seg[1:] if w not in ("--ultra-compact", "--skip-env")]
    if rest[:1] == ["proxy"]:
        return [rest[1:]]
    if rest[:1] == ["run"]:
        rest = [w for w in rest[1:] if w not in ("-c", "--command")]
        return [s for part in segments(tokens(" ".join(rest)))
                for s in unwrap(part)]
    if rest[:1] == ["read"]:
        return [["cat"] + rest[1:]]
    return [rest]


def allowed(seg):
    if not seg:
        return True
    words = list(seg)
    if words[0] == "git" and words[1:2] == ["-C"] and len(words) > 3:
        words = ["git"] + words[3:]
    for entry in ALLOWED:
        head = entry.split()
        if words[:len(head)] == head:
            return not any(w == f or w.startswith(f + "=")
                           for w in words for f in WRITERS)
    return False


PUNCT = set("();<>|&")


def clean(toks):
    """The tokens without the two redirects the reviewer may keep, stderr
    folded into stdout (`2>&1`) or thrown away (`2>/dev/null`), or the
    reason this line is not read-only: any other redirect, a subshell or a
    background `&`, an operator the splitter does not know (`|&`)."""
    out, i = [], 0
    while i < len(toks):
        t = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        if t in SEPARATORS:
            out.append(t)
        elif t == ">&" and nxt.isdigit() or t == ">" and nxt == "/dev/null":
            i += 1
        elif t and set(t) <= PUNCT:
            return None, f"`{t}`"
        else:
            out.append(t)
        i += 1
    return out, None


def check(command):
    """The first reason this command is not read-only, or None."""
    if "`" in command or "$(" in command or "<(" in command:
        return "a command or process substitution"
    toks, reason = clean(tokens(command.replace("\n", " ; ")))
    if reason:
        return reason
    for seg in segments(toks):
        for part in unwrap(seg):
            if not allowed(part):
                return "`" + " ".join(part[:3]) + "`"
    return None


def block(reason):
    msg = (f"Blocked: {reason} is outside the reviewer's read-only shell "
           "(git diff|show|log|status, grep, rg, cat, ls, head, tail, wc, gh pr "
           "view|diff|checks, gh run view). A review reads and runs "
           "nothing: report what you could not check instead of running "
           "it.")
    print(json.dumps({
        "permissionDecision": "deny",
        "permissionDecisionReason": msg,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": msg,
        },
    }))
    print(msg, file=sys.stderr)
    sys.exit(2)


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(data, dict):
    sys.exit(0)

tool_input = data.get("tool_input") or data.get("toolArgs") or {}
command = tool_input.get("command") if isinstance(tool_input, dict) else None
if not isinstance(command, str):
    sys.exit(0)
try:
    reason = check(command)
except ValueError:
    sys.exit(0)
if reason:
    block(reason)
sys.exit(0)
