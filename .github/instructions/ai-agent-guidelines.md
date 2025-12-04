---
description: Engineering excellence guidelines for AI agents working on Bloginator and derived projects
applyTo: '**'
---

# AI Agent Engineering Guidelines - Bloginator Standard

This document establishes mandatory engineering standards for all AI-assisted development on Bloginator and projects derived from this codebase. These standards are non-negotiable and must be enforced automatically without manual reminder.

**Last Updated**: 2025-11-22
**Standard Version**: 1.0.0
**Applies To**: All Bloginator-derived projects

---

## 1. Code Quality Standards (MANDATORY)

### 1.1 Test Coverage Requirements

**CRITICAL**: All code changes MUST maintain or improve test coverage.

- **Minimum Coverage**: 85% line coverage AND 85% branch coverage
- **Measurement**: Use `pytest --cov=src --cov-branch --cov-report=term`
- **Enforcement**: CI must fail if coverage drops below 85%
- **New Code**: 100% coverage required for all new modules

**Before ANY code commit**:
1. Run full test suite: `pytest tests/ -v`
2. Measure coverage: `pytest --cov=src --cov-branch --cov-report=json`
3. Verify coverage >= 85% for both line and branch
4. If coverage drops, add tests BEFORE committing

### 1.2 Type Safety Requirements

**CRITICAL**: All Python code MUST pass MyPy strict type checking.

- **Configuration**: MyPy strict mode (see pyproject.toml)
- **Zero Tolerance**: No type errors allowed in new code
- **Existing Code**: Fix type errors before adding features
- **Command**: `mypy src/bloginator --strict`

**Type Annotation Rules**:
- All function signatures must have complete type hints
- All function return types must be explicitly annotated
- Use `typing` module for complex types
- No `Any` types without explicit justification comment

### 1.3 Code Formatting and Linting

**CRITICAL**: All code MUST pass automated quality checks.

**Required Tools**:
- **Black**: `black src/ tests/ --line-length 100`
- **Ruff**: `ruff check src/ tests/`
- **isort**: `isort src/ tests/ --profile black`
- **pydocstyle**: `pydocstyle src/bloginator`

**Pre-commit Hooks**: MUST be installed and passing
```bash
pre-commit install
pre-commit run --all-files
```

### 1.4 Documentation Requirements

**CRITICAL**: All public APIs MUST have Google-style docstrings.

**Required Elements**:
- Module-level docstring explaining purpose
- Class docstring with attributes description
- Function/method docstring with Args, Returns, Raises
- Complex logic must have inline comments

**Example**:
```python
def process_document(path: Path, quality: QualityRating) -> Document:
    """Extract and process a document from the filesystem.

    Args:
        path: Absolute path to document file
        quality: Quality rating for search ranking

    Returns:
        Processed Document with extracted content and metadata

    Raises:
        FileNotFoundError: If path does not exist
        ExtractionError: If document cannot be processed
    """
```

---

## 2. Testing Strategy (MANDATORY)

### 2.1 Test Organization

**Structure**:
```
tests/
├── unit/           # Fast, isolated tests (>90% of tests)
├── integration/    # Multi-component tests
├── e2e/           # Full workflow tests
└── benchmarks/    # Performance tests
```

### 2.2 Test Coverage Requirements by Layer

| Layer | Minimum Coverage | Priority |
|-------|-----------------|----------|
| Models | 100% | Critical |
| Core Logic | 95% | Critical |
| CLI Commands | 85% | High |
| API Endpoints | 85% | High |
| UI Components | 75% | Medium |
| Utilities | 90% | High |

### 2.3 Required Test Scenarios

**For EVERY new feature, implement tests for**:
1. **Happy Path**: Normal successful operation
2. **Edge Cases**: Boundary conditions, empty inputs, max values
3. **Error Paths**: Invalid inputs, missing files, network failures
4. **Concurrency**: Race conditions if applicable
5. **Failure Recovery**: Retry logic, graceful degradation

### 2.4 LLM Testing Strategy (CRITICAL FOR AI PROJECTS)

**MANDATORY**: All LLM-dependent code MUST support mock mode for testing.

**Environment Variable**: `BLOGINATOR_LLM_MOCK=true`
- When set, MUST use MockLLMClient instead of real LLM
- Must work in CI/CD without API keys
- Must provide deterministic, testable responses

**Mock Implementation Requirements**:
- Detect request type (outline, draft, refinement)
- Return realistic, structured responses
- Support error injection for failure testing
- Log all requests for debugging

**VS Code Integration**:
- Provide launch.json configurations for mock mode
- Document debugging workflow with mocks
- Enable end-to-end testing without external dependencies

---

## 3. Security Standards (MANDATORY)

### 3.1 Secret Management

**CRITICAL**: NEVER commit secrets to version control.

**Required Practices**:
- Use `.env` files for local secrets (gitignored)
- Use environment variables in CI/CD
- Rotate API keys regularly
- Use `gitleaks` to scan for secrets before commit

**Pre-commit Check**:
```bash
gitleaks detect --source . --verbose
```

### 3.2 Security Scanning

**MANDATORY**: Run security tools before every commit.

**Required Tools**:
- **Bandit**: `bandit -r src/bloginator/`
- **pip-audit**: `pip-audit` (check dependencies)
- **Safety**: `safety check` (alternative to pip-audit)

**CI/CD**: Security scans MUST run on every PR

### 3.3 Dependency Security

**CRITICAL**: Keep dependencies updated and secure.

