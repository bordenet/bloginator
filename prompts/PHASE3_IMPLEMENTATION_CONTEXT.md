# Phase 3 Implementation Context - December 29, 2025

## Current State

**Phases 1 & 2**: ✅ COMPLETED and pushed to origin main
**Phase 3**: 🔄 READY TO START

**Commits pushed**:
- `f4cd191` - feat: optimize LLM prompts for brevity and add comprehensive tests
- `645c00d` - fix: use MockLLMClient fallback and recommend Opus for review

---

## What Was Completed

### Phase 1: Quick Fixes (26% Token Reduction)

**Problem**: Blog posts were "HIGHLY verbose, often repetitive" with 0/30 success rate.

**Changes**:
1. **Fixed contradictory instructions** in `prompts/outline/base.yaml`
   - Removed conflicting `{{num_sections}}` parameter (line 100)
   - Kept single instruction: "Create EXACTLY 5-7 top-level sections"
   - Updated `OutlinePromptBuilder.build_user_prompt()` signature (removed num_sections param)
   - Updated `OutlineGenerator.generate()` to not pass num_sections

2. **Standardized length targets** in `prompts/draft/base.yaml`
   - Removed conflicting `{{max_words}}` parameter
   - Single target: "Target 60-80 words TOTAL"
   - Clear fail: "FAIL THRESHOLD: If you write more than 100 words, you have FAILED"

3. **Reduced corpus context bloat**:
   - Outline: 8 results → 3 results, 500 chars → 200 chars (-60% tokens)
   - Draft: 5 sources → 3 sources (-40% tokens)
   - Voice samples: 5 → 3 samples, 200 → 150 words (-40% tokens)
   - Files: `_outline_prompt_builder.py`, `draft_generator.py`, `_section_refiner.py`

4. **Created shared rules**: `prompts/common/brevity-rules.yaml`
   - 714 words of consolidated quality rules
   - Not yet used (future refactoring to use Jinja2 includes)

**Token Budget Impact**:
| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Outline | ~1,500 | ~950 | -37% |
| Draft/section | ~1,950 | ~1,540 | -21% |
| **Total/blog** | **~15,900** | **~11,730** | **-26%** |

### Phase 2: Test Suite Implementation

**Created test infrastructure**:
```
tests/llm_prompts/
├── conftest.py              # Claude Sonnet 4.5 + MockLLMClient fallback
├── test_outline_prompt.py   # 6 outline tests
└── test_draft_prompt.py     # 6 draft tests
```

**Key implementation detail**: Tests use MockLLMClient when `ANTHROPIC_API_KEY` not set (tests always run, never skip).

**Outline tests** (6):
1. `test_section_count_compliance` - 5-7 sections
2. `test_minimal_subsections` - <1.5 subsections/section
3. `test_keyword_matching` - ≥70% sections match keywords
4. `test_corpus_grounding` - ERROR on off-topic corpus
5. `test_markdown_structure` - ## headings present
6. `test_no_ai_slop` - No em-dashes, flowery language

**Draft tests** (6):
1. `test_word_count_compliance` - ≤100 words (target 60-80)
2. `test_paragraph_count` - 1-2 paragraphs max
3. `test_no_repeated_concepts` - Concepts stated once
4. `test_topic_validation` - ERROR on off-topic sources
5. `test_table_for_structured_data` - Tables for comparisons
6. `test_no_bullet_lists` - No bullets (prose/tables only)

**Quality Review Feature Added**:
- Created `src/bloginator/generation/quality_reviewer.py`
- Created `prompts/review/base.yaml`
- Integrated into draft CLI with `--skip-quality-review` flag
- **IMPORTANT**: Should use Claude Opus for review (noted in code comments and docs)

---

## Phase 3: What Needs to Be Done

### Goal
Split outline and quality review into focused multi-call workflows for better quality.

**User priority**: "I don't care about LLM round-trips, I care about quality of output/results"

### Task 1: Refactor Outline Generation (2 calls)

**Current**: 1 call (950 tokens)
**Target**: 2 calls (500 + 800 = 1,300 tokens)

**Call 1: Topic Validation** (~500 tokens)
- **Purpose**: Early failure on off-topic corpus
- **Input**: title, keywords, corpus preview (200 chars × 3)
- **Prompt**: "Does corpus content match topic? Return VALID or ERROR"
- **Output**: "VALID" or "ERROR: Topic mismatch - corpus discusses X, topic is Y"
- **File to create**: `prompts/outline/topic-validation.yaml`

**Call 2: Outline Generation** (~800 tokens)
- **Purpose**: Generate outline structure (only if validation passed)
- **Input**: title, keywords, validated corpus context
- **Prompt**: Current outline prompt (simplified, no topic validation section)
- **Output**: 5-7 section outline
- **File to modify**: `prompts/outline/base.yaml` (remove topic validation section)

