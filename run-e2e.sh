#!/usr/bin/env bash

################################################################################
# Bloginator End-to-End Workflow Demo
################################################################################
# PURPOSE: Run complete workflow demo (extract → index → outline → draft)
#   - Setup Python environment and dependencies
#   - Extract documents from corpus
#   - Build semantic search index
#   - Search indexed corpus
#   - Generate blog outline from corpus
#   - Generate full draft from outline
#   - Optionally launch Streamlit UI
#
# USAGE:
#   ./run-e2e.sh [OPTIONS]
#   ./run-e2e.sh --help
#
# OPTIONS:
#   -y, --yes         Auto-confirm all prompts
#   -v, --verbose     Show detailed output
#   --skip-build      Skip build/setup (assumes already installed)
#   --skip-ollama     Skip Ollama checks
#   --clean           Clean outputs before running
#   --resume          Resume from last completed step
#   --restart         Clear state and start over
#   --gui             Launch Streamlit UI after completion
#   --ollama-host     Ollama server URL (default: http://localhost:11434)
#   --ollama-model    Ollama model name (default: mixtral:8x7b)
#   -h, --help        Display help message
#
# EXAMPLES:
#   ./run-e2e.sh                        # Full demo from scratch
#   ./run-e2e.sh -y                     # Non-interactive
#   ./run-e2e.sh --skip-build -v        # Run demo, verbose
#   ./run-e2e.sh --clean --restart      # Start completely fresh
#   ./run-e2e.sh --gui                  # Run demo then launch UI
#
# WORKFLOW
#   1. Environment setup (Python venv, dependencies)
#   2. Ollama service check (if needed)
#   3. Extract documents from corpus
#   4. Build semantic search index
#   5. Perform sample search
#   6. Generate blog outline
#   7. Generate blog draft
#   8. Optional: launch Streamlit UI
#
# REQUIREMENTS
#   - Python 3.10+
#   - Ollama with mixtral:8x7b model
#   - Corpus configured in corpus/corpus.yaml
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

# shellcheck source=scripts/lib/compact.sh
source "$SCRIPT_DIR/scripts/lib/compact.sh"

# shellcheck source=scripts/e2e-lib.sh
source "$SCRIPT_DIR/scripts/e2e-lib.sh"

cd "$SCRIPT_DIR"

################################################################################
# Configuration
################################################################################

export AUTO_YES=false
export VERBOSE=${VERBOSE:-0}

export SKIP_BUILD=false
export SKIP_OLLAMA=false
export CLEAN=false
export LAUNCH_GUI=false
export RESUME=false
export RESTART=false
export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-mixtral:8x7b}"

################################################################################
# Argument Parsing
################################################################################

show_help() {
    cat << 'EOF'
NAME
    run-e2e.sh - End-to-end workflow demo

SYNOPSIS
    ./run-e2e.sh [OPTIONS]

DESCRIPTION
    Runs the complete Bloginator workflow: extract corpus, build search index,
    generate outline, and generate blog draft.

OPTIONS
    -y, --yes         Auto-confirm all prompts
    -v, --verbose     Show detailed output
    --skip-build      Skip environment setup (assumes installed)
    --skip-ollama     Skip Ollama service checks
    --clean           Clean outputs before running
    --resume          Resume from last completed step
    --restart         Clear state and start over
    --gui             Launch Streamlit UI after completion
    --ollama-host     Ollama server URL (default: http://localhost:11434)
    --ollama-model    Ollama model (default: mixtral:8x7b)
    -h, --help        Display this help

EXAMPLES
    ./run-e2e.sh              # Full demo from scratch
    ./run-e2e.sh -y -v        # Non-interactive, verbose
    ./run-e2e.sh --skip-build # Run demo (already installed)
    ./run-e2e.sh --clean      # Clean outputs before running
    ./run-e2e.sh --gui        # Run demo then launch Streamlit

WORKFLOW
    1. Setup environment (Python venv, dependencies)
    2. Check Ollama service and model availability
    3. Extract documents from corpus
    4. Build semantic search index with embeddings
    5. Perform sample search demonstration
    6. Generate blog outline from corpus
    7. Generate full blog draft from outline
    8. (Optional) Launch Streamlit web UI

REQUIREMENTS
    - Python 3.10+
    - Ollama with mixtral:8x7b (or compatible) model
    - Corpus configured in corpus/corpus.yaml
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes) AUTO_YES=true; shift ;;
            -v|--verbose) export VERBOSE=1; shift ;;
            --skip-build) SKIP_BUILD=true; shift ;;
            --skip-ollama) SKIP_OLLAMA=true; shift ;;
            --clean) CLEAN=true; shift ;;
            --resume) RESUME=true; shift ;;
            --restart) RESTART=true; shift ;;
            --gui) LAUNCH_GUI=true; shift ;;
            --ollama-host) OLLAMA_HOST="$2"; shift 2 ;;
            --ollama-model) OLLAMA_MODEL="$2"; shift 2 ;;
            -h|--help) show_help; exit 0 ;;
            *) echo "Unknown option: $1"; exit 1 ;;
        esac
    done
}

confirm() {
    local prompt="$1"
    local default="${2:-y}"
    
    if [[ "$AUTO_YES" == "true" ]]; then
        verbose "$prompt [auto-confirming]"
        return 0
    fi
    
    local response
    if read -t 3 -p "$prompt [$default, auto-yes in 3s]: " -r response 2>/dev/null; then
        response="${response:-$default}"
    else
        response="$default"
        echo ""
    fi
    [[ "$response" =~ ^[Yy]$ ]]
}

