# Batch Mode Blog Generation

> **When to load:** When using batch mode for blog generation with assistant LLM

---

## Batch Mode Procedure

When generating blogs using batch mode with assistant LLM, follow this exact procedure:

### Step 1: Count Sections FIRST

Before generating ANY responses, count the total sections in the outline:

```bash
cat blogs/OUTLINE.json | python3 -c "
import sys,json
d=json.load(sys.stdin)
sections=d.get('sections',[])
total=len(sections)
subs=sum(len(s.get('subsections',[])) for s in sections)
print(f'Total requests needed: {total + subs}')
"
```

### Step 2: Generate Matching Response Count

The response script MUST generate exactly as many responses as there are sections.
Do NOT hardcode response counts. Each outline is different:
- SDE ladder: 17 sections
- SRE ladder: 18 sections
- Manager ladder: 19 sections
- Hiring managers: 15 sections

### Step 3: Use Batch Mode Correctly

```bash
# Clear previous requests/responses
rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*

# Start draft generation in background
BLOGINATOR_LLM_MOCK=assistant bloginator draft \
    --index .bloginator/chroma \
    --outline blogs/OUTLINE.json \
    -o blogs/OUTPUT.md \
    --batch --batch-timeout 120 2>&1 &

# Wait for requests to be generated
sleep 5

# Provide responses (must match request count!)
python tmp/batch_responses.py

# Wait for completion
wait
```

### Step 4: Verify Output

After generation, verify:
1. File exists and has content
2. Tables are present (for career ladders)
3. Citation metrics are reasonable

```bash
# Check file size and table count
ls -la blogs/career-ladders/OUTPUT.md
grep -c "^|" blogs/career-ladders/OUTPUT.md
```

---

## Common Mistakes to Avoid

1. **Hardcoding 17 responses** - Different outlines have different section counts
2. **Not waiting for requests** - Must `sleep 5` before writing responses
3. **Running commands serially** - Use `&` and `wait` for background processes
4. **Not clearing old requests** - Always `rm -rf .bloginator/llm_requests/*` first
5. **Timeout too short** - Use `--batch-timeout 120` minimum for testing

---

## Pre-Flight Checklist Before Blog Generation

Before starting ANY blog generation task:

- [ ] Verify outline exists: `ls -la blogs/*.json`
- [ ] Count sections in outline (see Step 1 above)
- [ ] Verify index exists: `ls -la .bloginator/chroma`
- [ ] Clear old requests: `rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*`
- [ ] Verify response script matches section count
