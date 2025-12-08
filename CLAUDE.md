# Claude AI Agent Guidelines for Bloginator

This document defines coding conventions and quality standards that MUST be followed
without exception for all work on this repository.

## ⛔ CRITICAL: WHEN STUCK, ASK FOR PERPLEXITY HELP ⛔

**The moment you get blocked or find yourself going in circles, STOP immediately.**

Do NOT continue trying random approaches. Instead:
1. **Generate a detailed Perplexity.ai prompt** for the user to run
2. Include: what you've tried, why it failed, specific technical details, environment info
3. **Wait for the user to return with Perplexity's response** before continuing
4. Fresh external research often unblocks problems that training data cannot solve

This is essential because:
- Your training data may be outdated or incomplete
- Perplexity has access to current documentation and community solutions
- The user can quickly get targeted answers for macOS/API-specific issues
- It prevents wasted time on dead-end approaches

## ⚠️ TERMINAL OUTPUT CAPTURE ISSUES ⚠️

After spawning many terminal sessions (60+), VS Code terminal output capture can fail.
Commands execute successfully but programmatic reads return empty.

**Workaround: Use file-based output instead of terminal capture:**
```bash
# Instead of reading terminal output directly:
python3 script.py > /tmp/output.txt 2>&1
# Then read /tmp/output.txt via the view tool
```

**Best practices:**
- Limit concurrent terminals to 3-5 sessions
- Use file redirection for any output you need to parse
- If terminal capture fails, dispose and recreate the terminal
- Consider `terminal.integrated.enablePersistentSessions: false` in VS Code settings

## ⛔⛔⛔ CRITICAL: NEVER BYPASS THE CORPUS ⛔⛔⛔

**THIS IS THE MOST IMPORTANT RULE IN THIS DOCUMENT.**
**VIOLATION OF THIS RULE IS A COMPLETE AND UTTER FAILURE LEADING TO UNTRUSTWORTHY AI SLOP.**

When generating blog content, you MUST use the bloginator pipeline with corpus search.
NEVER write blog content directly from your training data. The entire purpose of this project is to generate from corpus in the author's voice.

### Why This Matters

The ENTIRE PURPOSE of bloginator is to generate content that:
1. Reflects the user's documented knowledge in the corpus
2. Matches the user's writing voice (voice scoring)
3. Uses the user's specific terminology and examples
4. Is grounded in RAG search results from the corpus

Content generated from your training data is USELESS because:
- It doesn't reflect the user's actual practices
- It doesn't match the user's voice
- It's generic "industry standard" content
- It defeats the entire purpose of this project

### ⛔ NEVER CREATE HARDCODED RESPONSE SCRIPTS ⛔

**DO NOT create scripts like `tmp/batch_responses.py` with hardcoded content.**

This is the WORST possible failure mode because:
1. It looks like it works (files get created, drafts get generated)
2. But the content is FABRICATED from training data, not corpus
3. The user cannot distinguish fake content from real corpus synthesis
4. It defeats the ENTIRE PURPOSE of this project

**If you find yourself writing a script with hardcoded response content, STOP.**
That content should come from READING THE REQUEST FILES and SYNTHESIZING FROM THE
CORPUS CONTENT inside them.

### How to Generate Blog Content Correctly

**ALWAYS use one of these approaches:**

1. **Interactive mode** (user provides LLM responses):
   ```bash
   BLOGINATOR_LLM_MOCK=interactive bloginator outline --index .bloginator/chroma \
       --title "Topic Title" --keywords "keyword1,keyword2,keyword3" -o outline.json
   BLOGINATOR_LLM_MOCK=interactive bloginator draft --index .bloginator/chroma \
       --outline outline.json -o draft.md
   ```

2. **Assistant mode** (Claude acts as LLM backend):
   ```bash
   BLOGINATOR_LLM_MOCK=assistant bloginator outline --index .bloginator/chroma \
       --title "Topic Title" --keywords "keyword1,keyword2" -o outline.json
   # Then read requests from .bloginator/llm_requests/
   # Write responses to .bloginator/llm_responses/
   # Responses MUST be based on corpus search results in the request
   ```

