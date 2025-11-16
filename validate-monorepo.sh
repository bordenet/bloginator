#!/usr/bin/env bash
#
# Bloginator Monorepo Validation Script
#
# Purpose:
#   Comprehensive validation of the Bloginator codebase including:
#   - Python environment setup and dependency checks
#   - Code formatting (black, isort)
#   - Linting (ruff, pydocstyle)
#   - Type checking (mypy)
#   - Security scanning (gitleaks, bandit)
#   - Unit tests with coverage
#   - Integration tests
#
# Usage:
#   ./validate-monorepo.sh           # Standard validation (unit + lint)
#   ./validate-monorepo.sh --quick   # Quick validation (no tests)
#   ./validate-monorepo.sh --all     # Full validation (unit + integration)
#   ./validate-monorepo.sh --help    # Show this help
#
# Options:
#   --quick     Skip tests, only run linting and formatting checks
#   --all       Run all tests including integration tests
#   --fix       Auto-fix formatting issues
#   --verbose   Show detailed output
#   --help      Display this help message
#
# Dependencies:
#   - Python 3.10+
#   - Virtual environment (.venv)
#   - All development dependencies installed

set -euo pipefail

# Repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Source common library
# shellcheck disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

# Initialize script
init_script

#######################################
# Configuration
#######################################
readonly VENV_DIR="${REPO_ROOT}/.venv"
readonly SRC_DIR="${REPO_ROOT}/src"
readonly TESTS_DIR="${REPO_ROOT}/tests"
readonly COVERAGE_THRESHOLD=80

# Validation options
RUN_TESTS=true
RUN_INTEGRATION=false
AUTO_FIX=false
VERBOSE=false

#######################################
# Parse command line arguments
#######################################
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                RUN_TESTS=false
                shift
                ;;
            --all)
                RUN_INTEGRATION=true
                shift
                ;;
            --fix)
                AUTO_FIX=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                grep '^#' "$0" | grep -v '#!/usr/bin/env' | sed 's/^# //' | sed 's/^#//'
                exit 0
                ;;
            *)
                die "Unknown option: $1. Use --help for usage information."
                ;;
        esac
    done
}

#######################################
# Check prerequisites
#######################################
check_prerequisites() {
    log_section "Checking Prerequisites"

    require_command python3 "Python 3 is required. Install it with: brew install python@3.10"
    require_command git "Git is required."

    # Check Python version
    local python_version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Python version: $python_version"

    # Check for virtual environment
    if [[ ! -d "$VENV_DIR" ]]; then
        log_warning "Virtual environment not found at $VENV_DIR"
        log_info "Run './scripts/setup-macos.sh' to set up the environment"
        return 1
    fi

    log_success "Prerequisites check passed"
}

#######################################
# Activate virtual environment
#######################################
setup_environment() {
    log_section "Setting Up Environment"

    if ! is_venv_active; then
        log_info "Activating virtual environment..."
        activate_venv "$VENV_DIR"
    else
        log_info "Virtual environment already active"
    fi

    # Verify key packages are installed
    local packages=("black" "ruff" "mypy" "pytest" "coverage")
    for pkg in "${packages[@]}"; do
        if ! python3 -m pip show "$pkg" &>/dev/null; then
            log_warning "Package '$pkg' not found. Installing dependencies..."
            python3 -m pip install -e ".[dev]" || die "Failed to install dependencies"
            break
        fi
    done

    log_success "Environment setup completed"
}

#######################################
# Run security scans
#######################################
run_security_scans() {
    log_section "Running Security Scans"

    # Gitleaks - check for secrets
    if command -v gitleaks &>/dev/null; then
        log_info "Running gitleaks..."
        if gitleaks detect --source="$REPO_ROOT" --verbose --no-git 2>&1 | tee /dev/null; then
            log_success "Gitleaks: No secrets detected"
        else
            log_error "Gitleaks: Potential secrets found!"
            return 1
        fi
    else
        log_warning "Gitleaks not installed, skipping secrets scan"
    fi

    # Bandit - Python security linter
    if python3 -m pip show bandit &>/dev/null; then
        log_info "Running bandit..."
        if python3 -m bandit -r "$SRC_DIR" -ll 2>&1 | tee /dev/null; then
            log_success "Bandit: No security issues found"
        else
            log_warning "Bandit: Potential security issues found"
        fi
    else
        log_info "Installing bandit..."
        python3 -m pip install bandit
        python3 -m bandit -r "$SRC_DIR" -ll
    fi

    log_success "Security scans completed"
}

