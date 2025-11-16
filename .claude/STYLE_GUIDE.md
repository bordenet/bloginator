# Bloginator Shell Script Style Guide

This document establishes coding standards for shell scripts in the Bloginator project, ensuring consistency and maintainability across the codebase.

## Core Principles

1. **Consistency over cleverness** - Write readable, maintainable code that the next developer can understand
2. **Fail fast** - Use `set -euo pipefail` in all scripts to catch errors immediately
3. **Clear messages** - Log every significant action so users understand what's happening
4. **Standard library** - Leverage `scripts/lib/common.sh` for common functions

## File Structure

Every shell script must begin with a standardized header:

```bash
#!/usr/bin/env bash
#
# Script Name
#
# Purpose:
#   Brief description of what this script does
#   Key responsibilities listed here
#
# Usage:
#   ./script-name.sh [options]
#   ./script-name.sh --help
#
# Options:
#   -h, --help    Show help message
#   --verbose     Enable verbose output
#
# Dependencies:
#   - bash 4.0+
#   - python3
#   - Additional tools listed here
```

All scripts should:
- Source the common library: `source "${REPO_ROOT}/scripts/lib/common.sh"`
- Call `init_script` to set up error handling
- Use the repository root as the working directory

## Error Handling

### Required Safeguards

Every script must include:

```bash
set -euo pipefail
```

This ensures:
- `set -e`: Exit on any command failure
- `set -u`: Exit on undefined variable usage
- `set -o pipefail`: Catch errors in piped commands

### Initialization

After sourcing the common library, initialize error handling:

```bash
source "${REPO_ROOT}/scripts/lib/common.sh"
init_script
```

### Validation Functions

Use library functions to validate prerequisites:

```bash
# Require a command
require_command python3 "Python 3 is required. Install with: brew install python@3.10"

# Require a file
require_file "${REPO_ROOT}/pyproject.toml" "pyproject.toml not found"

# Require a directory
require_directory "$VENV_DIR" "Virtual environment not found"
```

### Explicit Checks

For critical operations, add explicit validation:

```bash
if ! python3 -m pytest tests/; then
    log_error "Tests failed"
    return 1
fi
```

## Logging Standards

### Use Library Functions

Always use logging functions from `common.sh` instead of raw `echo`:

```bash
log_info "Starting validation..."         # Informational messages
log_success "Validation completed"         # Completed operations
log_warning "Skipping optional step"       # Non-fatal issues
log_error "Test suite failed"              # Errors (script continues)
die "Python not found"                     # Fatal errors (script exits)
log_debug "Variable value: $foo"           # Debug data (DEBUG=1 only)
log_header "Build & Test"                  # Major section dividers
log_section "Running Unit Tests"           # Subsection titles
```

### Message Formatting

- **Ongoing actions**: Use present continuous tense
  - ✓ "Installing dependencies..."
  - ✗ "Install dependencies..."

- **Completed actions**: Use past tense
  - ✓ "Dependencies installed"
  - ✗ "Dependencies install"

- **Descriptions**: Use present tense
  - ✓ "This script validates the codebase"
  - ✗ "This script will validate the codebase"

### Levels and When to Use Them

| Function | Use Case | Example |
|----------|----------|---------|
| `log_info` | Normal operation steps | "Activating virtual environment..." |
| `log_success` | Confirmation of success | "All tests passed" |
| `log_warning` | Non-fatal issues | "Gitleaks not installed, skipping" |
| `log_error` | Errors, script continues | "Linting failed" |
| `die` | Fatal errors, exit immediately | "Python 3.10+ required" |
| `log_debug` | Debug information | "VENV_DIR=/path/to/venv" |
| `log_header` | Major sections | "Environment Setup" |
| `log_section` | Subsections | "Installing Dependencies" |

## Variable Naming

### Constants

Use `readonly` for constants and all-caps with underscores:

```bash
readonly VENV_DIR="${REPO_ROOT}/.venv"
readonly PYTHON_VERSION="3.10"
readonly COVERAGE_THRESHOLD=80
```

### Configuration Variables

Use all-caps for configuration that might change:

```bash
RUN_TESTS=true
AUTO_FIX=false
VERBOSE=false
```

### Local Variables

Use lowercase with underscores for local/temporary variables:

```bash
local python_version
python_version=$(python3 --version)

local packages=("black" "ruff" "mypy")
```

### Path Variables

End path variables with `_DIR` or `_FILE`:

```bash
readonly REPO_ROOT="$(git rev-parse --show-toplevel)"
readonly SRC_DIR="${REPO_ROOT}/src"
readonly TESTS_DIR="${REPO_ROOT}/tests"
readonly CONFIG_FILE="${REPO_ROOT}/pyproject.toml"
```

## Function Guidelines

### Naming Conventions

Use descriptive names following these patterns:

**Action verbs** for functions that do something:
```bash
install_python()
setup_environment()
run_tests()
download_ml_models()
```

**Question functions** for boolean checks (return 0 or 1):
```bash
is_macos()
is_venv_active()
has_python()
```

**Getter functions** for retrieving values:
```bash
get_repo_root()
get_python_version()
```

### Function Documentation

Document functions with comments explaining:
- What it does
- Global variables it uses/modifies
- Arguments it takes
- Return values

```bash
#######################################
# Install Python via Homebrew
# Globals:
#   PYTHON_VERSION
#   VERBOSE
# Arguments:
#   None
# Returns:
#   0 if successful, 1 on failure
#######################################
install_python() {
    log_section "Installing Python"
    # ... implementation
}
```

### Error Handling in Functions

Functions should return proper exit codes:

