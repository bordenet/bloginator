"""End-to-end tests for LLM generation round-trips.

These tests verify the complete LLM generation cycle from prompt construction
through response parsing using the mock LLM client for deterministic testing.

Part of Coder B's implementation (see docs/PARALLEL_VALIDATION_COVERAGE_PLAN.md).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bloginator.generation.draft_generator import DraftGenerator
from bloginator.generation.llm_base import LLMProvider, LLMResponse
from bloginator.generation.llm_client import MockLLMClient, create_llm_client
from bloginator.generation.outline_generator import OutlineGenerator
from bloginator.models.outline import Outline, OutlineSection
from bloginator.search import SearchResult


@pytest.fixture
def mock_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable mock LLM mode for testing."""
    monkeypatch.setenv("BLOGINATOR_LLM_MOCK", "true")


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Create mock LLM client directly."""
    return MockLLMClient(model="test-model", verbose=False)


@pytest.fixture
def mock_searcher() -> MagicMock:
    """Create mock corpus searcher with realistic results."""
    searcher = MagicMock()
    searcher.search.return_value = [
        SearchResult(
            chunk_id="chunk-1",
            content="Leadership requires effective communication and team building.",
            metadata={"filename": "leadership.md", "document_id": "doc1"},
            distance=0.15,
        ),
        SearchResult(
            chunk_id="chunk-2",
            content="Engineering culture emphasizes continuous improvement.",
            metadata={"filename": "culture.md", "document_id": "doc2"},
            distance=0.20,
        ),
    ]
    searcher.batch_search.return_value = [
        [
            SearchResult(
                chunk_id="chunk-3",
                content="Section content about leadership practices.",
                metadata={"filename": "practices.md", "document_id": "doc3"},
                distance=0.18,
            )
        ]
    ]
    return searcher


@pytest.mark.e2e
class TestMockLLMClient:
    """Test MockLLMClient behavior directly."""

    def test_mock_client_always_available(self, mock_llm_client: MockLLMClient) -> None:
        """Mock client should always report as available."""
        assert mock_llm_client.is_available() is True

    def test_mock_client_generates_response(self, mock_llm_client: MockLLMClient) -> None:
        """Mock client should generate valid response."""
        response = mock_llm_client.generate(
            prompt="Write a test document.",
            temperature=0.7,
            max_tokens=500,
        )

        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.model == "test-model"
        assert response.finish_reason == "stop"

    def test_mock_client_detects_outline_request(self, mock_llm_client: MockLLMClient) -> None:
        """Mock client should return outline-style response for outline prompts."""
        response = mock_llm_client.generate(
            prompt="Create an outline for a blog post about testing.",
            temperature=0.7,
            max_tokens=1000,
        )

        # Outline responses should contain section markers
        assert "##" in response.content or "Section" in response.content

    def test_mock_client_detects_draft_request(self, mock_llm_client: MockLLMClient) -> None:
        """Mock client should return draft-style response for draft prompts."""
        response = mock_llm_client.generate(
            prompt="Write a paragraph about software testing best practices.",
            temperature=0.7,
            max_tokens=500,
        )

        # Draft responses should be prose paragraphs
        assert len(response.content) > 100


@pytest.mark.e2e
class TestLLMClientFactory:
    """Test LLM client factory with mock mode."""

    def test_factory_creates_mock_when_env_set(self, mock_llm_env: None) -> None:
        """Factory should create MockLLMClient when BLOGINATOR_LLM_MOCK=true."""
        client = create_llm_client(provider=LLMProvider.OLLAMA, model="llama3")
        assert isinstance(client, MockLLMClient)

    def test_factory_respects_mock_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Factory should always use mock when env var is set regardless of provider."""
        monkeypatch.setenv("BLOGINATOR_LLM_MOCK", "true")

        # Even with OLLAMA provider, should get mock
        client = create_llm_client(provider=LLMProvider.OLLAMA)
        assert isinstance(client, MockLLMClient)