**Implementation steps**:
1. Create `prompts/outline/topic-validation.yaml`:
   - System prompt: "You validate whether corpus content matches requested topics"
   - User prompt: "Topic: {{title}}, Keywords: {{keywords}}, Corpus: {{corpus_preview}}"
   - Expected output: "VALID" or "ERROR: ..."

2. Modify `OutlineGenerator.generate()`:
   - Add `_validate_topic()` method (calls validation prompt)
   - If validation returns ERROR, return outline with validation_notes set
   - Only proceed to outline generation if VALID

3. Simplify `prompts/outline/base.yaml`:
   - Remove "TOPIC VALIDATION (HIGHEST PRIORITY - Execute FIRST)" section (lines 47-62)
   - Validation now handled by separate call

### Task 2: Refactor Quality Review (2 calls)

**Current**: 1 call (4,000 tokens)
**Target**: 2 calls (1,500 + 2,000 = 3,500 tokens)

**Call 1: Structural Analysis** (~1,500 tokens)
- **Purpose**: Identify specific issues to fix
- **Input**: draft content (full markdown)
- **Prompt**: "Analyze for: word count, bullets, redundancy, AI slop. Return JSON list of issues."
- **Output**: JSON like `{"issues": [{"type": "word_count", "severity": "high", "details": "Section X has 150 words, target 60-80"}]}`
- **File to create**: `prompts/review/structural-analysis.yaml`

**Call 2: Content Revision** (~2,000 tokens)
- **Purpose**: Apply targeted fixes based on identified issues
- **Input**: draft content + issue list
- **Prompt**: "Fix these specific issues: [list]. Return revised markdown."
- **Output**: Revised blog content
- **File to modify**: `prompts/review/base.yaml` (focus on revision, not analysis)
- **CRITICAL**: Use Claude Opus for this call (highest quality)

**Implementation steps**:
1. Create `prompts/review/structural-analysis.yaml`:
   - System prompt: "You are a strict editor analyzing blog content for issues"
   - User prompt: "Analyze this draft: {{draft_content}}"
   - Expected output: JSON array of issues

2. Modify `QualityReviewer`:
   - Add `_analyze_structure()` method (calls analysis prompt)
   - If no issues found, skip revision (return original)
   - Add `_revise_content()` method (calls revision prompt with issue list)
   - Update `review_and_revise()` to orchestrate 2 calls

3. Update `prompts/review/base.yaml`:
   - Remove analysis instructions
   - Focus on: "Given these issues: {{issues}}, revise the content"

### Task 3: Implement Quality Review Tests (4 tests)

**File to create**: `tests/llm_prompts/test_quality_review_prompt.py`

**Tests**:
1. `test_word_count_reduction` - Validates 40-60% reduction from original
2. `test_redundancy_elimination` - Validates no repeated concepts across sections
3. `test_bullet_conversion` - Validates bullets converted to prose/tables
4. `test_ai_slop_removal` - Validates em-dashes, flowery language removed

**Test structure** (follow pattern from outline/draft tests):
```python
class TestQualityReviewPromptReduction:
    def test_word_count_reduction(self, claude_client, prompt_loader):
        # Create verbose draft with 500 words
        # Run through quality review
        # Assert revised content is 200-300 words (40-60% reduction)

class TestQualityReviewPromptQuality:
    def test_redundancy_elimination(self, claude_client, prompt_loader):
        # Create draft with repeated concepts
        # Run through quality review
        # Assert revised content has no repetition

    def test_bullet_conversion(self, claude_client, prompt_loader):
        # Create draft with PowerPoint bullets
        # Run through quality review
        # Assert revised content uses prose or tables

    def test_ai_slop_removal(self, claude_client, prompt_loader):
        # Create draft with em-dashes, "dive deep", etc.
        # Run through quality review
        # Assert revised content has no slop patterns
```

### Task 4: Run Full Test Suite and Validate

**Commands**:
```bash
# Run all LLM prompt tests (with or without API key)
pytest tests/llm_prompts/ -v

# Expected: 16 tests pass (6 outline + 6 draft + 4 quality review)
```

**Validation checklist**:
- [ ] All 16 tests pass with MockLLMClient (no API key)
- [ ] All 16 tests pass with Claude API (if key available)
- [ ] Token budget reduced or similar to before
- [ ] Quality metrics documented in test output
- [ ] No breaking changes to existing code

---

## Current Todo List

Phase 3 tasks:
1. [in_progress] Refactor outline into 2 calls (topic validation + generation)
2. [pending] Refactor quality review into 2 calls (analysis + revision)
3. [pending] Implement quality review tests (4 tests)
4. [pending] Run full test suite and validate improvements

---

## Important Technical Details

### Files Modified in Phases 1 & 2

**Prompts**:
- `prompts/outline/base.yaml` - Removed num_sections contradiction
- `prompts/draft/base.yaml` - Standardized length targets
- `prompts/corpus-synthesis-llm.md` - Updated length guidelines
- `prompts/review/base.yaml` - NEW: Quality review prompt
- `prompts/common/brevity-rules.yaml` - NEW: Shared rules (not yet used)

