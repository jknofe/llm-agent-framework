#!/usr/bin/env bash
# Installer for llm-agent-framework.
#
# Puts the framework into $LLM_AGENT_HOME (default ~/.llm-agent-framework)
# and adds an `init-agent` function to your shell rc file. The function
# pulls the latest version from git (if a remote is configured) and then
# runs init_agent.py with your arguments.
#
# Usage:
#   ./install.sh                                  # from a local checkout
#   LLM_AGENT_REPO_URL=<url> bash install.sh      # clone first, then install
#
# Idempotent: re-running replaces the managed rc block.
set -euo pipefail

INSTALL_DIR="${LLM_AGENT_HOME:-$HOME/.llm-agent-framework}"
REPO_URL="${LLM_AGENT_REPO_URL:-}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- locate or fetch the framework -----------------------------------------
if [ -f "$script_dir/init_agent.py" ]; then
    # Running from a checkout: use it in place, no copy.
    INSTALL_DIR="$script_dir"
elif [ -f "$INSTALL_DIR/init_agent.py" ]; then
    : # already installed, just refresh the rc block
elif [ -n "$REPO_URL" ]; then
    git clone "$REPO_URL" "$INSTALL_DIR"
else
    echo "error: init_agent.py not found." >&2
    echo "Run install.sh from a checkout, or set LLM_AGENT_REPO_URL to clone one." >&2
    exit 1
fi

# --- pick the rc file -------------------------------------------------------
case "${SHELL##*/}" in
    zsh) rc_file="${ZDOTDIR:-$HOME}/.zshrc" ;;
    *)   rc_file="$HOME/.bashrc" ;;
esac
rc_file="${LLM_AGENT_RC_FILE:-$rc_file}"

# --- write the managed block (replace if present) ---------------------------
begin_marker="# >>> llm-agent-framework >>>"
end_marker="# <<< llm-agent-framework <<<"

block="$begin_marker
export LLM_AGENT_HOME=\"$INSTALL_DIR\"
init-agent() {
    if git -C \"\$LLM_AGENT_HOME\" remote get-url origin >/dev/null 2>&1; then
        git -C \"\$LLM_AGENT_HOME\" pull --ff-only --quiet \\
            || echo \"init-agent: git pull failed, using local copy\" >&2
    fi
    python3 \"\$LLM_AGENT_HOME/init_agent.py\" \"\$@\"
}
$end_marker"

touch "$rc_file"
if grep -qF "$begin_marker" "$rc_file"; then
    tmp="$(mktemp)"
    awk -v b="$begin_marker" -v e="$end_marker" '
        $0 == b {skip=1; next}
        $0 == e {skip=0; next}
        !skip
    ' "$rc_file" >"$tmp"
    mv "$tmp" "$rc_file"
fi
printf '\n%s\n' "$block" >>"$rc_file"

echo "installed: init-agent -> $INSTALL_DIR/init_agent.py"
echo "rc file:   $rc_file"
echo "Open a new shell or run: source $rc_file"
echo "Then run init-agent in your project root and answer the prompts."
