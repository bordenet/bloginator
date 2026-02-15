# Common Batch Mode Mistakes

> **When to load:** When batch generation fails

## Mistakes to Avoid

1. **Hardcoding 17 responses** - Different outlines have different section counts
2. **Not waiting for requests** - Must `sleep 5` before writing responses
3. **Running commands serially** - Use `&` and `wait` for background processes
4. **Not clearing old requests** - Always `rm -rf .bloginator/llm_requests/*` first
5. **Timeout too short** - Use `--batch-timeout 120` minimum for testing

## Pre-Flight Checklist

Before starting ANY blog generation task:

- [ ] Verify outline exists: `ls -la blogs/*.json`
- [ ] Count sections in outline (see procedure.md)
- [ ] Verify index exists: `ls -la .bloginator/chroma`
- [ ] Clear old requests: `rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*`
- [ ] Verify response script matches section count

