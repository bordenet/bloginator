"""Tests for draft generator."""

from unittest.mock import Mock

import pytest

from bloginator.generation.draft_generator import DraftGenerator
from bloginator.models.draft import DraftSection
from bloginator.models.outline import Outline, OutlineSection
from bloginator.search import SearchResult


class TestDraftGenerator:
    """Tests for DraftGenerator."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = Mock()
        return client

    @pytest.fixture
    def mock_searcher(self):
        """Create mock searcher."""
        searcher = Mock()
        # Mock batch_search to return empty lists by default
        searcher.batch_search.return_value = []
        return searcher

    @pytest.fixture
    def generator(self, mock_llm_client, mock_searcher):
        """Create draft generator with mocks."""
        return DraftGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
            sources_per_section=5,
        )

    def test_initialization(self, mock_llm_client, mock_searcher):
        """Test generator initialization."""
        generator = DraftGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
            sources_per_section=10,
        )

        assert generator.llm_client == mock_llm_client
        assert generator.searcher == mock_searcher
        assert generator.sources_per_section == 10

    def test_build_source_context_empty(self, generator):
        """Test building context with no results."""
        context = generator._build_source_context([])

        assert "No source material found" in context

    def test_build_source_context_with_results(self, generator):
        """Test building context from search results."""
        results = [
            SearchResult(
                chunk_id="chunk1",
                content="First result content",
                distance=0.1,
                metadata={},
            ),
            SearchResult(
                chunk_id="chunk2",
                content="Second result content",
                distance=0.2,
                metadata={},
            ),
        ]

        context = generator._build_source_context(results)

        assert "[Source 1]" in context
        assert "First result content" in context
        assert "[Source 2]" in context
        assert "Second result content" in context

    def test_generate_section_basic(self, generator, mock_llm_client, mock_searcher):
        """Test generating a basic section."""
        # Mock search results
        search_results = [
            SearchResult(
                chunk_id=f"chunk{i}",
                content=f"Source content {i}",
                distance=0.2,
                metadata={
                    "document_id": f"doc{i}",
                    "filename": f"file{i}.md",
                },
            )
            for i in range(5)
        ]
        mock_searcher.search.return_value = search_results

        # Mock LLM response
        llm_response = Mock()
        llm_response.content = "Generated section content."
        mock_llm_client.generate.return_value = llm_response

        outline_section = OutlineSection(
            title="Test Section",
            description="Section description",
        )

        draft_section = generator._generate_section(
            outline_section=outline_section,
            keywords=["test"],
            temperature=0.7,
            max_words=300,
        )

        # Verify section
        assert draft_section.title == "Test Section"
        assert draft_section.content == "Generated section content."
        assert len(draft_section.citations) == 5
        assert draft_section.citations[0].chunk_id == "chunk0"
        assert draft_section.citations[0].filename == "file0.md"

    def test_generate_section_with_subsections(self, generator, mock_llm_client, mock_searcher):
        """Test generating section with subsections."""
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="chunk1",
                content="Content",
                distance=0.2,
                metadata={"document_id": "doc1", "filename": "file.md"},
            )
        ]

        llm_response = Mock()
        llm_response.content = "Generated content"
        mock_llm_client.generate.return_value = llm_response

        # Outline with subsection
        subsection = OutlineSection(
            title="Subsection",
            description="Sub desc",
        )
        outline_section = OutlineSection(
            title="Main",
            description="Main desc",
            subsections=[subsection],
        )

        draft_section = generator._generate_section(
            outline_section=outline_section,
            keywords=["test"],
        )

        # Should have generated subsection
        assert len(draft_section.subsections) == 1
        assert draft_section.subsections[0].title == "Subsection"
        assert draft_section.subsections[0].content == "Generated content"

    def test_generate_section_prompts(self, generator, mock_llm_client, mock_searcher):
        """Test that prompts are constructed correctly."""
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="chunk1",
                content="Source material",
                distance=0.2,
                metadata={"document_id": "doc1", "filename": "file.md"},
            )
        ]

        llm_response = Mock()
        llm_response.content = "Content"
        mock_llm_client.generate.return_value = llm_response

        outline_section = OutlineSection(
            title="Section Title",
            description="Section description",
        )

        generator._generate_section(
            outline_section=outline_section,
            keywords=["keyword1", "keyword2"],
            max_words=500,
        )

        # Verify LLM call
        call_args = mock_llm_client.generate.call_args

        user_prompt = call_args.kwargs["prompt"]
        assert "Section Title" in user_prompt
        assert "Section description" in user_prompt
        assert "500 words" in user_prompt
        assert "Source material" in user_prompt

        system_prompt = call_args.kwargs["system_prompt"]
        assert "technical writer" in system_prompt.lower()
        assert "source" in system_prompt.lower()

    def test_generate_full_draft(self, generator, mock_llm_client, mock_searcher):
        """Test generating complete draft from outline."""
        # Mock batch search (returns results for 2 sections)
        mock_searcher.batch_search.return_value = [
            [
                SearchResult(
                    chunk_id="chunk1",
                    content="Source",
                    distance=0.2,
                    metadata={"document_id": "doc1", "filename": "file.md"},
                )
            ],
            [
                SearchResult(
                    chunk_id="chunk2",
                    content="Source",
                    distance=0.2,
                    metadata={"document_id": "doc2", "filename": "file2.md"},
                )
            ],
        ]

        # Mock LLM
        llm_response = Mock()
        llm_response.content = "Generated content for section."
        mock_llm_client.generate.return_value = llm_response

        # Create outline
        outline = Outline(
            title="Test Document",
            thesis="Test thesis",
            keywords=["test", "document"],
            sections=[
                OutlineSection(title="Intro", description="Introduction"),
                OutlineSection(title="Body", description="Main content"),
            ],
        )

        # Generate draft
        draft = generator.generate(
            outline=outline,
            temperature=0.7,
            max_section_words=300,
        )

        # Verify draft
        assert draft.title == "Test Document"
        assert draft.thesis == "Test thesis"
        assert draft.keywords == ["test", "document"]
        assert len(draft.sections) == 2
        assert draft.sections[0].title == "Intro"
        assert draft.sections[1].title == "Body"
        # Stats should be calculated
        assert draft.total_words > 0

    def test_generate_with_custom_params(self, generator, mock_llm_client, mock_searcher):
        """Test generation with custom parameters."""
        mock_searcher.batch_search.return_value = [
            [
                SearchResult(
                    chunk_id="chunk1",
                    content="Source",
                    distance=0.2,
                    metadata={"document_id": "doc1", "filename": "file.md"},
                )
            ]
        ]

        llm_response = Mock()
        llm_response.content = "Content"
        mock_llm_client.generate.return_value = llm_response

        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=[OutlineSection(title="Section", description="Desc")],
        )

        generator.generate(
            outline=outline,
            temperature=0.5,
            max_section_words=500,
        )

        # Verify temperature passed to LLM
        call_args = mock_llm_client.generate.call_args
        assert call_args.kwargs["temperature"] == 0.5
        # Max tokens should be roughly 2x word count
        assert call_args.kwargs["max_tokens"] == 1000

    def test_refine_section_basic(self, generator, mock_llm_client, mock_searcher):
        """Test refining a section."""
        # Mock search
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="new_chunk",
                content="New source material",
                distance=0.15,
                metadata={"document_id": "new_doc", "filename": "new.md"},
            )
        ]

        # Mock LLM
        llm_response = Mock()
        llm_response.content = "Refined content"
        mock_llm_client.generate.return_value = llm_response

        # Original section
        original_section = DraftSection(
            title="Section",
            content="Original content",
            citations=[],
        )

        # Refine
        refined = generator.refine_section(
            section=original_section,
            feedback="Add more examples",
            keywords=["test"],
            temperature=0.7,
        )

        # Verify refined section
        assert refined.title == "Section"
        assert refined.content == "Refined content"
        assert len(refined.citations) > 0

        # Verify LLM prompt
        call_args = mock_llm_client.generate.call_args
        user_prompt = call_args.kwargs["prompt"]
        assert "Original content" in user_prompt
        assert "Add more examples" in user_prompt
        assert "New source material" in user_prompt

    def test_refine_section_preserves_subsections(self, generator, mock_llm_client, mock_searcher):
        """Test that refinement preserves subsections."""
        mock_searcher.search.return_value = []

        llm_response = Mock()
        llm_response.content = "Refined"
        mock_llm_client.generate.return_value = llm_response

        subsection = DraftSection(title="Sub", content="Sub content")
        original = DraftSection(
            title="Main",
            content="Original",
            citations=[],
            subsections=[subsection],
        )

        refined = generator.refine_section(
            section=original,
            feedback="Improve",
            keywords=["test"],
        )

        # Subsections should be preserved
        assert len(refined.subsections) == 1
        assert refined.subsections[0].title == "Sub"

    def test_refine_section_avoids_duplicate_citations(
        self, generator, mock_llm_client, mock_searcher
    ):
        """Test that refinement doesn't duplicate citations."""
        # Mock search returns same chunk as existing citation
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="existing_chunk",
                content="Content",
                distance=0.2,
                metadata={"document_id": "doc1", "filename": "file.md"},
            )
        ]

        llm_response = Mock()
        llm_response.content = "Refined"
        mock_llm_client.generate.return_value = llm_response

        # Original section with citation
        from bloginator.models.draft import Citation

        original = DraftSection(
            title="Section",
            content="Original",
            citations=[
                Citation(
                    chunk_id="existing_chunk",
                    document_id="doc1",
                    filename="file.md",
                )
            ],
        )

        refined = generator.refine_section(
            section=original,
            feedback="Improve",
            keywords=["test"],
        )

        # Should not have duplicate
        assert len(refined.citations) == 1
        assert refined.citations[0].chunk_id == "existing_chunk"

    def test_generate_error_handling(self, generator, mock_llm_client, mock_searcher):
        """Test error handling during generation."""
        mock_searcher.batch_search.return_value = [[]]
        mock_llm_client.generate.side_effect = Exception("LLM failed")

        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=[OutlineSection(title="Section", description="Desc")],
        )

        with pytest.raises(Exception, match="LLM failed"):
            generator.generate(outline=outline)

    def test_generate_limits_citations(self, generator, mock_llm_client, mock_searcher):
        """Test that citations are limited to top 5."""
        # Return 10 results
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id=f"chunk{i}",
                content=f"Content {i}",
                distance=0.1 + (i * 0.05),  # Decreasing scores
                metadata={"document_id": f"doc{i}", "filename": f"file{i}.md"},
            )
            for i in range(10)
        ]

        llm_response = Mock()
        llm_response.content = "Content"
        mock_llm_client.generate.return_value = llm_response

        outline_section = OutlineSection(
            title="Section",
            description="Desc",
        )

        draft_section = generator._generate_section(
            outline_section=outline_section,
            keywords=["test"],
        )

        # Should keep only top 5 citations
        assert len(draft_section.citations) == 5
        # Should be highest scores
        assert draft_section.citations[0].chunk_id == "chunk0"
        assert draft_section.citations[4].chunk_id == "chunk4"
