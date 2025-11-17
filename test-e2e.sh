#!/usr/bin/env bash
################################################################################
# Script Name: test-e2e.sh
################################################################################
# PURPOSE: End-to-end test for Bloginator (search → outline → draft)
# USAGE: ./test-e2e.sh [OPTIONS]
# PLATFORM: Cross-platform (Linux/macOS)
################################################################################

# Strict error handling
set -euo pipefail

################################################################################
# Constants
################################################################################

# Colors for output
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

################################################################################
# Functions
################################################################################

# Function: show_help
# Description: Display help information
show_help() {
    cat << EOF
NAME
    test-e2e.sh - End-to-end test for Bloginator

SYNOPSIS
    test-e2e.sh [OPTIONS]

DESCRIPTION
    Tests the complete Bloginator workflow: corpus search, outline generation,
    and draft generation with full logging. Requires an indexed corpus.

OPTIONS
    -h, --help              Display this help message
    -v, --verbose           Show LLM request/response interactions
    -t, --title TITLE       Blog post title (default: "Building a DevOps Culture at Scale")
    -k, --keywords KEYWORDS Comma-separated keywords (default: "devops,kubernetes,automation,culture,collaboration,ci-cd")
    --thesis THESIS         Main thesis statement (default: "Effective DevOps culture requires both technical infrastructure AND organizational transformation")

EXAMPLES
    ./test-e2e.sh
        Run test with default title, keywords, and thesis

    ./test-e2e.sh --verbose
        Run test with verbose LLM output

    ./test-e2e.sh --title "Building a DevOps Culture at Scale" \\
        --keywords "devops,kubernetes,automation,culture,collaboration,ci-cd" \\
        --thesis "Effective DevOps culture requires both technical infrastructure AND organizational transformation"
        Run test with custom title, keywords, and thesis (these are the default values)

EXIT STATUS
    0   Success
    1   Error

AUTHOR
    Bloginator Project

EOF
}

################################################################################
# Main Script
################################################################################

# Parse arguments
VERBOSE=false
TITLE="Building a DevOps Culture at Scale"
KEYWORDS="devops,kubernetes,automation,culture,collaboration,ci-cd"
THESIS="Effective DevOps culture requires both technical infrastructure AND organizational transformation"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--title)
            TITLE="$2"
            shift 2
            ;;
        -k|--keywords)
            KEYWORDS="$2"
            shift 2
            ;;
        --thesis)
            THESIS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Setup logging
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/tmp/bloginator_test_${TIMESTAMP}"
mkdir -p "$LOG_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Bloginator End-to-End Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${GREEN}📁 Test Directory: ${LOG_DIR}${NC}"
echo ""

# Activate virtual environment
echo -e "${YELLOW}⚙️  Activating virtual environment...${NC}"
cd ~/GitHub/Personal/bloginator
# shellcheck disable=SC1091
source .venv/bin/activate

# Verify Ollama connectivity
echo -e "${YELLOW}🔌 Verifying Ollama connectivity...${NC}"
OLLAMA_HOST="http://mbp-14-m1.local:11434"
if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null; then
    echo -e "${GREEN}✓ Ollama server reachable at ${OLLAMA_HOST}${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Ollama server not reachable at ${OLLAMA_HOST}${NC}"
    echo -e "${YELLOW}   Check that Ollama is running and hostname is correct${NC}"
fi
echo ""

# Configuration
INDEX_PATH=".bloginator/chroma"

# Set verbose flag for commands
VERBOSE_FLAG=""
if [[ "$VERBOSE" == true ]]; then
    VERBOSE_FLAG="--verbose"
fi

# Note: Assumes you've already run extraction and indexing:
# bloginator extract -o output/extracted --config corpus/corpus.local.yaml
# bloginator index output/extracted -o .bloginator/chroma

