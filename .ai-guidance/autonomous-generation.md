# Autonomous Blog Generation (Zero Intervention)

> **When to load:** When generating blogs autonomously without user intervention

---

## Overview: The Full Blog Generation Pipeline

1. **Pick topics from `corpus/blog-topics.yaml`** - Contains all curated topics
2. **Generate outline** - Creates section structure with corpus search
3. **Generate draft** - Creates prose content with RAG from corpus
4. **Act as LLM backend** - Read request files, synthesize from sources, write responses
5. **Verify output** - Check word count, citations, voice score

---

## Step-by-Step: Generate One Blog Autonomously

```bash
# 1. Set the topic variables
TITLE="Your Blog Title"
KEYWORDS="keyword1,keyword2,keyword3"
AUDIENCE="engineering-leaders"  # or ic-engineers, devops-sre, all-disciplines
OUTPUT_NAME="blog-name"

# 2. Generate outline first
rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*
BLOGINATOR_LLM_MOCK=assistant bloginator outline \
  --index .bloginator/chroma \
  --title "$TITLE" \
  --keywords "$KEYWORDS" \
  --audience "$AUDIENCE" \
  -o "blogs/${OUTPUT_NAME}-outline.json" \
  --batch --batch-timeout 60 2>&1 &

# 3. Wait for requests, then provide responses (Claude reads & synthesizes)
sleep 3
# [Claude reads .bloginator/llm_requests/*.json and writes responses]

# 4. Generate draft from outline
rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*
BLOGINATOR_LLM_MOCK=assistant bloginator draft \
  --index .bloginator/chroma \
  --outline "blogs/${OUTPUT_NAME}-outline.json" \
  -o "blogs/${OUTPUT_NAME}.md" \
  --batch --batch-timeout 180 2>&1 &

# 5. Wait for requests, then provide responses
sleep 5
# [Claude reads .bloginator/llm_requests/*.json and writes responses]
```

---

## How Claude MUST Synthesize Responses

When reading request files, Claude MUST:

1. **Extract source material** - Look for `[Source 1]`, `[Source 2]`, etc. in the prompt
2. **Identify key concepts** - What specific terms, frameworks, metrics are in sources?
3. **Synthesize into prose** - Combine sources into flowing paragraphs
4. **Match author voice** - Use sentence structure and vocabulary from sources
5. **Never invent** - If sources don't cover something, don't make it up

**Example transformation:**

**Sources in request:**
```
[Source 1] SDE-1 engineers should focus on learning the codebase...
[Source 2] Entry-level engineers pair with seniors on complex work...
[Source 3] First year is about building foundational skills...
```

**CORRECT response (synthesized from sources):**
```json
{
  "content": "The first year as an SDE-1 centers on mastering the codebase while establishing trust through consistent delivery. New engineers tackle well-defined tasks independently while pairing with senior colleagues on complex work. This apprenticeship model accelerates skill-building.",
  "prompt_tokens": 1500,
  "completion_tokens": 60,
  "finish_reason": "stop"
}
```

**WRONG response (invented from training data):**
```json
{
  "content": "Junior developers typically spend 3-6 months onboarding. Best practices suggest code reviews and mentorship programs...",
  ...
}
```

---

## Voice Matching Requirements

When synthesizing, match the author's voice by:

1. **Use same terminology** - If sources say "Plan-of-Record", use that exact term
2. **Match sentence length** - Short, punchy sentences if sources are direct
3. **Preserve specific numbers** - "3 years experience" not "several years"
4. **Keep organizational terms** - "Four Quadrants", "Level 1/Level 2" as in sources
5. **Avoid AI slop** - No em-dashes (—), no "dive deep", no "leverage"

---

## Deduplication Requirements

Within each response and across sections:

1. **State each concept once** - Don't repeat the same point with different words
2. **Consolidate overlapping sources** - If sources repeat, synthesize into one statement
3. **Forward reference, don't repeat** - "As noted in the previous section" not full repeat
4. **Keep unique details** - Different examples from same concept should all appear once

---

## Quality Verification After Generation

After each blog is generated, verify:

```bash
# Check file exists and has content
ls -la blogs/OUTPUT.md
wc -w blogs/OUTPUT.md  # Should be 2000+ words for full blogs

# Check voice score and citations
head -20 blogs/OUTPUT.md  # Look for voice score in metadata

# Check for AI slop
grep -c "—" blogs/OUTPUT.md  # Should be 0 (no em-dashes)
grep -i "dive deep\|leverage\|game.changer" blogs/OUTPUT.md  # Should be 0
```

---

## Batch Generation: All Topics from blog-topics.yaml

To generate all blogs from the curated list:

```bash
# Read topics from corpus/blog-topics.yaml
# For each topic, extract: title, keywords, audience, summary, sections
# Generate outline then draft for each
# See corpus/blog-topics.yaml for full list
```

**Priority order:**
1. Career ladders (SDE, SRE, MGR) - Already have outlines
2. Recruiting series (8 topics)
3. Agile rituals series (12 topics)
4. Operational excellence series (15 topics)
5. Culture & leadership series (20 topics)
