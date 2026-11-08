#!/usr/bin/env bash
# All reps of one harness in one herdr pane, one after another.
# Usage: BENCH_PROFILE=sh run.sh <harness> <pane-id> <first-rep> <last-rep>
set -uo pipefail
H=$1; P=$2; FIRST=$3; LAST=$4
HERE=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1090
. "$HERE/profiles/${BENCH_PROFILE:-sh}.env"
export EFFORT
B=${BENCH_DIR:-$HOME/tmp/harness-bench}
A="bench-${H}"
pane_agent() { herdr pane list --workspace "$HERDR_WORKSPACE_ID" | python3 -c \
  "import json,sys;print([p.get('agent') for p in json.load(sys.stdin)['result']['panes'] if p['pane_id']=='$P'][0])"; }
quit_agent() {
  for try in 1 2 3; do
    [ "$(pane_agent)" = None ] && return 0
    herdr agent send-keys "$A" ctrl+c >/dev/null 2>&1; sleep 1
    herdr agent send-keys "$A" ctrl+c >/dev/null 2>&1; sleep 2
    [ "$(pane_agent)" = None ] && return 0
    herdr pane send-text "$P" "/exit" >/dev/null 2>&1; sleep 1
    herdr pane send-keys "$P" enter >/dev/null 2>&1 || herdr agent send-keys "$A" enter >/dev/null 2>&1; sleep 4
  done
  [ "$(pane_agent)" = None ]
}
status() { herdr agent get "$A" 2>/dev/null | python3 -c \
  "import json,sys;print(json.load(sys.stdin)['result']['agent']['agent_status'])" 2>/dev/null; }

for N in $(seq "$FIRST" "$LAST"); do
  D=$("$HERE/setup.sh" "$H" "$N") || { echo "setup $H r$N failed"; exit 1; }
  LOG="$B/results/$H-r$N.log"
  echo "$(date +%T) setup $D" >> "$LOG"
  [ "$(pane_agent)" = None ] || quit_agent || { echo "agent still running in $P" >&2; exit 1; }
  herdr pane run "$P" "cd $D" >/dev/null; sleep 2
  case "$H" in
    claude)   herdr agent start "$A" --kind claude --pane "$P" --timeout 60000 \
                -- --model "$CC_SESSION" --effort "$EFFORT" --permission-mode auto >/dev/null 2>&1 ;;
    opencode) herdr agent start "$A" --kind opencode --pane "$P" --timeout 60000 \
                >/dev/null 2>&1 ;;
  esac
  sleep 3
  # Claude asks to trust each new run directory: accept it only for this run.
  if [ "$(status)" = blocked ]; then
    scr=$(herdr agent read "$A" --source visible)
    cwd=$(herdr pane list --workspace "$HERDR_WORKSPACE_ID" | python3 -c \
      "import json,sys;print([p.get('foreground_cwd') for p in json.load(sys.stdin)['result']['panes'] if p['pane_id']=='$P'][0])")
    if echo "$scr" | grep -q "trust this folder" && [ "$cwd" = "$D" ]; then
      herdr agent send-keys "$A" down >/dev/null; sleep 1
      if herdr agent read "$A" --source visible | grep -q '❯ Yes, I trust this folder'; then
        herdr agent send-keys "$A" enter >/dev/null; sleep 6
        echo "$(date +%T) trusted $D" >> "$LOG"
      fi
    fi
  fi
  [ "$(status)" = blocked ] && { echo "$(date +%T) STOP: blocked at start" >> "$LOG"; exit 1; }

  T0=$(date +%s)
  python3 "$HERE/drive.py" "$A" "$H" "$D" "$LOG"; RC=$?
  echo "$(date +%T) driver rc=$RC wall=$(( $(date +%s) - T0 ))s" >> "$LOG"

  # Quit the agent and verify the pane is a shell again: a session left
  # running would swallow the next rep's cd and be driven instead.
  quit_agent || { echo "$(date +%T) STOP: agent did not quit" >> "$LOG"; exit 1; }
  python3 "$HERE/metrics.py" "$H" "$D" > "$B/results/$H-r$N.metrics.json" 2>>"$LOG"
  python3 "$HERE/grade.py" "$D" > "$B/results/$H-r$N.grade.json" 2>>"$LOG"
  [ $RC -ne 0 ] && { echo "$(date +%T) halted, see log" >> "$LOG"; exit 1; }
done
echo "done $H r$FIRST..r$LAST"
