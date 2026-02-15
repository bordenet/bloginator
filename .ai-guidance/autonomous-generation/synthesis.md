# Content Synthesis Rules

> **When to load:** When synthesizing responses from corpus sources

## How Claude MUST Synthesize Responses

When reading request files, Claude MUST:

1. **Extract source material** - Look for `[Source 1]`, `[Source 2]`, etc.
2. **Identify key concepts** - What terms, frameworks, metrics are in sources?
3. **Synthesize into prose** - Combine sources into flowing paragraphs
4. **Match author voice** - Use sentence structure/vocabulary from sources
5. **Never invent** - If sources don't cover something, don't make it up

## Example Transformation

**Sources in request:**
```
[Source 1] SDE-1 engineers should focus on learning the codebase...
[Source 2] Entry-level engineers pair with seniors on complex work...
[Source 3] First year is about building foundational skills...
```

**CORRECT response (synthesized):**
```json
{
  "content": "The first year as an SDE-1 centers on mastering the codebase while establishing trust through consistent delivery. New engineers tackle well-defined tasks independently while pairing with senior colleagues on complex work.",
  "prompt_tokens": 1500,
  "completion_tokens": 60,
  "finish_reason": "stop"
}
```

**WRONG response (invented):**
```json
{
  "content": "Junior developers typically spend 3-6 months onboarding. Best practices suggest code reviews and mentorship programs..."
}
```

