# Custom LLM Integration Guide

This guide explains how to connect Bloginator to custom LLM endpoints, including self-hosted models, LM Studio, vLLM, text-generation-webui, or any OpenAI-compatible API.

## Quick Start

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Configure Your Custom LLM

Edit `.env` and set:

```bash
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_MODEL=your-model-name
BLOGINATOR_LLM_BASE_URL=http://your-endpoint:port/v1
```

### 3. Test Connection

```bash
# This will verify your LLM endpoint is accessible
bloginator outline "test topic" --dry-run
```

## Supported Configurations

### LM Studio (Local)

LM Studio provides a local OpenAI-compatible API.

```bash
# .env configuration
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_MODEL=local-model
BLOGINATOR_LLM_BASE_URL=http://localhost:1234/v1
```

**Steps:**
1. Download and start LM Studio
2. Load your preferred model
3. Start the local server (default port: 1234)
4. Run Bloginator with the config above

### vLLM (Self-hosted)

vLLM is a high-performance inference server.

```bash
# .env configuration
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_MODEL=meta-llama/Llama-2-7b-chat-hf
BLOGINATOR_LLM_BASE_URL=http://your-vllm-server:8000/v1
```

### Text Generation WebUI (oobabooga)

```bash
# .env configuration
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_MODEL=your-loaded-model
BLOGINATOR_LLM_BASE_URL=http://localhost:5000/v1

# If using API extensions
BLOGINATOR_LLM_CUSTOM_HEADERS="X-API-KEY:your-api-key-if-needed"
```

### Custom Remote Endpoint

```bash
# .env configuration
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_MODEL=custom-model
BLOGINATOR_LLM_BASE_URL=https://your-api.example.com/v1
BLOGINATOR_LLM_API_KEY=your-api-key-here
```

### Ollama (Local - Default)

Ollama is the default provider, but you can also configure it explicitly:

```bash
# .env configuration
BLOGINATOR_LLM_PROVIDER=ollama
BLOGINATOR_LLM_MODEL=llama3
BLOGINATOR_LLM_BASE_URL=http://localhost:11434
```

## Advanced Configuration

### Custom Headers

For endpoints requiring special headers (authentication, routing, etc.):

```bash
BLOGINATOR_LLM_CUSTOM_HEADERS="Authorization:Bearer YOUR_TOKEN,X-Custom:value"
```

Format: `Header1:Value1,Header2:Value2`

### Temperature & Token Limits

Adjust generation parameters:

```bash
# Lower = more focused, higher = more creative (0.0 - 1.0)
BLOGINATOR_LLM_TEMPERATURE=0.7

# Maximum tokens to generate
BLOGINATOR_LLM_MAX_TOKENS=2000

# Request timeout (seconds)
BLOGINATOR_LLM_TIMEOUT=120
```

### Debug Mode

Enable detailed logging:

```bash
BLOGINATOR_DEBUG=true
```

## API Compatibility

Bloginator's `CustomLLMClient` expects OpenAI-compatible chat completion endpoints:

### Request Format

