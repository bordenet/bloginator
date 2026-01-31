"""Tests for outline generator."""

from unittest.mock import Mock

import pytest

from bloginator.generation._outline_coverage import analyze_section_coverage
from bloginator.generation._outline_parser import parse_outline_response
from bloginator.generation.outline_generator import OutlineGenerator
from bloginator.models.outline import OutlineSection
from bloginator.search import SearchResult


class TestOutlineGenerator:
    """Tests for OutlineGenerator."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = Mock()
        return client

    @pytest.fixture
    def mock_searcher(self):
        """Create mock searcher."""
        searcher = Mock()
        # Default: return empty search results
        searcher.search.return_value = []
        return searcher

    @pytest.fixture
    def generator(self, mock_llm_client, mock_searcher):
        """Create outline generator with mocks."""
        return OutlineGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
            min_coverage_sources=3,
        )

    def test_initialization(self, mock_llm_client, mock_searcher):
        """Test generator initialization."""
        generator = OutlineGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
            min_coverage_sources=5,
        )

        assert generator.llm_client == mock_llm_client
        assert generator.searcher == mock_searcher
        assert generator.min_coverage_sources == 5

    def test_parse_outline_response_simple(self):
        """Test parsing simple outline response."""
        llm_output = """
## Introduction
Overview of the topic

## Background
Historical context

## Conclusion
Summary
"""

        sections = parse_outline_response(llm_output)

        assert len(sections) == 3
        assert sections[0].title == "Introduction"
        assert sections[0].description == "Overview of the topic"
        assert sections[1].title == "Background"
        assert sections[1].description == "Historical context"
        assert sections[2].title == "Conclusion"
        assert sections[2].description == "Summary"

    def test_parse_outline_response_with_subsections(self):
        """Test parsing outline with subsections."""
        llm_output = """
## Main Section
Main description

### Subsection 1
Sub description 1

### Subsection 2
Sub description 2

## Another Section
Another description
"""

        sections = parse_outline_response(llm_output)

        assert len(sections) == 2
        assert sections[0].title == "Main Section"
        assert len(sections[0].subsections) == 2
        assert sections[0].subsections[0].title == "Subsection 1"
        assert sections[0].subsections[0].description == "Sub description 1"
        assert sections[0].subsections[1].title == "Subsection 2"
        assert sections[1].title == "Another Section"

    def test_parse_outline_response_multiline_description(self):
        """Test parsing with multiline descriptions."""
        llm_output = """
## Section
First line of description.
Second line of description.
Third line too.
"""

        sections = parse_outline_response(llm_output)

        assert len(sections) == 1
        assert sections[0].title == "Section"
        # Multiple lines should be concatenated with spaces
        assert "First line" in sections[0].description
        assert "Second line" in sections[0].description
        assert "Third line" in sections[0].description

    def test_parse_outline_response_empty(self):
        """Test parsing empty response."""
        sections = parse_outline_response("")
        assert sections == []

    def test_analyze_section_coverage_good(self, generator, mock_searcher):
        """Test coverage analysis with good results."""
        # Mock search results
        search_results = [
            SearchResult(
                chunk_id=f"chunk{i}",
                content=f"Content {i}",
                distance=0.2,
                metadata={"document_id": f"doc{i}"},
            )
            for i in range(10)
        ]
        mock_searcher.search.return_value = search_results

        section = OutlineSection(title="Test Section")
        analyze_section_coverage(
            section, keywords=["test"], searcher=mock_searcher, min_coverage_sources=3
        )

        # Should have high coverage
        assert section.coverage_pct > 50.0
        assert section.source_count == 10
        assert section.notes == ""  # No warning for good coverage

    def test_analyze_section_coverage_low(self, generator, mock_searcher):
        """Test coverage analysis with poor results."""
        # Mock low-quality results with distance=0.85 (similarity=0.15)
        # Coverage calc: effective_sim=0.15, normalized=0.15/0.25=0.6,
        # result_factor=0.5 (1 result), coverage=0.6*0.5*100=30%
        search_results = [
            SearchResult(
                chunk_id="chunk1",
                content="Content",
                distance=0.85,
                metadata={"document_id": "doc1"},
            )
        ]
        mock_searcher.search.return_value = search_results

        section = OutlineSection(title="Test Section")
        analyze_section_coverage(
            section, keywords=["test"], searcher=mock_searcher, min_coverage_sources=3
        )

        # Should have low coverage
        assert section.coverage_pct < 50.0
        assert "⚠️" in section.notes

    def test_analyze_section_coverage_no_results(self, generator, mock_searcher):
        """Test coverage analysis with no results."""
        mock_searcher.search.return_value = []

        section = OutlineSection(title="Test Section")
        analyze_section_coverage(
            section, keywords=["test"], searcher=mock_searcher, min_coverage_sources=3
        )

        assert section.coverage_pct == 0.0
        assert section.source_count == 0
        assert "No corpus coverage" in section.notes

    def test_analyze_section_coverage_few_sources(self, generator, mock_searcher):
        """Test coverage with few unique sources but good similarity."""
        # Many results from same document with high similarity
        search_results = [
            SearchResult(
                chunk_id=f"chunk{i}",
                content=f"Content {i}",
                distance=0.05,  # High similarity (low distance)
                metadata={"document_id": "doc1"},
            )
            for i in range(10)
        ]
        mock_searcher.search.return_value = search_results

        section = OutlineSection(title="Test Section")
        analyze_section_coverage(
            section, keywords=["test"], searcher=mock_searcher, min_coverage_sources=3
        )

        # Only 1 unique source (below min_coverage_sources=3) but high coverage
        assert section.source_count == 1
        assert "Limited sources" in section.notes

    def test_analyze_section_coverage_recursive(self, generator, mock_searcher):
        """Test coverage analysis on nested sections."""
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="chunk1",
                content="Content",
                distance=0.2,
                metadata={"document_id": "doc1"},
            )
        ]

        subsection = OutlineSection(title="Subsection")
        section = OutlineSection(
            title="Main",
            subsections=[subsection],
        )

        analyze_section_coverage(
            section, keywords=["test"], searcher=mock_searcher, min_coverage_sources=3
        )

        # Both should be analyzed
        assert section.coverage_pct > 0
        assert subsection.coverage_pct > 0

    def test_generate_basic(self, generator, mock_llm_client, mock_searcher):
        """Test basic outline generation."""
        # Mock LLM responses for TWO calls: validation then generation
        validation_response = Mock()
        validation_response.content = "VALID"

        generation_response = Mock()
        generation_response.content = """
