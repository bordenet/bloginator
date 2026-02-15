# LLM Mode Configuration

> **When to load:** When configuring LLM behavior

## BLOGINATOR_LLM_MOCK Values

| Value | Client | Use Case |
|-------|--------|----------|
| `true` | `MockLLMClient` | Unit tests - canned responses |
| `interactive` | `InteractiveLLMClient` | Human-in-the-loop via terminal |
| `assistant` | `AssistantLLMClient` | File-based communication for AI |
| *(unset)* | Real LLM client | Production with Ollama/OpenAI |

**Note**: `BLOGINATOR_LLM_MOCK` takes precedence over `BLOGINATOR_LLM_PROVIDER`.

## How to Act as LLM Backend

When using assistant mode:

1. **Read each request** in `.bloginator/llm_requests/request_NNNN.json`
2. **Extract source material** from `prompt` field (`[Source 1]`, etc.)
3. **Synthesize content** from ONLY those sources
4. **Write response** to `.bloginator/llm_responses/response_NNNN.json`

**Response format:**
```json
{
  "content": "The synthesized prose from corpus sources...",
  "prompt_tokens": 1500,
  "completion_tokens": 300,
  "finish_reason": "stop"
}
```

**CRITICAL:** Content must trace to `[Source N]` sections. No invented content.

## No External LLM Required

- User does NOT have external LLM API keys configured
- For testing, use `BLOGINATOR_LLM_MOCK=true`
- For real generation, Claude acts as LLM via assistant mode
- NEVER switch to Ollama without explicit user request

