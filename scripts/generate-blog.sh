#!/bin/bash
# ⚠️  DEPRECATED: This script uses the template-based auto-responder which
#    produces low-quality, generic content. Do NOT use for production blogs.
#
#    For quality blog generation, use BLOGINATOR_LLM_MOCK=assistant mode
#    with an AI assistant providing responses. See docs/QUICK_START_GUIDE.md.

set -e

# Emit deprecation warning
echo ""
echo "⚠️  WARNING: generate-blog.sh is DEPRECATED and produces low-quality content."
echo "   This script uses hardcoded template responses, not actual AI generation."
echo ""
echo "   For quality blogs, use the manual workflow with BLOGINATOR_LLM_MOCK=assistant:"
echo "     1. export BLOGINATOR_LLM_MOCK=assistant"
echo "     2. bloginator outline --index .bloginator/index --title '...' -o outline.json"
echo "     3. Respond to requests in .bloginator/llm_requests/ manually"
echo "     4. bloginator draft --index .bloginator/index --outline outline.json -o draft.md"
echo ""
echo "   See docs/QUICK_START_GUIDE.md for the full workflow."
echo ""
read -p "Press Enter to continue anyway (Ctrl+C to abort)..."

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load common functions and configuration
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_env_config

# Derived paths
INDEX_DIR="${BLOGINATOR_CHROMA_DIR}"
LLM_REQUESTS_DIR="${BLOGINATOR_DATA_DIR}/llm_requests"
LLM_RESPONSES_DIR="${BLOGINATOR_DATA_DIR}/llm_responses"

# Check if blog parameters are provided
if [ $# -lt 5 ]; then
    echo "Usage: $0 <output_file> <title> <thesis> <keywords> <outline_file>"
    echo "Example: $0 ${BLOGINATOR_OUTPUT_DIR}/generated/blog2-planning.md 'Sprint Planning' 'Effective sprint planning...' 'sprint,planning,agile' ${BLOGINATOR_OUTPUT_DIR}/generated/blog2-outline.json"
    exit 1
fi

OUTPUT_FILE="$1"
TITLE="$2"
THESIS="$3"
KEYWORDS="$4"
OUTLINE_FILE="$5"

echo "=== Generating Blog: $TITLE ==="

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "venv311" ]; then
    source venv311/bin/activate
else
    echo "Error: No virtual environment found at venv/ or venv311/"
    exit 1
fi

AUTO_RESPOND_PY="${PROJECT_ROOT}/scripts/respond-to-llm-requests.py"

# Clean request/response directories
rm -f "$LLM_REQUESTS_DIR"/* "$LLM_RESPONSES_DIR"/* 2>/dev/null || true

# Start continuous auto-responder in background
echo "Starting continuous auto-responder..."
(
    while true; do
        python3 "$AUTO_RESPOND_PY" 2>&1 | grep -E "(✓|Generated)" || true
        sleep 1
    done
) &
RESPONDER_PID=$!

# Ensure we kill the responder on exit
trap "kill $RESPONDER_PID 2>/dev/null || true" EXIT

# Generate outline
echo "Generating outline..."
bloginator outline --index "$INDEX_DIR" \
    --keywords "$KEYWORDS" \
    --title "$TITLE" \
    --thesis "$THESIS" \
    -o "$OUTLINE_FILE"

echo "Outline complete: $OUTLINE_FILE"

# Wait a moment for any final responses
sleep 2

# Clean request/response directories for draft
rm -f "$LLM_REQUESTS_DIR"/* "$LLM_RESPONSES_DIR"/*

# Generate draft
echo "Generating draft..."
bloginator draft --index "$INDEX_DIR" \
    --outline "$OUTLINE_FILE" \
    -o "$OUTPUT_FILE"

echo "Draft complete: $OUTPUT_FILE"
wc -w "$OUTPUT_FILE"

# Kill the responder
kill $RESPONDER_PID 2>/dev/null || true

echo "=== Blog generation complete ==="
