#!/bin/bash
# Dexter Task Runner
# Usage: ./scripts/run-task.sh "Task Title" [--repo owner/repo] [--context "extra context"] [--task-id ID]
#
# This script:
# 1. Parses task details
# 2. Spawns a Codex agent in background
# 3. Updates progress.json as work happens
# 4. Commits and pushes after each step
# 5. Creates a PR when done
# 6. Outputs Telegram notification

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
TASK_TITLE=""
REPO=""
CONTEXT=""
TASK_ID=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO="$2"
            shift 2
            ;;
        --context)
            CONTEXT="$2"
            shift 2
            ;;
        --task-id)
            TASK_ID="$2"
            shift 2
            ;;
        *)
            if [[ -z "$TASK_TITLE" ]]; then
                TASK_TITLE="$1"
            fi
            shift
            ;;
    esac
done

# Validate
if [[ -z "$TASK_TITLE" ]]; then
    echo -e "${RED}Error: Task title is required${NC}"
    echo "Usage: ./scripts/run-task.sh \"Task Title\" [--repo owner/repo] [--context \"context\"] [--task-id ID]"
    exit 1
fi

# Generate task ID if not provided
if [[ -z "$TASK_ID" ]]; then
    TASK_ID="task-$(date +%s)-$(head -c 4 /dev/urandom | xxd -p)"
fi

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  DEXTER TASK RUNNER${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Task:${NC} $TASK_TITLE"
echo -e "${GREEN}ID:${NC}   $TASK_ID"
[[ -n "$REPO" ]] && echo -e "${GREEN}Repo:${NC} $REPO"
[[ -n "$CONTEXT" ]] && echo -e "${GREEN}Context:${NC} $CONTEXT"
echo ""

# Run the orchestrator
python3 "$SCRIPT_DIR/orchestrator.py" \
    --task-id "$TASK_ID" \
    --title "$TASK_TITLE" \
    ${REPO:+--repo "$REPO"} \
    ${CONTEXT:+--context "$CONTEXT"}
