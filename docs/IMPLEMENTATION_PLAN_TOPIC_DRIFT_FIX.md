# Implementation Plan: Topic Drift Fix

**Status**: Phase 1 Completed
**Created**: 2024-12-04
**Last Updated**: 2024-12-05
**Related**: ASSESSMENT_VECTORIZATION_AND_PROMPTS.md (archived)

---

## Problem Summary

All 7 test blogs generated content about dashboards/SLIs instead of requested topics (hiring, agile rituals, incidents). Root cause: weak corpus search + weak prompt validation = garbage-in/garbage-out.

**Critical Issues**:
1. Generic search queries return irrelevant content
2. LLM prompts trust corpus results without topic validation
3. Shallow corpus context (200 chars/result) provides minimal signal

---

## Phase 1: Critical Fixes (IMMEDIATE)

### 1.1 Add Topic Validation to Outline Prompt

**File**: `prompts/outline/base.yaml`
**Status**: ✅ Completed

**Changes**:
```yaml
# Add after line 31 (after existing CRITICAL CONSTRAINT section)

TOPIC VALIDATION (HIGHEST PRIORITY - Execute FIRST):
Before creating any outline, validate corpus relevance:

1. READ the corpus context carefully
2. CHECK if it actually discusses: {{title}} and {{keywords}}
3. REJECT if corpus is about a different topic:
   - Example: If corpus discusses "dashboards" but title is "Hiring Managers", REJECT
   - Example: If corpus discusses "SLIs" but keywords are "agile, stand-up", REJECT

4. If corpus context does NOT match the topic, respond with:
   "ERROR: Corpus search returned irrelevant content.
    Detected topics: [list topics you see in corpus]
    Requested topic: {{title}} ({{keywords}})
    Cannot create outline without relevant source material."

5. ONLY proceed if corpus context clearly relates to the requested topic.

MANDATORY KEYWORD ENFORCEMENT:
- Every main section title MUST contain at least one keyword from: {{keywords}}
- If you cannot justify a section using the keywords, do NOT include it
- Section descriptions must reference the title and keywords explicitly

EXAMPLES OF CORRECT BEHAVIOR:
✓ Title: "What Great Hiring Managers Do", Keywords: "recruiting, interviewing"
  → Sections: "Hiring Manager Responsibilities", "Interview Process Ownership"

✗ Title: "What Great Hiring Managers Do", Keywords: "recruiting, interviewing"
  → Sections: "Dashboard Design", "SLI Selection" (WRONG TOPIC - REJECT!)
```

**Testing**:
- Feed outline generator with intentionally mismatched corpus (dashboard content + hiring title)
- Verify it rejects instead of generating wrong content
- Verify it generates correctly when corpus matches topic

---

### 1.2 Improve Search Query Construction

**File**: `src/bloginator/generation/_outline_prompt_builder.py`
**Status**: ✅ Completed

**Current Code** (lines 11-33):
```python
def build_search_queries(title: str, keywords: list[str]) -> list[str]:
    return [
        title,  # Full title first
        f"{keywords[0]} {keywords[1]}" if len(keywords) > 1 else keywords[0],
        f"{keywords[0]} implementation" if keywords else "",
        f"{keywords[0]} best practices" if keywords else "",
        f"{' '.join(keywords[:2])} guide" if len(keywords) > 1 else "",
    ]
```

**New Code**:
```python
def build_search_queries(
    title: str,
    keywords: list[str],
    thesis: str = "",
) -> list[str]:
    """Build specific, contextualized search queries.

    Creates longer queries that provide better topic discrimination
    by including title, keywords, and thesis context.

    Args:
        title: Document title
        keywords: Topic keywords
        thesis: Optional thesis statement for additional context

    Returns:
        List of search queries with increasing specificity
    """
    queries = []

    # Query 1: Full title (most specific)
    queries.append(title)

    # Query 2: Title + first 2 keywords for context
    if len(keywords) >= 2:
        queries.append(f"{title} {keywords[0]} {keywords[1]}")

    # Query 3: Keywords with thesis context (if available)
    if thesis and len(keywords) >= 1:
        # Extract key phrases from thesis (first 50 chars)
        thesis_snippet = thesis[:50].strip()
        queries.append(f"{keywords[0]} {keywords[1] if len(keywords) > 1 else ''} {thesis_snippet}")

    # Query 4: Longer keyword combination for broader coverage
    if len(keywords) >= 3:
        queries.append(f"{keywords[0]} {keywords[1]} {keywords[2]}")
    elif len(keywords) >= 2:
        queries.append(f"{keywords[0]} {keywords[1]} practices")

    # Remove empty strings and deduplicate
    queries = [q.strip() for q in queries if q.strip()]
    return list(dict.fromkeys(queries))  # Preserve order, remove duplicates
```

