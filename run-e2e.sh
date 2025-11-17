#!/usr/bin/env bash
################################################################################
# Script Name: run-e2e.sh
################################################################################
# PURPOSE: End-to-end workflow demo for Bloginator (extract → index → outline → draft)
# USAGE: ./run-e2e.sh [OPTIONS]
# PLATFORM: Cross-platform (Linux/macOS)
#
# QUICK START (Automated):
#   ./run-e2e.sh                           # Full demo
#   ./run-e2e.sh --resume                  # Continue from last step
#   ./run-e2e.sh --restart                 # Start over
#
# MANUAL WALKTHROUGH (Run these commands yourself):
#
#   # Step 1: Setup
#   python3 -m venv venv
#   source venv/bin/activate
#   pip install -e ".[dev]"
#
#   # Step 2: Start Ollama (if using local LLM)
#   ollama serve
#   ollama run mixtral:8x7b    # Then type /bye to exit
#
#   # Step 3: Extract documents
#   bloginator extract -o output/extracted --config corpus/corpus.yaml
#
#   # Step 4: Build search index
#   bloginator index output/extracted/ -o .bloginator/chroma
#
#   # Step 5: Search corpus
#   bloginator search .bloginator/chroma "kubernetes devops" -n 5
#
#   # Step 6: Generate outline
#   bloginator outline --index .bloginator/chroma \
#     --title "Building a DevOps Culture at Scale" \
#     --keywords "devops,kubernetes,automation" \
#     --thesis "Effective DevOps requires technical AND organizational transformation" \
#     --sections 5 --output output/outline --format both
#
#   # Step 7: Generate draft
#   bloginator draft --index .bloginator/chroma \
#     --outline output/outline.json \
#     --output output/draft.md
#
# OPTIONS:
#   --skip-build    Skip build/setup (assumes already installed)
#   --skip-ollama   Skip Ollama checks (assumes already running)
#   --clean         Clean outputs before running
#   --resume        Continue from last completed step
#   --restart       Clear state and start over
#   --verbose, -v   Show LLM prompts and responses
#   --gui           Launch Streamlit UI after completion
#   --help, -h      Show detailed help
################################################################################

set -euo pipefail

################################################################################
# Configuration
################################################################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

SKIP_BUILD=false
SKIP_OLLAMA=false
CLEAN=false
VERBOSE=false
LAUNCH_GUI=false
RESUME=false
RESTART=false
OLLAMA_HOST_ARG=""
OLLAMA_MODEL_ARG=""

# Paths
CORPUS_CONFIG="${CORPUS_CONFIG:-corpus/corpus.yaml}"
OUTPUT_DIR="${PROJECT_ROOT}/output"
EXTRACTED_DIR="${OUTPUT_DIR}/extracted"
INDEX_DIR="${PROJECT_ROOT}/.bloginator/chroma"
GENERATED_DIR="${OUTPUT_DIR}/generated"
STATE_FILE="${OUTPUT_DIR}/.run-e2e-state"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
LIGHT_GRAY='\033[0;37m'
DARK_GRAY='\033[1;30m'
BRIGHT_WHITE='\033[1;37m'
BRIGHT_CYAN='\033[1;36m'
BRIGHT_YELLOW='\033[1;33m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Trap handler for cleanup
trap 'echo -e "\n${RED}✗ E2E workflow interrupted${NC}"; exit 1' INT TERM

################################################################################
# Parse Arguments
################################################################################
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-ollama)
            SKIP_OLLAMA=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --gui)
            LAUNCH_GUI=true
            shift
            ;;
        --ollama-host)
            OLLAMA_HOST_ARG="$2"
            shift 2
            ;;
        --ollama-model)
            OLLAMA_MODEL_ARG="$2"
            shift 2
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        --restart)
            RESTART=true
            shift
            ;;
        --help|-h)
            cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bloginator - End-to-End Workflow Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Demonstrates the complete workflow:
  1. Build and setup environment
  2. Extract documents from corpus
  3. Index content with semantic embeddings
  4. Search the indexed corpus
  5. Generate blog outline from corpus
  6. Generate full draft from outline

