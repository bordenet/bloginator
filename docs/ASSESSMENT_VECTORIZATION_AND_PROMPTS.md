# Assessment: Corpus Vectorization and LLM Prompt Quality

## Executive Summary

After analyzing the topic drift issue (all 7 test blogs generating dashboard/SLI content instead of hiring, agile rituals, and incidents), I've identified **three critical problems** that must be addressed:

1. **CRITICAL: Corpus search is retrieving irrelevant content** - The search queries are too generic and aren't effectively filtering for topic-relevant material
2. **HIGH: LLM prompts lack strong topic constraints** - Prompts don't adequately enforce topic alignment with title/keywords/thesis
3. **MEDIUM: Corpus context is too shallow** - Only 200 characters per search result provides minimal topic signal

**ROOT CAUSE**: This is likely a **garbage-in/garbage-out** problem where poor corpus retrieval + weak prompt constraints allow the LLM to drift to whatever dominant topics exist in the corpus (in this case, dashboards).

---

## Problem 1: Corpus Search Quality (CRITICAL)

### Current Implementation Issues

**File**: [src/bloginator/generation/_outline_prompt_builder.py:11-33](src/bloginator/generation/_outline_prompt_builder.py:11-33)

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

**Problems**:
- Generic augmentation ("implementation", "best practices", "guide") dilutes specificity
- No use of thesis statement for additional context
- No query expansion based on topic domain
- Queries are too short to effectively discriminate between topics

**Example Failure Case**:
```
Title: "What Great Hiring Managers Actually Do"
Keywords: ["recruiting", "interviewing", "hiring manager"]
Generated Query: "recruiting implementation"  # Too generic!
Result: Returns dashboard content because it happens to have higher similarity
```

**File**: [src/bloginator/generation/draft_generator.py:176-184](src/bloginator/generation/draft_generator.py:176-184)

```python
query = f"{outline_section.title} {outline_section.description} {' '.join(keywords[:2])}"
```

**Problem**: Simple string concatenation without query optimization or relevance boosting.

### Vectorization Quality Assessment

**File**: [src/bloginator/indexing/indexer.py:39](src/bloginator/indexing/indexer.py:39)

```python
embedding_model_name: str = "all-MiniLM-L6-v2"
```

**Current Model**: `all-MiniLM-L6-v2`
- **Strengths**: Fast, lightweight (80MB), general-purpose
- **Weaknesses**:
  - Limited semantic understanding for nuanced topic discrimination
  - Trained on general web corpus, not technical/professional content
  - May struggle to differentiate between:
    - "hiring managers" vs "incident managers"
    - "agile rituals" vs "SRE practices"

**Recommendation**: Consider upgrading to a more powerful model:
- `all-mpnet-base-v2` (420MB) - Better semantic understanding
- `multi-qa-mpnet-base-dot-v1` - Optimized for question-answer retrieval
- Domain-specific models if available

### Proposed Solutions

1. **Improve Query Construction** ([_outline_prompt_builder.py:11-33](src/bloginator/generation/_outline_prompt_builder.py:11-33)):
   - Include thesis statement in queries
   - Use longer, more specific queries
   - Add negative keywords to exclude irrelevant topics
   - Implement query expansion with synonyms

2. **Add Query Validation** (new functionality):
   - Log actual search results returned
   - Add similarity score threshold filtering
   - Implement topic coherence check before using results

3. **Upgrade Embedding Model**:
   - Test `all-mpnet-base-v2` for better semantic discrimination
   - Consider fine-tuning on your corpus for domain specificity

---

## Problem 2: LLM Prompt Constraints (HIGH)

### Current Prompt Analysis

**File**: [prompts/outline/base.yaml:26-31](prompts/outline/base.yaml:26-31)

```yaml
CRITICAL CONSTRAINT:
- Each section MUST directly relate to the keywords provided
- Do NOT invent sections on tangential or unrelated topics
- Do NOT include sections about other methodologies, approaches, or topics unless explicitly requested
- All sections should be grounded in the keywords and thesis provided
- If a section cannot be justified by the keywords, do not include it
```

**Good**: Has explicit constraints against topic drift.

**File**: [prompts/outline/base.yaml:64-70](prompts/outline/base.yaml:64-70)

```yaml
CRITICAL INSTRUCTIONS:
- Base your outline ONLY on the corpus context provided above
- Every section MUST directly relate to actual content in the corpus
- Do NOT invent or hallucinate sections not grounded in the corpus
- Do NOT include sections about unrelated topics (e.g., if corpus is about dashboards, don't create sections about sprint planning)
- Only create sections for topics actually present in the provided corpus context
- If the corpus doesn't cover a topic, don't create a section for it
```

**Problem**: This is **too trusting of corpus search results**. If corpus search returns dashboard content (due to poor retrieval), the LLM will follow instructions and create dashboard sections!

**CONTRADICTION**:
- System prompt says: "Base ONLY on keywords and thesis"
- User prompt says: "Base ONLY on corpus context"
- When corpus context is wrong, the user prompt wins!

### Draft Prompt Analysis

**File**: [prompts/draft/base.yaml:28-33](prompts/draft/base.yaml:28-33)

```yaml
You are a skilled technical writer creating authentic content.
Write in a clear, professional voice based ONLY on the provided source material.
{{classification_guidance}}.
Write for {{audience_context}}.
Do not invent facts or examples not present in the sources.
Write naturally without explicitly citing sources in the text.
```

