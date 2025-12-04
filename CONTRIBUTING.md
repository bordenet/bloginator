# Contributing to Bloginator

Thank you for your interest in contributing to Bloginator. This document provides guidelines and instructions for contributing.

## Code of Conduct

This project follows a professional code of conduct. We expect all contributors to:
- Be respectful and constructive in discussions
- Focus on technical merit and project goals
- Welcome newcomers and help them get started
- Report issues and security vulnerabilities responsibly

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Virtual environment tool (venv, virtualenv, or conda)
- Ollama (recommended for local testing)

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/bloginator.git
   cd bloginator
   ```

3. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

6. Verify setup:
   ```bash
   pytest tests/unit/ -q
   ```

## Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation changes
- `refactor/` for code refactoring
- `test/` for test additions or improvements

### Making Changes

1. Write code following our style guide (see below)
2. Add or update tests for your changes
3. Update documentation as needed
4. Run quality checks locally:
   ```bash
   pre-commit run --all-files
   pytest tests/ -v
   ```

### Committing Changes

Write clear, descriptive commit messages:

```
type: Brief description (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what changed and why, not how.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Submitting a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a pull request on GitHub
3. Fill out the PR template completely
4. Ensure all CI checks pass
5. Respond to review feedback

## Code Quality Standards

### Style Guide

- **Formatting**: Black with 100 character line length
- **Linting**: Ruff with project configuration
- **Type Hints**: Required for all functions (MyPy strict mode)
- **Docstrings**: Google style for all public functions and classes
- **Imports**: Sorted with isort (black-compatible profile)

### Testing Requirements

- All new features must include tests
- Bug fixes must include regression tests
- Maintain or improve code coverage
- Tests must pass on Python 3.10, 3.11, and 3.12

### Test Categories

- **Unit tests**: `tests/unit/` - Fast, isolated tests
- **Integration tests**: `tests/integration/` - Multi-component tests
- **E2E tests**: `tests/e2e/` - Full workflow tests
- **Benchmarks**: `tests/benchmarks/` - Performance tests

Run specific test categories:
```bash
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests
pytest tests/e2e/ -v           # End-to-end tests
pytest -m "not slow" -v        # Skip slow tests
```

## Documentation

- Update relevant documentation for any user-facing changes
- Add docstrings for new functions and classes
- Update README.md if adding new features
- Add entries to docs/CHANGELOG.md

## Security

- Never commit API keys, credentials, or proprietary content
- Use `.env` files for local configuration (gitignored)
- Report security vulnerabilities privately to mattbordenet@hotmail.com
- Run `bandit` and `gitleaks` before committing

## Questions?

- Open an issue for bugs or feature requests
- Use discussions for questions and ideas
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
