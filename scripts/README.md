# Scripts Directory

Utility and workflow scripts for the Bloginator project.

## Main Workflows

- **`../run-e2e.sh`** - End-to-end workflow demo (extract → index → outline → draft)
  - Run from repository root: `./run-e2e.sh`
  - Orchestrates the complete blog generation pipeline
  - Supports resume/restart flags for resuming interrupted workflows

- **`../run-streamlit.sh`** - Launch the Streamlit web UI
  - Run from repository root: `./run-streamlit.sh`
  - Starts the Bloginator web interface on port 8501

## Blog Generation Utilities

- **`generate_remaining_blogs.sh`** - Generate multiple blog posts in sequence
  - Generates blogs 2-4 (Sprint Planning, Sprint Grooming, Retrospectives)
  - Uses `auto_respond.py` for automatic LLM response handling
  - Output files saved to `output/generated/`

- **`generate_blog_improved.sh`** - Generate a single blog post with improved coordination
  - Usage: `./generate_blog_improved.sh <output_file> <title> <thesis> <keywords> <outline_file>`
  - Better handling of auto-responder coordination
  - Example: `./generate_blog_improved.sh output/generated/blog.md "My Title" "My thesis..." "keyword1,keyword2" output/generated/outline.json`

- **`auto_respond.py`** - Automatically respond to Bloginator LLM requests
  - Used by blog generation scripts to simulate LLM responses
  - Monitors `.bloginator/llm_requests/` directory
  - Writes responses to `.bloginator/llm_responses/`
  - Can be run standalone: `python3 scripts/auto_respond.py`

## Validation & Testing

- **`../validate-monorepo.sh`** - Comprehensive code validation
  - Run from repository root: `./validate-monorepo.sh [OPTIONS]`
  - Options: `--quick`, `--all`, `--fix`, `--verbose`
  - Runs formatting, linting, type checking, and tests

## Library Scripts

- **`lib/common.sh`** - Shared utilities for other scripts
  - Common functions and helpers used across scripts
  - Sourced by validation and other scripts

- **`e2e-lib.sh`** - Shared E2E workflow library
  - Configuration and utilities for end-to-end workflows
  - Sourced by `run-e2e.sh`
  - Provides state management, timer functions, and printing utilities

## Path Resolution

All scripts are designed to work correctly from any directory by computing their own project root:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
```

This ensures scripts function properly when called from nested locations or symlinked.

## Output Directory

Generated blog files (markdown and JSON outlines) are saved to:
- `output/generated/` - Blog markdown and outline files

This directory is in `.gitignore` to prevent accidental commits of generated content.
