# Bloginator Production Runbook

**Last Updated**: 2025-12-11
**Status**: Ready for production use with local/cloud LLMs

---

## Quick Links

- **Status Page**: Check `.bloginator/status.json` for system health
- **Logs**: Located in `.bloginator/logs/`
- **Index**: `.bloginator/chroma/` (search database)
- **Config**: `.env` (environment variables)
- **Commands**: `bloginator --help`

---

## Common Issues & Solutions

### 1. Command Hangs or Times Out

**Symptoms**:
- `bloginator outline` takes >5 minutes
- `bloginator draft` seems stuck
- Process consuming high CPU/memory

**Diagnosis**:
```bash
# Check if LLM is running (if using Ollama)
ollama list

# Check system resources
top -p $(pgrep -f "bloginator")

# Check for zombie processes
ps aux | grep bloginator | grep -v grep
```

**Solutions**:

**If using Ollama locally**:
```bash
# Verify Ollama is running
ps aux | grep ollama

# If not running
ollama serve

# Test connection
curl http://localhost:11434/api/health

# If slow, check model loaded
ollama ps

# Unload unused models
ollama rm model-name
```

**If using cloud LLM (OpenAI/Anthropic)**:
```bash
# Check API key is set
echo $OPENAI_API_KEY    # For OpenAI
echo $ANTHROPIC_API_KEY  # For Anthropic

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Check rate limits (may need to wait)
```

**Generic fixes**:
```bash
# Kill stuck process
pkill -9 -f "bloginator"

# Increase timeout in .env
export BLOGINATOR_OUTLINE_TIMEOUT=300  # 5 minutes
export BLOGINATOR_DRAFT_TIMEOUT=600    # 10 minutes

# Run with smaller batch size
bloginator outline --index .bloginator/chroma \
  --title "Topic" --keywords "key1,key2" \
  --max-search-results 5  # Instead of default 10
```

---

### 2. Search Returns No Results

**Symptoms**:
- `bloginator search "engineering" -n 10` returns empty results
- All search queries return score 0.00
- Corpus seems to have no data

**Diagnosis**:
```bash
# Check if index exists
ls -la .bloginator/chroma/

# Check index size
du -sh .bloginator/chroma/

# Try simple search
bloginator search .bloginator/chroma "the" -n 5

# Check corpus content
ls -la corpus/ | head -10
wc -l corpus/*.txt  # Count extracted text
```

**Solutions**:

**If index is empty**:
```bash
# Verify corpus exists
ls -la corpus/ | grep -E "\.txt|\.md"

# If no files, extract them
bloginator extract ~/Documents -o corpus

# Then index
bloginator index corpus -o .bloginator/chroma

# Verify indexing worked
bloginator search .bloginator/chroma "test" -n 5
```

**If index exists but search fails**:
```bash
# Rebuild index from scratch
rm -rf .bloginator/chroma
mkdir -p .bloginator/chroma

# Reindex
bloginator index corpus -o .bloginator/chroma

# Verify
ls -la .bloginator/chroma/ | wc -l  # Should have >100 files
```

**If corpus has content but very few results**:
```bash
# Problem: Embedding model may not match your content domain
# Solution 1: Add more relevant documents to corpus
bloginator extract ~/more-writing -o corpus

# Solution 2: Try hybrid search with BM25
bloginator search --index .bloginator/chroma \
  --mode hybrid "your keywords" -n 10
```

---

### 3. Index Creation Fails

**Symptoms**:
```
Error: Failed to index documents
Error: chromadb error: ...
Error: Out of memory
```

**Diagnosis**:
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS

# Check disk space
df -h .bloginator/

# Check Python memory usage
python -c "import psutil; print(psutil.virtual_memory())"
```

**Solutions**:

**If out of memory**:
```bash
# Increase system swap/memory limit
# Or index in smaller batches

# Index with smaller batch size
bloginator index corpus -o .bloginator/chroma \
  --batch-size 10  # Default 100

