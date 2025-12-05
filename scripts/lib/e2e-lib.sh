#!/usr/bin/env bash
################################################################################
# Shared Library for E2E Workflow Scripts
################################################################################
# PURPOSE: Common configuration, utilities, and helper functions
# USAGE: source scripts/lib/e2e-lib.sh

# Exit on error, undefined variables, pipe failures
set -euo pipefail

################################################################################
# Configuration
################################################################################

# Detect script root (supports being sourced from different locations)
if [ -n "${BASH_SOURCE[0]:-}" ]; then
    E2E_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$E2E_SCRIPT_DIR/.." && pwd)"
else
    PROJECT_ROOT="$(pwd)"
fi

# Source .env if it exists to pick up BLOGINATOR_* environment variables
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/.env"
fi

# Set defaults for base directory
BLOGINATOR_DATA_DIR="${BLOGINATOR_DATA_DIR:-.bloginator}"

# Build paths relative to BLOGINATOR_DATA_DIR unless absolute paths given
if [[ "${BLOGINATOR_CHROMA_DIR:-}" != /* ]]; then
    BLOGINATOR_CHROMA_DIR="${BLOGINATOR_DATA_DIR}/${BLOGINATOR_CHROMA_DIR:-chroma}"
fi
if [[ "${BLOGINATOR_OUTPUT_DIR:-}" != /* ]]; then
    BLOGINATOR_OUTPUT_DIR="${BLOGINATOR_DATA_DIR}/${BLOGINATOR_OUTPUT_DIR:-output}"
fi

# Paths (using config from .env with fallbacks)
CORPUS_CONFIG="${CORPUS_CONFIG:-corpus/corpus.yaml}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/${BLOGINATOR_OUTPUT_DIR}}"
EXTRACTED_DIR="${OUTPUT_DIR}/extracted"
INDEX_DIR="${INDEX_DIR:-${PROJECT_ROOT}/${BLOGINATOR_CHROMA_DIR}}"
GENERATED_DIR="${OUTPUT_DIR}/generated"
STATE_FILE="${OUTPUT_DIR}/.run-e2e-state"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
LIGHT_GRAY='\033[0;37m'
DARK_GRAY='\033[1;30m'
BRIGHT_WHITE='\033[1;37m'
BRIGHT_CYAN='\033[1;36m'
BRIGHT_YELLOW='\033[1;33m'
DIM='\033[2m'
NC='\033[0m' # No Color

################################################################################
# Timer Functions
################################################################################

# Timer state
SCRIPT_START_TIME=$(date +%s)
TIMER_PID=""

# Update timer display in top-right corner (yellow on black)
update_timer() {
    local start_time="$1"
    while true; do
        local cols elapsed hours minutes seconds timer_text timer_col
        cols=$(tput cols 2>/dev/null || echo 80)
        elapsed=$(($(date +%s) - start_time))
        hours=$((elapsed / 3600))
        minutes=$(((elapsed % 3600) / 60))
        seconds=$((elapsed % 60))
        printf -v timer_text "[%02d:%02d:%02d]" "$hours" "$minutes" "$seconds"
        timer_col=$((cols - ${#timer_text}))
        echo -ne "\033[s\033[1;${timer_col}H\033[33;40m${timer_text}\033[0m\033[u"
        sleep 1
    done
}

# Start background timer display
start_timer() {
    update_timer "$SCRIPT_START_TIME" &
    TIMER_PID=$!
}

# Stop background timer display
stop_timer() {
    [[ -n "$TIMER_PID" ]] && { kill "$TIMER_PID" 2>/dev/null || true; wait "$TIMER_PID" 2>/dev/null || true; }
    TIMER_PID=""
}

################################################################################
# State Management Functions
################################################################################

save_state() {
    local step_name="$1"
    mkdir -p "$OUTPUT_DIR"
    echo "$step_name:$(date +%s)" >> "$STATE_FILE"
    echo "$step_name" >> "$STATE_FILE.completed"
}

is_step_completed() {
    local step_name="$1"
    [ -f "$STATE_FILE.completed" ] && grep -q "^$step_name$" "$STATE_FILE.completed"
}

clear_state() {
    rm -f "$STATE_FILE" "$STATE_FILE.completed"
}

show_resume_status() {
    if [ -f "$STATE_FILE.completed" ]; then
        echo ""
        print_info "Previous run detected. Completed steps:"
        while read -r step; do
            print_success "$step"
        done < "$STATE_FILE.completed"
        echo ""
    fi
}

################################################################################
# Output Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${MAGENTA}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

################################################################################
# Command Execution Helpers
################################################################################

run_command() {
    local description="$1"
    local command="$2"
    local verbose="${3:-${VERBOSE:-false}}"

    print_step "$description"

    if $verbose; then
        if eval "$command"; then
            print_success "$description completed"
        else
            print_error "$description failed"
            exit 1
        fi
    else
        if eval "$command" > /dev/null 2>&1; then
            print_success "$description completed"
        else
            print_error "$description failed"
            echo "Run with --verbose to see error details"
            exit 1
        fi
    fi
}

################################################################################
# Ollama Check Functions
################################################################################

check_ollama_service() {
    local host="${1:-http://localhost:11434}"

    if curl -s -f "${host}/api/tags" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_ollama_model() {
    local host="${1:-http://localhost:11434}"
    local model="${2:-mixtral:8x7b}"

    # Strip tag suffix if present (e.g., mixtral:8x7b -> mixtral)
    local model_name="${model%%:*}"

    if curl -s -f "${host}/api/tags" | grep -q "\"name\":\"${model}\""; then
        return 0
    elif curl -s -f "${host}/api/tags" | grep -q "\"name\":\"${model_name}:"; then
        # Model exists with different tag
        return 0
    else
        return 1
    fi
}

list_ollama_models() {
    local host="${1:-http://localhost:11434}"
    curl -s "${host}/api/tags" | grep -o '"name":"[^"]*"' | cut -d'"' -f4
}

################################################################################
# Trap Handler
################################################################################

cleanup_on_interrupt() {
    echo -e "\n${RED}✗ E2E workflow interrupted${NC}"
    exit 1
}

# Set trap for cleanup
trap cleanup_on_interrupt INT TERM
