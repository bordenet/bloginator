#!/bin/bash
# Improved blog generation script with better auto-respond coordination

set -e

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if blog parameters are provided
if [ $# -lt 5 ]; then
    echo "Usage: $0 <output_file> <title> <thesis> <keywords> <outline_file>"
    echo "Example: $0 output/generated/blog2-planning.md 'Sprint Planning' 'Effective sprint planning...' 'sprint,planning,agile' output/generated/blog2-outline.json"
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

AUTO_RESPOND_PY="${PROJECT_ROOT}/scripts/auto_respond.py"

# Clean request/response directories
rm -f .bloginator/llm_requests/* .bloginator/llm_responses/* 2>/dev/null || true

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
bloginator outline --index output/index \
    --keywords "$KEYWORDS" \
    --title "$TITLE" \
    --thesis "$THESIS" \
    -o "$OUTLINE_FILE"

echo "Outline complete: $OUTLINE_FILE"

# Wait a moment for any final responses
sleep 2

# Clean request/response directories for draft
rm -f .bloginator/llm_requests/* .bloginator/llm_responses/*

# Generate draft
echo "Generating draft..."
bloginator draft --index output/index \
    --outline "$OUTLINE_FILE" \
    -o "$OUTPUT_FILE"

echo "Draft complete: $OUTPUT_FILE"
wc -w "$OUTPUT_FILE"

# Kill the responder
kill $RESPONDER_PID 2>/dev/null || true

echo "=== Blog generation complete ==="