Usage:
  ./run-e2e.sh [OPTIONS]

Options:
  --skip-build          Skip build/setup (assumes already installed)
  --skip-ollama         Skip Ollama checks (assumes already running)
  --clean               Clean outputs directory before running
  --resume              Resume from last completed step (auto-detects state)
  --restart             Clear state and start from beginning
  --verbose, -v         Show LLM interactions (prompts and responses)
  --gui                 Launch Streamlit UI after completing workflow
  --ollama-host <url>   Ollama server URL (e.g., http://192.168.5.53:11434)
  --ollama-model <name> Ollama model name (default: mixtral:8x7b)
  --help, -h            Show this help message

Examples:
  ./run-e2e.sh                  # Full demo from scratch
  ./run-e2e.sh --skip-build     # Run demo (already installed)
  ./run-e2e.sh --clean          # Start fresh (delete old outputs)
  ./run-e2e.sh -v               # Verbose output (show LLM interactions)
  ./run-e2e.sh --gui            # Run demo then launch Streamlit UI
  ./run-e2e.sh --resume         # Continue from where it stopped
  ./run-e2e.sh --restart        # Clear state, start over

  # Use remote Ollama server
  ./run-e2e.sh --ollama-host http://192.168.5.53:11434
  ./run-e2e.sh --ollama-host http://192.168.5.53:11434 --ollama-model mixtral:8x7b -v

Requirements:
  - Python 3.10+
  - Ollama with mixtral:8x7b model (for generation)
  - Corpus configured in corpus/corpus.yaml
EOF
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

################################################################################
# State Management Functions
################################################################################
save_state() {
    local step_name="$1"
    mkdir -p "$OUTPUT_DIR"
    echo "$step_name:$(date +%s)" >> "$STATE_FILE"
    echo "$step_name" >> "$STATE_FILE.completed"
}

is_step_completed() {
    local step_name="$1"
    [ -f "$STATE_FILE.completed" ] && grep -q "^$step_name$" "$STATE_FILE.completed"
}

clear_state() {
    rm -f "$STATE_FILE" "$STATE_FILE.completed"
}

show_resume_status() {
    if [ -f "$STATE_FILE.completed" ]; then
        echo ""
        print_info "Previous run detected. Completed steps:"
        while read -r step; do
            print_success "$step"
        done < "$STATE_FILE.completed"
        echo ""
    fi
}

################################################################################
# Helper Functions
################################################################################
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${MAGENTA}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

run_command() {
    local description="$1"
    local command="$2"

    print_step "$description"

    if $VERBOSE; then
        if eval "$command"; then
            print_success "$description completed"
        else
            print_error "$description failed"
            exit 1
        fi
    else
        if eval "$command" > /dev/null 2>&1; then
            print_success "$description completed"
        else
            print_error "$description failed"
            echo "Run with --verbose to see error details"
            exit 1
        fi
    fi
}

################################################################################
# Main Script
################################################################################
START_TIME=$(date +%s)

# Handle restart flag
if $RESTART; then
    print_info "Clearing previous state..."
    clear_state
    print_success "State cleared. Starting from beginning."
    echo ""
fi

# Show resume status if applicable
if $RESUME || [ -f "$STATE_FILE.completed" ]; then
    show_resume_status
    RESUME=true
fi

# Export Ollama configuration if provided via command-line
if [ -n "$OLLAMA_HOST_ARG" ]; then
    export OLLAMA_HOST="$OLLAMA_HOST_ARG"
fi
if [ -n "$OLLAMA_MODEL_ARG" ]; then
    export OLLAMA_MODEL="$OLLAMA_MODEL_ARG"
fi

# Enable verbose logging in bloginator if requested
if $VERBOSE; then
    export BLOGINATOR_VERBOSE=1
fi

print_header "Bloginator - End-to-End Workflow Demo"

print_info "Project root: $PROJECT_ROOT"
print_info "Corpus config: $CORPUS_CONFIG"
print_info "Output directory: $OUTPUT_DIR"
print_info "Index directory: $INDEX_DIR"
if [ -n "$OLLAMA_HOST_ARG" ]; then
    print_info "Ollama server: $OLLAMA_HOST_ARG"
fi
if [ -n "$OLLAMA_MODEL_ARG" ]; then
    print_info "Ollama model: $OLLAMA_MODEL_ARG"
fi

################################################################################
# Step 1: Environment Setup
################################################################################
STEP_NAME="build-setup"
if $RESUME && is_step_completed "$STEP_NAME"; then
    print_header "STEP 1: Build and Setup (✓ Already Completed)"
    # Still need to activate venv when resuming
    if [ -d ".venv" ]; then
        # shellcheck disable=SC1091
        source .venv/bin/activate
    fi
elif ! $SKIP_BUILD; then
    print_header "STEP 1: Build and Setup"

    # Check Python version
    PYTHON_CMD=""
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python 3.10+"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_info "Python: $PYTHON_VERSION"

    # Create virtual environment
    if [ ! -d ".venv" ]; then
        run_command "Creating virtual environment" \
            "$PYTHON_CMD -m venv .venv"
    else
        print_info "Virtual environment already exists"
    fi

    # Activate virtual environment
    print_step "Activating virtual environment"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    print_success "Virtual environment activated"

    # Install package in development mode
    run_command "Installing bloginator package" \
        "pip install -e ."

    # Install dev dependencies
    if [ -f "pyproject.toml" ]; then
        run_command "Installing dev dependencies" \
            "pip install -e '.[dev]'"
    fi

    print_success "Build and setup complete"
    save_state "$STEP_NAME"
else
    print_header "STEP 1: Build and Setup (Skipped)"
    save_state "$STEP_NAME"

    # Still need to activate venv
    if [ -d ".venv" ]; then
        # shellcheck disable=SC1091
        source .venv/bin/activate
        print_info "Virtual environment activated"
    else
        print_warning "No virtual environment found, using system Python"
    fi
fi

################################################################################
# Step 2: Ollama Check
################################################################################
STEP_NAME="ollama-check"
if $RESUME && is_step_completed "$STEP_NAME"; then
    print_header "STEP 2: Ollama Verification (✓ Already Completed)"
elif ! $SKIP_OLLAMA; then
    print_header "STEP 2: Ollama Verification"

    # Determine Ollama host
    OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
    OLLAMA_MODEL="${OLLAMA_MODEL:-mixtral:8x7b}"

    # Check if Ollama server is reachable
    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        print_success "Ollama server reachable at ${OLLAMA_HOST}"
    else
        print_warning "Ollama server not reachable at ${OLLAMA_HOST}"
        print_info "Check that Ollama is running or use --skip-ollama"
        exit 1
    fi

    print_info "Using model: ${OLLAMA_MODEL}"
    save_state "$STEP_NAME"
else
    print_header "STEP 2: Ollama Verification (Skipped)"
    print_warning "Skipping Ollama checks - generation steps may fail"
    save_state "$STEP_NAME"
fi

################################################################################
# Step 3: Clean (Optional)
################################################################################
STEP_NAME="clean-outputs"
if $RESUME && is_step_completed "$STEP_NAME"; then
    print_header "STEP 3: Clean Output Directory (✓ Already Completed)"
elif $CLEAN; then
    print_header "STEP 3: Clean Output Directory"

    if [ -d "$OUTPUT_DIR" ]; then
        run_command "Removing old outputs" \
            "rm -rf $OUTPUT_DIR"
    fi

    run_command "Creating fresh output directories" \
        "mkdir -p $EXTRACTED_DIR $GENERATED_DIR"

    print_success "Output directory cleaned"
    save_state "$STEP_NAME"
else
    print_header "STEP 3: Prepare Output Directory"

    mkdir -p "$EXTRACTED_DIR" "$GENERATED_DIR"
    print_info "Output directories ready"
    save_state "$STEP_NAME"
fi

################################################################################
# Step 4: Extract Corpus
################################################################################
STEP_NAME="extract-content"
if $RESUME && is_step_completed "$STEP_NAME"; then
    print_header "STEP 4: Extract Corpus Documents (✓ Already Completed)"

    # Still count extracted files for summary
    EXTRACTED_COUNT=$(find "$EXTRACTED_DIR" -type f -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    print_info "Previously extracted $EXTRACTED_COUNT files"
else
    print_header "STEP 4: Extract Corpus Documents"

    # Check if corpus config exists
    if [ ! -f "$CORPUS_CONFIG" ]; then
        print_error "Corpus config not found: $CORPUS_CONFIG"
        print_info "Create one based on corpus.yaml.example"
        exit 1
    fi

    print_info "Extracting from: $CORPUS_CONFIG"

    run_command "Extracting documents to $EXTRACTED_DIR" \
        "bloginator extract -o '$EXTRACTED_DIR' --config '$CORPUS_CONFIG'"

    # Count extracted files
    EXTRACTED_COUNT=$(find "$EXTRACTED_DIR" -type f -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$EXTRACTED_COUNT" -eq 0 ]; then
        print_error "No files were extracted"
        exit 1
    fi

    print_success "Extracted $EXTRACTED_COUNT files"
    save_state "$STEP_NAME"
fi

################################################################################
# Step 5: Index Content
################################################################################
STEP_NAME="index-content"
if $RESUME && is_step_completed "$STEP_NAME"; then
    print_header "STEP 5: Index Extracted Content (✓ Already Completed)"
    print_info "Index already exists at $INDEX_DIR"
else
    print_header "STEP 5: Index Extracted Content"

    # Verify extracted files exist
    if [ ! -d "$EXTRACTED_DIR" ] || [ -z "$(ls -A "$EXTRACTED_DIR" 2>/dev/null)" ]; then
        print_error "No extracted files found in $EXTRACTED_DIR"
        exit 1
    fi

    print_info "Building semantic search index..."

    run_command "Creating vector embeddings and ChromaDB index" \
        "bloginator index '$EXTRACTED_DIR' -o '$INDEX_DIR'"

    # Verify index was created
    if [ ! -d "$INDEX_DIR" ]; then
        print_error "Index was not created"
        exit 1
    fi

    print_success "Index created at $INDEX_DIR"
    save_state "$STEP_NAME"
fi

################################################################################
# Step 6: Search Demo
################################################################################
STEP_NAME="search-demo"
if $RESUME && is_step_completed "$STEP_NAME"; then
    print_header "STEP 6: Search Demo (✓ Already Completed)"
else
    print_header "STEP 6: Search Demo"

    print_info "Testing semantic search..."

    # Example search queries
    QUERIES=(
        "kubernetes devops automation"
        "building team culture"
        "technical leadership"
    )

    for query in "${QUERIES[@]}"; do
        print_step "Query: \"$query\""
        if $VERBOSE; then
            bloginator search "$INDEX_DIR" "$query" -n 3 || true
        else
            bloginator search "$INDEX_DIR" "$query" -n 3 2>/dev/null | head -20 || true
        fi
        echo ""
    done

    print_success "Search demo complete"
    save_state "$STEP_NAME"
fi

################################################################################
# Step 7: Generate Outline
################################################################################
STEP_NAME="generate-outline"
if $RESUME && is_step_completed "$STEP_NAME"; then
    print_header "STEP 7: Generate Outline (✓ Already Completed)"
else
    print_header "STEP 7: Generate Outline"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    LOG_DIR="/tmp/bloginator_test_${TIMESTAMP}"
    mkdir -p "$LOG_DIR"

    print_info "Test directory: ${LOG_DIR}"

    OUTLINE_LOG="${LOG_DIR}/outline.log"
    OUTLINE_OUTPUT="${LOG_DIR}/outline"

    TITLE="Building a DevOps Culture at Scale"
    KEYWORDS="devops,kubernetes,automation,culture,collaboration,ci-cd"
    THESIS="Effective DevOps culture requires both technical infrastructure AND organizational transformation"

    print_info "Title: $TITLE"
    print_info "Keywords: $KEYWORDS"
    print_info "Thesis: $THESIS"
    echo ""

    if $VERBOSE; then
        bloginator outline \
          --index "$INDEX_DIR" \
          --title "$TITLE" \
          --keywords "$KEYWORDS" \
          --thesis "$THESIS" \
          --sections 5 \
          --temperature 0.7 \
          --output "$OUTLINE_OUTPUT" \
          --format both \
          --min-coverage 2 \
          --log-file "$OUTLINE_LOG" \
          --verbose || { print_error "Outline generation failed"; exit 1; }
    else
        bloginator outline \
          --index "$INDEX_DIR" \
          --title "$TITLE" \
          --keywords "$KEYWORDS" \
          --thesis "$THESIS" \
          --sections 5 \
          --temperature 0.7 \
          --output "$OUTLINE_OUTPUT" \
          --format both \
          --min-coverage 2 \
          --log-file "$OUTLINE_LOG" > /dev/null 2>&1 || { print_error "Outline generation failed"; exit 1; }
    fi

    echo ""
    print_success "Outline generated"
    print_info "Log file: ${OUTLINE_LOG}"
    print_info "Output: ${OUTLINE_OUTPUT}.json and ${OUTLINE_OUTPUT}.md"

    save_state "$STEP_NAME"
fi

################################################################################
# Step 8: Generate Draft
################################################################################
STEP_NAME="generate-draft"
if $RESUME && is_step_completed "$STEP_NAME"; then
    print_header "STEP 8: Generate Draft (✓ Already Completed)"
else
    print_header "STEP 8: Generate Draft"

    DRAFT_LOG="${LOG_DIR}/draft.log"
    DRAFT_OUTPUT="${LOG_DIR}/draft.md"

    print_info "Generating draft from outline..."
    print_info "Log: ${DRAFT_LOG}"
    print_info "Output: ${DRAFT_OUTPUT}"
    echo ""

    if $VERBOSE; then
        bloginator draft \
          --index "$INDEX_DIR" \
          --outline "${OUTLINE_OUTPUT}.json" \
          --output "$DRAFT_OUTPUT" \
          --temperature 0.7 \
          --sources-per-section 5 \
          --max-section-words 300 \
          --log-file "$DRAFT_LOG" \
          --verbose || { print_error "Draft generation failed"; exit 1; }
    else
        bloginator draft \
          --index "$INDEX_DIR" \
          --outline "${OUTLINE_OUTPUT}.json" \
          --output "$DRAFT_OUTPUT" \
          --temperature 0.7 \
          --sources-per-section 5 \
          --max-section-words 300 \
          --log-file "$DRAFT_LOG" > /dev/null 2>&1 || { print_error "Draft generation failed"; exit 1; }
    fi

    echo ""
    print_success "Draft generated"
    print_info "Log file: ${DRAFT_LOG}"

    save_state "$STEP_NAME"
fi

################################################################################
# Summary
################################################################################
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

print_header "E2E Workflow Complete!"

echo ""
echo -e "${GREEN}✓ Summary${NC}"
echo "  - Extracted files: $EXTRACTED_COUNT"
echo "  - Index location: $INDEX_DIR"
echo "  - Test outputs: $LOG_DIR"
echo "  - Duration: ${DURATION}s"
echo ""

print_info "Generated Files:"
if [ -d "$LOG_DIR" ]; then
    find "$LOG_DIR" -maxdepth 1 -type f | while read -r file; do
        echo "  - $(basename "$file")"
    done
else
    echo "  (none - generation was skipped)"
fi

echo ""
print_info "Next Steps:"
echo "  - View outline: cat ${OUTLINE_OUTPUT}.md"
echo "  - View draft: cat ${DRAFT_OUTPUT}"
echo "  - Check logs: tail ${OUTLINE_LOG} ${DRAFT_LOG}"
echo "  - Interactive search: bloginator search $INDEX_DIR"
echo "  - Launch UI: ./run-streamlit.sh"
echo ""

print_success "All done! 🎉"

################################################################################
# Launch Streamlit UI (Optional)
################################################################################
if $LAUNCH_GUI; then
    echo ""
    print_header "Launching Streamlit UI"

    if [ -f "run-streamlit.sh" ]; then
        print_info "Starting Streamlit UI..."
        ./run-streamlit.sh
    else
        print_error "run-streamlit.sh not found"
        print_info "Create it or run: streamlit run src/bloginator/ui/app.py"
    fi
fi
