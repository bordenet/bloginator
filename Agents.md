# AI Agent Guidelines - Bloginator

> **Last Updated:** 2026-02-02
> **Languages:** python
> **Type:** cli-tools

<!-- GOLDEN:framework:start -->

## Superpowers Bootstrap

At the START of every conversation, run:

```bash
node ~/.codex/superpowers-augment/superpowers-augment.js bootstrap
```

**Key skills:**
| Skill | When to Use |
|-------|-------------|
| `superpowers:brainstorming` | Before creative/feature work |
| `superpowers:systematic-debugging` | Before fixing bugs |
| `superpowers:test-driven-development` | Before writing implementation |
| `superpowers:verification-before-completion` | Before claiming done |

---

## Anti-Slop Rules

- **No flattery** - Skip "Great question!"
- **No hype** - Avoid "revolutionary", "game-changing"
- **Evidence-based** - Cite sources or qualify as opinion
- **Direct** - State facts without embellishment

---

## Quality Gates (Python)

```bash
./scripts/run-fast-quality-gate.sh  # Quick check
pytest tests/ --cov=src/bloginator --cov-fail-under=85  # Full
```

<!-- GOLDEN:framework:end -->

---

## 🚨 CRITICAL: Progressive Guidance Modules

**This project has extensive AI guidance.** Load modules on-demand based on your task.

| Module | When to Load | Command |
|--------|--------------|---------|
| **corpus-rules.md** | 🔴 ALWAYS before ANY content generation | `view .ai-guidance/corpus-rules.md` |
| **llm-backend.md** | When generating blog content or acting as LLM | `view .ai-guidance/llm-backend.md` |
| **batch-generation.md** | When using batch mode for blogs | `view .ai-guidance/batch-generation.md` |
| **autonomous-generation.md** | When generating blogs autonomously | `view .ai-guidance/autonomous-generation.md` |
| **quality-gates.md** | Before commits, PRs, or quality checks | `view .ai-guidance/quality-gates.md` |
| **commands.md** | When running CLI or debugging | `view .ai-guidance/commands.md` |
| **repo-structure.md** | When working on project organization | `view .ai-guidance/repo-structure.md` |
| **troubleshooting.md** | When debugging process/terminal issues | `view .ai-guidance/troubleshooting.md` |

### ⛔ CRITICAL RULE

**Before generating ANY blog content, you MUST load `corpus-rules.md`.**
This is non-negotiable. Failure to load this module will result in AI slop that defeats the project's purpose.

---

## Project Overview

**Bloginator** generates blog content from a user's knowledge corpus using RAG search and voice matching.

**Key principle:** NEVER bypass the corpus. All content must be synthesized from corpus search results, not training data.

**LLM Mode:** Claude acts as the LLM backend via `BLOGINATOR_LLM_MOCK=assistant` - this is the normal workflow.

---

## Quick Start

```bash
# Activate environment
source venv/bin/activate

# Run quality checks
./scripts/run-fast-quality-gate.sh

# Search corpus
bloginator search .bloginator/chroma "your query" -n 5

# Generate blog (as LLM backend)
BLOGINATOR_LLM_MOCK=assistant bloginator outline --index .bloginator/chroma \
    --title "Topic" --keywords "key1,key2" -o outline.json
# Then read requests from .bloginator/llm_requests/ and respond
```

---

*For detailed guidance, load the appropriate module from `.ai-guidance/`.*