**Requirements**:
- Pin exact versions in requirements.txt
- Use dependabot for automated updates
- Review security advisories weekly
- Update critical security patches within 48 hours

---

## 4. CI/CD Standards (MANDATORY)

### 4.1 Required CI Checks

**ALL of these MUST pass before merge**:
1. ✅ Tests (all Python versions: 3.10, 3.11, 3.12)
2. ✅ Coverage >= 85% (line and branch)
3. ✅ Ruff linting (zero errors)
4. ✅ MyPy type checking (zero errors)
5. ✅ Bandit security scan (zero high/medium issues)
6. ✅ pip-audit (zero vulnerabilities)
7. ✅ pydocstyle (zero errors)

### 4.2 Coverage Enforcement

**pyproject.toml configuration**:
```toml
[tool.coverage.report]
fail_under = 85.0
show_missing = true
```

**CI command**:
```bash
pytest --cov=src --cov-branch --cov-report=term --cov-fail-under=85
```

---

## 5. Language and Documentation Standards (MANDATORY)

### 5.1 Prohibited Language

**NEVER use these terms without evidence**:
- "production-grade" (unless deployed in production)
- "enterprise-ready" (unless used by enterprises)
- "world-class" (subjective marketing)
- "best-in-class" (subjective marketing)
- "cutting-edge" (vague marketing)
- "revolutionary" (hyperbole)

### 5.2 Required Language Style

**Use precise, factual language**:
- ✅ "Implements X using Y algorithm"
- ✅ "Achieves 85% test coverage"
- ✅ "Supports Python 3.10+"
- ❌ "Production-grade implementation"
- ❌ "Enterprise-level quality"
- ❌ "World-class testing"

### 5.3 Cross-Reference Validation

**MANDATORY**: All documentation links MUST be valid.

**Automated Check**:
```bash
# Run after ANY documentation change
./scripts/validate-cross-references.sh
```

**Requirements**:
- All internal links must resolve
- All file references must exist
- All shell scripts must be executable
- All examples must be tested

---

## 6. LLM Mock Integration (MANDATORY FOR AI PROJECTS)

### 6.1 Mock Mode Environment Variable

**REQUIRED**: Support `BLOGINATOR_LLM_MOCK=true` environment variable.

**Behavior**:
- When set, use MockLLMClient for all LLM operations
- No external API calls
- Deterministic responses for testing
- Full end-to-end workflow support

### 6.2 VS Code Configuration

**REQUIRED**: Provide `.vscode/launch.json` with mock configurations.

**Example**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Bloginator CLI (Mock LLM)",
      "type": "python",
      "request": "launch",
      "module": "bloginator.cli.main",
      "args": ["outline", "--index", "test_index", "--keywords", "test"],
      "env": {
        "BLOGINATOR_LLM_MOCK": "true"
      }
    }
  ]
}
```

### 6.3 Mock Testing Documentation

**REQUIRED**: Document in `docs/TESTING_GUIDE.md`:
- How to enable mock mode
- How to test with mocks in VS Code
- How to inject errors for failure testing
- Privacy/security implications of mock vs real LLM

---

## 7. Enforcement and Compliance

### 7.1 Automated Enforcement

**These standards are enforced automatically**:
- Pre-commit hooks prevent non-compliant commits
- CI/CD fails on standard violations
- Coverage drops block merges
- Type errors block merges

### 7.2 AI Agent Behavior

**AI agents working on this codebase MUST**:
1. Run all quality checks before suggesting code
2. Include tests with every code change
3. Verify coverage after changes
4. Fix type errors immediately
5. Use factual, precise language
6. Validate all documentation links
7. Never commit without passing all checks

### 7.3 Violation Response

**If standards are violated**:
1. CI/CD fails immediately
2. PR is blocked from merge
3. Automated comment explains violation
4. Developer must fix before proceeding

---

## 8. Project-Specific Standards

### 8.1 Bloginator-Specific Requirements

**Content Safety**:
- All generated content MUST pass blocklist validation
- No proprietary content in examples or tests
- Privacy-sensitive data must be sanitized

**LLM Provider Support**:
- Must support Ollama (local)
- Must support OpenAI-compatible APIs
- Must support mock mode for testing

**Documentation**:
- User guide for end users
- Developer guide for contributors
- Custom LLM guide for integrations

---

## 9. Continuous Improvement

### 9.1 Metrics Tracking

**Track and report**:
- Test coverage (line and branch)
- Type coverage (MyPy)
- Security scan results
- Performance benchmarks

### 9.2 Regular Reviews

**Quarterly**:
- Review and update these guidelines
- Assess compliance across projects
- Identify improvement opportunities
- Update tooling and standards

---

## 10. Quick Reference Checklist

**Before EVERY commit**:
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage >= 85%: `pytest --cov=src --cov-branch`
- [ ] No type errors: `mypy src/bloginator`
- [ ] Linting passes: `ruff check src/ tests/`
- [ ] Formatting correct: `black src/ tests/ --check`
- [ ] Docstrings complete: `pydocstyle src/bloginator`
- [ ] No secrets: `gitleaks detect --source .`
- [ ] Security clean: `bandit -r src/bloginator/`
- [ ] Pre-commit passes: `pre-commit run --all-files`

**Before EVERY PR**:
- [ ] All CI checks green
- [ ] Documentation updated
- [ ] docs/CHANGELOG.md updated
- [ ] Cross-references validated
- [ ] No prohibited language in docs

---

*These standards are mandatory and non-negotiable. Compliance is enforced automatically.*
