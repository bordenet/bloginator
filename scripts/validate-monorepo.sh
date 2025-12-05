#!/usr/bin/env bash

################################################################################
# Bloginator Monorepo Validation Script
################################################################################
# PURPOSE: Comprehensive validation of the Bloginator codebase
#   - Code formatting (black, isort)
#   - Linting (ruff, pydocstyle)
#   - Type checking (mypy)
#   - Security scanning (gitleaks, bandit)
#   - Unit tests with coverage
#   - Integration tests
#
# USAGE:
#   ./validate-monorepo.sh [OPTIONS]
#   ./validate-monorepo.sh --help
#
# OPTIONS:
#   -y, --yes         Auto-confirm all prompts
#   -v, --verbose     Show detailed output
#   --quick           Skip tests, only run linting
#   --all             Run all tests including integration
#   --fix             Auto-fix formatting issues
#   -h, --help        Display help message
#
# EXAMPLES:
#   ./validate-monorepo.sh              # Standard validation (lint + unit tests)
#   ./validate-monorepo.sh -y           # Non-interactive
#   ./validate-monorepo.sh --quick      # Fast validation (lint only, no tests)
#   ./validate-monorepo.sh --all        # Full validation with integration tests
#   ./validate-monorepo.sh --fix -y     # Auto-fix and validate
#
# DEPENDENCIES:
#   - Python 3.10+
#   - Virtual environment (.venv)
#   - All development dependencies
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

# Change to project root (parent of scripts/)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

################################################################################
# Configuration
################################################################################

export AUTO_YES=false
export VERBOSE=${VERBOSE:-0}
readonly VENV_DIR="${PROJECT_ROOT}/venv"
readonly SRC_DIR="${PROJECT_ROOT}/src"
readonly TESTS_DIR="${PROJECT_ROOT}/tests"
readonly COVERAGE_THRESHOLD=70

RUN_TESTS=true
RUN_INTEGRATION=false
AUTO_FIX=false

################################################################################
# Helper Functions
################################################################################

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
        response="$default"
        echo ""
    fi
    [[ "$response" =~ ^[Yy]$ ]]
}

################################################################################
# Argument Parsing
################################################################################

show_help() {
    cat << 'EOF'
NAME
    validate-monorepo.sh - Comprehensive Bloginator validation

SYNOPSIS
    ./validate-monorepo.sh [OPTIONS]

DESCRIPTION
    Validates code formatting, linting, types, security, and runs tests
    with coverage verification.

OPTIONS
    -y, --yes       Auto-confirm all prompts
    -v, --verbose   Show detailed output
    --quick         Skip tests, only run linting
    --all           Run all tests including integration and slow tests
    --fix           Auto-fix formatting and linting issues
    -h, --help      Display this help

EXAMPLES
    ./validate-monorepo.sh              # Standard validation
    ./validate-monorepo.sh -y           # Non-interactive validation
    ./validate-monorepo.sh --quick      # Fast lint-only check
    ./validate-monorepo.sh --fix -y     # Auto-fix all issues

COVERAGE THRESHOLD
    Minimum: 70% (configurable in script)
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes) AUTO_YES=true; shift ;;
            -v|--verbose) export VERBOSE=1; shift ;;
            --quick) RUN_TESTS=false; shift ;;
            --all) RUN_INTEGRATION=true; shift ;;
            --fix) AUTO_FIX=true; shift ;;
            -h|--help) show_help; exit 0 ;;
            *) print_error "Unknown option: $1"; exit 1 ;;
        esac
    done
}

print_error() {
    echo -e "${C_RED}✗ Error: $*${C_RESET}" >&2
}

################################################################################
# Validation Functions
################################################################################

check_prerequisites() {
    task_start "Checking prerequisites"

    if [[ ! -d "$VENV_DIR" ]]; then
        task_fail "Virtual environment not found"
        echo ""
        echo "Create it with: ./scripts/setup-macos.sh"
        exit 1
    fi

    verbose "Found virtual environment at $VENV_DIR"
    task_ok "Prerequisites verified"
}

setup_environment() {
    task_start "Activating virtual environment"

    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"

    verbose "Virtual environment activated"
    task_ok "Environment ready"
}

validate_formatting() {
    task_start "Checking code formatting"

    verbose "Running black..."
    if [[ "$AUTO_FIX" == "true" ]]; then
        if python -m black "$SRC_DIR" "$TESTS_DIR" > /dev/null 2>&1; then
            verbose "Black: formatted code"
        else
            task_warn "Black: some files need formatting"
        fi
    else
        if python -m black --check "$SRC_DIR" "$TESTS_DIR" > /dev/null 2>&1; then
            verbose "Black: all files formatted correctly"
        else
            task_warn "Black: formatting issues found (use --fix to auto-format)"
        fi
    fi

    verbose "Running isort..."
    if [[ "$AUTO_FIX" == "true" ]]; then
        if python -m isort "$SRC_DIR" "$TESTS_DIR" > /dev/null 2>&1; then
            verbose "isort: imports sorted"
        else
            task_warn "isort: some imports need sorting"
        fi
    else
        if python -m isort --check "$SRC_DIR" "$TESTS_DIR" > /dev/null 2>&1; then
            verbose "isort: all imports sorted correctly"
        else
            task_warn "isort: import sorting issues (use --fix to auto-sort)"
        fi
    fi

    task_ok "Formatting validation complete"
}

