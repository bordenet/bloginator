#!/usr/bin/env bash

################################################################################
# Purge Bloginator Corpus and Outputs
################################################################################
#
# NAME
#   purge-corpus-and-outputs.sh - Reset Bloginator workspace to clean state
#
# SYNOPSIS
#   purge-corpus-and-outputs.sh [-y|--yes] [-v|--verbose] [-n|--what-if]
#                               [--wipe-shadow-copies] [-h|--help]
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
# PRESERVES (by default)
#   .env                         Environment configuration (NEVER touched)
#   corpus/*.yaml                Corpus configuration files
#   .bloginator/templates/       Custom prompt templates
#   .bloginator/blocklist.json   Proprietary term blocklist
#   /tmp/bloginator/corpus_shadow/  Shadow copies of source files (for offline)
#
# OPTIONS
#   -y, --yes              Auto-confirm all prompts (non-interactive mode)
#   -v, --verbose          Show detailed output for each operation
#   -n, --what-if          Show what would be deleted without actually deleting
#   --wipe-shadow-copies   DANGEROUS: Also delete /tmp/bloginator/corpus_shadow/
#                          Requires explicit confirmation (10s timeout, default No)
#   -h, --help             Display this help message and exit
#
# EXAMPLES
#   Interactive cleanup:
#     ./scripts/purge-corpus-and-outputs.sh
#
#   Non-interactive (for CI/scripts):
#     ./scripts/purge-corpus-and-outputs.sh -y
#
#   Preview what would be deleted:
#     ./scripts/purge-corpus-and-outputs.sh --what-if
#
#   Full wipe including shadow copies (DANGEROUS when offline):
#     ./scripts/purge-corpus-and-outputs.sh -y --wipe-shadow-copies
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
WHAT_IF=false
WIPE_SHADOW_COPIES=false

# Load paths from .env
load_env_config

# Derived paths
EXTRACTED_DIR="${BLOGINATOR_OUTPUT_DIR}/extracted"
GENERATED_DIR="${BLOGINATOR_OUTPUT_DIR}/generated"
LLM_REQUESTS_DIR="${BLOGINATOR_DATA_DIR}/llm_requests"
LLM_RESPONSES_DIR="${BLOGINATOR_DATA_DIR}/llm_responses"
HISTORY_DIR="${BLOGINATOR_DATA_DIR}/history"
SHADOW_COPY_DIR="/tmp/bloginator/corpus_shadow"

################################################################################
# Helper Functions
################################################################################

show_help() {
    # Extract and display the header documentation (lines 2-63)
    sed -n '2,63p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
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

# Confirm with timeout - for dangerous operations
# Returns 1 (false) if timeout expires or user says no
confirm_with_timeout() {
    local prompt="$1"
    local timeout_seconds="${2:-10}"

    if [[ "$AUTO_YES" == "true" ]]; then
        echo "⚠️  Auto-confirming dangerous operation (--yes was specified)"
        return 0
    fi

    echo ""
    echo "⚠️  $prompt"
    echo "    This operation cannot be undone when offline."
    echo "    Defaulting to 'No' in ${timeout_seconds} seconds..."
    echo ""

    local response=""
    if read -r -t "$timeout_seconds" -p "Type 'yes' to confirm: " response; then
        if [[ "$response" == "yes" ]]; then
            return 0
        fi
    fi

    echo ""
    echo "Operation cancelled (timeout or declined)."
    return 1
}

log_verbose() {
    if [[ "$VERBOSE" -eq 1 ]]; then
        echo "  $*"
    fi
}

# Execute or simulate based on --what-if flag
do_remove() {
    local target="$1"
    local description="$2"

    if [[ ! -e "$target" ]]; then
        log_verbose "$target not found, skipping"
        return 0
    fi

    if [[ "$WHAT_IF" == "true" ]]; then
        echo "  [WHAT-IF] Would remove: $target"
        return 0
    fi

    task_start "$description"
    rm -rf "$target"
    task_ok "${description} - done"
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
        -n|--what-if)
            WHAT_IF=true
            shift
            ;;
        --wipe-shadow-copies)
            WIPE_SHADOW_COPIES=true
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