### How to Act as the LLM Backend (Option C - The Correct Way)

When using assistant mode, Claude must:

1. **Read each request file** in `.bloginator/llm_requests/request_NNNN.json`
2. **Extract the source material** from the `prompt` field (look for `[Source 1]`, `[Source 2]`, etc.)
3. **Synthesize content** from ONLY those sources using `prompts/corpus-synthesis-llm.md` guidelines
4. **Write response files** to `.bloginator/llm_responses/response_NNNN.json`

**Response file format:**
```json
{
  "content": "The synthesized prose from corpus sources...",
  "prompt_tokens": 1500,
  "completion_tokens": 300,
  "finish_reason": "stop"
}
```

**CRITICAL: The `content` field must contain prose synthesized from the [Source N] sections
in the request's prompt. If you write content that doesn't trace to those sources,
you have failed.**

**NEVER do this:**
- Write markdown files directly with `save-file` for blog content
- Generate content from your training data
- Skip the corpus search step
- Take shortcuts for speed

### If You're Tempted to Shortcut

STOP. Ask the user how they want to proceed. Options:
- Wait for interactive mode (slower but correct)
- Use assistant mode (you act as LLM, reading corpus results)
- Batch process with a script

Speed is NOT worth generating useless content.

## CRITICAL: Repository Cleanliness

### Temporary Files Policy

- ALL temporary/experimental scripts go in `tmp/` directory (git-ignored)
- ALL blog generation outputs go in `blogs/` directory (git-ignored)
- ALL prompt experiments go in `prompts/experimentation/` (git-ignored)
- ALL context handoff prompts go in `prompts/` (e.g., `prompts/finish-refactoring-options-b-c.md`)
- NEVER create shell scripts or markdown files in the repository root
- Exception: Only permanent, maintained scripts/docs belong in root

### Markdown Documentation Policy

- Keep all working markdown files in `docs/` updated as you work
- Create index files (e.g., `docs/IMPLEMENTATION_PLAN_TOPIC_DRIFT_FIX.md`) that reference other docs
- Write comprehensive prompts to `prompts/` for context handoffs
- Reference prompt files instead of pasting huge inline content
- Each prompt should be 200-400 lines max, focused on execution steps

## CRITICAL: LLM Mode Configuration

### Available LLM Modes

The `BLOGINATOR_LLM_MOCK` environment variable controls LLM behavior:

| Value | Client | Use Case |
|-------|--------|----------|
| `true` | `MockLLMClient` | Unit tests - returns canned responses |
| `interactive` | `InteractiveLLMClient` | Human-in-the-loop via terminal prompts |
| `assistant` | `AssistantLLMClient` | File-based communication for AI agents |
| *(unset)* | Real LLM client | Production use with Ollama/OpenAI/Anthropic |

**Note**: `BLOGINATOR_LLM_MOCK` takes precedence over `BLOGINATOR_LLM_PROVIDER`.

### Assistant Mode (Claude as the LLM)

When `BLOGINATOR_LLM_MOCK=assistant`:
1. Bloginator writes requests to `.bloginator/llm_requests/request_NNNN.json`
2. Bloginator waits for `.bloginator/llm_responses/response_NNNN.json`
3. Claude (or another AI agent) reads requests and writes responses

**CRITICAL: Use the synthesis prompt at `prompts/corpus-synthesis-llm.md`** when generating responses. This prompt defines:
- How to synthesize corpus results into cohesive prose
- Quality markers and anti-patterns
- Output length guidelines
- Success metrics

To act as the LLM backend:
1. Set `BLOGINATOR_LLM_MOCK=assistant` in `.env`
2. Run a bloginator command (e.g., `bloginator outline --index .bloginator/chroma --title "Topic" --keywords "key1,key2" -o outline.json`)
3. Monitor `.bloginator/llm_requests/` for new request files
4. Read the request, apply `prompts/corpus-synthesis-llm.md` guidelines, write to `.bloginator/llm_responses/`

### Demo Script

