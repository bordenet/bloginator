# Bloginator Examples

This directory contains example corpus documents and generated outputs to help you understand what Bloginator can do.

## Example Corpus

The `corpus/` directory contains sample documents from the [Engineering Culture](https://github.com/bordenet/Engineering_Culture) repository:

- **what-dashboards-are-good-for.md**: Understanding the proper role of observability dashboards
- **constructive-feedback-sbi-model.md**: The Situation-Behavior-Impact framework for feedback
- **mechanisms-building-self-correcting-systems.md**: Building systematic improvement processes

These documents demonstrate the type of content Bloginator works best with:

- Well-structured markdown with clear headings
- Practical, experience-based content from real engineering work
- Consistent voice and style across documents
- Cross-references that show topic relationships

## Quick Start with Examples

### 1. Extract and Index the Example Corpus

```bash
# Extract text from example documents
bloginator extract examples/corpus -o examples/output/extracted

# Create searchable index
bloginator index examples/output/extracted -o examples/output/index
```

### 2. Search the Corpus

```bash
# Search for relevant content
bloginator search examples/output/index "code review feedback" -n 5
```

### 3. Generate an Outline

```bash
# Generate outline for a new document
bloginator outline \
  --index examples/output/index \
  --keywords "team,culture,collaboration" \
  --thesis "Effective engineering teams combine technical excellence with strong collaboration" \
  -o examples/output/outline.json
```

### 4. Generate a Draft

```bash
# Generate draft from outline
bloginator draft \
  --index examples/output/index \
  --outline examples/output/outline.json \
  -o examples/output/draft.md
```

## Example Outputs

The `output/` directory contains sample generated content:

- **outline.json**: Example outline generated from the corpus
- **draft.md**: Example draft document generated from the outline

These show you what to expect from Bloginator's generation capabilities.

## What Makes Good Corpus Content?

Based on these examples, good corpus documents:

1. **Have clear structure**: Use headings, lists, and sections
2. **Are substantial**: At least 500-1000 words per document
3. **Are authentic**: Written in your natural voice
4. **Are practical**: Include specific examples and advice
5. **Are consistent**: Similar style and tone across documents

## Customizing for Your Use Case

To use Bloginator for your own content:

1. **Collect your writing**: Blog posts, documentation, presentations, notes
2. **Convert to supported formats**: PDF, DOCX, Markdown, or TXT
3. **Organize by topic**: Group related documents together
4. **Extract and index**: Use the commands above
5. **Generate content**: Create outlines and drafts based on your corpus

## Performance Expectations

With this example corpus (3 documents, ~2000 words total):

- **Extract**: <1 second
- **Index**: 5-10 seconds
- **Search**: <1 second
- **Outline**: 30-60 seconds
- **Draft**: 1-3 minutes

Larger corpora will take longer but scale reasonably well.

## Next Steps

- Read the [User Guide](../docs/USER_GUIDE.md) for detailed documentation
- Try the [Web UI](../docs/USER_GUIDE.md#web-interface) for a visual interface
- Explore [Templates](../src/bloginator/templates/) for different document types
- Check [Best Practices](../docs/USER_GUIDE.md#best-practices) for tips

## Questions?

See the [Troubleshooting Guide](../docs/USER_GUIDE.md#troubleshooting) or open an issue on GitHub.
