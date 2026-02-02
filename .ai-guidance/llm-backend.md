# LLM Backend Mode

> **When to load:** When generating blog content, acting as LLM backend, or configuring LLM modes

---

## ⚠️ CRITICAL: YOU ARE THE LLM ⚠️

**WHEN GENERATING BLOGS, YOU (CLAUDE) ARE THE LLM BACKEND.**

This is NOT optional. This is HOW THE SYSTEM WORKS.

When `.env` contains `BLOGINATOR_LLM_MOCK=assistant`:
1. You run `bloginator outline` or `bloginator draft`
2. Bloginator writes requests to `.bloginator/llm_requests/request_NNNN.json`
3. **YOU read those requests and write responses to `.bloginator/llm_responses/response_NNNN.json`**
4. Bloginator reads your responses and continues

**YOU DO NOT:**
- Ask "should I use an external LLM?"
- Say "the user needs to configure an API key"
- Suggest switching to Ollama/OpenAI/Anthropic
- Write blog content directly to markdown files

**YOU DO:**
- Read each request file from `.bloginator/llm_requests/`
- Extract source material from the `prompt` field
- Synthesize content from ONLY those sources
- Write response files to `.bloginator/llm_responses/`
- Continue until all requests are answered

This is the NORMAL workflow. Acting as the LLM backend is YOUR JOB in this project.

---

## LLM Mode Configuration

The `BLOGINATOR_LLM_MOCK` environment variable controls LLM behavior:

| Value | Client | Use Case |
|-------|--------|----------|
| `true` | `MockLLMClient` | Unit tests - returns canned responses |
| `interactive` | `InteractiveLLMClient` | Human-in-the-loop via terminal prompts |
| `assistant` | `AssistantLLMClient` | File-based communication for AI agents |
| *(unset)* | Real LLM client | Production use with Ollama/OpenAI/Anthropic |

**Note**: `BLOGINATOR_LLM_MOCK` takes precedence over `BLOGINATOR_LLM_PROVIDER`.

---

## How to Act as the LLM Backend

When using assistant mode, you must:

1. **Read each request file** in `.bloginator/llm_requests/request_NNNN.json`
2. **Extract the source material** from the `prompt` field (look for `[Source 1]`, `[Source 2]`, etc.)
3. **Synthesize content** from ONLY those sources using `prompts/corpus-synthesis-llm.md` guidelines
4. **Write response files** to `.bloginator/llm_responses/response_NNNN.json`

**Response file format:**
```json
{
  "content": "The synthesized prose from corpus sources...",
  "prompt_tokens": 1500,
  "completion_tokens": 300,
  "finish_reason": "stop"
}
```

**CRITICAL: The `content` field must contain prose synthesized from the [Source N] sections
in the request's prompt. If you write content that doesn't trace to those sources,
you have failed.**

---

## To Start Acting as LLM Backend

1. Set `BLOGINATOR_LLM_MOCK=assistant` in `.env`
2. Run a bloginator command (e.g., `bloginator outline --index .bloginator/chroma --title "Topic" --keywords "key1,key2" -o outline.json`)
3. Monitor `.bloginator/llm_requests/` for new request files
4. Read the request, apply `prompts/corpus-synthesis-llm.md` guidelines, write to `.bloginator/llm_responses/`

---

## No External LLM Required

- The user does NOT have external LLM API keys configured
- For testing, use `BLOGINATOR_LLM_MOCK=true` (canned responses)
- For real generation, Claude can act as the LLM via assistant mode
- NEVER switch to Ollama or other LLMs without explicit user request
