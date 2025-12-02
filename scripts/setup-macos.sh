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
#   -f, --force     Force reinstall all dependencies
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

# Resolve symlinks to get actual script location
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ "$SCRIPT_PATH" != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

# shellcheck source=lib/compact.sh
source "$SCRIPT_DIR/lib/compact.sh"

# Navigate to project root
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

################################################################################
# Configuration
################################################################################

export AUTO_YES=false
export FORCE_INSTALL=false
readonly VENV_DIR="${REPO_ROOT}/.venv"
readonly PYTHON_VERSION="3.13"
readonly REQUIRED_PYTHON_MIN="3.10"
readonly REQUIRED_PYTHON_MAX="3.14"  # Exclusive

# Cache directory for tracking installed packages
CACHE_DIR="$REPO_ROOT/.setup-cache"
mkdir -p "$CACHE_DIR"

################################################################################
# Helper Functions
################################################################################

# Check if package is cached
is_cached() {
    local pkg="$1"
    [[ -f "$CACHE_DIR/$pkg" ]] && [[ $FORCE_INSTALL == false ]]
}

# Mark package as cached
mark_cached() {
    local pkg="$1"
    touch "$CACHE_DIR/$pkg"
}

# Find compatible Python version
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

# Confirm with user (respects AUTO_YES, defaults to yes after 3 seconds)
confirm() {
    local prompt="$1"
    local default="${2:-y}"

    if [[ "$AUTO_YES" == "true" ]]; then
        verbose "$prompt [auto-confirming]"
        return 0
    fi

    local response
    if read -t 3 -p "$prompt [$default, auto-yes in 3s]: " -r response 2>/dev/null; then
        response="${response:-$default}"
    else
        # Timeout: default to yes
        response="$default"
        echo ""  # newline since timeout suppresses it
    fi
    [[ "$response" =~ ^[Yy]$ ]]
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
    -f, --force     Force reinstall all dependencies
    -h, --help      Display this help

EXAMPLES
    ./scripts/setup-macos.sh        # Interactive setup
    ./scripts/setup-macos.sh -y     # Non-interactive
    ./scripts/setup-macos.sh -v -y  # Verbose + non-interactive
    ./scripts/setup-macos.sh -f     # Force reinstall everything

PERFORMANCE
    First run: ~3-5 minutes (installs everything)
    Subsequent: ~30-60 seconds (checks only, skips cached items)
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes) AUTO_YES=true; shift ;;
            -v|--verbose) export VERBOSE=1; shift ;;
            -f|--force) FORCE_INSTALL=true; shift ;;
            -h|--help) show_help; exit 0 ;;
            *) print_error "Unknown option: $1. Use --help for usage."; exit 1 ;;
        esac
    done
}

################################################################################
# Setup Functions
################################################################################

setup_homebrew() {
    task_start "Checking Homebrew"

    if command -v brew &>/dev/null; then
        verbose "Homebrew $(brew --version | head -n1 | awk '{print $2}')"
        task_ok "Homebrew ready"
    else
        task_start "Installing Homebrew"
        if confirm "Install Homebrew?"; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" 2>&1 | verbose
            mark_cached "homebrew"
            task_ok "Homebrew installed"
        else
            task_fail "Homebrew required"
            exit 1
        fi
    fi
}

