# Batch Generation: All Topics

> **When to load:** When generating multiple blogs from topic list

## Topic Source

Read topics from `corpus/blog-topics.yaml`. For each topic extract:
- title
- keywords
- audience
- summary
- sections

Generate outline then draft for each topic.

## Priority Order

1. **Career ladders** (SDE, SRE, MGR) - Already have outlines
2. **Recruiting series** (8 topics)
3. **Agile rituals series** (12 topics)
4. **Operational excellence series** (15 topics)
5. **Culture & leadership series** (20 topics)

## Batch Process

```bash
# Read topics from corpus/blog-topics.yaml
# For each topic:
#   1. Extract: title, keywords, audience, summary, sections
#   2. Generate outline
#   3. Generate draft
# See corpus/blog-topics.yaml for full list
```

