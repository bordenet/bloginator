# AI Agent Guidelines - Bloginator

> **Last Updated:** 2026-02-02
> **Languages:** python
> **Type:** cli-tools
<!-- GOLDEN:self-manage:start -->
## ⚠️ Before ANY Task
1. Load `.ai-guidance/invariants.md` — contains critical rules
2. After editing ANY guidance file, check: `wc -l AGENTS.md .ai-guidance/*.md 2>/dev/null`
   - `AGENTS.md` >250 lines → refactor into `.ai-guidance/`
   - Any `.ai-guidance/*.md` >250 lines → split into sub-directory
3. Over the limit, draft a diff. Do not apply it. A human merges it.
<!-- GOLDEN:self-manage:end -->
<!-- golden-agents:stamp version=1.4.0 updated=2026-11-13 -->
<!-- golden-agents:modules python=0e3e36e76bbebc463c7dca7e512f93d13eca07baa8a9c234dfab02ade1e1247e security=1ac770a3537cafe41a39200b507aaa0b4c6a52f2d978d3c9d6be1b44a91687a3 testing=4f99d896d81c026019fbe4e2682baf1ae0bda9cec0ce1c690be6a95d54781509 build-hygiene=17a6efa17673d4e31ff352f4f1a83cb6aab5a9f8804c7e530e1d23677142be86 deployment=738982f51f7ceb856fb3aea9d97236de6725440e04d112cbd1b7ec276c116be8 cli-tools=d999ec7ef38441c0b11517692162d6a94d0434f06e89664aa62feb5f6da63154 -->
<!-- GOLDEN:framework:start -->

---

## Quality Gates

Before a commit:
1. **Lint**: `ruff check .`
2. **Build**: `pip install -e .`
3. **Test**: `pytest`
4. **Coverage**: Minimum 70%

Lint, then build, then test. Run the same commands in CI or a hook.

---

## Communication Rules

- **No flattery** - Skip "Great question!" or "Excellent point!"
- **No hype** - Avoid "revolutionary", "game-changing", "seamless"
- **Evidence-based** - Cite sources or qualify as opinion
- **Direct** - State facts without embellishment

**Banned phrases**: production-grade, world-class, leverage, utilize, incredibly, extremely, Happy to help!

---

## 🚨 Progressive Module Loading

**STOP and load the relevant module BEFORE these actions:**

### Language Modules (🔴 Required)
- 🔴 **BEFORE writing ANY `.py` file**: Read `.golden-agents/modules/python.md`

### Workflow Modules (🔴 Required)
- 🔴 **BEFORE any commit, PR, push, or merge**: Read `.golden-agents/modules/security.md`
- 🔴 **WHEN tests fail OR after 2+ failed fix attempts**: Read `.golden-agents/modules/testing.md`
- 🔴 **WHEN build fails OR lint errors appear**: Read `.golden-agents/modules/build-hygiene.md`
- 🟡 **BEFORE deploying to any environment**: Read `.golden-agents/modules/deployment.md`

### Project type guidance:
- Read `.golden-agents/modules/cli-tools.md`

<!-- GOLDEN:framework:end -->

### Optional: Superpowers integration

If [superpowers](https://github.com/obra/superpowers) is installed, run at session start:

```bash
node ~/.codex/superpowers-augment/superpowers-augment.js bootstrap
```

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