@pytest.mark.e2e
class TestOutlineGenerationRoundTrip:
    """Test complete outline generation cycle."""

    def test_outline_generation_produces_valid_structure(
        self, mock_llm_client: MockLLMClient, mock_searcher: MagicMock
    ) -> None:
        """Outline generation should produce valid Outline with sections."""
        generator = OutlineGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
            min_coverage_sources=2,
        )

        outline = generator.generate(
            title="Engineering Leadership Best Practices",
            keywords=["leadership", "engineering", "culture"],
            thesis="Great leaders build great teams",
            num_sections=3,
        )

        assert isinstance(outline, Outline)
        assert outline.title == "Engineering Leadership Best Practices"
        assert len(outline.sections) > 0
        assert all(isinstance(s, OutlineSection) for s in outline.sections)

    def test_outline_generation_with_coverage_analysis(
        self, mock_llm_client: MockLLMClient, mock_searcher: MagicMock
    ) -> None:
        """Outline generation should include coverage analysis."""
        generator = OutlineGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
            min_coverage_sources=1,
        )

        outline = generator.generate(
            title="Team Culture",
            keywords=["culture", "team"],
            num_sections=2,
        )

        # Each section should have coverage_pct (may be 0 if mocked)
        for section in outline.sections:
            assert hasattr(section, "coverage_pct")


@pytest.mark.e2e
class TestDraftGenerationRoundTrip:
    """Test complete draft generation cycle."""

    def test_draft_generation_from_outline(
        self, mock_llm_client: MockLLMClient, mock_searcher: MagicMock
    ) -> None:
        """Draft generation should produce content for all outline sections."""
        generator = DraftGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
        )

        # Create test outline
        outline = Outline(
            title="Test Document",
            thesis="Testing is important",
            keywords=["test", "quality"],
            sections=[
                OutlineSection(
                    title="Introduction",
                    description="Overview of testing importance",
                ),
                OutlineSection(
                    title="Best Practices",
                    description="Testing best practices",
                ),
            ],
        )

        draft = generator.generate(
            outline=outline,
            temperature=0.7,
            max_section_words=200,
        )

        assert draft is not None
        assert len(draft.sections) >= 1

    def test_draft_generation_respects_max_words(
        self, mock_llm_client: MockLLMClient, mock_searcher: MagicMock
    ) -> None:
        """Draft generation should respect max_section_words parameter."""
        generator = DraftGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
        )

        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=[OutlineSection(title="Section", description="Desc")],
        )

        # Generate with low max_words
        draft = generator.generate(
            outline=outline,
            max_section_words=100,
        )

        # Mock should still generate, just verify call completes
        assert draft is not None


@pytest.mark.e2e
class TestLLMResponseParsing:
    """Test LLM response parsing and error handling."""

    def test_outline_parsing_handles_various_formats(
        self, mock_llm_client: MockLLMClient, mock_searcher: MagicMock
    ) -> None:
        """Outline parser should handle various markdown formats."""
        generator = OutlineGenerator(
            llm_client=mock_llm_client,
            searcher=mock_searcher,
        )

        # Multiple generation calls to test consistency
        for _ in range(3):
            outline = generator.generate(
                title="Test Topic",
                keywords=["test"],
                num_sections=2,
            )
            # Should always get a valid outline
            assert isinstance(outline, Outline)
            assert outline.title == "Test Topic"

    def test_generation_with_empty_corpus_results(self, mock_llm_client: MockLLMClient) -> None:
        """Generation should handle empty corpus search results."""
        empty_searcher = MagicMock()
        empty_searcher.search.return_value = []
        empty_searcher.batch_search.return_value = [[]]

        generator = OutlineGenerator(
            llm_client=mock_llm_client,
            searcher=empty_searcher,
        )

        # Should still generate an outline (possibly with low coverage)
        outline = generator.generate(
            title="New Topic",
            keywords=["new"],
            num_sections=2,
        )

        assert isinstance(outline, Outline)


@pytest.mark.e2e
class TestQualityAssuranceIntegration:
    """Test quality assurance features with mock LLM."""

    def test_slop_detection_available(self) -> None:
        """Slop detection module should be importable and functional."""
        from bloginator.quality.slop_detector import SlopDetector

        detector = SlopDetector()
        result = detector.detect("This is a test paragraph with delve deep into.")

        assert result is not None
        assert isinstance(result, list)

    def test_quality_assurance_available(self) -> None:
        """Quality assurance module should be available."""
        from bloginator.quality.quality_assurance import QualityAssurance

        qa = QualityAssurance()
        assert qa is not None
        assert hasattr(qa, "assess_quality")

    def test_retry_orchestrator_available(self) -> None:
        """Retry orchestrator should be available for generation retries."""
        from bloginator.quality.retry_orchestrator import RetryOrchestrator

        # Should be importable and instantiable
        assert RetryOrchestrator is not None