`scripts/respond-to-llm-requests.py` provides **template-based** responses for demos.
It does NOT use any LLM - just hardcoded content for specific topics.

### No External LLM Required

- The user does NOT have external LLM API keys configured
- For testing, use `BLOGINATOR_LLM_MOCK=true` (canned responses)
- For real generation, Claude can act as the LLM via assistant mode
- NEVER switch to Ollama or other LLMs without explicit user request

## CRITICAL: Documentation Standards

### No Hyperbolic Language

NEVER use sensational or marketing language in documentation:

- **Banned phrases**: "production-grade", "world-class", "game-changing", "revolutionary",
  "cutting-edge", "unparalleled", "best-in-class", "enterprise-ready"
- **Instead**: Use factual, specific descriptions of what the code does
- **Example**: "Handles 1000 documents/minute" not "blazing fast performance"

## Mandatory Coding Standards

### Python Style Guide

All Python code MUST comply with `docs/PYTHON_STYLE_GUIDE.md`. Key requirements:

- **Line length**: 100 characters maximum (enforced by Black/Ruff)
- **Type annotations**: Required on all function parameters, return values, and class attributes
- **Docstrings**: Google style, required for all public modules, classes, and functions
- **Function length**: Target ≤50 lines, maximum 100 lines
- **Parameters**: ≤5 per function, use dataclass/dict for more
- **Import order**: stdlib → third-party → local (enforced by isort)
- **Max file length**: 300 lines maximum. Strive for ~250 lines

## Mandatory Quality Gates

All code MUST pass these checks before commit or PR:

```bash
# Format check (automatic in CI)
ruff check src/bloginator tests
black --check src/bloginator tests
isort --check-only src/bloginator tests

# Type checking
mypy src/bloginator/models src/bloginator/extraction src/bloginator/search \
     src/bloginator/safety src/bloginator/export src/bloginator/services \
     src/bloginator/indexing/indexer.py src/bloginator/generation \
     src/bloginator/utils/parallel.py

# Docstring checking
pydocstyle src/bloginator

# Tests with coverage
pytest --cov=src/bloginator --cov-fail-under=70
```

### CI Workflow Requirements

1. **Lint and type check** - Must pass Ruff, pydocstyle, and mypy
2. **Tests** - Must pass on Python 3.10, 3.11, and 3.12 with ≥70% coverage
3. **Security scanning** - Bandit, pip-audit, and Safety checks run (non-blocking)
4. **Codecov** - Coverage reports uploaded to Codecov

## Development Workflow

### Before Every Commit

1. Run quality gate script: `./scripts/run-fast-quality-gate.sh`
2. Verify all tests pass: `pytest tests/unit --no-cov`
3. Fix any linting/type errors before committing

### Before Every Push

1. Run full test suite: `pytest --cov=src/bloginator`
2. Verify coverage meets threshold (≥70%)
3. Ensure CI will pass by running all quality checks locally

## Code Patterns

### Error Handling

```python
# Good - descriptive with context
raise ValueError(f"Invalid file path: {path!r} (must exist)")

# Bad - vague
raise ValueError("invalid path")
```

### Type Annotations

```python
# Required pattern
def process_document(
    file_path: Path,
    *,
    include_metadata: bool = True,
    max_chunks: int = 100,
) -> list[DocumentChunk]:
    """Process a document into chunks."""
    ...
```

### Testing

```python
class TestFeatureName:
    """Tests for FeatureName functionality."""

    def test_specific_behavior(self, tmp_path: Path) -> None:
        """Specific behavior should produce expected result."""
        # Arrange
        ...
        # Act
        ...
        # Assert
        ...
```

## Project Structure

```text
src/bloginator/
  cli/           # Click CLI commands
  export/        # Document exporters (HTML, Markdown, DOCX, PDF)
  extraction/    # Document chunking and metadata extraction
  generation/    # LLM clients and content generation
  indexing/      # ChromaDB vector indexing
  models/        # Pydantic models and dataclasses
  monitoring/    # Logging and metrics
  quality/       # Slop detection and quality assurance
  safety/        # Blocklist and content filtering
  search/        # Semantic search
  services/      # History and template management
tests/
  unit/          # Unit tests (fast, isolated)
  integration/   # Integration tests
  e2e/           # End-to-end workflow tests
  benchmarks/    # Performance tests
docs/
  *.md           # Documentation files
```