**Update Call Site** (`src/bloginator/generation/outline_generator.py`):
- Pass `thesis` parameter to `build_search_queries()`
- Log generated queries for inspection

**Testing**:
- Verify longer, more specific queries are generated
- Check query deduplication works
- Validate thesis integration improves specificity

---

### 1.3 Increase Corpus Context Depth

**File**: `src/bloginator/generation/_outline_prompt_builder.py`
**Status**: ✅ Completed

**Current Code** (lines 36-56):
```python
def build_corpus_context(results: list[SearchResult]) -> str:
    if not results:
        return ""

    context = "Key topics found in corpus:\n\n"
    for i, result in enumerate(results[:5], 1):
        preview = result.content[:200].replace("\n", " ").strip()  # Only 200 chars!
        context += f"{i}. {preview}...\n\n"

    return context
```

**New Code**:
```python
def build_corpus_context(results: list[SearchResult]) -> str:
    """Build rich corpus context with metadata and longer previews.

    Provides LLM with sufficient context to understand corpus content
    and validate topic relevance. Includes similarity scores and source
    metadata to help LLM assess result quality.

    Args:
        results: Search results from corpus searcher

    Returns:
        Formatted corpus context string with metadata
    """
    if not results:
        return "No corpus material found for this topic."

    context_parts = ["CORPUS SEARCH RESULTS (validate topic match!):\n"]

    # Increase from 5 to 8 results for better coverage
    for i, result in enumerate(results[:8], 1):
        # Increase from 200 to 500 characters for better context
        preview = result.content[:500].replace("\n", " ").strip()

        # Add rich metadata
        similarity = f"{result.similarity_score:.3f}" if result.similarity_score else "N/A"
        source = result.metadata.get("filename", "unknown")

        context_parts.append(
            f"[{i}] Similarity: {similarity} | Source: {source}\n"
            f"{preview}...\n"
        )

    return "\n".join(context_parts)
```

**Impact**:
- Context increases from ~1000 chars (200×5) to ~4000 chars (500×8)
- LLM sees similarity scores to assess result quality
- Source filenames help LLM understand content provenance

**Testing**:
- Verify context format is readable
- Check LLM can use metadata effectively
- Validate increased context improves topic matching

---

### 1.4 Add Search Result Logging

**File**: `src/bloginator/generation/outline_generator.py`
**Status**: ✅ Completed

**Purpose**: Visibility into what corpus search returns so we can diagnose bad retrieval.

**Implementation**:
```python
# Add after search results are retrieved (around line 80-90)

import logging
logger = logging.getLogger(__name__)

# Log search query and results
logger.info(f"Search query: {search_query}")
logger.info(f"Retrieved {len(search_results)} results")

if search_results:
    # Log top 3 results with similarity scores
    for i, result in enumerate(search_results[:3], 1):
        preview = result.content[:100].replace("\n", " ")
        logger.info(
            f"  Result {i}: similarity={result.similarity_score:.3f}, "
            f"source={result.metadata.get('filename', 'unknown')}, "
            f"preview={preview}..."
        )
else:
    logger.warning("No corpus results found for query")
```

**Testing**:
- Run outline generation with `--verbose` or debug logging
- Verify search queries and results are logged
- Use logs to diagnose topic mismatch issues

---

### 1.5 Add Topic Validation to Draft Prompt

**File**: `prompts/draft/base.yaml`
**Status**: ✅ Completed

**Changes**:
```yaml
# Update system_prompt (line 27) to add topic validation

system_prompt: |
  You are a skilled technical writer creating authentic content.
  Write in a clear, professional voice based ONLY on the provided source material.

  CRITICAL TOPIC VALIDATION:
  - Before writing, verify source material relates to: {{title}}
  - If sources are about a DIFFERENT topic, state:
    "ERROR: Source material does not match section topic.
     Section: {{title}}
     Sources appear to be about: [describe actual source topics]
     Cannot generate content without relevant sources."
  - Only proceed if sources clearly relate to the section topic.

  {{classification_guidance}}.
  Write for {{audience_context}}.
  Do not invent facts or examples not present in the sources.
  Write naturally without explicitly citing sources in the text.

  # ... rest of existing prompt unchanged
```

