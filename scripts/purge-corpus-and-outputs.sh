#!/usr/bin/env bash

################################################################################
# Purge Bloginator Corpus and Outputs
################################################################################
#
# NAME
#   purge-corpus-and-outputs.sh - Reset Bloginator workspace to clean state
#
# SYNOPSIS
#   purge-corpus-and-outputs.sh [-y|--yes] [-v|--verbose] [-h|--help]
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
#   $BLOGINATOR_OUTPUT_DIR/extracted/  Extracted document text and metadata
#   $BLOGINATOR_OUTPUT_DIR/generated/  Generated outlines and drafts
#   $BLOGINATOR_CHROMA_DIR/            ChromaDB vector index
#   $BLOGINATOR_DATA_DIR/history/      Generation history (via CLI)
#   $BLOGINATOR_DATA_DIR/llm_*/        LLM request/response files
#   chroma_db/                         Legacy ChromaDB location
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
#     ./scripts/purge-corpus-and-outputs.sh
#
#   Non-interactive (for CI/scripts):
#     ./scripts/purge-corpus-and-outputs.sh -y
#
#   Verbose output for debugging:
#     ./scripts/purge-corpus-and-outputs.sh -y -v
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
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

# Navigate to project root
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

################################################################################
# Configuration
################################################################################

AUTO_YES=false
export VERBOSE=0

# Load paths from .env
load_env_config

# Derived paths
EXTRACTED_DIR="${BLOGINATOR_OUTPUT_DIR}/extracted"
GENERATED_DIR="${BLOGINATOR_OUTPUT_DIR}/generated"
LLM_REQUESTS_DIR="${BLOGINATOR_DATA_DIR}/llm_requests"
LLM_RESPONSES_DIR="${BLOGINATOR_DATA_DIR}/llm_responses"
HISTORY_DIR="${BLOGINATOR_DATA_DIR}/history"

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
echo "Using configuration from .env:"
echo "  DATA_DIR:   $BLOGINATOR_DATA_DIR"
echo "  OUTPUT_DIR: $BLOGINATOR_OUTPUT_DIR"
echo "  CHROMA_DIR: $BLOGINATOR_CHROMA_DIR"
echo ""
echo "This will remove:"
echo "  • $EXTRACTED_DIR/   (extracted documents)"
echo "  • $GENERATED_DIR/   (generated blogs)"
echo "  • $BLOGINATOR_CHROMA_DIR/   (vector index)"
echo "  • $LLM_REQUESTS_DIR/   (LLM request files)"
echo "  • $LLM_RESPONSES_DIR/  (LLM response files)"
echo "  • $HISTORY_DIR/   (generation history)"
echo "  • chroma_db/            (legacy index location)"
echo ""
echo "Preserved:"
echo "  • .env, corpus/*.yaml, ${BLOGINATOR_DATA_DIR}/templates/, ${BLOGINATOR_DATA_DIR}/blocklist.json"
echo ""

if ! confirm "Proceed with cleanup?"; then
    echo "Aborted."
    exit 0
fi

echo ""

# Use bloginator history clear if available (uses API)
if command -v bloginator &> /dev/null; then
    if [[ -d "$HISTORY_DIR" ]] && [[ -n "$(ls -A "$HISTORY_DIR" 2>/dev/null)" ]]; then
        task_start "Clearing generation history via CLI"
        bloginator history clear --yes 2>/dev/null || true
        task_ok "History cleared"
    fi
fi

# Clear extracted documents
if [[ -d "$EXTRACTED_DIR" ]]; then
    task_start "Removing $EXTRACTED_DIR/"
    rm -rf "$EXTRACTED_DIR"
    task_ok "Extracted documents removed"
else
    log_verbose "$EXTRACTED_DIR/ not found, skipping"
fi

# Clear generated content
if [[ -d "$GENERATED_DIR" ]]; then
    task_start "Removing $GENERATED_DIR/"
    rm -rf "$GENERATED_DIR"
    task_ok "Generated content removed"
else
    log_verbose "$GENERATED_DIR/ not found, skipping"
fi

# Clear ChromaDB index
if [[ -d "$BLOGINATOR_CHROMA_DIR" ]]; then
    task_start "Removing $BLOGINATOR_CHROMA_DIR/"
    rm -rf "$BLOGINATOR_CHROMA_DIR"
    task_ok "ChromaDB index removed"
else
    log_verbose "$BLOGINATOR_CHROMA_DIR/ not found, skipping"
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
if [[ -d "$LLM_REQUESTS_DIR" ]] || [[ -d "$LLM_RESPONSES_DIR" ]]; then
    task_start "Removing LLM request/response files"
    rm -rf "$LLM_REQUESTS_DIR" "$LLM_RESPONSES_DIR"
    task_ok "LLM files removed"
else
    log_verbose "LLM request/response dirs not found, skipping"
fi

# Ensure output directory exists (but empty)
mkdir -p "$BLOGINATOR_OUTPUT_DIR"

echo ""
task_ok "Cleanup complete!"
echo ""
echo "Next steps:"
echo "  1. Extract:  bloginator extract --config corpus/sample.yaml -o $EXTRACTED_DIR"
echo "  2. Index:    bloginator index $EXTRACTED_DIR -o $BLOGINATOR_CHROMA_DIR"
echo "  3. Generate: bloginator outline --index $BLOGINATOR_CHROMA_DIR --title 'My Blog'"
