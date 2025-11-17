#!/usr/bin/env bash
# Bloginator macOS Development Environment Setup
# Usage: ./scripts/setup-macos.sh [OPTIONS]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
init_script

readonly VENV_DIR="${REPO_ROOT}/.venv"
readonly PYTHON_VERSION="3.13"
readonly REQUIRED_PYTHON_MIN="3.10"
readonly REQUIRED_PYTHON_MAX="3.14"  # Exclusive upper bound

AUTO_CONFIRM=false
VERBOSE=false
PYTHON_CMD=""  # Will be set by install_python()

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes)
                AUTO_CONFIRM=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                grep '^#' "$0" | grep -v '#!/usr/bin/env' | sed 's/^# //' | sed 's/^#//'
                exit 0
                ;;
            *)
                die "Unknown option: $1. Use --help for usage information."
                ;;
        esac
    done
}

check_macos() {
    log_section "Checking System Requirements"

    if ! is_macos; then
        die "This script is designed for macOS only. Current OS: $OSTYPE"
    fi

    local macos_version
    macos_version=$(sw_vers -productVersion)
    log_info "macOS version: $macos_version"
    log_success "System requirements check passed"
}

install_homebrew() {
    log_section "Installing Homebrew"

    if command -v brew &>/dev/null; then
        log_info "Homebrew already installed: $(brew --version | head -n1)"

        if confirm "Update Homebrew?" "y"; then
            log_info "Updating Homebrew..."
            run_quiet brew update
            log_success "Homebrew updated"
        fi
    else
        log_info "Installing Homebrew..."
        if confirm "Install Homebrew package manager?" "y"; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            log_success "Homebrew installed"
        else
            die "Homebrew is required for installation"
        fi
    fi
}

find_compatible_python() {
    # Try to find a compatible Python version (3.10-3.13)
    for version in 3.13 3.12 3.11 3.10; do
        if command -v "python${version}" &>/dev/null; then
            local py_version
            py_version=$("python${version}" --version 2>&1 | awk '{print $2}')
            local major_minor
            major_minor=$(echo "$py_version" | cut -d. -f1,2)

            # Check if version is in range [3.10, 3.14)
            if [[ $(echo -e "${major_minor}\n${REQUIRED_PYTHON_MIN}" | sort -V | head -n1) == "${REQUIRED_PYTHON_MIN}" ]] && \
               [[ $(echo -e "${major_minor}\n${REQUIRED_PYTHON_MAX}" | sort -V | head -n1) == "${major_minor}" ]]; then
                echo "python${version}"
                return 0
            fi
        fi
    done
    return 1
}

install_python() {
    log_section "Installing Python"

    if command -v python3 &>/dev/null; then
        local python_version
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
        log_info "Python already installed: $python_version"

        # Check version compatibility (>=3.10, <3.14)
        local major_minor
        major_minor=$(echo "$python_version" | cut -d. -f1,2)

        # Check if version is too old or too new
        if [[ $(echo -e "${major_minor}\n${REQUIRED_PYTHON_MIN}" | sort -V | head -n1) != "${REQUIRED_PYTHON_MIN}" ]]; then
            log_warning "Python version $python_version is below minimum $REQUIRED_PYTHON_MIN"
            PYTHON_CMD=""
        elif [[ "${major_minor}" == "${REQUIRED_PYTHON_MAX}" ]] || \
             [[ $(echo -e "${REQUIRED_PYTHON_MAX}\n${major_minor}" | sort -V | head -n1) != "${major_minor}" ]]; then
            log_warning "Python version $python_version is not compatible (requires <$REQUIRED_PYTHON_MAX)"
            PYTHON_CMD=""
        else
            log_success "Python version meets requirements"
            PYTHON_CMD="python3"
            return 0
        fi
    fi

    # Try to find a compatible Python version
    log_info "Looking for compatible Python version..."
    if PYTHON_CMD=$(find_compatible_python); then
        log_success "Found compatible Python: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1 | awk '{print $2}'))"
        return 0
    fi

    # Need to install a compatible Python
    log_info "Installing Python $PYTHON_VERSION..."
    if confirm "Install Python $PYTHON_VERSION via Homebrew?" "y"; then
        run_quiet brew install "python@${PYTHON_VERSION}"
        PYTHON_CMD="python${PYTHON_VERSION}"
        log_success "Python $PYTHON_VERSION installed"
    else
        die "A compatible Python version (${REQUIRED_PYTHON_MIN} <= version < ${REQUIRED_PYTHON_MAX}) is required"
    fi

    # Verify installation
    require_command "$PYTHON_CMD" "Python installation failed"
    log_info "Using Python: $(which "$PYTHON_CMD")"
    log_info "Python version: $($PYTHON_CMD --version)"
}

install_git() {
    log_section "Installing Git"

    if command -v git &>/dev/null; then
        log_info "Git already installed: $(git --version)"
        log_success "Git is ready"
    else
        log_info "Installing Git..."
        if confirm "Install Git?" "y"; then
            run_quiet brew install git
            log_success "Git installed"
        else
            die "Git is required for development"
        fi
    fi
}

install_dev_tools() {
    log_section "Installing Development Tools"

    # Gitleaks for secrets scanning
    if ! command -v gitleaks &>/dev/null; then
        if confirm "Install gitleaks for secrets scanning?" "y"; then
            log_info "Installing gitleaks..."
            run_quiet brew install gitleaks
            log_success "Gitleaks installed"
        fi
    else
        log_info "Gitleaks already installed"
    fi

    # Pre-commit for git hooks
    if ! command -v pre-commit &>/dev/null; then
        if confirm "Install pre-commit for git hooks?" "y"; then
            log_info "Installing pre-commit..."
            run_quiet brew install pre-commit
            log_success "Pre-commit installed"
        fi
    else
        log_info "Pre-commit already installed"
    fi
}