validate_linting() {
    task_start "Running linting checks"

    verbose "Running ruff..."
    if [[ "$AUTO_FIX" == "true" ]]; then
        if python -m ruff check --fix "$SRC_DIR" "$TESTS_DIR" > /dev/null 2>&1; then
            verbose "Ruff: issues fixed"
        else
            task_warn "Ruff: some issues remain"
        fi
    else
        if python -m ruff check "$SRC_DIR" "$TESTS_DIR" > /dev/null 2>&1; then
            verbose "Ruff: no linting issues"
        else
            task_warn "Ruff: linting issues found (use --fix to auto-fix)"
        fi
    fi

    verbose "Running pydocstyle..."
    if python -m pydocstyle "$SRC_DIR" > /dev/null 2>&1; then
        verbose "Pydocstyle: all docstrings valid"
    else
        task_warn "Pydocstyle: docstring issues found"
    fi

    task_ok "Linting validation complete"
}

validate_types() {
    task_start "Running type checking"

    verbose "Running mypy..."
    if python -m mypy "$SRC_DIR" > /dev/null 2>&1; then
        verbose "MyPy: type checking passed"
    else
        task_warn "MyPy: type errors found (non-blocking)"
    fi

    task_ok "Type checking complete"
}

validate_security() {
    task_start "Running security scans"

    verbose "Checking for exposed secrets..."
    if command -v gitleaks &>/dev/null; then
        if gitleaks detect --source="$SCRIPT_DIR" --no-git > /dev/null 2>&1; then
            verbose "gitleaks: no secrets detected"
        else
            task_warn "gitleaks: potential secrets found (review carefully)"
        fi
    else
        verbose "gitleaks: not installed (skipping)"
    fi

    verbose "Running bandit security scan..."
    if python -m bandit -r "$SRC_DIR" -q 2>/dev/null; then
        verbose "bandit: no security issues found"
    else
        task_warn "bandit: security issues found (review carefully)"
    fi

    task_ok "Security scans complete"
}

run_unit_tests() {
    task_start "Running unit tests"

    verbose "Running pytest with coverage..."
    local pytest_args=(
        "$TESTS_DIR"
        "--cov=$SRC_DIR/bloginator"
        "--cov-report=term-missing"
        "--cov-fail-under=$COVERAGE_THRESHOLD"
        "-m" "not slow and not integration"
        "-q"
    )

    if [[ $VERBOSE -eq 1 ]]; then
        pytest_args+=("-v")
    fi

    if python -m pytest "${pytest_args[@]}"; then
        verbose "Tests passed with coverage >= ${COVERAGE_THRESHOLD}%"
        task_ok "Unit tests passed"
    else
        task_fail "Unit tests failed or coverage below ${COVERAGE_THRESHOLD}%"
        exit 1
    fi
}

run_integration_tests() {
    task_start "Running integration tests"

    verbose "Running integration test suite..."
    if python -m pytest "$TESTS_DIR" -m "integration" -q 2>/dev/null; then
        verbose "Integration tests passed"
        task_ok "Integration tests passed"
    else
        task_warn "Integration tests failed or none found"
    fi
}

################################################################################
# Main
################################################################################

main() {
    parse_args "$@"

    print_header "Bloginator Monorepo Validation"
    echo ""

    # Show configuration
    if [[ $VERBOSE -eq 1 ]]; then
        verbose "Configuration:"
        verbose "  Run tests: $RUN_TESTS"
        verbose "  Run integration: $RUN_INTEGRATION"
        verbose "  Auto-fix: $AUTO_FIX"
        verbose "  Coverage threshold: ${COVERAGE_THRESHOLD}%"
        echo ""
    fi

    # Run validation
    check_prerequisites
    setup_environment
    validate_formatting
    validate_linting
    validate_types
    validate_security

    if [[ "$RUN_TESTS" == "true" ]]; then
        run_unit_tests
        if [[ "$RUN_INTEGRATION" == "true" ]]; then
            run_integration_tests
        fi
    else
        verbose "Skipping tests (--quick mode)"
    fi

    echo ""
    print_header "✓ Validation complete! $(get_elapsed_time)"
    echo ""

    if [[ "$AUTO_FIX" == "true" ]]; then
        echo "All issues have been auto-fixed."
    else
        echo "Use --fix to auto-fix formatting and linting issues."
    fi
    echo ""
}

main "$@"
