# Batch Mode Procedure

> **When to load:** When using batch mode for blog generation

## Step 1: Count Sections

```bash
cat blogs/OUTLINE.json | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('sections',[]); print(f'Requests: {len(s)+sum(len(x.get(\"subsections\",[])) for x in s)}')"
```

## Step 2: Match Response Count

Response script MUST match section count. Do NOT hardcode - each outline differs (17-19 sections).

## Step 3: Batch Mode

```bash
rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*
BLOGINATOR_LLM_MOCK=assistant bloginator draft \
    --index .bloginator/chroma --outline blogs/OUTLINE.json \
    -o blogs/OUTPUT.md --batch --batch-timeout 120 2>&1 &
sleep 5
python tmp/batch_responses.py
wait
```

## Step 4: Verify

```bash
ls -la blogs/career-ladders/OUTPUT.md
grep -c "^|" blogs/career-ladders/OUTPUT.md
```

