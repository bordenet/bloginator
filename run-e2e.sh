#!/usr/bin/env bash
################################################################################
# Script Name: run-e2e.sh
################################################################################
# PURPOSE: End-to-end workflow demo for Bloginator (extract → index → outline → draft)
# USAGE: ./run-e2e.sh [OPTIONS]
# PLATFORM: Cross-platform (Linux/macOS)
#
# This script has been refactored for maintainability (<400 lines).
# Shared functionality moved to scripts/e2e-lib.sh
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
#   --ollama-host   Ollama server URL (e.g., http://192.168.5.53:11434)
#   --ollama-model  Ollama model name (default: mixtral:8x7b)
#   --help, -h      Show detailed help
################################################################################

# Source shared library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/e2e-lib.sh
source "$SCRIPT_DIR/scripts/e2e-lib.sh"

# Setup timer cleanup on exit
trap stop_timer EXIT

################################################################################
# Script-Specific Configuration
################################################################################

SKIP_BUILD=false
SKIP_OLLAMA=false
CLEAN=false
VERBOSE=false
LAUNCH_GUI=false
RESUME=false
RESTART=false
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-mixtral:8x7b}"

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
            OLLAMA_HOST="$2"
            shift 2
            ;;
        --ollama-model)
            OLLAMA_MODEL="$2"
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
# Main Workflow
################################################################################

# Start timer
start_timer

# Handle restart flag
if $RESTART; then
    print_info "Clearing previous state..."
    clear_state
    print_success "State cleared. Starting from beginning."
    echo ""
fi

# Show resume status if applicable
if $RESUME; then
    show_resume_status
fi

print_header "Bloginator E2E Workflow Demo"

# Step 1: Environment Setup
if ! $SKIP_BUILD && ! ($RESUME && is_step_completed "setup"); then
    print_step "Step 1: Environment Setup"

    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    print_info "Installing bloginator..."
    # shellcheck disable=SC1091
    source venv/bin/activate
    pip install -q -e ".[all]"
    print_success "Bloginator installed"

    save_state "setup"
elif $RESUME && is_step_completed "setup"; then
    print_info "Skipping setup (already completed)"
fi

# Step 2: Ollama Check
if ! $SKIP_OLLAMA && ! ($RESUME && is_step_completed "ollama"); then
    print_step "Step 2: Ollama Check"

    if check_ollama_service "$OLLAMA_HOST"; then
        print_success "Ollama server is running at $OLLAMA_HOST"

        if check_ollama_model "$OLLAMA_HOST" "$OLLAMA_MODEL"; then
            print_success "Model $OLLAMA_MODEL is available"
        else
            print_warning "Model $OLLAMA_MODEL not found. Available models:"
            list_ollama_models "$OLLAMA_HOST"
            print_error "Please pull the model: ollama pull $OLLAMA_MODEL"
            exit 1
        fi
    else
        print_error "Ollama server not reachable at $OLLAMA_HOST"
        print_info "Start Ollama with: ollama serve"
        exit 1
    fi

    save_state "ollama"
elif $RESUME && is_step_completed "ollama"; then
    print_info "Skipping Ollama check (already completed)"
fi

# Step 3: Clean (Optional)
if $CLEAN && ! ($RESUME && is_step_completed "clean"); then
    print_step "Step 3: Clean Previous Outputs"
    rm -rf "$OUTPUT_DIR" "$INDEX_DIR"
    print_success "Cleaned output and index directories"
    save_state "clean"
fi

# Step 4: Extract Corpus
if ! ($RESUME && is_step_completed "extract"); then
    print_step "Step 4: Extract Corpus"

    if [ ! -f "$CORPUS_CONFIG" ]; then
        print_error "Corpus config not found: $CORPUS_CONFIG"
        exit 1
    fi

    bloginator extract -o "$EXTRACTED_DIR" --config "$CORPUS_CONFIG" ${VERBOSE:+--verbose}
    print_success "Corpus extracted to $EXTRACTED_DIR"

    save_state "extract"
elif $RESUME && is_step_completed "extract"; then
    print_info "Skipping extraction (already completed)"
fi

# Step 5: Index Content
if ! ($RESUME && is_step_completed "index"); then
    print_step "Step 5: Index Content"

    bloginator index "$EXTRACTED_DIR" -o "$INDEX_DIR"
    print_success "Index built at $INDEX_DIR"

    save_state "index"
elif $RESUME && is_step_completed "index"; then
    print_info "Skipping indexing (already completed)"
fi

# Step 6: Search Demo
if ! ($RESUME && is_step_completed "search"); then
    print_step "Step 6: Search Demo"

    print_info "Searching for 'kubernetes devops'..."
    bloginator search "$INDEX_DIR" "kubernetes devops" -n 5
    print_success "Search completed"

    save_state "search"
elif $RESUME && is_step_completed "search"; then
    print_info "Skipping search demo (already completed)"
fi

# Step 7: Generate Outline
if ! ($RESUME && is_step_completed "outline"); then
    print_step "Step 7: Generate Outline"

    mkdir -p "$GENERATED_DIR"
    OUTLINE_PATH="$GENERATED_DIR/outline"

    bloginator outline \
        --index "$INDEX_DIR" \
        --title "Building a DevOps Culture at Scale" \
        --keywords "devops,kubernetes,automation,culture" \
        --thesis "Effective DevOps culture requires both technical infrastructure AND organizational transformation" \
        --sections 5 \
        --output "$OUTLINE_PATH" \
        --format both \
        ${VERBOSE:+--verbose}

    print_success "Outline generated at $OUTLINE_PATH.md and $OUTLINE_PATH.json"

    save_state "outline"
elif $RESUME && is_step_completed "outline"; then
    print_info "Skipping outline generation (already completed)"
fi

# Step 8: Generate Draft
if ! ($RESUME && is_step_completed "draft"); then
    print_step "Step 8: Generate Draft"

    OUTLINE_JSON="$GENERATED_DIR/outline.json"
    DRAFT_PATH="$GENERATED_DIR/draft.md"

    if [ ! -f "$OUTLINE_JSON" ]; then
        print_error "Outline not found: $OUTLINE_JSON"
        exit 1
    fi

    bloginator draft \
        --index "$INDEX_DIR" \
        --outline "$OUTLINE_JSON" \
        --output "$DRAFT_PATH" \
        ${VERBOSE:+--verbose}

    print_success "Draft generated at $DRAFT_PATH"

    save_state "draft"
elif $RESUME && is_step_completed "draft"; then
    print_info "Skipping draft generation (already completed)"
fi

# Summary
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - SCRIPT_START_TIME))

print_header "E2E Workflow Complete!"

print_success "All steps completed successfully"
print_info "Total time: ${ELAPSED}s"
echo ""
print_info "Generated files:"
echo "  - Outline: $GENERATED_DIR/outline.md"
echo "  - Draft:   $GENERATED_DIR/draft.md"
echo ""

# Launch Streamlit UI (Optional)
if $LAUNCH_GUI; then
    print_step "Launching Streamlit UI..."
    streamlit run src/bloginator/ui/app.py
fi