**Code**:
- `src/bloginator/generation/_outline_prompt_builder.py` - Reduced corpus context, removed num_sections
- `src/bloginator/generation/outline_generator.py` - Removed num_sections param
- `src/bloginator/generation/draft_generator.py` - Reduced sources 5→3
- `src/bloginator/generation/_section_refiner.py` - Reduced voice samples 5→3
- `src/bloginator/generation/quality_reviewer.py` - NEW: QualityReviewer class
- `src/bloginator/generation/_llm_mock_client.py` - Added quality review detection
- `src/bloginator/generation/_llm_mock_responses.py` - Added mock review responses
- `src/bloginator/cli/draft.py` - Integrated quality review, added --skip-quality-review flag

**Tests**:
- `tests/llm_prompts/conftest.py` - NEW: Claude client + fixtures (MockLLMClient fallback)
- `tests/llm_prompts/test_outline_prompt.py` - NEW: 6 outline tests
- `tests/llm_prompts/test_draft_prompt.py` - NEW: 6 draft tests

**Docs**:
- `docs/PROMPT_OPTIMIZATION_2025_12_29.md` - NEW: Complete documentation

### Key Design Decisions

1. **MockLLMClient fallback**: Tests use mock when no API key (never skip tests)
2. **Use Opus for review**: Quality review should use Claude Opus (highest quality)
3. **Backward compatible**: All changes maintain existing API signatures
4. **Quality over efficiency**: User doesn't care about round-trips, only quality
5. **Shared rules deferred**: Created `brevity-rules.yaml` but not yet using Jinja2 includes

### Code Patterns to Follow

**Adding new prompts**:
1. Create YAML in `prompts/` directory
2. Use Jinja2 templates for variable substitution
3. Include system_prompt and user_prompt_template sections
4. Add quality_criteria for self-documentation

**Adding prompt tests**:
1. Create test file in `tests/llm_prompts/`
2. Use `claude_client` fixture (auto-falls back to mock)
3. Organize into test classes by category
4. Use descriptive assertion messages with context

**Modifying LLM workflows**:
1. Keep `LLMClient` interface clean
2. Add orchestration logic in generator/reviewer classes
3. Log token usage and metrics
4. Return structured results, not raw strings

---

## Critical Constraints from CLAUDE.md

1. **NEVER bypass the corpus**: All blog content must come from RAG search
2. **Mock LLM correctly**: Assistant mode reads request files, synthesizes from sources
3. **No hardcoded responses**: Scripts must read corpus content from request files
4. **Repository cleanliness**: All temp files in `tmp/`, all outputs in `blogs/`
5. **Quality over speed**: "I don't care about LLM round-trips, I care about quality"

---

## Next Session Startup Commands

```bash
cd /Users/mattbordenet/GitHub/bloginator

# Verify current state
git log --oneline -5
git status

# Read context
cat prompts/PHASE3_IMPLEMENTATION_CONTEXT.md

# Start implementing
# 1. Create topic validation prompt
# 2. Modify OutlineGenerator for 2-call workflow
# 3. Create structural analysis prompt
# 4. Modify QualityReviewer for 2-call workflow
# 5. Implement quality review tests
# 6. Run full test suite
```

---

## Expected Outcomes (Phase 3 Complete)

**Token budget**:
- Outline: 950 → 1,300 tokens (+350, but better quality via topic validation)
- Draft: 10,780 tokens (no change)
- Review: 4,000 → 3,500 tokens (-500, can skip revision if clean)
- **Total**: 15,730 → 15,580 tokens (-150 tokens, +2 calls, better quality)

**Test coverage**:
- 16 tests total (6 outline + 6 draft + 4 quality review)
- All tests use MockLLMClient fallback
- Tests validate constraint compliance and quality

**Quality improvements**:
- Early topic validation prevents hallucination
- Focused prompts reduce confusion
- Structural analysis enables targeted fixes
- Can skip revision when clean (efficiency bonus)

**Documentation**:
- Updated `docs/PROMPT_OPTIMIZATION_2025_12_29.md`
- Test suite README explaining how to run tests
- Baseline metrics documented

---

## Reference Documentation

**In repo**:
- `CLAUDE.md` - Project instructions and constraints
- `docs/PROMPT_OPTIMIZATION_2025_12_29.md` - Complete Phase 1 & 2 docs
- `prompts/corpus-synthesis-llm.md` - Synthesis guidelines

**External (created during session)**:
- `/tmp/phase1-option-a-summary.md` - Detailed Phase 1 changes
- `/tmp/phase2-test-suite-summary.md` - Detailed Phase 2 implementation
- `/tmp/IMPLEMENTATION_COMPLETE_PHASES_1_2.md` - Combined summary
- `/tmp/llm-prompt-analysis.md` - Original analysis with 3 refactoring options

---

## Status: Ready for Phase 3 Implementation

All prerequisite work completed. All changes committed and pushed. Fresh context window ready.

**Start with**: Task 1 - Create topic validation prompt and refactor OutlineGenerator.
