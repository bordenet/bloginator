# Bloginator: Future Work & Extensibility

This document outlines potential enhancements and extensibility plans for Bloginator.

**Note:** Items marked [DONE] have been implemented and remain here for historical context.

---

## Completed Short-Term Items

### [DONE] Export CLI Command

Implemented in `src/bloginator/cli/export.py`. Users can now run:

```bash
bloginator export draft.md --format pdf -o output.pdf
```

### [DONE] Hybrid Search (BM25 + Semantic)

Implemented in `src/bloginator/search/bm25.py` and `searcher.py`:

- BM25 lexical scoring via `BM25Index` class
- Hybrid search combining semantic similarity with BM25
- Configurable weights for semantic vs. keyword matching

### [DONE] OpenAI Native Client

Implemented in `src/bloginator/generation/llm_openai.py`:

- Native OpenAI SDK integration
- Supports GPT-4o (default), GPT-4, GPT-3.5-turbo
- Optional dependency: `pip install bloginator[cloud]`

---

## Short-Term Improvements

### 1. Advanced Analytics

**Priority**: LOW
**Effort**: 2 weeks

**Tasks**:

- Topic modeling across corpus (LDA/NMF)
- Writing style evolution over time
- Vocabulary growth and diversity metrics
- Readability scores (Flesch-Kincaid, etc.)
- Keyword extraction and trending topics

**Value**: Corpus insights for content planning

---

## Medium-Term Enhancements (3-6 months)

### 2. Plugin Architecture

**Priority**: HIGH
**Effort**: 3-4 weeks

**Design**:

```python
# Plugin interface
class BloginatorPlugin(ABC):
    @abstractmethod
    def extract(self, file_path: Path) -> List[Document]: ...

    @abstractmethod
    def index(self, documents: List[Document]) -> None: ...

    @abstractmethod
    def generate(self, prompt: str, context: List[Document]) -> str: ...
```

**Plugin Ideas**:

- Notion integration (extract pages from workspaces)
- Confluence integration (extract team documentation)
- GitHub integration (README, issues, PRs, wiki)
- Slack integration (extract channel archives)
- Google Docs integration

**Value**: Extensibility without core code changes

---

### 3. Collaborative Features

**Priority**: MEDIUM
**Effort**: 4-6 weeks

**Tasks**:

- Multi-user authentication (OAuth, SAML)
- Shared corpus management (team workspaces)
- Role-based access control (viewer, editor, admin)
- Collaborative editing (real-time or async)
- Comment/review workflows
- Version control and approval gates

**Value**: Scales from individual to team/org use

---

### 4. Incremental Learning

**Priority**: MEDIUM
**Effort**: 3-4 weeks

**Tasks**:

- Feedback loop: user rates generated content
- Track successful/unsuccessful generations
- Fine-tune embeddings based on feedback
- Learn user preferences over time
- Adaptive prompt engineering

**Value**: System improves with use

---

## Long-Term Vision (6-12+ months)

### 5. Multi-Modal Support

**Priority**: LOW
**Effort**: 2-3 months

**Tasks**:

- Extract text from images (OCR with Tesseract/EasyOCR)
- Extract text from audio (Whisper transcription)
- Extract text from video (frame extraction + OCR, audio transcription)
- Index multi-modal content
- Generate content with image/audio references

**Value**: Richer corpus, more creative outputs

---

### 6. Domain-Specific Fine-Tuning

**Priority**: LOW
**Effort**: 3-4 months

**Tasks**:

- Fine-tune open-source LLMs on user's corpus
- Train LoRA adapters for style preservation
- Support for QLoRA (4-bit quantization)
- Model versioning and A/B testing

**Value**: Ultimate voice preservation, no API costs

---

### 7. Advanced Templates & Workflows

**Priority**: MEDIUM
**Effort**: 2-3 months

**Tasks**:

- Template DSL (domain-specific language)
- Conditional sections based on corpus content
- Multi-stage generation pipelines
- Approval gates and human-in-the-loop
- Integration with external tools (Grammarly, Hemingway)

**Value**: Complex, high-value document workflows

---

### 8. API & Integrations

**Priority**: MEDIUM
**Effort**: 4-6 weeks

**Tasks**:

- REST API with OpenAPI/Swagger docs
- GraphQL API for flexible queries
- Webhooks for event notifications
- VS Code extension
- Obsidian plugin

**Value**: Integration into existing workflows

---

## Technical Debt & Refactoring

### Code Quality

- [DONE] Reduce files >400 lines (split extraction, generation modules)
- Increase type hint coverage to 100%
- Improve error messages and logging

### Performance

- Profile and optimize slow operations
- Implement caching for expensive operations
- Add lazy loading for large corpora
- Consider async/await for I/O operations

### Security

- Add input validation and sanitization
- Implement rate limiting for API
- Add CSRF protection for web UI
- Encrypt sensitive data at rest

### Accessibility

- WCAG 2.1 AA compliance for web UI
- Screen reader support
- Keyboard navigation
- High contrast mode
- Internationalization (i18n) support

---

## Conclusion

Bloginator has a solid foundation. Priority should be:

1. **User Value**: Analytics, learning from feedback
2. **Extensibility**: Plugin architecture, API, integrations
3. **Scale**: Team/org features, fine-tuning
4. **Quality**: Performance, security, accessibility

Focus on what users actually need, not what seems technically interesting.
