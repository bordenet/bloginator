# Corpus Rules - CRITICAL

> **When to load:** ALWAYS load before ANY content generation task

---

## ⛔⛔⛔ NEVER BYPASS THE CORPUS ⛔⛔⛔

**THIS IS THE MOST IMPORTANT RULE FOR THIS PROJECT.**
**VIOLATION LEADS TO UNTRUSTWORTHY AI SLOP.**

When generating blog content, you MUST use the bloginator pipeline with corpus search.
NEVER write blog content directly from your training data.

### Why This Matters

The ENTIRE PURPOSE of bloginator is to generate content that:
1. Reflects the user's documented knowledge in the corpus
2. Matches the user's writing voice (voice scoring)
3. Uses the user's specific terminology and examples
4. Is grounded in RAG search results from the corpus

Content generated from your training data is USELESS because:
- It doesn't reflect the user's actual practices
- It doesn't match the user's voice
- It's generic "industry standard" content
- It defeats the entire purpose of this project

---

## ⛔ NEVER CREATE HARDCODED RESPONSE SCRIPTS ⛔

**DO NOT create scripts like `tmp/batch_responses.py` with hardcoded content.**

This is the WORST possible failure mode because:
1. It looks like it works (files get created, drafts get generated)
2. But the content is FABRICATED from training data, not corpus
3. The user cannot distinguish fake content from real corpus synthesis
4. It defeats the ENTIRE PURPOSE of this project

**If you find yourself writing a script with hardcoded response content, STOP.**
That content should come from READING THE REQUEST FILES and SYNTHESIZING FROM THE
CORPUS CONTENT inside them.

---

## How to Generate Blog Content Correctly

**ALWAYS use one of these approaches:**

1. **Interactive mode** (user provides LLM responses):
   ```bash
   BLOGINATOR_LLM_MOCK=interactive bloginator outline --index .bloginator/chroma \
       --title "Topic Title" --keywords "keyword1,keyword2,keyword3" -o outline.json
   BLOGINATOR_LLM_MOCK=interactive bloginator draft --index .bloginator/chroma \
       --outline outline.json -o draft.md
   ```

2. **Assistant mode** (Claude acts as LLM backend):
   ```bash
   BLOGINATOR_LLM_MOCK=assistant bloginator outline --index .bloginator/chroma \
       --title "Topic Title" --keywords "keyword1,keyword2" -o outline.json
   # Then read requests from .bloginator/llm_requests/
   # Write responses to .bloginator/llm_responses/
   # Responses MUST be based on corpus search results in the request
   ```

---

## If You're Tempted to Shortcut

STOP. Ask the user how they want to proceed. Options:
- Wait for interactive mode (slower but correct)
- Use assistant mode (you act as LLM, reading corpus results)
- Batch process with a script

Speed is NOT worth generating useless content.

---

## Anti-Hallucination Checklist

Before writing any response content, verify:

- [ ] Every claim traces to a `[Source N]` section
- [ ] No metrics or numbers I invented
- [ ] No examples not explicitly in sources
- [ ] No "industry standard" filler from training data
- [ ] Terminology matches sources exactly
