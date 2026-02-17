# AI Agent Guidelines - Bloginator

> **Last Updated:** 2026-02-02
> **Languages:** python
> **Type:** cli-tools
<!-- GOLDEN:self-manage:start -->
## ⚠️ Before ANY Task
1. Load `.ai-guidance/invariants.md` — contains critical rules
2. After editing ANY guidance file, check: `wc -l Agents.md .ai-guidance/*.md 2>/dev/null`
   - `Agents.md` >150 lines → refactor into `.ai-guidance/`
   - Any `.ai-guidance/*.md` >250 lines → split into sub-directory
<!-- GOLDEN:self-manage:end -->
<!-- GOLDEN:framework:start -->

---

## Quality Gates (MANDATORY)

Before ANY commit:
1. **Lint**: `ruff check .`
2. **Build**: `pip install -e .`
3. **Test**: `pytest`
4. **Coverage**: Minimum 70%

**Order matters.** Lint → Build → Test. Never skip steps.

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
- 🔴 **BEFORE writing python code**: Read `$HOME/.golden-agents/templates/languages/python.md`

### Workflow Modules (🔴 Required)
- 🔴 **BEFORE any commit, PR, push, or merge**: Read `$HOME/.golden-agents/templates/workflows/security.md`
- 🔴 **WHEN tests fail OR after 2+ failed fix attempts**: Read `$HOME/.golden-agents/templates/workflows/testing.md`
- 🔴 **WHEN build fails OR lint errors appear**: Read `$HOME/.golden-agents/templates/workflows/build-hygiene.md`
- 🟡 **BEFORE deploying to any environment**: Read `$HOME/.golden-agents/templates/workflows/deployment.md`
- 🟡 **WHEN conversation exceeds 50 exchanges**: Read `$HOME/.golden-agents/templates/workflows/context-management.md`

### Project type guidance:
- Read `$HOME/.golden-agents/templates/project-types/cli-tools.md`

### Optional: Superpowers integration

If [superpowers](https://github.com/obra/superpowers) is installed, run at session start:

```bash
node ~/.codex/superpowers-augment/superpowers-augment.js bootstrap
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
