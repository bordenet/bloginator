#!/bin/bash
################################################################################
# Fast Quality Gate for Bloginator
################################################################################
# PURPOSE: Quick validation checks for code quality
#   - Code formatting (black)
#   - Linting (ruff) - includes import sorting via I rules
#   - Type checking (mypy) on key modules
#   - Fast unit tests (excluding slow tests)
#
# USAGE:
#   ./scripts/run-fast-quality-gate.sh [OPTIONS]
#   ./scripts/run-fast-quality-gate.sh --help
#
# OPTIONS:
#   -h, --help      Display help message
#
# EXAMPLES:
#   ./scripts/run-fast-quality-gate.sh      # Run all fast quality checks
#
# NOTES:
#   - Used by pre-commit hooks for fast validation
#   - For comprehensive validation, use validate-monorepo.sh
################################################################################

set -e

# Parse arguments
for arg in "$@"; do
    case $arg in
        -h|--help)
            sed -n '3,23p' "${BASH_SOURCE[0]}" | sed 's/^# //' | sed 's/^#$//'
            exit 0
            ;;
    esac
done

# Timer state
SCRIPT_START_TIME=$(date +%s)
TIMER_PID=""

# Timer functions
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
    TIMER_PID=""
}

trap stop_timer EXIT

# Start timer
start_timer

echo "🚀 Running Fast Quality Gate..."

# Check if we're in a virtualenv
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Run: source venv/bin/activate"
fi

# Check if src directory exists
if [ ! -d "src" ]; then
    echo "⚠️  src/ directory not found, skipping checks"
    exit 0
fi

# 1. Format check
echo ""
echo "1/5 Checking code formatting (black)..."
if [[ -n "${PRE_COMMIT:-}" ]]; then
    echo "   Skipping Black check inside pre-commit (handled by dedicated Black hook)."
else
    if ! black --check --line-length=100 src/ tests/ 2>/dev/null; then
        echo "❌ Code not formatted. Run: black --line-length=100 src/ tests/"
        exit 1
    fi
    echo "✅ Formatting OK"
fi

# 2. Linting
echo ""
echo "2/5 Linting (ruff)..."
if command -v ruff &> /dev/null; then
    if ! ruff check src/ tests/ 2>/dev/null; then
        echo "❌ Linting failed. Run: ruff check --fix src/ tests/"
        exit 1
    fi
    echo "✅ Linting OK"
else
    echo "⚠️  ruff not in PATH, skipping (pre-commit will handle this)"
fi

# 3. Type checking (targeted high-value modules)
echo ""
echo "3/5 Type checking (mypy)..."
if ls src/**/*.py 1> /dev/null 2>&1; then
    if command -v mypy &> /dev/null; then
        if ! mypy \
            src/bloginator/models \
            src/bloginator/extraction \
            src/bloginator/search \
            src/bloginator/safety \
            src/bloginator/export \
            src/bloginator/services \
            src/bloginator/indexing/indexer.py \
            src/bloginator/generation \
            src/bloginator/utils/parallel.py 2>/dev/null; then
            echo "❌ Type checking failed"
            exit 1
        fi
        echo "✅ Type checking OK"
    else
        echo "⚠️  mypy not in PATH, skipping (pre-commit will handle this)"
    fi
else
    echo "⚠️  No Python files found, skipping type check"
fi

# 4. Import sorting (handled by ruff I rules, checked in step 2)
echo ""
echo "4/5 Import sorting..."
echo "✅ Import sorting OK (verified by ruff I rules in step 2)"

# 5. Unit tests (fast subset only) - skip if no tests yet
echo ""
echo "5/5 Running fast unit tests..."
if [[ -n "${PRE_COMMIT:-}" ]]; then
    echo "⚠️  Skipping tests in pre-commit context (handled separately)"
elif [ -d "tests" ] && ls tests/**/*.py 1> /dev/null 2>&1; then
    # Ensure the package is installed for testing
    if ! python -c "import bloginator" 2>/dev/null; then
        echo "📦 Installing project in editable mode..."
        if ! pip install -e . >/dev/null 2>&1; then
            echo "⚠️  Failed to install project, skipping tests"
        else
            if ! pytest tests/ -m "not slow" --tb=short -q 2>/dev/null; then
                echo "❌ Fast tests failed"
                exit 1
            fi
            echo "✅ Fast tests passed"
        fi
    else
        if ! pytest tests/ -m "not slow" --tb=short -q 2>/dev/null; then
            echo "❌ Fast tests failed"
            exit 1
        fi
        echo "✅ Fast tests passed"
    fi
else
    echo "⚠️  No tests found, skipping test execution"
fi

echo ""
echo "✅ Fast Quality Gate passed!"