## Test Overview
Introduction to testing best practices

## Document Management
How to organize test documents
"""
        # First call returns validation, second returns outline
        mock_llm_client.generate.side_effect = [validation_response, generation_response]

        # Mock search results
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="chunk1",
                content="Content about testing and documents",
                distance=0.2,
                metadata={"document_id": "doc1"},
            )
        ]

        outline = generator.generate(
            title="Test Document",
            keywords=["test", "document"],
            thesis="Test thesis",
            num_sections=2,
        )

        # Verify LLM was called twice (validation + generation)
        assert mock_llm_client.generate.call_count == 2
        # Get the second call (generation) args
        call_args = mock_llm_client.generate.call_args_list[1]

        # Check prompt contains required elements (in generation call)
        user_prompt = call_args.kwargs["prompt"]
        assert "Test Document" in user_prompt
        assert "test, document" in user_prompt
        assert "Test thesis" in user_prompt

        # Verify outline
        assert outline.title == "Test Document"
        assert outline.thesis == "Test thesis"
        assert outline.keywords == ["test", "document"]
        assert len(outline.sections) == 2
        assert outline.sections[0].title == "Test Overview"

    def test_generate_with_temperature(self, generator, mock_llm_client, mock_searcher):
        """Test generation with custom temperature."""
        # Mock TWO calls: validation (temp=0.0) then generation (custom temp)
        validation_response = Mock()
        validation_response.content = "VALID"

        generation_response = Mock()
        generation_response.content = "## Section\nDescription"

        mock_llm_client.generate.side_effect = [validation_response, generation_response]
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="chunk1",
                content="Test content about testing",
                distance=0.2,
                metadata={"document_id": "doc1"},
            )
        ]

        generator.generate(
            title="Test",
            keywords=["test"],
            temperature=0.5,
        )

        # Verify LLM called twice
        assert mock_llm_client.generate.call_count == 2
        # First call (validation) uses temperature=0.0
        assert mock_llm_client.generate.call_args_list[0].kwargs["temperature"] == 0.0
        # Second call (generation) uses custom temperature
        assert mock_llm_client.generate.call_args_list[1].kwargs["temperature"] == 0.5

    def test_generate_error_handling(self, generator, mock_llm_client, mock_searcher):
        """Test error handling in generation."""
        mock_llm_client.generate.side_effect = Exception("LLM error")

        with pytest.raises(Exception, match="LLM error"):
            generator.generate(
                title="Test",
                keywords=["test"],
            )

    def test_generate_calculates_stats(self, generator, mock_llm_client, mock_searcher):
        """Test that stats are calculated after generation."""
        # Mock TWO LLM calls: validation then generation
        validation_response = Mock()
        validation_response.content = "VALID"

        generation_response = Mock()
        generation_response.content = """
## Test Implementation
How to implement testing

## Test Coverage
Understanding test coverage
"""
        mock_llm_client.generate.side_effect = [validation_response, generation_response]

        # Mock different coverage levels
        def search_side_effect(query, n_results):
            if "Test Implementation" in query or "implementation" in query:
                return [
                    SearchResult(
                        chunk_id="c1",
                        content="Content about test implementation with test keywords",
                        distance=0.1,
                        metadata={"document_id": "doc1"},
                    )
                ] * 10
            else:
                # Return content that passes validation (must include keywords)
                return [
                    SearchResult(
                        chunk_id="c2",
                        content="Test coverage information with test keywords",
                        distance=0.85,
                        metadata={"document_id": "doc2"},
                    )
                ]

        mock_searcher.search.side_effect = search_side_effect

        outline = generator.generate(
            title="Test",
            keywords=["test"],
        )

        # Stats should be calculated
        assert outline.avg_coverage > 0
        # Test Coverage section should have low coverage
        assert outline.low_coverage_sections > 0