# Calculate shadow copy size if it exists
SHADOW_SIZE="(not present)"
if [[ -d "$SHADOW_COPY_DIR" ]]; then
    SHADOW_SIZE="$(du -sh "$SHADOW_COPY_DIR" 2>/dev/null | cut -f1 || echo "unknown")"
fi

echo "🧹 Bloginator Cleanup"
echo "====================="
if [[ "$WHAT_IF" == "true" ]]; then
    echo "  [WHAT-IF MODE - No changes will be made]"
fi
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
echo "  • .env, corpus/*.yaml, ${BLOGINATOR_DATA_DIR}/templates/"
echo "  • ${BLOGINATOR_DATA_DIR}/blocklist.json"
echo "  • $SHADOW_COPY_DIR/ ($SHADOW_SIZE) - source file shadow copies"
if [[ "$WIPE_SHADOW_COPIES" == "true" ]]; then
    echo ""
    echo "⚠️  --wipe-shadow-copies specified: Shadow copies WILL be deleted"
fi
echo ""

if [[ "$WHAT_IF" != "true" ]]; then
    if ! confirm "Proceed with cleanup?"; then
        echo "Aborted."
        exit 0
    fi
fi

echo ""

# Use bloginator history clear if available (uses API)
if command -v bloginator &> /dev/null; then
    if [[ -d "$HISTORY_DIR" ]] && [[ -n "$(ls -A "$HISTORY_DIR" 2>/dev/null)" ]]; then
        if [[ "$WHAT_IF" == "true" ]]; then
            echo "  [WHAT-IF] Would clear generation history via CLI"
        else
            task_start "Clearing generation history via CLI"
            bloginator history clear --yes 2>/dev/null || true
            task_ok "History cleared"
        fi
    fi
fi

# Clear standard directories
do_remove "$EXTRACTED_DIR" "Removing extracted documents"
do_remove "$GENERATED_DIR" "Removing generated content"
do_remove "$BLOGINATOR_CHROMA_DIR" "Removing ChromaDB index"
do_remove "chroma_db" "Removing legacy ChromaDB"
do_remove "$LLM_REQUESTS_DIR" "Removing LLM request files"
do_remove "$LLM_RESPONSES_DIR" "Removing LLM response files"

# Handle shadow copy deletion (dangerous operation)
if [[ "$WIPE_SHADOW_COPIES" == "true" ]]; then
    if [[ -d "$SHADOW_COPY_DIR" ]]; then
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "⚠️  SHADOW COPY DELETION REQUESTED"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        echo "Shadow copy directory: $SHADOW_COPY_DIR"
        echo "Size: $SHADOW_SIZE"
        echo ""
        echo "This contains cached copies of files from:"
        echo "  • SMB network shares (NAS)"
        echo "  • OneDrive cloud files"
        echo ""
        echo "If you delete these while offline, you will NOT be able to"
        echo "re-extract or re-index your corpus until you're back online."
        echo ""

        if [[ "$WHAT_IF" == "true" ]]; then
            echo "  [WHAT-IF] Would delete: $SHADOW_COPY_DIR/"
        elif confirm_with_timeout "Delete shadow copies?" 10; then
            task_start "Removing shadow copies"
            rm -rf "$SHADOW_COPY_DIR"
            task_ok "Shadow copies removed"
        else
            echo "Shadow copies preserved."
        fi
    else
        log_verbose "$SHADOW_COPY_DIR not found, skipping"
    fi
fi

# Ensure output directory exists (but empty)
if [[ "$WHAT_IF" != "true" ]]; then
    mkdir -p "$BLOGINATOR_OUTPUT_DIR"
fi

echo ""
if [[ "$WHAT_IF" == "true" ]]; then
    task_ok "What-if preview complete (no changes made)"
else
    task_ok "Cleanup complete!"
fi
echo ""
echo "Next steps:"
echo "  1. Extract:  bloginator extract --config corpus/corpus.yaml -o $EXTRACTED_DIR"
echo "  2. Index:    bloginator index $EXTRACTED_DIR -o $BLOGINATOR_CHROMA_DIR"
echo "  3. Generate: bloginator outline --index $BLOGINATOR_CHROMA_DIR --title 'My Blog'"
