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
    if [ -d ".venv" ]; then
        echo "Activate with:"
        echo "  source .venv/bin/activate"
        echo ""
        read -p "Activate now? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # shellcheck disable=SC1091
            source .venv/bin/activate
        fi
    else
        echo "Create and activate with:"
        echo "  python3 -m venv .venv"
        echo "  source .venv/bin/activate"
        echo "  pip install -e '.[all]'"
        exit 1
    fi
fi

# Check for UI module
if [ ! -f "src/bloginator/ui/app.py" ]; then
    echo -e "${RED}✗ UI module not found at src/bloginator/ui/app.py${NC}"
    exit 1
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
