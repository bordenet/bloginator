#!/usr/bin/env bash
################################################################################
# Script Name: run-streamlit.sh
################################################################################
# PURPOSE: Launch Bloginator Streamlit web UI
# USAGE: ./run-streamlit.sh [OPTIONS]
# PLATFORM: Cross-platform (Linux/macOS)
################################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Timer state
SCRIPT_START_TIME=$(date +%s)
TIMER_PID=""

# Timer functions
update_timer() {
    local start_time="$1"
    while true; do
        local cols elapsed hours minutes seconds timer_text timer_col
        cols=$(tput cols 2>/dev/null || echo 80)
        elapsed=$(($(date +%s) - start_time))
        hours=$((elapsed / 3600))
        minutes=$(((elapsed % 3600) / 60))
        seconds=$((elapsed % 60))
        printf -v timer_text "[%02d:%02d:%02d]" "$hours" "$minutes" "$seconds"
        timer_col=$((cols - ${#timer_text}))
        echo -ne "\033[s\033[1;${timer_col}H\033[33;40m${timer_text}\033[0m\033[u"
        sleep 1
    done
}

start_timer() {
    update_timer "$SCRIPT_START_TIME" &
    TIMER_PID=$!
}

stop_timer() {
    [[ -n "$TIMER_PID" ]] && { kill "$TIMER_PID" 2>/dev/null || true; wait "$TIMER_PID" 2>/dev/null || true; }
    TIMER_PID=""
}

trap stop_timer EXIT

# Default port
PORT="${STREAMLIT_PORT:-8501}"

# Parse arguments
OPEN_BROWSER=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --no-browser)
            OPEN_BROWSER=false
            shift
            ;;
        --help|-h)
            cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bloginator - Streamlit Web UI Launcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Launch the Bloginator web interface.

Usage:
  ./run-streamlit.sh [OPTIONS]

Options:
  --port PORT      Port to run on (default: 8501)
  --no-browser     Don't open browser automatically
  --help, -h       Show this help message

Examples:
  ./run-streamlit.sh                 # Launch on default port 8501
  ./run-streamlit.sh --port 8080     # Launch on custom port
  ./run-streamlit.sh --no-browser    # Don't open browser
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

# Start timer
start_timer

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Bloginator Web UI${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo -e "${RED}✗ Streamlit not found${NC}"
    echo ""
    echo "Install it with:"
    echo "  pip install -e '.[web]'"
    echo ""
    echo "Or install all dependencies:"
    echo "  pip install -e '.[all]'"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo -e "${YELLOW}⚠ No virtual environment detected${NC}"
    echo ""

    # Check for venv311, venv, or .venv (in that order of preference)
    if [ -d "venv311" ]; then
        VENV_PATH="venv311"
    elif [ -d "venv" ]; then
        VENV_PATH="venv"
    elif [ -d ".venv" ]; then
        VENV_PATH=".venv"
    else
        VENV_PATH=""
    fi

    if [ -n "$VENV_PATH" ]; then
        echo "Found virtual environment: ${YELLOW}${VENV_PATH}${NC}"
        echo "Activate with:"
        echo "  source ${VENV_PATH}/bin/activate"
        echo ""
        echo -e -n "Automatically activate virtual environment '${YELLOW}${VENV_PATH}${NC}'? ${GREEN}[Y/n]${NC} (Timeout 3s) "

        # Clear REPLY before reading to prevent previous values from affecting timeout
        REPLY=""
        # Disable echo to prevent user input from being displayed
        stty -echo
        # Read a single character with a 3-second timeout
        # -t 3: timeout after 3 seconds
        # -n 1: read only 1 character
        # -r: raw input (backslashes do not act as escape characters)
        read -t 3 -n 1 -r REPLY || true # || true to prevent script from exiting on timeout
        # Re-enable echo
        stty echo
        echo # Add a newline after the prompt

        if [[ "$REPLY" =~ ^[nN]$ ]]; then
            echo -e "${YELLOW}Virtual environment activation skipped.${NC}"
            echo -e "${YELLOW}Please activate it manually if needed: source ${VENV_PATH}/bin/activate${NC}"
            exit 1
        else
            echo -e "${GREEN}Activating virtual environment...${NC}"
            source "$VENV_PATH/bin/activate"
        fi
    else
        echo "No virtual environment found. Create one with:"
        echo "  python3 -m venv venv311"
        echo "  source venv311/bin/activate"
        echo "  pip install -e '.[web]'"
        exit 1
    fi
fi

# Check for UI module
if [ ! -f "src/bloginator/ui/app.py" ]; then
    echo -e "${RED}✗ UI module not found at src/bloginator/ui/app.py${NC}"
    exit 1
fi

# Check for chromadb and other critical Python dependencies
if ! python -c "import chromadb" &> /dev/null || \
   ! python -c "import streamlit" &> /dev/null; then # Added streamlit check for completeness
    echo -e "${YELLOW}⚠ Missing critical Python dependencies (e.g., chromadb, streamlit).${NC}"
    echo -e -n "Install them using 'pip install -e '.[web]'? ${GREEN}[Y/n]${NC} (Timeout 3s) "

    REPLY=""
    stty -echo
    read -t 3 -n 1 -r REPLY || true
    stty echo
    echo # Add a newline after the prompt

    if [[ "$REPLY" =~ ^[nN]$ ]]; then
        echo -e "${YELLOW}Dependency installation skipped. Please install manually if needed: pip install -e '.[web]'${NC}"
        exit 1
    else
        echo -e "${GREEN}Installing dependencies...${NC}"
        if pip install -e '.[web]'; then
            echo -e "${GREEN}✓ Dependencies installed successfully.${NC}"
        else
            echo -e "${RED}✗ Failed to install dependencies. Please try running 'pip install -e '.[web]'' manually.${NC}"
            exit 1
        fi
    fi
fi

# Define the required Streamlit version based on pyproject.toml
REQUIRED_STREAMLIT_VERSION="1.28.0"

# Get the currently installed Streamlit version
CURRENT_STREAMLIT_VERSION=""
if python -c "import streamlit; print(streamlit.__version__)" &> /dev/null; then
    CURRENT_STREAMLIT_VERSION=$(python -c "import streamlit; print(streamlit.__version__)")
fi

if [[ "$CURRENT_STREAMLIT_VERSION" != "$REQUIRED_STREAMLIT_VERSION" ]]; then
    echo -e "${YELLOW}⚠ Streamlit version mismatch.${NC}"
    echo -e "${YELLOW}Required: ${REQUIRED_STREAMLIT_VERSION}, Installed: ${CURRENT_STREAMLIT_VERSION:-'None'}${NC}"
    echo -e -n "Install Streamlit version ${REQUIRED_STREAMLIT_VERSION}? ${GREEN}[Y/n]${NC} (Timeout 3s) "

    REPLY=""
    stty -echo
    read -t 3 -n 1 -r REPLY || true
    stty echo
    echo # Add a newline after the prompt

    if [[ "$REPLY" =~ ^[nN]$ ]]; then
        echo -e "${YELLOW}Streamlit version change skipped. Please ensure a compatible version is installed manually.${NC}"
        exit 1
    else
        echo -e "${GREEN}Installing Streamlit==${REQUIRED_STREAMLIT_VERSION}...${NC}"
        if pip install "streamlit==${REQUIRED_STREAMLIT_VERSION}"; then
            echo -e "${GREEN}✓ Streamlit ${REQUIRED_STREAMLIT_VERSION} installed successfully.${NC}"
        else
            echo -e "${RED}✗ Failed to install Streamlit==${REQUIRED_STREAMLIT_VERSION}. Please try manually.${NC}"
            exit 1
        fi
    fi
fi

echo -e "${GREEN}✓ Environment ready${NC}"
echo ""

# Kill any existing Streamlit instances
EXISTING_PIDS=$(pgrep -f "streamlit run.*bloginator" || true)
if [ -n "$EXISTING_PIDS" ]; then
    echo -e "${YELLOW}ℹ${NC} Stopping existing Streamlit instances..."
    echo "$EXISTING_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Old instances stopped${NC}"
    echo ""
fi

# Launch Streamlit
echo -e "${BLUE}ℹ${NC} Starting Streamlit on port ${PORT}..."
echo -e "${BLUE}ℹ${NC} URL: ${CYAN}http://localhost:${PORT}${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Build streamlit command
STREAMLIT_CMD="streamlit run src/bloginator/ui/app.py --server.port=${PORT}"

if ! $OPEN_BROWSER; then
    STREAMLIT_CMD="${STREAMLIT_CMD} --server.headless=true"
fi

# Run streamlit
exec ${STREAMLIT_CMD}
