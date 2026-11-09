#!/usr/bin/env bash
# One benchmark run directory: satty at the pinned commit, the framework
# scaffold for one harness, the canonical tasks, and the profile's models.
# Usage: BENCH_PROFILE=sh setup.sh <harness> <rep>  (see tests/harness-benchmark.md)
set -euo pipefail
H=$1; N=$2
HERE=$(cd "$(dirname "$0")" && pwd)
FW=$(cd "$HERE/../.." && pwd)
# shellcheck disable=SC1090
. "$HERE/profiles/${BENCH_PROFILE:-sh}.env"
B=${BENCH_DIR:-$HOME/tmp/harness-bench}; D=$B/runs/$H-r$N
[ -e "$D" ] && { echo "$D exists" >&2; exit 1; }
mkdir -p "$B/runs" "$B/results"
[ -d "$B/satty.git" ] || git clone -q --mirror https://github.com/gabm/Satty "$B/satty.git"

git clone -q "$B/satty.git" "$D"
cd "$D"
git checkout -q f578432
git switch -q -c bench
# No remote: a task must never push, least of all into the local mirror.
git remote remove origin

python3 "$FW/init_agent.py" --harness "$H" -y --name satty \
  --description "GTK4 screenshot annotator" >/dev/null
cp -R "$HERE"/tasks/* .ai/tasks/
git -C .ai add -A
git -C .ai commit -q -m "bench: canonical tasks"

# The profile's worker and reviewer, written exactly as the former /agent-models
# writes them: one model: line after description: in each agent file.
# Effort: every role inherits the supervisor's. Claude Code sub-agents
# follow the session when their agent file has no effort: line; OpenCode
# sub-agents do not, so the effort is written as the variant.
case "$H" in
  claude)   A=.claude/agents;   W=$CC_WORKER; R=$CC_REVIEWER ;;
  opencode) A=.opencode/agents; W="$OC_WORKER#$EFFORT"; R="$OC_REVIEWER#$EFFORT"
            printf '{"model": "%s#%s"}\n' "$OC_SESSION" "$EFFORT" > opencode.json
            echo opencode.json >> .git/info/exclude ;;
  *) echo "unknown harness $H" >&2; exit 1 ;;
esac
python3 - "$A/worker.md" "$W" "$A/reviewer.md" "$R" <<'PY'
import sys
args = sys.argv[1:]
for path, model in zip(args[::2], args[1::2]):
    lines = open(path).read().split("\n")
    end = lines.index("---", 1)
    head = [l for l in lines[:end] if not l.startswith("model:")]
    i = next(k for k, l in enumerate(head) if l.startswith("description:"))
    head.insert(i + 1, f"model: {model}")
    open(path, "w").write("\n".join(head + lines[end:]))
PY
if [ "$H" = claude ]; then
  # Drop any effort: line (the framework's reviewer ships effort: high).
  sed -i '' '/^effort:/d' "$A/worker.md" "$A/reviewer.md"
fi
git add -A >/dev/null
git -c user.name=bench -c user.email=bench@local commit -q -m "bench: scaffold $H"
echo "$D"
