"""Tests for draft models."""

import pytest

from bloginator.models.draft import Citation, Draft, DraftSection


class TestCitation:
    """Tests for Citation model."""

    def test_create_basic_citation(self):
        """Test creating a basic citation."""
        citation = Citation(
            chunk_id="chunk123",
            document_id="doc456",
            filename="article.md",
        )

        assert citation.chunk_id == "chunk123"
        assert citation.document_id == "doc456"
        assert citation.filename == "article.md"
        assert citation.content_preview == ""
        assert citation.similarity_score == 0.0

    def test_create_citation_with_details(self):
        """Test citation with preview and score."""
        citation = Citation(
            chunk_id="chunk1",
            document_id="doc1",
            filename="test.md",
            content_preview="This is a preview...",
            similarity_score=0.85,
        )

        assert citation.content_preview == "This is a preview..."
        assert citation.similarity_score == 0.85

    def test_similarity_score_validation(self):
        """Test similarity score range validation."""
        # Valid range
        citation = Citation(
            chunk_id="c1",
            document_id="d1",
            filename="f.md",
            similarity_score=0.5,
        )
        assert citation.similarity_score == 0.5

        # Invalid: negative
        with pytest.raises(ValueError):
            Citation(
                chunk_id="c1",
                document_id="d1",
                filename="f.md",
                similarity_score=-0.1,
            )

        # Invalid: > 1.0
        with pytest.raises(ValueError):
            Citation(
                chunk_id="c1",
                document_id="d1",
                filename="f.md",
                similarity_score=1.5,
            )


class TestDraftSection:
    """Tests for DraftSection model."""

    def test_create_basic_section(self):
        """Test creating a basic section."""
        section = DraftSection(
            title="Introduction",
            content="This is the introduction.",
        )

        assert section.title == "Introduction"
        assert section.content == "This is the introduction."
        assert section.citations == []
        assert section.voice_score == 0.0
        assert section.has_blocklist_violations is False
        assert section.subsections == []

    def test_create_section_with_citations(self):
        """Test section with citations."""
        citation1 = Citation(
            chunk_id="c1",
            document_id="d1",
            filename="source1.md",
        )
        citation2 = Citation(
            chunk_id="c2",
            document_id="d2",
            filename="source2.md",
        )

        section = DraftSection(
            title="Section",
            content="Content",
            citations=[citation1, citation2],
        )

        assert len(section.citations) == 2
        assert section.citations[0].chunk_id == "c1"
        assert section.citations[1].chunk_id == "c2"

    def test_voice_score_validation(self):
        """Test voice score range validation."""
        # Valid
        section = DraftSection(
            title="Test",
            content="Content",
            voice_score=0.75,
        )
        assert section.voice_score == 0.75

        # Invalid: negative
        with pytest.raises(ValueError):
            DraftSection(
                title="Test",
                content="Content",
                voice_score=-0.1,
            )

        # Invalid: > 1.0
        with pytest.raises(ValueError):
            DraftSection(
                title="Test",
                content="Content",
                voice_score=1.5,
            )

    def test_nested_subsections(self):
        """Test nested subsections."""
        subsection = DraftSection(
            title="Subsection",
            content="Sub content",
        )

        section = DraftSection(
            title="Main",
            content="Main content",
            subsections=[subsection],
        )

        assert len(section.subsections) == 1
        assert section.subsections[0].title == "Subsection"

    def test_blocklist_violations_flag(self):
        """Test blocklist violations flag."""
        section = DraftSection(
            title="Test",
            content="Content",
            has_blocklist_violations=True,
        )

        assert section.has_blocklist_violations is True


