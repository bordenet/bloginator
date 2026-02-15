# Correct Content Generation Approach

> **When to load:** When generating blog content

## ALWAYS Use One of These Approaches

**1. Interactive mode** (user provides LLM responses):
```bash
BLOGINATOR_LLM_MOCK=interactive bloginator outline --index .bloginator/chroma \
    --title "Topic Title" --keywords "keyword1,keyword2,keyword3" -o outline.json
BLOGINATOR_LLM_MOCK=interactive bloginator draft --index .bloginator/chroma \
    --outline outline.json -o draft.md
```

**2. Assistant mode** (Claude acts as LLM backend):
```bash
BLOGINATOR_LLM_MOCK=assistant bloginator outline --index .bloginator/chroma \
    --title "Topic Title" --keywords "keyword1,keyword2" -o outline.json
# Then read requests from .bloginator/llm_requests/
# Write responses to .bloginator/llm_responses/
# Responses MUST be based on corpus search results in the request
```

## If You're Tempted to Shortcut

STOP. Ask the user how to proceed. Options:
- Wait for interactive mode (slower but correct)
- Use assistant mode (you act as LLM, reading corpus results)
- Batch process with a script

Speed is NOT worth generating useless content.

## Anti-Hallucination Checklist

Before writing any response content, verify:

- [ ] Every claim traces to a `[Source N]` section
- [ ] No metrics or numbers I invented
- [ ] No examples not explicitly in sources
- [ ] No "industry standard" filler from training data
- [ ] Terminology matches sources exactly

