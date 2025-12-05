# Blog Generation Task - Continue from Previous Session

## Context

We've been fixing bugs in Bloginator and generating blog posts. Recent commits:

```
1a6322f Fix search validator to accept high-similarity results without keyword match
9dc7afd Improve coverage calculation and add new blog topics
677960c Fix critical metadata bug: add source field to ChromaDB indexer
```

The corpus is indexed at `.bloginator/chroma` with collection name `bloginator_corpus`.

## Blogs to Generate

Generate outlines and drafts for these 8 blog topics (already in `corpus/blog-topics.yaml`):

### Priority 1 - Should be near-100% corpus matches:
1. **WHAT vs HOW** - "Understanding the Differences Between the WHAT and the HOW in Product Definition"
   - Source: `Understanding_the_Differences_Between_the__WHAT__and_the__HOW__in_Product_Definition.md`
   - Keywords: product-management, requirements, what-vs-how, engineering, collaboration
   - Audience: all-disciplines

2. **Leadership Terminology** - Keywords: leadership, management, engineering
3. **SBI Feedback** - Keywords: feedback, coaching, management
4. **Technical Leadership** - Keywords: leadership, management, review, engineering

### Priority 2 - Incident definitions (user note: NO P0/Sev0 - that's hyperbolic!):
5. **Incident Priority and Severity Definitions** - Define P1/P2/P3 or Sev1/Sev2/Sev3

### Priority 3 - Career Ladders (must match source 100%):
6. **SDE Career Ladder** - Source: Career_Ladder directory
7. **SRE Career Ladder** - Source: Career_Ladder directory
8. **MGR Career Ladder** - Source: Career_Ladder directory

## Commands to Use

```bash
# Activate environment
source .venv/bin/activate

# Generate outline (interactive mode - you provide LLM responses)
BLOGINATOR_LLM_MOCK=interactive bloginator outline \
  --index .bloginator/chroma \
  --title "Blog Title Here" \
  --keywords "keyword1,keyword2,keyword3" \
  --audience "engineering-leaders" \
  -o blogs/output-name-outline.json

# Generate draft from outline
BLOGINATOR_LLM_MOCK=interactive bloginator draft \
  --index .bloginator/chroma \
  --outline blogs/output-name-outline.json \
  -o blogs/output-name-draft.md
```

## Interactive Mode Instructions

When `BLOGINATOR_LLM_MOCK=interactive`:
1. The CLI shows the prompt with CORPUS CONTEXT (search results from ChromaDB)
2. You provide the LLM response based on that context
3. Type `END_RESPONSE` on a new line when done
4. The tool parses your response and continues

## Key Technical Details

- **Coverage threshold**: 0.25 similarity = 100% coverage
- **High similarity bypass**: Results with similarity >= 0.4 skip keyword validation
- **Best match weight**: 90% best match + 10% average for coverage calculation
- Similarity = 1 - distance (ChromaDB uses cosine distance)

## Verification

After generating, check the output files exist and have reasonable content:
```bash
ls -la blogs/*.json blogs/*.md
head -50 blogs/what-vs-how-draft.md
```

## Quality Gate (run before committing)

```bash
./scripts/run-fast-quality-gate.sh
pytest tests/unit/generation/ -v --no-cov
```