**Testing**:
- Feed draft generator with mismatched sources
- Verify it rejects instead of generating off-topic content
- Test with correct sources to ensure normal generation works

---

## Phase 1 Testing Protocol

**Test Suite**: Create `tests/integration/test_topic_alignment.py`

**Test Cases**:
1. **test_outline_rejects_mismatched_corpus**
   - Setup: Mock corpus search to return dashboard content
   - Input: Outline request for "Hiring Managers" topic
   - Expected: Outline generator returns error/rejection message
   - Validates: Topic validation in outline prompt works

2. **test_outline_accepts_matched_corpus**
   - Setup: Mock corpus search to return hiring content
   - Input: Outline request for "Hiring Managers" topic
   - Expected: Outline generated successfully with hiring-related sections
   - Validates: Normal path still works

3. **test_draft_rejects_mismatched_sources**
   - Setup: Mock sources about dashboards for a hiring section
   - Input: Draft request for hiring manager section
   - Expected: Draft generator returns error/rejection
   - Validates: Topic validation in draft prompt works

4. **test_improved_search_queries**
   - Input: Title, keywords, thesis
   - Expected: Longer, more specific queries generated
   - Validates: Query construction improvements work

5. **test_corpus_context_richness**
   - Input: Mock search results with metadata
   - Expected: Context includes similarity scores, source names, 500-char previews
   - Validates: Context building improvements work

**Quality Metrics** (not coverage):
- ✅ Topic validation actually prevents wrong content generation
- ✅ Search queries are specific enough to discriminate topics
- ✅ Corpus context provides sufficient signal for LLM
- ✅ Logging provides actionable debugging information

---

## Phase 2: Search Quality (NEXT WEEK)

### 2.1 Add Search Result Validation

**File**: `src/bloginator/search/validators.py` (NEW)
**Status**: 📅 Planned

**Purpose**: Programmatic validation of search result relevance before LLM sees them.

**Implementation**:
```python
"""Search result validation and quality checks."""

from typing import Any
import logging

from bloginator.search import SearchResult

logger = logging.getLogger(__name__)


def validate_search_results(
    results: list[SearchResult],
    expected_keywords: list[str],
    similarity_threshold: float = 0.3,
    min_keyword_matches: int = 1,
) -> tuple[list[SearchResult], list[str]]:
    """Validate search results for topic relevance.

    Filters results based on:
    1. Similarity score threshold
    2. Keyword presence in content

    Args:
        results: Search results to validate
        expected_keywords: Keywords that should appear in results
        similarity_threshold: Minimum similarity score to accept
        min_keyword_matches: Minimum keywords that must appear in content

    Returns:
        Tuple of (filtered_results, warnings)
    """
    filtered_results = []
    warnings = []

    for result in results:
        # Check 1: Similarity threshold
        if result.similarity_score < similarity_threshold:
            warnings.append(
                f"Low similarity ({result.similarity_score:.3f}) for: "
                f"{result.content[:50]}..."
            )
            continue

        # Check 2: Keyword presence
        content_lower = result.content.lower()
        matches = sum(1 for kw in expected_keywords if kw.lower() in content_lower)

        if matches < min_keyword_matches:
            warnings.append(
                f"Insufficient keyword matches ({matches}/{min_keyword_matches}) "
                f"in: {result.content[:50]}..."
            )
            continue

        filtered_results.append(result)

    # Log overall quality
    if len(filtered_results) < len(results) / 2:
        logger.warning(
            f"Search quality concern: {len(filtered_results)}/{len(results)} "
            f"results passed validation"
        )

    return filtered_results, warnings
```

**Integration Points**:
- Call in `outline_generator.py` after search, before building context
- Call in `draft_generator.py` after section search
- Log warnings for diagnostic purposes

**Testing**:
- Test with high-quality results (should pass through)
- Test with low similarity results (should filter out)
- Test with off-topic results (should filter out via keyword check)

---

### 2.2 Experiment with Better Embedding Models

**Status**: 📅 Planned

**Current**: `all-MiniLM-L6-v2` (80MB, fast, general-purpose)

**Candidates**:
1. **all-mpnet-base-v2** (420MB)
   - Better semantic understanding
   - Trained on larger corpus
   - Higher quality embeddings