## Prohibited Patterns

1. **No untyped functions** - Every function must have type annotations
2. **No missing docstrings** - Public APIs must be documented
3. **No ignoring mypy errors** - Fix the issue, don't add `# type: ignore`
4. **No tests without assertions** - Every test must verify behavior
5. **No coverage exclusions without justification** - Document why `# pragma: no cover`

## Running Quality Checks

```bash
# Quick local check
source venv/bin/activate
ruff check src/bloginator tests
mypy src/bloginator/models src/bloginator/generation
pytest tests/unit -x --no-cov

# Full CI simulation
pytest --cov=src/bloginator --cov-report=term-missing
```

## Coverage Requirements

- **Minimum overall**: 70% (enforced in CI)
- **Target for new code**: 80%+
- **Critical paths**: 90%+ recommended

Current coverage: ~71% (as of 2025-12-07)

## ⚠️ BATCH MODE BLOG GENERATION ⚠️

When generating blogs using batch mode with assistant LLM, follow this exact procedure:

### Step 1: Count Sections FIRST

Before generating ANY responses, count the total sections in the outline:

```bash
cat blogs/OUTLINE.json | python3 -c "
import sys,json
d=json.load(sys.stdin)
sections=d.get('sections',[])
total=len(sections)
subs=sum(len(s.get('subsections',[])) for s in sections)
print(f'Total requests needed: {total + subs}')
"
```

### Step 2: Generate Matching Response Count

The response script MUST generate exactly as many responses as there are sections.
Do NOT hardcode response counts. Each outline is different:
- SDE ladder: 17 sections
- SRE ladder: 18 sections
- Manager ladder: 19 sections
- Hiring managers: 15 sections

### Step 3: Use Batch Mode Correctly

```bash
# Clear previous requests/responses
rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*

# Start draft generation in background
BLOGINATOR_LLM_MOCK=assistant bloginator draft \
    --index .bloginator/chroma \
    --outline blogs/OUTLINE.json \
    -o blogs/OUTPUT.md \
    --batch --batch-timeout 120 2>&1 &

# Wait for requests to be generated
sleep 5

# Provide responses (must match request count!)
python tmp/batch_responses.py

# Wait for completion
wait
```

### Step 4: Verify Output

After generation, verify:
1. File exists and has content
2. Tables are present (for career ladders)
3. Citation metrics are reasonable

```bash
# Check file size and table count
ls -la blogs/career-ladders/OUTPUT.md
grep -c "^|" blogs/career-ladders/OUTPUT.md
```

### Common Mistakes to Avoid

1. **Hardcoding 17 responses** - Different outlines have different section counts
2. **Not waiting for requests** - Must `sleep 5` before writing responses
3. **Running commands serially** - Use `&` and `wait` for background processes
4. **Not clearing old requests** - Always `rm -rf .bloginator/llm_requests/*` first
5. **Timeout too short** - Use `--batch-timeout 120` minimum for testing

## ⚠️ EFFICIENCY: AVOID REPETITIVE DEBUGGING ⚠️

### Signs You're Going in Circles

- Running the same command 3+ times expecting different results
- Waiting for output that never comes
- Terminal capture returning empty strings repeatedly

### When This Happens

1. **STOP immediately** - Don't run the same thing again
2. **Diagnose the root cause** - Check file existence, process status, error logs
3. **Use file redirection** - `command > /tmp/out.txt 2>&1` then `view /tmp/out.txt`
4. **Ask for help** - Generate a Perplexity prompt if truly stuck

### Pre-Flight Checklist Before Blog Generation

Before starting ANY blog generation task:

- [ ] Verify outline exists: `ls -la blogs/*.json`
- [ ] Count sections in outline (see Step 1 above)
- [ ] Verify index exists: `ls -la .bloginator/chroma`
- [ ] Clear old requests: `rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*`
- [ ] Verify response script matches section count
