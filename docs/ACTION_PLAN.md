# Bloginator Action Plan

Active work items and incomplete features.

---

## Corpus Management

**Priority**: HIGH

### Corpus Source Management (✅ COMPLETE)
- ✅ **Add source form** with name, path, quality, tags, voice notes
- ✅ **Path helper buttons** - Home, Current Dir, Desktop
- ✅ **Delete source** from corpus.yaml with list filtering
- ✅ **Prune index** - remove documents from deleted sources
- ✅ **Delete index** - full reset without losing source config
- ⚠️ **Write tests** for corpus management UI functions (MISSING)

**Status**: Implemented in `src/bloginator/ui/_pages/corpus.py` but lacks unit/integration tests

### Corpus Upload Feature (📁 Design Phase - BLOCKED)
- [ ] **Implement corpus_upload_manager.py** service with file validation, storage, and YAML updates
- [ ] **Add "Add Sources" tab** to Streamlit UI with file uploader and metadata collection
- [ ] **Add "Manage Sources" section** with delete/edit/view functionality
- [ ] **Write unit tests** for upload manager (target: 95%+ coverage)
- [ ] **Write integration tests** for full upload→storage→YAML workflow
- [ ] **Test YAML corruption recovery** - verify backup/restore on failures
- [ ] **UI Testing** - manual verification of upload widget and forms
- [ ] **E2E Testing** - upload files → extract → search full workflow

**Docs**: See `docs/CORPUS_UPLOAD_REQUIREMENTS.md`, `docs/CORPUS_UPLOAD_DESIGN.md`, `docs/CORPUS_UPLOAD_TEST_PLAN.md`

---

## Test Coverage

**Current**: ~76% (CI enforces 70% minimum)
**Target**: 80%+

### High-Priority Coverage Gaps
- [ ] CLI commands: `draft.py`, `extract_config.py`, `extract_single.py`, `history.py`, `outline.py`, `search.py`, `serve.py`, `template.py`
- [ ] Utilities: `checksum.py` (40% coverage), `parallel.py` edge cases
- [ ] Web routes (if extras enabled): `web/routes/*.py`
- [ ] PDF export tests (skipped - requires reportlab)

### Coverage Strategy
- [ ] Add realistic E2E tests for each CLI command
- [ ] Focus on edge cases and error paths, not just happy path
- [ ] Use fixtures to reduce test boilerplate

---

## Known Gaps

### Specificity in Generated Content
Generated content scores 3.87-4.94/5.0 on specificity dimension.
- [ ] Enhance prompts with more concrete examples and metrics guidance
- [ ] Consider implementing SpecificityExtractor helper (see OPTIMIZATION_LEARNINGS.md)
- [ ] Run extended 30-50 round optimization for convergence

### Voice Preservation
Current voice similarity scoring works, but needs improvement.
- [ ] Consider training custom embedding model on user's corpus
- [ ] Explore style transfer techniques
- [ ] Add "voice intensity" slider for RAG influence control

### Performance Optimization
- [ ] Profile extraction, indexing, and search operations
- [ ] Identify slow paths (especially for large corpora)
- [ ] Benchmark generation latency

---

## Documentation

- [ ] Keep README synchronized with actual features and CLI
- [ ] Update coverage badge when coverage changes materially (±3-5%)
- [ ] Prune completed items from ACTION_PLAN.md periodically

---

## Future Work

See `docs/FUTURE_WORK.md` for longer-term initiatives:
- Plugin architecture
- Collaborative features
- Cloud provider support (OpenAI, Anthropic integrations)
- Advanced search & retrieval (hybrid search, re-ranking)
- Incremental learning from user feedback
- Mobile & desktop apps
- Academic and technical documentation use cases
