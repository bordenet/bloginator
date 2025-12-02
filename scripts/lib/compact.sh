#!/usr/bin/env bash

################################################################################
# Compact Output Library - Vertical Real Estate Optimized
################################################################################
# PURPOSE: Minimal vertical space usage with in-place updates and timer
# USAGE: source "$(dirname "${BASH_SOURCE[0]}")/lib/compact.sh"
################################################################################

# ANSI escape sequences
readonly ANSI_CLEAR_LINE='\033[2K'
# shellcheck disable=SC2034  # May be used by scripts sourcing this library
readonly ANSI_CURSOR_UP='\033[1A'
readonly ANSI_CURSOR_SAVE='\033[s'
readonly ANSI_CURSOR_RESTORE='\033[u'
readonly ANSI_HIDE_CURSOR='\033[?25l'
readonly ANSI_SHOW_CURSOR='\033[?25h'
# shellcheck disable=SC2034  # May be used by scripts sourcing this library
readonly ANSI_MOVE_TO_COL='\033[%dG'

# Colors
readonly C_RED='\033[0;31m'
readonly C_GREEN='\033[0;32m'
readonly C_YELLOW='\033[1;33m'
readonly C_BLUE='\033[0;34m'
readonly C_CYAN='\033[0;36m'
readonly C_GRAY='\033[0;90m'
readonly C_BOLD='\033[1m'
readonly C_RESET='\033[0m'

# Symbols
readonly SYM_OK="${C_GREEN}✓${C_RESET}"
readonly SYM_FAIL="${C_RED}✗${C_RESET}"
readonly SYM_WARN="${C_YELLOW}⚠${C_RESET}"
readonly SYM_RUN="${C_BLUE}▸${C_RESET}"

# Global state
SCRIPT_START_TIME=$(date +%s)
CURRENT_TASK=""
VERBOSE=${VERBOSE:-0}

################################################################################
# Timer Functions
################################################################################

# Get elapsed time in HH:MM:SS format
get_elapsed_time() {
    local now
    now=$(date +%s)
    local elapsed=$((now - SCRIPT_START_TIME))
    printf "%02d:%02d:%02d" $((elapsed/3600)) $(((elapsed%3600)/60)) $((elapsed%60))
}

# Print timer in top-right corner
print_timer() {
    # Skip timer if not a TTY (e.g., piped output)
    [[ ! -t 1 ]] && return 0

    local cols
    cols=$(tput cols 2>/dev/null || echo 80)
    local timer
    timer=$(get_elapsed_time)
    local timer_text="${C_GRAY}[${timer}]${C_RESET}"
    local timer_len=11  # Length of [HH:MM:SS] with ANSI codes stripped
    local pos=$((cols - timer_len))

    # Save cursor, move to position, print timer, restore cursor
    printf "\033[s"
    printf "\033[%dG" "$pos"  # Move to column
    printf "%b" "${timer_text}"
    printf "\033[u"
}

# Update status line in place
update_status() {
    local symbol="$1"
    local message="$2"

    # Clear line and print status with timer
    printf "\r\033[2K"
    printf "%b %s" "${symbol}" "${message}"
    print_timer
}

# Finalize status line (move to next line)
finalize_status() {
    printf "\n"
}

# Skip task (already done)
task_skip() {
    local message="${1:-$CURRENT_TASK}"
    update_status "${C_GRAY}○${C_RESET}" "${message} ${C_GRAY}(cached)${C_RESET}"
    finalize_status
}

################################################################################
# Compact Logging Functions
################################################################################

# Start a task (shows spinner/progress)
task_start() {
    CURRENT_TASK="$1"
    update_status "${SYM_RUN}" "${CURRENT_TASK}..."

    if [[ $VERBOSE -eq 1 ]]; then
        finalize_status
    fi
}

# Complete task successfully
task_ok() {
    local message="${1:-$CURRENT_TASK}"
    update_status "${SYM_OK}" "${message}"
    finalize_status
}

# Task failed
task_fail() {
    local message="${1:-$CURRENT_TASK}"
    update_status "${SYM_FAIL}" "${message}"
    finalize_status
}

# Task warning
task_warn() {
    local message="${1:-$CURRENT_TASK}"
    update_status "${SYM_WARN}" "${message}"
    finalize_status
}

# Verbose-only output
verbose() {
    if [[ $VERBOSE -eq 1 ]]; then
        echo -e "${C_GRAY}  $*${C_RESET}"
    fi
}

################################################################################
# Header/Section Functions
################################################################################

# Print compact header (single line)
print_header() {
    echo -e "${C_CYAN}${C_BOLD}$*${C_RESET}"
}

# Print section (minimal)
print_section() {
    echo -e "${C_BLUE}▸${C_RESET} ${C_BOLD}$*${C_RESET}"
}

################################################################################
# Cleanup
################################################################################

# Show cursor on exit
cleanup_display() {
    printf "\033[?25h"
}

trap cleanup_display EXIT

# Hide cursor for cleaner updates
printf "\033[?25l"