```bash
validate_code() {
    if ! python3 -m black --check src/; then
        log_error "Formatting check failed"
        return 1
    fi
    return 0
}
```

## Command Execution

### Quiet vs Verbose Output

Provide both modes for command execution:

```bash
run_quiet() {
    if [[ "$VERBOSE" == "true" ]]; then
        "$@"
    else
        "$@" &>/dev/null
    fi
}

# Usage
run_quiet brew install python@3.10
```

### Command Validation

Always validate critical commands succeeded:

```bash
if python3 -m pytest tests/; then
    log_success "Tests passed"
else
    log_error "Tests failed"
    return 1
fi
```

### Using the `run_command` Helper

For operations that should be logged:

```bash
run_command "Installing dependencies" python3 -m pip install -e ".[dev]"
```

## Comments

### What to Comment

Comment the **why**, not the **what**:

✓ Good:
```bash
# ChromaDB requires a specific version of numpy for Apple Silicon
python3 -m pip install "numpy<2.0"
```

✗ Bad:
```bash
# Install numpy
python3 -m pip install numpy
```

### When to Comment

Add comments for:
- **Workarounds**: Explain why a non-obvious solution is needed
- **Edge cases**: Document special handling
- **Complex logic**: Clarify multi-step operations
- **Dependencies**: Note version constraints or platform-specific requirements

### Comment Style

Use single-line comments for brief explanations:
```bash
# Activate virtual environment for isolated dependencies
source "$VENV_DIR/bin/activate"
```

Use block comments for function documentation (see Function Guidelines above).

## Testing Shell Scripts

### Manual Testing Checklist

Before committing, test your script with:

- [ ] Fresh clone (no dependencies installed)
- [ ] All dependencies already installed (idempotency)
- [ ] With `--verbose` flag
- [ ] With `--help` flag
- [ ] Invalid arguments
- [ ] Missing required files
- [ ] In both interactive and non-interactive modes

### Shellcheck

All scripts should pass shellcheck:

```bash
shellcheck validate-monorepo.sh
shellcheck scripts/setup-macos.sh
shellcheck scripts/lib/common.sh
```

Add shellcheck directives when necessary:

```bash
# shellcheck disable=SC1091  # Can't follow sourced file
source "${REPO_ROOT}/scripts/lib/common.sh"
```

## Anti-Patterns

### Don't Do This

❌ **Relative paths from unknown locations**
```bash
cd ../../src  # Where are we starting from?
```

✓ **Absolute paths from repo root**
```bash
cd "${REPO_ROOT}/src"
```

❌ **Raw echo for messages**
```bash
echo "Installing dependencies..."
```

✓ **Logging functions**
```bash
log_info "Installing dependencies..."
```

❌ **Unvalidated commands**
```bash
python3 -m pip install -e .
```

✓ **Validated with feedback**
```bash
if python3 -m pip install -e .; then
    log_success "Dependencies installed"
else
    die "Failed to install dependencies"
fi
```

❌ **Magic values**
```bash
if [[ "$exit_code" -eq 42 ]]; then
```

✓ **Named constants**
```bash
readonly EXIT_CODE_MISSING_DEPENDENCY=42
if [[ "$exit_code" -eq "$EXIT_CODE_MISSING_DEPENDENCY" ]]; then
```

❌ **Silent failures**
```bash
brew install python@3.10 2>/dev/null || true
```

✓ **Explicit handling**
```bash
if ! brew install python@3.10; then
    log_warning "Failed to install Python, trying alternative method..."
    # ... fallback logic
fi
```

## Platform-Specific Code

Use helper functions for platform detection:

```bash
if is_macos; then
    brew install gitleaks
elif is_linux; then
    apt-get install gitleaks
else
    log_warning "Unsupported platform: $OSTYPE"
fi
```

## Exit Codes

Use standard exit codes:

- `0` - Success
- `1` - General error
- `2` - Misuse of command (invalid arguments)

```bash
main() {
    # ... validation logic

    if [[ $ERROR_COUNT -eq 0 ]]; then
        log_success "Validation passed"
        exit 0
    else
        log_error "Validation failed with $ERROR_COUNT errors"
        exit 1
    fi
}
```

## Example: Well-Structured Script

```bash
#!/usr/bin/env bash
#
# Example Script Following Style Guide
#
# Purpose:
#   Demonstrates proper structure and style for Bloginator shell scripts
#
# Usage:
#   ./example.sh [--verbose] [--help]
#
# Dependencies:
#   - bash 4.0+
#   - python3

set -euo pipefail

# Repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Source common library
# shellcheck disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

# Initialize script
init_script

# Configuration
readonly VENV_DIR="${REPO_ROOT}/.venv"
VERBOSE=false

#######################################
# Parse command line arguments
# Globals:
#   VERBOSE
# Arguments:
#   $@ - Command line arguments
# Returns:
#   None
#######################################
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                grep '^#' "$0" | sed 's/^# //'
                exit 0
                ;;
            *)
                die "Unknown option: $1"
                ;;
        esac
    done
}

#######################################
# Main workflow
#######################################
main() {
    log_header "Example Script"

    parse_args "$@"

    log_section "Running Example Task"
    log_info "This is how we do things in Bloginator"

    # ... implementation

    print_summary
}

main "$@"
```

## Additional Resources

- **Bash Best Practices**: https://google.github.io/styleguide/shellguide.html
- **Shellcheck**: https://www.shellcheck.net/
- **Common Library**: `scripts/lib/common.sh` in this repository

## Maintenance

This style guide should be updated when:
- New patterns emerge that should be standardized
- Better approaches are discovered
- The codebase evolves with new requirements

Last updated: 2025-11-16
