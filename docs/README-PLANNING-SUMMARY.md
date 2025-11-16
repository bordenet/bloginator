# Bloginator - Planning Summary & Implementation Roadmap

**Project Status**: Planning Complete, Ready for Implementation
**Created**: 2025-11-16
**Target Start**: Mid-week (New Job)
**Estimated Duration**: 8 weeks (Phases 0-7)

---

## Executive Summary

Bloginator is an AI-assisted content generation system that helps engineering leaders create authentic, high-quality documents by leveraging their historical writing corpus. The system prevents "AI slop" by grounding all generation in actual prior writing, maintains author's authentic voice, and protects against proprietary content leakage.

**Key Differentiators**:
- ✅ Voice preservation (not generic AI output)
- ✅ Corpus-grounded generation (no hallucinations)
- ✅ Proprietary content protection (blocklist enforcement)
- ✅ Two deployment modes (cloud API + fully local)
- ✅ Cost controls (cloud mode)
- ✅ Privacy-first architecture

---

## Documentation Overview

### Core Planning Documents

1. **[PRD-BLOGINATOR-001-Core-System.md](./PRD-BLOGINATOR-001-Core-System.md)** (18,000 words)
   - Complete problem statement and user stories
   - Success metrics and goals
   - Technical design (high-level)
   - Risk mitigation strategies
   - Example workflows

2. **[DESIGN-SPEC-001-Implementation-Plan.md](./DESIGN-SPEC-001-Implementation-Plan.md)** (25,000 words)
   - Detailed phase-by-phase implementation plan
   - Per-phase deliverables and acceptance criteria
   - Code examples and data models
   - Validation checklists
   - Technology stack decisions

3. **[ARCHITECTURE-002-Deployment-Modes.md](./ARCHITECTURE-002-Deployment-Modes.md)** (12,000 words)
   - Cloud mode vs. Local mode separation
   - Component architecture (common vs. mode-specific)
   - LLM abstraction layer design
   - Cost control measures (cloud mode)
   - Configuration and mode selection

4. **[TESTING-SPEC-003-Quality-Assurance.md](./TESTING-SPEC-003-Quality-Assurance.md)** (15,000 words)
   - Comprehensive testing strategy (unit, integration, E2E)
   - Quality gates and pre-commit hooks
   - CI/CD pipeline configuration
   - Performance benchmarks
   - Cost control tests

5. **[CLAUDE_GUIDELINES.md](./CLAUDE_GUIDELINES.md)** (8,000 words)
   - Mandatory quality gates (pre-commit, testing, linting)
   - Cost control requirements
   - Bloginator-specific principles
   - Anti-patterns to avoid
   - Response guidelines for AI assistants

**Total Planning Documentation**: ~78,000 words (150+ pages)

---

## Project Scope

### In Scope (Phases 0-7)

**Phase 0: Project Setup** (Week 1, Days 1-2)
- Repository initialization
- Dependency configuration
- Pre-commit hooks
- Import reusable components from Films Not Made

**Phase 1A: Cloud Mode (Claude)** (Weeks 1-3)
- Document extraction and indexing
- Semantic search with weighting
- Blocklist and safety layer
- CloudLLMProvider (Claude)
- Generation engine (outline, draft)
- Cost controls
- CLI tools

**Phase 1B: Cloud Mode (OpenAI)** (Week 4)
- OpenAI implementation
- Prompt optimization for GPT-4
- Side-by-side testing

**Phase 2: Local Mode** (Weeks 5-6)
- LocalLLMProvider (Ollama)
- Prompt optimization for Llama3/Mistral
- Performance benchmarking

**Phase 3: Refinement & Iteration** (Part of Weeks 3-6)
- Iterative refinement engine
- Version management
- Diff visualization

**Phase 4: Web UI** (Weeks 7-8)
- Web interface for both modes
- Mode switching
- Cost dashboard (cloud)
- Model management (local)

**Phase 5: External Sources & Polish** (Week 8+)
- External source support with attribution
- Template library
- Advanced search features
- Production documentation

