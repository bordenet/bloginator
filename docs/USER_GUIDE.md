# Bloginator User Guide

This comprehensive guide covers all features and workflows in Bloginator, from corpus management to document generation and refinement.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Corpus Management](#corpus-management)
4. [Document Templates](#document-templates)
5. [Content Generation](#content-generation)
6. [Refinement & Iteration](#refinement--iteration)
7. [Blocklist Management](#blocklist-management)
8. [Web Interface](#web-interface)
9. [Command-Line Reference](#command-line-reference)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Overview

Bloginator creates documents by leveraging your historical writing. The system:

1. **Indexes your past writing** (blog posts, documents, presentations)
2. **Searches semantically** to find relevant content
3. **Generates new content** based on retrieved examples
4. **Protects proprietary information** with blocklist validation
5. **Refines iteratively** based on feedback

This approach can reduce document creation time while maintaining consistency with your existing writing style.

---

## Getting Started

### Quick Start Workflow

#### Option 1: Web Interface (Recommended)

```bash
# Start the web server
bloginator serve --port 8000

# Open your browser to http://localhost:8000
# Follow the on-screen wizard to:
# 1. Upload and index your corpus
# 2. Choose a document template
# 3. Generate and refine content
```

#### Option 2: Command Line

```bash
# 1. Extract and index your writing
bloginator extract ~/my-writing -o ./extracted
bloginator index ./extracted -o ./my-index

# 2. Search your corpus
bloginator search ./my-index "team leadership"

# 3. Generate a document
bloginator outline --index ./my-index \
  --keywords "engineering,leadership,culture" \
  --template team_charter

bloginator draft outline.json -o draft.md

# 4. Refine the draft
bloginator refine draft.md "Make tone more collaborative"

# 5. Export
bloginator export draft.md --format docx -o final.docx
```

---

## Corpus Management

Your corpus is the foundation of content generation. A well-curated corpus improves the quality and relevance of generated content.

### What to Include

**Good Corpus Material**:
- Blog posts you've written
- Internal technical documents
- Presentations and talks
- Performance reviews you've written
- Project proposals and retrospectives
- Engineering playbooks and guides
- Email newsletters (if well-written)

**Avoid**:
- Meeting notes (usually low quality)
- Chat logs (too informal)
- Code comments (not prose)
- Others' writing (won't match your voice)

### Extracting Documents

The `extract` command processes various document formats into plain text:

```bash
# Basic extraction
bloginator extract ~/my-writing -o ./extracted

# With quality markers (affects search ranking)
bloginator extract ~/my-writing -o ./extracted --quality preferred

# Limit to specific file types
bloginator extract ~/my-writing -o ./extracted --formats pdf,docx

# Recursive extraction from nested directories
bloginator extract ~/my-writing -o ./extracted --recursive
```

**Quality Markers**:
- `preferred`: Your best work, refined and polished
- `standard`: Normal quality writing
- `draft`: Rough drafts or lower quality

Quality markers affect search ranking—`preferred` content is weighted more heavily.

### Indexing Your Corpus

The `index` command creates a searchable vector database:

```bash
# Basic indexing
bloginator index ./extracted -o ./my-index

# With custom embedding model
bloginator index ./extracted -o ./my-index \
  --model sentence-transformers/all-mpnet-base-v2

# Incremental updates (add new documents to existing index)
bloginator index ./new-documents -o ./my-index --update
```

**What Happens During Indexing**:
1. Text is split into semantic chunks (paragraphs/sections)
2. Each chunk is converted to a vector embedding
3. Vectors are stored in ChromaDB for fast semantic search
4. Metadata (dates, quality, source) is preserved

### Managing Your Corpus

**Adding New Documents**:
```bash
# Extract new documents
bloginator extract ~/new-writing -o ./new-extracted --quality preferred

# Update existing index
bloginator index ./new-extracted -o ./my-index --update
```

**Viewing Corpus Stats**:
```bash
# Show index statistics
bloginator stats ./my-index
```

**Rebuilding Index**:
```bash
# If index becomes corrupted, rebuild from scratch
rm -rf ./my-index
bloginator index ./extracted -o ./my-index
```

---

## Document Templates

Bloginator includes 12 pre-built templates for common document types. Templates provide structured outlines that guide content generation.

### Available Templates

| Template ID | Name | Use Case |
|-------------|------|----------|
| `blog_post` | Blog Post | Technical blog posts with introduction, body, conclusion |
| `job_description` | Job Description | Engineering role descriptions with requirements |
| `career_ladder` | Career Ladder | Career progression frameworks by level |
| `engineering_playbook` | Engineering Playbook | Team practices, processes, and principles |
| `technical_design` | Technical Design Doc | Design docs with problem, solution, alternatives |
| `onboarding_guide` | Onboarding Guide | New hire onboarding with week-by-week plan |
| `project_proposal` | Project Proposal | Project proposals with scope, timeline, metrics |
| `performance_review` | Performance Review | Engineering performance evaluation framework |
| `architecture_doc` | Architecture Doc | System architecture documentation |
| `team_charter` | Team Charter | Team mission, values, and ways of working |
| `incident_postmortem` | Incident Postmortem | Blameless postmortems with timeline and action items |
| `rfp_response` | RFP Response | Response to Request for Proposal |

### Using Templates

**Via Web Interface**:
1. Navigate to "Create Document"
2. Select a template from the dropdown
3. Customize the outline if needed
4. Generate draft

**Via Command Line**:
```bash
# Generate outline from template
bloginator outline --index ./my-index \
  --template career_ladder \
  -o outline.json

# View available templates
bloginator templates list

# View template details
bloginator templates show career_ladder
```

### Customizing Templates

Templates are JSON files in `src/bloginator/templates/`. You can:

1. **Modify existing templates**: Edit the JSON files directly
2. **Create custom templates**: Copy and modify an existing template
3. **Share templates**: Contribute useful templates back to the project

**Template Structure**:
```json
{
  "title": "Document Title",
  "thesis": "Main argument or theme",
  "keywords": ["keyword1", "keyword2"],
  "sections": [
    {
      "title": "Section Title",
      "description": "What this section should cover",
      "subsections": [
        {
          "title": "Subsection Title",
          "description": "Subsection details"
        }
      ]
    }
  ]
}
```

---

## Content Generation

### Step 1: Generate Outline

The outline defines the structure of your document:

```bash
# From keywords
bloginator outline --index ./my-index \
  --keywords "engineering,culture,values" \
  -o outline.json

# From a template
bloginator outline --index ./my-index \
  --template engineering_playbook \
  -o outline.json

# From a thesis statement
bloginator outline --index ./my-index \
  --thesis "Building high-performing engineering teams requires clear values and practices" \
  -o outline.json

# Combining approaches
bloginator outline --index ./my-index \
  --template team_charter \
  --keywords "collaboration,ownership,innovation" \
  --thesis "Our team values shipping fast while maintaining quality" \
  -o outline.json
```

**Review the Outline**: Always review `outline.json` before generating the draft. You can edit it manually to:
- Adjust section titles
- Add or remove sections
- Modify section descriptions
- Reorder sections

### Step 2: Generate Draft

```bash
# Basic draft generation
bloginator draft outline.json -o draft.md

# With voice similarity threshold (0.0-1.0, higher = stricter)
bloginator draft outline.json -o draft.md --similarity 0.75

# With source citations
bloginator draft outline.json -o draft.md --citations

# Specify output format
bloginator draft outline.json -o draft.md --format markdown
bloginator draft outline.json -o draft.docx --format docx
```

**What Happens During Generation**:
1. Each section is analyzed for relevant keywords
2. Corpus is searched for related content
3. Retrieved passages are used to generate section content
4. Voice similarity is checked against your corpus
5. Blocklist is validated to prevent proprietary leaks
6. Final draft is assembled

### Understanding Voice Similarity

Voice similarity measures how closely generated content matches your writing style:

- **0.6-0.7**: More creative, may drift from your style
- **0.7-0.8**: Balanced (default)
- **0.8-0.9**: Very similar to your voice
- **0.9-1.0**: Extremely conservative, may be repetitive

### Source Citations

When generating with `--citations`, Bloginator includes references:

```markdown
## Team Values

Our team prioritizes collaboration and ownership [^1]. We believe in shipping
fast while maintaining high quality standards [^2].

[^1]: Source: "Engineering Culture Memo" (2023-06-15)
[^2]: Source: "Q3 Team Retrospective" (2023-09-30)
```

---

## Refinement & Iteration

Generated drafts are rarely perfect. Bloginator supports iterative refinement through natural language feedback.

### Refining Content

```bash
# Make specific changes
bloginator refine draft.md "Make the tone more optimistic"

# Multiple refinement passes
bloginator refine draft.md "Expand the leadership section"
bloginator refine draft.md "Add specific examples to the collaboration section"
bloginator refine draft.md "Make the conclusion more actionable"

# Refine specific sections
bloginator refine draft.md \
  --section "Team Values" \
  "Add more emphasis on psychological safety"
```

**Effective Refinement Prompts**:
- ✅ "Make the tone more collaborative"
- ✅ "Expand section 3 with specific examples"
- ✅ "Simplify the technical jargon"
- ✅ "Add a stronger call to action"
- ❌ "Make it better" (too vague)
- ❌ "Fix the problems" (not specific)

### Tracking Changes

```bash
# View changes between versions
bloginator diff draft.md draft_v2.md

# View all versions
bloginator versions draft.md

# Revert to previous version
bloginator revert draft.md --version 2
```

### Version Management

Bloginator automatically saves versions:
```
draft.md           # Current version
draft.v1.md        # First version
draft.v2.md        # After first refinement
draft.v3.md        # After second refinement
```

---

## Blocklist Management

The blocklist prevents proprietary information from appearing in generated content.

### Why Use a Blocklist?

Protect:
- Company names (especially from NDAs)
- Product codenames and internal projects
- Client/customer names
- Trade secrets and proprietary terms
- Personal information (emails, names)

### Adding Blocklist Entries

```bash
# Add exact match term
bloginator blocklist add "Acme Corp" \
  --category company_name \
  --notes "Former employer, under NDA"

# Add case-insensitive term
bloginator blocklist add "SecretProject" \
  --category internal_project \
  --case-insensitive

# Add regex pattern
bloginator blocklist add "[a-zA-Z0-9._%+-]+@acmecorp\.com" \
  --category email \
  --regex \
  --notes "Company email addresses"
```

### Managing Blocklist

```bash
# View all entries
bloginator blocklist list

# Filter by category
bloginator blocklist list --category company_name

# Remove entry
bloginator blocklist remove "Acme Corp"

# Validate text against blocklist
bloginator blocklist validate draft.md
```

### Blocklist Categories

Organize entries by category for easier management:
- `company_name`: Company and organization names
- `product_name`: Product and service names
- `internal_project`: Internal project codenames
- `person_name`: Names of individuals
- `email`: Email addresses
- `url`: URLs and domains
- `trade_secret`: Proprietary technical terms
- `nda_term`: Terms under NDA
- `custom`: Other categories

### Automatic Blocklist Checking

Blocklist validation happens automatically during:
1. Draft generation (`bloginator draft`)
2. Refinement (`bloginator refine`)
3. Export (`bloginator export`)

If violations are found, generation is blocked and violations are reported.

---

## Web Interface

The web UI provides an intuitive interface for all Bloginator features.

### Starting the Web Server

```bash
# Start on default port (8000)
bloginator serve

# Custom port
bloginator serve --port 3000

# Custom host (allow external access)
bloginator serve --host 0.0.0.0 --port 8000

# Enable auto-reload (for development)
bloginator serve --reload
```

### Web Interface Features

**Home Page** (`/`):
- Overview of Bloginator
- Quick access to main workflows
- Recent activity

**Corpus Management** (`/corpus`):
- Upload documents (drag & drop)
- Create/update index
- Manage blocklist
- View corpus statistics

**Create Document** (`/create`):
- 3-step wizard workflow
- Template selection
- Outline generation
- Draft generation
- Refinement interface

**Search** (`/search`):
- Semantic search interface
- Preview search results
- Adjust number of results
- See source metadata

### Web UI Workflow

1. **Upload Corpus**:
   - Navigate to "Corpus Management"
   - Upload PDFs, DOCX, or Markdown files
   - Mark quality level (preferred/standard/draft)
   - Click "Create Index"

2. **Generate Document**:
   - Navigate to "Create Document"
   - Select a template or enter keywords
   - Review and customize outline
   - Generate draft
   - Download or continue refining

3. **Refine**:
   - Enter natural language feedback
   - Click "Refine"
   - Review changes
   - Repeat until satisfied

4. **Export**:
   - Choose format (Markdown, DOCX, HTML, TXT)
   - Download final document

---

## Command-Line Reference

### Core Commands

```bash
# Extract documents
bloginator extract <input-dir> -o <output-dir> [OPTIONS]
  --quality <preferred|standard|draft>
  --formats <pdf,docx,md,txt>
  --recursive
  --tags <tag1,tag2>

# Create index
bloginator index <input-dir> -o <output-dir> [OPTIONS]
  --model <embedding-model>
  --update  # Incremental update
  --chunk-size <int>

# Search corpus
bloginator search <index-path> <query> [OPTIONS]
  -n, --n-results <int>  # Number of results (default: 10)
  --format <json|text>

# Generate outline
bloginator outline [OPTIONS]
  --index <path>
  --keywords <keyword1,keyword2>
  --template <template-id>
  --thesis <string>
  -o, --output <file>

# Generate draft
bloginator draft <outline-file> [OPTIONS]
  -o, --output <file>
  --similarity <float>  # 0.0-1.0
  --citations
  --format <markdown|docx|html|txt>

# Refine content
bloginator refine <draft-file> <feedback> [OPTIONS]
  --section <section-name>
  -o, --output <file>

# Export document
bloginator export <input-file> [OPTIONS]
  --format <markdown|docx|html|txt>
  -o, --output <file>

# Manage blocklist
bloginator blocklist add <term> [OPTIONS]
  --category <category>
  --case-insensitive
  --regex
  --notes <string>

bloginator blocklist list [--category <category>]
bloginator blocklist remove <term>
bloginator blocklist validate <file>

# Start web server
bloginator serve [OPTIONS]
  --host <hostname>  # Default: 127.0.0.1
  --port <port>      # Default: 8000
  --reload           # Auto-reload on code changes

# View templates
bloginator templates list
bloginator templates show <template-id>

# Utilities
bloginator stats <index-path>
bloginator diff <file1> <file2>
bloginator versions <file>
bloginator revert <file> --version <n>
```

### Global Options

```bash
--verbose, -v    # Verbose output
--quiet, -q      # Minimal output
--help, -h       # Show help
--version        # Show version
```

---

## Best Practices

### Corpus Quality

1. **Curate carefully**: Only include your best writing
2. **Mark quality levels**: Use `--quality preferred` for your best work
3. **Regular updates**: Add new writing to keep corpus current
4. **Diverse content**: Include various document types and topics
5. **Remove duplicates**: Don't index the same content multiple times

### Document Generation

1. **Start with templates**: Use pre-built templates when possible
2. **Review outlines**: Always check the outline before generating
3. **Iterate gradually**: Make small refinements rather than big rewrites
4. **Use citations**: Track sources with `--citations` flag
5. **Check voice similarity**: Aim for 0.7-0.8 for balanced results

### Blocklist Management

1. **Proactive protection**: Add terms before generating content
2. **Use categories**: Organize blocklist entries by type
3. **Regular audits**: Review blocklist quarterly
4. **Regex patterns**: Use regex for flexible matching (emails, URLs)
5. **Document reasons**: Add notes explaining why terms are blocked

### Performance Optimization

1. **Chunk size**: Larger chunks (800-1200 tokens) for coherent context
2. **Index updates**: Use `--update` for incremental additions
3. **Similarity threshold**: Lower threshold (0.6-0.7) for faster generation
4. **Local LLMs**: Use Ollama/LM Studio for privacy and cost savings
5. **Batch processing**: Generate multiple documents in one session

---

## Troubleshooting

### Common Issues

**Search returns no results**:
- Check index exists and is not corrupted
- Try broader search terms
- Verify corpus was indexed successfully
- Rebuild index if necessary

**Generated content doesn't match my voice**:
- Increase similarity threshold (0.8-0.9)
- Review corpus quality—remove low-quality writing
- Mark best content as `preferred` quality
- Add more diverse examples to corpus

**Blocklist not catching terms**:
- Verify exact spelling and capitalization
- Use `--case-insensitive` for flexible matching
- Consider regex patterns for variations
- Check category filters aren't excluding entries

**Web UI not loading**:
- Verify server is running (`bloginator serve`)
- Check port isn't already in use
- Try different port: `bloginator serve --port 3000`
- Check firewall settings

**Generation is slow**:
- Use local LLM (Ollama) instead of cloud API
- Reduce similarity threshold
- Decrease number of search results
- Use smaller embedding model

**Outline generation fails**:
- Provide more specific keywords or thesis
- Try a different template
- Check index path is correct
- Verify LLM is accessible

### Getting Help

- **Documentation**: Check [docs/](.) directory
- **Issues**: Report bugs at [GitHub Issues](https://github.com/bordenet/bloginator/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/bordenet/bloginator/discussions)
- **Logs**: Run with `--verbose` for detailed logging

---

## Advanced Topics

### Custom Embedding Models

```bash
# Use different sentence-transformers model
bloginator index ./extracted -o ./my-index \
  --model sentence-transformers/all-mpnet-base-v2

# Popular models:
# - all-MiniLM-L6-v2 (default, fast, good quality)
# - all-mpnet-base-v2 (slower, higher quality)
# - all-MiniLM-L12-v2 (balanced)
```

### Metadata Filtering

```bash
# Extract with custom metadata tags
bloginator extract ~/my-writing -o ./extracted \
  --tags "engineering,leadership,2023"

# Search with metadata filters (coming soon)
bloginator search ./my-index "culture" --tags "leadership"
```

### Batch Processing

```bash
# Generate multiple documents from template
for topic in leadership culture onboarding; do
  bloginator outline --index ./my-index \
    --template engineering_playbook \
    --keywords "$topic" \
    -o "outline_$topic.json"

  bloginator draft "outline_$topic.json" \
    -o "draft_$topic.md"
done
```

### API Integration (Advanced)

The web UI exposes REST APIs for programmatic access:

```bash
# Search API
curl -X POST http://localhost:8000/api/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "team leadership", "n_results": 10}'

# Generate outline API
curl -X POST http://localhost:8000/api/documents/outline \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["culture", "values"], "template_id": "team_charter"}'
```

See API documentation at `http://localhost:8000/api/docs` when server is running.

---

## Next Steps

- Explore [Templates](../src/bloginator/templates/) for pre-built document types
- Read [Developer Guide](DEVELOPER_GUIDE.md) for architecture and system design details
- Check [Custom LLM Guide](CUSTOM_LLM_GUIDE.md) for advanced LLM configuration
- Review [Future Work](FUTURE_WORK.md) for planned features and enhancements

**Happy writing with Bloginator!**