setup_virtualenv() {
    log_section "Setting Up Python Virtual Environment"

    if [[ -d "$VENV_DIR" ]]; then
        log_info "Virtual environment already exists: $VENV_DIR"

        if confirm "Recreate virtual environment?" "n"; then
            log_info "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
        else
            log_success "Using existing virtual environment"
            return 0
        fi
    fi

    log_info "Creating virtual environment at $VENV_DIR..."
    log_info "Using Python: $PYTHON_CMD"
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    log_success "Virtual environment created"

    # Activate virtual environment
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"

    # Upgrade pip
    log_info "Upgrading pip..."
    run_quiet python -m pip install --upgrade pip
    log_success "pip upgraded"
}

install_python_dependencies() {
    log_section "Installing Python Dependencies"

    # Ensure we're in the virtual environment
    if ! is_venv_active; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
    fi

    require_file "${REPO_ROOT}/pyproject.toml" "pyproject.toml not found"

    # Install project with development dependencies
    log_info "Installing Bloginator with development dependencies..."
    if [[ "$VERBOSE" == "true" ]]; then
        python3 -m pip install -e ".[dev]"
    else
        python3 -m pip install -e ".[dev]" --quiet
    fi
    log_success "Python dependencies installed"

    # Verify key packages
    log_info "Verifying installed packages..."
    local packages=("click" "chromadb" "sentence-transformers" "pytest" "black" "ruff" "mypy")
    for pkg in "${packages[@]}"; do
        if python3 -m pip show "$pkg" &>/dev/null; then
            log_debug "  ✓ $pkg"
        else
            log_warning "  ✗ $pkg not found"
        fi
    done
    log_success "Package verification completed"
}

install_precommit_hooks() {
    log_section "Installing Pre-commit Hooks"

    if ! command -v pre-commit &>/dev/null; then
        log_warning "Pre-commit not installed, skipping hooks setup"
        log_info "Install with: brew install pre-commit"
        return 0
    fi

    if [[ -f "${REPO_ROOT}/.pre-commit-config.yaml" ]]; then
        log_info "Installing pre-commit hooks..."
        run_quiet pre-commit install
        log_success "Pre-commit hooks installed"

        if confirm "Run pre-commit on all files to verify setup?" "n"; then
            log_info "Running pre-commit on all files..."
            if pre-commit run --all-files; then
                log_success "Pre-commit validation passed"
            else
                log_warning "Pre-commit found some issues (this is normal on first run)"
            fi
        fi
    else
        log_warning "No .pre-commit-config.yaml found, skipping"
    fi
}

download_ml_models() {
    log_section "Downloading ML Models"

    # Ensure we're in the virtual environment
    if ! is_venv_active; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
    fi

    if confirm "Download sentence-transformers model (all-MiniLM-L6-v2)?" "y"; then
        log_info "Downloading model (this may take a few minutes)..."
        python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
        log_success "Model downloaded and cached"
    else
        log_info "Skipping model download (will download on first use)"
    fi
}

verify_installation() {
    log_section "Verifying Installation"

    # Ensure we're in the virtual environment
    if ! is_venv_active; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
    fi

    # Check CLI is accessible
    log_info "Checking Bloginator CLI..."
    if python3 -m bloginator.cli.main --version &>/dev/null; then
        log_success "Bloginator CLI is working"
    else
        log_warning "Bloginator CLI check failed"
    fi

    # Run basic tests
    if confirm "Run quick validation tests?" "y"; then
        log_info "Running validation tests..."
        if [[ -f "${REPO_ROOT}/validate-monorepo.sh" ]]; then
            bash "${REPO_ROOT}/validate-monorepo.sh" --quick || log_warning "Validation found some issues"
        else
            log_warning "validate-monorepo.sh not found"
        fi
    fi

    log_success "Installation verification completed"
}

print_next_steps() {
    log_header "Installation Complete!"

    cat << EOF

Next steps:

1. Activate the virtual environment:
   source .venv/bin/activate

2. Verify the installation:
   python -m bloginator.cli.main --version

3. Run tests and validation:
   ./validate-monorepo.sh

4. Try the CLI commands:
   bloginator extract --help
   bloginator index --help
   bloginator search --help
   bloginator outline --help
   bloginator draft --help

For more information:
  - README.md (project overview)
  - .claude/project-context.md (development guide)

EOF

    if [[ $ERROR_COUNT -gt 0 ]] || [[ $WARNING_COUNT -gt 0 ]]; then
        log_warning "Setup completed with $ERROR_COUNT error(s) and $WARNING_COUNT warning(s)"
    else
        log_success "Setup completed successfully!"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    log_header "Bloginator macOS Development Environment Setup"

    parse_args "$@"

    # Show configuration
    if [[ "$AUTO_CONFIRM" == "true" ]]; then
        log_info "Running in auto-confirm mode"
    fi
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Running in verbose mode"
    fi
    echo ""

    # Run setup steps
    check_macos
    install_homebrew
    install_python
    install_git
    install_dev_tools
    setup_virtualenv
    install_python_dependencies
    install_precommit_hooks
    download_ml_models
    verify_installation

    # Print summary and next steps
    print_next_steps
}

# Run main function
main "$@"