class TestDraft:
    """Tests for Draft model."""

    def test_create_basic_draft(self):
        """Test creating a basic draft."""
        draft = Draft(
            title="Test Document",
            thesis="Main thesis",
            keywords=["test", "document"],
        )

        assert draft.title == "Test Document"
        assert draft.thesis == "Main thesis"
        assert draft.keywords == ["test", "document"]
        assert draft.sections == []
        assert draft.voice_score == 0.0
        assert draft.total_citations == 0
        assert draft.total_words == 0
        assert draft.has_blocklist_violations is False

    def test_create_draft_with_sections(self):
        """Test draft with sections."""
        section1 = DraftSection(title="Intro", content="Introduction text")
        section2 = DraftSection(title="Body", content="Body text")

        draft = Draft(
            title="Document",
            keywords=["test"],
            sections=[section1, section2],
        )

        assert len(draft.sections) == 2

    def test_calculate_stats_empty(self):
        """Test stats calculation with no sections."""
        draft = Draft(title="Empty", keywords=[])
        draft.calculate_stats()

        assert draft.total_words == 0
        assert draft.total_citations == 0
        assert draft.voice_score == 0.0

    def test_calculate_stats_word_count(self):
        """Test word count calculation."""
        sections = [
            DraftSection(title="S1", content="This has five words total"),  # 5 words
            DraftSection(title="S2", content="Three words here"),  # 3 words
        ]

        draft = Draft(title="Test", keywords=[], sections=sections)
        draft.calculate_stats()

        assert draft.total_words == 8

    def test_calculate_stats_citations(self):
        """Test citation counting."""
        citation1 = Citation(chunk_id="c1", document_id="d1", filename="f1.md")
        citation2 = Citation(chunk_id="c2", document_id="d2", filename="f2.md")
        citation3 = Citation(chunk_id="c3", document_id="d3", filename="f3.md")

        section1 = DraftSection(
            title="S1",
            content="Text",
            citations=[citation1, citation2],
        )
        section2 = DraftSection(
            title="S2",
            content="Text",
            citations=[citation3],
        )

        draft = Draft(title="Test", keywords=[], sections=[section1, section2])
        draft.calculate_stats()

        assert draft.total_citations == 3

    def test_calculate_stats_voice_score(self):
        """Test voice score averaging."""
        sections = [
            DraftSection(title="S1", content="Text", voice_score=0.8),
            DraftSection(title="S2", content="Text", voice_score=0.6),
            DraftSection(title="S3", content="Text", voice_score=0.7),
        ]

        draft = Draft(title="Test", keywords=[], sections=sections)
        draft.calculate_stats()

        # Average: (0.8 + 0.6 + 0.7) / 3 = 0.7
        assert draft.voice_score == pytest.approx(0.7, rel=0.01)

    def test_calculate_stats_nested_sections(self):
        """Test stats with nested sections."""
        subsection = DraftSection(
            title="Sub",
            content="Four words in subsection",  # 4 words
            voice_score=0.9,
        )

        section = DraftSection(
            title="Main",
            content="Five words in main section",  # 5 words
            voice_score=0.7,
            subsections=[subsection],
        )

        draft = Draft(title="Test", keywords=[], sections=[section])
        draft.calculate_stats()

        assert draft.total_words == 9  # 5 + 4
        # Voice score: (0.7 + 0.9) / 2 = 0.8
        assert draft.voice_score == pytest.approx(0.8, rel=0.01)

    def test_get_all_sections_flat(self):
        """Test getting all sections from flat structure."""
        section1 = DraftSection(title="S1", content="C1")
        section2 = DraftSection(title="S2", content="C2")

        draft = Draft(
            title="Test",
            keywords=[],
            sections=[section1, section2],
        )

        all_sections = draft.get_all_sections()

        assert len(all_sections) == 2

    def test_get_all_sections_nested(self):
        """Test getting all sections from nested structure."""
        subsection = DraftSection(title="Sub", content="SubC")
        section = DraftSection(
            title="Main",
            content="MainC",
            subsections=[subsection],
        )

        draft = Draft(title="Test", keywords=[], sections=[section])

        all_sections = draft.get_all_sections()

        assert len(all_sections) == 2
        titles = [s.title for s in all_sections]
        assert "Main" in titles
        assert "Sub" in titles

    def test_to_markdown_basic(self):
        """Test markdown generation produces clean prose format."""
        section = DraftSection(
            title="Introduction",
            content="This is the introduction.",
        )

        draft = Draft(
            title="Test Document",
            thesis="Main thesis",
            keywords=["test"],
            sections=[section],
        )

        markdown = draft.to_markdown()

        # Clean title without scoring prefixes
        assert "# Test Document" in markdown
        assert "[00-00-00]" not in markdown  # No scoring in drafts
        assert "*Main thesis*" in markdown
        assert "## Introduction" in markdown
        assert "This is the introduction." in markdown

        # No metrics table - that belongs in outlines
        assert "| Metric | Score | Description |" not in markdown

        # Minimal metadata in comment
        assert "<!--" in markdown
        assert "Generated:" in markdown
        assert "-->" in markdown

    def test_to_markdown_nested(self):
        """Test markdown with nested sections."""
        subsection = DraftSection(
            title="Subsection",
            content="Subsection content",
        )
        section = DraftSection(
            title="Main Section",
            content="Main content",
            subsections=[subsection],
        )

        draft = Draft(
            title="Document",
            keywords=["test"],
            sections=[section],
        )

        markdown = draft.to_markdown()

        assert "## Main Section" in markdown
        assert "Main content" in markdown
        assert "### Subsection" in markdown
        assert "Subsection content" in markdown

    def test_to_markdown_clean_format(self):
        """Test markdown produces clean output without citations or scoring."""
        citation = Citation(
            chunk_id="c1",
            document_id="d1",
            filename="source.md",
            content_preview="Preview text",
            similarity_score=0.85,
        )

        section = DraftSection(
            title="Section",
            content="Content",
            citations=[citation],
        )

        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[section],
        )
        draft.calculate_stats()

        markdown = draft.to_markdown()

        # Clean output - no citation markers or sources appendix
        assert "## Section" in markdown
        assert "Content" in markdown
        assert "source.md" not in markdown
        assert "*[1 sources]*" not in markdown
        assert "## Sources" not in markdown

        # The include_citations param is deprecated and ignored
        markdown_with_flag = draft.to_markdown(include_citations=True)
        assert markdown == markdown_with_flag

    def test_blocklist_violations(self):
        """Test blocklist violations tracking."""
        draft = Draft(
            title="Test",
            keywords=[],
            sections=[],
            has_blocklist_violations=True,
            blocklist_validation_result={
                "is_valid": False,
                "violations": [{"pattern": "test"}],
            },
        )

        assert draft.has_blocklist_violations is True
        assert not draft.blocklist_validation_result["is_valid"]
