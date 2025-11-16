#!/usr/bin/env bash
#
# Common library functions for Bloginator shell scripts
#
# This library provides standardized logging, error handling, and utility
# functions used across all shell scripts in the project.
#
# Usage:
#   source "$(dirname "$0")/lib/common.sh"
#   init_script
#
# Dependencies:
#   - bash 4.0+
#   - tput (for colors)

# Color definitions
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_GRAY='\033[0;37m'
readonly COLOR_BOLD='\033[1m'

# Script state
SCRIPT_START_TIME=$(date +%s)
ERROR_COUNT=0
WARNING_COUNT=0

#######################################
# Initialize script with error handling
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
#######################################
init_script() {
    set -euo pipefail
    trap 'error_trap $? $LINENO' ERR
}

#######################################
# Error trap handler
# Globals:
#   ERROR_COUNT
# Arguments:
#   $1 - Exit code
#   $2 - Line number
# Returns:
#   Exit with error code
#######################################
error_trap() {
    local exit_code=$1
    local line_number=$2
    log_error "Script failed at line $line_number with exit code $exit_code"
    exit "$exit_code"
}

#######################################
# Log informational message
# Arguments:
#   $1 - Message to log
# Returns:
#   None
#######################################
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

#######################################
# Log success message
# Arguments:
#   $1 - Message to log
# Returns:
#   None
#######################################
log_success() {
    echo -e "${COLOR_GREEN}[✓]${COLOR_RESET} $1"
}

#######################################
# Log warning message
# Globals:
#   WARNING_COUNT
# Arguments:
#   $1 - Message to log
# Returns:
#   None
#######################################
log_warning() {
    ((WARNING_COUNT++))
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $1"
}

#######################################
# Log error message
# Globals:
#   ERROR_COUNT
# Arguments:
#   $1 - Message to log
# Returns:
#   None
#######################################
log_error() {
    ((ERROR_COUNT++))
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1" >&2
}

#######################################
# Log fatal error and exit
# Arguments:
#   $1 - Error message
# Returns:
#   Exit with code 1
#######################################
die() {
    log_error "$1"
    exit 1
}

#######################################
# Log debug message (only if DEBUG=1)
# Arguments:
#   $1 - Message to log
# Returns:
#   None
#######################################
log_debug() {
    if [[ "${DEBUG:-0}" == "1" ]]; then
        echo -e "${COLOR_GRAY}[DEBUG]${COLOR_RESET} $1"
    fi
}

#######################################
# Log section header
# Arguments:
#   $1 - Section title
# Returns:
#   None
#######################################
log_header() {
    echo ""
    echo -e "${COLOR_BOLD}${COLOR_CYAN}========================================${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}  $1${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}========================================${COLOR_RESET}"
    echo ""
}

#######################################
# Log subsection title
# Arguments:
#   $1 - Subsection title
# Returns:
#   None
#######################################
log_section() {
    echo ""
    echo -e "${COLOR_CYAN}▶ $1${COLOR_RESET}"
    echo ""
}

#######################################
# Require a command to be available
# Arguments:
#   $1 - Command name
#   $2 - Optional error message
# Returns:
#   Exit 1 if command not found
#######################################
require_command() {
    local cmd=$1
    local msg=${2:-"Required command '$cmd' not found. Please install it."}

    if ! command -v "$cmd" &> /dev/null; then
        die "$msg"
    fi
}

#######################################
# Require a file to exist
# Arguments:
#   $1 - File path
#   $2 - Optional error message
# Returns:
#   Exit 1 if file not found
#######################################
require_file() {
    local file=$1
    local msg=${2:-"Required file not found: $file"}

    if [[ ! -f "$file" ]]; then
        die "$msg"
    fi
}

#######################################
# Require a directory to exist
# Arguments:
#   $1 - Directory path
#   $2 - Optional error message
# Returns:
#   Exit 1 if directory not found
#######################################
require_directory() {
    local dir=$1
    local msg=${2:-"Required directory not found: $dir"}

    if [[ ! -d "$dir" ]]; then
        die "$msg"
    fi
}

#######################################
# Check if running on macOS
# Returns:
#   0 if macOS, 1 otherwise
#######################################
is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
}

#######################################
# Check if running on Linux
# Returns:
#   0 if Linux, 1 otherwise
#######################################
is_linux() {
    [[ "$OSTYPE" == "linux-gnu"* ]]
}

#######################################
# Print script execution summary
# Globals:
#   SCRIPT_START_TIME
#   ERROR_COUNT
#   WARNING_COUNT
# Returns:
#   None
#######################################
print_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - SCRIPT_START_TIME))

    echo ""
    log_header "Execution Summary"

    echo "Duration: ${duration}s"
    echo "Errors: $ERROR_COUNT"
    echo "Warnings: $WARNING_COUNT"

    if [[ $ERROR_COUNT -eq 0 ]]; then
        log_success "Script completed successfully!"
        return 0
    else
        log_error "Script completed with $ERROR_COUNT error(s)"
        return 1
    fi
}

#######################################
# Run command with logging
# Arguments:
#   $1 - Description of what's being done
#   $@ - Command to run
# Returns:
#   Exit code of command
#######################################
run_command() {
    local description=$1
    shift

    log_info "$description"
    log_debug "Running: $*"

    if "$@"; then
        log_success "$description completed"
        return 0
    else
        local exit_code=$?
        log_error "$description failed with exit code $exit_code"
        return $exit_code
    fi
}

#######################################
# Get repository root directory
# Returns:
#   Absolute path to repository root
#######################################
get_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || echo "."
}

#######################################
# Check if virtual environment is active
# Returns:
#   0 if active, 1 otherwise
#######################################
is_venv_active() {
    [[ -n "${VIRTUAL_ENV:-}" ]]
}

#######################################
# Activate virtual environment
# Arguments:
#   $1 - Path to virtual environment
# Returns:
#   None
#######################################
activate_venv() {
    local venv_path=$1

    if [[ ! -d "$venv_path" ]]; then
        die "Virtual environment not found: $venv_path"
    fi

    # shellcheck disable=SC1091
    source "$venv_path/bin/activate"
    log_success "Activated virtual environment: $venv_path"
}