### Out of Scope (Future Releases)

- Multi-user collaboration
- Real-time collaborative editing
- Version control systems integration
- Publishing automation (Medium, LinkedIn)
- Analytics and performance tracking
- Visual asset generation (diagrams)
- Mobile applications
- Hybrid mode (cloud + local)
- Multi-model ensemble

---

## Technology Stack

### Common Infrastructure (Both Modes)

```
Extraction:
  - PyMuPDF (PDF)
  - python-docx (DOCX)
  - Native (Markdown, TXT)
  - zipfile (ZIP archives)

Indexing:
  - ChromaDB (vector store)
  - sentence-transformers (all-MiniLM-L6-v2)
  - torch (for embeddings)

Search:
  - ChromaDB similarity search
  - Custom recency/quality weighting

Safety:
  - Custom blocklist implementation
  - Regex pattern matching

CLI:
  - Click (framework)
  - Rich (formatting)

Data Models:
  - Pydantic v2

Configuration:
  - YAML (config files)
  - Environment variables
```

### Cloud Mode Specific

```
LLM APIs:
  - anthropic>=0.25.0 (Claude)
  - openai>=1.0.0 (OpenAI)
  - tiktoken (OpenAI token counting)

Cost Control:
  - Custom implementation
```

### Local Mode Specific

```
LLM:
  - ollama>=0.1.0 (Ollama client)
  - Models: llama3:8b, mistral, etc.
```

### Development Tools

```
Quality:
  - black (formatting)
  - ruff (linting)
  - mypy (type checking)
  - isort (import sorting)

Testing:
  - pytest
  - pytest-cov
  - pytest-mock

Security:
  - gitleaks (secret detection)
  - bandit (security linting)

Pre-commit:
  - pre-commit framework
  - Custom validation hooks
```

### Web UI (Phase 4)

```
Backend:
  - Flask or FastAPI
  - WebSocket (progress updates)

Frontend:
  - HTML/CSS/JavaScript
  - Modern responsive design
  - No heavy framework (keep it simple)
```

---

## Implementation Sequence

### Phase Progression

```
Week 1:
  Days 1-2: Phase 0 (Setup)
  Days 3-5: Phase 1 - Extraction & Indexing

Week 2:
  Days 1-3: Phase 2 - Search & Retrieval
  Days 4-5: Phase 3 - Blocklist & Safety

Week 3:
  All week: Phase 4 - Content Generation (Cloud/Claude)

Week 4:
  All week: Phase 1B - OpenAI Integration + Testing

Weeks 5-6:
  Phase 2 (Local Mode) + Refinement Engine

Weeks 7-8:
  Web UI + External Sources + Polish
```

### Critical Path

```
Setup → Extraction → Indexing → Search → Blocklist → Generation (Claude) → Testing
                                                              ↓
                                                          OpenAI Integration
                                                              ↓
                                                          Local Mode
                                                              ↓
                                                          Web UI
```

### Parallel Work Streams

Some components can be developed in parallel:
- Search refinement while building generation
- OpenAI integration while testing Claude
- Web UI mockups while building backend

---

## Quality Requirements

### Code Quality Gates (Every Commit)

**Pre-Commit Hooks** (Automated):
1. ✅ Black formatting (line-length=100)
2. ✅ Ruff linting
3. ✅ MyPy type checking (strict mode)
4. ✅ Import sorting (isort)
5. ✅ Gitleaks (secret detection)
6. ✅ Fast unit tests (<5s)
7. ✅ Docstring validation

**Validation Script** (`./validate-bloginator.sh`):
- All pre-commit checks
- Full test suite
- Coverage check (≥80%)
- Security scanning

### Test Coverage Requirements

**Minimum Coverage**: 80% line coverage

**Per-Module Requirements**:
- Safety/Blocklist: 90%+ (critical)
- All other modules: 80%+

**Test Distribution**:
- 60% unit tests (fast, isolated)
- 30% integration tests
- 10% E2E tests

### Performance Benchmarks