**Problem**: NO MENTION OF TOPIC CONSTRAINTS. The draft prompt trusts source material completely without validating topic relevance.

### Proposed Solutions

1. **Add Topic Validation Layer** (prompts/outline/base.yaml):
   ```yaml
   TOPIC VALIDATION (execute BEFORE creating outline):
   1. Check if corpus context actually relates to: {{title}} and {{keywords}}
   2. If corpus context is about a DIFFERENT topic, REJECT IT and state:
      "WARNING: Corpus search returned irrelevant content about [detected topic].
       Cannot create outline for {{title}} without relevant source material."
   3. Only proceed if corpus context matches the requested topic.
   ```

2. **Strengthen Title/Keyword Enforcement**:
   ```yaml
   MANDATORY TOPIC ALIGNMENT:
   - Every section title MUST include at least one keyword from: {{keywords}}
   - Section content MUST directly address the title: {{title}}
   - If a section doesn't clearly relate to {{title}}, DO NOT include it
   - Example: For title "What Great Hiring Managers Do", sections must be about
     hiring managers specifically, NOT about dashboards, SLIs, or unrelated topics.
   ```

3. **Add Pre-generation Sanity Check** (draft_generator.py):
   - Before generating, check if search results contain target keywords
   - Log warning if similarity scores are below threshold
   - Optionally: Add LLM-based relevance scoring of search results

---

## Problem 3: Corpus Context Depth (MEDIUM)

### Current Implementation

**File**: [src/bloginator/generation/_outline_prompt_builder.py:36-56](src/bloginator/generation/_outline_prompt_builder.py:36-56)

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

**Problems**:
- **200 characters per result** is extremely shallow
- No metadata about document title, tags, or quality rating
- No similarity scores shown to LLM
- Only 5 results used for outline (may miss relevant content)

**Impact**: 200 characters × 5 results = ~1000 characters total context. This is minimal topic signal for the LLM to understand corpus coverage.

### Proposed Solutions

1. **Increase Context Depth**:
   ```python
   preview = result.content[:500]  # Increase from 200 to 500 chars
   # Or use first paragraph instead of arbitrary character limit
   ```

2. **Add Rich Metadata**:
   ```python
   context = f"[Similarity: {result.similarity_score:.2f}] "
   context += f"[Source: {result.metadata.get('filename')}] "
   context += result.content[:300]
   ```

3. **Include Document Titles**:
   - If corpus documents have titles, include them
   - Helps LLM understand if content is relevant

---

## Recommended Implementation Priority

### Phase 1: Critical Fixes (Do Immediately)

1. **Add Topic Validation to Outline Prompt** ([prompts/outline/base.yaml](prompts/outline/base.yaml)):
   - Add explicit topic mismatch detection
   - Require keyword presence in section titles
   - Make LLM validate corpus relevance before proceeding

2. **Improve Search Queries** ([_outline_prompt_builder.py](src/bloginator/generation/_outline_prompt_builder.py)):
   - Include thesis in queries
   - Use longer, more specific query strings
   - Add logging to inspect actual search results

3. **Increase Corpus Context Depth** ([_outline_prompt_builder.py:52](src/bloginator/generation/_outline_prompt_builder.py:52)):
   - Increase from 200 to 500 characters per result
   - Add similarity scores and source metadata

### Phase 2: Search Quality (Do Next Week)

4. **Add Search Result Validation** (new file: `src/bloginator/search/validators.py`):
   - Check if results contain target keywords
   - Filter results below similarity threshold
   - Log warnings for poor retrieval quality

5. **Experiment with Embedding Models**:
   - Test `all-mpnet-base-v2` on a subset
   - Compare retrieval quality vs current model
   - Decide if performance trade-off is worth it

### Phase 3: Advanced Improvements (Do Later)

6. **Query Expansion and Optimization**:
   - Implement semantic query expansion
   - Add synonym detection
   - Use multiple query strategies and merge results

7. **LLM-based Relevance Scoring**:
   - Before generation, ask LLM to rate search result relevance
   - Filter out low-relevance results automatically

---

## Testing Protocol

After implementing fixes, re-run the 7 test blogs and verify:

1. **Topic Alignment**: Does generated content actually match the requested topic?
2. **Corpus Utilization**: Are search results actually relevant to the topic?
3. **Keyword Presence**: Do section titles contain requested keywords?
4. **No Topic Drift**: Are there any sections about unrelated topics?

Success Criteria:
- ✅ 7/7 blogs generate content about the REQUESTED topic
- ✅ Search logs show high similarity scores (>0.5) for relevant content
- ✅ No dashboard/SLI content in hiring/agile/incident blogs
- ✅ Section titles include keywords from the request

---

## Conclusion

The topic drift issue stems from **weak search + weak prompt constraints**, creating a perfect storm where:
1. Poor corpus retrieval returns dashboard content
2. Prompts trust corpus results without validation
3. LLM follows instructions and creates dashboard content

**The fix requires strengthening BOTH layers**:
- **Layer 1**: Improve corpus search quality
- **Layer 2**: Add LLM prompt validation to catch bad retrieval

This is classic **garbage-in/garbage-out**—we must fix the garbage coming in (corpus search) AND add validation to detect garbage before it goes into the LLM.
