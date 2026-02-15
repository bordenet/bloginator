# ⚠️ CRITICAL: YOU ARE THE LLM

> **When to load:** When generating blog content

## YOU (CLAUDE) ARE THE LLM BACKEND

This is NOT optional. This is HOW THE SYSTEM WORKS.

When `.env` contains `BLOGINATOR_LLM_MOCK=assistant`:
1. You run `bloginator outline` or `bloginator draft`
2. Bloginator writes requests to `.bloginator/llm_requests/request_NNNN.json`
3. **YOU read those requests and write responses to `.bloginator/llm_responses/response_NNNN.json`**
4. Bloginator reads your responses and continues

## YOU DO NOT:
- Ask "should I use an external LLM?"
- Say "the user needs to configure an API key"
- Suggest switching to Ollama/OpenAI/Anthropic
- Write blog content directly to markdown files

## YOU DO:
- Read each request file from `.bloginator/llm_requests/`
- Extract source material from the `prompt` field
- Synthesize content from ONLY those sources
- Write response files to `.bloginator/llm_responses/`
- Continue until all requests are answered

This is the NORMAL workflow. Acting as the LLM backend is YOUR JOB.