2. **multi-qa-mpnet-base-dot-v1** (420MB)
   - Optimized for question-answering
   - Better for query→document matching

**Experiment Protocol**:
1. Create test corpus subset (100 documents)
2. Index with both models
3. Run same 7 queries from test cases
4. Compare:
   - Topic relevance of top 5 results
   - Similarity score distributions
   - Retrieval time (performance cost)

**Decision Criteria**:
- If new model significantly improves topic discrimination → migrate
- If performance cost too high → stay with current
- Document findings in this file

---

## Phase 3: Advanced Improvements (LATER)

### 3.1 Query Expansion and Optimization

**Status**: 💡 Future Work

**Approach**:
- Use LLM to expand queries with synonyms and related terms
- Example: "hiring manager" → "talent acquisition", "recruiting lead"
- Merge results from multiple query strategies

### 3.2 LLM-Based Relevance Scoring

**Status**: 💡 Future Work

**Approach**:
- Before generation, ask LLM: "Does this source relate to [topic]?"
- Filter low-relevance sources automatically
- Reduces garbage-in problem at the source

---

## Progress Tracking

### Phase 1 Tasks

- [x] 1.1 Add topic validation to outline prompt (`prompts/outline/base.yaml`)
- [x] 1.2 Improve search query construction (`_outline_prompt_builder.py`)
- [x] 1.3 Increase corpus context depth (`_outline_prompt_builder.py`)
- [x] 1.4 Add search result logging (`outline_generator.py`)
- [x] 1.5 Add topic validation to draft prompt (`prompts/draft/base.yaml`)
- [x] Create integration tests (`tests/integration/test_topic_alignment.py`)
- [x] Test with hiring managers blog (worst performer #1)
- [x] Test with stand-up meetings blog (worst performer #2)
- [x] Commit and push to origin/main
- [ ] Document results and lessons learned below

### Phase 2 Tasks

- [x] 2.1 Implement search result validation
- [ ] 2.2 Run embedding model experiments
- [ ] Document findings

### Phase 3 Tasks

- [ ] 3.1 Query expansion
- [ ] 3.2 LLM-based relevance scoring

---

## Results Log

### Test Run: 2025-12-04 (After Phase 1 Implementation)

**Setup**:
- Phase 1 critical fixes implemented:
    - Topic validation added to outline and draft prompts.
    - Improved search query construction with thesis.
    - Increased corpus context depth and added metadata.
    - Search result logging added.
- Integration tests (`tests/integration/test_topic_alignment.py`) created.
- Two worst-performing test cases re-run in mock LLM mode.

**Results**:
1. **"What Great Hiring Managers Actually Do"**:
    - `outline.md` was rejected: "❌ OUTLINE REJECTED: Only 0/5 sections (0%) match provided keywords."
    - `draft.md` was effectively empty.
2. **"Daily Stand-Up Meetings That Don't Suck"**:
    - `outline.md` was rejected: "❌ OUTLINE REJECTED: Only 2/5 sections (40%) match provided keywords. The outline appears to be hallucinated (not grounded in your corpus)."
    - The corresponding `draft.md` was off-topic (prior assessment indicated "100% OFF TOPIC").

**Observations**:
- The new topic validation in the outline prompt successfully identified and rejected outlines where corpus content was irrelevant or led to hallucination.
- For "Hiring Managers", the rejection was absolute (0% keyword match), leading to an empty draft, which is desirable behavior for preventing off-topic content.
- For "Daily Stand-Up Meetings", the outline was partially rejected (40% keyword match), indicating some hallucination, and the resulting draft was still off-topic, suggesting either incomplete validation or continued issues with corpus content relevance at the draft stage.
- The core problem remains: the corpus often does not provide sufficiently relevant content for the requested topics, or the initial search results, despite improvements, are still too broad or low-quality. The LLM's interpretation of "relevance" might also need stricter guidance, especially at the draft level.

**Next Steps**:
Proceed with **Phase 2: Search Quality**, focusing on:
1. **Add Search Result Validation (2.1)**: Implement programmatic filtering of irrelevant search results *before* they reach the LLM, to act as a stronger guardrail against "garbage-in".
2. **Experiment with Better Embedding Models (2.2)**: Investigate alternative embedding models that offer higher semantic precision for topic discrimination, aiming to improve the quality of initial search results.
