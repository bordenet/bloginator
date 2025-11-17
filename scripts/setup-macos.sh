#!/usr/bin/env bash

################################################################################
# Bloginator macOS Development Setup
################################################################################
# PURPOSE: Set up Bloginator development environment on macOS
#   - Installs Homebrew and required system dependencies
#   - Detects and installs compatible Python version (3.10-3.13)
#   - Creates Python virtual environment with project dependencies
#   - Configures pre-commit hooks for code quality
#
# USAGE:
#   ./scripts/setup-macos.sh [OPTIONS]
#   ./scripts/setup-macos.sh --help
#
# OPTIONS:
#   -y, --yes       Auto-confirm all prompts
#   -v, --verbose   Show detailed output
#   -h, --help      Display help message
#
# EXAMPLES:
#   ./scripts/setup-macos.sh            # Interactive setup
#   ./scripts/setup-macos.sh -y         # Non-interactive
#   ./scripts/setup-macos.sh -v -y      # Verbose non-interactive
#
# DEPENDENCIES:
#   - macOS (tested on Apple Silicon)
#   - curl (for Homebrew installation)
################################################################################

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
init_script

################################################################################
# Constants
################################################################################

readonly VENV_DIR="${REPO_ROOT}/.venv"
readonly PYTHON_VERSION="3.13"
readonly REQUIRED_PYTHON_MIN="3.10"
readonly REQUIRED_PYTHON_MAX="3.14"  # Exclusive

AUTO_CONFIRM=false
VERBOSE=false
PYTHON_CMD=""

# Timer variables
SCRIPT_START_TIME=$(date +%s)
TIMER_PID=""

################################################################################
# Timer Functions
################################################################################

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

start_timer() {
    update_timer "$SCRIPT_START_TIME" &
    TIMER_PID=$!
}

stop_timer() {
    [[ -n "$TIMER_PID" ]] && { kill "$TIMER_PID" 2>/dev/null || true; wait "$TIMER_PID" 2>/dev/null || true; }
}

trap stop_timer EXIT

################################################################################
# Output Functions
################################################################################

log_step() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo ""; echo "▶ $1"; echo ""
    else
        echo -ne "\r\033[K▶ $1"
    fi
}

log_step_done() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo "[✓] $1"
    else
        echo -e "\r\033[K▶ $1\t\t[✓]"
    fi
}

log_info_verbose() {
    [[ "$VERBOSE" != "true" ]] && return 0
    log_info "$@"
}

################################################################################
# Argument Parsing
################################################################################

show_help() {
    cat << 'EOF'
NAME
    setup-macos.sh - Set up Bloginator development environment

SYNOPSIS
    ./scripts/setup-macos.sh [OPTIONS]

DESCRIPTION
    Sets up development environment including Homebrew, Python 3.10-3.13,
    Git, development tools, virtual environment, and dependencies.

OPTIONS
    -y, --yes       Auto-confirm all prompts
    -v, --verbose   Show detailed output
    -h, --help      Display this help

EXAMPLES
    ./scripts/setup-macos.sh        # Interactive setup
    ./scripts/setup-macos.sh -y     # Non-interactive
    ./scripts/setup-macos.sh -v -y  # Verbose non-interactive
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes) AUTO_CONFIRM=true; shift ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -h|--help) show_help; exit 0 ;;
            *) die "Unknown option: $1. Use --help for usage." ;;
        esac
    done
}

################################################################################
# Helper Functions
################################################################################

find_compatible_python() {
    for version in 3.13 3.12 3.11 3.10; do
        if command -v "python${version}" &>/dev/null; then
            local py_version major_minor
            py_version=$("python${version}" --version 2>&1 | awk '{print $2}')
            major_minor=$(echo "$py_version" | cut -d. -f1,2)

            if [[ $(printf '%s\n' "${major_minor}" "${REQUIRED_PYTHON_MIN}" | sort -V | head -n1) == "${REQUIRED_PYTHON_MIN}" ]] && \
               [[ $(printf '%s\n' "${major_minor}" "${REQUIRED_PYTHON_MAX}" | sort -V | tail -n1) != "${major_minor}" ]]; then
                echo "python${version}"
                return 0
            fi
        fi
    done
    return 1
}

################################################################################
# Setup Functions
################################################################################

check_macos() {
    log_step "Checking system requirements"
    is_macos || die "This script requires macOS. Current OS: $OSTYPE"
    log_info_verbose "macOS $(sw_vers -productVersion)"
    log_step_done "System requirements"
}

install_homebrew() {
    log_step "Installing Homebrew"

    if command -v brew &>/dev/null; then
        log_info_verbose "Homebrew $(brew --version | head -n1 | awk '{print $2}')"
        if [[ "${HOMEBREW_NO_AUTO_UPDATE:-}" != "1" ]]; then
            confirm "Update Homebrew?" "n" && run_quiet brew update
        fi
    else
        confirm "Install Homebrew?" "y" || die "Homebrew required"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    log_step_done "Homebrew"
}

