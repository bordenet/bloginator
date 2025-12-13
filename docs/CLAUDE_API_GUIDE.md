# Using Claude API with Bloginator

Bloginator has full native support for the Anthropic Claude API, allowing you to generate blogs using Claude models directly from the command line.

## Quick Start (3 Steps)

### Step 1: Get Your API Key

1. Go to [api.anthropic.com](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to API keys
4. Create a new API key
5. Copy the key (format: `sk-ant-...`)

### Step 2: Configure Environment

Add to your `.env` file:

```env
BLOGINATOR_LLM_PROVIDER=anthropic
BLOGINATOR_LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

Or set environment variables directly:

```bash
export BLOGINATOR_LLM_PROVIDER=anthropic
export BLOGINATOR_LLM_MODEL=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

### Step 3: Generate a Blog

```bash
# Generate outline
bloginator outline \
  --index .bloginator/chroma \
  --title "Building Scalable Systems" \
  --keywords "architecture,scaling,performance" \
  -o outline.json

# Generate draft from outline
bloginator draft \
  --index .bloginator/chroma \
  --outline outline.json \
  -o draft.md
```

## Available Claude Models

Update `BLOGINATOR_LLM_MODEL` to use different models:

| Model | Performance | Cost | Latency | Best For |
|-------|-------------|------|---------|----------|
| `claude-3-5-sonnet-20241022` | Highest quality | Balanced | Medium | Production quality blogs, complex topics |
| `claude-3-opus-20240229` | Highest capability | Most expensive | Slower | Very complex, nuanced content |
| `claude-3-sonnet-20240229` | High quality | Balanced | Medium | General blog generation |
| `claude-3-haiku-20240307` | Faster | Cheapest | Fast | Quick drafts, simple topics |

**Recommendation for blog generation**: Use `claude-3-5-sonnet-20241022` (best balance of quality and speed).

## Complete Example Workflow

```bash
# 1. Setup (one-time)
export BLOGINATOR_LLM_PROVIDER=anthropic
export BLOGINATOR_LLM_MODEL=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=sk-ant-your-key

# 2. Extract your blog corpus
bloginator extract ~/my-blog-archive -o extracted --quality preferred

# 3. Build search index
bloginator index extracted -o .bloginator/chroma

# 4. Generate blog outline
bloginator outline \
  --index .bloginator/chroma \
  --title "Engineering Leadership at Scale" \
  --keywords "leadership,engineering,team-building,culture" \
  --thesis "Scaling an engineering team requires rethinking communication, decision-making, and organizational structure" \
  -o outline.json

# 5. Generate full blog draft
bloginator draft \
  --index .bloginator/chroma \
  --outline outline.json \
  --output draft.md

# 6. View result
cat draft.md

# 7. Export to other formats (optional)
bloginator export draft.md --format docx -o final.docx
```

## Configuration Options

### Temperature (Creativity vs. Consistency)

```bash
export BLOGINATOR_LLM_TEMPERATURE=0.7  # Default (balanced)
# 0.0 = deterministic/factual
# 0.7 = balanced (recommended for blogs)
# 1.0 = maximum creativity
```

### Token Limits

```bash
export BLOGINATOR_LLM_MAX_TOKENS=2000  # Default
# Adjust based on desired output length
```

### Timeout

```bash
export BLOGINATOR_LLM_TIMEOUT=120  # Default (seconds)
# Increase for longer/complex generations
```

## Inline Configuration (One-off Runs)

Generate without modifying `.env`:

```bash
BLOGINATOR_LLM_PROVIDER=anthropic \
BLOGINATOR_LLM_MODEL=claude-3-5-sonnet-20241022 \
ANTHROPIC_API_KEY=sk-ant-your-key \
bloginator outline \
  --index .bloginator/chroma \
  --title "Your Topic" \
  --keywords "key1,key2,key3" \
  -o outline.json
```

## Batch Generation (Multiple Blogs)

Generate multiple blogs in a loop:

```bash
#!/bin/bash

export BLOGINATOR_LLM_PROVIDER=anthropic
export BLOGINATOR_LLM_MODEL=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=sk-ant-your-key

# Topic definitions
declare -a topics=(
  "Incident Response Best Practices"
  "Building Resilient Microservices"
  "Effective Code Review Practices"
  "Mentoring Engineering Teams"
)

for topic in "${topics[@]}"; do
  echo "Generating blog: $topic"
  
  # Generate outline
  bloginator outline \
    --index .bloginator/chroma \
    --title "$topic" \
    --keywords "engineering,best-practices" \
    -o "blogs/${topic}_outline.json"
  
  # Generate draft
  bloginator draft \
    --index .bloginator/chroma \
    --outline "blogs/${topic}_outline.json" \
    -o "blogs/${topic}.md"
done

echo "✓ All blogs generated"
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

**Solution**:
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY=sk-ant-your-key

# Or add to .env and reload
cat >> .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-your-key
EOF
source .env
```

### "Anthropic generation failed: 401 Unauthorized"

**Solution**: API key is invalid or expired
```bash
# 1. Verify key format starts with sk-ant-
# 2. Check key at console.anthropic.com
# 3. Generate a new key if needed
# 4. Update ANTHROPIC_API_KEY
```

### "Connection refused"

**Solution**: Claude API is unavailable (rare)
```bash
# Test connection
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"

# If it fails, Anthropic API is down - try again later
```

### "Rate limit exceeded"

**Solution**: You've made too many requests
```bash
# Wait before retrying
sleep 60

# Or adjust your batch processing to space out requests
```

### "Max tokens exceeded"

**Solution**: Generated content exceeds token limit
```bash
# Increase limit
export BLOGINATOR_LLM_MAX_TOKENS=4000

# Or request shorter generation
bloginator draft --outline outline.json --max-section-words 200
```

## Cost Estimation

Claude pricing (as of 2024):

| Model | Input | Output |
|-------|-------|--------|
| claude-3-5-sonnet | $3/M tokens | $15/M tokens |
| claude-3-opus | $15/M tokens | $75/M tokens |
| claude-3-haiku | $0.80/M tokens | $4/M tokens |

**Typical blog generation cost**:
- Outline generation: ~5,000 tokens input + 1,000 tokens output = $0.05
- Draft generation: ~20,000 tokens input + 2,000 tokens output = $0.15
- **Total per blog**: ~$0.20 using claude-3-5-sonnet

**Budget estimate**:
- 10 blogs/month = $2
- 100 blogs/month = $20
- 1000 blogs/month = $200

## Comparing Providers

### Claude API (Recommended for Quality)
✓ Highest quality outputs
✓ Best for professional content
✓ Pay-per-token (no setup costs)
✓ Fast generation
✗ Requires API key management
✗ No local privacy (cloud-based)

### Ollama (Recommended for Privacy)
✓ Local/private
✓ No API key needed
✓ No usage costs
✗ Requires more setup
✗ Lower quality than Claude
✗ Requires local compute resources

### OpenAI (Alternative)
✓ Good quality (GPT-4)
✓ Similar to Claude pricing
✗ Slightly different output style
✗ May not match your voice as well

## Advanced Usage

### Using with Different Blog Styles

```bash
# Professional/Technical
export BLOGINATOR_LLM_TEMPERATURE=0.5
export BLOGINATOR_LLM_MODEL=claude-3-5-sonnet-20241022

# Conversational/Engaging
export BLOGINATOR_LLM_TEMPERATURE=0.8
export BLOGINATOR_LLM_MODEL=claude-3-5-sonnet-20241022

# Formal/Academic
export BLOGINATOR_LLM_TEMPERATURE=0.3
export BLOGINATOR_LLM_MODEL=claude-3-opus-20240229
```

### Combining with Assistant Mode

You can switch between Claude API and Claude-via-requests:

```bash
# Use Claude API directly (fast)
export BLOGINATOR_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
bloginator outline --index ... --title "..." -o outline.json

# Or use assistant mode (gives you control)
export BLOGINATOR_LLM_MOCK=assistant
bloginator outline --index ... --title "..." -o outline.json
# Then you manually respond to requests in .bloginator/llm_requests/
```

## Next Steps

1. **Try the quick start** above
2. **Review generated output** and adjust temperature/model as needed
3. **Integrate into CI/CD** for automated blog generation
4. **Use with corpus** to leverage your existing writing for style matching

## Related Documentation

- [CUSTOM_LLM_GUIDE.md](CUSTOM_LLM_GUIDE.md) - Other LLM providers
- [USER_GUIDE.md](USER_GUIDE.md) - Full Bloginator usage
- [OLLAMA_FALLBACK.md](OLLAMA_FALLBACK.md) - Fallback behavior when local Ollama is unavailable