# Step 1: Test Search
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1: Testing Corpus Search${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

bloginator search "$INDEX_PATH" "kubernetes devops automation" -n 5

echo ""
echo -e "${GREEN}✓ Search completed${NC}"
echo ""

# Step 2: Generate Outline
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 2: Generating Outline${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

OUTLINE_LOG="${LOG_DIR}/outline.log"
OUTLINE_OUTPUT="${LOG_DIR}/outline"

echo -e "Title: ${TITLE}"
echo -e "Keywords: ${KEYWORDS}"
echo -e "Thesis: ${THESIS}"
echo -e "Log:   ${OUTLINE_LOG}"
echo -e "Output: ${OUTLINE_OUTPUT}.json and ${OUTLINE_OUTPUT}.md"
echo ""

bloginator outline \
  --index "$INDEX_PATH" \
  --title "$TITLE" \
  --keywords "$KEYWORDS" \
  --thesis "$THESIS" \
  --sections 5 \
  --temperature 0.7 \
  --output "$OUTLINE_OUTPUT" \
  --format both \
  --min-coverage 2 \
  --log-file "$OUTLINE_LOG" \
  $VERBOSE_FLAG

echo ""
echo -e "${GREEN}✓ Outline generated${NC}"
echo -e "${YELLOW}📋 Log file: ${OUTLINE_LOG}${NC}"
echo ""

# Step 3: Generate Draft
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 3: Generating Draft${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

DRAFT_LOG="${LOG_DIR}/draft.log"
DRAFT_OUTPUT="${LOG_DIR}/draft.md"

echo -e "Title: ${TITLE} (from outline)"
echo -e "Log:   ${DRAFT_LOG}"
echo -e "Output: ${DRAFT_OUTPUT}"
echo ""

bloginator draft \
  --index "$INDEX_PATH" \
  --outline "${OUTLINE_OUTPUT}.json" \
  --output "$DRAFT_OUTPUT" \
  --temperature 0.7 \
  --sources-per-section 5 \
  --max-section-words 300 \
  --log-file "$DRAFT_LOG" \
  $VERBOSE_FLAG

echo ""
echo -e "${GREEN}✓ Draft generated${NC}"
echo -e "${YELLOW}📋 Log file: ${DRAFT_LOG}${NC}"
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Test Complete - Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

echo -e "${GREEN}📁 All outputs in: ${LOG_DIR}${NC}"
echo ""

echo -e "${YELLOW}Logs:${NC}"
echo -e "  • Outline: ${OUTLINE_LOG}"
echo -e "  • Draft:   ${DRAFT_LOG}"
echo ""

echo -e "${YELLOW}Generated Files:${NC}"
find "${LOG_DIR}" -maxdepth 1 -type f -exec ls -lh {} \; | while read -r line; do
    echo -e "  • $line"
done
echo ""

echo -e "${GREEN}To tail logs in real-time (in another terminal):${NC}"
echo -e "${YELLOW}  tail -f ${OUTLINE_LOG}${NC}"
echo -e "${YELLOW}  tail -f ${DRAFT_LOG}${NC}"
echo ""

echo -e "${GREEN}To view generated content:${NC}"
echo -e "${YELLOW}  cat ${OUTLINE_OUTPUT}.md${NC}"
echo -e "${YELLOW}  cat ${DRAFT_OUTPUT}${NC}"
echo ""

# Display file sizes
echo -e "${GREEN}File Sizes:${NC}"
if [ -f "${OUTLINE_OUTPUT}.json" ]; then
    SIZE=$(wc -c < "${OUTLINE_OUTPUT}.json")
    echo -e "  • Outline JSON: ${SIZE} bytes"
fi
if [ -f "${OUTLINE_OUTPUT}.md" ]; then
    LINES=$(wc -l < "${OUTLINE_OUTPUT}.md")
    echo -e "  • Outline MD: ${LINES} lines"
fi
if [ -f "${DRAFT_OUTPUT}" ]; then
    WORDS=$(wc -w < "${DRAFT_OUTPUT}")
    LINES=$(wc -l < "${DRAFT_OUTPUT}")
    echo -e "  • Draft: ${WORDS} words, ${LINES} lines"
fi
echo ""

echo -e "${GREEN}✅ Test completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Review the outline: cat ${OUTLINE_OUTPUT}.md"
echo -e "  2. Review the draft: cat ${DRAFT_OUTPUT}"
echo -e "  3. Check the logs: tail ${OUTLINE_LOG} ${DRAFT_LOG}"