################################################################################
# Workflow Tasks
################################################################################

step_setup_environment() {
    task_start "Setting up environment"
    
    if [[ ! -d "venv" ]]; then
        verbose "Creating Python virtual environment..."
        python3 -m venv venv > /dev/null 2>&1
        verbose "Created venv"
    fi
    
    # shellcheck source=/dev/null
    source venv/bin/activate
    
    verbose "Installing bloginator..."
    if ! python -m pip install -q -e ".[dev]" 2>/dev/null; then
        task_fail "Failed to install dependencies"
        exit 1
    fi
    
    verbose "Environment ready"
    task_ok "Environment setup complete"
}

step_check_ollama() {
    task_start "Checking Ollama service"
    
    verbose "Ollama host: $OLLAMA_HOST"
    verbose "Ollama model: $OLLAMA_MODEL"
    
    if ! check_ollama_service "$OLLAMA_HOST" 2>/dev/null; then
        task_fail "Ollama not reachable at $OLLAMA_HOST"
        echo ""
        echo "Start Ollama with: ollama serve"
        exit 1
    fi
    
    verbose "Ollama is running"
    
    if ! check_ollama_model "$OLLAMA_HOST" "$OLLAMA_MODEL" 2>/dev/null; then
        task_fail "Model $OLLAMA_MODEL not available"
        echo ""
        echo "Pull the model with: ollama pull $OLLAMA_MODEL"
        exit 1
    fi
    
    verbose "Model $OLLAMA_MODEL is available"
    task_ok "Ollama service verified"
}

step_extract_corpus() {
    task_start "Extracting corpus"
    
    if [[ ! -f corpus/corpus.yaml ]]; then
        task_fail "Corpus config not found: corpus/corpus.yaml"
        exit 1
    fi
    
    verbose "Extracting documents..."
    if ! bloginator extract -o output/extracted --config corpus/corpus.yaml > /dev/null 2>&1; then
        task_fail "Failed to extract corpus"
        exit 1
    fi
    
    verbose "Extraction complete"
    task_ok "Corpus extracted"
}

step_build_index() {
    task_start "Building search index"
    
    verbose "Indexing extracted documents..."
    if ! bloginator index output/extracted -o .bloginator/chroma > /dev/null 2>&1; then
        task_fail "Failed to build index"
        exit 1
    fi
    
    verbose "Index complete"
    task_ok "Search index built"
}

step_search_demo() {
    task_start "Running search demo"
    
    verbose "Searching for 'kubernetes devops'..."
    if ! bloginator search .bloginator/chroma "kubernetes devops" -n 5 > /dev/null 2>&1; then
        task_warn "Search query failed (non-fatal)"
    fi
    
    task_ok "Search demo complete"
}

step_generate_outline() {
    task_start "Generating blog outline"
    
    mkdir -p output/generated
    
    verbose "Creating outline..."
    if ! bloginator outline \
        --index .bloginator/chroma \
        --title "Building a DevOps Culture at Scale" \
        --keywords "devops,kubernetes,automation,culture" \
        --thesis "Effective DevOps requires technical infrastructure AND organizational transformation" \
        --sections 5 \
        --output output/generated/outline \
        --format both > /dev/null 2>&1; then
        task_fail "Failed to generate outline"
        exit 1
    fi
    
    verbose "Outline generated"
    task_ok "Blog outline complete"
}

step_generate_draft() {
    task_start "Generating blog draft"
    
    if [[ ! -f output/generated/outline.json ]]; then
        task_fail "Outline JSON not found"
        exit 1
    fi
    
    verbose "Creating draft..."
    if ! bloginator draft \
        --index .bloginator/chroma \
        --outline output/generated/outline.json \
        --output output/generated/draft.md > /dev/null 2>&1; then
        task_fail "Failed to generate draft"
        exit 1
    fi
    
    verbose "Draft generated"
    task_ok "Blog draft complete"
}

step_cleanup_state() {
    task_start "Cleaning state"
    
    if [[ -d ".bloginator/e2e-state" ]]; then
        rm -rf .bloginator/e2e-state
        verbose "State cleared"
    fi
    
    task_ok "Ready to run"
}

################################################################################
# Main
################################################################################

main() {
    parse_args "$@"
    
    print_header "Bloginator E2E Workflow"
    echo ""
    
    # Handle restart flag
    if [[ "$RESTART" == "true" ]]; then
        step_cleanup_state
    fi
    
    # Run workflow steps
    if [[ "$SKIP_BUILD" != "true" ]]; then
        step_setup_environment
    else
        verbose "Skipping environment setup (--skip-build)"
    fi
    
    if [[ "$SKIP_OLLAMA" != "true" ]]; then
        step_check_ollama
    else
        verbose "Skipping Ollama check (--skip-ollama)"
    fi
    
    if [[ "$CLEAN" == "true" ]]; then
        task_start "Cleaning previous outputs"
        rm -rf output generated .bloginator/chroma
        task_ok "Outputs cleaned"
    fi
    
    step_extract_corpus
    step_build_index
    step_search_demo
    step_generate_outline
    step_generate_draft
    
    echo ""
    print_header "✓ Workflow complete! $(get_elapsed_time)"
    echo ""
    echo "Generated files:"
    echo "  - Outline: output/generated/outline.md"
    echo "  - Draft:   output/generated/draft.md"
    echo ""
    
    if [[ "$LAUNCH_GUI" == "true" ]]; then
        echo "Launching Streamlit UI..."
        echo ""
        exec ./run-streamlit.sh --no-browser
    fi
}

main "$@"
