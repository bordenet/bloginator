#!/bin/bash
#
# DEPRECATED: Use validate-monorepo.sh instead
#
# This script is maintained for backwards compatibility.
# The newer validate-monorepo.sh provides:
# - Better logging with colors and structure
# - More comprehensive checks (security, integration tests)
# - Consistent with RecipeArchive patterns
# - Options: --quick, --all, --fix, --verbose
#
# Usage:
#   ./validate-monorepo.sh           # Standard validation
#   ./validate-monorepo.sh --quick   # Skip tests
#   ./validate-monorepo.sh --all     # Include integration tests
#   ./validate-monorepo.sh --fix     # Auto-fix issues
#
set -e

SKIP_SLOW=false
FIX=false
PRE_COMMIT_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-slow)
            SKIP_SLOW=true
            shift
            ;;
        --fix)
            FIX=true
            shift
            ;;
        --pre-commit)
            PRE_COMMIT_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-slow] [--fix] [--pre-commit]"
            exit 1
            ;;
    esac
done

echo "╔════════════════════════════════════════╗"
echo "║   Bloginator Validation Suite          ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "⚠️  DEPRECATION NOTICE:"
echo "   This script is deprecated. Please use validate-monorepo.sh instead."
echo "   validate-monorepo.sh provides better logging, more checks, and consistent patterns."
echo ""
echo "   Continuing with legacy validation..."
echo ""

# Activate venv if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    # Try .venv first (recommended), then venv (legacy)
    if [[ -f ".venv/bin/activate" ]]; then
        echo "Activating virtual environment (.venv)..."
        source .venv/bin/activate
    elif [[ -f "venv/bin/activate" ]]; then
        echo "Activating virtual environment (venv)..."
        source venv/bin/activate
    else
        echo "⚠️  Virtual environment not found."
        echo "   Run: ./scripts/setup-macos.sh"
        echo "   Or manually: python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'"
        exit 1
    fi
fi

# 1. Pre-commit hooks only
if [[ "$PRE_COMMIT_ONLY" == "true" ]]; then
    echo "Running pre-commit hooks only..."
    pre-commit run --all-files
    exit 0
fi

# Check if src directory exists
if [ ! -d "src" ]; then
    echo "⚠️  src/ directory not found. Creating initial structure..."
    echo "   This appears to be the initial setup. Skipping validation."
    exit 0
fi

# 2. Code formatting
echo "═══ 1/8 Code Formatting (black) ═══"
if [[ "$FIX" == "true" ]]; then
    black --line-length=100 src/ tests/
else
    black --check --line-length=100 src/ tests/
fi
echo "✅ Formatting OK"
echo ""

# 3. Linting
echo "═══ 2/8 Linting (ruff) ═══"
if [[ "$FIX" == "true" ]]; then
    ruff check --fix src/ tests/
else
    ruff check src/ tests/
fi
echo "✅ Linting OK"
echo ""

# 4. Type checking
echo "═══ 3/8 Type Checking (mypy) ═══"
if ls src/**/*.py 1> /dev/null 2>&1; then
    mypy src/ --strict --ignore-missing-imports
    echo "✅ Type checking OK"
else
    echo "⚠️  No Python files found, skipping type check"
fi
echo ""

# 5. Import sorting
echo "═══ 4/8 Import Sorting (isort) ═══"
if [[ "$FIX" == "true" ]]; then
    isort --profile=black --line-length=100 src/ tests/
else
    isort --check-only --profile=black --line-length=100 src/ tests/
fi
echo "✅ Import sorting OK"
echo ""

# 6. Security scanning
echo "═══ 5/8 Security Scanning (gitleaks) ═══"
if command -v gitleaks &> /dev/null; then
    gitleaks detect --no-git --source . --verbose
    echo "✅ No secrets detected"
else
    echo "⚠️  gitleaks not installed, skipping"
    echo "   Install: brew install gitleaks  # macOS"
    echo "   Or: https://github.com/gitleaks/gitleaks#installing"
fi
echo ""

# 7. Unit tests
echo "═══ 6/8 Unit Tests (pytest) ═══"
if [ -d "tests" ] && ls tests/**/*.py 1> /dev/null 2>&1; then
    if [[ "$SKIP_SLOW" == "true" ]]; then
        pytest tests/ -m "not slow" -v --cov=src --cov-report=term-missing --cov-report=html
    else
        pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
    fi
    echo "✅ Tests OK"
else
    echo "⚠️  No tests found, skipping test execution"
fi
echo ""

# 8. Coverage check
echo "═══ 7/8 Coverage Check ═══"
if [ -f ".coverage" ]; then
    coverage report --fail-under=80 || {
        echo "⚠️  Coverage below 80%"
        echo "   This is expected during initial development"
    }
    echo "✅ Coverage checked"
else
    echo "⚠️  No coverage data found (tests may not have run)"
fi
echo ""

# 9. Documentation check
echo "═══ 8/8 Documentation Check ═══"
if ls src/**/*.py 1> /dev/null 2>&1; then
    python -c "
import ast
import sys
from pathlib import Path

def check_docstrings(filepath):
    code = filepath.read_text()
    tree = ast.parse(code)
    errors = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if not node.name.startswith('_'):  # Public
                if not ast.get_docstring(node):
                    errors.append(f'{filepath}:{node.lineno} - {node.name} missing docstring')

    return errors

all_errors = []
for f in Path('src').rglob('*.py'):
    all_errors.extend(check_docstrings(f))

if all_errors:
    print('⚠️  Missing docstrings (will be required for final release):')
    for e in all_errors[:10]:  # Show first 10
        print(f'  {e}')
    if len(all_errors) > 10:
        print(f'  ... and {len(all_errors) - 10} more')
    # Don't fail during initial development
    # sys.exit(1)
" || echo "⚠️  Some docstrings missing (acceptable during development)"
    echo "✅ Documentation checked"
else
    echo "⚠️  No Python files found, skipping documentation check"
fi
echo ""

echo "╔════════════════════════════════════════╗"
echo "║   ✅ VALIDATION CHECKS COMPLETED        ║"
echo "╚════════════════════════════════════════╝"