# Or split corpus into chunks
mkdir corpus-chunk1 corpus-chunk2
mv corpus/*.txt.1-500 corpus-chunk1/
bloginator index corpus-chunk1 -o .bloginator/chroma
bloginator index corpus-chunk2 -o .bloginator/chroma
```

**If ChromaDB corrupt**:
```bash
# Backup existing index
mv .bloginator/chroma .bloginator/chroma.backup

# Create fresh index
mkdir -p .bloginator/chroma
bloginator index corpus -o .bloginator/chroma

# Verify
bloginator search .bloginator/chroma "test" -n 3
```

**If embedding model fails to download**:
```bash
# Pre-download embedding model
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-mpnet-base-v2')
print('Model loaded successfully')
"

# Then retry indexing
bloginator index corpus -o .bloginator/chroma
```

---

### 4. Generated Content Has Poor Quality

**Symptoms**:
- Outline is generic or vague
- Draft has "AI slop" (em-dashes, corporate jargon, hedging)
- Content doesn't match your voice
- Low specificity score (< 3.5/5)

**Diagnosis**:
```bash
# Run quality check on draft
bloginator quality draft.md

# View quality metrics
cat draft.json | grep -A 5 "quality_score"

# Manually review for AI slop
grep -E "—|furthermore|As mentioned|various|diverse" draft.md
```

**Solutions**:

**If corpus is insufficient**:
```bash
# Check what the search finds for your topic
bloginator search .bloginator/chroma "your-topic" -n 20

# If few results, add more relevant documents
cp ~/Documents/your-topic-writings/* corpus/
bloginator index corpus -o .bloginator/chroma

# Regenerate with better corpus data
rm outline.json draft.md
bloginator outline --index .bloginator/chroma \
  --title "Your Topic" --keywords "key1,key2"
```

**If voice doesn't match**:
```bash
# Refine with voice feedback
bloginator refine draft.md \
  --feedback "Use more technical terms, less corporate language"

# Or manually edit voice examples in corpus
# Add example sentences showing your preferred style
```

**If too much AI slop**:
```bash
# Regenerate with stricter quality rules
bloginator draft outline.json -o draft.md \
  --max-quality-retries 5 \
  --quality-threshold high  # Instead of default

# Or use manual refinement
bloginator refine draft.md \
  --feedback "Remove em-dashes (—), use concrete examples instead of generalities"
```

---

### 5. LLM Connection Failures

**Symptoms**:
```
Error: Failed to connect to LLM
Error: API key invalid
Error: Rate limit exceeded
Connection timeout
```

**Diagnosis**:

**For Ollama**:
```bash
# Check Ollama running
ollama list

# Check port 11434 is open
netstat -an | grep 11434

# Test connection
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama3",
    "prompt": "hello"
  }'
```

**For OpenAI**:
```bash
# Check API key
echo $OPENAI_API_KEY | wc -c  # Should be >50 chars

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | head -10

# Check rate limits
# Visit https://platform.openai.com/account/billing/limits
```

**For Anthropic**:
```bash
# Check API key
echo $ANTHROPIC_API_KEY | wc -c

# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

**Solutions**:

**Ollama connection**:
```bash
# Start Ollama
ollama serve

# In new terminal
source venv/bin/activate
bloginator outline --index .bloginator/chroma \
  --title "Test" --keywords "test"
```

**OpenAI rate limit**:
```bash
# Wait 60 seconds for rate limit to reset
# Or upgrade account for higher limits
# https://platform.openai.com/account/billing/limits

# Temporarily switch to local LLM
export BLOGINATOR_LLM_PROVIDER=ollama
ollama pull llama3
bloginator outline --index .bloginator/chroma \
  --title "Test" --keywords "test"
```

**API key invalid**:
```bash
# Verify key in .env
cat .env | grep -E "OPENAI_API_KEY|ANTHROPIC_API_KEY"

# Or set from command line (don't commit to .env!)
export OPENAI_API_KEY="sk-..."
bloginator outline --index .bloginator/chroma \
  --title "Test" --keywords "test"

# Check key format
# OpenAI: starts with "sk-"
# Anthropic: 40+ character hex string
```

---

### 6. Extraction Fails on File

**Symptoms**:
```
Error: Failed to extract text from document.pdf
Error: Unsupported file format
Error: PDF appears corrupted
```

**Diagnosis**:
```bash
# Check file integrity
file ~/Downloads/document.pdf

# Try manual extraction to see error
bloginator extract ~/Downloads/document.pdf -o /tmp/test

# Get full error trace
BLOGINATOR_DEBUG=1 bloginator extract ~/Downloads/document.pdf -o /tmp/test
```

**Solutions**:

**If PDF corrupted**:
```bash
# Try repair tools
# macOS: Use Preview to re-save PDF
# Linux: `gs -sDEVICE=pdfwrite -o fixed.pdf input.pdf`

# Or skip and try another file
bloginator extract ~/Documents -o corpus \
  --skip ~/Downloads/bad-file.pdf
```

**If unsupported format**:
```bash
# Convert to supported format
# Supported: PDF, DOCX, MD, TXT, ZIP

# For Word files (.doc)
libreoffice --headless --convert-to docx document.doc

# For RTF
pandoc document.rtf -o document.md

# Then extract
bloginator extract ~/Documents -o corpus
```

**If image-heavy PDF**:
```bash
# PDF with images requires OCR (tesseract)
# Install tesseract
brew install tesseract  # macOS
apt-get install tesseract-ocr  # Linux

# Then retry extraction
bloginator extract ~/Documents -o corpus
```

---

### 7. Batch Mode Stale File Errors

**Symptoms**:
```
Error: Response file not found: llm_responses/batch_12345.json
Error: Batch timeout waiting for responses
FileNotFoundError: .bloginator/llm_requests/batch_67890.json
```

**Diagnosis**:
```bash
# Check for orphaned files
ls -la .bloginator/llm_requests/
ls -la .bloginator/llm_responses/

# Check timestamps (should be recent)
ls -lrt .bloginator/llm_requests/ | tail -5
```

**Solutions**:

**If response file missing**:
```bash
# Check request file exists
ls .bloginator/llm_requests/batch_12345.json

# If missing both, re-run generation
rm -rf .bloginator/llm_requests .bloginator/llm_responses
bloginator outline --index .bloginator/chroma \
  --title "Topic" --keywords "key1,key2" \
  --batch
```

**If stale files from previous runs**:
```bash
# Clean up old requests/responses
find .bloginator/llm_requests -mtime +1 -delete  # Files >24h old
find .bloginator/llm_responses -mtime +1 -delete

# Or do full cleanup
rm -rf .bloginator/llm_requests .bloginator/llm_responses
mkdir -p .bloginator/llm_requests .bloginator/llm_responses
```

**If batch times out**:
```bash
# Increase timeout
bloginator outline --index .bloginator/chroma \
  --title "Topic" --keywords "key1,key2" \
  --batch --batch-timeout 120  # 2 minutes instead of 60s

# Or use interactive mode instead
BLOGINATOR_LLM_MOCK=interactive bloginator outline \
  --index .bloginator/chroma \
  --title "Topic" --keywords "key1,key2"
```

---

### 8. High Memory Usage / Slow Performance

**Symptoms**:
- `bloginator index` using >4GB RAM
- `bloginator draft` taking 10+ minutes
- System becomes unresponsive

**Diagnosis**:
```bash
# Monitor while running
watch -n 1 'ps aux | grep bloginator'

# Check memory by process
ps aux | grep bloginator | awk '{print $6}'

# Profile code
python -m cProfile -o /tmp/stats.prof -m \
  bloginator.cli.main draft outline.json -o draft.md
snakeviz /tmp/stats.prof
```

**Solutions**:

**For indexing**:
```bash
# Index with smaller batch size
bloginator index corpus -o .bloginator/chroma \
  --batch-size 25  # Instead of 100

# Or index multiple times with subset of corpus
mkdir corpus-1 corpus-2
split corpus corpus-1 corpus-2

bloginator index corpus-1 -o .bloginator/chroma
bloginator index corpus-2 -o .bloginator/chroma  # Appends
```

**For generation**:
```bash
# Limit search results (uses less context)
bloginator draft outline.json -o draft.md \
  --max-search-results 5  # Instead of 10

# Use faster model
export BLOGINATOR_LLM_MODEL=llama2  # Instead of llama3

# Reduce outline complexity
# (Edit outline.json to have fewer sections)
```

**For search**:
```bash
# Use BM25 mode (faster than semantic)
bloginator search --index .bloginator/chroma \
  --mode bm25 "query" -n 10
```

---

### 9. Docker/Container Deployment Issues

**Symptoms**:
- Container exits immediately
- Can't find index in container
- File permissions errors
- Port already in use

**Solutions**:

**Index not found**:
```bash
# Mount index directory
docker run -v $(pwd)/.bloginator:/app/.bloginator \
  bloginator:latest \
  search --index .bloginator/chroma "query"
```

**Port already in use**:
```bash
# Use different port
docker run -p 8001:8000 bloginator:latest serve

# Or kill existing container
docker kill $(docker ps | grep bloginator | awk '{print $1}')
```

**File permissions**:
```bash
# Run with same user ID as host
docker run --user $(id -u):$(id -g) \
  -v $(pwd):/workspace \
  bloginator:latest \
  extract /workspace/corpus -o /workspace/output
```

---

### 10. Troubleshooting Workflow

When something breaks:

```bash
# 1. Collect diagnostics
echo "=== Environment ===" > /tmp/diagnostics.txt
env | grep -i bloginator >> /tmp/diagnostics.txt
python --version >> /tmp/diagnostics.txt
pip list | grep -E "bloginator|chromadb|sentence-transformers" >> /tmp/diagnostics.txt

echo "=== System ===" >> /tmp/diagnostics.txt
df -h >> /tmp/diagnostics.txt
free -h >> /tmp/diagnostics.txt
ps aux | grep bloginator >> /tmp/diagnostics.txt

echo "=== Configuration ===" >> /tmp/diagnostics.txt
ls -la .bloginator/ >> /tmp/diagnostics.txt
cat .env | grep -v "API_KEY\|PASSWORD" >> /tmp/diagnostics.txt

# 2. Run command with debug output
BLOGINATOR_DEBUG=1 PYTHONUNBUFFERED=1 \
  bloginator outline --index .bloginator/chroma \
    --title "Test" --keywords "test" > /tmp/debug.log 2>&1

# 3. Review logs
cat /tmp/debug.log | tail -50

# 4. Check .bloginator logs
ls -lrt .bloginator/logs/
tail -100 .bloginator/logs/latest.log

# 5. Collect for support
cat /tmp/diagnostics.txt /tmp/debug.log > /tmp/issue-report.txt
```

---

## Performance Tuning

### Baseline Expectations

| Operation | Time | RAM | Notes |
|-----------|------|-----|-------|
| `init` | 10-60s | 500MB | Downloads embedding model |
| `extract` (per doc) | 1-10s | 100MB | Depends on file size |
| `index` (100 docs) | 5-30s | 1GB | First run slower |
| `search` | <1s | 100MB | After index ready |
| `outline` | 30-90s | 800MB | Depends on LLM |
| `draft` | 1-5min | 1GB | Depends on LLM speed |

### Optimization Checklist

```bash
# 1. Use SSD for .bloginator/
# 2. Allocate 4GB+ RAM
# 3. Use fast LLM (llama3 > llama2)
# 4. Use local LLM (Ollama) instead of cloud
# 5. Limit search results to 5-10 documents
# 6. Index with batch-size 50-100
```

---

## Maintenance Schedule

### Daily
- Monitor `.bloginator/logs/` for errors
- Check available disk space

### Weekly
- Run full test suite: `pytest tests/ --cov=src/bloginator`
- Verify index health: `bloginator search .bloginator/chroma "test" -n 5`

### Monthly
- Update dependencies: `pip install -e ".[dev]" --upgrade`
- Rebuild index from fresh corpus (if memory permits)
- Review generated content quality

### Quarterly
- Test disaster recovery (restore from backups)
- Review REPO_HOLES.md for new issues
- Plan infrastructure upgrades if needed

---

## Escalation & Support

### When to Escalate

1. **Memory exhaustion** (>10GB)
2. **Disk full** (<1GB free)
3. **LLM API costs** (>$100/month)
4. **Index corruption** (can't rebuild)
5. **Repeated timeouts** (>30% failure rate)

### Gathering Info for Support

```bash
./scripts/collect-diagnostics.sh > /tmp/diagnostics.txt
# (Script not yet created - can be added later)

cat /tmp/diagnostics.txt | head -100
```

### Resources

- **Docs**: See `docs/` directory
- **Issues**: GitHub Issues for bug reports
- **Community**: Discussions for questions
- **Email**: matt@bordenet.com for urgent issues
