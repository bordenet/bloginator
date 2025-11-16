# CRITICAL LESSONS FOR CLAUDE - BLOGINATOR PROJECT

## Project Context

Bloginator is a content generation system that helps engineering leaders create authentic documents from their historical writing corpus. The system must:
- Preserve author's authentic voice (avoid "AI slop")
- Prevent proprietary content leakage
- Ground all generation in actual corpus material
- Work entirely locally for privacy

## Over-Engineering Prevention

1. **DO NOT REFACTOR WORKING CODE**
   - If code passes tests and functions correctly, leave it alone
   - Do not split files or create abstractions without explicit user request
   - Do not "improve" code that isn't broken
   - RAG pipelines are complex—working code is precious

2. **RESOURCE CONSERVATION**
   - Every edit consumes user's compute and time
   - Make minimal, necessary changes only
   - Never make speculative or "nice to have" changes
   - LLM inference is expensive—optimize prompt engineering, not code churn

3. **CHANGE VALIDATION**
   - Run tests BEFORE attempting any refactoring
   - Validate the actual problem before proposing solutions
   - Start with smallest possible change that could fix the issue
   - Test with real corpus data, not toy examples

4. **FILE ORGANIZATION**
   - Do not create new files without explicit user request
   - Do not split existing files into multiple files
   - Do not move code between files unless specifically asked
   - Modular architecture doesn't mean every function needs its own file

## Bloginator-Specific Principles

### 1. Voice Preservation is Paramount

**ALWAYS**:
- Test generated content for voice similarity against corpus
- Ground generation in actual source material
- Provide citations for all generated claims
- Flag content that lacks corpus support

**NEVER**:
- Generate content without corpus grounding
- Blend generic AI language with author's voice
- Remove citations without explicit user request
- Assume voice consistency without validation

### 2. Privacy and Proprietary Content Protection

**ALWAYS**:
- Enforce blocklist validation on all generated content
- Process documents locally—no cloud APIs without explicit consent
- Preserve document metadata and source attribution
- Warn users before any external API calls

**NEVER**:
- Skip blocklist validation "to save time"
- Send user documents to external services without permission
- Cache proprietary content in logs or debug output
- Assume a term is "safe"—validate against blocklist

### 3. RAG System Reliability

**ALWAYS**:
- Verify vector store integrity before queries
- Handle missing embeddings gracefully
- Validate chunk coverage for generated sections
- Test with realistic corpus sizes (100s of documents)

**NEVER**:
- Assume embeddings are up-to-date
- Generate content from insufficient context (<3 source chunks)
- Ignore low-confidence scores
- Skip validation of retrieved chunks

### 4. Iterative Refinement Quality

**ALWAYS**:
- Show diffs when applying refinements
- Allow reverting individual changes
- Preserve version history during session
- Validate refined content against blocklist

**NEVER**:
- Lose previous versions during refinement
- Apply feedback without showing changes
- Assume user wants to keep all changes
- Skip voice validation after refinements

## Response Guidelines

### 1. WHEN ENCOUNTERING ERRORS

**Corpus/Indexing Errors**:
- Check if vector store exists and is accessible
- Verify embedding model is loaded
- Confirm document extraction completed successfully
- Look for corrupted or locked files

**Generation Errors**:
- Verify LLM service (Ollama, LM Studio) is running
- Check if sufficient context was retrieved from corpus
- Validate prompt template syntax
- Test with simpler queries first

**Blocklist Violations**:
- Do NOT override blocklist—it exists for legal reasons
- Report violations clearly to user
- Suggest alternative phrasings or topics
- Do not attempt to "work around" blocklist

### 2. WHEN ASKED TO IMPROVE CODE

**Request Specifics**:
- "Improve voice preservation" → How? What metric?
- "Better search results" → What's wrong with current results?
- "Faster generation" → Where's the bottleneck?

**Focus on Data Before Code**:
- Is corpus adequately indexed?
- Are embeddings up-to-date?
- Is chunking strategy appropriate?
- Are prompts well-tuned?