setup_python() {
    task_start "Checking Python"

    local python_cmd
    if python_cmd=$(find_compatible_python); then
        local py_version
        py_version=$($python_cmd --version 2>&1 | awk '{print $2}')
        verbose "Found $python_cmd ($py_version)"
        task_ok "Python $py_version ready"
        echo "$python_cmd"
        return 0
    fi

    # Check system python3
    if command -v python3 &>/dev/null; then
        local python_version major_minor is_too_old is_too_new
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
        major_minor=$(echo "$python_version" | cut -d. -f1,2)

        is_too_old=false
        is_too_new=false
        [[ $(printf '%s\n' "${major_minor}" "${REQUIRED_PYTHON_MIN}" | sort -V | head -n1) != "${REQUIRED_PYTHON_MIN}" ]] && is_too_old=true
        [[ $(printf '%s\n' "${major_minor}" "${REQUIRED_PYTHON_MAX}" | sort -V | tail -n1) == "${major_minor}" ]] && is_too_new=true

        if [[ "$is_too_old" == "false" ]] && [[ "$is_too_new" == "false" ]]; then
            verbose "System python3 ($python_version) is compatible"
            task_ok "Python $python_version ready"
            echo "python3"
            return 0
        fi

        [[ "$is_too_new" == "true" ]] && verbose "Python $python_version too new (need <$REQUIRED_PYTHON_MAX)"
        [[ "$is_too_old" == "true" ]] && verbose "Python $python_version too old (need >=$REQUIRED_PYTHON_MIN)"
    fi

    # Install Python via Homebrew
    task_start "Installing Python"
    if confirm "Install Python $PYTHON_VERSION via Homebrew?"; then
        brew install "python@${PYTHON_VERSION}" 2>&1 | verbose
        mark_cached "python"
        task_ok "Python $PYTHON_VERSION installed"
        echo "python${PYTHON_VERSION}"
    else
        task_fail "Compatible Python required"
        exit 1
    fi
}

setup_git() {
    task_start "Checking Git"

    if command -v git &>/dev/null; then
        verbose "Git $(git --version | awk '{print $3}')"
        task_ok "Git ready"
    else
        task_start "Installing Git"
        if confirm "Install Git?"; then
            brew install git 2>&1 | verbose
            mark_cached "git"
            task_ok "Git installed"
        else
            task_fail "Git required"
            exit 1
        fi
    fi
}

setup_dev_tools() {
    task_start "Checking development tools"

    if ! command -v gitleaks &>/dev/null; then
        task_start "Installing gitleaks"
        if confirm "Install gitleaks?"; then
            brew install gitleaks 2>&1 | verbose
            mark_cached "gitleaks"
            task_ok "gitleaks installed"
        fi
    else
        verbose "gitleaks already installed"
    fi

    if ! command -v pre-commit &>/dev/null; then
        task_start "Installing pre-commit"
        if confirm "Install pre-commit?"; then
            brew install pre-commit 2>&1 | verbose
            mark_cached "pre-commit"
            task_ok "pre-commit installed"
        fi
    else
        verbose "pre-commit already installed"
    fi

    task_ok "Development tools ready"
}

is_venv_broken() {
    # Check if venv is broken by testing basic python import
    if [[ ! -d "$VENV_DIR" ]]; then
        return 1
    fi

    if [[ ! -x "$VENV_DIR/bin/python" ]]; then
        return 0  # Broken
    fi

    # Try to import basic modules to detect corruption
    if ! "$VENV_DIR/bin/python" -c "import sys, os, pip" 2>/dev/null; then
        return 0  # Broken
    fi

    return 1  # Not broken
}

setup_virtualenv() {
    task_start "Setting up Python virtual environment"

    if [[ -d "$VENV_DIR" ]]; then
        if is_venv_broken; then
            verbose "Existing venv is broken, removing..."
            rm -rf "$VENV_DIR"
        elif [[ $FORCE_INSTALL == true ]]; then
            verbose "Force install flag set, removing existing venv..."
            rm -rf "$VENV_DIR"
        elif is_cached "venv"; then
            task_skip "Virtual environment (cached and healthy)"
            return 0
        elif confirm "Recreate virtual environment?"; then
            rm -rf "$VENV_DIR"
            verbose "Removed existing venv"
        else
            task_ok "Virtual environment (existing)"
            return 0
        fi
    fi

    # Find python without showing task messages
    local python_cmd
    python_cmd=$(find_compatible_python) || python_cmd="python3"

    verbose "Creating venv with $python_cmd..."
    if ! "$python_cmd" -m venv --copies "$VENV_DIR" 2>&1; then
        task_fail "Failed to create virtual environment"
        exit 1
    fi

    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"

    verbose "Upgrading pip, setuptools, wheel..."
    if ! python -m pip install --upgrade pip setuptools wheel --quiet 2>&1; then
        task_fail "Failed to upgrade pip/setuptools/wheel"
        exit 1
    fi

    mark_cached "venv"
    task_ok "Virtual environment ready"
}

