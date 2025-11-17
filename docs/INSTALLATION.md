# Installation Guide

This guide will walk you through installing and setting up Bloginator on your system.

## Prerequisites

### Required

- **Python 3.10 or higher**
- **pip** (Python package manager)
- **Git** (for cloning the repository)

### Recommended

- **Ollama** or **LM Studio** for local LLM inference (privacy-preserving mode)
- **4GB+ available RAM** for vector indexing
- **1GB+ disk space** for dependencies and index storage

### Optional

- Cloud LLM API key (Claude, GPT-4, etc.) if not using local mode

---

## Installation Methods

### Method 1: Install from Source (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/bordenet/bloginator.git
cd bloginator

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Bloginator with development dependencies
pip install -e ".[dev]"

# 4. Verify installation
bloginator --version
```

### Method 2: Install for Development

If you plan to contribute or modify Bloginator:

```bash
# 1. Clone and navigate to repository
git clone https://github.com/bordenet/bloginator.git
cd bloginator

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install with development dependencies
pip install -e ".[dev]"

# 4. Install pre-commit hooks for code quality
pre-commit install

# 5. Run tests to verify setup
pytest tests/unit/ -q
```

---

## Post-Installation Setup

### 1. Set Up Local LLM (Recommended)

For privacy-preserving, cost-free operation, install a local LLM:

#### Option A: Ollama (Recommended)

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Or on macOS with Homebrew
brew install ollama

# Pull a model (recommended: llama2 or mistral)
ollama pull llama2
ollama pull mistral

# Verify Ollama is running
ollama list
```

#### Option B: LM Studio

1. Download from [https://lmstudio.ai/](https://lmstudio.ai/)
2. Install and launch LM Studio
3. Download a model (recommended: Llama 2 or Mistral 7B)
4. Start the local server

### 2. Configure Environment (Optional)

Create a `.env` file in your project directory for custom configuration:

```bash
# Optional: Specify custom paths
BLOGINATOR_DATA_DIR=~/.bloginator/data
BLOGINATOR_INDEX_DIR=~/.bloginator/index
BLOGINATOR_BLOCKLIST_PATH=~/.bloginator/blocklist.json

# Optional: Cloud LLM configuration (if not using local mode)
# ANTHROPIC_API_KEY=your_api_key_here
# OPENAI_API_KEY=your_api_key_here

# Optional: LLM provider preference
LLM_PROVIDER=ollama  # Options: ollama, lmstudio, anthropic, openai
LLM_MODEL=llama2     # Default model to use
```

### 3. Verify Installation

```bash
# Check version
bloginator --version

# View available commands
bloginator --help

# Run a quick test
bloginator search --help
```

---

## Setting Up Your First Corpus

### 1. Gather Your Writing

Collect your historical writing into a directory:

```bash
mkdir ~/my-corpus
# Copy your PDFs, DOCX files, Markdown files, etc. to this directory
```

Supported formats:
- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- Markdown (`.md`)
- Plain text (`.txt`)
- ZIP archives containing any of the above

### 2. Extract and Index

```bash
# Extract text from your documents
bloginator extract ~/my-corpus -o ./extracted --quality preferred

# Create searchable vector index
bloginator index ./extracted -o ./my-index
```

### 3. Test Search

```bash
# Search your corpus
bloginator search ./my-index "leadership" -n 5
```

### 4. Start Web UI

```bash
# Launch the web interface
bloginator serve --port 8000

# Open browser to http://localhost:8000
```

---

## Troubleshooting

### Python Version Issues

If you see errors about Python version:

```bash
# Check your Python version
python3 --version

# If < 3.10, install a newer version
# macOS (Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11
```

### Missing Dependencies

If extraction fails with PDF or DOCX errors:

```bash
# Reinstall with all dependencies
pip install -e ".[dev]" --force-reinstall
```

### ChromaDB Installation Issues

If you encounter ChromaDB/SQLite errors:

```bash
# macOS: Install system SQLite
brew install sqlite

# Linux: Install build dependencies
sudo apt install build-essential python3-dev

# Reinstall ChromaDB
pip uninstall chromadb
pip install chromadb
```

### Ollama Connection Issues

If Bloginator can't connect to Ollama:

```bash
# Verify Ollama is running
ollama list

# Start Ollama service (if needed)
ollama serve

# Check if models are available
ollama list
```

### Import Errors

If you see "Module not found" errors:

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall in development mode
pip install -e ".[dev]"
```

---

## Upgrading

To upgrade to the latest version:

```bash
# Navigate to repository
cd bloginator

# Pull latest changes
git pull origin main

# Update dependencies
pip install -e ".[dev]" --upgrade

# Run migrations (if any)
# Migration commands will be shown in release notes
```

---

## Uninstalling

To completely remove Bloginator:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Remove repository (if desired)
cd ..
rm -rf bloginator/

# Remove data directories (if created)
rm -rf ~/.bloginator/
```

---

## Next Steps

Once installed, proceed to the [User Guide](USER_GUIDE.md) to learn how to:
- Build and search your corpus
- Generate documents from templates
- Refine content with natural language feedback
- Export to various formats

---

## Getting Help

- **Documentation**: [docs/](.)
- **Issues**: [GitHub Issues](https://github.com/bordenet/bloginator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bordenet/bloginator/discussions)

---

## System Requirements Summary

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.11+ |
| RAM | 4GB | 8GB+ |
| Disk Space | 1GB | 5GB+ (for models) |
| OS | macOS, Linux, Windows 10+ | macOS, Linux |
| LLM | Cloud API | Local (Ollama/LM Studio) |
