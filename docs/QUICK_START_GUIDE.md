# Bloginator Quick Start Guide

Generate high-quality, corpus-grounded blog posts using AI-assisted content generation.

## Prerequisites

1. Python 3.10+ with virtual environment
2. Indexed corpus in `.bloginator/index/`
3. An AI assistant (Claude) to act as the LLM backend

## The Quality Method (Recommended)

The **only supported method** for blog generation uses `BLOGINATOR_LLM_MOCK=assistant` mode,
where an AI assistant (Claude) reads each content request and writes thoughtful, corpus-grounded
responses.

### Why This Method Works

- **Corpus grounding**: Each section request includes relevant source material from your indexed corpus
- **Human-quality writing**: AI writes natural prose that synthesizes sources intelligently
- **Topic validation**: AI can detect when source material doesn't match the section topic
- **Iterative refinement**: You can review and regenerate individual sections

### Step-by-Step Workflow

#### 1. Set Up Environment

```bash
# Activate virtual environment
source .venv/bin/activate

# Configure assistant mode
export BLOGINATOR_LLM_MOCK=assistant
```

Or add to `.env`:
```
BLOGINATOR_LLM_MOCK=assistant
```

#### 2. Generate an Outline

```bash
bloginator outline \
  --index .bloginator/index \
  --title "Your Blog Title" \
  --keywords "keyword1,keyword2,keyword3" \
  --audience engineering-leaders \
  -o blogs/my-blog-outline.json
```

The CLI will pause waiting for AI responses. Check `.bloginator/llm_requests/` for request files.

#### 3. Respond to LLM Requests

For each `request_NNNN.json` file:

1. Read the request to understand what content is needed
2. Write a response using the provided source material
3. Save as `response_NNNN.json` in `.bloginator/llm_responses/`

**Response format:**
```json
{
  "content": "Your written content here...",
  "timestamp": 1764913280.5
}
```

#### 4. Generate the Draft

```bash
bloginator draft \
  --index .bloginator/index \
  --outline blogs/my-blog-outline.json \
  -o blogs/my-blog-draft.md
```

This generates multiple section requests. Respond to each one with corpus-grounded content.

#### 5. Review and Export

```bash
# Check word count
wc -w blogs/my-blog-draft.md

# Export to HTML (optional)
bloginator export --format html blogs/my-blog-draft.md -o blogs/my-blog.html
```

## Working with an AI Assistant

When Claude is your LLM backend, share these instructions:

1. **Monitor** `.bloginator/llm_requests/` for new request files
2. **Read** the request JSON, noting:
   - Section title and description
   - Target word count
   - Source material provided
3. **Write** content that:
   - Synthesizes the source material naturally
   - Stays within the target length
   - Uses no em-dashes, avoids clichés
   - Includes specific metrics/examples from sources
4. **Save** response as `response_NNNN.json` with matching request ID

## Valid Audience Values

- `engineering-leaders` (managers, directors, VPs)
- `software-engineers` (individual contributors)
- `general` (broad technical audience)

## Troubleshooting

### "Missing option '--index'"
Always include `--index .bloginator/index` for outline and draft commands.

### Request files not appearing
Ensure `BLOGINATOR_LLM_MOCK=assistant` is set before running bloginator commands.

### Low corpus coverage
If requests show "No source material found", the corpus lacks content on that topic.
Consider adding relevant documents to `corpus/` and re-indexing.

## Deprecated: Quick/Template Method

> ⚠️ **DO NOT USE** `scripts/respond-to-llm-requests.py` or `scripts/generate-blog.sh`
>
> These scripts use hardcoded template responses that produce generic, low-quality content.
> They exist only for demo purposes and will be removed in a future release.

The template-based approach produces:
- Generic placeholder content
- No actual corpus synthesis
- Poor readability and engagement
- Content that fails quality review

Always use the AI-assisted quality method described above.