setup_dependencies() {
    task_start "Installing Python dependencies"

    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"

    if is_cached "python-deps" && ! is_install_broken; then
        task_skip "Python dependencies (cached)"
        return 0
    fi

    verbose "Installing bloginator with dev, web, and cloud extras..."
    verbose "Pinning streamlit==1.28.0 for UI compatibility..."

    local install_log
    install_log=$(mktemp)
    # shellcheck disable=SC2064
    trap "rm -f '$install_log'" RETURN

    # First pass: install bloginator and dependencies + pinned streamlit
    if ! python -m pip install -e ".[dev,web,cloud]" "streamlit==1.28.0" > "$install_log" 2>&1; then
        task_fail "Failed to install Python dependencies (first attempt)"
        verbose "$(cat "$install_log" | tail -20)"

        # Try again with --no-cache-dir in case of cache corruption
        verbose "Retrying with --no-cache-dir..."
        if ! python -m pip install --no-cache-dir -e ".[dev,web,cloud]" "streamlit==1.28.0" > "$install_log" 2>&1; then
            task_fail "Failed to install Python dependencies (retry)"
            verbose "$(cat "$install_log" | tail -30)"
            exit 1
        fi
    fi

    # Show last few lines of install log if verbose
    if [[ $VERBOSE -eq 1 ]]; then
        tail -5 "$install_log" | while read -r line; do
            verbose "$line"
        done
    fi

    verbose "Verifying critical packages..."
    local missing=()
    for pkg in pytest black ruff mypy bandit streamlit pre-commit; do
        if ! python -m pip show "$pkg" > /dev/null 2>&1; then
            missing+=("$pkg")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        task_fail "Missing packages: ${missing[*]}"
        exit 1
    fi

    mark_cached "python-deps"
    task_ok "Python dependencies installed and verified"
}

is_install_broken() {
    # Check if install is broken by verifying critical imports work
    if ! python -c "import pip, setuptools" 2>/dev/null; then
        return 0  # Broken
    fi
    return 1  # Not broken
}

setup_precommit_hooks() {
    if is_cached "pre-commit-hooks"; then
        task_skip "Pre-commit hooks (cached)"
        return 0
    fi

    task_start "Installing pre-commit hooks"

    if command -v pre-commit &>/dev/null; then
        # shellcheck source=/dev/null
        source "$VENV_DIR/bin/activate"
        if pre-commit install > /dev/null 2>&1; then
            mark_cached "pre-commit-hooks"
            task_ok "Pre-commit hooks installed"
        else
            task_warn "Pre-commit hook installation returned non-zero (continuing)"
        fi
    fi
}

validate_runtime() {
    task_start "Validating runtime environment"

    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"

    # Test 1: Python is functional
    verbose "Testing Python..."
    if ! python -c "import sys; sys.exit(0)" 2>/dev/null; then
        task_fail "Python not functional"
        exit 1
    fi

    # Test 2: Development tools are operational
    verbose "Testing development tools..."
    for tool in black ruff mypy pytest; do
        if ! python -m "$tool" --version > /dev/null 2>&1; then
            task_fail "Development tool '$tool' not operational"
            exit 1
        fi
    done

    # Test 3: Core pip packages are installed
    verbose "Verifying pip packages..."
    if ! python -m pip show bloginator pytest black ruff mypy > /dev/null 2>&1; then
        task_fail "Required packages not installed"
        exit 1
    fi

    task_ok "Runtime environment validated"
}

################################################################################
# Main
################################################################################

main() {
    parse_args "$@"

    print_header "Bloginator macOS Setup"
    echo ""

    setup_homebrew
    setup_git
    setup_dev_tools
    setup_python > /dev/null
    setup_virtualenv
    setup_dependencies
    setup_precommit_hooks
    validate_runtime

    echo ""
    print_header "✓ Setup complete! $(get_elapsed_time)"
    echo ""
    echo "Environment is ready. Next steps:"
    echo "  1. source .venv/bin/activate           # Activate virtual environment"
    echo "  2. ./validate-monorepo.sh              # Run validation checks"
    echo "  3. ./run-e2e.sh                        # Run end-to-end demo"
    echo "  4. ./run-streamlit.sh                  # Launch web UI"
    echo ""
}

main "$@"