| Operation | Target | Critical? |
|-----------|--------|-----------|
| Index 500 docs | <30 min | Yes |
| Search query | <3s | Yes |
| Outline (cloud) | <10s | No |
| Draft (cloud) | <60s | No |
| Draft (local) | <120s | No |
| Blocklist check | <1s | Yes |

---

## Cost Controls (Cloud Mode)

### Default Limits

- **Per-session limit**: $5.00 USD
- **Per-operation warning**: $1.00+
- **Per-operation confirmation**: $2.00+
- **Test suite limit**: <$1.00 per full run

### Implementation

All cloud LLM calls MUST:
1. ✅ Estimate cost before calling API
2. ✅ Display estimate to user
3. ✅ Check against session limit
4. ✅ Track actual usage
5. ✅ Display running total

### Budget Profiles

```yaml
experimental:
  limit: $1.00
  model: claude-3-haiku-20240307

standard:
  limit: $5.00
  model: claude-3-5-sonnet-20241022

production:
  limit: $20.00
  model: claude-3-5-sonnet-20241022
```

---

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Voice preservation quality | Medium | High | Extensive testing, similarity scoring, iterative improvement |
| LLM hallucination | Medium | High | RAG-first, source attribution, validation |
| Blocklist evasion | Low | High | Multiple validation layers, fuzzy matching |
| Cost overruns (cloud) | Medium | Medium | Hard limits, estimation, user confirmation |
| Performance (local) | Medium | Low | Optimize prompts, support remote Ollama |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | High | High | Strict phase gating, defer non-essential features |
| Over-engineering | Medium | Medium | Follow CLAUDE_GUIDELINES principles |
| Integration complexity | Low | Medium | Reuse Films Not Made patterns |

### Mitigation Strategies

1. **Voice Preservation**: Blind testing with author's past work, similarity scoring
2. **Hallucination**: RAG-only generation, source attribution, confidence scoring
3. **Blocklist**: Multiple validation layers, fuzzy matching, user review
4. **Cost**: Hard limits, estimation, cheaper models for tests
5. **Scope**: Clear phase deliverables, defer Phase 5+ features if needed

---

## Success Criteria

### Phase Completion Criteria

Each phase is complete when:
1. ✅ All acceptance criteria met
2. ✅ Tests pass with ≥80% coverage
3. ✅ Code passes all quality gates
4. ✅ Documentation updated
5. ✅ Validation checklist completed
6. ✅ Demo recorded (for major phases)

### Project Completion Criteria

Project is complete when:
1. ✅ All 7 phases delivered
2. ✅ End-to-end workflow works in both modes
3. ✅ Voice preservation scores >0.7
4. ✅ Blocklist enforcement at 100% (exact matches)
5. ✅ Performance meets or exceeds benchmarks
6. ✅ User can create document in <60 min (cloud mode)
7. ✅ Comprehensive documentation published
8. ✅ CI/CD pipeline configured

### Acceptance Testing

**Workflow Test** (Cloud Mode):
```
1. Upload corpus (100 documents)
2. Extract and index (<10 min)
3. Search for concept (returns relevant results)
4. Add blocklist entries (company names)
5. Generate outline (keywords + thesis)
6. Generate draft from outline
7. Verify draft:
   - Voice similarity >0.7
   - No blocklist violations
   - Proper source attribution
   - Cost <$1
8. Refine draft (natural language feedback)
9. Export to Markdown and DOCX
```

**Workflow Test** (Local Mode):
```
Same as cloud mode, but:
- Use Ollama (llama3:8b)
- No cost tracking
- Acceptable latency (<120s for draft)
```

---

## Deployment Modes Comparison

### Cloud Mode (Phase 1)

**Pros**:
- ✅ Fast setup (API key only)
- ✅ High-quality output (Claude Sonnet 3.5)
- ✅ Fast inference (cloud GPUs)
- ✅ No local compute requirements

**Cons**:
- ❌ Ongoing API costs
- ❌ Internet required
- ❌ Data sent to Anthropic/OpenAI
- ❌ Privacy concerns for sensitive content

