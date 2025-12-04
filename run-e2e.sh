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
#   3. Setup corpus (create default config if needed)
#   4. Extract documents from corpus
#   5. Build semantic search index
#   6. Perform sample search
#   7. Generate blog outline
#   8. Generate blog draft
#   9. Optional: launch Streamlit UI
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

# Load .env file if it exists
if [ -f ".env" ]; then
    verbose "Loading environment variables from .env file..."
    set -o allexport
    source .env
    set +o allexport
fi

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
export OLLAMA_HOST="${OLLAMA_HOST:-${BLOGINATOR_LLM_BASE_URL:-http://localhost:11434}}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-${BLOGINATOR_LLM_MODEL:-mixtral:8x7b}}"

# For --generate-only mode
export GENERATE_ONLY=false
export BLOG_TITLE=""
export BLOG_KEYWORDS=""
export BLOG_THESIS=""
export BLOG_CLASSIFICATION="guidance"
export BLOG_AUDIENCE="all-disciplines"
export BLOG_NUM_SECTIONS=5
export BLOG_SOURCES_PER_SECTION=5
export BLOG_MAX_WORDS_PER_SECTION=300

################################################################################
# Argument Parsing
################################################################################

show_help() {
    cat << 'EOF'
NAME
    run-e2e.sh - End-to-end workflow demo

SYNOPSIS
    ./run-e2e.sh [MODE] [OPTIONS]

DESCRIPTION
    Runs Bloginator workflows. Can run the complete end-to-end process
    (corpus extraction, indexing, generation) or run only the generation
    step using a pre-built index.

MODES
    (default)         Run the full end-to-end workflow.
    --generate-only   Run only the generation steps (outline and draft).
                      Requires a pre-existing index. All --blog-* options
                      are required for this mode.

GENERAL OPTIONS
    -y, --yes         Auto-confirm all prompts.
    -v, --verbose     Show detailed output.
    -h, --help        Display this help.

FULL WORKFLOW OPTIONS
    --skip-build      Skip environment setup (assumes installed).
    --skip-ollama     Skip Ollama service checks.
    --clean           Clean outputs before running.
    --restart         Clear state and start over.
    --gui             Launch Streamlit UI after completion.
    --ollama-host     Ollama server URL (default: from .env or http://localhost:11434).
    --ollama-model    Ollama model (default: from .env or mixtral:8x7b).

GENERATION OPTIONS (for --generate-only mode)
    --title           Blog post title.
    --keywords        Comma-separated keywords for the blog post.
    --thesis          The main thesis or argument of the post.
    --classification  Content classification (default: guidance).
    --audience        Target audience (default: all-disciplines).
    --num-sections    Number of sections in the outline (default: 5).
    --sources-per-section Number of sources per section for draft (default: 5).
    --max-section-words Max words per section for draft (default: 300).

EXAMPLES
    # Full demo from scratch
    ./run-e2e.sh -y -v

    # Clean and restart the full demo
    ./run-e2e.sh --clean --restart

    # Generate a specific blog post using an existing index
    ./run-e2e.sh --generate-only \
      --title "Guidance for building great dashboards" \
      --keywords "SLI metrics,golden signals,dashboard design" \
      --thesis "Consider audience, outcomes, and style guides for valuable dashboards."
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

            # Generation options
            --generate-only) GENERATE_ONLY=true; shift ;;
            --title) BLOG_TITLE="$2"; shift 2 ;;
            --keywords) BLOG_KEYWORDS="$2"; shift 2 ;;
            --thesis) BLOG_THESIS="$2"; shift 2 ;;
            --classification) BLOG_CLASSIFICATION="$2"; shift 2 ;;
            --audience) BLOG_AUDIENCE="$2"; shift 2 ;;
            --num-sections) BLOG_NUM_SECTIONS="$2"; shift 2 ;;
            --sources-per-section) BLOG_SOURCES_PER_SECTION="$2"; shift 2 ;;
            --max-section-words) BLOG_MAX_WORDS_PER_SECTION="$2"; shift 2 ;;

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

run_bloginator() {
    if [[ "$VERBOSE" -eq 1 ]]; then
        bloginator "$@"
    else
        bloginator "$@" > /dev/null 2>&1
    fi
}