**Code changes are often NOT the solution**:
- Poor generation quality → Improve prompts or chunk strategy
- Slow search → Optimize vector store parameters, not code
- Voice inconsistency → Analyze corpus coverage, not refactor generation engine

### 3. WHEN HANDLING DEPENDENCIES

**Local-First Stack**:
- Verify Ollama/LM Studio is running before LLM calls
- Check ChromaDB/FAISS vector store is accessible
- Confirm sentence-transformers model is downloaded
- Validate document extraction libraries (PyMuPDF, python-docx)

**No Surprise Cloud Dependencies**:
- Do NOT add OpenAI, Anthropic, or cloud APIs without explicit user request
- If cloud LLM is optional, make it clearly opt-in
- Document any external network calls
- Prefer local models even if slower

## Mandatory Quality Gates (CRITICAL)

### Pre-Commit Requirements (Enforced on EVERY Commit)

**MUST PASS before commit**:
1. ✅ **Black formatting** (line-length=100)
2. ✅ **Ruff linting** (all errors fixed)
3. ✅ **MyPy type checking** (strict mode)
4. ✅ **Import sorting** (isort, black-compatible)
5. ✅ **Gitleaks** (no secrets detected)
6. ✅ **Fast unit tests** (non-slow tests pass)
7. ✅ **Docstring check** (all public functions documented)

**Setup** (Required first step):
```bash
# Install pre-commit hooks
pre-commit install

# Verify hooks work
pre-commit run --all-files
```

**Auto-fix common issues**:
```bash
# Format and fix linting
black --line-length=100 src/ tests/
ruff check --fix src/ tests/
isort --profile=black --line-length=100 src/ tests/
```

**NEVER**:
- Commit without running pre-commit hooks
- Use `--no-verify` to bypass hooks
- Ignore type errors ("I'll fix it later")
- Skip writing tests ("this is just a prototype")

### Test Coverage Requirements (CRITICAL)

**Minimum Coverage**: 80% line coverage for ALL modules

**Per-Phase Requirements**:
- Phase 1 (Extraction & Indexing): 80%+ coverage before Phase 2
- Phase 2 (Search): 80%+ coverage before Phase 3
- Phase 3 (Blocklist): 90%+ coverage (safety-critical)
- Phase 4+ (Generation): 80%+ coverage per phase

**Run tests before EVERY commit**:
```bash
# Fast tests (pre-commit)
pytest tests/unit/ -m "not slow" -q

# Full validation (before PR)
./validate-bloginator.sh

# Check coverage
pytest tests/ --cov=src --cov-report=term-missing
coverage report --fail-under=80
```

**Test Organization**:
- 60% unit tests (fast, isolated, comprehensive)
- 30% integration tests (component interactions)
- 10% E2E tests (full workflows)

**NEVER**:
- Merge code with <80% coverage
- Skip writing tests because "it's simple code"
- Write tests that don't actually test anything
- Use `pytest.skip` without explicit justification

### Cost Control Requirements (Cloud Mode ONLY)

**MANDATORY Cost Protections**:
1. ✅ **Token counting** before every LLM call
2. ✅ **Cost estimation** displayed to user
3. ✅ **Session cost tracking** with running total
4. ✅ **Hard limits** (default: $5/session, configurable)
5. ✅ **User confirmation** for operations >$1
6. ✅ **Test cost caps** (<$1 per full test run)

**Implementation Requirements**:
```python
# REQUIRED pattern for all LLM calls
def generate_content(prompt, llm, cost_controller):
    # 1. Estimate cost
    estimate = cost_controller.estimate_cost(prompt, max_tokens)

    # 2. Check limit
    if not cost_controller.check_and_track(prompt, max_tokens):
        raise CostLimitExceeded(f"Would exceed ${cost_controller.limit_usd} limit")

    # 3. Generate
    result = llm.generate(prompt, max_tokens)

    # 4. Track actual cost
    cost_controller.record_actual_cost(result['usage'])

    return result
```