**Best For**:
- Quick start and experimentation
- Occasional use
- Users without powerful local hardware

### Local Mode (Phase 2)

**Pros**:
- ✅ 100% local processing
- ✅ No ongoing costs
- ✅ Complete privacy
- ✅ No internet required

**Cons**:
- ❌ Requires Ollama installation
- ❌ Requires model downloads (4-7GB)
- ❌ Slower inference (depends on hardware)
- ❌ Lower quality (vs. Claude Sonnet 3.5)

**Best For**:
- Privacy-critical content
- Heavy usage (cost-conscious)
- Users with powerful hardware
- Offline environments

---

## Getting Started (Implementation)

### Week 1, Day 1: Setup

```bash
# 1. Create repository
mkdir bloginator
cd bloginator
git init

# 2. Copy planning documents
cp -r /path/to/films-not-made/docs/bloginator/* ./docs/

# 3. Initialize project structure
# (See DESIGN-SPEC-001, Phase 0)

# 4. Setup pre-commit hooks
pip install pre-commit
pre-commit install

# 5. Validate setup
./validate-bloginator.sh
```

### Week 1, Days 2-5: Phase 1 (Extraction & Indexing)

Follow DESIGN-SPEC-001, Phase 1 implementation plan.

**Key Deliverables**:
- Document extraction pipeline
- ChromaDB indexing
- Metadata management
- CLI commands (extract, index)
- Tests with 80%+ coverage

---

## Reusable Components from Films Not Made

### Direct Reuse (Minimal Changes)

1. **Extraction Pipeline**:
   - `src/fnm/extraction/` → `src/bloginator/extraction/`
   - PDF, DOCX, MD, TXT extractors
   - Change: Add metadata extraction

2. **Chunking Strategies**:
   - `src/fnm/chunking/` → `src/bloginator/chunking/`
   - Change: Add paragraph-based chunking for blog posts

3. **CLI Framework**:
   - `src/fnm/cli/main.py` → `src/bloginator/cli/main.py`
   - Click structure, Rich formatting
   - Change: Bloginator-specific commands

4. **Test Utilities**:
   - `tests/conftest.py`
   - Fixtures and helpers
   - Change: Bloginator test data

### Adapt and Extend

1. **Indexing**:
   - Reuse ChromaDB integration
   - Add metadata filtering
   - Add recency/quality weighting

2. **Search**:
   - Reuse semantic search
   - Add combined scoring
   - Add advanced filters

3. **Validation Scripts**:
   - Adapt `validate-monorepo.sh` → `validate-bloginator.sh`
   - Adapt `.pre-commit-config.yaml`

### New Components (No Reuse)

1. **LLM Integration**:
   - CloudLLMProvider (Claude, OpenAI)
   - LocalLLMProvider (Ollama)
   - LLM abstraction layer

2. **Voice Preservation**:
   - Voice similarity scoring
   - Style analysis
   - Characteristic phrase detection

3. **Blocklist System**:
   - BlocklistManager
   - Pattern matching (exact, regex, case-insensitive)
   - Validation layer

4. **Cost Control**:
   - Token counting
   - Cost estimation
   - Session tracking
   - User confirmation

5. **Refinement Engine**:
   - Natural language feedback parsing
   - Targeted regeneration
   - Diff computation
   - Version management

---

## Key Decision Points

### Decisions Made

1. **Two deployment modes** (cloud + local)
   - Rationale: Different use cases, user preferences
   - Trade-off: More implementation complexity

2. **ChromaDB for vector store**
   - Rationale: Persistent, local-first, good performance
   - Alternative considered: FAISS (less features)

3. **sentence-transformers for embeddings**
   - Rationale: Local, good quality, fast
   - Always local (even in cloud mode) for privacy

4. **Pydantic v2 for data models**
   - Rationale: Validation, serialization, type safety
   - Migration from Films Not Made patterns

5. **Click for CLI framework**
   - Rationale: Familiar, good ecosystem
   - Reuse from Films Not Made

