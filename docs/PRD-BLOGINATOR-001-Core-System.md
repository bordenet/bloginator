# PRD-BLOGINATOR-001: Core Content Generation System

**Status**: Planning Phase
**Priority**: P0 (Foundation)
**Owner**: Matt Bordenet
**Created**: 2025-11-16
**Last Updated**: 2025-11-16
**Dependencies**: None (Greenfield Project)

---

## Overview

Bloginator is an AI-assisted content generation system that helps engineering leaders create authentic, high-quality documents about software engineering culture, processes, and people management by leveraging their own historical writing corpus. The system indexes years of prior written material to generate new content that reads in the author's authentic voice—avoiding generic "AI slop" while dramatically reducing document creation time from dozens of hours to minutes.

---

## Problem Statement

### The Manual Labor Problem

Engineering leaders accumulate years of written material—blog posts, internal documents, presentations, peer reviews, process documentation—covering common software engineering topics like culture, agile processes, hiring, career development, and team management. This corpus represents refined thinking, authentic voice, and hard-won insights.

When creating new documents (job descriptions, career ladders, engineering playbooks, blog posts), leaders face a painful choice:

1. **Start from scratch**: Fast but loses the nuance and voice developed over years
2. **Manual synthesis**: Search through dozens of old documents, copy-paste relevant sections, stitch together coherent narrative—taking 8-40+ hours per document

**Current Reality**:
- 8-40 hours per document searching through old materials
- Documents scattered across:
  - .zip archives from former employers
  - PDFs (presentations, reports)
  - Markdown files (blog posts, READMEs)
  - .docx Word documents (formal documents, proposals)
  - Multiple file shares and backup drives
- No systematic way to search by concept, theme, or topic
- High risk of losing valuable insights buried in old files
- Manual copy-paste risks inadvertently including proprietary information from former employers

### The "AI Slop" Problem

Generic AI tools (ChatGPT, Claude, etc.) can generate content quickly but produce recognizably artificial writing:
- Generic corporate speak
- Lack of personal voice and authenticity
- No grounding in the author's actual experience and thinking
- Readers can instantly tell it's AI-generated
- Loses the credibility that comes from authentic experience

**The credibility gap**: Engineering leaders are hired for their perspective and experience. Documents that sound like they were written by anyone (or anything) undermine that value.

### The Proprietary Content Problem

When manually stitching together documents from multiple employers, there's constant risk of:
- Including proprietary technology names, methodologies, or trade secrets
- Referencing confidential projects or data
- Inadvertently violating NDAs from former employers
- Using trade names or branded terms that shouldn't appear in new employer's materials

**Current mitigation**: Manual review of every sentence, which is exhausting and error-prone.

### The Evolution Problem

Writing quality and thinking evolve over time. Materials from 5-10 years ago may contain useful concepts but:
- Less refined writing style
- Outdated perspectives or approaches
- Immature thinking that has since evolved
- Different context that may not apply today

**Current approach**: Manually identify and update dated thinking while preserving core insights—time-consuming and inconsistent.

---

## Goals

### Primary Goals

1. **Authentic Voice Preservation**: Generate content that reads in the author's authentic voice, indistinguishable from manually-written material
2. **Corpus-Grounded Generation**: All generated content must be grounded in actual prior writing, not generic AI training data
3. **Dramatic Time Reduction**: Reduce document creation time from 8-40 hours to 30-60 minutes (including outline and drafting)
4. **Interactive Refinement**: Allow iterative refinement through natural conversation about themes, emphasis, tone
5. **Proprietary Content Protection**: Systematically prevent leakage of proprietary information, trade secrets, or confidential references from prior employers

### Secondary Goals