**Display costs to user**:
```
⚙️  Generating outline...
   Input tokens: 1,247
   Output tokens: ~800 (estimated)
   Estimated cost: $0.08
   Session total: $0.23 / $5.00
   Proceed? [Y/n]
```

**NEVER**:
- Make LLM API calls without cost estimation
- Hide costs from user
- Disable cost limits to "make it work"
- Use expensive models (opus, gpt-4) without explicit user request
- Run cloud tests without cost caps

### Linting & Type Safety (CRITICAL)

**Linting (Ruff)**:
```bash
# Check linting
ruff check src/ tests/

# Auto-fix
ruff check --fix src/ tests/
```

**Required Ruff Configuration** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]
ignore = []

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
```

**Type Checking (MyPy)**:
```bash
# Check types
mypy src/ --strict --ignore-missing-imports
```

**Required MyPy Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
ignore_missing_imports = true
```

**NEVER**:
- Ignore type errors with `# type: ignore` without comment explaining why
- Use `Any` type without justification
- Skip type hints on new functions
- Disable strict mode

### Build & Validation Script (MANDATORY)

**Run before EVERY pull request**:
```bash
./validate-bloginator.sh
```

**What it checks**:
1. ✅ Code formatting (black)
2. ✅ Linting (ruff)
3. ✅ Type checking (mypy)
4. ✅ Import sorting (isort)
5. ✅ Security scanning (gitleaks)
6. ✅ Unit tests (all)
7. ✅ Coverage check (≥80%)
8. ✅ Docstring validation

**Exit codes**:
- `0`: All checks passed ✅
- `1`: One or more checks failed ❌

**NEVER**:
- Skip validation before PR
- Merge PRs with failing validation
- Disable validation checks
- Use `--skip-slow` in CI/CD (only for local development)

## Banned Activities

### 1. NEVER

**Content Generation**:
- Generate content without corpus grounding
- Skip blocklist validation to "fix" generation errors
- Invent examples or facts not in corpus
- Blend multiple voices without attribution

**System Behavior**:
- Rewrite working RAG pipeline just to make it "cleaner"
- Change prompt templates without A/B testing
- Add cloud APIs without explicit permission
- Remove safety checks to improve performance

**Code Organization**:
- Split files without user request
- Create new abstractions for "future extensibility"
- Add type hints or documentation unless specifically asked
- Suggest improvements to code that passes tests

**Quality & Testing**:
- Commit without pre-commit hooks passing
- Merge code with <80% test coverage
- Skip writing tests for new code
- Make LLM calls without cost tracking (cloud mode)
- Ignore linting or type errors

### 2. ALWAYS

**Testing & Validation**:
- Run `./validate-bloginator.sh` before every PR
- Write tests for all new code (80%+ coverage)
- Test with real corpus data (not toy examples)
- Validate blocklist enforcement in all code paths
- Verify voice similarity scores meet thresholds
- Track and display costs (cloud mode)

**Code Quality**:
- Format code with Black (line-length=100)
- Fix all Ruff linting errors
- Pass MyPy type checking (strict mode)
- Sort imports with isort
- Document all public functions (Google-style docstrings)
- Run pre-commit hooks before committing

**User Communication**:
- Make minimal, focused changes
- Verify changes work before proceeding
- Ask user before making architectural changes
- Respect existing code organization

**Privacy & Safety**:
- Enforce blocklist on all generated content
- Keep processing local by default
- Log blocklist violations for user review
- Never bypass safety checks
- Estimate costs before cloud LLM calls
- Respect session cost limits

## Bloginator Anti-Patterns to Avoid

### Anti-Pattern 1: Over-Optimizing Voice Preservation

**Bad**:
```python
# Creating complex voice analysis with 15 metrics
class VoicePreservationAnalyzer:
    def analyze_lexical_diversity(self): ...
    def analyze_syntactic_complexity(self): ...
    def analyze_semantic_coherence(self): ...
    # ... 12 more methods
```