install_python() {
    log_step "Installing Python"

    if command -v python3 &>/dev/null; then
        local python_version major_minor is_too_old is_too_new
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
        major_minor=$(echo "$python_version" | cut -d. -f1,2)
        log_info_verbose "Found python3: $python_version"

        is_too_old=false; is_too_new=false
        [[ $(printf '%s\n' "${major_minor}" "${REQUIRED_PYTHON_MIN}" | sort -V | head -n1) != "${REQUIRED_PYTHON_MIN}" ]] && is_too_old=true
        [[ $(printf '%s\n' "${major_minor}" "${REQUIRED_PYTHON_MAX}" | sort -V | tail -n1) == "${major_minor}" ]] && is_too_new=true

        if [[ "$is_too_old" == "false" ]] && [[ "$is_too_new" == "false" ]]; then
            PYTHON_CMD="python3"
            log_info_verbose "Python $python_version is compatible"
            log_step_done "Python $python_version"
            return 0
        fi

        [[ "$is_too_new" == "true" ]] && log_info_verbose "Python $python_version too new (need <$REQUIRED_PYTHON_MAX)"
        [[ "$is_too_old" == "true" ]] && log_info_verbose "Python $python_version too old (need >=$REQUIRED_PYTHON_MIN)"
    fi

    log_info_verbose "Searching for compatible Python..."
    if PYTHON_CMD=$(find_compatible_python); then
        local found_version
        found_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
        log_info_verbose "Found $PYTHON_CMD ($found_version)"
        log_step_done "Python $found_version"
        return 0
    fi

    log_info_verbose "Installing python@$PYTHON_VERSION..."
    confirm "Install Python $PYTHON_VERSION via Homebrew?" "y" || die "Compatible Python required"
    run_quiet brew install "python@${PYTHON_VERSION}"
    PYTHON_CMD="python${PYTHON_VERSION}"
    log_step_done "Python $PYTHON_VERSION (installed)"
}

install_git() {
    log_step "Installing Git"
    if command -v git &>/dev/null; then
        log_info_verbose "Git $(git --version | awk '{print $3}')"
    else
        confirm "Install Git?" "y" || die "Git required"
        run_quiet brew install git
    fi
    log_step_done "Git"
}

install_dev_tools() {
    log_step "Installing development tools"
    command -v gitleaks &>/dev/null || { confirm "Install gitleaks?" "y" && run_quiet brew install gitleaks; }
    command -v pre-commit &>/dev/null || { confirm "Install pre-commit?" "y" && run_quiet brew install pre-commit; }
    log_step_done "Development tools"
}

setup_virtualenv() {
    log_step "Setting up Python virtual environment"

    if [[ -d "$VENV_DIR" ]]; then
        if confirm "Recreate virtual environment?" "n"; then
            rm -rf "$VENV_DIR"
        else
            log_step_done "Virtual environment (existing)"
            return 0
        fi
    fi

    log_info_verbose "Creating venv with $PYTHON_CMD..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    log_info_verbose "Upgrading pip..."
    run_quiet python -m pip install --upgrade pip
    log_step_done "Virtual environment"
}

install_python_dependencies() {
    log_step "Installing Python dependencies"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    log_info_verbose "Installing bloginator[dev]..."
    python -m pip install -e ".[dev]" > /dev/null 2>&1 || die "Failed to install dependencies"
    log_step_done "Python dependencies"
}

install_pre_commit_hooks() {
    log_step "Installing pre-commit hooks"
    if command -v pre-commit &>/dev/null; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
        pre-commit install > /dev/null 2>&1 || true
    fi
    log_step_done "Pre-commit hooks"
}

################################################################################
# Main
################################################################################

main() {
    parse_args "$@"
    start_timer

    if [[ "$VERBOSE" == "true" ]]; then
        echo "========================================"
        echo "  Bloginator macOS Setup"
        echo "========================================"
        [[ "$AUTO_CONFIRM" == "true" ]] && echo "[INFO] Auto-confirm mode"
        echo ""
    fi

    check_macos
    install_homebrew
    install_python
    install_git
    install_dev_tools
    setup_virtualenv
    install_python_dependencies
    install_pre_commit_hooks

    stop_timer

    local elapsed hours minutes seconds
    elapsed=$(($(date +%s) - SCRIPT_START_TIME))
    hours=$((elapsed / 3600))
    minutes=$(((elapsed % 3600) / 60))
    seconds=$((elapsed % 60))

    echo ""
    echo "========================================"
    echo "✓ Setup completed successfully"
    printf "Total time: %02d:%02d:%02d\n" "$hours" "$minutes" "$seconds"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "  1. source .venv/bin/activate"
    echo "  2. ./validate-monorepo.sh"
    echo ""
}

main "$@"
