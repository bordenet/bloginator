# Voice Matching Requirements

> **When to load:** When synthesizing content to match author's voice

## Voice Matching Principles

When synthesizing, match the author's voice by:

1. **Use same terminology** - If sources say "Plan-of-Record", use that exact term
2. **Match sentence length** - Short, punchy sentences if sources are direct
3. **Preserve specific numbers** - "3 years experience" not "several years"
4. **Keep organizational terms** - "Four Quadrants", "Level 1/Level 2" as in sources
5. **Avoid AI slop** - No em-dashes (—), no "dive deep", no "leverage"

## Deduplication Requirements

Within each response and across sections:

1. **State each concept once** - Don't repeat with different words
2. **Consolidate overlapping sources** - Synthesize into one statement
3. **Forward reference, don't repeat** - "As noted in previous section"
4. **Keep unique details** - Different examples should all appear once

## Quality Verification

After each blog is generated, verify:

```bash
# Check file exists and has content
ls -la blogs/OUTPUT.md
wc -w blogs/OUTPUT.md  # Should be 2000+ words for full blogs

# Check for AI slop
grep -c "—" blogs/OUTPUT.md  # Should be 0 (no em-dashes)
grep -i "dive deep\|leverage\|game.changer" blogs/OUTPUT.md  # Should be 0
```