6. **Pre-commit hooks mandatory**
   - Rationale: Enforce quality from day 1
   - No bypassing (except emergencies)

7. **80% test coverage minimum**
   - Rationale: Balance rigor and velocity
   - 90% for safety-critical code

8. **Cost limits mandatory (cloud mode)**
   - Rationale: Prevent surprise bills
   - Default $5/session

### Open Questions (To Be Decided During Implementation)

1. **Template format**: LLM prompts, schemas, or example docs?
   - Defer to Phase 5
   - Start with simple prompt templates

2. **Version control**: Git-like or session-based?
   - Start with session-based (simpler)
   - Evaluate git-like in Phase 5

3. **Multi-author support**: Single author or multiple?
   - Phase 1-4: Single author only
   - Phase 5+: Consider multi-author

4. **Export citations**: Inline, footnotes, or removed?
   - Make it configurable
   - Default: inline (removable)

5. **Incremental corpus updates**: Manual or watch folder?
   - Phase 1-4: Manual re-upload
   - Phase 5+: Consider watch folder

---

## Communication Plan

### Status Updates

**Weekly**:
- Phase completion status
- Blockers and risks
- Next week's goals

**Per-Phase**:
- Demo video
- Validation checklist results
- Lessons learned

### Documentation Maintenance

**Continuous**:
- Update README with latest instructions
- Document any deviations from plan
- Track open questions and decisions

**Per-Phase**:
- Update architecture docs with actual implementation
- Record performance benchmarks
- Update testing docs with actual coverage

---

## Next Steps

### Immediate (This Week)

1. **Create new repository**: `bloginator`
2. **Copy planning documents**: Move `docs/bloginator/` to new repo
3. **Setup project structure**: Follow Phase 0 implementation plan
4. **Verify reusable components**: Test extraction pipeline from Films Not Made
5. **Configure pre-commit hooks**: Ensure all quality gates work

### Week 1 Goals

- ✅ Complete Phase 0 (Setup)
- ✅ Complete Phase 1, Task 1.1-1.2 (Document models, metadata extraction)
- ✅ Start Phase 1, Task 1.3 (Indexing with metadata)
- ✅ All tests passing, coverage ≥80%

### Week 2 Goals

- ✅ Complete Phase 1 (Extraction & Indexing)
- ✅ Complete Phase 2 (Search & Retrieval)
- ✅ Start Phase 3 (Blocklist)

### Week 3 Goals

- ✅ Complete Phase 3 (Blocklist)
- ✅ Complete Phase 4 (Generation - Claude)
- ✅ End-to-end workflow test (cloud mode)

---

## Appendix: Files to Migrate to New Repo

### From Films Not Made Repository

**Documentation** (copy, then adapt):
1. `docs/bloginator/PRD-BLOGINATOR-001-Core-System.md`
2. `docs/bloginator/DESIGN-SPEC-001-Implementation-Plan.md`
3. `docs/bloginator/ARCHITECTURE-002-Deployment-Modes.md`
4. `docs/bloginator/TESTING-SPEC-003-Quality-Assurance.md`
5. `docs/bloginator/CLAUDE_GUIDELINES.md`
6. `docs/bloginator/README-PLANNING-SUMMARY.md` (this file)

**Code** (copy, then adapt):
- TBD: Will copy during Phase 0 implementation

### Which Documents to Take

**Per user request**: "We will take exactly TWO documents from here and move them to a new repo."

**Recommendation**:

1. **DEVELOPER_GUIDE.md** (adapt for Bloginator)
   - Coding conventions
   - Testing standards
   - Validation scripts
   - Architecture patterns

2. **README.md** (adapt for Bloginator)
   - Project overview
   - Quick start
   - Installation instructions
   - Feature list

These two documents, combined with the 6 planning documents already in `docs/bloginator/`, will provide complete documentation for the new Bloginator project.

---

## Contact & Support

**Primary Contact**: Matt Bordenet
**Project Start**: Mid-week (new job)
**Priority**: High (production use case)

---

*End of Planning Summary*
