#!/usr/bin/env bash

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

# Add a path to the cleanup queue for processing later
add_to_cleanup_queue() {
    local path="$1"
    local description="$2"
    if [[ -e "$path" ]]; then
        CLEANUP_PATHS+=("$path")
        CLEANUP_DESCRIPTIONS+=("$description")
    else
        log_verbose "Target '$path' not found, skipping."
    fi
}

# Process the queued paths: report size and file counts, then optionally delete
process_cleanup_queue() {
    local title="$1"
    local confirmation_prompt="$2"
    local confirmation_fn=${3:-confirm}

    if [ ${#CLEANUP_PATHS[@]} -eq 0 ]; then
        log_verbose "No items in queue for '$title', skipping."
        return 0
    fi

    echo "$title"
    local total_files=0
    local total_size_bytes=0
    local report_lines=()

    # Create a detailed report
    for i in "${!CLEANUP_PATHS[@]}"; do
        local path="${CLEANUP_PATHS[i]}"
        local desc="${CLEANUP_DESCRIPTIONS[i]}"
        local file_count
        file_count=$(find "$path" -type f 2>/dev/null | wc -l | tr -d ' ')
        local size_bytes=0
        local size_human="0B"

        if [[ "$file_count" -gt 0 ]]; then
            # Use -sk for kilobytes (macOS compatible) and convert to bytes
            local size_kb
            size_kb=$(du -sk "$path" 2>/dev/null | awk '{print $1}')
            size_bytes=$((size_kb * 1024))
            size_human=$(du -sh "$path" 2>/dev/null | awk '{print $1}')
        fi

        total_files=$((total_files + file_count))
        total_size_bytes=$((total_size_bytes + size_bytes))
        report_lines+=("$(printf "  • %-24s -> %-25s (%d files, %s)" "$desc" "$path" "$file_count" "$size_human")")
    done

    # Print the report
    for line in "${report_lines[@]}"; do
        echo "$line"
    done

    local total_size_human
    total_size_human=$(echo "$total_size_bytes" | numfmt --to=iec-i --suffix=B --format="%.1f")
    echo "--------------------------------------------------------------------------------"
    printf "  TOTAL: %d files, %s\n\n" "$total_files" "$total_size_human"

    # Handle what-if mode or get confirmation
    if [[ "$WHAT_IF" == "true" ]]; then
        echo "  [WHAT-IF MODE] No files will be deleted."
        # Clear the queue for the next potential processing group (e.g., shadow copies)
        CLEANUP_PATHS=()
        CLEANUP_DESCRIPTIONS=()
        return 0
    fi

    if $confirmation_fn "$confirmation_prompt"; then
        task_start "Removing ${#CLEANUP_PATHS[@]} locations"
        for path in "${CLEANUP_PATHS[@]}"; do
            rm -rf "$path"
        done
        task_ok "${#CLEANUP_PATHS[@]} locations removed"
    else
        echo "Cleanup for '$title' cancelled."
    fi

    # Reset queue for next run
    CLEANUP_PATHS=()
    CLEANUP_DESCRIPTIONS=()
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

# Set up the cleanup queue
declare -a CLEANUP_PATHS=()
declare -a CLEANUP_DESCRIPTIONS=()

# Use bloginator history clear if available (uses API)
if command -v bloginator &> /dev/null; then
    if [[ -d "$HISTORY_DIR" ]] && [[ -n "$(ls -A "$HISTORY_DIR" 2>/dev/null)" ]]; then
        if [[ "$WHAT_IF" == "true" ]]; then
            echo "  [WHAT-IF] Would clear generation history via: 'bloginator history clear --yes'"
        else
            task_start "Clearing generation history via CLI"
            bloginator history clear --yes 2>/dev/null || true
            task_ok "History cleared"
        fi
    fi
fi

# Queue standard directories for removal
add_to_cleanup_queue "$EXTRACTED_DIR" "Extracted documents"
add_to_cleanup_queue "$GENERATED_DIR" "Generated content"
add_to_cleanup_queue "$BLOGINATOR_CHROMA_DIR" "ChromaDB index"
add_to_cleanup_queue "chroma_db" "Legacy ChromaDB"
add_to_cleanup_queue "$LLM_REQUESTS_DIR" "LLM request files"
add_to_cleanup_queue "$LLM_RESPONSES_DIR" "LLM response files"

# Process the main cleanup queue
process_cleanup_queue "The following standard items will be removed:" "Proceed with standard cleanup?"

# Handle shadow copy deletion (dangerous operation)
if [[ "$WIPE_SHADOW_COPIES" == "true" ]]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "⚠️  SHADOW COPY DELETION REQUESTED"
    echo "═══════════════════════════════════════════════════════════════"

    add_to_cleanup_queue "$SHADOW_COPY_DIR" "Shadow copies"

    process_cleanup_queue "The following shadow copy items will be removed:" "Delete shadow copies?" "confirm_with_timeout"
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