```json
POST /v1/chat/completions
{
  "model": "your-model",
  "messages": [
    {"role": "system", "content": "system prompt"},
    {"role": "user", "content": "user prompt"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### Response Format

```json
{
  "choices": [
    {
      "message": {
        "content": "generated text"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 200
  }
}
```

## Migrating from films-not-made

If you're migrating from another project with custom LLM configuration:

### 1. Copy .env Settings

```bash
# Review your films-not-made .env
cat ../films-not-made/.env

# Copy relevant LLM settings to bloginator .env
# Adapt variable names:
#   YOUR_LLM_ENDPOINT → BLOGINATOR_LLM_BASE_URL
#   YOUR_MODEL_NAME   → BLOGINATOR_LLM_MODEL
#   YOUR_API_KEY      → BLOGINATOR_LLM_API_KEY
```

### 2. Map Variable Names

| films-not-made | bloginator |
|----------------|------------|
| `LLM_API_URL` | `BLOGINATOR_LLM_BASE_URL` |
| `LLM_MODEL` | `BLOGINATOR_LLM_MODEL` |
| `API_KEY` | `BLOGINATOR_LLM_API_KEY` |
| Custom headers | `BLOGINATOR_LLM_CUSTOM_HEADERS` |

### 3. Test Configuration

```bash
# Verify endpoint is accessible
curl $BLOGINATOR_LLM_BASE_URL/models

# Test with bloginator
bloginator search "test query" --limit 3
```

## Troubleshooting

### Connection Errors

**Error**: `Unable to connect to custom LLM`

**Solutions**:
1. Verify the endpoint is running: `curl $BLOGINATOR_LLM_BASE_URL/models`
2. Check firewall/network settings
3. Ensure URL includes `/v1` suffix for OpenAI compatibility
4. Try increasing `BLOGINATOR_LLM_TIMEOUT`

### Invalid Response Errors

**Error**: `Invalid response from custom LLM`

**Solutions**:
1. Verify your endpoint returns OpenAI-compatible responses
2. Check API logs for errors
3. Enable debug mode: `BLOGINATOR_DEBUG=true`
4. Test endpoint directly with curl:

```bash
curl -X POST $BLOGINATOR_LLM_BASE_URL/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
  }'
```

### Authentication Failures

**Error**: HTTP 401/403

**Solutions**:
1. Verify `BLOGINATOR_LLM_API_KEY` is set correctly
2. Add custom auth headers via `BLOGINATOR_LLM_CUSTOM_HEADERS`
3. Check API key permissions/expiration

### Model Not Found

**Error**: Model not available

**Solutions**:
1. List available models: `curl $BLOGINATOR_LLM_BASE_URL/models`
2. Verify `BLOGINATOR_LLM_MODEL` matches an available model
3. Load the model in your LLM server (LM Studio, vLLM, etc.)

## Example Workflows

### Local Development (LM Studio)

```bash
# 1. Start LM Studio and load a model
# 2. Start local server on port 1234
# 3. Configure bloginator
cat > .env << 'EOF'
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_MODEL=local-model
BLOGINATOR_LLM_BASE_URL=http://localhost:1234/v1
BLOGINATOR_CORPUS_DIR=corpus
EOF

# 4. Add your blog posts
cp ~/my-blogs/*.md corpus/

# 5. Index corpus
bloginator index corpus/

# 6. Generate content
bloginator draft "My next blog post topic"
```

### Production (Remote Endpoint)

```bash
# 1. Configure remote endpoint
cat > .env << 'EOF'
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_MODEL=production-model
BLOGINATOR_LLM_BASE_URL=https://api.example.com/v1
BLOGINATOR_LLM_API_KEY=sk-your-production-key
BLOGINATOR_CORPUS_DIR=corpus
EOF

# 2. Index corpus
bloginator index corpus/

# 3. Generate content
bloginator draft "Topic" --output output/draft.md
```

## Security Best Practices

1. **Never commit `.env` to version control** (already in `.gitignore`)
2. **Use environment-specific `.env` files** (`.env.dev`, `.env.prod`)
3. **Rotate API keys regularly** if using cloud endpoints
4. **Use HTTPS** for remote endpoints
5. **Limit API key permissions** to only what's needed
6. **Monitor API usage** to detect anomalies

## Performance Tips

1. **Local LLMs**: Use GPU acceleration (CUDA/Metal) for better performance
2. **Batch Processing**: Generate multiple drafts in sequence
3. **Caching**: Bloginator uses ChromaDB for semantic caching
4. **Timeouts**: Increase `BLOGINATOR_LLM_TIMEOUT` for large generation tasks
5. **Token Limits**: Adjust `BLOGINATOR_LLM_MAX_TOKENS` based on your needs

## Getting Help

If you encounter issues:

1. Check this guide's troubleshooting section
2. Enable debug mode: `BLOGINATOR_DEBUG=true`
3. Review LLM server logs
4. Test endpoint directly with curl
5. Open an issue on GitHub with debug output