**Good**:
```python
# Start with simple embedding similarity
def voice_similarity_score(generated: str, corpus_samples: list[str]) -> float:
    """Compare generated text embedding to corpus embeddings."""
    # Simple, testable, works
```

**Why**: Start simple. Add complexity only when simple approach fails.

### Anti-Pattern 2: Premature Template Abstraction

**Bad**:
```python
# Creating complex template engine before any templates exist
class TemplateEngine:
    def render(self, template: Template, context: Context) -> str: ...
    def compile(self, source: str) -> Template: ...
    def validate(self, template: Template) -> bool: ...
```

**Good**:
```python
# Start with f-strings and simple prompt templates
def create_outline_prompt(keywords: list[str], thesis: str) -> str:
    return f"""Based on these keywords: {', '.join(keywords)}
    And this thesis: {thesis}
    Create an outline..."""
```

**Why**: Build 3-5 templates first, THEN abstract if patterns emerge.

### Anti-Pattern 3: Ignoring Corpus Coverage Warnings

**Bad**:
```python
# Generate anyway, even with low coverage
def generate_draft(outline):
    chunks = search_corpus(outline)
    # chunks might be empty or irrelevant
    return llm.generate(chunks)  # ❌ No validation
```

**Good**:
```python
# Validate and warn user
def generate_draft(outline):
    chunks = search_corpus(outline)
    coverage = calculate_coverage(chunks, outline)
    if coverage < 0.3:
        warn_user(f"Low corpus coverage: {coverage:.0%}")
        if not user_confirms_anyway():
            return None
    return llm.generate(chunks)
```

**Why**: User needs to know when system is extrapolating beyond corpus.

### Anti-Pattern 4: Blocking on Perfect Blocklist

**Bad**:
```python
# Trying to build perfect proprietary term detection
class ProprietaryTermDetector:
    def use_nlp_entity_recognition(self): ...
    def use_fuzzy_matching_with_ml(self): ...
    def use_context_aware_scoring(self): ...
```

**Good**:
```python
# Start with exact match and regex
def check_blocklist(text: str, blocklist: list[str]) -> list[str]:
    violations = []
    for term in blocklist:
        if term.lower() in text.lower():
            violations.append(term)
    return violations
```

**Why**: Simple exact matching catches 95% of issues. Add complexity only if needed.

## Success Metrics for Code Quality

1. **Tests Pass**: All tests green before and after changes
2. **Voice Similarity**: Generated content scores >0.7 vs. corpus
3. **Blocklist Enforcement**: 100% catch rate for exact matches
4. **Performance**:
   - Index 500 docs in <30 min
   - Search in <3 sec
   - Generate draft in <5 min
5. **Privacy**: Zero unintentional external API calls

## When to Ask User Before Proceeding

1. **Architectural Changes**: Switching vector stores, LLM providers, embedding models
2. **Feature Additions**: New document types, export formats, UI components
3. **Performance Tradeoffs**: Faster but less accurate, vs. slower but better quality
4. **Privacy Decisions**: Adding cloud LLM option, external API integrations
5. **Blocklist Behavior**: How to handle near-matches, partial matches, context-dependent terms

## Emergency Brake: When to Stop and Seek Help

**STOP and ask user if**:
1. Blocklist is being violated repeatedly (legal risk)
2. Generated content consistently lacks voice similarity (core value prop broken)
3. Performance degrades below success metrics (30min+ indexing, 10sec+ search)
4. External API calls are happening without user awareness (privacy violation)
5. Tests fail after changes and you can't quickly fix (don't dig deeper hole)

---

**Remember**: Bloginator's value is authentic voice preservation and proprietary content protection. Fast, working code that achieves these goals beats elegant, complex code that doesn't.

**Pragmatic Minimalism**: Make the smallest change that solves the real problem. Test it. Ship it. Iterate.
