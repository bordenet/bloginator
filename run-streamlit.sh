#!/usr/bin/env bash

################################################################################
# Bloginator Streamlit Web UI Launcher
################################################################################
# PURPOSE: Launch the Bloginator Streamlit web application
#   - Validates Python environment and dependencies
#   - Ensures correct streamlit version (1.28.0)
#   - Auto-activates virtual environment if needed
#   - Stops any existing instances
#   - Launches on specified port with optional browser
#
# USAGE:
#   ./run-streamlit.sh [OPTIONS]
#   ./run-streamlit.sh --help
#
# OPTIONS:
#   --port PORT     Port to run on (default: 8501)
#   --no-browser    Don't open browser automatically
#   -v, --verbose   Show detailed output
#   -h, --help      Display help message
#
# EXAMPLES:
#   ./run-streamlit.sh              # Launch on port 8501 with browser
#   ./run-streamlit.sh --port 8080  # Launch on custom port
#   ./run-streamlit.sh --no-browser # Launch without opening browser
#   ./run-streamlit.sh -v           # Verbose output
#
# DEPENDENCIES:
#   - Python 3.10+
#   - Virtual environment (.venv)
#   - streamlit==1.28.0
#   - bloginator package installed
#
# NOTES:
#   - App takes ~10 seconds to initialize on first run
#   - Press Ctrl+C to stop the server
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

cd "$SCRIPT_DIR"

################################################################################
# Configuration
################################################################################

VENV_DIR="${SCRIPT_DIR}/.venv"
PORT="${STREAMLIT_PORT:-8501}"
OPEN_BROWSER=true
REQUIRED_STREAMLIT_VERSION="1.28.0"
VERBOSE=${VERBOSE:-0}

################################################################################
# Helper Functions
################################################################################

print_error() {
    echo -e "${C_RED}✗ Error: $*${C_RESET}" >&2
}

confirm() {
    local prompt="$1"
    local default="${2:-y}"
    
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
# Argument Parsing
################################################################################

show_help() {
    cat << 'EOF'
NAME
    run-streamlit.sh - Launch Bloginator web UI

SYNOPSIS
    ./run-streamlit.sh [OPTIONS]

DESCRIPTION
    Launches the Bloginator Streamlit web application with automatic
    environment validation and setup.

OPTIONS
    --port PORT     Port to run on (default: 8501)
    --no-browser    Don't open browser automatically
    -v, --verbose   Show detailed output
    -h, --help      Display this help

EXAMPLES
    ./run-streamlit.sh              # Launch on port 8501 with browser
    ./run-streamlit.sh --port 8080  # Launch on custom port
    ./run-streamlit.sh --no-browser # Launch without browser
    ./run-streamlit.sh -v           # Verbose output

INITIALIZATION TIME
    First run: ~10-15 seconds (model downloads)
    Subsequent runs: 5-10 seconds
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port) PORT="$2"; shift 2 ;;
            --no-browser) OPEN_BROWSER=false; shift ;;
            -v|--verbose) export VERBOSE=1; shift ;;
            -h|--help) show_help; exit 0 ;;
            *) print_error "Unknown option: $1"; exit 1 ;;
        esac
    done
}

################################################################################
# Validation Functions
################################################################################

check_venv() {
    task_start "Checking virtual environment"
    
    if [[ ! -d "$VENV_DIR" ]]; then
        task_fail "Virtual environment not found at $VENV_DIR"
        echo ""
        echo "Create it with: ./scripts/setup-macos.sh"
        exit 1
    fi
    
    verbose "Virtual environment found at $VENV_DIR"
    task_ok "Virtual environment ready"
}

activate_venv() {
    task_start "Activating virtual environment"
    
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    
    verbose "Virtual environment activated"
    task_ok "Environment activated"
}

check_dependencies() {
    task_start "Checking dependencies"
    
    # Check for UI module
    if [[ ! -f "$SCRIPT_DIR/src/bloginator/ui/app.py" ]]; then
        task_fail "UI module not found at src/bloginator/ui/app.py"
        exit 1
    fi
    verbose "UI module found"
    
    # Check for critical packages
    if ! python -c "import streamlit, chromadb, bloginator" 2>/dev/null; then
        task_warn "Missing required packages"
        echo ""
        if confirm "Install required packages?"; then
            verbose "Installing packages..."
            if ! python -m pip install -e ".[web]" "streamlit==1.28.0" > /dev/null 2>&1; then
                task_fail "Failed to install packages"
                exit 1
            fi
        else
            task_fail "Required packages missing"
            exit 1
        fi
    fi
    
    verbose "All dependencies present"
    task_ok "Dependencies verified"
}

check_streamlit_version() {
    task_start "Checking streamlit version"
    
    local installed_version
    installed_version=$(python -c "import streamlit; print(streamlit.__version__)" 2>/dev/null || echo "")
    
    if [[ -z "$installed_version" ]]; then
        task_fail "Streamlit not installed"
        exit 1
    fi
    
    verbose "Installed version: $installed_version"
    
    if [[ "$installed_version" != "$REQUIRED_STREAMLIT_VERSION" ]]; then
        task_warn "Streamlit version mismatch (installed: $installed_version, required: $REQUIRED_STREAMLIT_VERSION)"
        echo ""
        if confirm "Install streamlit==$REQUIRED_STREAMLIT_VERSION?"; then
            verbose "Installing streamlit $REQUIRED_STREAMLIT_VERSION..."
            if ! python -m pip install "streamlit==$REQUIRED_STREAMLIT_VERSION" > /dev/null 2>&1; then
                task_fail "Failed to install streamlit"
                exit 1
            fi
        else
            task_warn "Continuing with version $installed_version (may have compatibility issues)"
        fi
    fi
    
    task_ok "Streamlit version verified"
}

stop_existing_instances() {
    task_start "Checking for existing instances"
    
    local existing_pids
    existing_pids=$(pgrep -f "streamlit run.*app.py" 2>/dev/null || echo "")
    
    if [[ -n "$existing_pids" ]]; then
        verbose "Found existing instances: $existing_pids"
        echo "$existing_pids" | xargs kill -9 2>/dev/null || true
        sleep 1
        verbose "Stopped existing instances"
    fi
    
    task_ok "Ready to launch"
}

################################################################################
# Main
################################################################################

main() {
    parse_args "$@"
    
    print_header "Bloginator Web UI"
    echo ""
    
    check_venv
    activate_venv
    check_dependencies
    check_streamlit_version
    stop_existing_instances
    
    echo ""
    echo "Launching streamlit on port $PORT..."
    echo "URL: http://localhost:$PORT"
    echo ""
    echo "First run takes ~10 seconds to initialize..."
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Build streamlit command
    local streamlit_cmd="streamlit run src/bloginator/ui/app.py --server.port=$PORT"
    
    if [[ "$OPEN_BROWSER" == "false" ]]; then
        streamlit_cmd="$streamlit_cmd --server.headless=true"
    fi
    
    # Run streamlit
    exec $streamlit_cmd
}

main "$@"