1. **Quality Evolution Awareness**: System should recognize and prefer more recent, refined thinking over older materials when conflicts arise
2. **Safe Citation Integration**: Support careful integration of properly-attributed external sources (e.g., O'Reilly Google SRE book)
3. **Multi-Format Support**: Handle diverse source formats (.zip, PDF, .docx, .md, .txt)
4. **Export Flexibility**: Generate outputs in Markdown, DOCX, or other formats as needed
5. **Searchable Corpus**: Enable ad-hoc searching of historical corpus for specific concepts or examples

### Non-Goals (For This PRD)

- Multi-user collaboration or team workspaces
- Real-time collaborative editing
- Version control or approval workflows
- Publishing automation to external platforms (Medium, LinkedIn, etc.)
- Analytics or performance tracking of published content
- Visual asset generation (diagrams, infographics)

---

## Success Metrics

### Quality Metrics

- **Voice Authenticity**: 90%+ of readers (who know the author's writing) cannot distinguish generated content from manually-written content in blind tests
- **Factual Accuracy**: 98%+ of statements are grounded in actual prior writing (not hallucinated)
- **Proprietary Content Leakage**: 0% of generated content includes flagged proprietary terms, trade names, or confidential references
- **Completeness**: Generated documents include all sections specified in outline with appropriate depth

### Performance Metrics

- **Index Building**: Initial corpus indexing completes in <30 minutes for 500+ documents
- **Draft Generation**: First draft generated in <5 minutes from outline submission
- **Iteration Speed**: Refinements applied in <2 minutes per iteration
- **Search Response**: Corpus search returns results in <3 seconds

### User Satisfaction Metrics

- **Time Savings**: 85%+ time reduction vs. manual document creation
- **Quality Rating**: Author rates 80%+ of generated drafts as "good enough to edit" vs. "needs major rewrite"
- **Iteration Count**: Requires <5 refinement iterations to reach "ready to publish" state
- **Adoption**: System used for 90%+ of new document creation after initial corpus indexing

---

## User Stories

### Epic: Corpus Building and Management

**US-001: As an engineering leader, I want to upload my historical writing corpus from multiple sources so the system can learn my voice and reference my ideas**

Acceptance Criteria:
- Support upload of .zip archives, individual PDFs, .docx, .md, .txt files
- Extract text from all supported formats with >95% accuracy
- Preserve document metadata (dates, filenames, source)
- Build searchable index of all content
- Handle large corpuses (500+ documents, 10+ GB)
- Process completes with progress indication and error handling

**US-002: As an engineering leader, I want to flag proprietary terms and trade secrets that should never appear in generated content so I don't accidentally violate NDAs**

Acceptance Criteria:
- Provide interface to specify blocklisted terms (company names, product names, proprietary methodologies)
- Support pattern matching (e.g., "Project [Codename]", "Acme Corp", "PropTech™")
- System validates generated content against blocklist before display
- Clear warning if blocked terms are detected in source materials
- Ability to review and update blocklist over time

**US-003: As an engineering leader, I want to mark documents or passages by quality/recency so the system prefers my more refined thinking**

Acceptance Criteria:
- Automatic timestamp extraction from document metadata
- Ability to manually mark documents as "preferred" or "deprecated"
- Ability to annotate specific passages as "evolved thinking" or "outdated perspective"
- System weights recent/preferred content higher in generation
- Transparency in what sources were used for each generated passage

### Epic: Document Creation

**US-004: As an engineering leader, I want to create a new document by specifying keywords, themes, and a thesis so I can quickly outline my thinking**

Acceptance Criteria:
- Natural language input for document concept (e.g., "career ladder for senior engineers focusing on technical leadership vs. people management")
- System suggests relevant topics and themes from corpus
- Generates structured outline with major sections
- Shows source material coverage for each section (e.g., "80% coverage from 12 documents")
- Warns if any section has low coverage (<30%) from corpus

**US-005: As an engineering leader, I want to generate a full draft from my outline that reads in my voice so I have a strong starting point**

Acceptance Criteria:
- Draft generated from approved outline
- Each paragraph grounded in specific prior writing
- Maintains consistent voice and tone throughout
- Preserves author's characteristic phrases, analogies, and examples
- Includes inline citations showing source documents (hideable/removable for final version)
- Flags any generated content that isn't directly grounded in corpus

**US-006: As an engineering leader, I want to refine the draft by providing natural language feedback so I can quickly iterate to final version**

Acceptance Criteria:
- Support feedback like:
  - "Make the tone more optimistic"
  - "Add more concrete examples from my startup experience"
  - "De-emphasize the waterfall critiques, focus on agile benefits"
  - "Make it shorter—target 1000 words"
- System regenerates affected sections
- Shows diff highlighting what changed
- Allows reverting individual changes
- Maintains version history for current session

**US-007: As an engineering leader, I want to export the final document in multiple formats so I can publish to different platforms**

Acceptance Criteria:
- Export to Markdown (for GitHub, blog platforms)
- Export to DOCX (for Google Docs, corporate systems)
- Export to plain text
- Export to HTML
- Option to include or exclude inline citations
- Preserve formatting (headers, lists, code blocks, emphasis)

### Epic: Corpus Search and Discovery

**US-008: As an engineering leader, I want to search my corpus for specific concepts or examples so I can quickly find reference material**

Acceptance Criteria:
- Semantic search (search by meaning, not just keywords)
- Natural language queries (e.g., "my thoughts on code review culture")
- Results ranked by relevance and recency
- Preview snippets with query context highlighted
- Ability to open full source document
- Filter by date range, document type, or manual tags

**US-009: As an engineering leader, I want to see what topics I've written about and identify gaps so I know where to focus new writing**

Acceptance Criteria:
- Visualization or listing of major themes in corpus
- Coverage metrics (e.g., "15 documents on hiring, 3 on performance reviews")
- Identification of related topics with low coverage
- Suggestions for document topics based on partial coverage
- Timeline view showing evolution of thinking on specific topics

### Epic: Safe External References

**US-010: As an engineering leader, I want to add trusted external sources (like the O'Reilly SRE book) that can be quoted with proper attribution**

Acceptance Criteria:
- Upload external reference materials (PDFs, books)
- Mark as "external source requiring attribution"
- System includes proper citations when using external material
- Visual distinction between author's voice and external quotes
- Ability to set citation style (footnotes, inline, bibliography)
- Never blend external source language into author's voice without attribution

---

## Technical Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web UI     │  │  CLI Tools   │  │  API Server  │      │
│  │ (Interactive)│  │  (Batch)     │  │  (Future)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│              Content Generation Engine                       │
│  ┌──────────────────┐  ┌───────────────────────────┐       │
│  │  Outline Builder │  │  Voice Preservation       │       │
│  │  - Topic mapping │  │  - Style analysis         │       │
│  │  - Coverage      │  │  - Phrase extraction      │       │
│  │    analysis      │  │  - Tone consistency       │       │
│  └─────────┬────────┘  └───────────┬───────────────┘       │
│            │                        │                        │
│  ┌─────────▼────────────────────────▼───────────────┐      │
│  │         RAG (Retrieval-Augmented Generation)     │      │
│  │  - Semantic search                               │      │
│  │  - Source ranking (recency, quality)             │      │
│  │  - Context assembly                              │      │
│  └─────────┬────────────────────────────────────────┘      │
│            │                                                 │
│  ┌─────────▼──────────────────────────────────────┐        │
│  │         Safety & Validation Layer               │        │
│  │  - Proprietary term detection                   │        │
│  │  - Blocklist enforcement                        │        │
│  │  - Attribution verification                     │        │
│  └─────────┬───────────────────────────────────────┘       │
└────────────┼─────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────┐
│                   Storage & Indexing Layer                    │
│  ┌──────────────────┐  ┌────────────────┐  ┌─────────────┐  │
│  │  Vector Store    │  │  Document      │  │  Metadata   │  │
│  │  (ChromaDB/      │  │  Storage       │  │  Store      │  │
│  │   FAISS)         │  │  (Raw files)   │  │  (SQLite)   │  │
│  └──────────────────┘  └────────────────┘  └─────────────┘  │
└───────────────────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────┐
│                    LLM & Embedding Layer                      │
│  ┌──────────────────┐  ┌────────────────────────────────┐   │
│  │  Local LLM       │  │  Embedding Model               │   │
│  │  (Ollama/        │  │  (sentence-transformers)       │   │
│  │   LM Studio)     │  │                                │   │
│  └──────────────────┘  └────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Document Extraction & Processing

**Supported Formats**:
- PDF (via PyMuPDF or similar)
- Microsoft Word .docx (via python-docx)
- Markdown (native parsing)
- Plain text
- .zip archives (recursive extraction)

**Metadata Extraction**:
- Document creation/modification dates
- Filenames and paths
- Document structure (headings, sections)
- Author information (if available)
- Manual tags/classifications

**Text Chunking**:
- Semantic chunking (preserve meaning)
- Section-based chunking (respect document structure)
- Configurable chunk size (balance context vs. granularity)
- Overlap between chunks for context preservation

#### 2. Vector Indexing & Semantic Search

**Embedding Model**:
- Local sentence-transformers model (e.g., all-MiniLM-L6-v2)
- No cloud API calls—complete privacy
- 384-dimensional embeddings (balance accuracy vs. speed)

**Vector Store**:
- ChromaDB (persistent, local-first) or FAISS
- Support for metadata filtering (date, source, quality rating)
- Efficient similarity search (<100ms for large corpuses)

**Search Capabilities**:
- Semantic similarity search (meaning-based, not keyword)
- Hybrid search (combine semantic + keyword)
- Recency weighting (prefer recent documents)
- Quality weighting (prefer marked "refined" content)
- Source diversity (pull from multiple documents, not just one)

#### 3. Voice Preservation System

**Style Analysis**:
- Extract characteristic phrases and expressions from corpus
- Analyze sentence structure patterns
- Identify preferred terminology and analogies
- Detect tone markers (formal, conversational, technical)

**Voice Consistency Validation**:
- Compare generated text to corpus style metrics
- Flag sections that don't match voice profile
- Suggest rephrasings that better match author's style
- Score generated content for "voice similarity"

#### 4. Content Generation Engine

**RAG-Based Generation**:
- Query vector store for relevant passages
- Assemble context from top-k results (k=10-20)
- Include source metadata in context
- Generate with explicit grounding instructions

**Prompt Engineering**:
- System prompts emphasizing:
  - "Use only the author's prior writing"
  - "Preserve the author's voice and characteristic phrases"
  - "Do not invent facts or examples not in source material"
  - "Explicitly cite sources for each claim"
- Templates for different document types (blog post, job description, playbook, etc.)

**LLM Integration**:
- Primary: Local LLM via Ollama (llama3, mistral, etc.)
- Fallback: LM Studio, GPT4All, or other local options
- Future: Optional cloud LLM with explicit user consent

#### 5. Safety & Validation Layer

**Proprietary Term Blocklist**:
- User-defined list of terms that must not appear
- Pattern matching (regex support)
- Company names, product names, project codenames
- Proprietary methodologies or frameworks
- Pre-generation validation (block before display)

**Attribution Verification**:
- Track source documents for every generated paragraph
- Validate external sources have proper citations
- Distinguish author's voice from quoted material
- Ensure no blending of external sources without attribution

**Confidence Scoring**:
- Score each generated section by corpus coverage
- Flag sections with low grounding (<30% corpus match)
- Warn user when system is "extrapolating" vs. "synthesizing"

#### 6. User Interface

**Web UI (Primary Interface)**:
- Dashboard: Corpus overview, statistics, recent documents
- Corpus Management: Upload, tag, blocklist management
- Document Creation: Outline builder → draft generation → refinement
- Search: Semantic search interface with filters
- Export: Multi-format export with options

**CLI Tools (Power Users & Automation)**:
- `bloginator extract <source>` - Extract and index documents
- `bloginator search <query>` - Search corpus
- `bloginator outline <concept>` - Generate document outline
- `bloginator draft <outline>` - Generate draft from outline
- `bloginator refine <draft> "<feedback>"` - Apply refinement
- `bloginator export <draft> --format=md|docx|html` - Export

---

## Data Model

### Document Record

```python
{
  "id": "doc_uuid",
  "filename": "blog-post-agile-transformation.md",
  "source_path": "/uploads/2019-blogs.zip/2019-07-agile.md",
  "format": "markdown",
  "created_date": "2019-07-15",
  "modified_date": "2019-07-18",
  "indexed_date": "2025-11-16",
  "quality_rating": "preferred",  # preferred | standard | deprecated
  "tags": ["agile", "transformation", "culture"],
  "is_external_source": false,
  "attribution_required": false,
  "word_count": 2847,
  "chunks": ["chunk_uuid_1", "chunk_uuid_2", ...]
}
```

### Chunk Record

```python
{
  "id": "chunk_uuid",
  "document_id": "doc_uuid",
  "content": "Full text of chunk...",
  "embedding": [0.123, -0.456, ...],  # 384-dim vector
  "chunk_index": 3,  # Position in document
  "section_heading": "Building Agile Mindset",
  "char_start": 1240,
  "char_end": 2015
}
```

### Blocklist Entry

```python
{
  "id": "block_uuid",
  "pattern": "Acme Corp",
  "pattern_type": "exact" | "regex",
  "category": "company_name" | "product_name" | "project" | "methodology",
  "added_date": "2025-11-16",
  "notes": "Former employer - NDA"
}
```

### Generated Document

```python
{
  "id": "draft_uuid",
  "title": "Engineering Career Ladder: IC Track",
  "status": "draft" | "refining" | "final",
  "created_date": "2025-11-16T14:32:00",
  "outline": {...},
  "current_version": 3,
  "versions": [
    {
      "version": 1,
      "content": "...",
      "source_chunks": ["chunk_uuid_1", ...],
      "citations": [...],
      "timestamp": "2025-11-16T14:35:00"
    },
    ...
  ],
  "blocklist_violations": [],  # Should always be empty in valid drafts
  "voice_similarity_score": 0.87
}
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Core document extraction, indexing, and basic search

**Deliverables**:
- Document extraction pipeline (PDF, DOCX, MD, TXT, ZIP)
- Text chunking with semantic awareness
- Vector indexing with ChromaDB/FAISS
- Basic semantic search CLI
- Corpus statistics and coverage analysis

**Acceptance Criteria**:
- Successfully index 500+ documents in <30 minutes
- Search returns relevant results in <3 seconds
- Support all specified file formats
- Unit tests with 80%+ coverage

### Phase 2: Content Generation (Weeks 3-4)

**Goal**: RAG-based draft generation with voice preservation

**Deliverables**:
- Outline generation from keywords/themes
- Draft generation from outlines
- Source attribution system
- Basic voice consistency validation
- CLI tools for generation pipeline

**Acceptance Criteria**:
- Generate coherent draft in <5 minutes
- All generated content grounded in corpus (citations provided)
- Voice similarity score >0.7 on test documents
- Draft includes all sections from outline

### Phase 3: Safety & Refinement (Weeks 5-6)

**Goal**: Proprietary content protection and iterative refinement

**Deliverables**:
- Blocklist management system
- Pre-generation validation
- Iterative refinement interface
- Quality/recency weighting system
- Diff visualization for refinements

**Acceptance Criteria**:
- 100% detection of blocklisted terms
- Refinement iterations complete in <2 minutes
- User can revert changes selectively
- Clear diff showing what changed and why

### Phase 4: Web UI (Weeks 7-8)

**Goal**: Interactive web interface for non-technical users

**Deliverables**:
- Web dashboard with corpus overview
- Corpus upload and management UI
- Document creation wizard (outline → draft → refine)
- Search interface
- Multi-format export

**Acceptance Criteria**:
- Complete document creation workflow in browser
- No CLI required for core workflows
- Responsive design (desktop focus, mobile-friendly)
- In-browser file upload with progress indication

### Phase 5: Polish & External Sources (Weeks 9-10)

**Goal**: Advanced features and production readiness

**Deliverables**:
- External source support with attribution
- Advanced search filters and facets
- Template library for common document types
- Comprehensive testing and validation
- Documentation and user guides

**Acceptance Criteria**:
- Support adding external sources (e.g., SRE book)
- Proper citation formatting (footnotes, bibliography)
- 10+ document templates (job desc, career ladder, blog post, etc.)
- User documentation complete
- E2E tests covering all major workflows

---

## Technical Risks & Mitigation

### Risk 1: Voice Preservation Quality

**Risk**: Generated content doesn't convincingly match author's voice

**Mitigation**:
- Extensive testing with blind reader studies
- Style analysis and validation system
- Explicit "grounding-only" prompts to LLM
- Iterative refinement to converge on author's voice
- Fallback to more conservative generation (more direct quoting)

### Risk 2: Corpus Coverage Gaps

**Risk**: User wants to write about topic with limited prior coverage

**Mitigation**:
- Coverage analysis warns user before generation
- Suggest related topics where coverage is better
- Allow "research mode" where user can add new seed content
- Graceful degradation—acknowledge gaps in generated content

### Risk 3: Blocklist Evasion

**Risk**: Proprietary terms appear in generated content despite blocklist

**Mitigation**:
- Multiple validation layers (pre-generation, post-generation)
- Fuzzy matching for near-misses (e.g., "Acme" vs "ACME Corp")
- Regular expression support for patterns
- Manual review workflow before export
- Comprehensive testing with adversarial examples

### Risk 4: LLM Hallucination

**Risk**: LLM invents facts or examples not in corpus

**Mitigation**:
- RAG-first architecture (grounding required)
- Source attribution for every claim
- Confidence scoring with low-confidence warnings
- Explicit prompts forbidding invention
- Validation against corpus (unsupported claims flagged)

### Risk 5: Performance at Scale

**Risk**: System becomes slow with very large corpuses (1000+ docs)

**Mitigation**:
- Optimized vector search (FAISS or Milvus for huge corpuses)
- Incremental indexing (only index new/changed documents)
- Caching of frequently-accessed embeddings
- Background processing for corpus updates
- Performance testing with realistic data volumes

---

## Open Questions

1. **Template Format**: Should document templates be LLM prompts, structured schemas, or example documents?

2. **Version Control**: Do we need git-like version control for generated documents, or is session-based versioning sufficient?

3. **Multi-Author Support**: Should system support multiple authors in same corpus (e.g., team blog), or strictly single-author?

4. **Cloud LLM Option**: Should we offer optional cloud LLM (GPT-4, Claude) with user consent, or strictly local-only?

5. **Export Citations**: Should exported documents include inline citations, footnotes, or remove citations entirely?

6. **Incremental Corpus Updates**: How do users add new documents over time—manual re-upload or watch folder?

---

## Success Criteria for PRD Approval

This PRD is approved when:

1. ✅ Stakeholder (Matt Bordenet) confirms problem statement accurately reflects pain points
2. ✅ Technical approach is feasible with available tools and resources
3. ✅ Success metrics are measurable and achievable
4. ✅ User stories cover all critical workflows
5. ✅ Implementation phases are realistic and sequenced logically
6. ✅ Risks are identified with credible mitigation strategies
7. ✅ Open questions are resolved or marked as "decide during implementation"

---

## References

- **Films Not Made PRD-001**: Extraction and indexing patterns (reusable)
- **Films Not Made PRD-002**: RAG-based generation architecture (similar use case)
- **Google SRE Book**: Example external source for attribution testing
- **RAG Best Practices**: LangChain documentation, RAG papers

---

## Appendix: Example User Workflow

### Scenario: Creating a "Senior Engineer Career Ladder" Document

**Step 1: User specifies concept**
```
Keywords: senior engineer, career ladder, IC track, technical leadership
Themes: technical excellence, mentorship, system design, influence
Thesis: Senior engineers grow through technical mastery AND organizational impact
```

**Step 2: System generates outline**
```
# Senior Engineer Career Ladder: Individual Contributor Track

## Introduction
- Role of IC track in engineering organization
- Parallel growth to management track
[Coverage: 78% from 8 documents]

## Core Competencies by Level
### Senior Engineer (L4)
- Technical execution and quality
- Mentorship of junior engineers
[Coverage: 92% from 15 documents]

### Staff Engineer (L5)
- System design and architecture
- Cross-team influence
[Coverage: 64% from 6 documents]

### Principal Engineer (L6)
- Organization-wide technical strategy
- Technical leadership without authority
[Coverage: 45% from 3 documents] ⚠️ Low coverage

## Evaluation Criteria
- Technical skills
- Impact and scope
- Leadership and mentorship
[Coverage: 88% from 12 documents]

## Promotion Process
- Nomination and packet preparation
- Calibration and review
[Coverage: 71% from 5 documents]
```

**Step 3: User approves outline (or requests changes)**

**Step 4: System generates draft**
- Pulls relevant chunks from corpus for each section
- Synthesizes coherent narrative in author's voice
- Includes inline citations (optional, hideable)
- Flags Principal Engineer section for low corpus coverage

**Step 5: User provides refinement feedback**
```
"Add more concrete examples from my startup experience.
Make the tone more optimistic about IC track opportunities.
Shorten the Introduction to 2 paragraphs max."
```

**Step 6: System applies refinements**
- Searches corpus for "startup" examples
- Adjusts tone using more positive source material
- Condenses Introduction, shows diff

**Step 7: User exports final document**
- Markdown for GitHub engineering handbook
- DOCX for HR system upload
- HTML for internal wiki

**Total time**: 35 minutes (vs. 12-20 hours manual)

---

*End of PRD-BLOGINATOR-001*
