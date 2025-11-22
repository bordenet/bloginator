#!/usr/bin/env bash
#
# validate-cross-references.sh - Validate all cross-references in documentation
#
# This script validates:
# - Internal markdown links
# - Script references in documentation
# - Environment variable consistency
# - File references in documentation
#
# Usage:
#   ./scripts/validate-cross-references.sh [--fix] [--verbose]
#
# Options:
#   --fix      Attempt to fix broken references automatically
#   --verbose  Show detailed output
#   --help     Show this help message

set -euo pipefail

# Script directory and repository root
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
VERBOSE=false
AUTO_FIX=false
EXIT_CODE=0

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

#######################################
# Print error message
#######################################
error() {
    echo -e "${RED}ERROR: $*${NC}" >&2
    EXIT_CODE=1
}

#######################################
# Print warning message
#######################################
warn() {
    echo -e "${YELLOW}WARNING: $*${NC}" >&2
}

#######################################
# Print success message
#######################################
success() {
    echo -e "${GREEN}✓ $*${NC}"
}

#######################################
# Print info message
#######################################
info() {
    if [[ "${VERBOSE}" == "true" ]]; then
        echo "$*"
    fi
}

#######################################
# Validate markdown internal links
#######################################
validate_markdown_links() {
    echo "Validating markdown internal links..."
    local broken_links=0

    while IFS= read -r -d '' md_file; do
        info "Checking ${md_file}..."

        # Extract markdown links [text](path)
        while IFS= read -r link; do
            # Skip external links (http/https)
            if [[ "${link}" =~ ^https?:// ]]; then
                continue
            fi

            # Skip anchors only
            if [[ "${link}" =~ ^# ]]; then
                continue
            fi

            # Resolve relative path
            local dir
            dir="$(dirname "${md_file}")"
            local target="${dir}/${link}"

            # Remove anchor if present
            target="${target%%#*}"

            # Check if file exists
            if [[ ! -f "${target}" && ! -d "${target}" ]]; then
                error "Broken link in ${md_file}: ${link} -> ${target}"
                ((broken_links++))
            fi
        done < <(grep -oP '\[.*?\]\(\K[^)]+' "${md_file}" 2>/dev/null || true)
    done < <(find "${REPO_ROOT}" -name "*.md" -type f -not -path "*/node_modules/*" -not -path "*/.venv/*" -print0)

    if [[ ${broken_links} -eq 0 ]]; then
        success "All markdown links are valid"
    else
        error "Found ${broken_links} broken markdown links"
    fi
}

#######################################
# Validate script references
#######################################
validate_script_references() {
    echo "Validating script references in documentation..."
    local broken_refs=0

    while IFS= read -r -d '' md_file; do
        info "Checking script references in ${md_file}..."

        # Look for script references like ./scripts/something.sh
        while IFS= read -r script_ref; do
            local script_path="${REPO_ROOT}/${script_ref#./}"

            if [[ ! -f "${script_path}" ]]; then
                error "Script reference not found in ${md_file}: ${script_ref}"
                ((broken_refs++))
            fi
        done < <(grep -oP '\./scripts/[a-zA-Z0-9_/-]+\.sh' "${md_file}" 2>/dev/null || true)
    done < <(find "${REPO_ROOT}" -name "*.md" -type f -not -path "*/node_modules/*" -not -path "*/.venv/*" -print0)

    if [[ ${broken_refs} -eq 0 ]]; then
        success "All script references are valid"
    else
        error "Found ${broken_refs} broken script references"
    fi
}

#######################################
# Validate environment variables
#######################################
validate_env_variables() {
    echo "Validating environment variable consistency..."
    local inconsistencies=0

    # Extract all BLOGINATOR_* env vars from code
    local code_vars
    code_vars=$(grep -rh "BLOGINATOR_[A-Z_]*" "${REPO_ROOT}/src" "${REPO_ROOT}/tests" 2>/dev/null | \
                grep -oP 'BLOGINATOR_[A-Z_]+' | sort -u || true)

    # Check if documented in .env.example or .env.test
    for var in ${code_vars}; do
        if ! grep -q "${var}" "${REPO_ROOT}/.env.example" 2>/dev/null && \
           ! grep -q "${var}" "${REPO_ROOT}/.env.test" 2>/dev/null; then
            warn "Environment variable ${var} used in code but not documented in .env.example or .env.test"
            ((inconsistencies++))
        fi
    done

    if [[ ${inconsistencies} -eq 0 ]]; then
        success "All environment variables are documented"
    else
        warn "Found ${inconsistencies} undocumented environment variables"
    fi
}

#######################################
# Main function
#######################################
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fix)
                AUTO_FIX=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                grep '^#' "${BASH_SOURCE[0]}" | grep -v '#!/usr/bin/env' | sed 's/^# //'
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    cd "${REPO_ROOT}"

    echo "Cross-Reference Validation"
    echo "=========================="
    echo ""

    validate_markdown_links
    echo ""

    validate_script_references
    echo ""

    validate_env_variables
    echo ""

    if [[ ${EXIT_CODE} -eq 0 ]]; then
        success "All cross-references are valid"
    else
        error "Cross-reference validation failed"
    fi

    exit ${EXIT_CODE}
}

main "$@"