run_pip_install() {
    if [[ "$VERBOSE" -eq 1 ]]; then
        python -m pip install -e ".[dev]"
    else
        python -m pip install -q -e ".[dev]" > /dev/null 2>&1
    fi
}

################################################################################
# Workflow Tasks
################################################################################

step_setup_environment() {
    task_start "Setting up environment"

    if command -v python3.12 &> /dev/null; then
        PYTHON_EXEC="python3.12"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_EXEC="python3.11"
    elif command -v python3.10 &> /dev/null; then
        PYTHON_EXEC="python3.10"
    else
        PYTHON_EXEC="python3"
    fi

    if [[ ! -d "venv" ]]; then
        verbose "Creating Python virtual environment with $PYTHON_EXEC..."
        "$PYTHON_EXEC" -m venv venv > /dev/null 2>&1
        verbose "Created venv"
    fi

    # shellcheck source=/dev/null
    source venv/bin/activate

    verbose "Installing bloginator..."
    if ! run_pip_install; then
        task_fail "Failed to install dependencies"
        exit 1
    fi

    verbose "Environment ready"
    task_ok "Environment setup complete"
}

step_check_ollama() {
    task_start "Checking Ollama service"

    verbose "Ollama host: $OLLAMA_HOST"

    if ! check_ollama_service "$OLLAMA_HOST" 2>/dev/null; then
        task_fail "Ollama not reachable at $OLLAMA_HOST"
        echo ""
        echo "Start Ollama with: ollama serve"
        exit 1
    fi

    verbose "Ollama is running"
    verbose "Desired model: $OLLAMA_MODEL"

    local available_models
    available_models=$(list_ollama_models "$OLLAMA_HOST")

    if [ -z "$available_models" ]; then
        task_fail "No models available in Ollama."
        echo ""
        echo "Pull a model with: ollama pull <model-name>"
        exit 1
    fi

    if echo "$available_models" | grep -q -w "$OLLAMA_MODEL"; then
        verbose "Model $OLLAMA_MODEL is available"
        task_ok "Ollama service verified"
    else
        task_warn "Model '$OLLAMA_MODEL' not found."
        echo ""
        echo "Available models:"
        echo "$available_models" | awk '{print "  - " $1}'
        echo ""

        local first_model
        first_model=$(echo "$available_models" | head -n 1)

        if confirm "Do you want to use the first available model ('$first_model') instead?"; then
            OLLAMA_MODEL="$first_model"
            export OLLAMA_MODEL
            verbose "Using model $OLLAMA_MODEL"
            task_ok "Ollama service verified (using fallback model)"
        else
            task_fail "Aborting. Please pull the desired model or specify an available one."
            exit 1
        fi
    fi
}

step_setup_corpus() {
    task_start "Setting up corpus"

    if [[ -f corpus/corpus.yaml ]]; then
        verbose "corpus.yaml already exists"
        task_ok "Corpus config ready"
        return
    fi

    if [[ -f corpus.yaml.example ]]; then
        verbose "Creating corpus.yaml from example..."
        cp corpus.yaml.example corpus/corpus.yaml
        verbose "Corpus config created"
        task_ok "Corpus initialized"
    else
        task_fail "corpus.yaml.example not found"
        exit 1
    fi
}

step_extract_corpus() {
    task_start "Extracting corpus"

    if [[ ! -f corpus/corpus.yaml ]]; then
        task_fail "Corpus config not found: corpus/corpus.yaml"
        exit 1
    fi

    verbose "Extracting documents..."
    if ! run_bloginator extract -o output/extracted --config corpus/corpus.yaml; then
        task_fail "Failed to extract corpus"
        exit 1
    fi

    verbose "Extraction complete"
    task_ok "Corpus extracted"
}

step_build_index() {
    task_start "Building search index"

    verbose "Indexing extracted documents..."
    if ! run_bloginator index output/extracted -o .bloginator/chroma; then
        task_fail "Failed to build index"
        exit 1
    fi

    verbose "Index complete"
    task_ok "Search index built"
}

step_search_demo() {
    task_start "Running search demo"

    verbose "Searching for 'kubernetes devops'..."
    if ! run_bloginator search .bloginator/chroma "kubernetes devops" -n 5; then
        task_warn "Search query failed (non-fatal)"
    fi

    task_ok "Search demo complete"
}

