#!/usr/bin/env bash

################################################################################
# Bloginator Corpus and Outputs Cleanup
################################################################################
#
# NAME
#   corpus-and-outputs-cleanup.sh - Reset Bloginator workspace to clean state
#
# SYNOPSIS
#   corpus-and-outputs-cleanup.sh [-y|--yes] [-v|--verbose] [-h|--help]
#
# DESCRIPTION
#   Cleans up all generated artifacts from Bloginator operations while
#   preserving configuration files. Uses bloginator CLI commands where
#   available to exercise the API, falling back to direct file operations
#   when necessary.
#
#   This script is intended for development and testing workflows where
#   you need to reset to a known clean state before running end-to-end tests.
#
# REMOVES
#   output/extracted/       Extracted document text and metadata
#   output/generated/       Generated outlines and drafts
#   .bloginator/chroma/     ChromaDB vector index
#   .bloginator/history/    Generation history (via CLI)
#   .bloginator/llm_*/      LLM request/response files
#   chroma_db/              Legacy ChromaDB location
#
# PRESERVES
#   .env                    Environment configuration (NEVER touched)
#   corpus/*.yaml           Corpus configuration files
#   .bloginator/templates/  Custom prompt templates
#   .bloginator/blocklist.json  Proprietary term blocklist
#
# OPTIONS
#   -y, --yes       Auto-confirm all prompts (non-interactive mode)
#   -v, --verbose   Show detailed output for each operation
#   -h, --help      Display this help message and exit
#
# EXAMPLES
#   Interactive cleanup:
#     ./scripts/corpus-and-outputs-cleanup.sh
#
#   Non-interactive (for CI/scripts):
#     ./scripts/corpus-and-outputs-cleanup.sh -y
#
#   Verbose output for debugging:
#     ./scripts/corpus-and-outputs-cleanup.sh -y -v
#
# EXIT STATUS
#   0   Cleanup completed successfully
#   1   User cancelled or error occurred
#
# AUTHOR
#   Bloginator Team
#
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

AUTO_YES=false
export VERBOSE=0

################################################################################
# Helper Functions
################################################################################

show_help() {
    # Extract and display the header documentation (lines 2-55)
    sed -n '2,55p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
    exit 0
}

confirm() {
    local prompt="$1"
    if [[ "$AUTO_YES" == "true" ]]; then
        return 0
    fi
    read -r -p "$prompt [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]]
}

log_verbose() {
    if [[ "$VERBOSE" -eq 1 ]]; then
        echo "  $*"
    fi
}

################################################################################
# Parse Arguments
################################################################################

while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes)
            AUTO_YES=true
            shift
            ;;
        -v|--verbose)
            export VERBOSE=1
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

################################################################################
# Main Cleanup
################################################################################

echo "🧹 Bloginator Cleanup"
echo "====================="
echo ""
echo "This will remove:"
echo "  • output/extracted/     (extracted documents)"
echo "  • output/generated/     (generated blogs)"
echo "  • .bloginator/chroma/   (vector index)"
echo "  • .bloginator/llm_*/    (LLM request/response files)"
echo "  • .bloginator/history/  (generation history)"
echo "  • chroma_db/            (legacy index location)"
echo ""
echo "Preserved:"
echo "  • .env, corpus/*.yaml, .bloginator/templates/, .bloginator/blocklist.json"
echo ""

if ! confirm "Proceed with cleanup?"; then
    echo "Aborted."
    exit 0
fi

echo ""

# Use bloginator history clear if available (uses API)
if command -v bloginator &> /dev/null; then
    if [[ -d ".bloginator/history" ]] && [[ -n "$(ls -A .bloginator/history 2>/dev/null)" ]]; then
        task_start "Clearing generation history via CLI"
        bloginator history clear --yes 2>/dev/null || true
        task_ok "History cleared"
    fi
fi

# Clear extracted documents
if [[ -d "output/extracted" ]]; then
    task_start "Removing output/extracted/"
    rm -rf output/extracted
    task_ok "Extracted documents removed"
else
    log_verbose "output/extracted/ not found, skipping"
fi

# Clear generated content
if [[ -d "output/generated" ]]; then
    task_start "Removing output/generated/"
    rm -rf output/generated
    task_ok "Generated content removed"
else
    log_verbose "output/generated/ not found, skipping"
fi

# Clear ChromaDB index
if [[ -d ".bloginator/chroma" ]]; then
    task_start "Removing .bloginator/chroma/"
    rm -rf .bloginator/chroma
    task_ok "ChromaDB index removed"
else
    log_verbose ".bloginator/chroma/ not found, skipping"
fi

# Clear legacy chroma_db location
if [[ -d "chroma_db" ]]; then
    task_start "Removing chroma_db/ (legacy)"
    rm -rf chroma_db
    task_ok "Legacy ChromaDB removed"
else
    log_verbose "chroma_db/ not found, skipping"
fi

# Clear LLM request/response files
if [[ -d ".bloginator/llm_requests" ]] || [[ -d ".bloginator/llm_responses" ]]; then
    task_start "Removing LLM request/response files"
    rm -rf .bloginator/llm_requests .bloginator/llm_responses
    task_ok "LLM files removed"
else
    log_verbose "LLM request/response dirs not found, skipping"
fi

# Ensure output directory exists (but empty)
mkdir -p output

echo ""
task_ok "Cleanup complete!"
echo ""
echo "Next steps:"
echo "  1. Extract:  bloginator extract --config corpus/sample.yaml -o output/extracted"
echo "  2. Index:    bloginator index output/extracted -o .bloginator/chroma"
echo "  3. Generate: bloginator outline --index .bloginator/chroma --title 'My Blog'"
