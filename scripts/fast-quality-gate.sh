#!/bin/bash
set -e

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
if ! black --check --line-length=100 src/ tests/ 2>/dev/null; then
    echo "❌ Code not formatted. Run: black --line-length=100 src/ tests/"
    exit 1
fi
echo "✅ Formatting OK"

# 2. Linting
echo ""
echo "2/5 Linting (ruff)..."
if ! ruff check src/ tests/ 2>/dev/null; then
    echo "❌ Linting failed. Run: ruff check --fix src/ tests/"
    exit 1
fi
echo "✅ Linting OK"

# 3. Type checking (skip if no src files yet)
echo ""
echo "3/5 Type checking (mypy)..."
if ls src/**/*.py 1> /dev/null 2>&1; then
    if ! mypy src/ --strict --ignore-missing-imports 2>/dev/null; then
        echo "❌ Type checking failed"
        exit 1
    fi
    echo "✅ Type checking OK"
else
    echo "⚠️  No Python files found, skipping type check"
fi

# 4. Import sorting
echo ""
echo "4/5 Checking import sorting (isort)..."
if ! isort --check-only --profile=black --line-length=100 src/ tests/ 2>/dev/null; then
    echo "❌ Imports not sorted. Run: isort --profile=black --line-length=100 src/ tests/"
    exit 1
fi
echo "✅ Import sorting OK"

# 5. Unit tests (fast subset only) - skip if no tests yet
echo ""
echo "5/5 Running fast unit tests..."
if [ -d "tests" ] && ls tests/**/*.py 1> /dev/null 2>&1; then
    if ! pytest tests/ -m "not slow" --tb=short -q 2>/dev/null; then
        echo "❌ Fast tests failed"
        exit 1
    fi
    echo "✅ Fast tests passed"
else
    echo "⚠️  No tests found, skipping test execution"
fi

echo ""
echo "✅ Fast Quality Gate passed!"
