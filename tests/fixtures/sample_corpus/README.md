# Sample Corpus for Testing

This directory contains sample blog posts for end-to-end testing of Bloginator.

## Contents

6 engineering leadership blog posts covering:

1. **one_on_ones.md** - Best practices for manager 1-on-1s (preferred quality)
2. **technical_debt.md** - Managing technical debt strategically (preferred quality)
3. **code_review_culture.md** - Building healthy code review practices (reference quality)
4. **hiring_engineers.md** - Senior engineer hiring guide (preferred quality)
5. **incident_response.md** - Incident management and on-call practices (reference quality)
6. **remote_work.md** - Distributed team culture lessons (preferred quality)

## Metadata

Each document includes:
- **Written date** - Simulated creation date
- **Tags** - Topical keywords
- **Quality rating** - preferred/reference classification

## Usage

### Extract and Index
```bash
bloginator extract tests/fixtures/sample_corpus -o output/extracted
bloginator index output/extracted -o output/index
```

### Search
```bash
bloginator search output/index "one-on-one meetings"
bloginator search output/index "technical debt" --quality-filter preferred
```

### Generate Content
```bash
# Generate outline
bloginator outline \
  --index output/index \
  --title "Engineering Leadership Guide" \
  --keywords "leadership,management,culture" \
  --classification best-practice \
  --audience engineering-leaders \
  -o outline.json

# Generate draft
bloginator draft \
  --index output/index \
  --outline outline.json \
  -o draft.md
```

## E2E Testing

Run the full end-to-end workflow test:
```bash
./tests/e2e/test_full_workflow.sh
```

This exercises:
- Document extraction
- Vector indexing
- Semantic search
- Outline generation
- Draft generation
- Export functionality
- History tracking

## Quality Ratings

- **Preferred**: Best writing, most authentic voice (4 documents)
- **Reference**: Solid content, good for citations (2 documents)
- **Supplemental**: Supporting material (none in this corpus)
- **Deprecated**: Outdated content (none in this corpus)

## Topics Covered

Search these topics to test corpus coverage:
- Leadership and management
- One-on-ones and mentoring
- Technical debt and architecture
- Code review culture
- Hiring and recruitment
- Incident response and SRE
- Remote work and distributed teams
- Team culture and collaboration

## Notes

These are synthetic blog posts created for testing. They represent realistic engineering leadership content suitable for validating Bloginator's end-to-end functionality.
