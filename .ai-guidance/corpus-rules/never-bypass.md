# ⛔ NEVER BYPASS THE CORPUS

> **When to load:** ALWAYS before ANY content generation

## THE MOST IMPORTANT RULE

**VIOLATION LEADS TO UNTRUSTWORTHY AI SLOP.**

When generating blog content, you MUST use the bloginator pipeline with corpus search.
NEVER write blog content directly from your training data.

## Why This Matters

The ENTIRE PURPOSE of bloginator is to generate content that:
1. Reflects the user's documented knowledge in the corpus
2. Matches the user's writing voice (voice scoring)
3. Uses the user's specific terminology and examples
4. Is grounded in RAG search results from the corpus

Content generated from training data is USELESS because:
- It doesn't reflect the user's actual practices
- It doesn't match the user's voice
- It's generic "industry standard" content
- It defeats the entire purpose of this project

## ⛔ NEVER CREATE HARDCODED RESPONSE SCRIPTS

**DO NOT create scripts like `tmp/batch_responses.py` with hardcoded content.**

This is the WORST failure mode because:
1. It looks like it works (files get created)
2. But the content is FABRICATED from training data
3. User cannot distinguish fake from real corpus synthesis
4. It defeats the ENTIRE PURPOSE of this project

**If you find yourself writing hardcoded response content, STOP.**