step_generate_outline() {
    task_start "Generating blog outline"

    mkdir -p output/generated

    verbose "Creating outline..."
    if ! run_bloginator outline \
        --index .bloginator/chroma \
        --title "Building a DevOps Culture at Scale" \
        --keywords "devops,kubernetes,automation,culture" \
        --thesis "Effective DevOps requires technical infrastructure AND organizational transformation" \
        --sections 5 \
        --output output/generated/outline \
        --format both; then
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
    if ! run_bloginator draft \
        --index .bloginator/chroma \
        --outline output/generated/outline.json \
        --output output/generated/draft.md; then
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

run_generation_workflow() {
    task_start "Running generation-only workflow"

    # Validate required arguments
    if [[ -z "$BLOG_TITLE" || -z "$BLOG_KEYWORDS" || -z "$BLOG_THESIS" ]]; then
        task_fail "Missing required arguments for --generate-only mode"
        echo "Error: --title, --keywords, and --thesis are required."
        show_help
        exit 1
    fi

    # Check if index exists
    if [[ ! -d ".bloginator/chroma" ]]; then
        task_fail "Chroma index not found at .bloginator/chroma"
        echo "Error: The generation workflow requires a pre-existing index."
        echo "Please run the full e2e workflow first without --generate-only."
        exit 1
    fi

    # Create a timestamped output directory
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    local output_dir="output/generated/cli_blog_${timestamp}"
    mkdir -p "$output_dir"
    local outline_path="$output_dir/outline"
    local draft_path="$output_dir/draft.md"

    verbose "Output will be saved to $output_dir"

    # --- Generate Outline ---
    task_start "Generating blog outline from specification"
    verbose "Title: $BLOG_TITLE"
    verbose "Keywords: $BLOG_KEYWORDS"

    local outline_cmd=(
        "outline"
        "--index" ".bloginator/chroma"
        "--title" "$BLOG_TITLE"
        "--keywords" "$BLOG_KEYWORDS"
        "--thesis" "$BLOG_THESIS"
        "--classification" "$BLOG_CLASSIFICATION"
        "--audience" "$BLOG_AUDIENCE"
        "--sections" "$BLOG_NUM_SECTIONS"
        "--output" "$outline_path"
        "--format" "both"
    )

    if ! run_bloginator "${outline_cmd[@]}"; then
        task_fail "Failed to generate outline"
        exit 1
    fi
    task_ok "Blog outline generated"

    # --- Generate Draft ---
    local outline_json_path="${outline_path}.json"
    if [[ ! -f "$outline_json_path" ]]; then
        task_fail "Outline JSON not found at $outline_json_path"
        exit 1
    fi

    task_start "Generating blog draft from outline"
    local draft_cmd=(
        "draft"
        "--index" ".bloginator/chroma"
        "--outline" "$outline_json_path"
        "--output" "$draft_path"
        "--sources-per-section" "$BLOG_SOURCES_PER_SECTION"
        "--max-section-words" "$BLOG_MAX_WORDS_PER_SECTION"
    )

    if ! run_bloginator "${draft_cmd[@]}"; then
        task_fail "Failed to generate draft"
        exit 1
    fi
    task_ok "Blog draft generated"

    echo ""
    print_header "✓ Generation complete!"
    echo ""
    echo "Generated files:"
    echo "  - Outline: ${outline_path}.md"
    echo "  - Draft:   ${draft_path}"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    parse_args "$@"

    # The --generate-only flag is a workflow choice, not a setup-skipper.
    # Environment should always be set up first, unless skipped via --skip-build.
    if [[ "$SKIP_BUILD" != "true" ]]; then
        step_setup_environment
    else
        verbose "Skipping environment setup (--skip-build)"
        if [ -f "venv/bin/activate" ]; then
            # shellcheck source=/dev/null
            source venv/bin/activate
        else
            echo "Error: --skip-build specified, but venv not found. Cannot proceed."
            exit 1
        fi
    fi

    # Decide which workflow to run
    if [[ "$GENERATE_ONLY" == "true" ]]; then
        print_header "Bloginator Generation Workflow"
        run_generation_workflow
        exit 0
    fi

    print_header "Bloginator E2E Workflow"
    echo ""

    # Handle restart flag for full workflow
    if [[ "$RESTART" == "true" ]]; then
        step_cleanup_state
    fi

    # Run full workflow steps
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

    step_setup_corpus
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