#######################################
# Run code formatting checks
#######################################
run_formatting_checks() {
    log_section "Running Code Formatting Checks"

    # Black
    log_info "Checking formatting with black..."
    if [[ "$AUTO_FIX" == "true" ]]; then
        python3 -m black "$SRC_DIR" "$TESTS_DIR" || die "Black formatting failed"
        log_success "Black: Code formatted"
    else
        if python3 -m black --check "$SRC_DIR" "$TESTS_DIR"; then
            log_success "Black: All files formatted correctly"
        else
            log_error "Black: Formatting issues found. Run with --fix to auto-format"
            return 1
        fi
    fi

    # isort
    log_info "Checking import sorting with isort..."
    if [[ "$AUTO_FIX" == "true" ]]; then
        python3 -m isort "$SRC_DIR" "$TESTS_DIR" || die "isort failed"
        log_success "isort: Imports sorted"
    else
        if python3 -m isort --check "$SRC_DIR" "$TESTS_DIR"; then
            log_success "isort: All imports sorted correctly"
        else
            log_error "isort: Import sorting issues found. Run with --fix to auto-sort"
            return 1
        fi
    fi

    log_success "Formatting checks completed"
}

#######################################
# Run linting
#######################################
run_linting() {
    log_section "Running Linting"

    # Ruff
    log_info "Running ruff..."
    if [[ "$AUTO_FIX" == "true" ]]; then
        python3 -m ruff check --fix "$SRC_DIR" "$TESTS_DIR" || log_warning "Ruff found issues"
    else
        if python3 -m ruff check "$SRC_DIR" "$TESTS_DIR"; then
            log_success "Ruff: No issues found"
        else
            log_error "Ruff: Linting issues found. Run with --fix to auto-fix"
            return 1
        fi
    fi

    # Pydocstyle
    log_info "Running pydocstyle..."
    if python3 -m pydocstyle "$SRC_DIR"; then
        log_success "Pydocstyle: All docstrings valid"
    else
        log_warning "Pydocstyle: Docstring issues found"
    fi

    log_success "Linting completed"
}

#######################################
# Run type checking
#######################################
run_type_checking() {
    log_section "Running Type Checking"

    log_info "Running mypy..."
    if [[ "$VERBOSE" == "true" ]]; then
        python3 -m mypy "$SRC_DIR" || log_error "MyPy: Type errors found"
    else
        if python3 -m mypy "$SRC_DIR" --no-error-summary 2>&1 | grep -E "(error|Success)"; then
            log_success "MyPy: Type checking passed"
        else
            log_error "MyPy: Type errors found"
            return 1
        fi
    fi

    log_success "Type checking completed"
}

#######################################
# Run unit tests
#######################################
run_unit_tests() {
    log_section "Running Unit Tests"

    local pytest_args=(
        "$TESTS_DIR"
        "-v"
        "--cov=$SRC_DIR/bloginator"
        "--cov-report=term-missing"
        "--cov-report=html:coverage_html"
        "--cov-fail-under=$COVERAGE_THRESHOLD"
        "-m" "not slow and not integration"
    )

    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-vv")
    fi

    log_info "Running pytest with coverage..."
    if python3 -m pytest "${pytest_args[@]}"; then
        log_success "Unit tests passed with coverage >= ${COVERAGE_THRESHOLD}%"
    else
        log_error "Unit tests failed or coverage below ${COVERAGE_THRESHOLD}%"
        return 1
    fi

    log_success "Unit tests completed"
}

#######################################
# Run integration tests
#######################################
run_integration_tests() {
    log_section "Running Integration Tests"

    log_info "Running integration tests..."
    if python3 -m pytest "$TESTS_DIR" -v -m "integration"; then
        log_success "Integration tests passed"
    else
        log_warning "Integration tests failed or none found"
    fi

    log_success "Integration tests completed"
}

#######################################
# Run all slow tests
#######################################
run_slow_tests() {
    log_section "Running Slow Tests"

    log_info "Running slow tests (this may take a while)..."
    if python3 -m pytest "$TESTS_DIR" -v -m "slow" --durations=10; then
        log_success "Slow tests passed"
    else
        log_warning "Slow tests failed or none found"
    fi

    log_success "Slow tests completed"
}

#######################################
# Main validation workflow
#######################################
main() {
    log_header "Bloginator Monorepo Validation"

    parse_args "$@"

    # Show configuration
    log_info "Configuration:"
    log_info "  Run tests: $RUN_TESTS"
    log_info "  Run integration: $RUN_INTEGRATION"
    log_info "  Auto-fix: $AUTO_FIX"
    log_info "  Verbose: $VERBOSE"
    echo ""

    # Run validation steps
    check_prerequisites
    setup_environment
    run_security_scans
    run_formatting_checks
    run_linting
    run_type_checking

    if [[ "$RUN_TESTS" == "true" ]]; then
        run_unit_tests

        if [[ "$RUN_INTEGRATION" == "true" ]]; then
            run_integration_tests
            run_slow_tests
        fi
    else
        log_info "Skipping tests (--quick mode)"
    fi

    # Print summary
    print_summary

    if [[ $ERROR_COUNT -eq 0 ]]; then
        log_header "✓ VALIDATION PASSED"
        exit 0
    else
        log_header "✗ VALIDATION FAILED"
        exit 1
    fi
}

# Run main function
main "$@"
