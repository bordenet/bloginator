# Autonomous Generation Pipeline

> **When to load:** When understanding the full blog generation workflow

## Overview: The Full Pipeline

1. **Pick topics** from `corpus/blog-topics.yaml` - Contains all curated topics
2. **Generate outline** - Creates section structure with corpus search
3. **Generate draft** - Creates prose content with RAG from corpus
4. **Act as LLM backend** - Read request files, synthesize from sources, write responses
5. **Verify output** - Check word count, citations, voice score

## Step-by-Step: Generate One Blog

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
  --title "$TITLE" --keywords "$KEYWORDS" --audience "$AUDIENCE" \
  -o "blogs/${OUTPUT_NAME}-outline.json" \
  --batch --batch-timeout 60 2>&1 &

# 3. Wait for requests, then provide responses (Claude reads & synthesizes)
sleep 3
# [Read .bloginator/llm_requests/*.json and write responses]

# 4. Generate draft from outline
rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*
BLOGINATOR_LLM_MOCK=assistant bloginator draft \
  --index .bloginator/chroma \
  --outline "blogs/${OUTPUT_NAME}-outline.json" \
  -o "blogs/${OUTPUT_NAME}.md" \
  --batch --batch-timeout 180 2>&1 &

# 5. Wait for requests, then provide responses
sleep 5
# [Read .bloginator/llm_requests/*.json and write responses]
```

