# Phase 2: Strict Typing Enablement Roadmap

**Status**: In Progress
**Goal**: Enable strict type checking across all production modules

## Completed (2 modules)

✅ `bloginator.utils.parallel` - Already strict compliant
✅ `bloginator.generation.llm_custom` - Already strict compliant

## Ready for Enablement (Estimated 2-3 hours)

### High Priority (2-3 modules)
- `bloginator.cli.extract_utils` - Extraction utilities
- `bloginator.generation._llm_mock_responses` - Mock responses

### Medium Priority (3-4 modules)
- `bloginator.timeout_config` - Configuration management
- `bloginator.monitoring.logger` - Logging setup

### Lower Priority (UI/Web - can skip for now)
- `bloginator.ui.*` - Streamlit UI (optional, complex)
- `bloginator.cli.serve` - Web server (optional)

## LLM Provider Modules (Special Case)

These require external API knowledge:
- `bloginator.generation.llm_ollama` - Ollama client
- `bloginator.generation.llm_openai` - OpenAI client
- `bloginator.generation.llm_anthropic` - Anthropic client

**Decision**: Keep relaxed until we have complete API type stubs

## Process for Each Module

1. **Check current state**:
   ```bash
   mypy src/bloginator/module_name.py --show-error-codes
   ```

2. **Fix any errors** (shouldn't be many):
   ```bash
   # Review errors
   # Fix them in the source
   # Re-run mypy
   ```

3. **Update pyproject.toml**:
   - Remove the module from type exclusions
   - Or update the override to strict=true

4. **Verify passes**:
   ```bash
   mypy src/bloginator/module_name.py
   pytest tests/ --cov=src/bloginator -q
   ```

5. **Commit**:
   ```bash
   git commit -m "refactor(module): enable strict type checking"
   ```

## Current State

**Modules with relaxed typing**: 10
- `tests.*`
- `bloginator.ui.*` (8 modules)
- `bloginator.cli.serve`
- `bloginator.cli.error_reporting`
- `bloginator.cli.search`
- `bloginator.generation.llm_mock`
- `bloginator.cli.extract_utils`
- `bloginator.generation.llm_ollama`

**Modules with strict typing**: 148 (implied)

## Success Criteria

- [ ] 8+ modules enabled with strict checking
- [ ] No new type: ignore comments
- [ ] All tests pass with --cov
- [ ] CI passes

## Notes

- Don't rush this. Do 1-2 modules per session.
- Fixing type issues often reveals real bugs.
- Some complexity is acceptable if it helps type checking.
- UI modules can stay relaxed (optional dependency).
